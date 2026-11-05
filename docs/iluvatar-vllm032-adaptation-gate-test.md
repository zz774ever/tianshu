# 天数 vLLM 0.32：27B / 35B-A3B 图文适配测试

本页保留 FlagTree `0.6.2a3+iluvatar3.6` 的历史测试。当前容器已按用户要求升级至 `0.7.0+iluvatar3.6`，升级步骤与新一轮结果见[FlagTree 0.7 复测记录](iluvatar-vllm032-flagtree070-retest.md)，两轮结果分别归档。

日期：2026-11-05。测试容器：`test_plugin_28`。使用仓库原有的 `tools/adaptation-gate-cases`，分别验证两个模型的 eager 和 CUDA Graph 模式。本轮不重新安装、不创建 venv、不修改测试图片或通过条件、不录制终端，也不另存服务日志；保留测试脚本生成的 JSON 结果。

## 1. 测试环境

| 项目 | 实际配置 |
| --- | --- |
| GPU | Iluvatar BI-V150，整机 16 卡，单卡 32768 MiB |
| 本轮用卡 | 0、1、2、3，TP4；不使用其他任务占用的卡 |
| Driver / IX-ML | 4.5.0 / 4.4.0 |
| CPU | 双路 Intel Xeon Gold 6330，56 个物理核心、112 个逻辑 CPU |
| 容器系统 / 架构 | Ubuntu 24.04.2 LTS / x86_64 |
| Python | 系统 Python 3.12.11，无 venv |
| vLLM | 0.32.0，提交 `5df63a7203cdb9328d824a27b682e77c7b9928be` |
| vllm-plugin-FL | PR 674，提交 `c17d866e08b583f63998cbd47bc39fe3e57efce0` |
| PyTorch | `2.10.0+corex.4.5.0` |
| FlagGems / FlagTree | 5.3.5 / `0.6.2a3+iluvatar3.6` |
| Triton | 3.6.0，由 FlagTree 提供 |
| FlagGems-vllm | 提交 `b5c2c2249319277ccda4d41aa0f65164bd9b2a19`，包元数据 0.1.0 |
| FlagCX | 使用 `/mnt/share/user_homes/iluv/FlagCX/build/lib/libflagcx.so` |
| pytest / OpenAI SDK / Pillow | 8.4.1 / 2.46.0 / 12.3.0 |

基础镜像为 `harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-iluvatar-ci`，已在容器系统 Python 中升级到上述版本。安装步骤见[环境搭建教程](iluvatar-vllm032-fresh-machine-setup.md)。

模型名称按本机目录记录；27B 的配置架构为 `Qwen3_5ForConditionalGeneration`，35B-A3B 为 `Qwen3_5MoeForConditionalGeneration`。本轮加载完整多模态模型，没有启用 `--language-model-only`。

## 2. 测试范围和判定

`run_serve_eager.sh`、`run_serve_graph.sh` 只负责启动服务；`run_test.sh` 等服务就绪后，依次执行三个原始 pytest 文件。

| 测试场景 | 请求数 | 内容 |
| --- | ---: | --- |
| `text_single` | 1 | 英文详细介绍 LLM，至少 256 字符，并检查指定关键词 |
| `text_concurrent_8` | 8 | 算术、常识等文本请求并发 |
| `image_single` | 1 | 精确识别测试图片中的 `hello vllm` |
| `image_concurrent_8` | 8 | 颜色、形状、数量和可见文字检测 |
| `mixed_concurrent_8` | 8 | 同时发送 4 条文本和 4 条图片请求 |

每轮 5 个场景、26 个请求。27B 和 35B-A3B 各运行 eager、Graph，共 20 个场景、104 个请求。保持原始英文题目和本地图片，不替换成之前手工 curl 的中文问题或远程图片。

请求使用 temperature=0、关闭 thinking；单条长文本最多 512 token，其他请求默认最多 128 token。检查回答非空、预期内容及顺序、最小长度、乱码、异常控制字符和重复输出。HTTP 200 本身不代表测试通过。

本轮设置客户端请求超时 600 秒、服务就绪超时 1800 秒；只延长等待时间，不改变题目、并发数、生成长度和断言。它是功能及生成质量门禁，不是完整精度或性能基准。

## 3. 终端 A：公共环境

在宿主打开容器终端：

```bash
docker exec -it test_plugin_28 bash
```

以下命令在容器内执行。先确认选定 GPU 空闲、测试端口 8132 未被占用。每次只启动一个模型服务；切换模型或模式前，先 Ctrl+C 停止上一轮并等待显存释放。

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3
export VLLM_PLUGINS=fl
export USE_FLAGGEMS=1
export GEMS_VENDOR=iluvatar
export FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX
export PYTHONPATH=/workspace/vllm-plugin-FL
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

