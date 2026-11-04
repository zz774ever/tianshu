# 本机 u180 / n180：手动复现 vLLM 0.32 纯文本测试

更新：2026-11-04。这份教程针对当前机器及已创建的 `testtianshuzdh` 容器。用户称机器为 n180，最初只读检查得到 hostname=u180。所有安装、脚本、缓存和测试记录留在容器内；共享模型与 FlagCX 目录为只读。

**本文保留此前 venv 环境的复现记录。当前手动操作请优先使用[教程二](iluvatar-vllm032-fresh-machine-setup.md)：官方镜像、原始环境验证、容器系统 Python 直接升级、不建 venv、终端 B 直接 OpenAI/curl。** 本文配套脚本和 activate-local.sh 属于旧流程，不与教程二的 env-direct.sh 混用。

按用户要求，本文只运行文本测试，不下载图片或多模态模型，也不执行图像、混合请求和完整图文门禁。这里修复的是搭建教程和脚本入口，不是模型适配的生成精度；真实结果和失败均保留，不保证生成内容全部正确。

## 1. 当前已准备好的内容

| 项目 | 容器内真实路径或固定版本 |
|---|---|
| 容器 | `testtianshuzdh`；独立32GiB共享内存；不共享宿主PID空间 |
| 基础镜像 | `harbor.baai.ac.cn/plugin/vllm-plugin-fl@sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18` |
| 教程仓库 | `/workspace/tianshu-delivery`，本仓库 |
| 隔离Python | `/workspace/validation/venv/bin/python`，Python3.12.11 |
| 适配源码 | `/workspace/pr674-plugin`，`c17d866e08b583f63998cbd47bc39fe3e57efce0` |
| vLLM源码 | `/workspace/vllm`，tag v0.32.0，commit `5df63a7203cdb9328d824a27b682e77c7b9928be` |
| 实际导入vLLM | venv内普通安装的 `0.32.0+empty`，不是继承镜像的0.28 |
| 厂商组件 | torch distribution `2.10.0+corex.4.5.0`；FlagTree `0.6.2a3+iluvatar3.6`；FlagGems `5.3.5` |
| 驱动用户态依赖 | `/workspace/driver-extracted/corex/lib64` |
| FlagCX | `/mnt/share/user_homes/iluv/FlagCX`，包含真实库和wrapper，挂载只读 |
| 模型 | `/data/models/Qwen/Qwen3-4B`、`Qwen3.6-27B`、`Qwen3.6-35B-A3B`，挂载只读 |
| 本次手动结果根目录 | `/workspace/tianshu-manual/results`，每步创建新子目录 |
| 此前完整原始验证记录 | `/workspace/validation/README.md`、`COMMANDS.md`、`REPORT.md`、`steps/` |

当前旧镜像的上层Python依赖与vLLM0.32声明存在差异，参见第8节。这里复现的是已测的固定厂商组合，不会用无约束升级替换CoreX torch或FlagTree。

## 2. 进入现有容器

唯一需要在宿主终端输入的是进入容器命令：

```bash
docker exec -it testtianshuzdh bash
```

**从下一行起全部在容器内执行。不要在宿主运行pip、apt、驱动安装或本文Python脚本。** 不要再次创建同名容器，不要修改其他人的服务。

核对文件，设置真实路径：

```bash
export DOCS_DIR=/workspace/tianshu-delivery
export REPRO_ROOT=/workspace/tianshu-manual
export ENV_DIR=/workspace/validation/venv
export REPO_DIR=/workspace/pr674-plugin
export FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX
export COREX_DRIVER_LIB_DIR=/workspace/driver-extracted/corex/lib64

test -f "$DOCS_DIR/tools/iluvatar-repro/activate-local.sh"
test -f "$ENV_DIR/bin/activate"
test -f "$REPO_DIR/pyproject.toml"
test -f "$FLAGCX_PATH/build/lib/libflagcx.so"
test -f "$COREX_DRIVER_LIB_DIR/libixthunk.so"
git -C "$DOCS_DIR" rev-parse HEAD
git -C "$REPO_DIR" rev-parse HEAD
```

如果这些目录不存在，说明进入了其他容器，或旧容器已经被删除。此时不要靠创建空文件绕过检查，转到新机教程搭建。

