#!/usr/bin/env bash
set -euo pipefail
root=${REPRO_ROOT:-/repro}
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
unset PYTHONPATH
python3 -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'
mkdir -p "$root/src" "$root/downloads" "$root/results"
python3 -m venv --system-site-packages "$root/venv"
export PATH="$root/venv/bin:$PATH"
python -c 'from importlib import metadata; actual = metadata.version("torch"); assert actual == "2.10.0+corex.4.5.0", actual'
python -m pip install --no-deps 'setuptools==80.10.2' 'setuptools-scm==10.2.1' 'wheel==0.48.0'
python -m pip install --no-deps -r "$script_dir/observed-python-pins.txt"
python -m pip install --no-deps --force-reinstall 'pytest==8.4.1'
python -m pip install --no-deps 'https://resource.flagos.net/repository/flagos-pypi-hosted/packages/flagtree/0.7.0+iluvatar3.6/flagtree-0.7.0+iluvatar3.6-cp312-cp312-linux_x86_64.whl#sha256=af6a7c9eddf167441fd872c3e6d673e9da572608dee79dba655b0775db740176'
download() {
    local url=$1 destination=$2 checksum=$3
    if [[ ! -f "$destination" ]]; then
        curl --fail --location --retry 3 --connect-timeout 20 --max-time 600 "$url" -o "$destination"
    fi
    printf '%s  %s\n' "$checksum" "$destination" | sha256sum -c -
}
download https://github.com/vllm-project/vllm/archive/refs/tags/v0.32.0.tar.gz "$root/downloads/vllm-v0.32.0.tar.gz" bf592c132f27bbb5f65cff0bbd2ee873eae722b79c8286934fd5b5cf88b43d61
tar -xzf "$root/downloads/vllm-v0.32.0.tar.gz" -C "$root/src"
VLLM_TARGET_DEVICE=empty VLLM_VERSION_OVERRIDE=0.32.0+empty python -m pip install --no-build-isolation --no-deps "$root/src/vllm-0.32.0"
download https://github.com/flagos-ai/FlagGems/archive/refs/tags/v5.5.0.dev0.tar.gz "$root/downloads/FlagGems-v5.5.0.dev0.tar.gz" b99408419aa0c66ca2ea7644438a7287194841d2daef860d756ec05c27ad680f
tar -xzf "$root/downloads/FlagGems-v5.5.0.dev0.tar.gz" -C "$root/src"
SETUPTOOLS_SCM_PRETEND_VERSION=5.5.0.dev0 python -m pip install --no-deps "$root/src/FlagGems-5.5.0.dev0"
download https://github.com/flagos-ai/FlagGems-vllm/archive/b434eafb1715849d1019ddcd480c5fc39461665c.tar.gz "$root/downloads/FlagGems-vllm-b434eaf.tar.gz" 827d65c8aa9d25a7c4ca8f4953d7eae56fa25808717c7755d91e5862061b10f3
tar -xzf "$root/downloads/FlagGems-vllm-b434eaf.tar.gz" -C "$root/src"
python -m pip install --no-deps --no-build-isolation "$root/src/FlagGems-vllm-b434eafb1715849d1019ddcd480c5fc39461665c"
plugin="$root/src/vllm-plugin-FL"
if [[ ! -d "$plugin/.git" ]]; then
    git init "$plugin"
    git -C "$plugin" remote add origin https://github.com/flagos-ai/vllm-plugin-FL.git
fi
test -z "$(git -C "$plugin" status --porcelain)"
git -C "$plugin" fetch --depth 1 origin 7a94aeec80fbb795d5596569eb7d40cfe5460106
git -C "$plugin" checkout --detach FETCH_HEAD
test "$(git -C "$plugin" rev-parse HEAD)" = 7a94aeec80fbb795d5596569eb7d40cfe5460106
python -m pip install --no-build-isolation --no-deps -e "$plugin"
python - <<'PY'
from importlib import metadata
expected = {'vllm': '0.32.0+empty', 'torch': '2.10.0+corex.4.5.0', 'flagtree': '0.7.0+iluvatar3.6', 'flag-gems': '5.5.0.dev0', 'flaggems-vllm': '0.3.0.dev1'}
for name, version in expected.items():
    actual = metadata.version(name)
    assert actual == version, (name, actual, version)
    print(name, actual)
PY
printf '%s\n' 'STACK_INSTALLED: activate environment, prepare FlagCX, then run verify-env.py and model gates.'
