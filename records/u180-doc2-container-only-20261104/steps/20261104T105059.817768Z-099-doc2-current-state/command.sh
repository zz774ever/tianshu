set -euo pipefail
cd /workspace/tianshu-delivery
git status --short
sed -n "1,130p" README.md
sed -n "1,100p" docs/iluvatar-vllm032-fresh-machine-setup.md
sed -n "1,220p" /workspace/validation/publish_tutorial.py
