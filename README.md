# vLLM 0.32 适配记录

## 系统 Python 新容器最小 gate 复现

[搭建、最终环境与 27B/35B Graph/Eager 实测记录](docs/iluvatar-pr674-minimal-container-20261107.md)。直接使用系统 Python，不创建 venv；只运行 adaptation-gate-cases。


## Iluvatar PR #674 / FlagGems 5.5 复现（2026-11-07）

- **[当前固定版本的环境搭建与四轮 gate 复现教程](docs/iluvatar-pr674-gems55-gate-reproduction.md)**：新容器、FlagTree 0.7 / FlagGems 5.5.0.dev0 / FlagGems-vllm、EMPTY vLLM 0.32、FlagCX、实际导入检查，以及其他机器需要改和不需要复制的设置。
- [配套安装、预检查和测试脚本](tools/gate-repro-20261107/)；[原始结果与日志证据](records/iluvatar-pr674-gems55-20261107/README.md)。
- 插件固定为 `7a94aee`；Qwen3.6-27B 与 Qwen3.6-35B-A3B 的 Graph / Eager **四轮均 26/26，合计 104/104 请求通过**。Graph 使用 `cudagraph_capture_sizes=[1,2,4,8,16,32]`，保留 `slice,mm,mm_out` 排除项。
- 本次还在独立 venv 执行教程安装与检查。普通新容器驱动预检查通过时不需要旧机器的驱动提取/替换步骤。当前依赖仍有声明冲突，功能 gate 不等于 NVIDIA 精度对齐；验证范围详见教程。

以下为按日期保留的其他平台及此前配置记录，新教程中的版本、路径和命令不与旧教程混用。


## 燧原 S60 官方镜像手动测试教程（2026-11-05）

- [完整操作步骤：官方镜像、建容器、升级 PR 675、4B 与两模型 eager / Graph、图文请求](docs/enflame-pr675-test-guide-20261105.md)。
- [新容器逐步实测记录](docs/enflame-pr675-fresh-container-test-20261105.md)：官方镜像新容器安装、TP2 通信、4B 及修正后四组图文请求通过；原 27B Inductor 启动失败和 eager 首轮超时保留，附超时采样与分段微测。
- [前期核验及历史证据边界](docs/enflame-pr675-verification-20261105.md)。保留此前在线服务、历史 Gate 与本轮新容器的区别。

## S60 当前环境门禁复测（2026-11-05）

- [本机环境、完整步骤与真实结果](docs/s60-adaptation-gates-20261105-current.md)：当前 S60/GCU、TP2；与下方 Iluvatar 参考机器结果分开记录。
- [四轮尝试与 15 份实际原始 JSON 汇总](records/s60-adaptation-gates-20261105-current/README.md)及 [SHA-256 清单和捕获观察](records/s60-adaptation-gates-20261105-current/manifest.json)。
- 27B eager / Graph 均 26/26；35B-A3B eager 25/26；35B-A3B Graph 启动失败，26 请求未执行。总计实际执行 78、通过 77，不是四轮全部通过。
- 原始脚本、图片、断言未改，不重装、不建 venv、不录屏、不另存完整服务日志。功能门禁不等于 NVIDIA 精度对齐。

## Iluvatar FlagTree 0.7 升级与复测（2026-11-05）

