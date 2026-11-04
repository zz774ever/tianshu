# FlagScale-Agent 完整命令归档

- [网页阅读版说明](../../docs/flagscale-agent-command-history-guide.md)
- [单份完整 Markdown](../../docs/flagscale-agent-complete-command-history.md)：8,501,759 字节，保留全部 shell、脚本写入/修改和其余工具调用。
- [完整脱敏审计 JSONL（gzip）](flagscale-agent-all-tool-records.redacted.jsonl.gz)：解压后每行一项工具记录，含完整保存结果。
- [覆盖和脚本校验清单](coverage-manifest.json)。
- [命令覆盖、Markdown 和脱敏验证结果](validation.json)。

截止时间：2026-11-04T15:52:53.981495+08:00。

主会话 7094 条消息、4045 次工具调用、1319 次 shell 调用；另有 446 项主助手补充记录，当前脚本快照 85 份。

Markdown 对过长结果提供有标记的摘录，命令和参数保留全文；JSONL 保存脱敏后的完整历史结果。两个文件都不补造没有保存的工具返回。原始私密对话、密钥、模型权重、tensor dump 和服务大日志没有上传。

```bash
gzip -dk flagscale-agent-all-tool-records.redacted.jsonl.gz
sha256sum flagscale-agent-all-tool-records.redacted.jsonl
```

解压后 JSONL 的 SHA256：`4aad8794204bbb9ebca8eae2621065f065abd6c8d5b962ba4001381cb11e9726`。
单份完整 Markdown 的 SHA256：`1c302937b9434188b0f4374824293a681f1b9e3a8aa920c00a16a5caf019d7f9`。

文档归档不代表模型或 CI 全部通过；执行结果、未完成项及运行中的诊断按文内时点区分。
