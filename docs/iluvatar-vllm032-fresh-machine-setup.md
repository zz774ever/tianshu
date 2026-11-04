# 教程二：本机新建容器，复现 vLLM 0.32 纯文本测试

更新：2026-11-04。适用于当前 u180 / n180 天数 BI-V150 机器：假设你还没有自己的环境，从拉镜像、建容器开始。已有 `testtianshuzdh` 环境可使用[教程一](iluvatar-vllm032-local-reproduction.md)；本文另建 `tianshu-vllm032-text`，避免覆盖已有容器。

**宿主机只执行必要的 Docker 操作。源码、Python 环境、脚本、缓存和日志全部放在新容器的 `/workspace/repro`。无需下载教程仓库，直接复制本文代码。只测试文本。**

本机已有的模型、驱动包和 FlagCX 全部只读复用。Docker 镜像与容器仍会占用宿主 Docker 存储；本文不创建宿主工作目录，不安装或修改宿主软件。容器删除后，可写层中的源码、venv 和日志也会删除，完成前不要删除容器。

验证边界：已有容器实测通过环境检查、真实双卡 FlagCX AllReduce、Qwen3-4B TP1/TP2 eager、TP2 FULL graph 和文本流式接口检查。**此次改写没有再从镜像新建容器完整重装**；本文做了语法、现有材料及对应路径核对，且在已有环境执行了文档内的厂商和运行时检查代码。见[本次修改与检查记录](../records/u180-doc2-container-only-20261104/README.md)。生成链路和回答正确性分开验收，已有算术错误尚未修复，见第 11 节及[原始验证记录](iluvatar-vllm032-tutorial-validation.md)。

## 1. 固定材料与本机前置条件

| 材料 | 本文使用的值 |
| --- | --- |
| 基础镜像 | `harbor.baai.ac.cn/plugin/vllm-plugin-fl@sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18` |
| Python | 镜像提供的 Python 3.12 |
| CoreX PyTorch distribution | `2.10.0+corex.4.5.0`；`torch.__version__` 实测为 `2.10.0` |
| FlagTree / Triton import | `0.6.2a3+iluvatar3.6` / `3.6.0`，必须有 Iluvatar 后端 |
| FlagGems / NumPy | `5.3.5` / `1.26.4` |
| vLLM | tag `v0.32.0`，提交 `5df63a7203cdb9328d824a27b682e77c7b9928be`，EMPTY 普通安装 |
| 适配插件 | `luoyc123/vllm-plugin-FL`，提交 `c17d866e08b583f63998cbd47bc39fe3e57efce0` |
| FlagGems-vllm | 提交 `b5c2c2249319277ccda4d41aa0f65164bd9b2a19`，包元数据仍为 `0.1.0` |
| 本机 FlagCX | `/mnt/share/user_homes/iluv/FlagCX`，提交 `6143384797219733aee89bd3118b2cb184ad4959` |
| Qwen3-4B | 宿主 `/mnt/share/user_homes/models/Qwen3-4B` → 容器 `/models/Qwen3-4B` |
| 驱动用户态包 | `/mnt/share/user_homes/yubenjie/0509/corex-driver-linux64-4.5.0.20260509_x86_64.run` |

宿主已具备可用 Docker、CoreX 4.5.0 驱动和上述共享材料。本文不安装宿主驱动或 Docker。另一台机器没有这些文件时，不能原样照搬路径，需先取得匹配材料。

只做 TP1 文本需要一张空闲卡；双卡通信和 TP2 需要两张。下文 `0,1` 是示例，必须在容器内检查当时占用后选择。

## 2. 宿主机：只拉镜像、创建容器、进入容器

**仅本节和第 11 节的 `docker exec` 在宿主终端执行。后续 git、pip、mkdir、驱动解包及 Python 代码全部在容器内。**

### 2.1 拉取固定镜像

```bash
docker pull harbor.baai.ac.cn/plugin/vllm-plugin-fl@sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18
```

仅当提示鉴权失败时，才执行 `docker login harbor.baai.ac.cn` 后重试。凭据向镜像维护者取得，不写进教程或测试日志。拉取失败保留终端错误，不换成未知镜像。

### 2.2 创建独立容器

