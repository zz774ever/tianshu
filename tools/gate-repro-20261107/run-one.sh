#!/usr/bin/env bash
set -euo pipefail
mode=${1:?Usage: bash run-one.sh graph-or-eager /models/model-directory}
export MODEL_PATH=${2:?Model directory is required}
if [[ "$mode" != graph && "$mode" != eager ]]; then
    exit 2
fi
: "${REPRO_ROOT:?Source activate.sh first}"
: "${PLUGIN_ROOT:?Source activate.sh first}"
: "${FLAGCX_PATH:?Source activate.sh first}"
test -f "$MODEL_PATH/config.json"
expected_commit=${EXPECTED_PLUGIN_COMMIT:-7a94aeec80fbb795d5596569eb7d40cfe5460106}
test "$(git -C "$PLUGIN_ROOT" rev-parse HEAD)" = "$expected_commit"
test -z "$(git -C "$PLUGIN_ROOT" status --porcelain)"
export PORT=${PORT:-8145}
export BASE_URL="http://127.0.0.1:$PORT/v1"
export SERVED_MODEL_NAME=qwen-gate
model_name=$(basename -- "$MODEL_PATH")
run_dir=$(mktemp -d "$REPRO_ROOT/results/${model_name}-${mode}-$(date +%Y%m%d-%H%M%S).XXXXXX")
export RESULTS_DIR="$run_dir/results"
export SERVER_PID_FILE="$run_dir/server.pid"
export VLLM_CACHE_ROOT="$run_dir/compile-cache"
if [[ "$mode" == graph ]]; then
    export GRAPH_COMPILATION_CONFIG='{"cudagraph_capture_sizes":[1,2,4,8,16,32]}'
else
    unset GRAPH_COMPILATION_CONFIG
fi
python - <<'PY'
import os
import socket
with socket.socket() as probe:
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    probe.bind(('127.0.0.1', int(os.environ['PORT'])))
PY
git -C "$PLUGIN_ROOT" rev-parse HEAD > "$run_dir/plugin-commit.txt"
date -Is > "$run_dir/started-at.txt"
printf '%s\n' "model=$MODEL_PATH" "devices=$CUDA_VISIBLE_DEVICES" "mode=$mode" "graph_config=${GRAPH_COMPILATION_CONFIG:-enforce-eager}" "blacklist=$VLLM_FL_FLAGOS_BLACKLIST_APPEND" > "$run_dir/settings.txt"
printf 'Results: %s\n' "$run_dir"
server=''
cleanup() {
    if [[ -n "$server" ]]; then
        kill -TERM -- "-$server" 2>/dev/null || true
        for ((attempt=0; attempt<30; attempt++)); do
            if ! kill -0 -- "-$server" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        if kill -0 -- "-$server" 2>/dev/null; then
            kill -KILL -- "-$server" 2>/dev/null || true
        fi
        wait "$server" 2>/dev/null || true
        server=''
    fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
cd "$PLUGIN_ROOT"
setsid bash "tools/adaptation-gate-cases/run_serve_$mode.sh" > "$run_dir/server.log" 2>&1 &
server=$!
printf '%s\n' "$server" > "$run_dir/launched-pid.txt"
deadline=$((SECONDS+SERVICE_TIMEOUT))
ready=0
while (( SECONDS < deadline )); do
    if ! kill -0 "$server" 2>/dev/null; then
        break
    fi
    if curl --silent --fail "$BASE_URL/models" > "$run_dir/models.json" 2>/dev/null; then
        kill -0 "$server"
        ready=1
        break
    fi
    sleep 5
done
status=1
if (( ready == 1 )); then
    date -Is > "$run_dir/ready-at.txt"
    status=0
    bash tools/adaptation-gate-cases/run_test.sh > "$run_dir/tests.log" 2>&1 || status=$?
else
    printf 'Service failed to become ready; inspect %s/server.log\n' "$run_dir" >&2
fi
printf '%s\n' "$status" > "$run_dir/gate-exit-code.txt"
date -Is > "$run_dir/gate-finished-at.txt"
if (( status == 0 )); then
    python - "$RESULTS_DIR" <<'PY' > "$run_dir/summary.json" || status=$?
import json
import sys
from pathlib import Path

expected = {'text_single':1, 'text_concurrent_8':8, 'image_single':1, 'image_concurrent_8':8, 'mixed_concurrent_8':8}
cases = {}
for path in Path(sys.argv[1]).rglob('*.json'):
    document = json.loads(path.read_text())
    scenario = document['case']['scenario']
    assert scenario not in cases
    cases[scenario] = document['summary']
    assert all(output['passed'] for output in document['output'])
assert set(cases) == set(expected), cases
for name, count in expected.items():
    assert cases[name]['passed'] and cases[name]['request_count'] == count
    assert cases[name]['passed_count'] == count
print(json.dumps({'passed':True, 'requests':26, 'cases':cases}, indent=2))
PY
fi
cleanup
git status --porcelain > "$run_dir/git-status-after.txt"
date -Is > "$run_dir/finished-at.txt"
printf '%s\n' "$status" > "$run_dir/exit-code.txt"
printf 'Finished: mode=%s model=%s exit=%s results=%s\n' "$mode" "$model_name" "$status" "$run_dir"
exit "$status"
