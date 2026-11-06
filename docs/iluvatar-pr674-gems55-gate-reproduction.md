# PR #674：27B / 35B 图文 gate 复现与新容器搭建

更新日期：2026-11-07。本文以 PR #674 的固定提交 `7a94aeec80fbb795d5596569eb7d40cfe5460106` 为对象，复现 vLLM 0.32、FlagGems 5.5.0.dev0、最新一轮实测 FlagGems-vllm 的文本、图片及混合并发测试。

这是环境搭建和测试教程。历史命令流水、排错过程中失败的命令及旧版驱动绕过方法不属于主线。

## 1. 测试对象与已知边界

| 对象 | 固定值 |
| --- | --- |
| 硬件 | 4 张空闲 Iluvatar BI-V150，每卡 32 GiB |
| CoreX / PyTorch | 驱动 4.5.0；`torch==2.10.0+corex.4.5.0` |
| Python | 3.12；实测 3.12.11 |
| vLLM | `0.32.0+empty`，上游 `v0.32.0` 源码，EMPTY 构建 |
| 插件 | 上游 PR #674，提交 `7a94aeec80fbb795d5596569eb7d40cfe5460106` |
| FlagTree | `0.7.0+iluvatar3.6`，提供带 iluvatar 后端的 Triton |
| FlagGems | `5.5.0.dev0`；tag `v5.5.0.dev0`，提交 `2bcfe2656dad0b654077fcfe7d66e6a93542afab` |
| FlagGems-vllm | `0.3.0.dev1`，提交 `b434eafb1715849d1019ddcd480c5fc39461665c` |
| FlagCX | 提交 `6143384797219733aee89bd3118b2cb184ad4959` |
| 模型 | `Qwen3.6-27B`、`Qwen3.6-35B-A3B`；后者是 MoE，不是 Qwen3.5-35B |
| 并行和上下文 | TP=4，BF16，`max_model_len=32768` |
| 算子排除 | `VLLM_FL_FLAGOS_BLACKLIST_APPEND=slice,mm,mm_out` |
| Graph 参数 | `--compilation-config '{"cudagraph_capture_sizes":[1,2,4,8,16,32]}'` |
| Eager 参数 | `--enforce-eager` |

普通 Python 依赖的实测版本单独保存在 [observed-python-pins.txt](../tools/gate-repro-20261107/observed-python-pins.txt)。这份列表用于保持本次 gate 环境，**不是符合上游所有依赖声明的通用 requirements**。

实际测试环境的 `pip check` 存在已知冲突，例如 transformers 5.14.1 / tokenizers 0.22.2 低于 vLLM 0.32 的声明、xgrammar 0.2.3 不等于声明的 0.2.8、缺少 oss-harmony，以及使用 FlagTree 提供 Triton 而非独立 `triton` distribution。完整输出随测试证据归档。不能将本次 gate 通过写成“所有依赖无冲突”，也不能将这些版本组合推广到结构化输出、其他模型或所有 vLLM 功能。

新 venv 重新安装该插件提交后，安装元数据还报告 `modelscope==1.35.3` 与继承的 `1.39.1` 不符；本轮模型从本地读取，没有执行 ModelScope 下载功能。两份 `pip-check.txt` 分别保留原环境和新 venv 的输出，不能把二者当成完全相同的包元数据。原环境通过 `PYTHONPATH` 使用新提交，原已安装插件的版本元数据仍可能是旧值；因此以实际模块路径和 Git SHA 核对源码，不能仅看插件包版本字符串。

### 软件来自哪里

- 镜像提供 CoreX 用户态运行时、厂商 PyTorch 和大量 Python 依赖；镜像名字中的 vLLM 0.28、FlagGems 5.3.5 不代表本文最终测试版本。
- vLLM 0.32、FlagTree 0.7、FlagGems 5.5 和 FlagGems-vllm 固定源码需要按下文安装到隔离 venv；不能只拉镜像就当作升级完成。
- PR 是插件源码和适配逻辑，不内嵌上述项目的完整安装包。
- 当前 PR 提交的 `.github/scripts/install_flaggems_vllm.py` 仍固定旧的 `b5c2c224...`；`.github/scripts/iluvatar/verify_stack.py` 仍断言 FlagGems 5.3.5。本文新版本测试路径不运行这两个旧锁定脚本，使用本文配套安装与检查脚本。