```bash
docker run -dit \
  --name tianshu-vllm032-text \
  --init \
  --shm-size=32g \
  --privileged \
  --ulimit nofile=65535:65535 \
  --mount type=bind,src=/dev,dst=/dev \
  --mount type=bind,src=/lib/modules,dst=/lib/modules,readonly \
  --mount type=bind,src=/mnt/share/user_homes,dst=/mnt/share/user_homes,readonly \
  --mount type=bind,src=/mnt/share/user_homes/models,dst=/models,readonly \
  --mount type=bind,src=/usr/local/corex-4.5.0.20260509/lib64/libcuda.so.1,dst=/usr/local/corex/lib64/libcuda.so.1,readonly \
  --mount type=bind,src=/usr/local/corex-4.5.0.20260509/lib64/libixml.so,dst=/usr/local/corex/lib64/libixml.so,readonly \
  --entrypoint /bin/bash \
  harbor.baai.ac.cn/plugin/vllm-plugin-fl@sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18
```

本机驱动目录带 `.20260509`，不能写成 `/usr/local/corex-4.5.0`。`--mount` 遇到源路径缺失会报错，不会替你建立宿主目录。名称冲突时确认是否已创建成功，不自动删除原容器。

设备访问使用 `/dev` 及相应权限；共享文件只读。独立 PID、IPC 和默认桥接网络，服务及客户端在同容器内通信，无需共享宿主网络或映射端口。

### 2.3 进入容器

```bash
docker exec -it tianshu-vllm032-text bash
```

**从下一节起全部在这个容器内执行。** Docker 失败就停在这里，不在宿主补执行后续步骤。

## 3. 容器内：开始记录，建立目录

```bash
export REPRO_ROOT=/workspace/repro
mkdir -p "$REPRO_ROOT"/{src,logs,results,cache}
command -v script
script -q -f "$REPRO_ROOT/logs/session-$(date -u +%Y%m%dT%H%M%SZ).log"
```

最后一条启动带终端记录的子 shell。继续在里面输入以下命令；结束时 `exit` 关闭记录。新终端也可重复这组命令，使用新时间戳。不要在记录会话中输入密码或令牌。

在记录 shell 中设置逐条命令记录器：

```bash
export REPRO_ROOT=/workspace/repro
set -euo pipefail
cat > "$REPRO_ROOT/record.sh" <<'SH'
run_step() {
    local label="$1"
    shift
    local step_dir
    step_dir="$(mktemp -d "$REPRO_ROOT/logs/$(date -u +%Y%m%dT%H%M%SZ)-${label}-XXXXXX")"
    printf '%q ' "$@" > "$step_dir/command.sh"
    printf '\n' >> "$step_dir/command.sh"
    date -u +%FT%TZ > "$step_dir/start.txt"
    local -a codes
    if "$@" 2>&1 | tee "$step_dir/output.log"; then
        codes=("${PIPESTATUS[@]}")
    else
        codes=("${PIPESTATUS[@]}")
    fi
    printf '%s\n' "${codes[0]}" > "$step_dir/exit-code.txt"
    printf '%s\n' "${codes[1]}" > "$step_dir/tee-exit-code.txt"
    date -u +%FT%TZ > "$step_dir/end.txt"
    printf 'EXIT_CODE=%s LOG=%s\n' "${codes[0]}" "$step_dir"
    if (( codes[0] != 0 )); then return "${codes[0]}"; fi
    return "${codes[1]}"
}
SH
source "$REPRO_ROOT/record.sh"
run_step system bash -c 'set -e; uname -m; python3 --version; df -h /workspace; command -v git curl make gcc'
```

每次保存命令、完整 stdout/stderr、起止时间和命令/tee 退出码。export、source 和文件创建等交互操作保存在 session 日志中。失败返回非零；重新进入 shell 后 source 记录器，先定位错误，不跳过失败。

镜像拉取和容器创建发生在记录器启动前：把第 2 节实际命令、拉取输出、容器 ID 及错误从终端复制到容器内保存，不补写虚构的成功记录：

```bash
cat > "$REPRO_ROOT/logs/docker-bootstrap.txt"
```

粘贴原始内容后按 Ctrl+D。此次改写未重新拉镜像或创建容器，因此没有新增这两步的成功记录。

## 4. 容器内：补齐驱动用户态依赖

之前只挂 `libcuda.so.1`、`libixml.so`，实际出现缺少 `libixthunk.so`。在容器内**仅解包**本机同版驱动包，将完整用户态库放在搜索路径最前。不要直接运行安装器安装驱动。

