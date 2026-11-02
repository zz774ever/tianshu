# S60 / vLLM 0.32 适配记录归档

本目录整理本次适配的现有记录，而不是重新运行实验。原始工作目录保留不变。

## 从哪里开始

- [最终状态与完整时间线](records/STATUS.md)
- [新版本使用说明](usage/enflame-vllm032.md) 与 [原使用说明](usage/enflame.md)
- [最终交付快照](records/handoff/20261102T055334Z/STATUS.md)
- [精度对齐审计](workspace-reports/precision-alignment-audit-20261102.md)
- [历史任务总结](workspace-reports/flagscale-agent-task-summary.md)
- `records/logs/`：原有成功、失败及诊断日志，不仅保留成功记录。
- `records/gate-results/`：真实设备验证结果。
- `records/diagnostics/`：补充诊断，不能代替正式验收。
- `records/handoff/`：历史交付快照，包含补丁及未跟踪文件归档。
- `records/` 顶层：结果 JSON、对比脚本、探针、算子差异记录和张量诊断数据。

## 验收状态（不能解释为全部通过）

- 27B / 35B eager 与 Graph 四组正式请求共 **103/104**。
- 35B eager 单文本断言原始结果为 **FAIL**，用户明确接受这个特定例外；不是 104/104。
- 0.6B 有 offline eager、Graph、TP2、在线服务和 NVIDIA 逐 token 对比证据；严格精度对齐未通过，用户接受已披露数值差异。
- 27B / 35B 不能仅凭在线服务结果声称完成独立 offline 全套或 NVIDIA 逐 token 验收。
- Harbor 拉取及依赖该镜像的构建按用户授权跳过；镜像发布、runner CI 未验证，不能标记通过。
- 曾有 115 项回归与 7 项构建入口回归通过记录；本次归档不重跑模型或测试。
- FlagGems 缺失算子上游待办汇总尚非完整闭环，已有算子差异和诊断记录不等同于完整提交清单。

## 归档与隐私规则

这是公开仓库的脱敏副本：凭据和内部 IPv4 地址做脱敏，源文件不修改。原始聊天会话因可能包含凭据及隐私不公开，明确列入 `EXCLUSIONS.json`；不应把聊天历史当实验输出。

运行时、依赖下载、第三方源码树、编译缓存、socket/PID 不上传；诊断 `.pt` 张量使用 gzip 无损压缩为 `.pt.gz`（`gzip -dk 文件.pt.gz` 可恢复），不是模型权重。没有加载或反序列化这些张量。

`MANIFEST.json` 记录每个归档文件的 SHA256、大小及原文件 SHA256；`REDACTIONS.json` 列出发生脱敏的文件，`EXCLUSIONS.json` 列出排除项。历史快照的内嵌哈希描述原始交付，脱敏后可能不再匹配，公开副本以本层 `MANIFEST.json` 为准。
