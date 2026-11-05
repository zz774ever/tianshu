# 燧原 S60：Qwen3.6-27B / Qwen3.6-35B-A3B 推理复现教程

日期：2026-11-05。按“官方镜像 → 新容器 → 原始环境 → 升级 vLLM / PR 插件 → 环境检查 → 4B → 两个大模型 eager / Graph”的顺序操作。

## 0. 先说明核验结果和实际问题

PR 链接正确：<https://github.com/flagos-ai/vllm-plugin-FL/pull/675>，标题为 `feat(enflame): adapt S60 backend to vLLM 0.32.0`。本教程固定到 2026-11-05 查询到的提交：

```text
5efa61dc4e9f86dc18d265adaa0cb9dc60397322
```

你提供的官方镜像也正确。本次通过 Harbor 的公开 token / manifest 接口核对，标签对应的 manifest digest 为：

```text
harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-enflame-ci
sha256:f21e53101ffcf00fa5b70b39913bd401be93c0d1834c0ae8d07684bf0690bc88
```

需要修正的地方：

1. 这是 **0.28 依赖镜像**，PR 675 要求 **0.32.0 empty 构建**。先升级 vLLM，再安装 PR；不能直接执行 PR 的 setup 脚本然后期待它自动升级 vLLM。
2. 燧原选择卡使用 `TOPS_VISIBLE_DEVICES`，不是沿用天数的 `CUDA_VISIBLE_DEVICES`。大模型按已有适配记录使用 **TP2**。
3. 35B Graph 需要显式传入 `{"custom_ops":["none","+SiluAndMul"]}`。大小写必须一致。不能把天数的 `{"mode":0,"cudagraph_mode":"FULL_DECODE_ONLY"}` 当作燧原已经验证过的配置。
4. TP2 需要 **FlagCX 动态库和 Python wrapper**。当前机器已有匹配组件，本教程复用该 wrapper，并链接新容器镜像里的 FlagCX 库；只设置一个不存在的 `FLAGCX_PATH` 不够。
5. 单纯用 `--no-deps` 升级 vLLM 可能缺少 0.32 的新增依赖。本教程单独解析 common 依赖，以约束保护厂商运行时，随后恢复并校验 FlagTree 编译器文件。
6. 本机实际宿主驱动是 **1.9.10**，仓库历史镜像说明写的是 **1.10.6**。已有设备和服务可用，不能因此把本机驱动写成 1.10.6；本教程不要求更新宿主驱动。
7. **当前适配容器并不满足全部官方 0.32 依赖声明。** 例如已安装 Transformers 5.6.0，而该固定 vLLM 提交要求 `>=5.16.1,<5.20.0`；本次通过 GitHub 官方源码再次核对。这是实际环境问题，即使已有服务能生成，也不能宣称依赖完整通过。下文按官方 common 依赖补齐，补齐后的组合仍需你重新执行模型测试。

本次直接核验了 PR、镜像 manifest、已安装版本、8 张设备的属性、两个编译器/算子文件校验器、真实 TP2 all-reduce、common 依赖解析 dry-run，以及现有大模型服务的健康检查和少量生成请求。**没有在本次新建容器中重跑整套安装及四组大模型测试，不能保证尚未执行的部分全部通过。** 每个检查点失败时先保留日志，再定位问题。

## 1. 环境记录

### 1.1 本机硬件和系统

| 项目 | 本次读取结果 |
|---|---|
| 平台 | 燧原 Enflame，S60 适配环境 |
| 可见加速卡数量 | 8 |
| 单卡显存 | 43,878,764,544 bytes，约 41846.05 MiB |
| 宿主驱动 | `/sys/module/enflame/version`：1.9.10 |
| 宿主操作系统 | Ubuntu 24.04.4 LTS |
| 当前适配容器操作系统 | Ubuntu 24.04.3 LTS |
| 架构 | x86_64 |
| CPU | AMD EPYC 9754 128-Core Processor |
| 操作系统可见逻辑 CPU 数 | 256 |

`efsmi` 在当前受限执行环境报 `ENFLAME driver is not loaded`，但内核模块存在，容器中 `torch.gcu.is_available()` 为 True，8 张设备可见，现有推理服务也正常。因此这次 `efsmi` 输出不能直接判定宿主驱动没有安装。请在你自己的宿主终端再执行一次并截图。容器中没有 `efsmi` 命令也不等于设备不可用。

### 1.2 软件版本

| 组件 | 官方 0.28 镜像基线 / 保留版本 | 升级后要求 |
|---|---|---|
| Python | 3.12.8 | 保留 |
| vLLM | 0.28.0+empty | 0.32.0+empty |
| vLLM 源码 | 0.28 基线 | `5df63a7203cdb9328d824a27b682e77c7b9928be` |
| vllm-plugin-FL | 新容器内实际读取，不猜测 | PR 675 固定提交，见上文 |
| PyTorch | 2.11.0+cpu | 保留 |
| torch-gcu | 2.11.0+3.8.20260713 | 保留 |
| FlagTree | 0.7.0+enflame3.6 | 保留并校验实际文件 |
| triton-gcu | 3.6.0+1.0.20260722 | 保留 |
| FlagGems | 5.4.0 | 保留 |
| FlagCX | 当前适配容器为 0.13.0；新容器再次核查 | 同时验证 wrapper 和库 |
| FlagGems-vllm | 新容器实际读取 | helper 固定 `b5c2c2249319277ccda4d41aa0f65164bd9b2a19` |
| OpenAI SDK / pandas | 3.28.0 / 3.0.6 | 保留 |