```bash
export DRIVER_PACKAGE=/mnt/share/user_homes/yubenjie/0509/corex-driver-linux64-4.5.0.20260509_x86_64.run
run_step driver-package-check bash -c '
  printf "%s  %s\n" 710468ef4434b5dfafc684e6160fffbbe49c7f3068af3089c86d04c8366b5626 "$DRIVER_PACKAGE" | sha256sum -c -
'
run_step driver-extract bash "$DRIVER_PACKAGE" --noexec --target "$REPRO_ROOT/driver-extracted"
export COREX_DRIVER_LIB_DIR="$REPRO_ROOT/driver-extracted/corex/lib64"
export LD_LIBRARY_PATH="$COREX_DRIVER_LIB_DIR:/usr/local/corex/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
run_step driver-libraries bash -c '
  set -e
  test -f "$COREX_DRIVER_LIB_DIR/libixthunk.so"
  printf "%s  %s\n" 6cf92e5c9112ab657af07076b29446c8210590cd46062111c60f8e367200a35f "$COREX_DRIVER_LIB_DIR/libcuda.so.1" | sha256sum -c -
  ldd "$COREX_DRIVER_LIB_DIR/libcuda.so.1"
  ldd /usr/local/corex/lib64/libcuda.so.1
'
```

两份 `ldd` 都必须没有 `not found`。解包目录已存在时先核对已有文件，不反复向未知目录解包。这里只调用 `--noexec`，不运行驱动安装脚本或操作内核模块。

## 5. 容器内：建立 venv，核对厂商组件

```bash
unset PYTHONPATH VLLM_VENDOR
run_step create-venv python3 -m venv --system-site-packages "$REPRO_ROOT/venv"
source "$REPRO_ROOT/venv/bin/activate"
export PYTHONNOUSERSITE=1
export GEMS_VENDOR=iluvatar
export REPRO_DEVICES=0,1
export COREX_VISIBLE_DEVICES="$REPRO_DEVICES"
export CUDA_VISIBLE_DEVICES="$REPRO_DEVICES"
if command -v ixsmi >/dev/null; then
    run_step devices ixsmi
else
    run_step devices nvidia-smi
fi
```

本机兼容命令可能名为 `nvidia-smi`，实际仍是天数卡。若 0、1 卡有任务，修改三个可见卡变量后继续；单卡使用者选择一张卡并跳过后面的双卡步骤。不要终止其他人的任务。

```bash
run_step vendor-check python - <<'PY'
import sys
from importlib import metadata
from pathlib import Path
import torch
import triton
from triton._C import libtriton

assert sys.version_info[:2] == (3, 12), sys.version
assert sys.prefix != sys.base_prefix, sys.executable
expected = {'torch': '2.10.0+corex.4.5.0', 'flagtree': '0.6.2a3+iluvatar3.6',
            'flag-gems': '5.3.5', 'numpy': '1.26.4'}
for name, value in expected.items():
    actual = metadata.version(name)
    print(name, actual, flush=True)
    assert actual == value, (name, actual, value)
assert triton.__version__ == '3.6.0'
assert hasattr(libtriton, 'iluvatar')
package = metadata.distribution('flagtree')
assert any(Path(package.locate_file(entry)).resolve() == Path(triton.__file__).resolve()
           for entry in package.files or ())
print('python:', sys.executable, 'torch:', torch.__version__, torch.__file__)
print('triton:', triton.__file__)
assert torch.cuda.is_available()
for device in range(torch.cuda.device_count()):
    free, total = torch.cuda.mem_get_info(device)
    print('GPU:', device, torch.cuda.get_device_name(device), free / 2**30, total / 2**30)
    assert free / 2**30 >= 30, 'Select an idle card with at least 30 GiB free'
assert (torch.ones(4, device='cuda') + 2).cpu().tolist() == [3, 3, 3, 3]
assert torch.tensor([1, 2, 3]).numpy().tolist() == [1, 2, 3]
print('VENDOR_PASS')
PY
```

失败就停止。镜像标签的历史版本文字不能代替检查；缺少专用 FlagTree wheel 时需取得匹配材料，不安装普通 torch 或独立 Triton 覆盖厂商组件。

## 6. 容器内：固定源码并安装

### 6.1 拉源码

以下 Git 配置只写容器 `/workspace/repro/gitconfig`。可直连时可不配置 URL 重写，仍需核对相同提交。代理只用于公开源码，不发送令牌。

