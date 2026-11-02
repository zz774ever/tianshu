# FlagScale Agent 适配任务记录与中止交接

记录日期：2026-10-30，时间均为 UTC。

**交接状态：原精度深挖轮次已中止，用户已接手，并在 Agent 中明确接受该精度差异、启动后续收尾。逐 token 严格对齐未通过的事实保留；整体适配尚未完成。**

## 中止动作与恢复点

- 任务会话：`d08319f6`。早期会话 `d430689c` 不是本次适配的恢复点。
- Agent PID：`432625`，交互终端 `/dev/pts/19`。
- 对原运行轮次发送一次 `SIGINT`，随后通过 Python 调用栈确认已回到 `prompt_toolkit` 输入提示符；该次检查时本地子进程为 0。
- 会话已自动保存：`conversation.json` 保存时间为 13:55:43 UTC，轮次 15，活动消息 141；`conversation_full.json` 为 3,797 条消息。`completed` 为 `false`。
- 保留交互进程供用户接手；本记录的整理者没有启动第二个 Agent、没有再发“继续”指令，没有提交或回退适配代码。
- 持续监控此前已按用户要求暂停；此次没有重新启动采集程序。
- 最终交接快照：`/workspace/s60-adaptation/handoff/20261030T135753Z/`。其中有会话副本、原 STATUS、已跟踪代码 diff、未跟踪文件副本和 Git 状态。
- 快照目录采用受限权限。原始会话可能含连接凭据，Markdown 记录没有复制这些凭据；原始快照不适合直接公开。

13:59 UTC 后的复核发现用户已在原 Agent 输入“这个精度差异是可以接受的”。会话进入第 16 轮，Agent 回复将记录验收决定、停止该精度排查并检查代码、回归结果和交付文档。该轮由用户启动，本记录整理者没有再次发送中断信号，也不接管后续执行。

因此，中止时的第 15 轮快照与用户接手后的第 16 轮应分别理解。若后续 Agent 已退出，可恢复原会话：

```bash
flagscale-agent --config /root/.flagscale/agent.yaml --auto-resume=d08319f6
```

同一会话仍由现有进程持有时，不要另开第二个恢复进程。原进程没有因本次交接被终止。

## 原始任务范围

- 在 Enflame S60 上适配 Qwen3-0.6B，实际模型 `/models/Qwen3-0.6B/`。
- 项目 `/workspace/vllm-plugin-FL`，分支 `adapt/vllm032-from-050`。
- 目标官方 vLLM `0.32.0`，固定上游 commit `5df63a7203cdb9328d824a27b682e77c7b9928be`，本地 empty build 源码 `/workspace/s60-adaptation/src/vllm`。
- 原始用户指令没有明确规定所有提示词都必须与 NVIDIA 逐 token 完全相同。Agent 后续采用了严格 token 对照；这些测试的失败结果仍应保留，不能自行修改验收标准后宣称通过。
- 本次中止不是适配完成。中止后的用户新指令已明确接受“这个精度差异”；这属于用户的验收决定，不是数值差异消失或严格 token 对齐通过。

## 已实现与已观察的验证

以下是不同阶段的已有证据，不是对当前全部工作树重新执行的最终验收。

| 项目 | 已有结果 | 证据及边界 |
| --- | --- | --- |
| Worker / ModelRunner / Attention | 已迁移相关 0.32 接口、KV 布局与流/设备处理 | 代码在未提交工作树中；最终整体回归未完成 |
| GCU Inductor 整数 ABI | 修正全局 int64→int32 替换导致的地址解释问题，并区分编译缓存 | CPU 参考查表测试覆盖 8 种组合；见 STATUS 与 `logs/index-diff-preserve-fresh.log` |
| 双卡通信 | 两 rank FlagCX all-reduce 和 TP=2 eager 已运行 | `logs/flagcx-collective.log`、`results-tp2-flagcx.json` |
| S60 eager / Graph | 5 提示、每提示 32 token，共 160 token 一致 | `results-eager-extended.json`、`results-graph-extended.json`；Graph 使用 `TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1`，不是默认 Graph 无条件通过 |
| HTTP 服务 | eager 与 Graph 的有限并发及流式断言通过 | `results-serve-eager.json`、`results-serve-graph.json`；不是完整服务验收 |
| NVIDIA 参考 | RTX 4090 实际运行官方 0.32 CUDA 参考，同模型文件 SHA-256 校验 | `results-nvidia-v1-eager-extended.json`；参考安装和生成已完成，后续不必重复安装 |
| CI setup | 0.32 empty 依赖与实际 setup 有通过记录 | `logs/ci-setup-v032-local-transport.log`；Git 运输曾使用经 commit 验证的本地官方浅克隆 |
| CI / Docker 发布 | 配方已更新，构建、发布和工作流验证未完成 | 旧 CI 镜像配置仍有历史 0.28 digest，不能当作已验证的 0.32 镜像 |