`torch` 的 `+cpu` 是这个厂商发行包的版本字符串，实际由 `torch_gcu` 在 GCU 上运行。FlagTree 提供 `triton` Python 命名空间，`pip show triton` 查不到独立发行包可以是正常状态。辅助算子的 release 为 v0.2.0，但其包元数据仍显示 0.1.0，必须检查来源提交，不能只看版本号。

## 2. 宿主准备：模型、空闲卡、FlagCX wrapper

以下在 **宿主终端 A** 执行。所有测试放进新容器，不修改现有 `vllm-fl-enflame-agent` 的 Python、源码或服务。

```bash
efsmi
cat /sys/module/enflame/version
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
docker inspect vllm-fl-enflame-agent --format '{{range .Mounts}}{{println .Type .Source "->" .Destination}}{{end}}'
```

当前已确认原适配容器里模型位于 `/models`。宿主路径不能照抄天数的 `/mnt/share/user_homes/models`；用 Docker 挂载信息取得：

```bash
export MODEL_ROOT="$(docker inspect vllm-fl-enflame-agent --format '{{range .Mounts}}{{if eq .Destination "/models"}}{{.Source}}{{end}}{{end}}')"
test -n "$MODEL_ROOT"
test -d "$MODEL_ROOT"
test -f "$MODEL_ROOT/Qwen3-4B/config.json"
test -f "$MODEL_ROOT/Qwen3.6-27B/config.json"
test -f "$MODEL_ROOT/Qwen3.6-35B-A3B/config.json"
printf '宿主模型目录：%s\n' "$MODEL_ROOT"
```

上述三项 `config.json` 已在现有容器中找到。宿主路径自动获取或文件检查失败时，先根据 `docker inspect` 的输出修正 `MODEL_ROOT`；不要在错误路径上继续创建容器。权重目录还必须包含完整分片、tokenizer 和模型配置。

准备本次日志和匹配的 FlagCX wrapper：

```bash
export RUN_DIR=/root/enflame-test-20261105
mkdir -p "$RUN_DIR/flagcx-runtime/plugin/interservice" "$RUN_DIR/logs"

docker cp \
  vllm-fl-enflame-agent:/workspace/s60-adaptation/flagcx-runtime/plugin/interservice/flagcx_wrapper.py \
  "$RUN_DIR/flagcx-runtime/plugin/interservice/flagcx_wrapper.py"

printf '%s  %s\n' \
  e6e4bdb2c0d0034100d861e132d5092a381cdab5764db7b2a3775b56efc1ff27 \
  "$RUN_DIR/flagcx-runtime/plugin/interservice/flagcx_wrapper.py" | sha256sum -c -
```

这是本机已有适配依赖的复用步骤，不能推广为任意 FlagCX 版本都兼容。校验失败就停止并核对来源，不要临时下载最新 `main` 的 wrapper 替换。

选择两张空闲卡，例如：

```bash
export TOPS_VISIBLE_DEVICES=5,6
```

`5,6` 是示例，执行前必须确认仍空闲。本次读取现有服务环境时，27B 使用 `0,1`，35B 使用 `2,3`，小模型服务使用 `4`；这不是后续时刻的占用保证。设备逻辑编号也不能仅凭 `/dev/gcuN` 文件名推断。

建议在独立 tmux 会话里完成后续长时间安装、编译和服务运行。

## 3. 拉取官方镜像、创建新容器

继续在 **宿主终端 A**：

```bash
export IMAGE='harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-enflame-ci@sha256:f21e53101ffcf00fa5b70b39913bd401be93c0d1834c0ae8d07684bf0690bc88'
docker pull "$IMAGE"
docker image inspect "$IMAGE" --format '{{json .RepoDigests}}'

docker run --detach \
  --name test_plugin_32_enflame_20261105 \
  --privileged \
  --shm-size=32g \
  --net=host \
  --ulimit nofile=65535:65535 \
  --mount "type=bind,src=$MODEL_ROOT,dst=/models,readonly" \
  --mount "type=bind,src=$RUN_DIR,dst=/test-output" \
  -e TOPS_VISIBLE_DEVICES="$TOPS_VISIBLE_DEVICES" \
  --entrypoint /bin/bash \
  "$IMAGE" -lc 'exec sleep infinity'

docker exec -it test_plugin_32_enflame_20261105 bash
```

镜像名保留官方 0.28 标识，后续是在容器内部升级。容器名已存在时换一个新名字，不要删除别人的容器。显式覆盖 entrypoint 是为了保持空容器运行。保持独立 PID 命名空间，不加 `--pid=host`。

