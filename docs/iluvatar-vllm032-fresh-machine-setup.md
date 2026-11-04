# 新天数机器：从拉取环境到运行 vLLM 0.32 测试

更新：2026-11-04。适用对象：要在另一台天数 Iluvatar / CoreX 服务器上复现本项目环境的同学。

本文按实际搭建顺序给出命令：检查宿主机 → 拉镜像 → 建立隔离 Python → 准备 FlagTree、FlagGems、FlagCX → 安装 vLLM 与适配插件 → 下载模型 → 通信及推理验证 → 图文门禁 → 保存结果。

主线基于当前容器核实的 **CoreX 4.5.0 + Python 3.12 + vLLM 0.32.0**。本文命令经过源码、安装元数据、已有安装脚本和 Shell/Python 语法核对；此次编写没有另找一台空白服务器完整重装，因此下文把尚需目标机器验证的条件写在对应步骤中。

## 1. 先确定要准备什么

### 1.1 硬件与权限

- 一台 Linux x86_64 天数服务器，宿主机已经安装与设备配套的 **CoreX 4.5.0 驱动**。
- Docker 可以正常运行，允许使用本文的设备与驱动库挂载方式。
- 最小 Qwen3-4B 文本冒烟使用 1 张空闲卡；通信验证至少 2 张；本文大模型图文测试使用 4 张 BI-V150。
- 可访问 GitHub、镜像仓库及模型下载源，或由管理员提前转移相同的镜像、源码和模型文件。
- 数据盘能容纳模型、源码、虚拟环境、编译缓存及日志；模型文件的需求以下载源实际大小为准。27B / 35B 模型需预留数十 GB 以上空间。

**宿主机驱动属于前置条件。** CoreX 安装包随操作系统、内核和设备而异，当前适配记录没有可公开验证的统一驱动安装包下载地址。没有驱动时先请管理员按厂商文档安装；只执行 `git clone` 或 `pip install` 不能补齐驱动。

如果新机器是 NVIDIA / A100 / A800，应使用对应 CUDA 镜像和 PyTorch。本文的 CoreX 库、FlagTree 后端、FlagCX 编译选项不能原样用于 NVIDIA 机器。

### 1.2 锁定的软件栈

| 组件 | 本文使用的版本 / 来源 | 用途 |
| --- | --- | --- |
| CoreX | 驱动和容器用户态 4.5.0 | 天数设备运行时及通信依赖 |
| Python | 3.12；当前实例 3.12.11 | 与厂商 wheel 的 ABI 对应 |
| PyTorch | `2.10.0+corex.4.5.0`，来自配套镜像 | 厂商 GPU 支持 |
| FlagTree | `0.6.2a3+iluvatar3.6` | 提供天数版 Triton 编译器 |
| Triton import | `3.6.0`，由 FlagTree 提供 | 运行和编译算子 |
| FlagGems | `5.3.5`；tag `v5.3.5`，提交 `4df52d9168ac55c1c1061cefb4638c570292d896` | 算子实现 |
| FlagCX | 提交 `6143384797219733aee89bd3118b2cb184ad4959` | 多卡通信；在目标容器编译 |
| vLLM | 上游 tag `v0.32.0`，以 EMPTY 模式构建 | 推理框架 |
| vllm-plugin-FL | 适配分支提交 `c17d866e08b583f63998cbd47bc39fe3e57efce0` | 天数平台、runner、算子及通信接入 |
| FlagGems-vllm | `v0.2.0` 源码提交 `b5c2c2249319277ccda4d41aa0f65164bd9b2a19` | 与插件配套的辅助算子；包元数据仍为 0.1.0 |

当前容器另外观察到：Transformers `5.14.1`、tokenizers `0.22.2`、NumPy `1.26.4`、OpenAI SDK `2.46.0`、Pillow `12.3.0`、pytest `8.4.1`、ModelScope `1.39.1`。这些记录用于核对镜像中的 Python 运行时；不要用一次无约束的 `pip install -U` 改动整套环境。

特别注意三个来源：

1. `zz774ever/tianshu` 是教程和交付记录仓库。
2. 本文已核实的适配源码在 `luoyc123/vllm-plugin-FL`，使用表中固定提交。
3. `flagos-ai/vllm-plugin-FL` 是上游仓库。直接克隆上游默认分支，不保证包含本次适配提交。

## 2. 在宿主机准备目录、镜像与容器

**本节全部在宿主机执行。已经进入容器的终端不一定提供 Docker。**

### 2.1 检查驱动、Docker 和磁盘

```bash
uname -m
ixsmi
docker version
df -h /data
```

`uname -m` 应为 `x86_64`；`ixsmi` 应能看到天数卡。部分环境只提供兼容命令 `nvidia-smi`，可用它检查天数驱动，但命令名字本身不代表机器装的是 NVIDIA 卡。

Docker 尚未安装时，按宿主机发行版的 Docker 官方安装步骤准备。本文不在正在使用的宿主机上自动替换驱动或容器运行时。

### 2.2 设置三条宿主机路径

只需根据目标机器修改以下路径。后文容器内统一使用 `/repro` 和 `/models`，不依赖旧机器的 `/workspace` 或共享盘用户名。

