# BI-V150 / Iluvatar：vLLM 0.32.0 最终适配执行记录

整理日期：2026-11-02。主要实机执行日期：2026-10-30。本文是截至停止 OCR 排查后的执行审计记录，不是全量适配通过或发布声明。

## 1. 最终结论与范围

本次在保留原始全局 vLLM 0.28.0 环境的前提下，建立隔离的 EMPTY vLLM 0.32.0 环境，适配 vllm-plugin-FL 的 Iluvatar runner、worker、通信、算子分发和 graph 生命周期，补齐安装校验及硬件 CI 门禁。

- Qwen3-4B 的 TP1/TP2 eager 与 graph 已有真实生成证据；这些是小模型冒烟，不等于完整模型验收。
- Qwen3.6-27B eager 历史门禁 26/26；最新 graph 门禁 26/26。
- Qwen3.6-35B-A3B 的 eager、FULL graph 均曾通过 26/26，但最新两组均为 **25/26**，同一 OCR 请求输出 `HELLO VLM`，正确判据为 `HELLO VLLM`。不能用早期通过覆盖后续失败。
- 最新同服务三组复测共 **78 请求，76 通过、2 失败；15 场景，13 通过、2 失败**。27B eager 本轮未重跑，不拼接为 104 请求全通过。
- 停止 OCR 排查后，相关单元回归 **157 passed，1 warning，16.53 秒**；实际依赖栈断言、安装来源校验与 shell 语法检查通过。
- 按用户要求停止 OCR 数值排查，既有失败保留；没有放宽判据、过滤 OCR、添加 xfail 或成功豁免。本文整理未重启模型、未追加 OCR 实验。

## 2. 环境、版本及来源

| 项目 | 实际记录 |
|---|---|
| 硬件 | Iluvatar BI-V150；完整模型主要使用 TP4、BF16 |
| 工作仓库 | `/workspace/vllm-plugin-FL`；整理时 HEAD 短哈希 `64c9d21`，工作树含未提交修改与新增文件 |
| 隔离 Python | `/workspace/envs/iluvatar-vllm032/bin/python` |
| vLLM | 精确 `0.32.0`，EMPTY 构建；厂商 PyTorch `2.10.0` 复用，未覆盖原始全局 0.28 环境 |
| vLLM 源码 | `/workspace/sources/vllm-0.32.0`，精确 tag 归档 |
| 归档 SHA256 | `bf592c132f27bbb5f65cff0bbd2ee873eae722b79c8286934fd5b5cf88b43d61` |
| FlagGems | `5.3.5` |
| FlagTree | `0.6.2a3+iluvatar3.6` |
| FlagGems-vllm | 安装源 pin `b5c2c2249319277ccda4d41aa0f65164bd9b2a19`；helper 对应 v0.2.0 源码，包元数据为 0.1.0，不能仅以元数据判断来源 |
| FlagCX | `/mnt/share/user_homes/iluv/FlagCX`，commit `6143384`，使用真实 CoreX 动态库 |
| 模型根目录 | `/mnt/share/user_homes/models`：Qwen3-4B、Qwen3.6-27B、Qwen3.6-35B-A3B |
| 证据根目录 | `/workspace/adapt-logs/` |

启动时显式指定仓库 `PYTHONPATH` 和隔离环境 `PATH`，避免继承的全局 site-packages 抢先导入。版本和库可加载性由实际 `verify_stack.py` 断言，不把“安装命令退出成功”当作生效证明。

## 3. 时间线

以下时间均为 **2026-10-30，UTC+08:00**。时分秒主要取已保存日志的文件修改时间，代表证据落盘时点，不冒充精确启动/结束时间；无可靠时间的阶段仅按依赖顺序排列。