```bash
export GIT_CONFIG_GLOBAL="$REPRO_ROOT/gitconfig"
run_step git-proxy git config --file "$GIT_CONFIG_GLOBAL" \
  url.https://gh-proxy.org/https://github.com/.insteadOf https://github.com/
run_step clone-vllm git clone --depth 1 --branch v0.32.0 \
  https://github.com/vllm-project/vllm.git "$REPRO_ROOT/src/vllm"
run_step clone-plugin git clone \
  https://github.com/luoyc123/vllm-plugin-FL.git "$REPRO_ROOT/src/vllm-plugin-FL"
export REPO_DIR="$REPRO_ROOT/src/vllm-plugin-FL"
run_step pin-plugin git -C "$REPO_DIR" checkout --detach c17d866e08b583f63998cbd47bc39fe3e57efce0
run_step source-check python - <<'PY'
import os
import subprocess
root = os.environ['REPRO_ROOT']
for name, expected in (
    ('vllm', '5df63a7203cdb9328d824a27b682e77c7b9928be'),
    ('vllm-plugin-FL', 'c17d866e08b583f63998cbd47bc39fe3e57efce0'),
):
    actual = subprocess.check_output(['git', '-C', f'{root}/src/{name}', 'rev-parse', 'HEAD'], text=True).strip()
    print(name, actual)
    assert actual == expected
PY
```

这是已核实的适配快照。PR 674、`0.5.0-dev` 或默认分支可能变化，不用 `git pull` 混入未知新代码。上面下载的是必需的推理框架和插件源码，没有下载教程仓库。

### 6.2 准备 venv 构建工具

```bash
run_step build-tools python -m pip install --no-deps \
  'setuptools==80.10.2' 'setuptools-scm==10.2.1' \
  'setuptools-rust==1.13.0' 'scikit-build-core==0.11.0' \
  'pybind11==3.1.0' 'ninja==1.13.0' 'cmake==4.4.2' \
  'packaging==26.2' wheel
run_step build-imports python -c 'import setuptools, setuptools_scm, setuptools_rust, scikit_build_core, pybind11, wheel, jinja2; print("BUILD_TOOLS_PASS")'
```

版本来自已观察环境；`wheel` 是补充的构建工具，实际选中的版本记录在日志和最终包清单。包源无法提供某版本时保留错误，不无约束升级运行时。这些命令由 venv Python 执行。

### 6.3 EMPTY 普通安装 vLLM，安装插件与辅助算子

```bash
run_step install-vllm env VLLM_TARGET_DEVICE=empty VLLM_VERSION_OVERRIDE=0.32.0 \
  python -m pip install --no-build-isolation --no-deps "$REPRO_ROOT/src/vllm"
run_step install-plugin python -m pip install --no-build-isolation --no-deps -e "$REPO_DIR"
run_step install-flaggems-vllm python "$REPO_DIR/.github/scripts/install_flaggems_vllm.py"
```

对 vLLM 使用普通安装：在 `--system-site-packages` venv 中仅 editable 安装，曾实际导入镜像 vLLM 0.28。插件可 editable 安装，下一节明确指定源码路径。

`empty` 不构建 NVIDIA `vllm._C`；`--no-deps` 保留厂商运行时；`--no-build-isolation` 避免按上游声明拉取普通 `torch==2.13.0`。不要先卸载镜像中的 torch、vLLM 或其他全局包。

辅助算子 helper 固定源码提交，并核对核心运行时版本没变。它可能补装缺少的 packaging、pybind11、PyYAML、SQLAlchemy，也只安装到当前 venv。容器专用 Git 配置同样适用于 helper 的 Git 下载。

## 7. 容器内：固定运行环境，复用只读 FlagCX

```bash
cat > "$REPRO_ROOT/env.sh" <<'SH'
export REPRO_ROOT=/workspace/repro
export REPO_DIR="$REPRO_ROOT/src/vllm-plugin-FL"
export FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX
export COREX_DRIVER_LIB_DIR="$REPRO_ROOT/driver-extracted/corex/lib64"
export GIT_CONFIG_GLOBAL="$REPRO_ROOT/gitconfig"
unset PYTHONPATH VLLM_VENDOR VLLM_ENGINE_ITERATION_TIMEOUT_S VLLM_RPC_TIMEOUT
source "$REPRO_ROOT/venv/bin/activate"
export PYTHONNOUSERSITE=1
export PYTHONPATH="$REPO_DIR"
export VLLM_PLUGINS=fl
export USE_FLAGGEMS=1
export GEMS_VENDOR=iluvatar
export REPRO_DEVICES="${REPRO_DEVICES:-0,1}"
export COREX_VISIBLE_DEVICES="$REPRO_DEVICES"
export CUDA_VISIBLE_DEVICES="$REPRO_DEVICES"
export LD_LIBRARY_PATH="$COREX_DRIVER_LIB_DIR:$FLAGCX_PATH/build/lib:/usr/local/corex/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export XDG_CACHE_HOME="$REPRO_ROOT/cache"
export TRITON_CACHE_DIR="$REPRO_ROOT/cache/triton"
export HF_HOME="$REPRO_ROOT/cache/huggingface"
export VLLM_CACHE_ROOT="$REPRO_ROOT/cache/vllm"
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3600
source "$REPRO_ROOT/record.sh"
SH
source "$REPRO_ROOT/env.sh"
run_step flagcx-library bash -c '
  set -e
  test "$(git -C "$FLAGCX_PATH" rev-parse HEAD)" = 6143384797219733aee89bd3118b2cb184ad4959
  test -f "$FLAGCX_PATH/plugin/interservice/flagcx_wrapper.py"
  test -f "$FLAGCX_PATH/build/lib/libflagcx.so"
  ldd "$FLAGCX_PATH/build/lib/libflagcx.so"
'
```