```bash
export REPRO_HOST_ROOT=/data/tianshu-repro
export MODEL_HOST_ROOT=/data/models
export COREX_HOST_ROOT=/usr/local/corex-4.5.0

mkdir -p "$REPRO_HOST_ROOT" "$MODEL_HOST_ROOT"
test -f "$COREX_HOST_ROOT/lib64/libcuda.so.1"
test -f "$COREX_HOST_ROOT/lib64/libixml.so"

git clone https://github.com/zz774ever/tianshu.git "$REPRO_HOST_ROOT/docs"
```

如果 `docs` 已存在，用 `git -C "$REPRO_HOST_ROOT/docs" pull --ff-only` 更新，不要重复 clone 到同一目录。

### 2.3 拉取已有的天数基础环境

适配仓库已有部署文档提供如下 CI 镜像和摘要：

```bash
docker login harbor.baai.ac.cn

export BASE_IMAGE='harbor.baai.ac.cn/plugin/vllm-plugin-fl@sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18'
docker pull "$BASE_IMAGE"
docker image inspect "$BASE_IMAGE" --format '{{json .RepoDigests}}'
```

该摘要对应文档中的 `v0.28.0-iluvatar-ci` 镜像。**这是基础环境，其中的 vLLM 0.28 后面会在隔离 venv 中替换成 0.32。** 镜像仓库访问权限需由维护者提供；不要在教程或命令中写入密码。

镜像摘要来源于适配仓库已有文档，本次编写没有在新主机执行 `docker pull`。镜像标签还包含历史 `flagtree0.6.0` 字样，不能据此判断实际安装版本；进入容器后必须执行第 4 节的真实元数据和后端检查。镜像缺少匹配的 FlagTree 时，用第 4.2 节的专用 wheel 补齐。

### 2.4 创建并进入容器

先通过 `ixsmi` 选空闲卡。下面以宿主机 0、1、2、3 卡为例；不是要求必须使用这四张卡。

```bash
docker run -dit \
  --name tianshu-vllm032 \
  --privileged \
  --ipc=host \
  --ulimit nofile=65535:65535 \
  --mount "type=bind,src=$REPRO_HOST_ROOT,dst=/repro" \
  --mount "type=bind,src=$MODEL_HOST_ROOT,dst=/models" \
  --mount type=bind,src=/dev,dst=/dev \
  --mount type=bind,src=/lib/modules,dst=/lib/modules,readonly \
  --mount "type=bind,src=$COREX_HOST_ROOT/lib64/libcuda.so.1,dst=/usr/local/corex/lib64/libcuda.so.1,readonly" \
  --mount "type=bind,src=$COREX_HOST_ROOT/lib64/libixml.so,dst=/usr/local/corex/lib64/libixml.so,readonly" \
  -e REPRO_ROOT=/repro \
  -e REPRO_DEVICES=0,1,2,3 \
  -e COREX_VISIBLE_DEVICES=0,1,2,3 \
  -e CUDA_VISIBLE_DEVICES=0,1,2,3 \
  --entrypoint /bin/bash \
  "$BASE_IMAGE"

docker exec -it tianshu-vllm032 bash
```

后文服务绑定容器的 `127.0.0.1`，测试也在同一容器运行，因此本例不需要暴露宿主机端口。CoreX 使用上述设备及驱动库挂载方式；本教程没有使用 NVIDIA Container Toolkit 的 `--gpus all`。

## 3. 在容器里建立目录与隔离 Python

**从本节起，除明确标注“宿主机”的命令，均在新容器内执行。**

### 3.1 准备系统工具

以下包管理命令适用于该 Ubuntu / Debian 系列镜像，需在容器里以 root 执行：

```bash
set -euo pipefail
apt-get update
apt-get install -y --no-install-recommends \
  git curl ca-certificates build-essential pkg-config python3-venv

export REPRO_ROOT=/repro
mkdir -p "$REPRO_ROOT/src" "$REPRO_ROOT/wheels" "$REPRO_ROOT/results"
python3 --version
python3 -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'
```

不要只在容器里新装一个通用 Python / PyTorch 后开始测试；必须能继承镜像内的厂商依赖。

### 3.2 建立 venv，保留镜像提供的厂商包

```bash
unset PYTHONPATH VLLM_VENDOR
python3 -m venv --system-site-packages "$REPRO_ROOT/venv"
source "$REPRO_ROOT/venv/bin/activate"
export PYTHONNOUSERSITE=1

which python
python -c 'import sys; print(sys.executable); assert sys.prefix != sys.base_prefix'
python -c 'import torch; print(torch.__version__, torch.__file__)'
```

期望 PyTorch 为 `2.10.0+corex.4.5.0`。`--system-site-packages` 有意复用镜像里的 CoreX PyTorch、FlagTree 等依赖；venv 用于单独安装 vLLM 0.32 和适配插件，不覆盖镜像原来的 vLLM 0.28。

如果新镜像 PyTorch 不是这个厂商构建，先修正基础环境。不要用 PyPI 上的普通 `torch==2.10.0` 替代它。

## 4. FlagTree / Triton：先核对，再决定是否安装

### 4.1 镜像已包含正确版本时直接复用

```bash
python - <<'PY'
from importlib import metadata
import triton
from triton._C import libtriton

print('FlagTree:', metadata.version('flagtree'))
print('Triton:', triton.__version__, triton.__file__)
assert metadata.version('flagtree') == '0.6.2a3+iluvatar3.6'
assert triton.__version__.startswith('3.6')
assert hasattr(libtriton, 'iluvatar'), 'Missing Iluvatar compiler backend'
PY
```

通过就继续第 5 节。FlagTree 提供 `import triton`，所以“未安装名为 triton 的独立 distribution”不一定有问题。不能随后再装一个通用 `triton` 覆盖同一导入目录。