| 时间/阶段 | 执行与观察 |
|---|---|
| 前期：环境隔离与接口适配 | 建立 0.32 EMPTY 环境；对齐 runner、worker、PP metadata、IR 注册与 FlagCX 路径；保留原始 0.28 |
| 12:31:55 | `smoke032-auxfix.log`：Qwen3-4B TP1 eager 实机生成 16 tokens |
| 约 12:59 | TP2 graph 保存两条 16-token 输出；退出日志存在 worker 强制终止和 shared_memory 清理警告，不把退出清理表述为无告警 |
| 13:48:34 | 27B eager v3 完成文本、图像、混合场景门禁 |
| 13:49:44 | `ci-empty032-install-v2.log`：独立 venv 真实构建安装、导入精确 0.32.0 |
| 中期 | 修复视觉 flash 路径 NaN、清零重入、MoE 路由语义；初始 graph 捕获 OOM，降低显存预算后继续受控诊断 |
| 16:29:51 | 35B eager v4 完成 26/26；同期 graph 仍有并发及生成正确性错误 |
| 17:42:10 | 27B borrowed-storage graph 结果落盘：不再捕获 OOM，但 25/26，长文本重复感叹号 |
| 编译路径对照 | compile-only、PIECEWISE、custom_ops/IR、SiLU 编译边界等实验，保留失败，不用配置预检代替生成验收 |
| 18:41:56 / 18:43:52 | 35B / 27B FULL graph、compilation NONE 对照各 26/26；仅是该次结果 |
| 20:27:49 | 27B graph recheck：26/26 |
| 20:28:25 / 20:28:52 | 35B graph / eager recheck：各 25/26，均在同一 OCR 失败 |
| 后期稳定性诊断 | 交替请求、逐 token 分数、离线/服务预算、通信确定性及首层采集；观察到波动，未证明根因 |
| 21:55:08 | 同步采集最终结果落盘，共 48 请求；四阶段失败数 4/2/2/2，同步没有消除问题 |
| 21:59:57 | 停止 OCR 后相关最终回归：157 passed，1 warning，16.53 秒 |
| 2026-11-02 | 汇总本记录；只读既有日志和 JSON，不追加实机实验 |

## 4. 代码与配置改动

以下按最终工作树与状态记录归类。工作树不是干净提交态，清单不等价于“所有差异均在最后一轮新增”，也未创建提交或分支。

| 文件/区域（仓库相对路径） | 适配内容及边界 |
|---|---|
| `vllm_fl/worker/iluvatar_model_runner.py` | 基于上游 0.32 迁移独立 Iluvatar runner，避免其他厂商直接承受此轮 runner 迁移 |
| `vllm_fl/platform.py`、`vllm_fl/__init__.py` | Iluvatar runner 选择、EMPTY 环境 IR 注册兼容、编译前预热与平台初始化；不无条件切换全厂商 runner |
| `vllm_fl/worker/worker.py` | 对齐 batch-invariant 导入、PP metadata 句柄、KV cache 初始化；移除对上游已删除 routed-expert 配置字段的访问 |
| `vllm_fl/dispatch/config/iluvatar.yaml` | 同时排除 FlagGems `zeros` 与 `zero_`，避免 16 GiB 清零失败；排除 `_scaled_dot_product_flash_attention` 和 `_flash_attention_forward`，避免视觉路径 NaN，保留其他算子 |
| `vllm_fl/dispatch/backends/vendor/iluvatar/moe_router.py` | 补齐 0.32 MoE padding/bias 语义；BF16 并列 score 不强求任意 expert 索引顺序一致 |
| `vllm_fl/distributed/communicator.py` | 对齐真实 FlagCX 初始化、TP 通信及失败关闭；不能以空库或静默 fallback 冒充通信通过 |
| `vllm_fl/dispatch/backends/vendor/iluvatar/vision_precision.py` | 仅 Iluvatar Qwen 视觉 forward 使用 FP32 归约并返回原 dtype，不改变 decoder 的归约策略；不是 OCR 根因修复 |
| `vllm_fl/dispatch/backends/vendor/iluvatar/autotune_memory.py` | 限定 Iluvatar 释放 autotune 诊断参数的额外持有；独立探针有效，但单独不足以解决完整捕获 OOM |
| `vllm_fl/compilation/graph.py` | EMPTY 缺少 weak_ref_tensor 时以借用 storage 重建 tensor，保留视图元数据及非持有生命周期，修复共享 graph pool 被强引用阻碍复用 |
| `vllm_fl/dispatch/backends/flaggems/impl/activation.py` | Iluvatar SiLU 增加 custom_op 编译边界及 fake shape 推导，实际计算仍由 FlagGems 执行 |
| 编译适配（platform/runner） | 扩展 CachedOp 预热，避开追踪 RLock；关闭 OOT 未导入的三项量化融合，避免 pass manager 缺失类；不把尚未通过的 Inductor 对照设为全平台默认 |
| `tools/adaptation-gate-cases/run_serve_eager.sh`、`run_serve_graph.sh` | 显存预算参数透传；graph 配置可用 `GRAPH_COMPILATION_CONFIG` 覆盖；eager 默认预算仍为 0.92，历史实机对照显式使用 0.70 |
| `.github/scripts/iluvatar/install_vllm.sh`、`setup.sh`、`verify_stack.py` | 精确归档校验及 EMPTY 安装、清除继承 PYTHONPATH、依赖与导入来源/真实 FlagCX 库断言 |
| `.github/scripts/iluvatar/run_gates.sh`、`.github/workflows/_iluvatar_gate.yml`、`_platform_test.yml` | 两模型 × eager/graph 串行门禁、失败日志上传、缺失模型拒绝；跳过 gate 不得在聚合通知中算成功，保持 registry 原 opt-in 策略 |
| `docs/usage/iluvatar-vllm032-status.md` | 保存阶段性结果、失败及停止 OCR 后收尾结论 |