确认 `ldd` 无 `not found`。已有 FlagCX 由只读共享目录提供，不重新编译、不 `make install`。只有路径变量，没有真实 `.so` 和 wrapper，不能算就绪。

检查最终导入：

```bash
run_step runtime-check python - <<'PY'
import ctypes
import json
import os
import sys
from importlib import metadata
from pathlib import Path
import torch
import vllm
import vllm_fl
from vllm.platforms import current_platform
from vllm_fl.distributed.device_communicators import flagcx

assert vllm.__version__.split('+')[0] == '0.32.0'
assert metadata.version('vllm').split('+')[0] == '0.32.0'
assert Path(sys.prefix).resolve() in Path(vllm.__file__).resolve().parents
assert Path(os.environ['REPO_DIR']).resolve() in Path(vllm_fl.__file__).resolve().parents
assert current_platform.vendor_name == 'iluvatar'
for name, expected in {'torch': '2.10.0+corex.4.5.0', 'flagtree': '0.6.2a3+iluvatar3.6',
                       'flag-gems': '5.3.5', 'numpy': '1.26.4'}.items():
    assert metadata.version(name) == expected
source = json.loads(metadata.distribution('flaggems-vllm').read_text('direct_url.json') or '{}')
assert source.get('vcs_info', {}).get('commit_id') == 'b5c2c2249319277ccda4d41aa0f65164bd9b2a19'
ctypes.CDLL(os.environ['FLAGCX_PATH'] + '/build/lib/libflagcx.so')
assert flagcx._flagcx_available
for name in ('transformers', 'tokenizers', 'huggingface-hub', 'fastapi', 'openai', 'requests'):
    print(name, metadata.version(name))
print('python:', sys.executable)
print('vllm:', vllm.__version__, vllm.__file__)
print('plugin:', vllm_fl.__file__)
print('devices:', torch.cuda.device_count())
print('RUNTIME_PASS')
PY
```

每次新开容器终端，先设置 `REPRO_DEVICES` 再 `source /workspace/repro/env.sh`。不向 `PYTHONPATH` 添加全局 site-packages。后文统一使用 `python -m ...`，避免裸 torchrun 等镜像脚本调用全局 Python。

已测环境继承 Transformers 5.14.1、tokenizers 0.22.2、huggingface-hub 1.24.0、FastAPI 0.139.2 等包，与上游 vLLM 0.32 的部分声明存在差异，不能宣称 `pip check` 全通过。新容器若版本不同或缺包，保留错误和包清单，单独对齐并重测，不用一次无约束升级代替诊断。

## 8. 容器内：真实双卡 FlagCX 通信

只有一张卡时跳过本节及所有 TP2，结果写“未测试”。双卡使用者创建探针：

```bash
cat > "$REPRO_ROOT/probe_flagcx.py" <<'PY'
import os
from datetime import timedelta
import torch
from torch import distributed
from vllm_fl.distributed.device_communicators.flagcx import PyFlagcxCommunicator

local_rank = int(os.environ['LOCAL_RANK'])
torch.cuda.set_device(local_rank)
distributed.init_process_group('gloo', timeout=timedelta(seconds=120))
communicator = None
try:
    assert distributed.get_world_size() == 2
    communicator = PyFlagcxCommunicator(distributed.group.WORLD, torch.device('cuda', local_rank))
    assert communicator.available and not communicator.disabled, getattr(communicator, 'init_error', None)
    tensor = torch.full((1024,), float(distributed.get_rank() + 1), device=f'cuda:{local_rank}')
    result = communicator.all_reduce(tensor)
    torch.cuda.synchronize()
    assert torch.equal(result, torch.full_like(result, 3))
    print(f'FLAGCX_PASS rank={distributed.get_rank()} values={result[:4].tolist()}', flush=True)
    distributed.barrier()
finally:
    if communicator is not None:
        communicator.destroy()
    distributed.destroy_process_group()
PY
export REPRO_DEVICES=0,1
source "$REPRO_ROOT/env.sh"
run_step communication-port python - <<'PY'
import socket
with socket.socket() as endpoint:
    endpoint.bind(('127.0.0.1', 18134))
print('PORT_FREE 18134')
PY
run_step flagcx-tp2 python -m torch.distributed.run \
  --nnodes=1 --nproc_per_node=2 \
  --master-addr=127.0.0.1 --master-port=18134 \
  "$REPRO_ROOT/probe_flagcx.py"
```