### 4.2 缺少正确版本：安装匹配的天数 wheel

本次查询通用 PyPI 的 `flagtree==0.6.2a3+iluvatar3.6` 返回 404，未找到可直接写进教程的匹配公开 wheel 地址。需要向镜像 / 厂商维护者取得对应 **Python 3.12、x86_64、CoreX 4.5.0** 的原始 wheel 和校验值，再放入宿主机 `$REPRO_HOST_ROOT/wheels/`，容器内即 `/repro/wheels/`。

以下仅在第 4.1 节不通过时执行；变量值使用维护者给出的真实文件路径和 SHA256：

```bash
export FLAGTREE_WHEEL=/repro/wheels/维护者提供的完整文件名.whl
export FLAGTREE_WHEEL_SHA256=维护者提供的SHA256

test -f "$FLAGTREE_WHEEL"
printf '%s  %s\n' "$FLAGTREE_WHEEL_SHA256" "$FLAGTREE_WHEEL" | sha256sum -c -
python -m pip install --no-deps --force-reinstall "$FLAGTREE_WHEEL"
```

安装后重新执行第 4.1 节。这个分支的外部交付物是专用 wheel；没有镜像里的正确版本、也没有匹配 wheel 时，不能宣称已具备可复现的完整环境。

### 4.3 需要拉取 FlagTree 源码时

```bash
git clone https://github.com/flagos-ai/flagtree.git "$REPRO_ROOT/src/flagtree"
git -C "$REPRO_ROOT/src/flagtree" rev-parse HEAD
```

这一步方便查看编译器源码。当前已安装 wheel 没有记录可核实的原始源码 commit，不能把“今天 clone 到的 main”冒充同一个二进制版本。主线搭建使用镜像 / wheel，**不需要重编 FlagTree**。

确实要进行编译器开发时，先取得与目标二进制对应的源码提交及 SDK / LLVM 依赖，再按照该提交 README 构建。官方当前 Triton 3.6 分支的安装形式如下；这是开发分支操作，不能直接替代上面的锁定环境：

```bash
: "${FLAGTREE_SOURCE_REF:?Set the source commit supplied by the compiler maintainer}"
cd "$REPRO_ROOT/src/flagtree"
git fetch origin "$FLAGTREE_SOURCE_REF"
git checkout --detach FETCH_HEAD
git submodule update --init --recursive
export FLAGTREE_BACKEND=iluvatar
```

先按该提交 README 准备构建依赖后，再执行：

```bash
FLAGTREE_BACKEND=iluvatar \
  python -m pip install --no-deps --no-build-isolation -v .
```

重编后必须重新检查第 4.1 节和全部算子、通信及模型测试。仅 clone 源码不影响已经安装的编译器。

## 5. 拉取并安装 FlagGems

镜像已经带有 5.3.5 时可以保留；为让源代码与目标版本一致，下面提供完整的拉取、锁定和安装命令。

```bash
git clone https://github.com/flagos-ai/FlagGems.git "$REPRO_ROOT/src/FlagGems"
git -C "$REPRO_ROOT/src/FlagGems" checkout --detach \
  4df52d9168ac55c1c1061cefb4638c570292d896
git -C "$REPRO_ROOT/src/FlagGems" describe --tags --exact-match

python -m pip install --no-deps -e "$REPRO_ROOT/src/FlagGems"

GEMS_VENDOR=iluvatar python - <<'PY'
from importlib import metadata
import flag_gems
print(metadata.version('flag-gems'), flag_gems.__file__)
assert metadata.version('flag-gems') == '5.3.5'
PY
```

`describe` 应显示 `v5.3.5`。这里保留 Python 构建隔离，因为该 FlagGems 提交的构建后端要求 `setuptools<77` 和 `setuptools-scm<10`，与后面插件构建所用工具不同。构建隔离只准备该项目声明的构建工具；`--no-deps` 防止安装器重选运行时 PyTorch / Triton。

不要在这套固定环境中另外执行会自动重装整套后端的 `setup.sh`。当前目标是保留已经核对的 CoreX 与编译器组合。

## 6. 拉取并编译 FlagCX

FlagCX 不是只需安装一个 Python 包。插件实际需要源码内的 Python wrapper 和 `build/lib/libflagcx.so` 两部分。

```bash
git clone https://github.com/flagos-ai/FlagCX.git "$REPRO_ROOT/src/FlagCX"
git -C "$REPRO_ROOT/src/FlagCX" checkout --detach \
  6143384797219733aee89bd3118b2cb184ad4959
git -C "$REPRO_ROOT/src/FlagCX" submodule update --init --recursive

export FLAGCX_PATH="$REPRO_ROOT/src/FlagCX"
export LD_LIBRARY_PATH="/usr/local/corex/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

test -f /usr/local/corex/include/nccl.h
test -e /usr/local/corex/lib/libnccl.so
test -e /usr/local/corex/lib/libcudart.so

cd "$FLAGCX_PATH"
make -j8 USE_ILUVATAR_COREX=1 \
  DEVICE_HOME=/usr/local/corex CCL_HOME=/usr/local/corex

test -f "$FLAGCX_PATH/build/lib/libflagcx.so"
test -f "$FLAGCX_PATH/plugin/interservice/flagcx_wrapper.py"
ldd "$FLAGCX_PATH/build/lib/libflagcx.so"

python - <<'PY'
import ctypes
import os
from pathlib import Path
library = Path(os.environ['FLAGCX_PATH']) / 'build/lib/libflagcx.so'
ctypes.CDLL(str(library))
print('FlagCX library loaded:', library)
PY
```