可核对的已有单测结果：

- `logs/unit-full-codegen.log`：1,165 passed、229 skipped、1 error；缺少 `torch_npu` 的收集错误意味着不是完整测试通过。
- `logs/unit-post-ci-setup.log`：75 passed。
- `logs/unit-nvidia-followup.log`：86 passed。
- `logs/unit-gcu-normalization-v3.log`：48 passed；属于候选归一化修改当时的有限回归。
- 上述测试分属不同阶段，不能累加成一个总通过数，也不能视为中止时全部代码的最终回归。

## 精度排查的配置与结果

表内“完全一致”按整条提示的 32 个 token 判断，不是准确率、任务质量分数或全部 token 的一致比例。不同 head、RMSNorm 配置必须与相应 NVIDIA 参考分别比较。

| 配置 | 测试集 | 完全一致 | 主要未通过项 |
| --- | --- | --- | --- |
| 早期 S60 BF16 基线 | 原始 5 提示 | 3/5 | 算术第 7、代码第 13 token 分歧 |
| 原生 FP32 head + RMSNorm 工作树候选 | 原始 5 提示 | 5/5 | 仅对此配置和有限样本成立；不替代 BF16 验收 |
| 同一候选 + FP32 head | 新增 10 提示 | 8/10 | Japan 第 14、JSON 第 16 token 分歧 |
| RMSNorm 工作树候选，原 BF16 head | 原始 5 提示 | 3/5 | Paris 第 11、算术第 7 token 分歧 |
| 全局禁用 FlagGems mean 的诊断 | BF16 5 提示 / FP32 head 10 提示 | 3/5、7/10 | 改善部分提示，同时产生其他分歧；不是有效整体修复 |
| CPU 完整 FP64 RMSNorm 诊断 | BF16 5 提示 | 2/5 | Paris 第 11、算术第 30、代码第 13 token 分歧 |
| CPU 完整 FP64 RMSNorm 诊断 + FP32 head | 新增 10 提示 | 9/10 | TCP/UDP 第 25 token 分歧 |

对照文件包括 `stress-fp32head-comparison.json`、`compare-bf16head-production.json`、`stress-no-gems-mean-comparison.json`、`bf16-no-gems-mean-comparison.json`、`stress-oracle-full-comparison.json`、`bf16-oracle-full-comparison.json`。

CPU FP64 是诊断配置，不是可部署的修复方案，也没有替代真实 NVIDIA 参考。

## 从批处理分歧到局部算子的定位过程

1. Japan 提示单条运行与 NVIDIA 的 32 token 一致，但 S60 同一提示批处理时从第 14 token 分歧。说明观察到的配置存在批次相关行为，并不说明注意力算子已经被证明有 bug。
2. 对齐实际 token、位置与此前历史后，第 8 层（索引 7）注意力的当前 Q/K/V 一致，但历史 KV 中位置 1 有差异：554 个 BF16 元素，最大绝对差 0.0625。
3. 固定 Q、布局和参数，仅交换两份真实 KV 历史，能重现捕获的全部 44 个注意力输出差异，最大绝对差 0.001953125。这证明历史 KV 足以解释该次注意力输出差异，不能归因于当前步注意力计算。
4. 继续追溯预填充：前 6 层边界一致；第 7 层（索引 6）post-attention RMSNorm 的输入一致，输出出现 1 个 BF16 元素差异，最大绝对差 0.0009765625；经 MLP 后扩大到 164 个元素差异。
5. 独立重放一度不能复现模型进程差异。随后启用 FL 运行时可复现，逐步骤比较在 FlagGems mean 归约发现 6 个 FP32 中间值差异，最大约 5.96×10⁻⁸。仅更换 `mean` 为 `sum / N` 仍保留临界差异。
6. 更换独立 GCU RMS 算子入口后，启用 FL 前后结果一致，但仍与 CPU FP64 的一个 BF16 值不同。仅把方差计算改成 CPU FP64 也不能消除该值差异；完整 FP64 RMSNorm 可以消除局部差异，但整模型仍未通过，结果如上表。

