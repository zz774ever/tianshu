set -euo pipefail
python /workspace/validation/check_doc2.py
export REPRO_DEVICES=0,1
source /workspace/tianshu-delivery/tools/iluvatar-repro/activate-local.sh
python /workspace/validation/doc2-checks/inline-01.py
python /workspace/validation/doc2-checks/inline-03.py
sha256sum /mnt/share/user_homes/yubenjie/0509/corex-driver-linux64-4.5.0.20260509_x86_64.run /workspace/driver-extracted/corex/lib64/libcuda.so.1
test -f /mnt/share/user_homes/models/Qwen3-4B/config.json
cd /workspace/tianshu-delivery
git diff --check