`make` 选项来自该固定提交的 `Makefile` 与 `docs/build.md`，这不是对旧环境最初编译命令的追溯。本次写教程没有重新编译正在使用的 FlagCX。

`ldd` 中不能有 `not found`。这里的 `libnccl.so` 是 CoreX 提供的兼容通信库，现有环境实际链接到 `/usr/local/corex/lib64/libnccl.so.2`；不应为解决名字相同的问题而安装 NVIDIA 的 NCCL 覆盖它。

不要额外执行 `make install` 改全局目录；本教程通过 `FLAGCX_PATH` 指向这个构建根目录。仅设置环境变量而没有编译出库，不算安装完成。

## 7. 拉取适配源码，安装 EMPTY vLLM 0.32

### 7.1 克隆真正包含适配的提交

```bash
git clone https://github.com/luoyc123/vllm-plugin-FL.git \
  "$REPRO_ROOT/src/vllm-plugin-FL"
export REPO_DIR="$REPRO_ROOT/src/vllm-plugin-FL"
git -C "$REPO_DIR" checkout --detach \
  c17d866e08b583f63998cbd47bc39fe3e57efce0
git -C "$REPO_DIR" rev-parse HEAD
git -C "$REPO_DIR" status --short
```

本教程固定已发布提交。原执行容器中正在诊断的未提交文件不属于此安装基线；后续适配提交发布后，应更新版本表并重新验证。

### 7.2 准备插件 / vLLM 构建工具

```bash
source "$REPRO_ROOT/venv/bin/activate"
unset PYTHONPATH VLLM_VENDOR

python -m pip install \
  'setuptools==80.10.2' \
  'setuptools-scm==10.2.1' \
  'setuptools-rust==1.13.0' \
  'scikit-build-core==0.11.0' \
  'pybind11==3.1.0' \
  'ninja==1.13.0' \
  'cmake==4.4.2' \
  'packaging==26.2' \
  'wheel==0.46.2'
```

除 `wheel` 依据 FlagGems 的构建声明补充外，上述版本来自当前环境元数据。下载源无法提供其中某个版本时，先保留错误并核对镜像 / 包源，避免无约束升级整个运行时。

### 7.3 下载精确上游归档并校验

```bash
curl --fail --location --retry 3 \
  --connect-timeout 20 --max-time 300 \
  https://github.com/vllm-project/vllm/archive/refs/tags/v0.32.0.tar.gz \
  -o "$REPRO_ROOT/src/vllm-v0.32.0.tar.gz"

printf '%s  %s\n' \
  bf592c132f27bbb5f65cff0bbd2ee873eae722b79c8286934fd5b5cf88b43d61 \
  "$REPRO_ROOT/src/vllm-v0.32.0.tar.gz" | sha256sum -c -
```

归档 SHA256 与插件安装 helper 一致。校验不通过时停止，不能跳过校验继续安装。

### 7.4 以 EMPTY 模式安装 vLLM

```bash
cd "$REPO_DIR"
VLLM_SOURCE_ARCHIVE="$REPRO_ROOT/src/vllm-v0.32.0.tar.gz" \
  bash .github/scripts/iluvatar/install_vllm.sh

python - <<'PY'
import sys
from pathlib import Path
import torch
import vllm
print('Python:', sys.executable)
print('vLLM:', vllm.__version__, vllm.__file__)
print('Torch:', torch.__version__, torch.__file__)
assert vllm.__version__.split('+')[0] == '0.32.0'
assert Path(sys.prefix).resolve() in Path(vllm.__file__).resolve().parents
assert torch.__version__ == '2.10.0+corex.4.5.0'
PY
```

该 helper 实际执行 `VLLM_TARGET_DEVICE=empty VLLM_VERSION_OVERRIDE=0.32.0 python -m pip install --no-build-isolation --no-deps <归档源码>`，并核对版本。其核心含义：

- `empty`：使用外部硬件插件，不构建 NVIDIA 的 `vllm._C`。
- `--no-deps`：不把 CoreX PyTorch / FlagTree 换成通用发行版。
- `--no-build-isolation`：复用已经准备的构建工具；上游 v0.32.0 的构建声明包含 `torch==2.13.0`，不能让隔离构建环境自动据此拉取普通 Torch。

不要直接执行普通的 `pip install vllm==0.32.0` 或 `pip install '.[test]'` 替代这一步，后者的依赖也包含上游 vLLM / audio 组合。

### 7.5 安装适配插件及 FlagGems-vllm

```bash
cd "$REPO_DIR"
python -m pip install --no-build-isolation --no-deps -e .
python .github/scripts/install_flaggems_vllm.py
```

第二条命令会拉取并安装固定的 FlagGems-vllm 提交，检查 `direct_url.json` 的 commit，并确认 Torch、FlagTree、FlagGems、vLLM、NumPy 的版本没有被替换。只看到包版本 `0.1.0` 不能证明装错，要核对固定源码提交。

### 7.6 核对并同步上层 Python 依赖

基础镜像还应提供 pytest、requests、OpenAI SDK、Pillow、PyYAML、SQLAlchemy 等依赖。先检查：