燧原这里不挂载天数的 `libcuda.so.1`、`libixml.so`，也不解包天数驱动。

## 4. 查看原始环境并获取固定源码

下面开始在 **新容器终端 A** 执行：

```bash
set -euo pipefail
export PIP_BREAK_SYSTEM_PACKAGES=1
mkdir -p /test-output/logs
cd /workspace

python --version
cat /etc/os-release
python -m pip show vllm vllm-plugin-fl torch torch-gcu flagtree triton-gcu flag-gems flagcx numpy openai pandas
python -m pip freeze > /test-output/logs/packages-before.txt

git clone --branch 0.5.0-dev \
  https://github.com/flagos-ai/vllm-plugin-FL.git \
  /workspace/vllm-plugin-FL-pr675
cd /workspace/vllm-plugin-FL-pr675
git fetch origin refs/pull/675/head
git checkout --detach 5efa61dc4e9f86dc18d265adaa0cb9dc60397322
test "$(git rev-parse HEAD)" = 5efa61dc4e9f86dc18d265adaa0cb9dc60397322
git rev-parse HEAD | tee /test-output/logs/plugin-commit.txt

python docker/enflame/verify_compiler.py | tee /test-output/logs/compiler-before.json
python docker/enflame/verify_index_fill.py | tee /test-output/logs/index-fill-before.json
```

已有本次专用源码目录时跳过 clone，先核对目录、远端及工作区状态，再 fetch / checkout。不要 `rm -rf` 已有工作区，也不使用 `git pull` 合并 PR。以后 PR 有更新时，先重新审查和验证，再更换教程固定提交。

GitHub 网络失败时，可以将 clone / fetch URL 改为你网络可用的代理，例如 `https://gh-proxy.com/https://github.com/...`；固定提交校验仍保留。不必修改宿主全局 Git 配置。

### 可选：记录原始 0.28 的 4B 基线

先完成下面第 5.1 节的运行环境脚本和单卡检查，再执行第 6 节的 4B 命令，此时还没有安装 PR。基线成败取决于镜像原插件是否存在且接口匹配。

若插件缺失、接口不匹配或无法启动，保存完整报错，将基线记为 FAIL 或未具备运行条件；不要套用天数的 `FusedMoE` 报错作为燧原既定结论。停止基线服务后，再执行第 5.2 节升级。

## 5. 配置运行环境、升级并检查

### 5.1 保存新终端都能加载的运行环境

在新容器内创建脚本；卡号由创建容器时传入的 `TOPS_VISIBLE_DEVICES` 保留：

```bash
cat > /workspace/enflame-test-env.sh <<'SH'
export PIP_BREAK_SYSTEM_PACKAGES=1
export VLLM_PLUGINS=fl
export USE_FLAGGEMS=1
export TORCH_GCU_ENABLE_INT64_AND_UINT64=1
export ENABLE_I64_CHECK=0
export TORCHGCU_INDUCTOR_ENABLE=1
export TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=99999
export FLAGCX_PATH=/test-output/flagcx-runtime
export LD_LIBRARY_PATH="$FLAGCX_PATH/build/lib:/opt/tops/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export FLAGGEMS_ENABLE_OPLIST_PATH=/test-output/logs/flaggems-enabled-ops.txt
unset CUDA_VISIBLE_DEVICES GEMS_VENDOR VLLM_USE_V2_MODEL_RUNNER
SH

source /workspace/enflame-test-env.sh
printf 'TOPS_VISIBLE_DEVICES=%s\n' "$TOPS_VISIBLE_DEVICES"
```

不沿用 `GEMS_VENDOR=iluvatar`。这里让 FlagGems 自动识别燧原。后续每次新开服务端终端，先 `source /workspace/enflame-test-env.sh`。客户端仅发送 HTTP 请求，不需要初始化设备。

先核查所选设备、显存和一个小张量：

```bash
python - <<'PY'
import torch
import torch_gcu

assert torch.gcu.is_available()
assert torch.gcu.device_count() == 2, '本教程的大模型步骤要求恰好两张可见卡'
for device in range(torch.gcu.device_count()):
    properties = torch.gcu.get_device_properties(device)
    print(device, properties)
    print('total_memory_bytes:', properties.total_memory)
    with torch.gcu.device(device):
        free, total = torch.gcu.mem_get_info()
        print('free_MiB:', free / 1024**2, 'total_MiB:', total / 1024**2)
tensor = torch.ones((32, 32), device='gcu:0')
torch.gcu.synchronize()
print('DEVICE_PASS:', tensor.device, tensor.sum().item())
PY
```

若仍看到 8 张卡、显存已被占用或设备初始化失败，先修正卡选择/访问问题再继续。后续大模型使用 0.94 显存预算，需要所选两卡基本空闲。

### 5.2 安装官方 vLLM 0.32 empty 构建