### 4.1 测试文件

新增/更新的回归覆盖：

- `tests/unit_tests/test_runner_selection.py`、`test_iluvatar_runner032.py`、`test_worker_pp032.py`。
- `tests/unit_tests/compilation/test_iluvatar_graph_refs.py`、`test_iluvatar_autotune_memory.py`、`test_gate_graph_memory.py`。
- `tests/unit_tests/test_iluvatar_activation_compile.py`、`test_iluvatar_compile_passes.py`、`test_iluvatar_compile_warmup.py`。
- `tests/unit_tests/test_iluvatar_flagcx.py`、`test_iluvatar_moe_router.py`、`test_iluvatar_vision_precision.py`、`test_iluvatar_zeros_config.py`。
- `tests/unit_tests/test_iluvatar_ci_setup.py`、`test_iluvatar_gate_ci.py`。

诊断用采集、复算脚本及 `.pt` 文件属于 `/workspace/adapt-logs/` 证据，不是已上线的生产功能；不因整理记录而删除或覆盖。

## 5. 测试结果与证据分层

### 5.1 最终模型门禁

每组完整门禁包含五场景、26 请求：单条文本、并发文本、单条图像、并发图像、混合请求。完整模型均 TP4、BF16、4096 上下文；历史对照显存预算 0.70。

| 模型/模式 | 有效结果 | 原始结果目录（位于 `/workspace/adapt-logs/`） | 解读 |
|---|---|---|---|
| 27B eager | 历史 5/5 场景，26/26 请求 | `gate-27b-eager-final/` | 最新三组复测未重跑此项 |
| 27B FULL graph、无编译 | 最新 5/5，26/26 | `gate-27b-graph-recheck-v10/` | 本轮通过，不是 NVIDIA 精度对齐 |
| 35B eager | 最新 4/5，25/26 | `gate-35b-eager-reproduce-v3/` | OCR `image-05` 为 `HELLO VLM`，失败保留 |
| 35B FULL graph、无编译 | 最新 4/5，25/26 | `gate-35b-graph-recheck-v10/` | 同一 OCR 失败，历史全通过不构成稳定修复 |

最终三组复测 **76/78**；上述四行不能当作同一轮 102/104 或 104/104 验收。所有五份场景 JSON 都必须读取，不能只取测试日志末尾最后一项 passed。

### 5.2 历史对照：不能替代最终结果