两个 rank 都应输出 `[3.0, 3.0, 3.0, 3.0]`，外层 `EXIT_CODE=0`。实际调用 `PyFlagcxCommunicator.all_reduce`，Gloo 只提供控制组。

不用 `--standalone`：此前实际因容器 hostname 无法解析而持续等待。显式单机回环地址解决入口问题，不修改宿主 hosts。端口占用时两处同步换端口，不杀未知进程。

## 9. 容器内：创建纯文本离线冒烟脚本

```bash
test -f /models/Qwen3-4B/config.json
cat > "$REPRO_ROOT/smoke.py" <<'PY'
import argparse
import hashlib
import json
import os
import sys
from importlib import metadata
from pathlib import Path
from vllm import LLM, SamplingParams
import vllm

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tp', type=int, choices=(1, 2), default=1)
    parser.add_argument('--graph', action='store_true')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    target = Path(args.output)
    assert not target.exists(), 'Use a new output path'
    options = {}
    if args.graph:
        options['compilation_config'] = {'mode': 0, 'cudagraph_mode': 'FULL',
                                         'custom_ops': ['all'], 'ir_enable_torch_wrap': False}
    model = LLM(model='/models/Qwen3-4B', tensor_parallel_size=args.tp, dtype='bfloat16',
                enforce_eager=not args.graph, max_model_len=512, max_num_seqs=2,
                max_num_batched_tokens=512, gpu_memory_utilization=0.65, seed=0, **options)
    prompts = ['The capital of France is', 'The speed of light in vacuum is approximately']
    generated = model.generate(prompts, SamplingParams(temperature=0, max_tokens=16))
    assert len(generated) == len(prompts)
    records = []
    for result in generated:
        completion = result.outputs[0]
        assert completion.token_ids and completion.text.strip()
        records.append({'prompt': result.prompt, 'text': completion.text, 'token_ids': list(completion.token_ids)})
    report = {'status': 'GENERATION_PASS', 'scope': 'Nonempty text only; inspect content separately',
              'python': sys.executable, 'vllm': vllm.__version__, 'vllm_path': vllm.__file__,
              'devices': os.environ['CUDA_VISIBLE_DEVICES'], 'tp': args.tp, 'graph': args.graph,
              'versions': {name: metadata.version(name) for name in ('torch', 'flagtree', 'flag-gems', 'numpy', 'transformers', 'tokenizers')},
              'model_config_sha256': hashlib.sha256(Path('/models/Qwen3-4B/config.json').read_bytes()).hexdigest(),
              'outputs': records}
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)

if __name__ == '__main__':
    main()
PY
```

模型只读使用，无需下载。缺少 `config.json` 时先确认挂载和完整材料，不往只读 `/models` 下载。模型 revision 和权重哈希需另存，仅同名目录不足以作跨机器精度对照。

## 10. 容器内：依次运行 TP1 / TP2 eager / FULL graph

```bash
export RUN_DIR="$(mktemp -d "$REPRO_ROOT/results/smoke-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")"
export REPRO_DEVICES=0
source "$REPRO_ROOT/env.sh"
run_step tp1-eager python "$REPRO_ROOT/smoke.py" --tp 1 --output "$RUN_DIR/tp1-eager.json"
```

单卡文本到这里即可。双卡通信已通过时，等上一条命令完全退出再运行：

```bash
export REPRO_DEVICES=0,1
source "$REPRO_ROOT/env.sh"
run_step tp2-eager python "$REPRO_ROOT/smoke.py" --tp 2 --output "$RUN_DIR/tp2-eager.json"
run_step tp2-full-graph python "$REPRO_ROOT/smoke.py" --tp 2 --graph --output "$RUN_DIR/tp2-full-graph.json"
```

配置为 BF16、seed 0、512 上下文、最多 2 序列、512 token 批次预算、0.65 显存预算。每条独立加载模型，首次编译/调优可能较慢，不叠加启动。

成功需退出 0、结果 JSON 的 `GENERATION_PASS` 和非空 token。graph 还要核对日志确实完成捕获；该配置关闭 Inductor、保留 FULL graph replay，不代表 Inductor 已验收。