export LD_LIBRARY_PATH=/usr/local/lib
export LD_LIBRARY_PATH="/usr/local/openmpi/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/usr/local/corex/lib64:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$FLAGCX_PATH/build/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/workspace/driver-extracted/corex/lib64:$LD_LIBRARY_PATH"

export TENSOR_PARALLEL_SIZE=4
export MAX_MODEL_LEN=32768
export GPU_MEMORY_UTILIZATION=0.70
export SERVED_MODEL_NAME=qwen
export PORT=8132
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=7200
export GRAPH_COMPILATION_CONFIG='{"mode":0,"cudagraph_mode":"FULL_DECODE_ONLY"}'

cd /workspace/vllm-plugin-FL/tools/adaptation-gate-cases
```

提取目录必须排在库搜索路径最前面，否则可能缺少 `libixthunk.so`，或选中镜像内不匹配的 `libcudart` 而在 `capture_begin()` 报 `ixErrorNotSupported`。目录来自环境搭建教程的 `--noexec` 解包步骤，不执行宿主驱动安装。

本轮使用 32768 上下文，没有设置之前手工测试中的 `--max-num-seqs 4`；原脚本不限制为 4 条序列。脚本会自动配置 `--allowed-local-media-path`，允许读取仓库已有的 8 张 PNG 图片，无需重新生成。

## 4. 启动四轮服务

按以下顺序执行，每轮都完成第 5 节客户端测试后再停止服务、开始下一轮。

27B eager：

```bash
export MODEL_PATH=/mnt/share/user_homes/models/Qwen3.6-27B
bash run_serve_eager.sh
```

27B CUDA Graph：

```bash
export MODEL_PATH=/mnt/share/user_homes/models/Qwen3.6-27B
bash run_serve_graph.sh
```

35B-A3B eager：

```bash
export MODEL_PATH=/mnt/share/user_homes/models/Qwen3.6-35B-A3B
bash run_serve_eager.sh
```

35B-A3B CUDA Graph：

```bash
export MODEL_PATH=/mnt/share/user_homes/models/Qwen3.6-35B-A3B
bash run_serve_graph.sh
```

Graph 配置中 `mode=0` 关闭 Inductor 编译，`FULL_DECODE_ONLY` 对满足条件的 decode 批次捕获和回放 Graph。图像编码和 prefill 在 Graph 外执行。须确认启动时实际完成捕获，不能只根据请求 HTTP 成功就判定 Graph 模式通过。

## 5. 终端 B：执行原始测试

另开终端进入同一容器：

```bash
docker exec -it test_plugin_28 bash
```

在容器内设置客户端参数，不需要 GPU 库环境：

```bash
cd /workspace/vllm-plugin-FL/tools/adaptation-gate-cases
export SERVED_MODEL_NAME=qwen
export PORT=8132
export SERVICE_TIMEOUT=1800
export REQUEST_TIMEOUT=600
unset BASE_URL
export NO_PROXY=localhost,127.0.0.1
export no_proxy=localhost,127.0.0.1
export PYTEST_ADDOPTS='-p no:cacheprovider'
```

每轮按终端 A 的模型和模式设置以下两项。下面是第一轮示例；后续将结果目录分别改为 `27b-graph`、`35b-eager`、`35b-graph`，35B 时同时更换 MODEL_PATH：

```bash
export MODEL_PATH=/mnt/share/user_homes/models/Qwen3.6-27B
export RESULTS_DIR=/workspace/adaptation-gate-results/manual/27b-eager
bash run_test.sh
echo "测试退出码：$?"
```

每轮只运行一次，等命令结束再切换。该脚本即使前面的测试失败，也会继续执行后面的测试文件。全部通过退出 0；任一失败退出非 0。截图保留服务启动成功、Graph 捕获完成、pytest 结果及失败详情即可，不需要录制终端。

每个场景产生一份 JSON，包含题目、图片路径、原始 API 响应、每条请求耗时和逐项检查结果。不同模式使用不同 RESULTS_DIR，避免覆盖。启动失败、连接错误、超时和回答检查失败应分别记录，不改断言来获得通过。

## 6. 本轮实际结果

四轮均已完成，结果目录：`/workspace/adaptation-gate-results/20261105-112054`。本轮 20 个场景通过 14 个、失败 6 个；104 条请求通过 81 条、失败 23 条。52 条文本请求全部通过；52 条图片请求通过 29 条、失败 23 条。

以下各场景列记录“通过请求数 / 请求总数”，不是仅检查 HTTP 状态。

| 模型 / 模式 | 文本单条 | 文本并发 | 图像单条 | 图像并发 | 混合并发 | 通过场景 | 通过请求 | run_test 退出码 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 27B eager | 1/1 | 8/8 | 0/1 | 0/8 | 4/8 | 2/5 | 13/26 | 1 |
| 27B FULL_DECODE_ONLY | 1/1 | 8/8 | 1/1 | 2/8 | 5/8 | 3/5 | 17/26 | 1 |
| 35B-A3B eager | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | 5/5 | 26/26 | 0 |
| 35B-A3B FULL_DECODE_ONLY | 1/1 | 8/8 | 0/1 | 8/8 | 8/8 | 4/5 | 25/26 | 1 |

两轮 Graph 均实际完成 `Capturing CUDA graphs (decode, FULL): 35/35`，随后服务启动成功。本轮没有重现此前 `capture_begin()` 的 `ixErrorNotSupported`。捕获期间出现过 Triton benchmark 退回 event timing 的警告，27B 还出现过共享内存等待提示，最终均完成捕获并执行全部请求。

104 条请求均取得 API 响应，`finish_reason` 全为 `stop`，没有请求异常、超时或达到 token 上限的情况。失败均为原始回答内容检查未通过，不能将服务启动成功或 HTTP 200 写成全部门禁通过。

### 27B 失败说明

27B eager 的 13 条文本请求全部通过，13 条图片请求全部未通过。27B Graph 的 13 条文本请求全部通过，13 条图片请求中 4 条通过、9 条未通过。这里的 13 条图片包括单图 1 条、纯图并发 8 条、混合并发中的 4 条。

这些失败均取得正常 API 响应，`finish_reason=stop`，没有因为超时、连接失败或达到 token 上限失败。主要未通过 `expected_semantics`、`expected_order`；个别四次重复 `white` 的回答还未通过 `no_repeated_word_run`。

| 图片及问题 | 预期内容 | 27B eager 实际回答 | 27B Graph 实际回答 |
| --- | --- | --- | --- |
| `image_single`：识别 image_05 文字 | `hello vllm` | `e`，失败 | `HELLO` 换行 `VLLM`，通过 |
| `image_concurrent_8`：image_01 四象限颜色 | red, green, blue, yellow | `black, white, white, black` | `white, white, white, white` |
| `image_concurrent_8`：image_03 从左到右形状 | circle, square, triangle | `Triangle, Circle, Square` | `Triangle, Circle, Square` |
| `image_concurrent_8`：image_04 三角形数量 | 3 | `0` | `0` |
| `image_concurrent_8`：image_07 三角形颜色 | yellow | `blue` | `blue` |

同一套图片在 35B-A3B eager 中通过，包括颜色顺序、形状顺序和计数；图片文件未修改。27B 两种模式的通过数不同属于本轮单次运行的观察，不能据此判断 Graph 修复了图像问题。27B 图片回答异常的具体根因尚未定位，不能宣称全部适配通过。

### 35B-A3B Graph 失败说明

唯一失败是 `image_single` 的 image_05 OCR。预期为 `hello vllm`，实际为 `HELLO` 换行 `VLIM`；第二个单词识别错误，未通过 `expected_semantics` 和 `expected_order`。同一模型 eager 的回答为 `HELLO` 换行 `VLLM`，通过原始检查。

35B-A3B Graph 的纯图并发及混合并发均全部通过。纯图并发中的 image_05 问题仅为“是否包含可见文字”，它通过不能替代单图场景的精确 OCR 检查。

## 7. 原始结果与收尾

完整逐场景 JSON 见[本轮结果索引](../records/u180-adaptation-gates-20261105/README.md)，[manifest.json](../records/u180-adaptation-gates-20261105/manifest.json) 记录 20 份原始报告、原测试脚本及图片的 SHA-256 和汇总结果。JSON 按字节复制保留，不修改响应或通过状态。本轮没有终端录制和单独服务日志，Graph 捕获完成情况来自执行时终端观察，原始 JSON 保存请求及检查结果。

本轮使用原脚本和原测试用例，覆盖原脚本中全部 5 个 pytest 场景；启动参数显式覆盖为 TP4、显存预算 0.70，Graph 使用 `mode=0`、`FULL_DECODE_ONLY`，不等于验证了脚本默认 TP2 / 0.92 或其他 Graph 模式。保留了所有失败，没有修改测试断言，也没有重复运行覆盖失败结果。

测试完成后只停止本轮启动的服务。端口 8132 已释放，GPU 0–3 在检查时各空闲约 32560 MiB；vLLM、插件和 FlagGems-vllm 源码工作区均干净。环境保留供后续复测，不需要重新安装。
