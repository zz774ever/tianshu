# Iluvatar PR #674 / FlagGems 5.5：本轮证据

插件提交：`7a94aeec80fbb795d5596569eb7d40cfe5460106`。硬件为 Iluvatar BI-V150，TP4、BF16、上下文 32768。两模型均保留 `slice,mm,mm_out` 排除项，Graph 使用 `[1,2,4,8,16,32]` 捕获大小，Eager 使用 `--enforce-eager`。

| 模型 | Graph | Eager | 执行时间 |
| --- | --- | --- | --- |
| Qwen3.6-27B | 26/26 | 26/26 | 2026-11-06 23:29:59 至 23:48:06 |
| Qwen3.6-35B-A3B | 26/26 | 26/26 | 2026-11-07 00:24:48 至 00:44:58 |
| 总计 | 52/52 | 52/52 | Asia/Shanghai |

合计 **104/104 请求、20/20 pytest 场景通过**。这是同一提交与同一依赖下实际分别运行的四轮测试。此前 FlagTree 0.7 / FlagGems 5.3.5、`FULL_DECODE_ONLY` 等历史数据不混入本轮。

## 复现入口

- [环境来源、设计、安装、四轮测试和目标机器差异](../../docs/iluvatar-pr674-gems55-gate-reproduction.md)。
- [配套可执行脚本](../../tools/gate-repro-20261107/)：安装、激活、预检查、单轮 gate。
- [整体结果与文件 SHA256](manifest.json)。
- [模型配置、处理器、chat template 的 SHA256 及权重分片大小](model-fingerprints.json)。这不是全部权重的字节校验，模型原始下载 revision 未独立确认。

## 原始证据

| 内容 | 27B | 35B |
| --- | --- | --- |
| 实际版本、模块路径和环境 | [environment.json](27b/environment.json) | [environment.json](35b/environment.json) |
| 逐场景校验和退出码 | [verification.json](27b/verification.json) | [verification.json](35b/verification.json) |
| Graph 服务日志 | [server.log](27b/graph/server.log) | [server.log](35b/graph/server.log) |
| Graph pytest 日志 | [tests.log](27b/graph/tests.log) | [tests.log](35b/graph/tests.log) |
| Graph 原始 JSON | [结果目录](27b/graph/results/) | [结果目录](35b/graph/results/) |
| Eager 服务日志 | [server.log](27b/eager/server.log) | [server.log](35b/eager/server.log) |
| Eager pytest 日志 | [tests.log](27b/eager/tests.log) | [tests.log](35b/eager/tests.log) |
| Eager 原始 JSON | [结果目录](27b/eager/results/) | [结果目录](35b/eager/results/) |
| 完成后显存状态 | [gpu-after.txt](27b/gpu-after.txt) | [gpu-after.txt](35b/gpu-after.txt) |

[27B 的 M-RoPE 单元测试日志](27b/unit-tests.log)为 10 passed。27B `verification.json` 还保留两次原失败长文本的专项结果：各 309 个合法 token，正常 `stop`，输出序列相同。

原始 JSON 和日志中的 `/workspace/...` 是实际执行容器内的路径，原样保留用于追溯；网页阅读请使用本页相对链接。日志包括主动清理后的进程退出信息，结合 gate 退出码和时间判定，不能仅搜索 `ERROR` 就认定请求失败。

## 安装教程的验证

本次另外创建了独立 `/workspace/gate-repro-setup-validation-20261107/venv`，实际执行了配套安装脚本。源码归档离线复用并逐一校验 SHA256，FlagTree wheel 从公开地址安装；vLLM、FlagGems、FlagGems-vllm 与插件均重新安装。

新 venv 的 [预检查日志](install-validation/preflight.log)返回 `PREFLIGHT_PASS`；[新增单测日志](install-validation/unit-tests.log)为 10 passed。配套 runner 在新 venv 服务上实际完成 **27B Eager 26/26**，退出码 0，见 [汇总 JSON](install-validation/gate/summary.json)、[pytest 日志](install-validation/gate/tests.log)和 [服务日志](install-validation/gate/server.log)。这是额外的安装流程验证，不重复计入本页 104 请求。

pytest 入口修正后，[最终预检查](install-validation/preflight-final.log)再次通过，使用 venv pytest CLI 启动的 [10 项单测](install-validation/pytest-cli-tests.log)全部通过，日志头明确显示新 venv 解释器。

这些验证发生在同一容器的独立 Python 环境，复用了已有驱动运行时和 FlagCX。没有在另一台空白宿主机执行 Docker 创建和 FlagCX 编译。新机的这两部分仍须在该机检查，不能据此宣称所有新机器安装已经实机验证。

安装演练中修正了三个可复现性问题：CoreX 后缀应查安装元数据；vLLM 构建版本覆盖需显式带 `+empty`；继承系统 pytest 包不一定生成 venv 命令入口。交付脚本已包含修正。这一轮 gate 的模型服务从新 venv 启动，客户端 shell 在启动时缓存了系统 pytest 路径，三个客户端分组沿用系统入口。随后已建立同版本 venv pytest 入口，后续新启动的 shell 会使用它；不能把这轮客户端日志中的系统解释器改写成新 venv，测试源码和判据未改变。

## 依赖与精度边界

[pip-check.txt](pip-check.txt)保存当前环境的真实依赖声明冲突，包括 transformers/tokenizers 等声明不一致、缺少 oss-harmony 以及 FlagTree 提供 Triton 的情况。这里的 gate 成功只覆盖本测试路径，不代表依赖声明全部满足或所有功能适用。

[新 venv 的 pip-check.txt](install-validation/pip-check.txt)还包含重新安装当前插件后暴露的 ModelScope 声明冲突：要求 1.35.3，继承版本为 1.39.1。本次只读取本地模型，没有验证该版本的下载功能。原环境安装元数据与通过 `PYTHONPATH` 指向的新源码并非同一概念，实际导入路径和 Git SHA 均另行核对。

本轮未做 NVIDIA 精度对齐、长期压力测试或完整上游 CI，也未移除既有算子排除项。推送内容不包含模型权重、访问令牌或原始对话。