```bash
python - <<'PY'
from importlib import metadata
for name in ('transformers', 'tokenizers', 'numpy', 'openai', 'pillow',
             'pytest', 'requests', 'pyyaml', 'sqlalchemy', 'modelscope'):
    print(name, metadata.version(name))
PY
```

若基础镜像中的这些包与当前运行记录不同，使用以下命令同步已观察的上层版本，保留 `--no-deps`，不触碰 PyTorch、FlagTree、FlagGems 或 vLLM：

```bash
python -m pip install --no-deps \
  'transformers==5.14.1' 'tokenizers==0.22.2' \
  'huggingface-hub==1.24.0' 'safetensors==0.8.0' 'numpy==1.26.4' \
  'pytest==8.4.1' 'requests==2.34.2' 'openai==2.46.0' \
  'pillow==12.3.0' 'PyYAML==6.0.1' 'sqlalchemy==2.0.48' \
  'fastapi==0.139.2' 'uvicorn==0.51.0' 'modelscope==1.39.1'
```

**这是当前适配容器的已观察组合，不是上游 vLLM 0.32 声明的依赖兼容承诺。** 精确归档的元数据要求 Transformers `>=5.16.1`、tokenizers `>=0.23.2`、huggingface-hub `>=1.31.0`，并将 FastAPI 限制在 `<0.137.0`；当前容器继承的上述版本与这些要求存在差异。原有测试是在继承环境中执行的，不能把它写成 `pip check` 已全部通过。要做严格上游依赖对齐，应单独升级并重跑验证，不能混在复现旧组合的步骤里悄悄改变版本。

镜像仍需提供其他传递依赖。若同步后出现缺包，先保留 ImportError、检查原镜像和已观察环境清单，再为该缺包补充对应 wheel；本教程没有把现有所有第三方 Python 包打成全离线 wheelhouse。

## 8. 统一设置运行环境并核验

配套脚本位于本教程仓库 `tools/iluvatar-repro/`。

```bash
export REPRO_ROOT=/repro
export REPRO_DEVICES=0,1,2,3
source "$REPRO_ROOT/docs/tools/iluvatar-repro/activate.sh"

python "$REPRO_ROOT/docs/tools/iluvatar-repro/verify_env.py" --min-devices 1
```

这会设置 venv、插件源码路径、FlagCX 根目录、可见卡号和 `VLLM_PLUGINS=fl USE_FLAGGEMS=1 GEMS_VENDOR=iluvatar`，并检查：

- 当前解释器是 venv，vLLM 确实从 venv 导入 0.32。
- PyTorch / FlagTree / FlagGems 版本正确。
- 实际 `import triton` 的文件由 FlagTree distribution 拥有，且包含天数编译后端。
- vllm-plugin-FL 来自当前源码目录，平台识别为 `iluvatar`。
- 可见设备数量满足要求。
- FlagCX 的真实动态库与 Python wrapper 均可导入。
- FlagGems-vllm 的源码 commit 正确。

使用 4 卡完整模型测试时再执行仓库已有的严格检查：

```bash
cd "$REPO_DIR"
python "$REPRO_ROOT/docs/tools/iluvatar-repro/verify_env.py" --min-devices 4
python .github/scripts/iluvatar/verify_stack.py
```

`verify_stack.py` 固定要求至少 4 张卡；只有 1 张卡做小模型冒烟时，不应把它的设备数断言当成安装失败。

**以后每新开一个容器终端，都先执行：**

```bash
export REPRO_ROOT=/repro
source "$REPRO_ROOT/docs/tools/iluvatar-repro/activate.sh"
```

仅 `source venv/bin/activate` 不会替你重建全部插件和通信环境变量。可见卡号需要变化时，在 source 前设置 `REPRO_DEVICES`。

## 9. 先做真实 FlagCX 双卡通信验证

本节会占用两张已选择的卡。只有一张卡时先跳到第 10 节 TP1 冒烟，不能把通信测试记成通过。

```bash
export REPRO_DEVICES=0,1
source "$REPRO_ROOT/docs/tools/iluvatar-repro/activate.sh"

torchrun --standalone --nproc_per_node=2 \
  "$REPRO_ROOT/docs/tools/iluvatar-repro/probe_flagcx.py"
```

预期两个 rank 均输出 `FLAGCX_PASS ... values=[3.0, 3.0, 3.0, 3.0]`，进程正常退出。脚本明确调用插件中的 `PyFlagcxCommunicator`；仅运行 Gloo 的 `all_reduce` 不能代替这一验证。

通信成功后，再恢复下一节需要的卡号。独立 AllReduce 成功只证明所测通信可用，不等于所有模型场景都通过。

## 10. 下载小模型，做最低成本的推理检查

### 10.1 下载 Qwen3-4B

模型放在 `/models`，对应宿主机 `$MODEL_HOST_ROOT`。已有模型时可直接复用完整目录。

```bash
modelscope download \
  --model Qwen/Qwen3-4B \
  --local_dir /models/Qwen3-4B

test -f /models/Qwen3-4B/config.json
```

用于跨机器精度对照时，应锁定相同模型 revision 并比较所有权重 / 配置 / tokenizer 文件校验值；只用同名模型目录不够。下载源的默认模型 revision 可能随时间变化。

### 10.2 TP1 eager 冒烟

```bash
export REPRO_DEVICES=0
source "$REPRO_ROOT/docs/tools/iluvatar-repro/activate.sh"
export RUN_DIR="$REPRO_ROOT/results/smoke-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
set -o pipefail

python "$REPRO_ROOT/docs/tools/iluvatar-repro/smoke.py" \
  --model /models/Qwen3-4B \
  --tp 1 \
  --output "$RUN_DIR/tp1-eager.json" \
  2>&1 | tee "$RUN_DIR/tp1-eager.log"
```