| 对照 | 已观察结果/意义 |
|---|---|
| graph v1 | 默认预算 0.92，PIECEWISE 捕获 OOM，失败 |
| graph v2 | 仅预算改 0.70，TP4/4096/51 捕获尺寸不变；27B autotune OOM，35B 3/5 场景通过，不能验收 |
| 35B graph v3 | 端口被旧服务占用，启动失败；关联 gate 无效，不能混入统计 |
| 35B graph v4 | 20/26；视觉 FP32 归约没有解决整体正确性 |
| 35B PIECEWISE | 23/26，图像 9 请求全通过，文本并发与混合失败 |
| borrowed-storage | 捕获显存稳定；27B 25/26、35B 21/26，证明显存问题修复不等于生成正确 |
| 35B compile-only、无 graph | 22/26；不能把错误只归因于捕获/replay |
| backend=eager 但混合 graph | 两模型均在权重加载前失败，上游 dispatcher/partition 配置约束未满足，不是生成样本 |
| custom_ops=all、禁 IR wrapping | 修复预热/融合及 SiLU 编译后，35B 22/26、27B 25/26，仍不通过 |
| FULL、compilation NONE | 两模型各捕获 35 个尺寸（1–256），首次均 26/26；保留 graph replay，不是 enforce-eager；后续 35B OCR 仍失败 |
| 35B eager/保留 JIT warmup/FP32 head | 多次 25/26，同一 OCR；单独补预热或提高输出投影精度均不充分 |
| 35B eager reproduce v2 | 单次 26/26，但同服务交替请求仍出现两种 OCR 输出，不能记作稳定修复 |

### 5.3 组件、小模型与单元回归

- `smoke032-auxfix.log`：Qwen3-4B TP1 eager，真实生成 16 tokens，首条为 `Paris. The capital of Germany is Berlin. The capital of Italy is Rome.`。
- `tp1-graph.json`：两条 16-token 生成，首条 IDs 与 eager 一致。
- `tp2-flagcx-zerosfix.json`：真实 FlagCX 下 TP2 eager 两条 16-token 生成。
- `tp2-flagcx-graph.json`：`version=0.32.0, tp=2, graph=true`，两条 16-token 生成；本次只读确认。旧状态文档“TP2 graph 验证中”已滞后，应以该结果和日志为准。退出清理日志有强制终止 worker/shared_memory 警告，未把它抹去。
- FlagCX 双卡 AllReduce：1024 元素均为 3；TP4 graph 探针对 FP32/BF16、三种大小各十次输入更新 replay 精确通过；固定有符号输入、2048/4096/32768 元素各 200 次，四 rank 逐位一致。这些不排除完整模型通信/状态交互。
- MoE 路由 n=1/17/256 的 score、唯一 expert ID 与权重验证通过；固定输入重复 200 次一致。实际 `TritonExpertsFL.apply()` 固定首 token/路由、M=1/6/8/17/128 各三次一致，不代表覆盖全部真实权重路由。
- SiLU 三种形状的真实 fullgraph 动态编译、逐位比较及 opcheck 通过；graph 共享池探针后续 allocated 增量小于 1 MiB。GDN 两种长度固定初态并扰动分配历史各 30 次一致，均仅是所测条件的组件证据。
- 阶段性回归记录包含 99 passed、136 passed/5 skipped、147 passed、150 passed/1 warning。测试集合演进，不能累加这些数字。
- **最终相关回归**：`iluvatar-regression032-final.log` 为 **157 passed，1 warning，16.53 秒**。不是全仓库、全厂商回归；早期 skip 不是通过。
- `verify-stack032-final.log` 实际断言通过；FlagGems-vllm helper 的 `release_is_installed()` 只读返回 True，未重装。
- 安装及启动脚本 `bash -n`、`git diff --check` 通过；真实独立 EMPTY 安装日志为 `ci-empty032-install-v2.log`。远端硬件 workflow 尚未实际运行。

## 6. 启动命令与复现入口

**本节是命令记录，不是本次执行指令。含 OCR 的门禁按用户要求停止追加。未来如重跑，须重新确认授权、GPU 空闲、端口及独立输出目录。历史卡号不代表当前可用，尤其不得占用他人正在使用的 0–3 卡。**

### 6.1 历史 35B eager

原脚本：`/workspace/adapt-logs/serve_35b_eager_final032.sh`。核心命令如下（原脚本另写 PID 文件）：