- [完整升级核验、测试步骤与结果](docs/iluvatar-vllm032-flagtree070-retest.md)：`test_plugin_28` 已升级到 `0.7.0+iluvatar3.6`，377 个安装文件与新版 wheel 逐个校验一致；Triton 模块仍标为 3.6.0，原因与正确版本查询方式已写入教程。
- [升级命令及版本解释](docs/iluvatar-vllm032-fresh-machine-setup.md#51-升级天数版-flagtree-至-07)，[20 份原始 JSON 与核验证据](records/u180-flagtree070-gates-20261105/README.md)。

| 模型 | eager | FULL_DECODE_ONLY |
| --- | ---: | ---: |
| Qwen3.6-27B | 26/26 | 26/26 |
| Qwen3.6-35B-A3B | 26/26 | 26/26 |

原始 20/20 场景、104/104 请求通过，其中文本 52/52、图片 52/52；两轮 Graph 均捕获 35/35。只替换 FlagTree，没有修改用例或推理源码。35B Graph 的 TLE 编译诊断及原算子回退分支已单独记录；本轮通过不能证明偶发 OCR 问题的唯一根因。下方旧版失败记录完整保留。

## Iluvatar 原始 0.6.2 图文门禁（2026-11-05）

- [完整测试步骤与结果说明](docs/iluvatar-vllm032-adaptation-gate-test.md)：硬件和软件环境、库路径、两个模型 eager / CUDA Graph 的启动命令、原始测试执行步骤、判定标准和失败样例。
- [20 份原始 JSON 结果索引](records/u180-adaptation-gates-20261105/README.md)及 [SHA-256 清单](records/u180-adaptation-gates-20261105/manifest.json)。

| 模型 | 模式 | 通过场景 | 通过请求 |
| --- | --- | ---: | ---: |
| Qwen3.6-27B | eager | 2/5 | 13/26 |
| Qwen3.6-27B | FULL_DECODE_ONLY | 3/5 | 17/26 |
| Qwen3.6-35B-A3B | eager | 5/5 | 26/26 |
| Qwen3.6-35B-A3B | FULL_DECODE_ONLY | 4/5 | 25/26 |

本轮在 `test_plugin_28` 的系统 Python 中，使用 TP4、32768 上下文和完整多模态模型执行原始适配门禁。52 条文本全部通过，52 条图片通过 29 条；失败均为内容检查未通过。两轮 Graph 均完成 35/35 捕获。本轮结果与下方历史阶段记录分别保留。

## 新机器环境搭建与测试教程

- **[教程二：官方镜像、原始环境验证、直接升级与文本测试](docs/iluvatar-vllm032-fresh-machine-setup.md)**：当前手动复现入口；不建 venv、不录制日志，容器内直接安装，终端 A 启服务、终端 B 用 curl 询问“详细介绍下人工智能”，包含 4B、27B、35B 文本命令。
- **[教程一：此前现有 venv 环境的复现记录](docs/iluvatar-vllm032-local-reproduction.md)**：保留旧版隔离环境、通信、eager/graph 和流式测试证据，不与教程二混用。
- [配套环境与验证脚本](tools/iluvatar-repro/)：环境激活、版本及库检查、真实 FlagCX 通信和 Qwen3-4B 冒烟。

本轮按教程二操作；旧 venv 用户若改走教程二，先恢复系统 Python。教程中的只读材料路径属于当前机器，换机器时需核对。下面的完整命令档案用于追溯历史操作。

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
- 此前阶段的大模型复测（历史配置）：27B graph 为 26/26；35B eager、graph 各为 25/26，同一图片 OCR 失败。
- 35B OCR 输出不稳定的归因尚未确定；按用户要求停止深入排查，保留失败证据。
- 截至该历史阶段，完整 104 请求全部通过、NVIDIA 逐 token 对照和远端硬件 CI 尚未达成；2026-11-05 FlagTree 0.7 的图文门禁复测另见本页上方独立记录。

这是带已知问题的阶段交付，不能表述为完整适配验收通过或发布声明。

## 仓库内容

原有 Iluvatar 部分仅包含审阅文档，报告中的 `/workspace/...` 为执行容器内的证据位置，不能直接在 GitHub 访问。新增 S60 归档位于 `records/s60-vllm032/`，包含脱敏日志、诊断脚本和适配交付补丁，不包含模型权重或访问令牌。

如需导师直接访问私有仓库，请由仓库所有者在 GitHub 的 **Settings → Collaborators** 中添加导师账号。