脚本使用 BF16、512 上下文、最多 2 个序列、显存预算 0.65，对两个文本 prompt 各生成最多 16 token。成功时保存版本、导入路径、文本与 token IDs。JSON 的 `status=PASS` 代表真实生成了非空结果，不是 NVIDIA 精度对齐结论。

### 10.3 TP2 eager 和 Graph 检查

拥有两张空闲卡且第 9 节通过后执行：

```bash
export REPRO_DEVICES=0,1
source "$REPRO_ROOT/docs/tools/iluvatar-repro/activate.sh"

python "$REPRO_ROOT/docs/tools/iluvatar-repro/smoke.py" \
  --model /models/Qwen3-4B --tp 2 \
  --output "$RUN_DIR/tp2-eager.json" \
  2>&1 | tee "$RUN_DIR/tp2-eager.log"

python "$REPRO_ROOT/docs/tools/iluvatar-repro/smoke.py" \
  --model /models/Qwen3-4B --tp 2 --graph \
  --output "$RUN_DIR/tp2-full-graph.json" \
  2>&1 | tee "$RUN_DIR/tp2-full-graph.log"
```

Graph 分支使用 `mode=0`、`cudagraph_mode=FULL`、`custom_ops=["all"]`、`ir_enable_torch_wrap=false`，保留 CUDA Graph replay、关闭目前另需验收的 Inductor 编译路径。它与 eager 是不同执行模式；这个新脚本组合需要在目标机器上实际运行后才能判定通过。

**Qwen3-4B 是纯文本小模型，本节不测试图片。** 环境搭建的首轮验证到这里即可；需要图文验证时再执行第 11 节。

## 11. 启动多模态模型并运行图文测试

### 11.1 准备模型

先跑一个 27B 模型即可检查这套图文测试链；35B-A3B MoE 是后续独立扩展项，不必在确认安装成功前就全部运行。

```bash
modelscope download \
  --model Qwen/Qwen3.6-27B \
  --local_dir /models/Qwen3.6-27B
test -f /models/Qwen3.6-27B/config.json
```

该模型名来自当前适配测试对象。下载源不可访问时，由维护者提供同一 revision 的完整模型目录，不要只拷贝部分 safetensors 文件。

### 11.2 终端 A：启动 eager 服务

```bash
export REPRO_ROOT=/repro
export REPRO_DEVICES=0,1,2,3
source "$REPRO_ROOT/docs/tools/iluvatar-repro/activate.sh"
cd "$REPO_DIR"

export MODEL_PATH=/models/Qwen3.6-27B
export SERVED_MODEL_NAME=qwen36-27b
export TENSOR_PARALLEL_SIZE=4
export MAX_MODEL_LEN=4096
export GPU_MEMORY_UTILIZATION=0.70
export PORT=8132
export GATE_DIR="$REPRO_ROOT/results/27b-eager-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$GATE_DIR"
export SERVER_PID_FILE="$GATE_DIR/server.pid"
printf '%s\n' "$GATE_DIR" > "$REPRO_ROOT/current-gate-dir.txt"
set -o pipefail

bash tools/adaptation-gate-cases/run_serve_eager.sh \
  2>&1 | tee "$GATE_DIR/server.log"
```

保持此终端运行。服务启动时会加载权重并编译 / 调优部分算子，首次启动可能明显慢于后续启动；日志持续推进与进程等待输入是不同状态。

### 11.3 终端 B：检查服务并运行官方测试

新开宿主机终端，进入同一个容器：

```bash
docker exec -it tianshu-vllm032 bash
```

随后在这个容器终端执行：

```bash
export REPRO_ROOT=/repro
source "$REPRO_ROOT/docs/tools/iluvatar-repro/activate.sh"
cd "$REPO_DIR"

export MODEL_PATH=/models/Qwen3.6-27B
export SERVED_MODEL_NAME=qwen36-27b
export PORT=8132
export BASE_URL="http://127.0.0.1:$PORT/v1"
export GATE_DIR="$(cat "$REPRO_ROOT/current-gate-dir.txt")"
export SERVER_PID_FILE="$GATE_DIR/server.pid"
export RESULTS_DIR="$GATE_DIR/results"
export SERVICE_TIMEOUT=1800
set -o pipefail

bash tools/adaptation-gate-cases/run_test.sh \
  2>&1 | tee "$GATE_DIR/tests.log"
```

`run_test.sh` 会等待 `/v1/models` 就绪，依次执行 `test_text.py`、`test_image.py`、`test_mix_text_image.py`；失败会返回非零。测试包含文本、图像、并发和混合请求，不是只确认 HTTP 返回 200。

脚本只接受上述环境变量，不接受模型路径等位置参数。固定提交中的 `SERVED_MODEL_NAME` 与服务参数应保持一致。

成功判据：整条测试命令退出码为 0，所有 pytest 场景通过，`$RESULTS_DIR` 里的逐请求 JSON 没有失败。不要删 OCR 图片、过滤并发样例或放宽期望词来让结果变绿。

查看输出位置和服务声明的模型：

```bash
curl --fail --silent --show-error "http://127.0.0.1:$PORT/v1/models"
find "$RESULTS_DIR" -type f -name '*.json' -print
```