```bash
cd /workspace
git clone --depth 1 --branch v0.32.0 \
  https://github.com/vllm-project/vllm.git /workspace/vllm-032
cd /workspace/vllm-032
test "$(git rev-parse HEAD)" = 5df63a7203cdb9328d824a27b682e77c7b9928be

python -m pip install \
  'setuptools>=78.1.1,<81' 'setuptools-scm>=8' 'setuptools-rust>=1.9' \
  wheel 'packaging>=26' 'cloudpickle>=3.1' pybind11 ninja 'cmake>=3.26.1'

cat > /workspace/enflame-vendor-constraints.txt <<'TXT'
torch==2.11.0+cpu
torch-gcu==2.11.0+3.8.20260713
flagtree==0.7.0+enflame3.6
triton-gcu==3.6.0+1.0.20260722
triton==3.6.0
flag-gems==5.4.0
openai==3.28.0
pandas==3.0.6
TXT

python -m pip install -r requirements/common.txt \
  -c /workspace/enflame-vendor-constraints.txt \
  2>&1 | tee /test-output/logs/vllm-common-install.log

VLLM_TARGET_DEVICE=empty \
  python -m pip install -v --no-build-isolation --no-deps -e . \
  2>&1 | tee /test-output/logs/vllm-install.log
```

若 resolver 报约束冲突，先停止并保存日志；不要删除厂商约束强行安装普通 CUDA 的 torch / Triton。`requirements/common.txt` 是本次升级需要补齐的依赖，`--no-deps` 仅用于随后安装 vLLM 本体和插件。不要设置 `VLLM_VERSION_OVERRIDE=0.32.0`，这个源码版本的 override 分支会绕过追加 `+empty` 的逻辑，导致 PR 的版本门禁不通过。

这里可能把 Transformers 等升级到与当前在线服务不同的版本。当前在线服务的成功结果不能替代新依赖组合的复现结果；本次没有实际执行这一安装事务。

本次在现有容器中使用上述厂商约束、官方 PyPI，执行 common 依赖的 `pip install --dry-run` 成功，未执行安装。解析结果包括 Transformers 5.19.0 和上游 Triton 3.6.0，确认下面恢复 FlagTree 的步骤确有必要。新容器的依赖差异仍以实际安装日志和最终门禁为准。

common 依赖可能安装上游 Triton 并覆盖 FlagTree 的同名文件。按照燧原镜像配方，恢复固定版本、固定哈希的编译器：

```bash
cat > /workspace/enflame-flagtree-wheel.txt <<'TXT'
flagtree==0.7.0+enflame3.6 --hash=sha256:94b3aaf9f9aefa02f535ee5339f16c5304c52a1de5e7e749f742f7b4bf01332d
TXT

mkdir -p /workspace/enflame-wheels
python -m pip download --no-deps --only-binary=:all: --require-hashes \
  --index-url https://resource.flagos.net/repository/flagos-pypi-enflame/simple \
  --dest /workspace/enflame-wheels -r /workspace/enflame-flagtree-wheel.txt

python -m pip uninstall -y triton
python -m pip install --force-reinstall --no-deps --no-index \
  --find-links /workspace/enflame-wheels 'flagtree==0.7.0+enflame3.6'

cd /workspace/vllm-plugin-FL-pr675
python docker/enflame/verify_compiler.py | tee /test-output/logs/compiler-restored.json
python docker/enflame/verify_index_fill.py | tee /test-output/logs/index-fill-restored.json
```

必须先下载并校验成功，再卸载上游 Triton。包 metadata 正确不能代替这两项文件校验。

### 5.3 安装 PR 插件和配套算子

```bash
cd /workspace/vllm-plugin-FL-pr675
python -m pip install --no-build-isolation --no-deps -e . \
  2>&1 | tee /test-output/logs/plugin-install.log
python .github/scripts/install_flaggems_vllm.py \
  2>&1 | tee /test-output/logs/flaggems-vllm-install.log
hash -r
```

helper 会核对固定来源提交。网络中断时修复网络后重试这一条；不要以“已经装过 0.1.0”为由跳过来源检查。

### 5.4 补齐 FlagCX 布局并核查

新容器使用镜像自带的 `flagcx/libflagcx.so`；第 2 节复制的是 Python wrapper，不是另一套设备运行库：

```bash
python - <<'PY'
from importlib import metadata
from pathlib import Path

distribution = metadata.distribution('flagcx')
library = Path(distribution.locate_file('flagcx/libflagcx.so'))
assert library.is_file(), library
target = Path('/test-output/flagcx-runtime/build/lib/libflagcx.so')
target.parent.mkdir(parents=True, exist_ok=True)
if target.is_symlink():
    assert target.resolve() == library.resolve(), (target, library)
else:
    assert not target.exists(), target
    target.symlink_to(library)
print('FlagCX version:', distribution.version)
print('FlagCX library:', library)
PY

ldd "$FLAGCX_PATH/build/lib/libflagcx.so" | tee /test-output/logs/flagcx-ldd.txt
```

