set -euo pipefail
sed -n "1,220p" /workspace/tianshu-delivery/tools/iluvatar-repro/activate.sh
sed -n "1,230p" /workspace/tianshu-delivery/tools/iluvatar-repro/verify_env.py
sed -n "1,210p" /workspace/tianshu-delivery/docs/iluvatar-vllm032-local-reproduction.md
ls -l /usr/local/corex/lib64/libcuda.so.1 /workspace/driver-extracted/corex/lib64
sed -n "1,140p" /workspace/pr674-plugin/pyproject.toml