`current-gate-dir.txt` 是本教程为单个当前实验设置的交接文件。同一工作目录并行跑多个服务时，每个终端应显式填写自己的 `GATE_DIR`，避免相互覆盖。

### 11.4 在相同模型上验证 FULL Graph

先在终端 A 用 Ctrl+C 停止当前示例服务，确认已释放对应卡和端口，再建立新的结果目录。不能在同一批卡上叠加启动两个模型。

重复第 11.2 节变量设置，把 `GATE_DIR` 命名为新的 `27b-full-graph-时间戳`，并将最后的启动命令替换为：

```bash
export GRAPH_COMPILATION_CONFIG='{"mode":0,"cudagraph_mode":"FULL","custom_ops":["all"],"ir_enable_torch_wrap":false}'

bash tools/adaptation-gate-cases/run_serve_graph.sh \
  2>&1 | tee "$GATE_DIR/server.log"
```

再按第 11.3 节在终端 B 运行同一组测试。Graph 不加这个配置就会采用不同的上游默认编译策略，不能与本文结果直接混用。

### 11.5 后续需要 35B 或完整矩阵时

35B 模型下载方法：

```bash
modelscope download \
  --model Qwen/Qwen3.6-35B-A3B \
  --local_dir /models/Qwen3.6-35B-A3B
```

单独测试时，将第 11.2 / 11.3 节两侧的模型路径和 served name 一起替换，使用新目录。若要一次执行两模型 × eager / graph 的完整矩阵，先停掉手动启动的服务，再执行：

```bash
source "$REPRO_ROOT/docs/tools/iluvatar-repro/activate.sh"
cd "$REPO_DIR"
export ILUVATAR_MODEL_27B=/models/Qwen3.6-27B
export ILUVATAR_MODEL_35B=/models/Qwen3.6-35B-A3B
export TENSOR_PARALLEL_SIZE=4
export MAX_MODEL_LEN=4096
export GPU_MEMORY_UTILIZATION=0.70
export PORT=8132
export ILUVATAR_GATE_RESULTS="$REPRO_ROOT/results/full-gates-$(date +%Y%m%d-%H%M%S)"
unset SERVED_MODEL_NAME

bash .github/scripts/iluvatar/run_gates.sh
```

`run_gates.sh` 自己管理服务启停，日志分别保存在四组目录。原适配记录存在 35B OCR 稳定性及精度对齐的未闭环问题；本文固定提交不保证完整矩阵全通过。环境安装成功、冒烟通过、完整图文验收通过是不同结论，应分别记录。

## 12. 运行适配相关单元测试

先停止占卡的示例服务，再执行：

```bash
source "$REPRO_ROOT/docs/tools/iluvatar-repro/activate.sh"
cd "$REPO_DIR"
set -o pipefail

python -m pytest \
  tests/unit_tests/test_runner_selection.py \
  tests/unit_tests/test_iluvatar*.py \
  tests/unit_tests/test_gate_graph_memory.py \
  tests/unit_tests/test_worker_pp032.py \
  tests/unit_tests/compilation/test_iluvatar_graph_refs.py \
  -q 2>&1 | tee "$REPRO_ROOT/results/iluvatar-unit-$(date +%Y%m%d-%H%M%S).log"
```

测试数会随提交变化，以该次输出为准。这些单测不能替代第 9–11 节的真实通信与生成。

## 13. 保存环境指纹和结果

```bash
export SNAPSHOT_DIR="$REPRO_ROOT/results/environment-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SNAPSHOT_DIR"

python -m pip list --format=json > "$SNAPSHOT_DIR/python-packages.json"
python -VV > "$SNAPSHOT_DIR/python-version.txt"
git -C "$REPO_DIR" rev-parse HEAD > "$SNAPSHOT_DIR/plugin-commit.txt"
git -C "$FLAGCX_PATH" rev-parse HEAD > "$SNAPSHOT_DIR/flagcx-commit.txt"
git -C "$REPRO_ROOT/src/FlagGems" rev-parse HEAD > "$SNAPSHOT_DIR/flaggems-commit.txt"
sha256sum "$FLAGCX_PATH/build/lib/libflagcx.so" > "$SNAPSHOT_DIR/flagcx-library.sha256"
python "$REPRO_ROOT/docs/tools/iluvatar-repro/verify_env.py" \
  --min-devices 1 > "$SNAPSHOT_DIR/verify-env.log" 2>&1
```

`python-packages.json` 是环境指纹，不是可以在任何硬件上直接 `pip install` 的通用 requirements。厂商 wheel 来源、源码提交、模型 revision 和镜像摘要同样需要保留。

给对方的最小结果包应包含：本教程链接、镜像摘要、环境指纹、各次测试命令、日志和 JSON、明确的失败项。模型权重和访问凭据不应塞进代码仓库。

## 14. 网络受限时的转移方法

### 14.1 转移相同镜像

在可访问镜像仓库的**宿主机**执行：

```bash
docker pull "$BASE_IMAGE"
docker tag "$BASE_IMAGE" tianshu-iluvatar-base:repro
docker save tianshu-iluvatar-base:repro -o tianshu-iluvatar-base.tar
sha256sum tianshu-iluvatar-base.tar
```

将 tar 与 SHA256 通过你已有的文件传输通道送到目标宿主机，校验后：

```bash
docker load -i tianshu-iluvatar-base.tar
export BASE_IMAGE=tianshu-iluvatar-base:repro
```