`ldd` 出现 `not found` 时先定位缺失的燧原/ECCL依赖，不能继续假定 TP2 通信可用。

### 5.5 最终环境检查

```bash
cd /workspace/vllm-plugin-FL-pr675
python docker/enflame/verify_compiler.py | tee /test-output/logs/compiler-final.json
python docker/enflame/verify_index_fill.py | tee /test-output/logs/index-fill-final.json

python - <<'PY' | tee /test-output/logs/environment-check.txt
import ctypes
import hashlib
import json
import os
import subprocess
from importlib import metadata
from pathlib import Path

import torch
import torch_gcu
import triton
import vllm
import vllm_fl
import flag_gems
import flaggems_vllm
from packaging.requirements import Requirement
from packaging.version import Version
from vllm.platforms import current_platform
from vllm_fl.distributed.device_communicators import flagcx

expected = {
    'torch': '2.11.0+cpu',
    'torch-gcu': '2.11.0+3.8.20260713',
    'flagtree': '0.7.0+enflame3.6',
    'triton-gcu': '3.6.0+1.0.20260722',
    'flag-gems': '5.4.0',
    'openai': '3.28.0',
    'pandas': '3.0.6',
}
for package, wanted in expected.items():
    actual = metadata.version(package)
    print(package, actual)
    assert actual == wanted, (package, actual, wanted)

parsed = Version(vllm.__version__)
assert parsed.base_version == '0.32.0'
assert 'empty' in (parsed.local or '').split('.')
dependency_errors = []
for declaration in metadata.requires('vllm') or []:
    requirement = Requirement(declaration)
    if requirement.marker and not requirement.marker.evaluate({'extra': ''}):
        continue
    try:
        installed = metadata.version(requirement.name)
    except metadata.PackageNotFoundError:
        dependency_errors.append(f'缺少 {requirement}')
        continue
    if not requirement.specifier.contains(installed, prereleases=True):
        dependency_errors.append(f'{requirement}，实际安装 {installed}')
assert not dependency_errors, dependency_errors
commit = subprocess.check_output(
    ['git', '-C', '/workspace/vllm-plugin-FL-pr675', 'rev-parse', 'HEAD'],
    text=True,
).strip()
assert commit == '5efa61dc4e9f86dc18d265adaa0cb9dc60397322'
assert Path(vllm_fl.__file__).resolve().is_relative_to('/workspace/vllm-plugin-FL-pr675')
source = json.loads(metadata.distribution('flaggems-vllm').read_text('direct_url.json'))
assert source['vcs_info']['commit_id'] == 'b5c2c2249319277ccda4d41aa0f65164bd9b2a19'
assert current_platform.device_type == 'gcu'
assert torch.gcu.is_available()
assert torch.gcu.device_count() == 2
assert flagcx._flagcx_available

wrapper = Path(os.environ['FLAGCX_PATH']) / 'plugin/interservice/flagcx_wrapper.py'
assert hashlib.sha256(wrapper.read_bytes()).hexdigest() == 'e6e4bdb2c0d0034100d861e132d5092a381cdab5764db7b2a3775b56efc1ff27'
library = str(Path(os.environ['FLAGCX_PATH']) / 'build/lib/libflagcx.so')
ctypes.CDLL(library)
bridge = flagcx.FLAGCXLibrary(library)
print('FlagCX wrapper:', bridge.__class__.__module__)
print('FlagCX handle:', bool(getattr(bridge, 'devHandle', None)))
print('vLLM:', vllm.__version__, vllm.__file__)
print('plugin:', commit, vllm_fl.__file__)
print('platform:', current_platform.device_type, current_platform.vendor_name)
print('Triton:', triton.__version__, triton.__file__)
print('FlagGems vendor:', getattr(flag_gems, 'vendor_name', 'auto-detected'))
print('辅助算子:', metadata.version('flaggems-vllm'), source)
print('CHECK_PASS: 版本、来源、设备和 FlagCX 加载检查通过')
PY

python -m pip freeze > /test-output/logs/packages-after.txt
```

这仍然只是环境门禁，下一步验证真实 TP2 collective，再进行模型生成。不要直接调用共享容器的 e2e runner，它可能清理同容器其他 vLLM 进程。

### 5.6 验证真实 TP2 FlagCX 通信

在本次私有容器、所选空闲两卡上运行，两个 rank 分别输入全 1 和全 2，all-reduce 结果都必须是全 3：

```bash
cat > /workspace/check_flagcx_tp2.py <<'PY'
import os
import torch
import torch_gcu
import torch.distributed as distributed
from vllm.platforms import current_platform
from vllm_fl.distributed.device_communicators.flagcx import PyFlagcxCommunicator

rank = int(os.environ['LOCAL_RANK'])
torch.gcu.set_device(rank)
distributed.init_process_group('gloo')
communicator = PyFlagcxCommunicator(
    distributed.group.WORLD, torch.device(f'gcu:{rank}')
)
assert communicator.available and not communicator.disabled, getattr(communicator, 'init_error', 'disabled')
tensor = torch.full((16,), rank + 1.0, device=f'gcu:{rank}')
result = communicator.all_reduce(tensor)
torch.gcu.synchronize()
assert torch.equal(result.cpu(), torch.full((16,), 3.0)), result.cpu()
print(f'FLAGCX_REAL_ALLREDUCE rank={rank} result={result.cpu().tolist()}', flush=True)
distributed.destroy_process_group()
PY

torchrun --standalone --nnodes=1 --nproc-per-node=2 \
  /workspace/check_flagcx_tp2.py \
  2>&1 | tee /test-output/logs/flagcx-tp2.log
```