证据：`logs/japan-cache-analysis.log`、`logs/japan-attention-cache-swap.log`、`logs/japan-prefill-layer6-analysis.log`、`logs/rms-gems-stages.log`、`logs/replay-rms-sumdiv.log`、`logs/replay-registered-rms-v2.log`、`logs/replay-oracle-variance.log`、`logs/replay-oracle-full.log`。

## 最后得到的关键纠正

在同一份真实输入上实测 NVIDIA 官方 fused RMSNorm：

```text
full boundary -0.2080078125 CPU64neq 1
row boundary  -0.2080078125 CPU64neq 1
```

NVIDIA 的实际临界值与独立 GCU 算子相同，而不是 CPU FP64 舍入后的 `-0.208984375`。证据：`logs/cuda-rms-boundary.log`。

因此前面观察到的 `0.0009765625` 差异是“某些计算路径之间的差异”，**不能单凭它认定 GCU 算错，更不能把 CPU FP64 值直接当作 NVIDIA 的正确舍入结果**。该元素相对于 CPU FP64 值约 0.47% 的差异，也不是模型整体准确率损失。此前状态说明中的“局部高精度参考已通过”不能扩大解释为 NVIDIA 精度验收通过。

## Agent 停顿与恢复记录

- 多次返回输入提示符与 `max_iterations: 200` 有关；已数到某轮恰好 200 个含工具调用的助手响应。达到限制不是任务完成，也不是进程崩溃。
- 断线后实际恢复会话为 `d08319f6`。中断留下一个没有保存工具结果的 shell 调用，后续接口报 `No tool output found for function call ...`。
- 已在 Agent 的输出历史校验中添加中断结果说明，保留调用 ID，明确执行状态未知，避免自动重跑命令或伪造成功；原始审计记录不被改写。该次 122 项相关测试通过，并用真实会话验证接口接受修复后的请求。
- 修复说明见 `/workspace/flagscale-agent-repairs/20261030T101046Z/修复记录.md`。
- 后续出现的 `[TASK_COMPLETE]` 有时只针对上下文清理，不能作为整体适配完成标记。最后原始会话仍为未完成状态。

## 中止时的代码状态和未完成工作

- 分支：`adapt/vllm032-from-050`，HEAD `64c9d216ee6c66acb0b9fc8c097b6c1eab3a4ef4`。
- 工作树有 19 个已跟踪文件修改、7 个未跟踪文件。已跟踪 diff 为 1,051 行增加、1,488 行删除；新增未跟踪文件不包含在该 diff 行数中。
- 当前仍包含 GCU 与 FlagGems 归一化路径的 RMSNorm 候选修改，以及相应测试；它不是已经通过最终精度回归的版本。没有擅自回退或提交。
- `git diff --check` 在本次中止检查时通过；这是格式检查，不代表功能正确。
- 全面精度标准、当前候选的取舍、最终 eager/Graph/TP/HTTP 回归仍需后续处理。
- 完整测试仍有可选依赖收集错误；更大模型/多模态 gate 尚未运行。原任务仅指定 Qwen3-0.6B，不能把额外模型测试说成用户明确要求。
- Docker 0.32 镜像构建、发布与 CI 工作流验证未完成。
- 没有基于当前未提交候选版本的最终性能、质量或生产可用性结论。

以上未完成项由用户接手后的 Agent 继续处理。本次仅中止原轮次和保存交接材料，本记录整理者没有启动新的测试或后续适配任务。用户后续明确接受精度差异，允许收尾继续；原始比较结果和限制仍须保留。

## 记录入口

- 本记录：`/workspace/flagscale-agent-task-summary.md`。
- 原始阶段状态：`/workspace/s60-adaptation/STATUS.md`，按章节保留历史实验；阅读时以后面的限定和本记录的最新纠正为准。
- 早期监控：`/workspace/flagscale-agent-task-monitor.md` 与 `/workspace/flagscale-agent-monitor/执行时间线.md`。持续采集已于 05:04 UTC 暂停，不能把早期监控的 PID/阶段当作当前状态。
- 任务产物：`/workspace/s60-adaptation/`；实验日志：其下 `logs/`。
- 可恢复原会话：`/root/.flagscale/sessions/d08319f6/`。
- 交接快照：`/workspace/s60-adaptation/handoff/20261030T135753Z/`。