```bash
export PYTHONPATH=/workspace/vllm-plugin-FL
export PATH=/workspace/envs/iluvatar-vllm032/bin:$PATH
export COREX_VISIBLE_DEVICES=4,5,6,7 CUDA_VISIBLE_DEVICES=4,5,6,7
export FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX
export VLLM_PLUGINS=fl USE_FLAGGEMS=1 GEMS_VENDOR=iluvatar
vllm serve /mnt/share/user_homes/models/Qwen3.6-35B-A3B \
  --served-model-name /mnt/share/user_homes/models/Qwen3.6-35B-A3B \
  --host 127.0.0.1 --port 8134 --tensor-parallel-size 4 \
  --max-model-len 4096 --gpu-memory-utilization 0.70 \
  --allowed-local-media-path /workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images \
  --trust-remote-code --enforce-eager
```

### 6.2 历史 27B FULL graph、关闭编译

原脚本：`/workspace/adapt-logs/serve_27b_full_nocompile032.sh`。原脚本显式设置 `VLLM_PLUGINS=fl`，没有显式 export `USE_FLAGGEMS`/`GEMS_VENDOR`；其继承环境和已验证依赖栈应分开理解，不能把未出现的 export 冒充历史命令。

```bash
export PYTHONPATH=/workspace/vllm-plugin-FL
export PATH=/workspace/envs/iluvatar-vllm032/bin:$PATH
export COREX_VISIBLE_DEVICES=8,9,10,11 CUDA_VISIBLE_DEVICES=8,9,10,11
export FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX
export VLLM_PLUGINS=fl
vllm serve /mnt/share/user_homes/models/Qwen3.6-27B \
  --served-model-name /mnt/share/user_homes/models/Qwen3.6-27B \
  --host 127.0.0.1 --port 8132 --tensor-parallel-size 4 \
  --max-model-len 4096 --gpu-memory-utilization 0.70 \
  --allowed-local-media-path /workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images \
  --trust-remote-code \
  --compilation-config '{"mode":0,"cudagraph_mode":"FULL","custom_ops":["all"],"ir_enable_torch_wrap":false}'
```

35B 对应原脚本为 `/workspace/adapt-logs/serve_35b_full_nocompile032.sh`：同配置，模型及 served name 为 `Qwen3.6-35B-A3B`，历史卡号 `12,13,14,15`，端口 `8133`。FULL graph 保留 replay，不可写成 eager；它绕开当前未验收的 Inductor 编译路径，但不解决最终 OCR 稳定性。

### 6.3 对已启动服务执行原始门禁的接口

以下为读取现有 `run_test.sh` 后整理的调用形式，并非声称本次又执行了一遍。它不接受位置参数，要求环境变量；使用全新结果目录，不覆盖历史证据。

```bash
cd /workspace/vllm-plugin-FL
export PATH=/workspace/envs/iluvatar-vllm032/bin:$PATH
export MODEL_PATH=/mnt/share/user_homes/models/Qwen3.6-35B-A3B
export PORT=8134
export RESULTS_DIR=/workspace/adapt-logs/NEW_UNIQUE_RUN/results
export SERVER_PID_FILE=/workspace/adapt-logs/35b-eager-final.pid
bash tools/adaptation-gate-cases/run_test.sh
```

`NEW_UNIQUE_RUN` 是将来调用者必须替换的独立目录，不是已执行实验。脚本轮询 `/v1/models` 就绪，然后依次运行 `pytest -sv test_text.py`、`test_image.py`、`test_mix_text_image.py`；任一失败最终返回非零。不得删除图像样本、只跑文本或依据最后一条 passed 判整组成功。

## 7. CI、安装与核验入口

### 7.1 已落地配置

- `.github/scripts/iluvatar/setup.sh` 接入 `install_vllm.sh`，精确版本与归档校验失败即退出；不使用继承 PYTHONPATH 冒充隔离安装。
- `.github/scripts/iluvatar/verify_stack.py` 核验 vLLM、厂商 PyTorch、FlagGems、FlagTree、导入路径及真实 FlagCX 库。
- `.github/workflows/_iluvatar_gate.yml` 与 `run_gates.sh` 对两模型依次执行 eager/graph；失败保留日志并传播非零状态。
- runner 的仓库变量 `ILUVATAR_FLAGCX_PATH` 必须指向容器实际挂载的 FlagCX 构建根目录；运行脚本使用 `FLAGCX_PATH`，要求存在 `build/lib/libflagcx.so`。缺失不能换空库。
- gate 默认 TP4、4096、显存预算 0.70，graph 默认 `mode=0/FULL/custom_ops=all/ir_enable_torch_wrap=false`；可显式覆盖。通用 eager 启动脚本默认 0.92，与硬件 gate 的显式 0.70 不矛盾。