## 2. 新机器上只需先修改这些值

以下宿主机路径是例子，必须换成该机器的实际位置：

```bash
export REPRO_HOST_ROOT=/data/fl-gate-repro
export MODEL_HOST_ROOT=/data/models
export REPRO_DEVICES=2,3,4,5
```

要求 `$MODEL_HOST_ROOT` 下已经有 `Qwen3.6-27B` 和 `Qwen3.6-35B-A3B` 两个完整模型目录。不要把只有 config/tokenizer、缺少权重的目录当作完整模型。权重不随本仓库分发。

模型官方标识分别为 `Qwen/Qwen3.6-27B`、`Qwen/Qwen3.6-35B-A3B`。本轮复用已有共享盘文件，未建立其原始下载 revision，因此不能把未来从 main 下载的权重直接称为同一份字节。随证据提供了 [模型元数据指纹及权重分片大小](../records/iluvatar-pr674-gems55-20261107/model-fingerprints.json)，用于比较 config、tokenizer 配置、预处理器、chat template 和权重索引；未计算全部权重 SHA256，指纹相同仍不等于证明所有权重字节一致。

| 项目 | 目标机器如何处理 |
| --- | --- |
| 卡号 `2,3,4,5` | 用 `ixsmi` 选择 4 张空闲卡；CUDA/CoreX 两个可见卡变量保持一致 |
| 模型和工作目录 | 只改宿主机变量；容器内统一为 `/models`、`/repro` |
| FlagCX 目录 | 有同提交且能加载的库就复用；否则在新容器编译 |
| 端口 8145 | 容器内被占用时 `export PORT=其他空闲端口`；无需固定 8132 |
| 网络代理 | 仅在目标机器确实需要时配置；主线不使用 gh-proxy、不改全局 Git URL |
| CoreX 安装位置 | 主线假定镜像内 `/usr/local/corex` 和 `/usr/local/openmpi`；不同镜像需改动态库路径并重新检查 |
| 少于 4 张卡或显存更小 | 不属于本轮 TP4 验证条件；不能直接引用本轮结果 |

## 3. 宿主机：创建没有驱动问题的新容器

这一节在宿主机执行，Docker 不要求安装在容器里。

```bash
ixsmi
docker version
mkdir -p "$REPRO_HOST_ROOT"
test -d "$MODEL_HOST_ROOT/Qwen3.6-27B"
test -d "$MODEL_HOST_ROOT/Qwen3.6-35B-A3B"

export IMAGE=harbor.baai.ac.cn/plugin/vllm-plugin-fl@sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18
docker pull "$IMAGE"
git clone --depth 1 --filter=blob:none --sparse https://github.com/zz774ever/tianshu.git "$REPRO_HOST_ROOT/guide"
git -C "$REPRO_HOST_ROOT/guide" sparse-checkout set tools/gate-repro-20261107

docker run --shm-size=32g -dit \
  --name fl-gate-gems55 \
  --privileged \
  --mount type=bind,src=/dev,dst=/dev \
  --mount "type=bind,src=$REPRO_HOST_ROOT,dst=/repro" \
  --mount "type=bind,src=$MODEL_HOST_ROOT,dst=/models,readonly" \
  -e REPRO_ROOT=/repro \
  -e REPRO_DEVICES="$REPRO_DEVICES" \
  --entrypoint /bin/bash \
  "$IMAGE"

docker exec -it fl-gate-gems55 bash
```

镜像需要认证时，在 `docker pull` 前按仓库权限执行 `docker login harbor.baai.ac.cn`。稀疏拉取只下载本教程工具，避免下载大型历史命令档案。`guide` 已存在时用 `git -C "$REPRO_HOST_ROOT/guide" pull --ff-only` 并确认稀疏目录包含 `tools/gate-repro-20261107`，不要重复 clone。

