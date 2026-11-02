#!/usr/bin/env bash
set -euo pipefail
cd /workspace/vllm-plugin-FL/tools/adaptation-gate-cases
for attempt in $(seq 1 600); do
    if curl --silent --fail --max-time 3 http://127.0.0.1:18101/health >/dev/null; then
        export MODEL_PATH=/models/Qwen3.6-35B-A3B PORT=18101
        export RESULTS_DIR=/workspace/s60-adaptation/gate-results/35b-eager-ci-dispatch-single
        exec python -m pytest test_text.py::test_text_single -vv -s
    fi
    sleep 3
done
printf 'Service readiness timed out\n' >&2
exit 1