本次已用相同通信逻辑、当前 PR、当前匹配的 FlagCX wrapper / 库，在逻辑卡 `5,6` 上实际通过，两个 rank 都返回全 3，进程退出码为 0。新容器仍需自行跑这一项。

## 6. 升级后先验证 Qwen3-4B eager

在 **容器终端 A**：

```bash
source /workspace/enflame-test-env.sh
set +e
set -o pipefail

python - <<'PY'
import socket
with socket.socket() as listener:
    listener.bind(('0.0.0.0', 8070))
print('端口 8070 空闲')
PY

vllm serve /models/Qwen3-4B \
  --served-model-name qwen --host 127.0.0.1 --port 8070 \
  --dtype bfloat16 --enforce-eager \
  --max-model-len 4096 --max-num-seqs 4 \
  --max-num-batched-tokens 512 --gpu-memory-utilization 0.70 \
  2>&1 | tee /test-output/logs/qwen3-4b-eager-server.log
```

4B 不传 `-tp`，使用可见集合中的第一张卡。4096 是先检查安装和生成的小模型冒烟配置；本次没有重新运行这组，不能写成已经通过。

从服务测试阶段起关闭交互 shell 的 `errexit`，方便 Ctrl+C 停服后继续下一组。安装和环境检查阶段的任一报错仍应先处理，不能跳过。

在 **另一个宿主终端 B** 进入同一个新容器：

```bash
docker exec -it test_plugin_32_enflame_20261105 bash
```

检查服务就绪后发请求：

```bash
curl --noproxy '*' --fail-with-body -sS --max-time 10 \
  http://127.0.0.1:8070/health
curl --noproxy '*' --fail-with-body -sS --max-time 10 \
  http://127.0.0.1:8070/v1/models

curl --noproxy '*' --fail-with-body -sS --max-time 600 \
  http://127.0.0.1:8070/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model":"qwen",
    "messages":[{"role":"user","content":"详细介绍下人工智能"}],
    "temperature":1.0,
    "max_tokens":256,
    "chat_template_kwargs":{"enable_thinking":false}
  }' \
  -o /test-output/logs/qwen3-4b-eager-text.json \
  -w '\nHTTP %{http_code}，耗时 %{time_total} 秒\n'

python -m json.tool /test-output/logs/qwen3-4b-eager-text.json
```

内容位于 `choices[0].message.content`。非流式请求在生成完成后返回。完成后在终端 A 按 Ctrl+C，确认本次服务退出、端口空闲、显存释放，再启动下一组。

## 7. Qwen3.6-27B 测试

以下使用 TP2、最大长度 32768、显存比例 0.94，与本机已有大模型 Gate 服务的主要容量参数一致。eager 和 Graph 保持同一套参数方便比较；没有空闲两卡时不要强行启动。

### 7.1 eager

终端 A：

```bash
source /workspace/enflame-test-env.sh
set -o pipefail
vllm serve /models/Qwen3.6-27B \
  -tp 2 --served-model-name qwen --host 127.0.0.1 --port 8070 \
  --dtype bfloat16 --max-model-len 32768 \
  --gpu-memory-utilization 0.94 --enforce-eager \
  --compilation-config '{"custom_ops":["none","+SiluAndMul"]}' \
  2>&1 | tee /test-output/logs/qwen36-27b-eager-server.log
```

服务就绪后，终端 B 按第 9 节先设 `CASE=qwen36-27b-eager`，再发文本和图像请求。完成后停止服务。

### 7.2 Graph

终端 A：

```bash
source /workspace/enflame-test-env.sh
set -o pipefail
vllm serve /models/Qwen3.6-27B \
  -tp 2 --served-model-name qwen --host 127.0.0.1 --port 8070 \
  --dtype bfloat16 --max-model-len 32768 \
  --gpu-memory-utilization 0.94 \
  --compilation-config '{"custom_ops":["none","+SiluAndMul"]}' \
  2>&1 | tee /test-output/logs/qwen36-27b-graph-server.log
```

Graph 组不传 `--enforce-eager`，保留 `TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1`。这里沿用燧原 PR 的编译/Graph 配置路径，不额外强行指定天数的 mode 0。必须在日志中确认实际发生 Graph capture，不能仅凭省略 eager 参数就填“Graph 通过”。

服务就绪后，终端 B 设置 `CASE=qwen36-27b-graph` 并执行第 9 节。完成后停止服务。

## 8. Qwen3.6-35B-A3B 测试

