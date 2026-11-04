# 教程二：官方天数镜像 → 原始环境验证 → 直接升级 vLLM 0.32 → 纯文本测试

更新：2026-11-04。适用于当前 u180 / n180 天数 BI-V150 机器。**宿主仅执行 Docker 拉取、创建、进入命令；安装和测试全部在容器内。不创建 venv，不下载教程仓库，不使用 run_step 或自定义测试客户端。终端 A 启动服务，终端 B 直接运行 OpenAI 示例或 curl，结果直接显示。**

已有容器可以从第 2 节开始，但升级过的环境不能再当成原始镜像环境。本文的系统 Python 是 `/usr/local/bin/python`；不要 source 旧教程的 `/workspace/repro/env.sh`，它会激活旧 venv。原来的 venv 无需删除。

执行顺序：原始版本及路径记录 → 驱动库检查 → vLLM 0.28 基线服务和请求 → 停服务 → 直接安装 0.32 与 PR 674 → 相同命令验证 4B → 27B/35B 文本测试。

## 1. 官方镜像与建容器：仅本节在宿主执行

镜像来自 **flagos-ai/vllm-plugin-FL 官方项目的 0.5.0-dev 分支**，不是本项目制作的镜像，也不是本次测试容器的打包产物：

- [官方 CI 配置](https://github.com/flagos-ai/vllm-plugin-FL/blob/0.5.0-dev/.github/configs/iluvatar.yml#L15) 列出标签及摘要。
- [官方天数部署说明](https://github.com/flagos-ai/vllm-plugin-FL/blob/0.5.0-dev/docs/usage/iluvatar.md#L12) 列出相同信息。

```bash
docker pull harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-iluvatar-ci
docker image inspect harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-iluvatar-ci --format '{{json .RepoDigests}}'
```

官方文档记录的摘要是 `sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18`。标签可能更新，保留本次实际 inspect 输出；不同摘要不能直接沿用本文实测结论。Harbor 拉取失败时保留原始错误，按 DNS、网络、权限或标签定位。只有提示需要鉴权时才 `docker login harbor.baai.ac.cn`，不要把凭据写入记录。

本机已经有宿主驱动和共享模型，无需安装宿主驱动、创建宿主目录或下载教程仓库。创建容器：

```bash
docker run -dit \
  --name tianshu-vllm032-text \
  --init --shm-size=32g --privileged \
  --ulimit nofile=65535:65535 \
  --mount type=bind,src=/dev,dst=/dev \
  --mount type=bind,src=/lib/modules,dst=/lib/modules,readonly \
  --mount type=bind,src=/mnt/share/user_homes,dst=/mnt/share/user_homes,readonly \
  --mount type=bind,src=/mnt/share/user_homes/models,dst=/models,readonly \
  --mount type=bind,src=/usr/local/corex-4.5.0.20260509/lib64/libcuda.so.1,dst=/usr/local/corex/lib64/libcuda.so.1,readonly \
  --mount type=bind,src=/usr/local/corex-4.5.0.20260509/lib64/libixml.so,dst=/usr/local/corex/lib64/libixml.so,readonly \
  --entrypoint /bin/bash \
  harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-iluvatar-ci

docker exec -it tianshu-vllm032-text bash
```

本机实际驱动路径带 `.20260509`，不是官方示例不带日期的目录。`--mount` 源路径不存在会报错，不自动创建宿主目录。名字已存在时进入现有容器，不删除或覆盖它。设备访问保留必要权限，模型和共享文件只读。

后文服务监听容器 `127.0.0.1:8060`；终端 B 必须进入**同一个容器**，不是创建另一个容器。不需要宿主端口映射或 host 网络。镜像和容器仍占用 Docker 存储；容器删除会丢失可写层中的源码、环境和日志。

## 2. 容器内：开始记录，展示原始环境

从这里开始，除明确标注的 docker exec，所有命令都在容器内执行。首先启动 Bash 终端记录：

```bash
mkdir -p /workspace/repro/{src,logs,results}
script -q -f -c 'bash --noprofile --norc -i' \
  "/workspace/repro/logs/setup-session-$(date -u +%Y%m%dT%H%M%SZ).log"
```

看到 `bash-...#` 提示符后再继续。必须保留显式 Bash；否则 script 可能启动 sh，出现 `source: not found` 或 `Illegal option -o pipefail`。只复制代码块，不复制提示符。heredoc 结束的 `PY` / `SH` 必须单独一行且顶格，Python 顶层代码也不要整体缩进。

```bash
export REPRO_ROOT=/workspace/repro
export PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
unset VIRTUAL_ENV PYTHONHOME PYTHONPATH VLLM_VENDOR
export PYTHONNOUSERSITE=1
set -o pipefail
command -v python pip vllm
python -VV
python -m pip --version
python -m pip list --format=json > "$REPRO_ROOT/logs/original-packages.json"
python - <<'PY' 2>&1 | tee "$REPRO_ROOT/logs/original-environment.log"
import os
import sys
from importlib import metadata
print('Python:', sys.executable, sys.version)
print('prefix:', sys.prefix, 'base_prefix:', sys.base_prefix)
assert sys.prefix == sys.base_prefix, '当前仍在 venv，请用本节 PATH/清理命令恢复系统 Python'
for name in ('vllm', 'vllm-plugin-fl', 'torch', 'flagtree', 'flag-gems',
             'numpy', 'transformers', 'tokenizers', 'openai', 'flaggems-vllm'):
    try:
        package = metadata.distribution(name)
        print(name, package.version, package._path)
    except metadata.PackageNotFoundError:
        print(name, 'NOT_INSTALLED')
print('LD_LIBRARY_PATH:', os.environ.get('LD_LIBRARY_PATH'))
PY
printf 'ORIGINAL_ENV_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

镜像摘要对应的本机原始系统环境实测：Python 3.12.11、vLLM `0.28.0+empty`、插件 `0.3.0rc0+g13eb9be69`、torch distribution `2.10.0+corex.4.5.0`、FlagTree `0.6.2a3+iluvatar3.6`、FlagGems `5.3.5`、NumPy `1.26.4`、OpenAI `2.46.0`；系统 Python 未安装 FlagGems-vllm。以你这次输出为准。这里只读取包元数据，不要求先成功 import torch。

本机 Qwen3-4B 实际路径是 `/models/Qwen3-4B`。历史参考 `/mnt/share/user_homes/zyp/models/Qwen/Qwen3-4B/` 在本机不存在，不能照抄。27B、35B 路径也只读复用：

```bash
test -f /models/Qwen3-4B/config.json && echo QWEN3_4B_FOUND
test -f /models/Qwen3.6-27B/config.json && echo QWEN36_27B_FOUND
test -f /models/Qwen3.6-35B-A3B/config.json && echo QWEN36_35B_FOUND
```

拉镜像、建容器的命令及原始输出也应留存。它们发生在 session 记录之前，可以从宿主终端复制到容器内编辑保存；这只是补录日志，不影响搭建，不要求运行一个等待输入的 cat。

## 3. 容器内：设备与驱动依赖检查，不安装驱动

```bash
if command -v ixsmi >/dev/null; then ixsmi; else nvidia-smi; fi
ldd /usr/local/corex/lib64/libcuda.so.1 2>&1 | tee "$REPRO_ROOT/logs/libcuda-before.log"
```

8、9、10、11 是旧参考卡号。本轮检查这些卡已有其他任务，0、1、2、3 空闲，因此本文使用 0–3；执行时再确认，不终止其他人的任务。

如果 `ldd` 没有 `not found`，跳过下面修复代码。如果明确缺少 `libixthunk.so`，执行下面的**容器内用户态依赖补齐**。原因是本机挂载的 libcuda 还依赖该库，而官方两个库的示例挂载未覆盖它；不是要求更换宿主驱动。

```bash
export DRIVER_PACKAGE=/mnt/share/user_homes/yubenjie/0509/corex-driver-linux64-4.5.0.20260509_x86_64.run
printf '%s  %s\n' \
  710468ef4434b5dfafc684e6160fffbbe49c7f3068af3089c86d04c8366b5626 \
  "$DRIVER_PACKAGE" | sha256sum -c -
```

校验必须为 OK。尚未解包才执行：

```bash
if [ ! -f "$REPRO_ROOT/driver-extracted/corex/lib64/libixthunk.so" ]; then
  bash "$DRIVER_PACKAGE" --noexec --target "$REPRO_ROOT/driver-extracted" \
    2>&1 | tee "$REPRO_ROOT/logs/driver-userspace-extract.log"
  printf 'EXTRACT_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
fi
export LD_LIBRARY_PATH="$REPRO_ROOT/driver-extracted/corex/lib64:/usr/local/corex/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
ldd /usr/local/corex/lib64/libcuda.so.1
```

确认不再有 `not found`。`--noexec` 不执行安装器，不改宿主驱动；只读模型和共享材料保持不变。本机挂载与解包的 libcuda SHA256 均为 `6cf92e5c9112ab657af07076b29446c8210590cd46062111c60f8e367200a35f`。另一台机器需对应的驱动材料，不能套用这份包。

为以后每个终端保存相同环境，只做环境变量设置，不激活 venv：

```bash
cat > "$REPRO_ROOT/env-direct.sh" <<'SH'
export REPRO_ROOT=/workspace/repro
export REPO_DIR="$REPRO_ROOT/src/vllm-plugin-FL"
export PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
unset VIRTUAL_ENV PYTHONHOME PYTHONPATH VLLM_VENDOR
export PYTHONNOUSERSITE=1
export GIT_CONFIG_GLOBAL="$REPRO_ROOT/gitconfig"
export FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX
export LD_LIBRARY_PATH="$FLAGCX_PATH/build/lib:/usr/local/corex/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if [ -f "$REPRO_ROOT/driver-extracted/corex/lib64/libixthunk.so" ]; then
  export LD_LIBRARY_PATH="$REPRO_ROOT/driver-extracted/corex/lib64:$LD_LIBRARY_PATH"
fi
export CUDA_VISIBLE_DEVICES="${REPRO_DEVICES:-0,1,2,3}"
export COREX_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES"
export VLLM_PLUGINS=fl
export USE_FLAGGEMS=1
export GEMS_VENDOR=iluvatar
export VLLM_ENGINE_ITERATION_TIMEOUT_S=36000
export VLLM_RPC_TIMEOUT=36000000
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3600
export XDG_CACHE_HOME="$REPRO_ROOT/cache"
export TRITON_CACHE_DIR="$REPRO_ROOT/cache/triton"
export HF_HOME="$REPRO_ROOT/cache/huggingface"
export VLLM_CACHE_ROOT="$REPRO_ROOT/cache/vllm"
SH
export REPRO_DEVICES=0,1,2,3
source "$REPRO_ROOT/env-direct.sh"
python - <<'PY'
import torch
print('torch:', torch.__version__, torch.__file__)
assert torch.cuda.is_available()
for device in range(torch.cuda.device_count()):
    free, total = torch.cuda.mem_get_info(device)
    print(device, torch.cuda.get_device_name(device), 'free GiB:', round(free / 2**30, 2))
assert (torch.ones(4, device='cuda') + 2).cpu().tolist() == [3, 3, 3, 3]
print('GPU_BASIC_PASS')
PY
```

如果出现 GPU 错误，先停在这里定位，不开始安装。env-direct.sh 中设置的两个旧超时变量按原参考保留；不保证新版本仍读取它们，不能用增大超时掩盖真实异常。

## 4. 原始环境验证：终端 A 启动 4B 服务

这是升级前测试。确认原始包版本仍是 0.28；已升级为 0.32 的容器不要降级伪造基线，使用之前保存的原始记录，或另建官方镜像容器验证。

```bash
source /workspace/repro/env-direct.sh
export CUDA_VISIBLE_DEVICES=0,1,2,3
export COREX_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES"
export VLLM_ENGINE_ITERATION_TIMEOUT_S=36000
export VLLM_RPC_TIMEOUT=36000000
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3600
vllm serve /models/Qwen3-4B/ --served-model-name qwen \
  --host 127.0.0.1 --enforce-eager --port 8060 --max-model-len 32768 \
  2>&1 | tee "$REPRO_ROOT/logs/baseline-028-server.log"
printf 'BASELINE_SERVER_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

可见四张卡不表示使用 TP4；这条命令没有 `-tp`，4B 默认 TP1。终端 A 保持运行，看到服务启动完成后再发请求。

**本轮原始系统环境实测失败**：镜像内置插件在注册时访问 `vllm.model_executor.layers.fused_moe.FusedMoE`，而原装 vLLM 0.28 没有该属性，报 AttributeError，尚未启动模型或接口。它不是驱动缺库，也不是 curl 参数问题。保留原始错误；不要修改原装源码把基线强行变绿。此时第 5 节接口验证记“服务启动失败，未通过”，再进入第 6 节验证适配后的环境。参见[本轮直接安装验证记录](../records/u180-direct-install-20261104/README.md)。

## 5. 原始环境验证：终端 B 直接执行 OpenAI 流式请求

终端 B 从宿主进入**同一个容器**：

```bash
docker exec -it tianshu-vllm032-text bash
```

以下全部在容器内。开始记录，再加载不含 venv 的环境：

```bash
script -q -f -c 'bash --noprofile --norc -i' \
  "/workspace/repro/logs/client-session-$(date -u +%Y%m%dT%H%M%SZ).log"
```

看到 Bash 提示符后执行：

```bash
source /workspace/repro/env-direct.sh
set -o pipefail
curl --noproxy '*' --connect-timeout 5 --max-time 10 --fail-with-body -sS \
  http://127.0.0.1:8060/v1/models
```

只有模型列表能返回 qwen，才运行下面的请求；连接失败先看终端 A，不静默等待半小时。

```bash
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost \
python - <<'PY' 2>&1 | tee "$REPRO_ROOT/logs/baseline-028-openai-stream.log"
from openai import OpenAI

client = OpenAI(api_key='EMPTY', base_url='http://127.0.0.1:8060/v1', timeout=300, max_retries=0)
response = client.chat.completions.create(
    model='qwen',
    messages=[{'role': 'user', 'content': 'Give me a short introduction to large language models.'}],
    max_tokens=20,
    temperature=0.7,
    top_p=0.8,
    presence_penalty=1.5,
    extra_body={'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}},
    stream=True,
)
for chunk in response:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='', flush=True)
print()
PY
printf 'BASELINE_CLIENT_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

输出直接显示在终端，同时保存在日志。如果想生成更多内容，可另一次改为 max_tokens=256 并保存新日志；原参考 20 token 只是短流式冒烟。

完成后在终端 A 按 Ctrl+C 停止服务，等待释放显存和端口，再升级。中断服务的退出码通常非零，不能记为“正常退出 0”。

## 6. 容器内直接搭建新环境，不建 venv

回到终端 A，保持 Bash 记录会话。所有 pip 操作仅修改**这个容器的系统 Python**，不修改宿主。本文使用 `python -m pip` 明确解释器，与系统 Python 下的 pip 命令等价。

### 6.1 拉取 vLLM 与官方插件 PR

```bash
source /workspace/repro/env-direct.sh
cd "$REPRO_ROOT/src"
git config --file "$GIT_CONFIG_GLOBAL" \
  url.https://gh-proxy.org/https://github.com/.insteadOf https://github.com/

git clone --depth 1 --branch v0.32.0 https://github.com/vllm-project/vllm.git vllm
git -C vllm rev-parse HEAD

git clone --branch 0.5.0-dev https://github.com/flagos-ai/vllm-plugin-FL.git vllm-plugin-FL
git -C vllm-plugin-FL fetch origin refs/pull/674/head
git -C vllm-plugin-FL checkout --detach FETCH_HEAD
git -C vllm-plugin-FL rev-parse HEAD
```

GitHub 代理仅用于公开源码，Docker 镜像仍直接使用官方 Harbor。代理慢时可换可用下载源或传入已校验 Git 源码，不能跳过提交检查。本文当前实测提交：

| 项目 | 提交 |
| --- | --- |
| vLLM tag v0.32.0 | `5df63a7203cdb9328d824a27b682e77c7b9928be` |
| PR 674 head | `c17d866e08b583f63998cbd47bc39fe3e57efce0` |

本轮直接查询官方 PR API，PR 674 仍开放、目标分支 0.5.0-dev，head 与上表一致。用 fetch + checkout 直接检出 PR，避免 `git pull origin pull/674/head` 在已有分支制造合并或因分叉策略失败。

**当前容器已有这两份源码，直接核对后跳过 clone，不重复下载：**

```bash
git -C "$REPRO_ROOT/src/vllm" rev-parse HEAD
git -C "$REPO_DIR" rev-parse HEAD
git -C "$REPO_DIR" status --short
```

已有目录不要再 clone 到同一位置。若 PR head 后续变化，记录新提交并重新测试，不能冒用本文结果。

### 6.2 构建工具与核心包指纹

```bash
python - <<'PY'
import json
import os
from importlib import metadata
from pathlib import Path
names = ('torch', 'flagtree', 'flag-gems', 'numpy')
versions = {name: metadata.version(name) for name in names}
Path(os.environ['REPRO_ROOT'], 'logs/core-before-upgrade.json').write_text(json.dumps(versions, indent=2))
print(versions)
PY
python -m pip install --no-deps \
  'setuptools==80.10.2' 'setuptools-scm==10.2.1' \
  'setuptools-rust==1.13.0' 'scikit-build-core==0.11.0' \
  'pybind11==3.1.0' 'ninja==1.13.0' 'cmake==4.4.2' \
  'packaging==26.2' 'wheel==0.48.0' \
  2>&1 | tee "$REPRO_ROOT/logs/install-build-tools.log"
printf 'BUILD_TOOLS_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

确认退出码为 0，再继续。不要普通 `pip install -U torch triton`；FlagTree 提供天数版 import triton，不能用通用 Triton 覆盖。镜像多数构建工具已经具备，本轮补充 wheel 0.48.0。

### 6.3 直接 editable 安装 vLLM 0.32 与 PR 674

```bash
cd "$REPRO_ROOT/src/vllm"
VLLM_TARGET_DEVICE=empty VLLM_VERSION_OVERRIDE=0.32.0 \
  python -m pip install -v --no-build-isolation --no-deps -e . \
  2>&1 | tee "$REPRO_ROOT/logs/install-vllm032.log"
printf 'INSTALL_VLLM_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

退出 0 后安装插件：

```bash
cd "$REPO_DIR"
python -m pip install --no-build-isolation --no-deps -e . \
  2>&1 | tee "$REPRO_ROOT/logs/install-plugin674.log"
printf 'INSTALL_PLUGIN_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

这里按你的要求在系统 Python 中 editable 安装，旧版 vLLM/插件由 pip 在容器内替换，不会影响宿主。两处 `--no-deps` 保留厂商运行时，避免解析安装上游普通 torch。`--no-build-isolation` 也避免上游构建声明中的 torch 2.13 自动进入隔离环境。插件版本可能显示 `0.0.0+gc17d866e0`，应核对源码提交，不单凭包版本字符串判断。

安装 PR 配套的辅助算子：

```bash
python "$REPO_DIR/.github/scripts/install_flaggems_vllm.py" \
  2>&1 | tee "$REPRO_ROOT/logs/install-flaggems-vllm.log"
printf 'INSTALL_FLAGGEMS_VLLM_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
hash -r
```

helper 固定 `b5c2c2249319277ccda4d41aa0f65164bd9b2a19`，检查运行时没有被替换。包元数据为 0.1.0，对应发布 v0.2.0，不算装错。

本机已经传入同版 `/workspace/repro/src/FlagGems-vllm` 源码；如外网慢，可以先检查该目录提交，然后仅对这个仓库改用本地 Git 源，再重跑 helper：

```bash
git -C "$REPRO_ROOT/src/FlagGems-vllm" rev-parse HEAD
git config --file "$GIT_CONFIG_GLOBAL" \
  url.file:///workspace/repro/src/FlagGems-vllm.insteadOf \
  https://github.com/flagos-ai/FlagGems-vllm.git
python "$REPO_DIR/.github/scripts/install_flaggems_vllm.py"
```

只有本地仓库存在且提交匹配才使用这个分支。helper 保留真实 VCS 提交校验，不手工伪造 direct_url.json。

### 6.4 核对实际导入和厂商包

```bash
source /workspace/repro/env-direct.sh
python - <<'PY' 2>&1 | tee "$REPRO_ROOT/logs/upgraded-environment.log"
import ctypes
import json
import os
import sys
from importlib import metadata
from pathlib import Path
import torch
import triton
import vllm
import vllm_fl
from vllm.platforms import current_platform
from vllm_fl.distributed.device_communicators import flagcx

assert sys.prefix == sys.base_prefix, sys.executable
assert vllm.__version__.split('+')[0] == '0.32.0', vllm.__version__
assert Path(os.environ['REPRO_ROOT'], 'src/vllm').resolve() in Path(vllm.__file__).resolve().parents
assert Path(os.environ['REPO_DIR']).resolve() in Path(vllm_fl.__file__).resolve().parents
versions = {name: metadata.version(name) for name in ('torch', 'flagtree', 'flag-gems', 'numpy')}
before = json.loads(Path(os.environ['REPRO_ROOT'], 'logs/core-before-upgrade.json').read_text())
assert versions == before, (before, versions)
assert hasattr(triton._C.libtriton, 'iluvatar')
assert current_platform.vendor_name == 'iluvatar'
assert torch.cuda.is_available()
assert (torch.ones(4, device='cuda') + 2).cpu().tolist() == [3, 3, 3, 3]
source = json.loads(metadata.distribution('flaggems-vllm').read_text('direct_url.json') or '{}')
assert source.get('vcs_info', {}).get('commit_id') == 'b5c2c2249319277ccda4d41aa0f65164bd9b2a19'
ctypes.CDLL(os.environ['FLAGCX_PATH'] + '/build/lib/libflagcx.so')
assert flagcx._flagcx_available
print('Python:', sys.executable)
print('vLLM:', vllm.__version__, vllm.__file__)
print('plugin:', vllm_fl.__file__)
print('core versions:', versions)
print('DIRECT_ENV_PASS')
PY
printf 'UPGRADED_ENV_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

本机 FlagCX 来自只读 `/mnt/share/user_homes/iluv/FlagCX`，必须有 `build/lib/libflagcx.so` 和 `plugin/interservice/flagcx_wrapper.py`。没有这些材料就不能把 TP4 当作已就绪。

## 7. 新环境验证：终端 A 使用相同 4B 启动命令

端口与模型名继续统一为 8060 / qwen，不混用参考中的 8000 和 Qwen3-8B。确认旧服务已经停止：

```bash
source /workspace/repro/env-direct.sh
export CUDA_VISIBLE_DEVICES=0,1,2,3
export COREX_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES"
export VLLM_ENGINE_ITERATION_TIMEOUT_S=36000
export VLLM_RPC_TIMEOUT=36000000
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3600
vllm serve /models/Qwen3-4B/ --served-model-name qwen \
  --host 127.0.0.1 --enforce-eager --port 8060 --max-model-len 32768 \
  2>&1 | tee "$REPRO_ROOT/logs/v032-4b-server.log"
printf 'V032_4B_SERVER_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

终端 A 保持运行，看到启动完成后在终端 B 直接请求。

## 8. 新环境验证：终端 B 直接 curl，直接看输出

终端 B 使用第 5 节进入同容器及 Bash 记录的方式，然后：

```bash
source /workspace/repro/env-direct.sh
set -o pipefail
curl --noproxy '*' --fail-with-body -sS --max-time 300 \
  http://127.0.0.1:8060/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "详细介绍下人工智能"}],
    "max_tokens": 256,
    "chat_template_kwargs": {"enable_thinking": false}
  }' | tee "$REPRO_ROOT/logs/v032-4b-curl.json"
printf '\nCURL_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

响应 JSON 直接显示，回答位于 `choices[0].message.content`。请求的 model 必须是服务声明的 qwen，不能照搬另一台机器的 `/data/nmodels/Qwen3-8B`。

这里没有设置 stream=true，所以 curl 等整段生成完成后才显示 JSON。大模型 eager 生成 256 token 可能需要几分钟；可在终端 A 查看 Running、generation throughput 和错误日志。希望边生成边看时，用第 5 节 OpenAI 流式请求，不重复启动服务。

如果需要逐字输出，用原 OpenAI 示例同样在终端 B 运行；复制第 5 节请求，将 tee 日志名改为 `v032-4b-openai-stream.log` 即可。没有自定义客户端、自动等待器或算术门禁。本轮系统 Python 直接升级实测中，这条 curl 和原 OpenAI 流式示例均退出 0，分别输出中文介绍和英文介绍，原始日志见文末记录。

curl 退出 0 表示 HTTP 请求成功；还需人工查看生成是否非空、是否合理。本次测试不等于逐 token 精度对齐。需要确认算术时可直接把问题改为“17+25等于多少，只回答数字”，保留真实输出；不要放宽预期把错误记为通过。

## 9. 27B、35B：仍然终端 A 服务、终端 B curl

先在终端 A Ctrl+C 停止 4B，确认释放显存和端口。以下每次只启动一个模型。四张卡需都空闲；35B-A3B 的 A3B 是激活参数量，不能只按 3B 估算权重显存。

```bash
export REPRO_DEVICES=0,1,2,3
source /workspace/repro/env-direct.sh
python - <<'PY'
import socket
import torch
assert torch.cuda.device_count() == 4
for device in range(4):
    free, total = torch.cuda.mem_get_info(device)
    print(device, 'free GiB:', round(free / 2**30, 2))
    assert free / 2**30 >= 30, '先停止自己的旧服务或换空闲卡'
with socket.socket() as endpoint:
    endpoint.bind(('127.0.0.1', 8060))
print('FOUR_GPUS_AND_PORT_READY')
PY
```

### 9.1 27B eager：终端 A

```bash
source /workspace/repro/env-direct.sh
vllm serve /models/Qwen3.6-27B --served-model-name qwen \
  --host 127.0.0.1 --port 8060 -tp 4 --dtype bfloat16 \
  --language-model-only --enforce-eager \
  --max-model-len 4096 --max-num-seqs 4 --max-num-batched-tokens 512 \
  --gpu-memory-utilization 0.70 \
  2>&1 | tee "$REPRO_ROOT/logs/v032-27b-eager-server.log"
printf 'SERVER_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

`--language-model-only` 是 vLLM 0.32 的参数，用于关闭多模态输入。这里只跑文本，不加载图片请求或执行图文测试脚本。

### 9.2 27B eager：终端 B

```bash
source /workspace/repro/env-direct.sh
curl --noproxy '*' --fail-with-body -sS --max-time 300 \
  http://127.0.0.1:8060/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "详细介绍下人工智能"}],
    "max_tokens": 256,
    "chat_template_kwargs": {"enable_thinking": false}
  }' | tee "$REPRO_ROOT/logs/v032-27b-eager-curl.json"
printf '\nCURL_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

### 9.3 35B-A3B eager：终端 A

先 Ctrl+C 停止 27B，确认释放卡和端口，再执行：

```bash
source /workspace/repro/env-direct.sh
vllm serve /models/Qwen3.6-35B-A3B --served-model-name qwen \
  --host 127.0.0.1 --port 8060 -tp 4 --dtype bfloat16 \
  --language-model-only --enforce-eager \
  --max-model-len 4096 --max-num-seqs 4 --max-num-batched-tokens 512 \
  --gpu-memory-utilization 0.70 \
  2>&1 | tee "$REPRO_ROOT/logs/v032-35b-eager-server.log"
printf 'SERVER_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

### 9.4 35B-A3B eager：终端 B

```bash
source /workspace/repro/env-direct.sh
curl --noproxy '*' --fail-with-body -sS --max-time 300 \
  http://127.0.0.1:8060/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "详细介绍下人工智能"}],
    "max_tokens": 256,
    "chat_template_kwargs": {"enable_thinking": false}
  }' | tee "$REPRO_ROOT/logs/v032-35b-eager-curl.json"
printf '\nCURL_EXIT_CODE=%s\n' "${PIPESTATUS[0]}"
```

27B 和 35B 分别保存自己的服务日志与 JSON。每组请求完成后，回终端 A Ctrl+C 停止服务，再启动下一组。本轮两组 eager 均实际启动并用上述 curl 返回非空中文回答、256 completion token、退出 0；finish_reason=length 表示达到此次长度上限，不表示完整长文或精度验收。各项原始结果见文末实测记录。

## 10. 收尾：保留原始结果和安装指纹

停止自己最后启动的服务，不批量 kill，不改宿主环境。容器内保存：

```bash
source /workspace/repro/env-direct.sh
python -m pip list --format=json > "$REPRO_ROOT/logs/upgraded-packages.json"
git -C "$REPRO_ROOT/src/vllm" rev-parse HEAD > "$REPRO_ROOT/logs/vllm-commit.txt"
git -C "$REPO_DIR" rev-parse HEAD > "$REPRO_ROOT/logs/plugin-commit.txt"
git -C "$FLAGCX_PATH" rev-parse HEAD > "$REPRO_ROOT/logs/flagcx-commit.txt"
sha256sum /models/Qwen3-4B/config.json /models/Qwen3.6-27B/config.json \
  /models/Qwen3.6-35B-A3B/config.json > "$REPRO_ROOT/logs/model-configs.sha256"
python -m pip check > "$REPRO_ROOT/logs/pip-check.txt" 2>&1
printf 'PIP_CHECK_EXIT_CODE=%s\n' "$?"
```

session 日志包含输入命令和终端结果；各服务、pip、OpenAI、curl 的输出另有文件。重跑时改日志名或使用新时间戳，不覆盖失败证据。使用 tee 时命令与 tee 的退出码可能不同，本文打印命令的 PIPESTATUS[0]，并保留 set -o pipefail。

原镜像继承的上层依赖与上游 0.32 声明部分不一致，pip check 可能非零；本轮没有通过随意升级 torch、Triton、Transformers 来掩盖差异。服务能生成、回答内容正确、完整依赖声明满足、性能达标是不同结论。

本轮实测的实际命令、结果与限制见[直接安装验证记录](../records/u180-direct-install-20261104/README.md)。没有执行的模型/模式写“未测试”，原始镜像失败也如实保留；教程不承诺所有生成内容正确。