本例客户端和服务均在同一容器内，服务监听 `127.0.0.1`，所以不需要 `--net=host`、`-p`、`--pid=host`。本例也不需要 `/usr/src`、`/lib/modules`、宿主驱动文件挂载；`--privileged` 已包含原来另写 `--cap-add=ALL` 的权限。使用 `--shm-size=32g`，无需叠加会改变共享内存来源的 `--ipc=host`。

### 驱动已经正常时，不执行历史修复

进入容器后先检查：

```bash
export CUDA_VISIBLE_DEVICES="$REPRO_DEVICES"
export COREX_VISIBLE_DEVICES="$REPRO_DEVICES"
export LD_LIBRARY_PATH="/usr/local/corex/lib64:/usr/local/openmpi/lib:/usr/local/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
unset PYTHONPATH
python3 - <<'PY'
from importlib import metadata
import torch
assert metadata.version('torch') == '2.10.0+corex.4.5.0'
assert torch.cuda.is_available() and torch.cuda.device_count() == 4
for index in range(4):
    assert torch.ones(1, device=f'cuda:{index}').cpu().item() == 1
print('BASE_RUNTIME_PASS')
PY
```

此项通过的新容器，**不需要**下载驱动 deb、解压到 `/workspace/driver-extracted`、替换 `libcuda.so.1`、创建历史驱动软链接或挂载旧服务器的特定驱动文件。若未通过，应先按该机器的实际错误修复厂商运行时，不能继续声称“没有驱动问题”。宿主驱动版本不同或镜像用户态不兼容时，请使用匹配的厂商部署方法，不要盲目复制旧机器修复。

版本使用 `importlib.metadata.version('torch')` 核对；厂商包的 `torch.__version__` 在本机只显示 `2.10.0`，不能依靠它判断 `+corex.4.5.0` 安装来源。

`libmpi.so.40` 找不到属于动态库搜索路径问题，先检查 `/usr/local/openmpi/lib` 是否存在并加入路径；它不能通过安装一个普通 PyPI 包代替。

## 4. 容器内：一次安装固定的软件栈

镜像已有 git、curl、make、C++ 编译器、Python venv 和 CoreX SDK 时直接继续。确实缺少基础工具时，才在该 Debian/Ubuntu 镜像安装对应工具；无须无条件重装所有工具。

仅缺少这些工具时，在容器内以 root 执行：

```bash
apt-get update
apt-get install -y --no-install-recommends git curl ca-certificates build-essential pkg-config python3-venv
```

CoreX SDK 来自配套镜像，不能用上述通用系统包替代。

```bash
export REPRO_ROOT=/repro
bash /repro/guide/tools/gate-repro-20261107/install-stack.sh
```

脚本完整源码在 [install-stack.sh](../tools/gate-repro-20261107/install-stack.sh)，依次执行：

1. 建立 `/repro/venv`，使用 `--system-site-packages` 继承镜像内的 CoreX PyTorch；清除烘焙的 `PYTHONPATH`，防止旧 vLLM 覆盖 venv。
2. 将关键普通 Python 包保持为本轮观察到的版本，以 `--no-deps` 避免解析器替换厂商 PyTorch、Triton、NumPy。另将同版本 pytest 安装进 venv，确保原始 `run_test.sh` 中的 `pytest` 命令使用 venv 解释器；仅继承系统包会保留系统 pytest 的 shebang。基础镜像继续提供未列出的传递依赖，因此不同基础镜像仍须检查。
3. 安装带 SHA256 校验的天数 FlagTree 0.7 wheel。FlagTree 提供 `import triton`，不再安装通用 PyPI Triton。
4. 下载并校验 vLLM 0.32.0 归档，使用 `VLLM_TARGET_DEVICE=empty VLLM_VERSION_OVERRIDE=0.32.0+empty` 构建，保留 `--no-build-isolation --no-deps`。显式写 `+empty` 保持本次安装元数据；仅覆盖为 `0.32.0` 时该构建不会自动追加这个后缀。
5. 下载并校验 FlagGems v5.5.0.dev0，以构建隔离安装它的匹配 setuptools 构建依赖；`--no-deps` 保留运行时栈。源码归档使用 `SETUPTOOLS_SCM_PRETEND_VERSION=5.5.0.dev0` 明确版本。
6. 下载并校验 FlagGems-vllm 固定提交，以 `--no-deps --no-build-isolation` 安装；不再随后执行安装旧 helper 的脚本。
7. 精确 fetch 插件提交 `7a94aee...`，安装 editable 插件，验证核心版本。