### 7.2 只读依赖核验命令

最终历史核验日志已保存；本次整理没有重新安装依赖。后续只读核验的明确入口为：

```bash
cd /workspace/vllm-plugin-FL
PYTHONPATH=/workspace/vllm-plugin-FL \
FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX \
  /workspace/envs/iluvatar-vllm032/bin/python \
  .github/scripts/iluvatar/verify_stack.py
```

### 7.3 完整硬件门禁入口（未在本次收尾执行）

```bash
cd /workspace/vllm-plugin-FL
export PATH=/workspace/envs/iluvatar-vllm032/bin:$PATH
export FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX
export ILUVATAR_MODEL_27B=/mnt/share/user_homes/models/Qwen3.6-27B
export ILUVATAR_MODEL_35B=/mnt/share/user_homes/models/Qwen3.6-35B-A3B
export ILUVATAR_GATE_RESULTS=/workspace/adapt-logs/NEW_UNIQUE_CI_RUN
bash .github/scripts/iluvatar/run_gates.sh
```

此示例省略 GPU 选择，**不能直接在共享机器执行**；须先确认授权并 export 对应 `COREX_VISIBLE_DEVICES`/`CUDA_VISIBLE_DEVICES`。输出目录也须替换为全新路径。脚本将实际包含 OCR，因此按当前停止排查范围不执行。远端硬件 workflow 仍未验证；本地语法与 wiring 单元测试不是远端运行证据。

## 8. 未解决的问题及归因边界

### 8.1 35B OCR 不稳定：未解决，按指令停止

- 同服务相同输入可输出 `HELLO VLLM` 或 `HELLO VLM`，覆盖 eager 和 graph；最终两个失败均有效。
- 逐 token 对照曾在第五个生成 token 分歧：某次 graph 中 `LL` 比 `LM` 高 0.125 log probability，eager 则 `LM` 高 0.0625。候选接近不等于找到了误差源。
- 上游离线/在线默认 token budget 分别 8192/2048；匹配 2048/256 后离线可正确，但离线成功不能替代服务门禁。
- 默认关闭的采集扩展先重置前缀缓存，关闭/开启/关闭三阶段各六次，失败数 2/1/2，表明两种采集状态均可复现。
- 某组成功/失败采集的 prefill 最后 token 各层逐位一致，但首个 decode 的首层已不同，最大绝对差 `0.0001220703125`，1292 元素不同；未排除 prefill 中间位置、递归状态或首层内部算子。
- 首层子模块采集 36 次，三阶段失败 2/2/1；部分失败样本在注意力输出投影出现差异，另一失败样本该处仍相同。仅 rank 0 部分采集不足以确定根因。
- 真实输入/权重复算的原生 PyTorch、按黑名单启用 FlagGems 各 200 次均一致于 CPU FP32 参考转 BF16，但某份服务投影有 14 元素不同、最大差 0.04296875；隔离复算未复现服务上下文差异。
- 首次全 rank 同步诊断因采集器误判 MoE 工作区轴布局中断，该诊断错误已修正并有布局回归；不是模型测试样本。
- 最终同步记录是磁盘完整 **48 次请求**，关闭/普通采集/同步采集/关闭各 12 次，失败数 **4/2/2/2**。监控曾中断，但客户端最终写出完整结果，不能继续沿用“同步阶段无结果”的旧结论。同步没有消除问题。

以上仅为定位线索，根因未定。不得据此断言 FlagCX、MoE、GDN、采集器或某个 GEMM 已被完全排除，也不得把不在真实服务调用路径上的融合 SiLU 探针差异当作模型修复理由。

### 8.2 其他尚未完成的验收

