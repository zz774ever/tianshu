set -euo pipefail
python /workspace/validation/check_doc2.py
cd /workspace/tianshu-delivery
git diff --check
git diff --stat
