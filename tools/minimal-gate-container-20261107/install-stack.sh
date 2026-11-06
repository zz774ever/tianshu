#!/usr/bin/env bash
set -euo pipefail
source /input/gate-env.sh
unset PYTHONPATH PIP_CONSTRAINT VLLM_VENDOR
export PIP_NO_CACHE_DIR=1
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
test "$(python -c 'from importlib.metadata import version; print(version("torch"))')" = 2.10.0+corex.4.5.0
mkdir -p /opt/gate /opt/FlagCX /tmp/gate-build
cp /input/gate-env.sh /input/run-one.sh /input/run-four.sh /input/inspect-env.py /opt/gate/
cp /input/SHA256SUMS /input/provenance.json /opt/gate/
cd /input
sha256sum -c SHA256SUMS
python -m pip install --no-deps 'wheel==0.48.0'
python -m pip install --no-deps '/input/flagtree-0.7.0+iluvatar3.6-cp312-cp312-linux_x86_64.whl'
tar -xzf /input/vllm-v0.32.0.tar.gz -C /tmp/gate-build
VLLM_TARGET_DEVICE=empty VLLM_VERSION_OVERRIDE=0.32.0+empty python -m pip install --no-build-isolation --no-deps /tmp/gate-build/vllm-0.32.0
tar -xzf /input/FlagGems-v5.5.0.dev0.tar.gz -C /tmp/gate-build
SETUPTOOLS_SCM_PRETEND_VERSION=5.5.0.dev0 python -m pip install --no-deps /tmp/gate-build/FlagGems-5.5.0.dev0
tar -xzf /input/FlagGems-vllm-b434eaf.tar.gz -C /tmp/gate-build
python -m pip install --no-build-isolation --no-deps /tmp/gate-build/FlagGems-vllm-b434eafb1715849d1019ddcd480c5fc39461665c
tar -xzf /input/vllm-plugin-FL-7a94aee.tar.gz -C /opt
SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+g7a94aeec8 python -m pip install --no-build-isolation --no-deps -e /opt/vllm-plugin-FL
tar -xzf /input/FlagCX-runtime-6143384.tar.gz -C /opt/FlagCX
rm -rf /tmp/gate-build
printf '%s\n' STACK_INSTALL_COMPLETE
