set -euo pipefail
cd /workspace/tianshu-delivery
cat tools/iluvatar-repro/activate-local.sh tools/iluvatar-repro/prepare_cli.py tools/iluvatar-repro/probe_flagcx.py
sed -n "1,230p" tools/iluvatar-repro/smoke.py
sed -n "1,160p" tools/iluvatar-repro/serve-text.sh
sed -n "1,150p" tools/iluvatar-repro/text_client.py
sed -n "1,180p" /workspace/pr674-plugin/.github/scripts/install_flaggems_vllm.py
sed -n "1,100p" /workspace/validation/verify_tutorial_publication.py