`GENERATION_PASS` 只表示生成链路可用。检查原文内容，错误也原样保留，不修改预期或删掉记录。

## 11. 容器内：纯文本 API 与流式测试

### 11.1 终端 A：启动单卡 eager 服务

离线测试退出后，检查端口，再启动。只监听同容器 `127.0.0.1:18133`。

```bash
export REPRO_DEVICES=0
source "$REPRO_ROOT/env.sh"
run_step api-port python - <<'PY'
import socket
with socket.socket() as endpoint:
    endpoint.bind(('127.0.0.1', 18133))
print('PORT_FREE 18133')
PY
run_step text-server python -m vllm.entrypoints.cli.main serve /models/Qwen3-4B \
  --served-model-name qwen --host 127.0.0.1 --port 18133 \
  --tensor-parallel-size 1 --enforce-eager --max-model-len 4096 \
  --max-num-seqs 16 --max-num-batched-tokens 512 \
  --gpu-memory-utilization 0.65 --seed 0
```

保持终端 A 运行。服务停止前还没有最终退出码；Ctrl+C 中断后的服务命令不应记成正常退出 0。

### 11.2 终端 B：进入同容器发起请求

**仅这一条 Docker 命令在宿主的新终端执行：**

```bash
docker exec -it tianshu-vllm032-text bash
```

后续重新回到容器内，开始另一个终端记录：

```bash
script -q -f "/workspace/repro/logs/client-session-$(date -u +%Y%m%dT%H%M%SZ).log"
```

在记录 shell 内执行：

```bash
set -euo pipefail
source /workspace/repro/env.sh
export CLIENT_DIR="$(mktemp -d "$REPRO_ROOT/results/api-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")"
cat > "$REPRO_ROOT/text_client.py" <<'PY'
import json
import os
from pathlib import Path
import time
from openai import OpenAI

root = Path(os.environ['CLIENT_DIR'])
def save(name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

client = OpenAI(api_key='EMPTY', base_url='http://127.0.0.1:18133/v1', timeout=300, max_retries=0)
summary = {'transport_passed': False, 'quality_passed': False}
try:
    deadline = time.monotonic() + 1800
    while True:
        try:
            models = client.models.list(timeout=5).model_dump()
            break
        except Exception:
            if time.monotonic() >= deadline:
                raise
            time.sleep(5)
    save('models.json', models)
    assert any(value['id'] == 'qwen' for value in models['data'])
    request = dict(model='qwen', messages=[{'role': 'user', 'content': 'Give me a short introduction to large language models.'}],
                   max_tokens=20, temperature=0.7, top_p=0.8, presence_penalty=1.5, stream=True,
                   extra_body={'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}})
    save('stream-request.json', request)
    chunks = []
    pieces = []
    for chunk in client.chat.completions.create(**request):
        chunks.append(chunk.model_dump())
        if chunk.choices and chunk.choices[0].delta.content:
            pieces.append(chunk.choices[0].delta.content)
            print(chunk.choices[0].delta.content, end='', flush=True)
        save('stream-response.json', {'text': ''.join(pieces), 'chunks': chunks})
    assert ''.join(pieces).strip()
    assert any(choice.get('finish_reason') for chunk in chunks for choice in chunk['choices'])
    checks = []
    for question, expected in [('What is 17 + 25? Answer only with the number.', '42'),
                               ('What is the capital of France? Answer only the city name.', 'paris')]:
        parameters = dict(model='qwen', messages=[{'role': 'user', 'content': question}],
                          max_tokens=32, temperature=0, top_p=1,
                          extra_body={'chat_template_kwargs': {'enable_thinking': False}})
        response = client.chat.completions.create(**parameters)
        text = response.choices[0].message.content or ''
        checks.append({'request': parameters, 'response': response.model_dump(), 'expected': expected,
                       'quality_passed': text.strip().rstrip('.。!').lower() == expected})
        save('quality-responses.json', checks)
        assert text.strip()
    summary.update(transport_passed=True, quality_passed=all(value['quality_passed'] for value in checks))
except Exception as error:
    summary['error'] = f'{type(error).__name__}: {error}'
save('summary.json', summary)
print('\n' + json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
raise SystemExit(0 if summary['transport_passed'] and summary['quality_passed'] else 1)
PY
run_step text-client python "$REPRO_ROOT/text_client.py"
```

结果在 `$CLIENT_DIR`，包含原始请求、逐流式 chunk、完整回答和汇总。脚本要求两项都通过才退出 0：

