# PR674：系统 Python 新容器最小 gate 复现记录

本轮按要求新建容器，直接使用镜像的系统 Python，不创建 venv。验证范围只有插件原始 `tools/adaptation-gate-cases`：Qwen3.6-27B、Qwen3.6-35B-A3B 分别运行 Graph 和 Eager。服务启动、依赖和动态库检查属于搭建步骤；不另跑单元测试、算子测试、精度对齐或性能测试。

结果：新容器直接使用系统 Python，27B Graph/Eager、35B Graph/Eager 各模式最新测试均为 26/26，合计 104/104。首次完整四轮曾为 103/104，35B Graph 出现过一条错误回答；仅对该轮同配置复测后为 26/26，首次失败根因尚未定位。本文保留两次结果，不把复测通过写成缺陷已修复。历史容器/venv 的结果不计入这里的统计。

[实际安装和执行脚本](https://github.com/zz774ever/tianshu/tree/main/tools/minimal-gate-container-20261107) · [环境、原始请求结果和打包核验记录](https://github.com/zz774ever/tianshu/tree/main/records/minimal-gate-container-20261107)

## 1. 固定输入

| 项目 | 本轮固定版本/来源 |
| --- | --- |
| 基础镜像 | `harbor.baai.ac.cn/plugin/vllm-plugin-fl@sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18` |
| vLLM | tag `v0.32.0`，以 `VLLM_TARGET_DEVICE=empty` 安装为 `0.32.0+empty` |
| PyTorch | 基础镜像的 `2.10.0+corex.4.5.0`，保留厂商构建 |
| 插件 | `7a94aeec80fbb795d5596569eb7d40cfe5460106` |
| FlagGems | `5.5.0.dev0`，提交 `2bcfe2656dad0b654077fcfe7d66e6a93542afab` |
| FlagGems-vllm | `b434eafb1715849d1019ddcd480c5fc39461665c`，包版本 `0.3.0.dev1` |
| FlagTree | `0.7.0+iluvatar3.6`，CPython 3.12 Linux wheel |
| FlagCX | 已编译运行库和 Python wrapper，来源提交 `6143384797219733aee89bd3118b2cb184ad4959` |

归档哈希见 `inputs/SHA256SUMS`，来源见 `inputs/provenance.json`。归档构建没有 `.git`，所以另外保存完整提交，不用包版本代替来源校验。插件的 SCM 版本标记为 `0.0.0+g7a94aeec8`。

这些输入通过已核验归档安装，不在测试时追踪会继续变化的分支 HEAD。上游来源对应：

- vLLM：`https://github.com/vllm-project/vllm/tree/v0.32.0`
- 插件：`https://github.com/flagos-ai/vllm-plugin-FL/tree/7a94aeec80fbb795d5596569eb7d40cfe5460106`
- FlagGems：`https://github.com/flagos-ai/FlagGems/tree/2bcfe2656dad0b654077fcfe7d66e6a93542afab`
- FlagGems-vllm：`https://github.com/flagos-ai/FlagGems-vllm/tree/b434eafb1715849d1019ddcd480c5fc39461665c`
- FlagTree wheel：`https://resource.flagos.net/repository/flagos-pypi-hosted/packages/flagtree/0.7.0+iluvatar3.6/flagtree-0.7.0+iluvatar3.6-cp312-cp312-linux_x86_64.whl`

GitHub 自动生成的 archive 和本轮 `git archive --prefix=vllm-plugin-FL/` 生成的插件归档压缩字节可能不同；不要拿另一种打包方式的归档套用这里的 SHA256。完整输入包包含本轮实际安装的字节。

## 2. 容器边界与打包设计

本轮机器：Linux `5.4.0-148-generic`，天数 Iluvatar BI-V150，每卡 32768 MiB，使用物理卡 `4,5,6,7`，TP=4。`ixsmi` 报 Driver Version 4.5.0、IX-ML 4.4.0。标称驱动版本相同不能替代第 9 节的具体运行库核对。

| 路径 | 放在哪里 | 打包时是否包含 |
| --- | --- | --- |
| 系统 Python 及安装包 | 容器文件系统 | 包含 |
| `/opt/vllm-plugin-FL` | 容器文件系统，插件 editable 源码和原始 gate | 包含，不能删除 |
| `/opt/FlagCX` | 容器文件系统，运行库、wrapper、LICENSE | 包含 |
| `/opt/gate` | 容器文件系统，环境脚本、执行脚本、来源信息 | 包含 |
| `/models` | 宿主模型目录只读挂载 | 不包含 |
| `/results` | 本轮结果目录挂载，包括日志、JSON 和编译缓存 | 不包含 |
| `/input` | 安装输入只读挂载 | 不包含，安装完成后运行不依赖它 |

因此不能把插件源码或 FlagCX 只安装到宿主挂载目录后就 `docker commit`：挂载内容不会进入镜像。本轮将两者实际复制到 `/opt`。

## 3. 普通宿主机创建容器

以下命令在有 Docker 的天数宿主机执行。把模型源目录改成该机器的真实位置，选择空闲的四张卡。不要在普通宿主机重复本记录末尾的独立 Docker 管理步骤。

```bash
IMAGE=harbor.baai.ac.cn/plugin/vllm-plugin-fl@sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18
docker run -dit --name fl-gate-minimal --shm-size=32g \
  --privileged --network host \
  -v /dev:/dev \
  -v /mnt/share/user_homes/models:/models:ro \
  -v "$PWD/inputs:/input:ro" \
  -v "$PWD/evidence:/results" \
  --entrypoint /bin/bash "$IMAGE"
docker exec -it fl-gate-minimal bash
```

这里只挂载设备、模型、安装输入和结果。普通驱动正常的机器不需要挂载 `/usr/src`、`/lib/modules`，也不需要照搬历史 `/workspace/driver-extracted` 路径。

## 4. 安装方式

本轮先记录原镜像包版本，再执行 `inputs/install-stack.sh`。脚本直接使用系统 `python -m pip`，只替换需要验证的核心组件。基础镜像的 setuptools 和 setuptools-scm 已满足构建要求，实际只补装缺失的 wheel；普通依赖沿用镜像现有版本。

安装顺序：构建工具 → 厂商 FlagTree → vLLM empty → FlagGems → FlagGems-vllm → 插件 → 容器内 FlagCX runtime。

```bash
bash /input/install-stack.sh
source /opt/gate/gate-env.sh
python /opt/gate/inspect-env.py --cuda --stack
```

注意：

- 不执行当前提交中固定旧 helper 的 `install_flaggems_vllm.py`，避免覆盖为旧提交。
- 不使用仍断言 FlagGems 5.3.5 的旧检查脚本。
- FlagTree 提供天数后端的 Triton；不要为消除 metadata 警告直接安装通用 `triton`。
- vLLM 版本覆盖值必须是 `0.32.0+empty`，仅写 `0.32.0` 不会自动添加 `+empty`。
- PyTorch 的厂商后缀通过 `importlib.metadata.version('torch')` 检查；`torch.__version__` 的显示可能不同。
- 安装脚本中的 `--no-deps` 用来保留镜像中厂商依赖；不代表依赖冲突检查已经通过。

本轮复用已编译的同版本 FlagCX 运行库，没有重新编译 FlagCX。需要从源码准备它的其他机器可以在具有 CoreX 开发环境的容器执行：

```bash
git clone https://github.com/flagos-ai/FlagCX.git /tmp/FlagCX
git -C /tmp/FlagCX checkout --detach 6143384797219733aee89bd3118b2cb184ad4959
git -C /tmp/FlagCX submodule update --init --depth 1 third-party/json
make -C /tmp/FlagCX -j4 USE_ILUVATAR_COREX=1 \
  DEVICE_HOME=/usr/local/corex CCL_HOME=/usr/local/corex
mkdir -p /opt/FlagCX/build/lib /opt/FlagCX/plugin/interservice
cp /tmp/FlagCX/build/lib/libflagcx.so /opt/FlagCX/build/lib/
cp /tmp/FlagCX/plugin/interservice/flagcx_wrapper.py /opt/FlagCX/plugin/interservice/
cp /tmp/FlagCX/LICENSE /opt/FlagCX/
```

这是重新编译的备选说明，不计入本轮实际执行命令；新编译产物需要在目标机器重新通过 gate。

## 5. 只运行 adaptation-gate-cases

每轮顺序执行，上一轮服务进程组退出后才启动下一轮。脚本运行原始 `run_serve_graph.sh` / `run_serve_eager.sh` 和 `run_test.sh`，不改用例，不降低判定条件。

```bash
export GATE_DEVICES=4,5,6,7
bash /opt/gate/run-one.sh graph /models/Qwen3.6-27B
bash /opt/gate/run-one.sh eager /models/Qwen3.6-27B
bash /opt/gate/run-one.sh graph /models/Qwen3.6-35B-A3B
bash /opt/gate/run-one.sh eager /models/Qwen3.6-35B-A3B
```

Graph 的实际参数为：

```bash
--compilation-config '{"cudagraph_capture_sizes":[1,2,4,8,16,32]}'
```

不设置 `mode:0`，避免改变要求验证的 Graph 模式。环境脚本保留：

```bash
export VLLM_FL_FLAGOS_BLACKLIST_APPEND=slice,mm,mm_out
```

这是本版本已知算子问题的兼容设置：bool padding mask 切片使用 PyTorch；mm 和 mm.out 避开已观察到的错误计算路径。M-RoPE 使用该插件提交默认实现，不追加本地补丁或覆盖变量。

原始服务脚本没有读取 `GPU_MEMORY_UTILIZATION` 环境变量，因此不把 `export GPU_MEMORY_UTILIZATION=0.70` 写成有效配置。端口默认 8145，TP=4，max model len=32768。固定 vLLM 源码中 `CacheConfig.gpu_memory_utilization` 的默认值为 0.92，本轮服务脚本未覆盖该值。

每轮五场景共 26 个请求：text single 1、text concurrent 8、image single 1、image concurrent 8、mixed concurrent 8；四轮共 104 个请求。退出码和 JSON 中每个请求的 `passed` 都需要通过。

每批复测使用新的空结果挂载目录。`run-one.sh` 遇到同名轮次目录已存在会停止，避免混用旧结果；不要把删除旧结果作为重跑的必要步骤，换一个结果目录即可。

## 6. 目标机器需要调整的配置

| 配置 | 调整原则 |
| --- | --- |
| 宿主模型路径 | 改 `docker run` 的挂载源，容器保持 `/models` |
| GPU 编号 | 改 `GATE_DEVICES` 为四张空闲卡，CUDA/CoreX 两个可见设备变量保持一致 |
| 端口 | 8145 被占用时在执行前 `export PORT=其他空闲端口` |
| 架构/显存 | 本轮针对天数 BI-V150 四卡；其他型号重新验证，不推定完全等价 |
| 驱动库 | 正常机器使用自身匹配驱动；本机专用修复单独记录，不作为通用必选步骤 |
| 模型内容 | 保证相同 config、processor/tokenizer、权重文件；同目录名不保证相同模型 |

模型证据 `model-files.json` 保存 config、处理器/索引等元数据哈希，以及每个权重分片的文件名和大小。本轮没有为约 119 GiB 权重另做完整逐字节哈希，不能将元数据一致或目录名一致扩大为所有权重字节已核验。

## 7. 本机管理入口

当前执行环境本身已经是容器，未暴露宿主 Docker socket。为真正新建容器，本轮在测试镜像外启动独立 Docker daemon，使用独立 data-root 和 socket，不修改宿主 Docker。

已通过 Harbor manifest 核对：`v0.28.0-iluvatar-ci` 标签在本轮执行时对应的 digest 就是上述 `eb904d40...`。宿主机即使已有缓存，未连接宿主 daemon 的独立 daemon 也无法直接复用，因此本轮发生了重复下载；这不是普通宿主机每次搭建都需要的步骤。

本机后续管理入口：

```bash
bash /workspace/minimal-gate-container-20261107/docker-local.sh ps -a
```

Docker 二进制、daemon 数据、安装归档和本轮结果位于外层 `/workspace/minimal-gate-container-20261107`，不进入最终测试镜像。普通宿主机直接使用 `docker` 即可。

## 8. 实测结果与打包

本轮只执行原始 adaptation gate，实际 JSON 与退出码均保留。原镜像驱动/运行库问题导致的一次服务启动失败不产生 gate 请求，单独记录在第 9 节。

首次完整四轮：27B Graph/Eager、35B Eager 均为 26/26；35B Graph 为 25/26，总计 103/104。35B Graph 文本并发的 `text-01` 要求计算 `19 + 23`，实际输出 `4ally`，未包含预期 `42`；其他 25 条请求通过。原始 gate 退出码为 1，不能因图片和混合用例通过而将整轮标为通过。

| 首次完整测试轮次 | 通过请求 | gate 退出码 | 启动至服务就绪 | 请求测试耗时 |
| --- | --- | --- | --- | --- |
| 27B Graph | 26/26 | 0 | 572 秒 | 84 秒 |
| 27B Eager | 26/26 | 0 | 536 秒 | 290 秒 |
| 35B Graph | 25/26 | 1 | 632 秒 | 79 秒 |
| 35B Eager | 26/26 | 0 | 511 秒 | 178 秒 |

启动时间包含 Python 导入、通信初始化、权重加载、profiling、必要编译和预热，不包含拉取基础镜像。首次 vLLM 编译约为 27B 88 秒、35B 62 秒。上述时间是当前机器/共享存储的实测记录，不是其他机器的耗时保证，也不是性能基准测试结果。

为确认是否可再次出现，只对失败的 35B Graph 做一次同环境、同源码、同模型、同参数的完整 gate 复测。首次结果保存为 `first-complete-summary.json`，该轮目录保存为 `Qwen3.6-35B-A3B-graph-first-quality-failure`。复测使用新的空结果目录以及 vLLM、Inductor、Triton 缓存目录，容器内 FlagGems 生成配置缓存沿用，没有修改模型代码、测试输入或通过条件。

复测结果为 26/26、退出码 0，启动 582 秒、请求测试 57 秒。原先失败的 `text-01` 在复测中的原文为 `4\n                    \n42`，包含预期 `42`，但带有额外的 `4` 和空白。当前原始 gate 的语义/顺序检查通过，不严格限定“只能有一个数字答案”的输出格式；本轮未修改这一判定逻辑。因此这里的通过必须理解为通过现有 gate，不能扩大为输出格式完全正确或该问题已根治。按各模型/模式最新结果汇总：

| 模型 | Graph | Eager |
| --- | --- | --- |
| Qwen3.6-27B | 26/26，退出码 0 | 26/26，退出码 0 |
| Qwen3.6-35B-A3B | 复测 26/26，退出码 0；首次 25/26 | 26/26，退出码 0 |

实际共执行 5 个完整 gate 轮次、130 个请求，129 个通过；不能把全部执行历史写成 130/130。`final-summary.json` 记录最新 104/104，同时记录首次 103/104、失败请求、根因未解决标记。复测通过不构成稳定性证明，也不等同于修复了一次质量错误。

35B Graph 同次服务随后的 mixed 场景中，同一道 `19 + 23` 返回 `42`。这说明同一模型目录、同一服务中存在不同上下文下的结果差异，尚不能凭一次回答认定模型本身有问题，也不能据此认定已修复。新旧环境的 cuBLAS、cuBLASLt 和 NCCL 共享库另做 SHA256 对照，三个库一致；不为这次结果错误无依据地替换更多运行库。

### 已打包镜像在另一台机器复测

本轮完成后导出的镜像 tar 和安装输入包放在外层 `artifacts/`。交付环境优先使用 `docker load`，无需重新 pip 安装、拉源码或创建 venv。模型权重和本机专用驱动挂载不在镜像 tar 中。

```bash
docker load -i iluvatar-gate-pr674-7a94aee-gems55-20261107.tar
mkdir -p "$PWD/gate-results-new"
docker run -dit --name fl-gate-retest --shm-size=32g \
  --privileged --network host \
  -v /dev:/dev \
  -v /目标机器/模型目录:/models:ro \
  -v "$PWD/gate-results-new:/results" \
  --entrypoint /bin/bash \
  local/iluvatar-gate:pr674-7a94aee-gems55-20261107
docker exec -it fl-gate-retest bash
export GATE_DEVICES=0,1,2,3
source /opt/gate/gate-env.sh
python /opt/gate/inspect-env.py --cuda --stack
bash /opt/gate/run-four.sh
```

`/目标机器/模型目录` 下应直接有 `Qwen3.6-27B`、`Qwen3.6-35B-A3B`。四张卡和端口按该机器实际情况修改。驱动正常的机器不添加本机专用挂载；如果环境检查失败，先处理厂商驱动与 CoreX 运行库的匹配问题，再加载模型。容器带的是用户态环境，不能替代目标机器的内核驱动。

若要从相同安装输入重建，将 `gate-install-inputs-20261107.tar` 解包到工作目录，使用第 3 节的基础镜像创建命令挂载 `inputs`，执行第 4 节脚本。该输入包不包含模型、宿主驱动或 Docker daemon。输入包和镜像 tar 属于供上传的大文件，不通过 GitHub 文档提交上传。

容器中 `/opt/gate/validation-summary.json` 保存本轮验证摘要，镜像标签 `io.flagos.gate.known-quality-failure=true` 明确保留已观察到的质量问题。该标签不是当前最新 gate 失败的意思，而是提醒接收者不要将一次复测通过误认为此前失败已根治。

本次“最小”指只安装需要替换的组件、只跑指定 gate、无 venv、无额外模型验证。基础镜像本身展开约 53.8 GB，仍含厂商 SDK 和原镜像内容；本轮没有另行制作极小运行时镜像，也不把模型、结果和本机专用运行库混入镜像。

本轮生成镜像：`local/iluvatar-gate:pr674-7a94aee-gems55-20261107`，ID 为 `sha256:44423fa86ea29b0350aa68484f0870cb4101724d939f1b2f9263e8919c0a3309`，Docker 记录大小 `55026763821` 字节（约 55.0 GB）。镜像位于本机独立 daemon；通过导出的 tar 可以加载到普通宿主 Docker。此次只导出供上传的文件，没有向未指定的镜像仓库推送。

导出文件位于当前外层容器 `/workspace/minimal-gate-container-20261107/artifacts/`：

| 文件 | 字节数 | SHA256 |
| --- | --- | --- |
| `iluvatar-gate-pr674-7a94aee-gems55-20261107.tar` | 55469534720 | `37234874632ed1eb133e841ca5d62c3e360e70b21bc72052727421fbec0eb33c` |
| `gate-install-inputs-20261107.tar` | 426342400 | `6fa3c13b0330d3ab36df20bfeff5951126f46729b39a5d95b43f235ebc9c4847` |

镜像 tar 为未压缩 `docker save` 归档，约 51.7 GiB；安装输入包约 406.6 MiB。`artifacts/SHA256SUMS` 可用于传输后校验。归档核验已确认镜像 ID、工作目录、标签、验证摘要、插件测试源码及 FlagCX 文件存在，新镜像层没有 `/models`、`/results`、`/input` 或本机专用运行库挂载中的文件。证据见 `packaged-image-archive-verification.json`。没有为归档核验再跑一套 GPU 测试。

测试结束后，为打包主动 `docker stop` 容器。交互 Bash 未在停止超时内退出，最终容器状态为 Exited 137、`OOMKilled=false`；这不是 gate 退出码，也不是模型测试 OOM。原始 gate 退出码分别保存在每轮的 `gate-exit-code.txt`/`exit-code.txt`。本机后续进入该容器前先通过独立 Docker 入口 `start fl-gate-minimal-20261107`，正常复测则优先使用打包镜像新建容器和新的结果目录。

## 9. 本机专用驱动对照记录

原镜像系统 Python 已有厂商 PyTorch，但使用原装驱动库时 `torch.cuda.is_available()` 为 False，`torch.cuda.init()` 报 `No CUDA GPUs are available`。可见设备数仍为 4，不能仅凭设备计数判定 GPU 可用。

对照步骤只改变驱动库搜索路径：补入当前机器已验证的 `libcuda.so.1` 后发现其依赖 `libixthunk.so` 在原镜像中缺失；两者完整提供后，四卡逐卡分配和回传通过。证据分别见 `base-environment.log`、`matching-driver-check.log`、`matching-driver-complete-check.log`。

| 文件 | SHA256 |
| --- | --- |
| 原镜像 `/usr/local/corex/lib64/libcuda.so.1` | `492a8447fda3588e69d1e552e35627ca31451a4b2ab6b9f59fb970655caeb4e4` |
| 本机匹配的 `libcuda.so.1` | `6cf92e5c9112ab657af07076b29446c8210590cd46062111c60f8e367200a35f` |
| 本机匹配的 `libixthunk.so` | `1d0257a2e3c75bb47fb83ed29b9757b3b0d80e4ca5fdde7b951a8e8c282d5c21` |

最初用于对照的容器已删除并重新创建。本轮正式安装容器增加只读挂载：

```bash
-v /workspace/minimal-gate-container-20261107/host-driver:/run/iluvatar-host-driver:ro
```

目录内包含匹配的 `libcuda.so.1`、`libixthunk.so`、`libcudart.so.10.2`。`gate-env.sh` 检测到挂载文件后才把此目录放到库搜索路径前面。挂载内容不进入 `docker commit`，不会把当前机器的驱动和运行库写死在交付镜像中。

驱动正常的其他机器省略这个挂载，直接使用其正常的厂商驱动配置。不要照搬这里的具体驱动文件替换其他机器。即使安装包完全一致，也必须先确认驱动初始化和真实 GPU 分配成功。

### 第一次 Graph 启动失败及进一步定位

只补齐前两个库后，GPU 分配虽然通过，第一次 27B Graph 服务仍在 `capture_begin` 报 `CUDA error: operation not supported`。服务未就绪，没有执行 gate 请求。失败轮的原始日志保留为 `Qwen3.6-27B-graph-initial-runtime-failure`。

核对结果：新容器和此前通过环境的 `libtorch_cuda.so`、`libc10_cuda.so` SHA256 完全相同，但 CoreX `libcudart` 不同。在同一新容器、同一 PyTorch、同一驱动下做运行库对照：原镜像 libcudart 使最小 Graph 捕获失败；换为当前机器匹配的 libcudart 后捕获、回放和结果回传通过。这是为定位服务启动失败进行的运行库能力检查，未增加其他项目测试。

| 文件 | SHA256 |
| --- | --- |
| 原镜像 libcudart | `d39d579627d19ddb903855ebc4859661579633a7ecc4d1ad51866d79296ba527` |
| 本机匹配 libcudart | `33a99c567b2277dca2a2d597e4ffb63b4ffd648fab85818650a031a5f6bfd30c` |
| 两边相同的 libtorch_cuda.so | `6c03712a0845a1a7da526fa52c02d9e6c00c80e48f527dcf0c0f97c83b1bb755` |
| 两边相同的 libc10_cuda.so | `1489b057693bf51b11184e5d021d973dca4b7ab0b3fc9a336cc5cde098721bab` |

证据见 `graph-runtime-original.log`、`graph-runtime-matching.log` 和对应退出码。不能只根据文件名、文件大小或标称 CoreX/PyTorch 版本判断环境完全一致，也不能把此次错误直接归因于 PR。最终环境检查增加一次很小的 Graph 捕获和回放，以便在加载几十 GB 模型之前发现此类运行库问题。

## 10. 最终安装集合与依赖声明边界

系统解释器为 `/usr/local/bin/python`，Python 3.12.11，`sys.prefix == sys.base_prefix == /usr/local`，未创建或激活 venv。

| 包 | 原镜像 | 本轮系统 Python |
| --- | --- | --- |
| torch | 2.10.0+corex.4.5.0 | 保留 |
| vllm | 0.28.0+empty | 0.32.0+empty |
| vllm-plugin-fl | 0.3.0rc0+g13eb9be69 | 0.0.0+g7a94aeec8，完整来源提交见上文 |
| flag-gems | 5.3.5 | 5.5.0.dev0 |
| flaggems-vllm | 未安装 | 0.3.0.dev1，b434eafb 提交 |
| flagtree | 0.6.2a3+iluvatar3.6 | 0.7.0+iluvatar3.6 |
| wheel | 未安装 | 0.48.0 |
| setuptools / setuptools-scm | 80.10.2 / 10.2.1 | 保留 |
| numpy | 1.26.4 | 保留 |
| transformers / tokenizers | 5.14.1 / 0.22.2 | 保留 |
| huggingface-hub | 1.24.0 | 保留 |
| compressed-tensors | 0.15.0.1 | 保留 |
| fastapi / starlette | 0.139.2 / 1.3.1 | 保留 |
| pydantic | 2.13.4 | 保留 |
| mcp / mistral-common | 1.28.1 / 1.11.3 | 保留 |
| opencv-python-headless / xgrammar | 4.11.0.86 / 0.2.3 | 保留 |
| openai / pillow / pytest | 2.46.0 / 12.3.0 / 8.4.1 | 保留 |
| modelscope | 1.39.1 | 保留 |

完整包集合见 `pip-list.json`、`pip-freeze.txt`，实际模块路径见 `final-environment-check.log`。插件从 `/opt/vllm-plugin-FL/vllm_fl` 导入，vLLM、FlagGems、Triton 从系统 site-packages 导入。

`pip-freeze.txt` 是审计快照，包含本地归档安装的 `file://` 来源和 editable 路径；它不是可直接搬到另一台机器执行的 requirements 文件。重建使用输入包和 `install-stack.sh`，搬运完整环境使用容器镜像。

`pip check` 的实际退出码为 1，共报告 12 项声明问题，完整原文见 `pip-check.log`：

- vLLM 缺少 oss-harmony；xgrammar 声明需要名为 triton 的 distribution，而天数 Triton 由 FlagTree wheel 提供。
- 插件要求 modelscope 1.35.3，镜像提供 1.39.1。
- compressed-tensors、fastapi、huggingface-hub、mcp、mistral-common、opencv-python-headless、tokenizers、transformers、xgrammar 与 vLLM 0.32.0 的版本声明不一致。

本轮目标是以最小安装改动复现指定 gate，保留基础镜像已经使用的普通依赖集合。核心导入和 GPU 分配通过不代表 `pip check` 通过；即使四轮 gate 全通过，也只证明本文固定版本组合覆盖到的文本、图片、混合请求路径。本轮不据此宣称所有 vLLM 功能或这些包的通用兼容性均已验证。