### 8.1 eager

终端 A：

```bash
source /workspace/enflame-test-env.sh
set -o pipefail
vllm serve /models/Qwen3.6-35B-A3B \
  -tp 2 --served-model-name qwen --host 127.0.0.1 --port 8070 \
  --dtype bfloat16 --max-model-len 32768 \
  --gpu-memory-utilization 0.94 --enforce-eager \
  --compilation-config '{"custom_ops":["none","+SiluAndMul"]}' \
  2>&1 | tee /test-output/logs/qwen36-35b-a3b-eager-server.log
```

终端 B 设置 `CASE=qwen36-35b-a3b-eager` 后执行第 9 节。完成后停止服务。

### 8.2 Graph

终端 A：

```bash
source /workspace/enflame-test-env.sh
set -o pipefail
vllm serve /models/Qwen3.6-35B-A3B \
  -tp 2 --served-model-name qwen --host 127.0.0.1 --port 8070 \
  --dtype bfloat16 --max-model-len 32768 \
  --gpu-memory-utilization 0.94 \
  --compilation-config '{"custom_ops":["none","+SiluAndMul"]}' \
  2>&1 | tee /test-output/logs/qwen36-35b-a3b-graph-server.log
```

35B 此处的 `+SiluAndMul` 尤其重要：历史默认 compiled SiLU 曾触发 `tops_truncf_v2_fp32_to_v1_bf16` / `NoTritonConfigsError`，显式启用 FL SiLU 后有真实设备通过记录。不要改为小写 `+silu_and_mul`。

终端 B 设置 `CASE=qwen36-35b-a3b-graph` 后执行第 9 节。

冷缓存编译、autotune、Graph capture 可能需要很长时间。仓库原生 S60 e2e 超时预算为 120 分钟；客户端的请求超时不负责等待服务启动。应先看到服务就绪和实际 capture 完成，再发请求。日志若出现最终 `Engine core initialization failed`，该次启动已经失败，应保存第一处真实异常。

## 9. 两个大模型统一客户端：文本 + 图像并发

每一组服务启动就绪后，在 **容器终端 B** 执行。按当前服务修改第一行，四个值为：`qwen36-27b-eager`、`qwen36-27b-graph`、`qwen36-35b-a3b-eager`、`qwen36-35b-a3b-graph`。

```bash
export CASE=qwen36-27b-eager
mkdir -p /test-output/logs

curl --noproxy '*' --fail-with-body -sS --max-time 10 \
  http://127.0.0.1:8070/health
curl --noproxy '*' --fail-with-body -sS --max-time 10 \
  http://127.0.0.1:8070/v1/models

curl --noproxy '*' --fail-with-body -sS --max-time 600 \
  http://127.0.0.1:8070/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model":"qwen",
    "messages":[{"role":"user","content":"详细介绍下人工智能"}],
    "temperature":1.0,
    "max_tokens":256,
    "chat_template_kwargs":{"enable_thinking":false}
  }' \
  -o "/test-output/logs/$CASE-text.json" \
  -w '\n文本请求：HTTP %{http_code}，耗时 %{time_total} 秒\n' &
text_pid=$!

curl --noproxy '*' --fail-with-body -sS --max-time 600 \
  http://127.0.0.1:8070/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model":"qwen",
    "messages":[{
      "role":"user",
      "content":[
        {
          "type":"image_url",
          "image_url":{
            "url":"https://qianwen-res.oss-accelerate.aliyuncs.com/Qwen3.5/demo/CI_Demo/mathv-1327.jpg"
          }
        },
        {"type":"text","text":"描述一下这张图片"}
      ]
    }],
    "temperature":1.0,
    "max_tokens":256,
    "chat_template_kwargs":{"enable_thinking":false}
  }' \
  -o "/test-output/logs/$CASE-image.json" \
  -w '\n图像请求：HTTP %{http_code}，耗时 %{time_total} 秒\n' &
image_pid=$!

text_status=0
image_status=0
wait "$text_pid" || text_status=$?
wait "$image_pid" || image_status=$?
printf 'curl 退出码：文本=%s，图像=%s\n' "$text_status" "$image_status"

python - <<'PY'
import json
import os
from pathlib import Path

for kind in ('text', 'image'):
    path = Path('/test-output/logs') / f'{os.environ["CASE"]}-{kind}.json'
    result = json.loads(path.read_text())
    assert 'error' not in result, result
    content = result['choices'][0]['message'].get('content')
    assert content and content.strip(), result
    print(f'\n{kind}:\n{content}')
    print('usage:', result.get('usage'))
PY

test "$text_status" -eq 0
test "$image_status" -eq 0
```

与原教程相比，这里分别保存两个后台请求的返回体和退出码；裸 `wait` 不能可靠表达“两个 curl 都成功”。HTTP 200、内容非空后还需要人工查看文本和图像理解是否合理。`finish_reason=length` 在 256-token 截断测试中可以正常出现。

### 图像 URL 下载失败怎么办