- `transport_passed`：模型列表正确、流式完成且非空、两个非流式请求均返回非空文本。
- `quality_passed`：两个明确问题分别回答 `42`、`Paris`。只有两个检查，不能代替完整精度对照。

**已测同套适配曾将 `17 + 25` 回答为 `52`，当时 transport 通过、quality 失败。** 本文未修复此生成问题，新容器仍失败时原样记录，不降低预期，也不只用 HTTP 200 宣称成功。`set -e` 会使失败结束当前记录 shell，但错误和 JSON 已保存，可重新进入容器查看。

完成后在终端 A 按 Ctrl+C 停止自己启动的服务。不要批量 kill 或启动第二个服务抢同一张卡。

## 12. 容器内：保存环境指纹与结果

服务停止后执行：

```bash
source /workspace/repro/env.sh
export SNAPSHOT_DIR="$(mktemp -d "$REPRO_ROOT/results/environment-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")"
run_step snapshot bash -c '
  set -e
  python -VV > "$SNAPSHOT_DIR/python-version.txt"
  python -m pip list --format=json > "$SNAPSHOT_DIR/python-packages.json"
  git -C "$REPO_DIR" rev-parse HEAD > "$SNAPSHOT_DIR/plugin-commit.txt"
  git -C "$REPRO_ROOT/src/vllm" rev-parse HEAD > "$SNAPSHOT_DIR/vllm-commit.txt"
  git -C "$FLAGCX_PATH" rev-parse HEAD > "$SNAPSHOT_DIR/flagcx-commit.txt"
  sha256sum "$FLAGCX_PATH/build/lib/libflagcx.so" > "$SNAPSHOT_DIR/flagcx-library.sha256"
  sha256sum /models/Qwen3-4B/config.json > "$SNAPSHOT_DIR/model-config.sha256"
  python -m pip check > "$SNAPSHOT_DIR/pip-check.txt" 2>&1 && status=0 || status=$?
  printf "%s\n" "$status" > "$SNAPSHOT_DIR/pip-check-exit-code.txt"
  cat "$SNAPSHOT_DIR/pip-check.txt"
  echo "PIP_CHECK_EXIT_CODE=$status (saved independently)"
'
```

快照只是保存指纹，内部 `pip check` 退出码独立记录，不能把快照成功当作依赖检查成功。包清单也不是跨硬件的通用 requirements。

需要完整模型校验值时，容器内执行只读扫描；大模型会花时间：

```bash
run_step model-hashes bash -c 'set -euo pipefail; cd /models/Qwen3-4B; find -L . -type f -print0 | sort -z | xargs -0 sha256sum > "$SNAPSHOT_DIR/model-files.sha256"'
```

最终保留 `/workspace/repro/logs` 和 `results`：Docker 原始输出、会话记录、每步命令/输出/退出码、包版本、源码提交、通信结果、生成结果和 API 原始 JSON。未执行写“未测试”，失败写具体错误。不要将模型权重、密码或令牌放进结果仓库。

## 13. 遇到错误时先看什么

| 现象 | 定位与处理 |
| --- | --- |
| Docker 拉取或挂载失败 | 保留终端错误；确认镜像权限及本机真实路径，未建好容器不继续 |
| 缺少 `libixthunk.so` | 第 4 节同版驱动包仅解包，source env.sh，检查 LD_LIBRARY_PATH 和 ldd |
| GPU 不可用 | 先检查设备访问、同版用户态库及选择的卡，不先改模型代码 |
| NumPy 桥接失败 | 核对 NumPy 1.26.4 和厂商 torch，不随意卸载镜像全局包 |
| 导入 vLLM 0.28 | 核对 `vllm.__file__`，清理 PYTHONPATH，按第 6 节普通安装到 venv |
| `vllm._C` 警告 | EMPTY 无 NVIDIA 扩展；看实际异常，确认 `VLLM_PLUGINS=fl` 及 iluvatar |
| FlagCX 可 import 但双卡失败 | 检查真实 `.so`、wrapper、ldd 及 AllReduce，不以 Gloo 成功代替 |
| torchrun 等待 hostname | 使用 venv Python 和第 8 节显式 127.0.0.1 static rendezvous |
| 首次启动慢或 graph OOM | 看日志是否推进，核对空闲卡、0.65 预算和本文配置，保留失败，不叠加启动 |
| 回答错误 | 保存模型哈希、模式、原始问题和回答，链路通过与精度失败分别登记 |

本文只在这台机器新建文本测试环境，不运行图片、OCR、混合请求或大模型门禁，也不把已有精度问题写成已解决。
