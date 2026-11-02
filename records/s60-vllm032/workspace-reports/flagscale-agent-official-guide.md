# FlagScale Agent 官方流程与本次任务判断依据

核对日期：2026-11-02 UTC。

本文通过 GitHub API 和官方仓库原始文件读取资料，并对照容器中的安装目录。它是流程审阅记录，不是一次新的适配执行或最终验收。本次没有中断、重启或向任务 Agent 发送指令，也没有更新安装版本。

## 1. 确认的官方仓库与版本

- 官方项目：[flagos-ai/FlagScale-Agent](https://github.com/flagos-ai/FlagScale-Agent)。这里的名称是 FlagScale Agent，不是另一个名为 scale-agent 的项目。
- 默认分支：`main`。读取时的分支提交：`4dff90ce84a7e8cfaac1af9a83f558baacc28d51`，提交时间 2026-09-24 03:38:43 UTC。
- GitHub API 此次没有返回正式 release；README 的 `0.1.0` 标识不应代替提交版本。
- 本地包版本 `0.1.0`，editable 安装目录 `/workspace/flagscale-agent-migration/FlagScale-Agent`。
- 已下载的官方资料保存在 `/workspace/flagscale-agent-official-review/4dff90ce84a7/`，包含中英文 README、配置示例、任务相关技能、运行循环、计划/会话/Guard 源码以及公开 issue。

后面的官方链接固定到本次读取的 commit，便于以后区分上游更新。

## 2. Agent 自身怎样执行任务

[官方中文说明](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/README_zh.md#L88) 描述的是 ReAct 循环：

```text
用户请求
  → 加载技能/知识，定义计划和验收标准
  → 模型决定行动
  → Guard 检查
  → 执行工具，保存观察结果
  → 更新计划/记忆
  → 再次推理
  → 完成、需要用户信息、被中断、达到限制或报错后结束本轮
```

一次用户输入启动一个 turn；一个 turn 里可以有很多次模型和工具交互。一个 turn 结束，并不自动表示整个多小时适配任务完成。

| 组件 | 实际作用 | 判断边界 |
| --- | --- | --- |
| Skills / Knowledge | 提供任务方法、验证矩阵和约束 | 文档中的流程不是已经执行的证据 |
| Plan | 保存步骤、验收条件、状态、验证说明 | 标成 done 仍要核对实际日志和产物 |
| Memory | 跨轮次保留事实、经验和诊断结论 | 环境、文件和进程状态可能过期 |
| Guard | 提醒、阻止操作或要求补充理由 | Guard 通过不等于正确性测试通过 |
| Judge | 用模型判断分类、循环和执行风险等 | 即使没有本地子任务，也可能在等 Judge 的网络请求 |
| evict / recall | 腾出活动上下文，之后按索引召回 | 不代表清除原始任务，也不表示任务完成 |
| hard_reset | 保存摘要后重建活动上下文 | 官方意图是接续原任务，不是结束任务 |

Guard 主要有 advisory/inject、block、escalate 三类行为。可覆盖的 block 使用 `_override_reason`；escalate 不应被理解为普通提醒。`VerificationGuard` 会要求标记完成时附验证内容，但源码本身也说明，非空验证列表不等于机器独立核验了所有事实。

## 3. 为什么它会停，以及怎样判断

依据：[执行循环](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/react/kernel.py)、[完成标记定义](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/react/prompt.py#L152)、[配置源码](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/react/config.py#L80)。

| 现象 | 可能含义 | 要核对的证据 |
| --- | --- | --- |
| 主线程在 `prompt_toolkit.prompt()` | 本轮已结束，等待下一次输入 | 最后会话、调用数、错误、停止标记 |
| 主线程在 Responses 流读取 | 正在等待模型回复 | 请求栈、耗时、随后是否产生消息 |
| 主线程在 Judge / safety classify | 等辅助判断模型 | Judge 调用栈；不是硬件推理进程 |
| 编译器、引擎等子进程活跃 | 工具或诊断仍在执行 | 对应 job、日志增长、实际输出 |
| 恰好达到迭代限制 | 本轮循环预算耗尽 | 实际配置与循环次数，不看界面文案猜测 |
| `[NEED_USER_INPUT]` | 按设计应缺少用户决策、确认或外部信息 | 是否明确说出需要什么；不是自动证明缺权限 |
| `[TASK_COMPLETE]` | 按设计应代表所有任务交付完成 | 原始范围、剩余计划、实际结果，不能只信标记 |
| 缺少工具调用结果的接口错误 | 历史中的 call/result 协议不完整 | 匹配调用 ID；不应当作适配代码或 GCU 报错 |

官方 README 和配置示例给出的 `max_iterations` 是 200；源码数据类默认值是 200000。此次只读取了本地配置的非敏感字段，实际 YAML 为 `max_iterations: 200`，因此此前多次 200 轮后返回输入框有配置依据。不能把文档示例、源码默认值、实际配置混在一起。

README 把 `max_continuations` 概述为空响应限制；源码还将它用于无工具且无停止标记的文本续写计数。它不是整个任务可以恢复的总次数。配置的 `time_budget_sec` 在源码中说明为时间提醒/收尾预算，不是硬性定时杀进程；不能拿它直接算完成 ETA。

源码保留了 `KernelResult.stop_reason`，但当前 `_react_loop()` 通常只显示时间和 token 摘要，没有把所有停止原因醒目地显示出来。因此“界面停了”必须结合会话和栈判断。

清理上下文后输出 `[TASK_COMPLETE]` 与官方“所有交付完成”的定义不一致。此前本会话发生过只完成上下文清理的完成声明；那不能作为适配验收结论。

## 4. 官方恢复与重载机制

依据：[斜杠命令](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/README_zh.md#L417)、[命令实现](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/react/commands.py)、[会话锁](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/react/session.py#L200)。

- `/session`：确认当前会话、目录和 turn。
- `/resume`：列出可恢复会话；`/resume <ID>` 恢复指定会话。
- `/reload`：保存会话后重启进程，恢复同一会话，使 Python 代码修改生效。
- `/reload config`：仅重载配置和技能，不加载新的 Python 代码。
- 会话锁用于防止两个进程同时写同一会话。重新进入容器不代表旧进程必然退出；先检查持有者和实际运行状态。
- 恢复会话不会自动证明原来的本地 job、远端进程或服务还活着。先核对实际状态，再决定续跑，避免重复安装或重复推理。
- 退出信号处理尝试保存会话并清理注册的本地 shell jobs；`SIGKILL` 无法走保存逻辑。`SIGINT` 在执行循环和输入提示符的语义不同，不能不看状态就反复发送。

本次任务的已知会话是 `d08319f6`；早期失败会话 `d430689c` 不是适配任务的当前恢复点。若确认会话没有其他活动持有者，现有实现可用：

```bash
flagscale-agent --config /root/.flagscale/agent.yaml --auto-resume=d08319f6
```

其中 `--auto-resume=...` 的等号形式来自当前实现；源码自行扫描该形式，不能假定空格形式与之等价。交互恢复也可使用官方文档的 `/resume d08319f6`。

## 5. vLLM 硬件适配的完整顺序

依据：[硬件适配技能](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/skills/infer-vllm-hw-adapt/SKILL.md)、[框架升级技能](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/skills/infer-vllm-plugin-upgrade/SKILL.md)。

1. **明确范围和基线**：记录硬件、可用卡、分支/commit、目标上游、模型、依赖、验证模式与 CI 范围。硬件适配技能默认已有共享框架升级基线；本次还实际涉及版本迁移，不能把两项工作量混为单纯启动测试。
2. **确认环境**：非 CUDA 后端使用指定源码的 `VLLM_TARGET_DEVICE=empty`；插件以 `--no-build-isolation --no-deps` 安装，避免替换供应商运行栈。确认实际 import 指向本次 checkout。
3. **差异分析**：对照旧版、目标上游和插件，审查 Platform、Worker、Attention、算子路由、Graph、模型、打包和 CI。
4. **按依赖实现**：platform/device → worker/cache → attention → ops/dispatch → compilation/graph → models → packaging/CI。每一块先做有限回归；先 eager 再 Graph。
5. **实际设备验证**：imports、单元/功能、真实离线完整生成、服务完整请求、并发、TP 和受影响架构。端口打开、加载权重、单测通过都不能单独等价于推理验收。
6. **输出正确性**：相同权重/tokenizer、相同关键生成配置，对照 NVIDIA 上游，保存 JSON、首个分歧位置和双方日志，写明精度等级或用户明确接受的差异。
7. **完整 gate 与三组件同栈**：按任务仓库的正式脚本执行适用矩阵，保留每例结果，证明 FlagGems、FlagTree、FlagCX 同时实际参与运行。
8. **CI 与交付**：检查镜像、版本断言、runner、模型挂载、触发条件、测试矩阵、汇总状态与日志上传。最终报告区分当前代码验证、历史证据、阻塞和未测项。

官方技能明确规定不修改上游/已安装 vLLM 源码，供应商补丁要有范围限制，不能以吞异常或无说明的 fallback 掩盖缺失功能。

## 6. 精度规则：不是只有“所有 token 一样”

依据：[官方比较协议](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/skills/infer-precision-check/SKILL.md#L60)。

| 等级 | 官方条件/用途 | 不能直接推出什么 |
| --- | --- | --- |
| Tier 1 | token ID 严格一致；文档将前 10 个 token、确定性注意力和基线文本列为严格要求 | 局部张量接近不代表 Tier 1；改用不同 head/dtype 后通过也不能替代原配置 |
| Tier 2 | 对符合条件的后段 FP16/BF16 累积误差、Flash Attention 噪声，参考 token 在每个位置的 Top-5 候选中 | 首个分歧 token 进入 Top-5 不代表所有位置通过；“5 例中 3 例一样”也不是 Tier 2 |
| Tier 3 | 数值限制等特定情况下的语义等价兜底，需逐提示词判断并记录 | 用户一句接受差异不能自动生成完整语义质量测评结果 |

细节：文档把 Tier 2 的一项用途写为第 11–30 token；没有给本次全部 32-token 输出自动放行的规则。它的示例 `compare.py` 主要进行严格比较，不能当作已实现完整三档判定的工具；示例仅比较共同 token 前缀也不足以证明输出长度相同。正式判断应另核对长度、完整输出和对应参考。

第一处分歧后的两次独立生成，其输入历史已经不同。若要把某步候选概率差异归因到同一个算子，应对齐实际输入 token、位置和历史；这属于因果诊断要求，不能只按相同生成步序号配对。

此前算术在第 7 token 分歧，处于官方要求严格的前段；代码在第 13 token 分歧，则可以评估是否满足 Tier 2 的限定条件。后者也要有完整候选概率证据，不能因为“BF16 常有误差”直接宣告通过。

用户后来明确说“这个精度差异是可以接受的”。这是本任务的范围/验收决定，可以结束已接受差异的深挖；记录应写“已知差异经用户接受”，保留严格对齐未通过的事实。它不自动豁免 CI、功能或完整 gate。

CPU FP64 参考是数值诊断工具，不能代替 NVIDIA 官方结果。此任务最后的 NVIDIA fused RMSNorm 实测与独立 GCU 在临界值上相同，已否定“仅凭该值不同于 CPU FP64 就判 GCU 算错”的推断。

## 7. 官方完整验收比小模型 smoke 更广

[硬件验证章节](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/skills/infer-vllm-hw-adapt/SKILL.md#L113) 要求：

- FlagGems、FlagTree、FlagCX 在同一固定环境同时启用；分别 import 或分开测过不够。需真实编译、算子路由和 collective/TP 证据。
- 正式目录为目标插件仓库的 `tools/adaptation-gate-cases`。这不是本 Agent 仓库内的测试目录。
- 技能描述的当前矩阵含 Qwen3.6-27B、Qwen3.6-35B-A3B，各 eager/Graph，加文本、图像、混合与八路并发，共 4 组、20 场景、104 请求。实际数量应从将要提交的插件代码重新发现，不能永远固定这些数字。
- 缺权重、fixture、过滤、跳过或超时均需列为未通过/阻塞，不以少量 Qwen3-0.6B smoke 替代。
- [CI 章节](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/skills/infer-vllm-hw-adapt/SKILL.md#L161) 将 CI 集成列为完整后端适配的必要项。

需要区分两层合同：用户原始指令只指定 S60、Qwen3-0.6B 和 vLLM 0.32；上述更广矩阵来自官方技能的完整后端验收要求，并非用户逐项明确提出。后续应把二者分别列出，明确是交付限定模型的适配结果，还是要求通过完整后端 gate。不能擅自扩展成无限任务，也不能把技能规定的未通过项悄悄写成已完成。

## 8. 什么时候继续排查，什么时候应改变方向

[官方调试策略](https://github.com/flagos-ai/FlagScale-Agent/blob/4dff90ce84a7e8cfaac1af9a83f558baacc28d51/flagscale_agent/skills/debug-strategy/SKILL.md#L30) 有 Two-Strike Rule：同类失败连续两次后停止叠加局部修补，重新审查上游假设，提出不同的方法；三种不同尝试后仍失败，或需要设计取舍/外部信息时，应向用户说明。

这不是“两次任意实验以后任务必须停止”，而是反对在错误假设下重复同类修补。每轮应说明假设、实验、具体结果、排除了什么和下一步。已有日志和结果足以回答时，不重复启动昂贵任务。

后续判断“是否值得继续”采用：

1. 是否仍在用户要求和已确认验收标准内。
2. 当前问题是功能错误、未达到精度等级，还是已接受的数值差异。
3. 最新实验能否区分两个具体假设，且有明确停止条件。
4. 同类尝试是否只在结果间来回摆动、产生回归。
5. 是否有未完成的必需交付比继续微调更优先。

此前建议的“再查 30–60 分钟”是排查预算建议，不是官方规定，更不是可靠完成 ETA。后续时间估计应拆成具体剩余阶段；根因未定时不保证“再几小时就完成”。

## 9. 公开 issue：相关现象已有报告，但不是本次根因证明

截至本次读取，下面两项均为 open，均无评论。它们是仓库中的公开问题报告，不等于维护者已确认或已有合并修复：

- [Issue #48](https://github.com/flagos-ai/FlagScale-Agent/issues/48)：长任务把 `[NEED_USER_INPUT]` 用作会话交接，多个 Guard 在高上下文压力下消耗最后预算，脚本写好却没执行。
- [Issue #47](https://github.com/flagos-ai/FlagScale-Agent/issues/47)：用户禁止 evict/hard_reset 时，ContextPressureGuard 可能没有可行工作路径。

它们支持重点检查“上下文/Guard 循环”这种可能性；不能据此把本次所有停顿都归为同一个 bug。本次部分停顿已有 200 轮限制的独立证据，恢复报错也有缺少 tool result 的独立复现。

## 10. 上游与本地差异

逐字节比较此次下载的相关文件：

- `infer-vllm-hw-adapt`、`infer-precision-check`、`infer-vllm-plugin-upgrade`、`debug-strategy`、`ops-discipline`、`infer-env-setup` 均与安装目录一致。
- 抽查的 `kernel.py`、`commands.py`、`session.py`、计划和若干 Guard 也一致。
- `agent.py`、`history.py`、`config.py`、README 和配置示例存在本地变化，包括此前的 Responses 协议、配置选择、工具结果和日志/恢复相关处理。

因此官方文档足以解释工作模型，但不能假定覆盖官方版本不会丢失本地修复。此次只下载资料并审阅，没有升级、覆盖或回退安装目录。

## 11. 对当前任务的判断基线

以下基于 2026-10-30 的执行记录和用户后续决定，不是 11-02 对所有任务阶段重跑后的结果：

| 范围 | 已有事实 | 后续怎样表述 |
| --- | --- | --- |
| 基础适配 | 有迁移、eager、TP2、Graph、有限 HTTP 并发/流式证据 | 保留具体配置、代码版本和日志，不推广为所有模型通过 |
| 精度 | 严格 token 比较有差异，用户明确接受 | “已知差异经用户接受”；不继续无授权深挖，不写 Tier 1 已过 |
| 最新有限单测 | 收尾阶段有 76 passed 记录 | 不是完整 suite、完整 gate 或全部当前代码的无条件背书 |
| 完整单测 | 历史有 1165 passed、229 skipped、1 collection error | 有收集错误就不称完整通过；说明依赖与作用范围 |
| 完整 gate | 历史记录未执行完整更广模型矩阵 | 未验证或范围待明确，不能自动视为精度接受后一并通过 |
| CI / 镜像 | 配方/setup 有修改及验证，构建/发布/工作流仍有缺口 | 逐项核对，不能以配置文件改了等同运行成功 |
| 完成/停止 | 曾多次达轮次上限，也曾错误把上下文清理标成完成 | 以实际停止原因、范围与证据判定，不看单个标记 |

原始任务阶段材料见 `/workspace/flagscale-agent-task-summary.md`，实验与阶段记录见 `/workspace/s60-adaptation/STATUS.md`。恢复点为 `/root/.flagscale/sessions/d08319f6/`。这些材料可能包含不同时间的结论；引用时明确配置、阶段和日期。

## 12. 后续每次状态检查的最小记录

```text
观察时间（UTC）：
会话 / turn / 最新消息：
实际阶段 / 当前动作：
进程状态：执行工具 / 等模型 / 等 Judge / 等输入 / 已退出
最新新增证据：
已通过项与对应配置、代码版本：
未通过 / 未测 / 用户接受的差异：
停止原因（如已停止）：
下一步及停止条件：
耗时估计依据（不能确定则写明）：
```

以上用于后续判断和记录。本次审阅没有恢复持续监控，也没有接管用户正在进行的后续工作。

## 13. 补充：旧版 Enflame 实际适配的对照资料

用户提供的 `0.4.0-dev/docs/usage/enflame.md` 及关联镜像配方已固定到插件提交 `732bdbd61e6f3965fb1017130215e3a96604f953` 阅读并留档。详细对照见 [Enflame 旧版适配参考](/workspace/enflame-previous-adaptation-reference.md)。该资料描述 vLLM 0.28 的验证历史，当前目标为 0.32，不能直接继承通过结论。新记录也补充了 11-02 当次 eager 请求结果和 Graph 编译结果；本节之前标为历史的状态表仍保留其原有时间边界。
