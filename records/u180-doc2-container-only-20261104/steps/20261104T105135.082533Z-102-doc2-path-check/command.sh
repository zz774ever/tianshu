set -euo pipefail
ls -ld /mnt/share/user_homes/models /mnt/share/user_homes/models/Qwen3-4B /data/models/Qwen/Qwen3-4B /mnt/share/user_homes/iluv/FlagCX
readlink -f /data/models/Qwen/Qwen3-4B
ls -l /mnt/share/user_homes/yubenjie/0509/corex-driver-linux64-4.5.0.20260509_x86_64.run
rg -n "docker run|source.*models|src=.*models|--mount|libcuda.so.1" /workspace/validation/steps/*/command.sh | head -n 65