## 3. 选择空闲卡，激活环境

原完整验证用卡8–11；编写本文时这些卡已有其他任务，因此脚本实测选择0、1卡。卡占用会变化，下面的0、1只是示例，每次先确认空闲。

```bash
export REPRO_DEVICES=0,1
source "$DOCS_DIR/tools/iluvatar-repro/activate-local.sh"
mkdir -p "$REPRO_ROOT/results"

ldd /usr/local/corex/lib64/libcuda.so.1
ldd "$FLAGCX_PATH/build/lib/libflagcx.so"
```

两份ldd输出都不应有 `not found`。`activate-local.sh` 将匹配驱动的用户态目录放在LD_LIBRARY_PATH最前；只挂载libcuda和libixml曾导致缺少libixthunk，必须保留这一步。

该用户态目录来自容器内对同版驱动包的 `--noexec` 解包，未运行安装器和内核操作；它不是给任意机器复用的通用驱动安装包。

准备venv自己的pytest入口，避免原门禁脚本调用全局Python：

```bash
python "$DOCS_DIR/tools/iluvatar-repro/prepare_cli.py"
hash -r
command -v python
command -v vllm
command -v pytest
head -n 1 "$(command -v pytest)"
```

三个命令均应位于 `/workspace/validation/venv/bin`。这里的pytest入口复用已安装pytest模块，仅写当前venv，不安装任何全局软件。

## 4. 每一步都保存完整记录

下面统一通过 `record.py` 执行。每次创建含UTC时间的独立目录，保存 `command.sh`、完整合并stdout/stderr的 `output.log` 和带起止时间、耗时、退出码、关键环境的 `metadata.json`，命令失败时原样返回非零。

```bash
export RECORDER="$DOCS_DIR/tools/iluvatar-repro/record.py"
export RECORD_ROOT="$REPRO_ROOT/results/steps"

python "$RECORDER" --root "$RECORD_ROOT" verify-env -- \
  python "$DOCS_DIR/tools/iluvatar-repro/verify_env.py" \
  --min-devices 2 --min-free-gib 30
```

检查范围：venv解释器、真实导入及CLI来源、插件精确commit、厂商版本、FlagTree编译器归属、FlagCX可加载、GPU加法及NumPy桥接。每张可见卡至少30GiB空闲才继续；这只是启动前检查，不是GPU锁，运行期间仍应避免他人同时占用。

如果显存不足，停止这一轮，确认后换卡并重新source，不要杀其他人的任务。不要把凭据放进记录命令或环境打印；记录器不用于登录、令牌提交等操作。

交互终端无需全局开启 `set -e`，以便失败后继续查看证据。记录器自身始终保存命令实际退出码，不会因为后续打印成功而掩盖失败。

## 5. 真实双卡FlagCX验证

保持两张卡可见，执行：

```bash
export FLAGCX_MASTER_PORT=18134
python - <<'PY'
import os
import socket
with socket.socket() as endpoint:
    endpoint.bind(('127.0.0.1', int(os.environ['FLAGCX_MASTER_PORT'])))
print('FlagCX control port is free')
PY

python "$RECORDER" --root "$RECORD_ROOT" flagcx-tp2 -- \
  python -m torch.distributed.run --nnodes=1 --nproc_per_node=2 \
  --master-addr=127.0.0.1 --master-port="$FLAGCX_MASTER_PORT" \
  "$DOCS_DIR/tools/iluvatar-repro/probe_flagcx.py"
```

预期两个rank分别输出 `FLAGCX_PASS ... values=[3.0, 3.0, 3.0, 3.0]`，外层 `EXIT_CODE=0`。脚本实际调用 `PyFlagcxCommunicator.all_reduce`；Gloo仅用于建立控制组。

使用 `python -m torch.distributed.run` 是必要的：镜像的裸torchrun脚本指向全局Python，即使venv已激活，也可能用回vLLM0.28。不要把这条命令改回裸torchrun。

这里还明确使用单机static rendezvous及127.0.0.1。实测 `--standalone` 会选用容器hostname作为控制端地址，而该hostname无法解析，持续重试；不修改宿主或容器hosts文件，用显式回环地址解决。端口占用时换一个空闲端口并重新检查。

## 6. Qwen3-4B：TP1 eager、TP2 eager、TP2 FULL graph