1. 原始四组合完整 104 请求矩阵在最新代码/稳定服务条件下全部通过，尚未获得；OCR 失败不能豁免。
2. NVIDIA + 原生上游 vLLM 0.32 的逐 token 精度对齐未完成；正常自然语言输出及单元测试都不能替代该基准。
3. Inductor/混合 PIECEWISE 路径仍有生成正确性问题；当前 Iluvatar gate 用 FULL、无编译对照规避该路径，不宣称编译器错误算子已定位。
4. 远端 Iluvatar 硬件 CI 未执行，runner 挂载、仓库变量和真实模型门禁还需独立验证。
5. 其他厂商完整 CI、依赖与全量回归未完成；平台分支隔离测试不能证明所有厂商实机无回归。
6. 没有本轮可比吞吐/延迟性能基准，不作性能提升或生产 SLA 声明。
7. TP2 graph 冒烟退出的 worker/shared_memory 警告未在本记录中当作已修复。

这些是后续验收边界，不是本次追加实验的授权。恢复 OCR 或触发硬件 CI 应先重新确认范围和资源。

## 9. 原始证据索引

下列相对条目默认位于 `/workspace/adapt-logs/`，保留原始输出，不重新生成覆盖：

| 类别 | 文件/目录 |
|---|---|
| 环境安装 | `ci-empty032-install-v2.log`、`verify-stack032-final.log` |
| 最终单元回归 | `iluvatar-regression032-final.log` |
| 小模型 | `smoke032-auxfix.log`、`tp1-graph.json`/`.log`、`tp2-flagcx-zerosfix.json`/`.log`、`tp2-flagcx-graph.json`/`.log` |
| 最终完整模型 | `gate-27b-eager-final/`、`gate-27b-graph-recheck-v10/`、`gate-35b-eager-reproduce-v3/`、`gate-35b-graph-recheck-v10/` |
| 历史 FULL 对照 | `gate-27b-full-nocompile-v1/`、`gate-35b-full-nocompile-v1/` |
| 历史编译对照 | `gate-35b-compile-only-v1/`、`gate-35b-graph-customops-v2/`、`gate-27b-graph-customops-v3/` |
| graph 内存 | `qwen36-27b-graph-borrowed-v2.log`、`summary-27b-graph-borrowed-v2.txt`、`summary-35b-graph-borrowed-v1.txt`、`graph-refs032-final-tests.log` |
| OCR 复现与分数 | `ocr-options032.json`、`serving-ocr-logprobs-v1.json` |
| 服务采集 | `serving-trace032.json`、`serving-trace032-comparison-v2.log`、`component-repeat032.json`、`inspect-repeat032-12-15.log`、`inspect-repeat032-12-22.log` |
| 真实权重复算 | `real-linear032.json`、`real-linear-gems032.json`、`copy-record032.json`、`moe-actual032.json` |
| 同步采集 | `sync-trace032-v2.json`、相关日志与 `.pt`；布局测试 `test-trace-layout032.log` |
| 历史服务脚本 | `serve_35b_eager_final032.sh`、`serve_27b_full_nocompile032.sh`、`serve_35b_full_nocompile032.sh` |

其他完整历史入口：

- `/workspace/vllm-plugin-FL/docs/usage/iluvatar-vllm032-status.md`：开发状态及阶段结果；TP2 graph 待验证条目已由本次直接读取 JSON 补正。
- `/workspace/flagscale-agent-monitor/历史执行明细.md`：逐步执行明细。
- `/workspace/flagscale-agent-monitor/监控记录.md`：监控侧记录，计数与最终写盘结果冲突时以原始结果文件为准。
- `/workspace/flagscale-agent-monitor/OCR问题记录与范围调整.md`：停止 OCR 与范围调整。
- `/workspace/flagscale-agent-monitor/FlagScale-Agent流程与Iluvatar历史适配参考.md`：流程及历史背景，不替代本次实际验证。

## 10. 本记录的交付与验证范围

唯一指定交付文件为 `/workspace/flagscale-agent-monitor/最终适配执行记录.md`。本文包含时间线、文件级改动、测试结果、历史启动及 CI 命令、未解决问题和证据索引；历史命令与未来调用示例明确区分。

文档整理只涉及新增本记录及只读核验，没有修改适配代码、停止他人服务、安装依赖或重跑含 OCR 的门禁。历史测试结论保持原样；“记录整理完成”不代表“硬件适配全部通过”。
