set -euo pipefail
: "${MODEL_PATH:?Set the existing Qwen3-4B model directory}"
export PORT="${PORT:-18133}"
test -f "$MODEL_PATH/config.json"
python - <<'PY'
import os
import socket
with socket.socket() as endpoint:
    endpoint.bind(('127.0.0.1', int(os.environ['PORT'])))
print('Text API port is free', flush=True)
PY
exec python -m vllm.entrypoints.cli.main serve "$MODEL_PATH" \
  --served-model-name qwen --host 127.0.0.1 --port "$PORT" \
  --tensor-parallel-size "${TENSOR_PARALLEL_SIZE:-1}" \
  --enforce-eager --max-model-len 4096 --max-num-seqs 16 \
  --max-num-batched-tokens 512 --gpu-memory-utilization 0.65 --seed 0