模型已存在，无需下载，也不要写入共享模型目录。先创建本轮独立结果目录：

```bash
export RUN_DIR="$REPRO_ROOT/results/smoke-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUN_DIR"
test -f /data/models/Qwen/Qwen3-4B/config.json
```

### 6.1 TP1 eager

```bash
export REPRO_DEVICES=0
source "$DOCS_DIR/tools/iluvatar-repro/activate-local.sh"

python "$RECORDER" --root "$RECORD_ROOT" tp1-eager -- \
  python "$DOCS_DIR/tools/iluvatar-repro/smoke.py" \
  --model /data/models/Qwen/Qwen3-4B --tp 1 \
  --output "$RUN_DIR/tp1-eager.json"
```

### 6.2 TP2 eager

等上一条命令退出后，再执行：

```bash
export REPRO_DEVICES=0,1
source "$DOCS_DIR/tools/iluvatar-repro/activate-local.sh"

python "$RECORDER" --root "$RECORD_ROOT" tp2-eager -- \
  python "$DOCS_DIR/tools/iluvatar-repro/smoke.py" \
  --model /data/models/Qwen/Qwen3-4B --tp 2 \
  --output "$RUN_DIR/tp2-eager.json"
```

### 6.3 TP2 FULL graph

```bash
python "$RECORDER" --root "$RECORD_ROOT" tp2-full-graph -- \
  python "$DOCS_DIR/tools/iluvatar-repro/smoke.py" \
  --model /data/models/Qwen/Qwen3-4B --tp 2 --graph \
  --output "$RUN_DIR/tp2-full-graph.json"
```

三种配置均为BF16、seed0、512上下文、最多2个序列、512 token批次预算和0.65显存预算。每条启动独立离线LLM进程，不绑定API端口。首次JIT调优可能较慢，等待日志推进，不要叠加启动。

graph采用 `{"mode":0,"cudagraph_mode":"FULL","custom_ops":["all"],"ir_enable_torch_wrap":false}`；保留graph replay，关闭Inductor。图捕获成功应在日志中核对，不能只根据命令中的 `--graph` 声称已运行graph。

成功需要命令退出0且JSON为PASS。JSON保存实际Python、vLLM路径、关键版本、可见卡号、config哈希和生成token IDs。**PASS只表示两条prompt生成了非空内容，不证明算术、图像质量或与NVIDIA逐token一致。** 文件已存在会拒绝覆盖，重跑请新建RUN_DIR。

如果只需要确认离线文本生成，到这里即可；下一节是同样的纯文本API及流式测试。

## 7. 纯文本API与流式请求

等离线测试进程退出后，终端A启动单卡文本服务。记录器会先检查端口空闲，服务仅监听同容器127.0.0.1：

```bash
export REPRO_DEVICES=0
source "$DOCS_DIR/tools/iluvatar-repro/activate-local.sh"
export PORT=18133
export MODEL_PATH=/data/models/Qwen/Qwen3-4B
export TENSOR_PARALLEL_SIZE=1

python "$RECORDER" --root "$RECORD_ROOT" text-api-server -- \
  bash "$DOCS_DIR/tools/iluvatar-repro/serve-text.sh"
```

保持终端A运行，终端B进入同一容器，重新激活：

```bash
docker exec -it testtianshuzdh bash
```

接下来在终端B的容器内执行：

```bash
export DOCS_DIR=/workspace/tianshu-delivery
export REPRO_DEVICES=0
source "$DOCS_DIR/tools/iluvatar-repro/activate-local.sh"
export RECORDER="$DOCS_DIR/tools/iluvatar-repro/record.py"
export RECORD_ROOT="$REPRO_ROOT/results/steps"
export API_RESULT_DIR="$REPRO_ROOT/results/text-api-$(date -u +%Y%m%dT%H%M%SZ)"

python "$RECORDER" --root "$RECORD_ROOT" text-api-client -- \
  python "$DOCS_DIR/tools/iluvatar-repro/text_client.py" \
  --base-url http://127.0.0.1:18133/v1 --model qwen \
  --output-dir "$API_RESULT_DIR"
```