归档、源码和校验值均留在 `/repro/downloads`、`/repro/src`。下载失败先处理目标机器的网络；已经校验通过的归档可离线复制到 `downloads`，脚本会直接复用。不要删除 SHA256 检查绕过内容不匹配。

不要在完成后再执行不受约束的 `pip install -U`、`pip install vllm`、`pip install 'flag-gems[iluvatar]'` 或 `pip install triton`。FlagGems 该提交的 iluvatar extra 指向另一套 CoreX/PyTorch 版本，不是本轮 CoreX 4.5/PyTorch 2.10 组合。

## 5. FlagCX：复用和编译二选一

### A. 目标机器已有相同版本的 FlagCX

创建容器时额外把该机器的 FlagCX 根目录挂入容器，例如 `--mount type=bind,src=/目标机器/FlagCX,dst=/flagcx,readonly`。进入后：

```bash
export FLAGCX_PATH=/flagcx
git -C "$FLAGCX_PATH" rev-parse HEAD
test -f "$FLAGCX_PATH/build/lib/libflagcx.so"
test -f "$FLAGCX_PATH/plugin/interservice/flagcx_wrapper.py"
```

提交应与表中一致，后续 `ctypes.CDLL` 检查必须通过。原服务器的 `/mnt/share/user_homes/iluv/FlagCX` 不是通用路径，不存在时不能照抄。

### B. 新容器没有 FlagCX：编译一次

```bash
git clone https://github.com/flagos-ai/FlagCX.git /repro/src/FlagCX
git -C /repro/src/FlagCX checkout --detach 6143384797219733aee89bd3118b2cb184ad4959
git -C /repro/src/FlagCX submodule update --init --depth 1 third-party/json
export FLAGCX_PATH=/repro/src/FlagCX
make -C "$FLAGCX_PATH" -j4 USE_ILUVATAR_COREX=1 \
  DEVICE_HOME=/usr/local/corex CCL_HOME=/usr/local/corex
```

需要镜像内已有 CoreX 开发头文件、编译器和 NCCL 兼容库。不是安装 NVIDIA NCCL，也不是安装一个同名 Python 包。新容器编译得到的二进制必须在目标机器完成下面的动态库加载与 TP4 模型测试后才算验收。

## 6. 激活并核对实际导入和算子排除

```bash
source /repro/guide/tools/gate-repro-20261107/activate.sh
python /repro/guide/tools/gate-repro-20261107/verify-env.py --model /models/Qwen3.6-27B
python /repro/guide/tools/gate-repro-20261107/verify-env.py --model /models/Qwen3.6-35B-A3B
```

`activate.sh` 尊重已设置的 `FLAGCX_PATH` 和 `REPRO_DEVICES`；默认只用于本文 `/repro` 布局。它明确指定当前插件源码为 `PYTHONPATH`，不追加旧插件或全局 site-packages。

以后重新 `docker exec` 进入容器，只需重新 source 此文件，不需要重复安装。选择 FlagCX 复用方案 A 的新 shell 需先重新 `export FLAGCX_PATH=/flagcx`；方案 B 使用默认 `/repro/src/FlagCX`。

其中 `PYTHONUNBUFFERED`、禁止生成 pyc、关闭 pytest 缓存只是日志和目录管理选项，不是硬件适配要求。`NO_PROXY` 用于确保本机测试流量不被网络代理转发；目标机器完全没有代理时不影响结果。服务和请求超时用于首次编译等待，不是提高精度或修复算子的开关。

