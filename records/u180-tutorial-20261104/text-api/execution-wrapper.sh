set -euo pipefail
export REPRO_DEVICES=2
source /workspace/tianshu-delivery/tools/iluvatar-repro/activate-local.sh
export MODEL_PATH=/data/models/Qwen/Qwen3-4B
export PORT=18133
export TENSOR_PARALLEL_SIZE=1
root=/workspace/tianshu-manual/results/tutorial-text-api-20261104
mkdir -p "$root"
python /workspace/tianshu-delivery/tools/iluvatar-repro/verify_env.py --min-devices 1 --min-free-gib 30
server=''
cleanup() {
    if [[ -n "$server" ]]; then
        kill -TERM -- "-$server" 2>/dev/null || true
        for ((attempt=0; attempt<30; attempt++)); do
            if ! kill -0 -- "-$server" 2>/dev/null; then
                wait "$server" 2>/dev/null || true
                return
            fi
            sleep 1
        done
        kill -KILL -- "-$server" 2>/dev/null || true
        wait "$server" 2>/dev/null || true
    fi
}
trap cleanup EXIT
setsid bash /workspace/tianshu-delivery/tools/iluvatar-repro/serve-text.sh > "$root/server.log" 2>&1 &
server=$!
printf '%s\n' "$server" > "$root/server.pid"
python /workspace/tianshu-delivery/tools/iluvatar-repro/record.py \
    --root "$REPRO_ROOT/results/steps" text-api-client -- \
    python /workspace/tianshu-delivery/tools/iluvatar-repro/text_client.py \
    --base-url http://127.0.0.1:18133/v1 --model qwen --output-dir "$root/client"