客户端最长等待1800秒就绪，发送一条纯文本流式介绍请求和两条非流式问答，不含image_url或其他图像输入。保存模型列表、完整请求、每个SSE chunk、非流式响应和summary.json。

流式请求沿用用户示例temperature0.7、top_p0.8、top_k20、presence_penalty1.5、max_tokens20、enable_thinking=False。两条确定性问答检查17+25及法国首都，单列 `quality_passed`，不掩盖答错。

默认退出码检查API功能：响应非空、流式有结束标记。要同时要求两条问答正确，在同一命令添加 `--require-quality`，答错会保存全部结果后退出1。API功能通过不能被写成质量通过；两种结果都在summary中。

运行结束在终端A按Ctrl+C停止自己的服务，再查看记录器退出码。不要用批量pkill，也不要在同一张卡上叠加离线LLM和API服务。换PORT时，服务端和客户端base-url必须一起调整。

本文不调用 `run_test.sh` 或 `run_gates.sh`，因为它们会包含图像测试。若后续只想运行适配仓库自带的文本用例，可在服务参数和模型名称匹配后单独调用 `python -m pytest -sv tools/adaptation-gate-cases/test_text.py`，其质量判据另行保存，不能当作完整门禁结果。

## 8. 依赖检查、源码和环境指纹

先保存实际依赖冲突。此命令在当前组合预期可能退出1，记录器会保留结果：

```bash
python "$RECORDER" --root "$RECORD_ROOT" pip-check -- python -m pip check
```

当前继承环境包含Transformers5.14.1、tokenizers0.22.2等，不满足vLLM0.32全部声明要求；verify_env PASS不代表pip check通过。FlagTree提供import triton，但不一定提供名为triton的独立distribution；不要安装普通Triton覆盖它。严格依赖A/B另建venv，不要改坏本轮基线。

保存指纹：

```bash
export SNAPSHOT_DIR="$REPRO_ROOT/results/environment-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$SNAPSHOT_DIR"
python -m pip list --format=json > "$SNAPSHOT_DIR/python-packages.json"
python -VV > "$SNAPSHOT_DIR/python-version.txt"
git -C "$DOCS_DIR" rev-parse HEAD > "$SNAPSHOT_DIR/tutorial-commit.txt"
git -C "$REPO_DIR" rev-parse HEAD > "$SNAPSHOT_DIR/plugin-commit.txt"
git -C "$REPO_DIR" status --porcelain > "$SNAPSHOT_DIR/plugin-status.txt"
git -C /workspace/vllm rev-parse HEAD > "$SNAPSHOT_DIR/vllm-source-commit.txt"
sha256sum "$FLAGCX_PATH/build/lib/libflagcx.so" > "$SNAPSHOT_DIR/flagcx-library.sha256"
sha256sum /data/models/Qwen/Qwen3-4B/config.json > "$SNAPSHOT_DIR/model-config.sha256"
python "$DOCS_DIR/tools/iluvatar-repro/verify_env.py" --min-devices 1 \
  > "$SNAPSHOT_DIR/verify-env.log" 2>&1
```

config哈希不是完整模型身份。跨机器精度比较还需相同模型revision以及所有权重、tokenizer和配置文件SHA256；遍历大模型权重会产生大量只读I/O，应在必要时单独执行。

## 9. 新开终端如何恢复

每次新开容器终端重新设置：

```bash
export DOCS_DIR=/workspace/tianshu-delivery
export REPRO_DEVICES=0,1
source "$DOCS_DIR/tools/iluvatar-repro/activate-local.sh"
export RECORDER="$DOCS_DIR/tools/iluvatar-repro/record.py"
export RECORD_ROOT="$REPRO_ROOT/results/steps"
```

RUN_DIR、PORT、ILUVATAR_GATE_RESULTS是每轮实验自己的变量，不会自动跨终端继承。用已明确保存的绝对路径查看结果，避免读错实验。

## 10. 本文交付的实测证据

教程脚本的实际验证、命令及明确的未执行范围见[本机教程验证记录](iluvatar-vllm032-tutorial-validation.md)。这些记录不包含令牌或模型权重。完整此前独立门禁的容器路径见第1节。

不要删除旧容器、清理他人的进程、覆盖共享模型或将运行时警告直接计为生成失败。出现新错误时，先保存记录器给出的目录和完整日志，再定位相应阶段。