检查脚本核对真实版本、真实模块路径、FlagTree 对 Triton 的归属、4 张可见卡、各卡实际分配及回传、NumPy 转换、FlagCX wrapper/动态库、模型处理器和权重文件，以及 bool slice / 非对齐 K 的 mm 和 mm.out 排除是否生效。

`PREFLIGHT_PASS` 只代表预检查通过，**不代表模型 gate 已通过**。

```bash
python -m pip check > /repro/results/pip-check.txt 2>&1 || true
python -m pytest -v -p no:cacheprovider \
  "$PLUGIN_ROOT/tests/unit_tests/test_iluvatar_mrope.py"
```

`pip check` 单独保存并人工核对第 1 节的已知冲突；不能通过删除声明或静默升级全部依赖把它冒充修复。出现已知列表之外的新冲突，需要先分析目标环境差异。

## 7. 依次运行四轮完整 gate

先确保选定四张卡没有其他模型服务。本轮脚本每次检查端口、启动自己的服务、等待自己进程就绪、执行原始 `run_test.sh`、校验五个场景共 26 个请求，然后停止本轮服务。四轮顺序执行，不并行占用同一组卡。

```bash
bash /repro/guide/tools/gate-repro-20261107/run-one.sh graph /models/Qwen3.6-27B
bash /repro/guide/tools/gate-repro-20261107/run-one.sh eager /models/Qwen3.6-27B
bash /repro/guide/tools/gate-repro-20261107/run-one.sh graph /models/Qwen3.6-35B-A3B
bash /repro/guide/tools/gate-repro-20261107/run-one.sh eager /models/Qwen3.6-35B-A3B
```

每条命令结束都应显示 `exit=0`；失败时先查看该轮日志，再决定是否继续。服务首次编译可能需要数分钟，不能因为终端暂时没输出就中断。另开终端查看时：

```bash
docker exec -it fl-gate-gems55 bash
ls -dt /repro/results/*
```

选择要观察的结果目录，再 `tail -f 该目录/server.log` 或 `tail -f 该目录/tests.log`。不要在等待期间修改正在运行的 shell 脚本，也不要在同一端口另起一个服务。

### Graph 到底使用什么配置

配套 `run-one.sh` 在 graph 分支传入：

```bash
export GRAPH_COMPILATION_CONFIG='{"cudagraph_capture_sizes":[1,2,4,8,16,32]}'
bash tools/adaptation-gate-cases/run_serve_graph.sh
```

原脚本将该环境变量转换为用户要求的 `--compilation-config` 参数。实际引擎使用 mode 3 编译和 `FULL_AND_PIECEWISE`；不是历史 mode 0 或 `FULL_DECODE_ONLY` 的规避路径。

M-RoPE 默认使用修复后的 `opaque-v1`；不要设置 `VLLM_FL_ILUVATAR_MROPE_IMPL=native`。每轮使用独立缓存目录，正常启用缓存，避免加载旧故障代码的编译产物。

### 显存设置的特别说明

**原始 gate 服务脚本不读取 `GPU_MEMORY_UTILIZATION` 环境变量。** 单纯执行 `export GPU_MEMORY_UTILIZATION=0.70` 不会改变该脚本启动的服务。本轮未通过 CLI 指定显存比例，沿用 vLLM 默认 0.92。

其他机器确需降低占用时，应在明确记录配置变化后给 `vllm serve` 增加 `--gpu-memory-utilization`，或在自己的脚本显式传入该参数；这属于另一组测试配置，不能仍称完全复现本文条件。先保证所选 GPU 没有其他进程，再分析 OOM。

## 8. 什么结果才算通过

| 场景 | 请求数 | 验收内容 |
| --- | --- | --- |
| `text_single` | 1 | 长文本生成和语义检查 |
| `text_concurrent_8` | 8 | 并发文本请求 |
| `image_single` | 1 | 单图识别/文字理解 |
| `image_concurrent_8` | 8 | 并发图片请求 |
| `mixed_concurrent_8` | 8 | 文本与图片混合并发 |
| 单轮合计 | 26 | 5 个 pytest 场景、26 个请求全部通过 |
| 两模型两模式 | 104 | 4 轮分别通过；不能只汇总成功请求掩盖失败轮次 |