URL 由服务端访问，客户端 `--noproxy '*'` 只影响客户端请求本地 API，不负责服务端下载远程图片。先在同一容器验证：

```bash
curl -L --fail --max-time 60 \
  'https://qianwen-res.oss-accelerate.aliyuncs.com/Qwen3.5/demo/CI_Demo/mathv-1327.jpg' \
  -o /test-output/mathv-1327.jpg
```

若需要排除服务端出网影响，可将下载的同一图片用 Python base64 编码为 `data:image/jpeg;base64,...`，填入请求的 `image_url.url`；接口支持这一输入形式。仍需保留图片来源和实际请求，不能把网络下载失败直接记为模型推理失败。

## 10. 如何确认 FlagGems 算子参与

先查看服务日志是否出现：

```text
FlagGems-vllm integration activated: package=...
[FlagGems] Enable ...
```

再读取本教程指定的算子记录文件：

```bash
cat /test-output/logs/flaggems-enabled-ops.txt
```

需要按模型/模式单独留档时，在启动该组服务前，将环境变量改为独立文件，例如：

```bash
export FLAGGEMS_ENABLE_OPLIST_PATH=/test-output/logs/qwen36-35b-graph-flaggems-ops.txt
```

需要查看 FL 显式算子调度时，在启动服务前增加：

```bash
export VLLM_FL_DISPATCH_DEBUG=1
export VLLM_FL_LOG_LEVEL=DEBUG
```

请求完成后在本组服务日志里查找 `[DISPATCH]`，核对具体算子的 `impl_id` / `kind`；有些算子按策略走 `vendor:gcu` 是正常情况。单独看到安装版本、启用名单、注册表或 integration activated，只能证明依赖/启用状态，不能据此宣称每个算子都实际执行了 FlagGems 内核。严格的执行证明需要结合对应运行时调度记录或 profiler。

## 11. 结果记录与已知限制

建议每组保存：服务启动命令、选卡、插件提交、软件快照、capture 日志、HTTP 状态/耗时、原始返回 JSON 和算子记录。宿主日志位于 `/root/enflame-test-20261105/logs`。

| 本次待复现项目 | 启动 | 文本 | 图像 | Graph capture | 算子证据 |
|---|---|---|---|---|---|
| 原始 0.28 / 4B eager（可选） | 待填 | 待填 | 不适用 | 不适用 | 待填 |
| 升级后 4B eager | 待填 | 待填 | 不适用 | 不适用 | 待填 |
| 升级后 27B TP2 eager | 待填 | 待填 | 待填 | 不适用 | 待填 |
| 升级后 27B TP2 Graph | 待填 | 待填 | 待填 | 待填 | 待填 |
| 升级后 35B-A3B TP2 eager | 待填 | 待填 | 待填 | 不适用 | 待填 |
| 升级后 35B-A3B TP2 Graph | 待填 | 待填 | 待填 | 待填 | 待填 |

本机历史原始 Gate JSON 已逐项读取：27B eager、27B Graph、35B Graph 各 26/26；35B eager 为 25/26，单文本的原始语义/顺序检查未通过，原因是答案缺少 `limitations` 字面关键词。历史文档记录该例外被接受，但本次复现仍须如实填写你的结果，不能写成历史 104/104。

这些历史结果来自先前适配轮次，不自动代表 PR 当前提交已重新通过四组硬件 Gate。当前 PR 仍处于 open 状态，新 0.32 镜像发布和完整硬件 CI 也没有由本教程验证。

本教程两条 curl 是与你天数记录一致的功能冒烟，不是完整 Gate，也不构成吞吐或时延基准。两种模式随机采样可能生成不同文本；比较性能还需要统一并发、长度、预热、缓存和采样参数。

若 OOM，先检查其他任务占卡、遗留的本次进程和实际可见设备。可以另建低容量配置降低上下文或并发，但要作为另一套配置记录，不能算原 32768 配置通过。不要为了绕过 Graph 编译错误关闭精度仿真并将其当作同配置成功。

## 12. 本教程依据

- [PR 675](https://github.com/flagos-ai/vllm-plugin-FL/pull/675)
- [固定提交的 0.32 状态说明](https://github.com/flagos-ai/vllm-plugin-FL/blob/5efa61dc4e9f86dc18d265adaa0cb9dc60397322/docs/usage/enflame-vllm032.md)
- [固定提交的燧原 Dockerfile](https://github.com/flagos-ai/vllm-plugin-FL/blob/5efa61dc4e9f86dc18d265adaa0cb9dc60397322/docker/enflame/Dockerfile)
- [固定提交的 S60 测试配置](https://github.com/flagos-ai/vllm-plugin-FL/blob/5efa61dc4e9f86dc18d265adaa0cb9dc60397322/tests/platforms/enflame.yaml)
- 当前容器 `/workspace/s60-adaptation/STATUS.md` 及 `gate-results/` 下请求级 JSON。
- 本次直接运行的 compiler/index_fill 校验器、GCU 设备查询、现有服务健康检查及短请求；详细边界见同目录的核验记录。