再从第 2.4 节建容器。镜像 tar 只包含保存的基础镜像；它不会自动包含挂载的模型、源码、venv 或日志。

### 14.2 提前准备源码、wheel 与模型

需要准备：表中固定提交的插件、FlagGems、带 submodule 的 FlagCX、校验过的 vLLM 归档、固定提交的 FlagGems-vllm、必要的 Python 构建包，以及模型完整目录。FlagTree 缺失时还需要专用 wheel。

源码可以用 `git bundle` 转移，例如在联网机器的插件仓库执行：

```bash
git branch repro-iluvatar-c17d866 c17d866e08b583f63998cbd47bc39fe3e57efce0
git bundle create vllm-plugin-FL.bundle repro-iluvatar-c17d866
```

在目标机器用 `git clone /传入路径/vllm-plugin-FL.bundle /repro/src/vllm-plugin-FL` 克隆并核对 HEAD。不要仅复制根仓库而漏掉 FlagCX 的 submodule 内容。

这不是一套已经制作好的全离线安装包。完全离线时，`install_flaggems_vllm.py` 的固定 Git URL、pip 构建隔离下载和 ModelScope 下载也需要对应的本地材料；仅有 Docker tar 不足以完成后续所有步骤。

## 15. 常见失败与定位顺序

| 现象 | 先检查什么 |
| --- | --- |
| 容器里 `torch.cuda.is_available()` 为 false | 宿主机 `ixsmi`、设备挂载、驱动库及 CoreX 版本；先不要修改模型代码 |
| venv 已激活但导入 vLLM 0.28 | `PYTHONPATH` 是否含全局 site-packages；重新 source 本教程 activate.sh，核对 `vllm.__file__` |
| 找不到 `vllm._C` | EMPTY 构建本身不提供 NVIDIA 扩展；确认 `VLLM_PLUGINS=fl` 与平台是 iluvatar，避免误走 CUDA 默认路径 |
| FlagTree 版本正确但缺少 iluvatar backend | 可能安装了错误平台的 wheel 或被独立 Triton 覆盖；检查真实文件归属和专用后端 |
| FlagCX 可 import 但多卡失败 | wrapper、真实 `.so`、`ldd`、CoreX 通信库和两张卡的独立 AllReduce；不能只看环境变量 |
| 编译 FlagGems 报 setuptools / SCM 不兼容 | 第 5 节保留其构建隔离；不要强迫它使用插件那套 setuptools 80 / SCM 10 |
| 首次启动很慢 | 看加载、编译、autotune 日志是否持续推进；预留服务就绪时间，避免重复启动抢同一批卡 |
| Graph 预热 OOM | 核对 4 卡、4096 上下文、0.70 预算和本文 FULL / mode=0 配置；保存失败日志 |
| 图像接口返回 200 但测试失败 | 这是内容正确性问题；保留 JSON、模型 revision、模式和输入，不能按 HTTP 状态算通过 |
| 35B OCR 仍不稳定 | 属于已记录的诊断范围；复现后单独登记，不应直接归因于新机器环境未安装 |
| 端口被占用 | 查当前容器中已有服务，停止自己的前一次示例或改两侧 PORT；不要批量杀其他人的进程 |

完成第 8 节表示依赖及导入来源通过检查；第 9 节表示所测 FlagCX 通信通过；第 10 节表示小模型能够生成；第 11 节才是图文场景验证。NVIDIA 逐 token / logits 对齐和性能验收需要单独设计对照，本教程没有将它们视为环境安装的成功条件。

## 16. 依据与配套文件

- [运行环境激活脚本](../tools/iluvatar-repro/activate.sh)
- [版本、路径、平台与库检查](../tools/iluvatar-repro/verify_env.py)
- [真实 FlagCX AllReduce 探针](../tools/iluvatar-repro/probe_flagcx.py)
- [Qwen3-4B 冒烟脚本](../tools/iluvatar-repro/smoke.py)
- [适配插件固定提交](https://github.com/luoyc123/vllm-plugin-FL/tree/c17d866e08b583f63998cbd47bc39fe3e57efce0)
- [vLLM 安装 helper](https://github.com/luoyc123/vllm-plugin-FL/blob/c17d866e08b583f63998cbd47bc39fe3e57efce0/.github/scripts/iluvatar/install_vllm.sh)
- [原 CoreX 镜像部署说明](https://github.com/luoyc123/vllm-plugin-FL/blob/c17d866e08b583f63998cbd47bc39fe3e57efce0/docs/usage/iluvatar.md)
- [FlagCX 固定版本构建说明](https://github.com/flagos-ai/FlagCX/blob/6143384797219733aee89bd3118b2cb184ad4959/docs/build.md)
- [FlagTree 天数官方安装说明](https://github.com/flagos-ai/FlagTree/wiki/User-manual-for-iluvatar)

最后一项官方 Wiki 在本次网络环境中访问失败；FlagTree 开发构建形式另外核对了当前已安装包随附 README。本文没有将不可取得的源码 commit、wheel 地址或未执行的新机测试结果编造成已验证事实。

本次文档交付检查：所有 Bash 代码块与配套 Shell 脚本通过语法检查；配套 Python 脚本通过编译和 Ruff 静态检查；本地相对链接通过检查。`verify_env.py --min-devices 1` 在现有适配 venv 中以正确插件源码路径实际返回 PASS，识别 BI-V150 和表中版本。本次没有重新运行通信探针或模型测试，也没有把这些新机执行步骤记成已跑通。