每轮目录包含 `server.log`、`tests.log`、服务 PID、提交 SHA、配置、退出码、`summary.json` 和 `results/模型名/port-端口/*.json`。看服务 `200 OK` 或只看 graph 捕获成功不足以验收，必须检查 JSON 的 `passed_count == request_count` 和脚本退出码。

`summary.json` 表示本轮五个场景的 JSON 数量和成功数已经再次核对；`exit-code.txt` 为运行及汇总校验的最终退出码。中断的轮次可能缺少完成文件，不得按通过统计。

## 9. 当前测试容器的真实情况与移植区别

| 本轮实际使用 | 新机器的处理 |
| --- | --- |
| `/workspace/envs/iluvatar-gate-gems55-20261106` | 新建 `/repro/venv`；不复制 venv，避免绝对 shebang 和动态库路径失效 |
| `/workspace/pr674-retest-7a94aee-20261106-2328` | 新拉 `/repro/src/vllm-plugin-FL` 的相同提交；不需要该历史目录名 |
| 物理 GPU `4,5,6,7` | 按目标机器选空闲四卡；本教程示例 `2,3,4,5` |
| `/mnt/share/user_homes/models` | 宿主模型目录挂到 `/models:ro` |
| `/mnt/share/user_homes/iluv/FlagCX` | 可加载的同提交库复用，或新编译 `/repro/src/FlagCX` |
| 模型来源 CEPH 共享盘 | 本地盘/其他共享盘均可，读取耗时会变；必须有相同完整模型文件 |
| 历史容器曾进行驱动库修复 | 新容器预检查正常就省略；不引入 `driver-extracted` 路径 |
| 旧环境继承了全局 `PYTHONPATH` | 每次激活覆盖为唯一插件源码路径；避免 import 旧插件 |
| 多层重复 `LD_LIBRARY_PATH` | 新激活脚本只补必要 CoreX、MPI、FlagCX 和 `/usr/local/lib`，不要求复制历史重复值 |
| GitHub 代理和历史网络补丁 | 目标网络能直连则不需要；不写入全局 Git URL 配置 |

`slice,mm,mm_out` 不是“这台机器路径不一样”造成的设置：当前版本组合已观察到 bool slice 不支持、特定 mm 路径计算错误，因此本文保留它们。不能因为另一台机器驱动正常就去掉这些排除项。去掉需要另外执行算子与完整 gate 对照。

插件已经内置的编译分区、图像编码器 graph 限制、FlagCX CUDA communicator 和 M-RoPE 修复从相同提交导入，不需要在新机器手工重复 patch。

## 10. 更新 PR 后如何复测

先结束自己的服务，确保没有未提交修改，再在新机执行：

```bash
cd "$PLUGIN_ROOT"
git fetch origin refs/pull/674/head
git checkout --detach FETCH_HEAD
git rev-parse HEAD
python -m pip install --no-build-isolation --no-deps -e .
export EXPECTED_PLUGIN_COMMIT=$(git rev-parse HEAD)
```

然后重新执行第 6 节和第 7 节，保留新的提交 SHA 与结果目录。配套 runner 默认锁定本文提交；只有明确测试新提交时才设置 `EXPECTED_PLUGIN_COMMIT`。拉取插件不会自动把 FlagGems/FlagGems-vllm 更新到任意最新版本。若新提交要求更新依赖，需要单独固定并记录其提交，再完整复测。

## 11. 实测结果与验证范围

27B 已于 2026-11-06 在上述固定提交完成 Graph/Eager，各 26/26 通过；新增 M-RoPE 单元测试 10/10，通过原失败长文本两次正常结束、各 309 个合法 token 且序列一致。

