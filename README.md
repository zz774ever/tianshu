# vLLM 0.32 适配记录

## 新机器环境搭建与测试教程

- **[本机 u180 / n180 纯文本复现：从现有容器开始](docs/iluvatar-vllm032-local-reproduction.md)**：已核实路径、驱动依赖、venv入口、双卡通信、文本eager/graph及流式API；当前机器请优先阅读，不运行图像门禁。
- **[从零准备天数 CoreX 环境并运行测试](docs/iluvatar-vllm032-fresh-machine-setup.md)**：宿主机与镜像、FlagTree / FlagGems / FlagCX、EMPTY vLLM 0.32、适配插件、模型下载、小模型冒烟和图文门禁的顺序命令。
- [配套环境与验证脚本](tools/iluvatar-repro/)：环境激活、版本及库检查、真实 FlagCX 通信和 Qwen3-4B 冒烟。

需要在另一台机器复现环境时，请先看这份教程。下面的完整命令档案用于追溯历史操作。

## FlagScale-Agent 完整命令档案（2026-11-04）

- [环境建立与后续操作：网页阅读版](docs/flagscale-agent-command-history-guide.md)
- [完整单份 Markdown：逐条命令、文件修改与脚本全文](docs/flagscale-agent-complete-command-history.md)
- [脱敏审计原始结果、覆盖统计与校验](records/flagscale-agent-command-history-20261104/README.md)

完整文件较大，请使用 Raw/Download 下载在编辑器阅读。原有 S60 和 Iluvatar 报告继续保留。


## 归档索引

- [S60 完整适配技术报告](docs/s60-vllm032-detailed-report.md)：版本差异、36 个改动文件逐项说明、根因与修复链、精度数值、完整请求矩阵、失败尝试、未做事项和复现方法。
- [S60 适配与验证总说明](docs/s60-vllm032-overview.md)：总体结论、适配内容、验收矩阵、配置前提、未闭环事项与证据导航。

- [S60 完整记录归档与验收边界](records/s60-vllm032/README.md)：日志、结果、诊断数据、使用说明及历史交付快照；公开脱敏副本，不包含凭据或原始聊天历史。
- [Iluvatar BI-V150 阶段报告](docs/iluvatar-vllm032-report.md)：保留已有报告。

以下为原有 Iluvatar 阶段说明，其测试数字与限制仅属于 Iluvatar，不适用于 S60。

# Iluvatar BI-V150：vLLM 0.32 适配阶段报告

供导师审阅的适配记录。主要实机执行日期为 2026-10-30，文档整理日期为 2026-11-02。

## 从这里开始

请阅读 **[最终适配执行记录](docs/iluvatar-vllm032-report.md)**，其中包含环境版本、代码改动、执行时间线、测试结果、启动命令和原始证据索引。

## 阶段结论

- 已完成隔离的 vLLM 0.32.0 EMPTY 环境、Iluvatar 兼容改动及基础验证。
- Qwen3-4B 已有 TP1/TP2 eager/graph 文本生成证据。
- 相关单元回归为 **157 passed、1 warning**，本地依赖栈核验通过。
- 最近大模型复测：27B graph 为 26/26；35B eager、graph 各为 25/26，同一图片 OCR 失败。
- 35B OCR 输出不稳定的归因尚未确定；按用户要求停止深入排查，保留失败证据。
- 完整 104 请求全部通过、NVIDIA 逐 token 对照和远端硬件 CI 尚未达成。

这是带已知问题的阶段交付，不能表述为完整适配验收通过或发布声明。

## 仓库内容

原有 Iluvatar 部分仅包含审阅文档，报告中的 `/workspace/...` 为执行容器内的证据位置，不能直接在 GitHub 访问。新增 S60 归档位于 `records/s60-vllm032/`，包含脱敏日志、诊断脚本和适配交付补丁，不包含模型权重或访问令牌。

如需导师直接访问私有仓库，请由仓库所有者在 GitHub 的 **Settings → Collaborators** 中添加导师账号。
