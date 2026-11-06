#!/usr/bin/env bash
set -euo pipefail
source /opt/gate/gate-env.sh
mode=${1:?Usage: bash /opt/gate/run-one.sh graph-or-eager /models/model-directory}
export MODEL_PATH=${2:?Model directory is required}
[[ "$mode" == graph || "$mode" == eager ]]
test -f "$MODEL_PATH/config.json"
export SERVED_MODEL_NAME=qwen-gate
export BASE_URL="http://127.0.0.1:$PORT/v1"
run_dir="/results/$(basename "$MODEL_PATH")-$mode"
mkdir "$run_dir"
export RESULTS_DIR="$run_dir/results"
export SERVER_PID_FILE="$run_dir/server.pid"
export VLLM_CACHE_ROOT="$run_dir/compile-cache"
export TRITON_CACHE_DIR="$run_dir/triton-cache"
export TORCHINDUCTOR_CACHE_DIR="$run_dir/inductor-cache"
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
date -Is > "$run_dir/started-at.txt"
printf '%s\n' "model=$MODEL_PATH" "devices=$CUDA_VISIBLE_DEVICES" "mode=$mode" "graph_config=${GRAPH_COMPILATION_CONFIG:-enforce-eager}" "blacklist=$VLLM_FL_FLAGOS_BLACKLIST_APPEND" > "$run_dir/settings.txt"
server=''
cleanup() {
    if [[ -n "$server" ]]; then
        kill -TERM -- "-$server" 2>/dev/null || true
        for ((attempt=0; attempt<30; attempt++)); do
            if ! kill -0 -- "-$server" 2>/dev/null; then break; fi
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
cd /opt/vllm-plugin-FL
setsid bash "tools/adaptation-gate-cases/run_serve_$mode.sh" > "$run_dir/server.log" 2>&1 &
server=$!
deadline=$((SECONDS+SERVICE_TIMEOUT))
ready=0
while (( SECONDS < deadline )); do
    if ! kill -0 "$server" 2>/dev/null; then break; fi
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
print(json.dumps({'passed': True, 'requests': 26, 'cases': cases}, indent=2))
PY
fi
cleanup
date -Is > "$run_dir/finished-at.txt"
printf '%s\n' "$status" > "$run_dir/exit-code.txt"
printf 'Finished: mode=%s model=%s exit=%s results=%s\n' "$mode" "$(basename "$MODEL_PATH")" "$status" "$run_dir"
exit "$status"