35B 于 2026-11-07 完成 Graph/Eager，各 26/26 通过。因此同提交、同依赖、同算子排除配置下，两模型两模式合计 **104/104 请求、20/20 场景通过**。完整结果、环境与日志见 [本轮证据索引](../records/iluvatar-pr674-gems55-20261107/README.md)。

教程安装脚本在同一容器的另一独立 venv 实际执行：重新安装固定栈、预检查通过、10 项 M-RoPE 单测通过，并通过配套 runner 完成额外一轮 27B Eager gate，26/26。该轮服务使用新 venv，已启动的 gate 客户端因 shell 命令缓存沿用系统 pytest；交付安装器已补齐 venv pytest 入口，并另行核对其调用。这个额外安装验证不重复计入上面的 104 请求。

本文的宿主 Docker 命令是为**驱动已经正常的其他天数机器**整理的部署步骤；当前执行容器没有 Docker CLI，本次没有在另一台空白机器完整执行 `docker pull/run` 和重装。因此不会把新机器安装方案写成已经实机全链路验证。配套检查脚本会在目标机验证基础条件，最终仍须该机四轮 gate 全通过。

功能 gate 不能替代 NVIDIA 基准精度对齐，也不代表所有模型、驱动、长期稳定性或完整上游 CI 已通过。

## 12. 常见误判与最短处理方法

| 现象 | 检查与处理 |
| --- | --- |
| `tools/adaptation-gate-cases` 不存在 | `git rev-parse HEAD` 与 `vllm_fl.__file__`；通常进入了另一个旧 checkout，不先重复装依赖 |
| 装了新 vLLM，导入仍为 0.28 | 检查 `sys.executable`、`vllm.__file__`、`PYTHONPATH`；重新 source 本文 activate.sh |
| PyTorch 只显示 2.10.0 | 查安装元数据；本机厂商后缀没有完整出现在 `torch.__version__` |
| EMPTY 构建包显示 0.32.0、没有后缀 | 保持 `VLLM_TARGET_DEVICE=empty`，显式使用 `VLLM_VERSION_OVERRIDE=0.32.0+empty`；仅版本后缀不同不能直接断言编译设备错误 |
| 插件版本字符串为 0.0.0+g... | 浅拉取缺少标签可能影响 setuptools-scm 命名；核对实际导入目录和 Git SHA，不用包版本替代提交验证 |
| pytest 日志显示 `/usr/local/bin/python` | `--system-site-packages` 继承了系统入口；安装器已把相同版本 pytest 强制安装到 venv，检查 `command -v pytest` 和入口 shebang |
| `libmpi.so.40` / `libflagcx.so` 加载失败 | 查动态库搜索路径及 `ldd` 的 `not found`，确认 FlagCX 的源码 wrapper 和二进制两部分都存在 |
| 缺少 `vllm._C` 的启动提示 | EMPTY 构建不提供该模块；结合后续 traceback 判断，不单靠提示认定失败，也不要为消除此提示安装 NVIDIA vLLM wheel |
| bool padding mask 被 slice 拒绝 | 核对追加排除项 `slice` 是否真正生效，执行配套预检查 |
| mm 对某些 K 维度结果错误 | 保留 `mm,mm_out`，同时排除普通和 out 入口；本轮没有声称修好了所有 FlagGems 矩阵乘法路径 |
| Graph 长文本异常、空输出或词表越界 | 先确认包含 `7a94aee` 的源码、默认 M-RoPE 修复及新缓存，再保留请求和原始 token 定位；不要只降低 gate 判据 |
| 等待广播块/编译日志很久不变化 | 看 worker 是否存活、CPU/GPU 是否仍推进及日志时间；首次编译/预热可能数分钟，但达到等待上限或进程退出仍按失败处理 |
| 图片语义 gate 失败但请求 200 | 检查 JSON 的失败条件、模型/processor/tokenizer、真实依赖与启动配置；200 只表示请求成功返回，不代表图片识别正确 |

排错结果和改过的运行参数要写进本轮结果目录；不要把不同提交、不同模型文件或不同 graph 模式的通过数据混在一个“全部通过”结论里。
