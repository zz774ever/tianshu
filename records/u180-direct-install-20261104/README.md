# 本轮官方镜像、系统 Python 直接安装验证

日期：2026-11-04。执行容器：`a20ad38e000a`（`tianshu-vllm032-text`）。全部安装和模型操作在容器内进行，没有宿主安装、驱动变更或新建 venv。镜像使用既有官方 CI 镜像；此次没有重新拉取或创建容器。

## 原始系统环境

升级前清除继承的 PYTHONPATH，并明确使用 `/usr/local/bin/python`。确认：Python 3.12.11；vLLM 0.28.0+empty；插件 0.3.0rc0+g13eb9be69；CoreX torch distribution 2.10.0+corex.4.5.0；FlagTree 0.6.2a3+iluvatar3.6；FlagGems 5.3.5；NumPy 1.26.4；OpenAI 2.46.0。系统环境未装 FlagGems-vllm。

GPU 0–3 各约 31.8 GiB 空闲，8–11 已有其他任务，未使用。历史 zyp 模型路径不存在，使用只读 `/models/Qwen3-4B`。

原始服务命令采用用户指定的 eager、8060、32768 上下文、qwen，补充容器内回环监听。结果退出 1，根因：旧插件注册路由访问不存在的 `vllm.model_executor.layers.fused_moe.FusedMoE`。没有模型加载，没有接口就绪。随后直接 curl 退出 7（连接拒绝）。原始基线不能记成通过，也没有为通过测试修改原装源码。

## 安装与校验

官方 PR 674 API 本次核实：open，目标分支 0.5.0-dev，head `c17d866e08b583f63998cbd47bc39fe3e57efce0`。

直接在容器系统 Python 安装 vLLM 0.32 与插件，均使用 editable、no-build-isolation、no-deps。原全局目录属于容器，旧 0.28 由 pip 替换；原 venv 不删除、不用于本轮服务。保持厂商 torch、FlagTree、FlagGems、NumPy。

辅助算子使用此前传入同版 Git 源码，只在容器专用 Git 配置中对该仓库设置 file URL 重写，再由官方 helper 安装并核对真实 VCS 提交。未伪造元数据。

vLLM 和插件同样复用此前在容器内校验过的 Git 源码缓存，未重跑外网 clone。本轮查询 PR API 核对实际 head；文档给出 fresh clone 和已有源码跳过下载两个分支。它是既有官方镜像容器中系统 Python 的直接升级验证，不是再次从空白机器完整拉镜像重装。

## 结果记录

原始命令和完整输出从容器 `/workspace/repro/logs` 归档到 [raw-steps.tar.gz](raw-steps.tar.gz)，包括每步 command.sh、output.log、起止时间、命令及 tee 退出码，以及指纹和本轮使用的文档代码片段。[逐条命令索引](COMMANDS.md) 可以直接在网页阅读，[manifest.json](manifest.json) 保存归档及每步命令、输出哈希。服务由测试进程启动，测试后只停止自己启动的服务。

上层 Python 包仍继承官方镜像，与上游 0.32 的部分依赖声明不同，不宣称 pip check 全通过。HTTP 成功、非空生成不代表生成精度或性能验收。新教程的基线失败与升级后结果分别列出，不混淆。

## 系统 Python vLLM 0.32 直接请求实测

系统 Python editable 安装成功，实际导入 `/workspace/repro/src/vllm/vllm/__init__.py` 和 PR 源码目录。torch、FlagTree、FlagGems、NumPy 与升级前元数据一致，文档运行时检查输出 DIRECT_ENV_PASS。没有依赖旧 venv。

4B 服务按 32768 上下文、eager、8060、qwen 启动，启动完成。直接 curl 的中文问题“详细介绍下人工智能”、max_tokens=256 返回非空中文介绍，退出 0，finish_reason=length。OpenAI 原示例 max_tokens=20、stream=True 正常显示英文介绍，退出 0。回答到 token 上限被截断属于本次请求设置，不记为完整长文验收。

一次执行流式代码时校验文件尚未传入，退出 2；补传文档原代码后重试成功。两次日志都保留。文档中直接以 heredoc 执行，不依赖这个校验临时文件。

显式 Bash 的 script 会话实测可以 source env-direct.sh，Python 为 `/usr/local/bin/python`，`sys.prefix == sys.base_prefix`。实际 pip check 退出 1，原始差异已保存，包含 oss-harmony 缺失、上层包版本差异和 xgrammar 声明的独立 triton distribution 缺失；没有为了清除元数据报告而安装通用 Triton 覆盖 FlagTree。

## 27B TP4 eager 纯文本实测

`/models/Qwen3.6-27B`，TP4、BF16、language-model-only、eager、4096 上下文、max_num_seqs=4、max_num_batched_tokens=512、显存预算 0.70，按文档启动成功。直接 curl 发送“详细介绍下人工智能”、max_tokens=256、enable_thinking=false，返回中文介绍，completion_tokens=256、finish_reason=length，退出 0。日志显示真实 tp4。

请求期间约 1.5–1.6 token/s，非流式等待约三分钟后显示完整 JSON；这是本次观察，不作为性能验收结论。服务启动前的状态检查连接拒绝保留为未就绪记录，不算模型请求失败。请求完成后停止本轮服务再运行下一个模型。

## 35B-A3B TP4 eager 纯文本实测

`/models/Qwen3.6-35B-A3B` 使用与 27B 相同的 TP4、BF16、language-model-only、eager、4096 上下文、max_num_seqs=4、512 token 批次预算、0.70 显存预算，启动成功。直接 curl 的同一中文问题返回非空中文介绍，completion_tokens=256、finish_reason=length，退出 0。真实 tp4，未运行图片或 OCR。

请求期间观察到约 1.9–2.0 token/s。本轮只验证上述 eager 直接请求，没有重跑 FULL graph、完整图文门禁、精度对照或性能验收。完成后停止本轮最后一个服务，保留系统 Python 的新环境供用户手动执行。

## 最终状态与直接回答

| 项目 | 实际结果 |
| --- | --- |
| 原装 0.28 + 原装插件基线启动 | 失败，FusedMoE 属性接口不匹配，退出 1 |
| 原装基线 curl | 服务未启动，连接拒绝，退出 7 |
| 系统 Python 直接安装 0.32 / PR 674 / FlagGems-vllm | 三项退出 0，核心厂商版本保持 |
| 4B eager curl / OpenAI stream | 均退出 0，非空回答 |
| 27B TP4 eager curl | 退出 0，非空中文回答，256 completion token |
| 35B TP4 eager curl | 退出 0，非空中文回答，256 completion token |
| pip check | 退出 1，保留依赖声明差异 |
| FULL graph / 精度和性能验收 | 本轮未执行 |

直接请求原始 JSON：[4B](responses/4b.json)、[27B](responses/27b.json)、[35B](responses/35b.json)。所有请求模型名 qwen、端口 8060、同一中文问题，服务逐组运行。回答达到 256 token 上限后结束，不作为完整长文验收。

最后核对 8060 已释放，0–3 卡各约 31.8 GiB 空闲；vLLM 和插件源码均无未提交改动。系统 Python 已升级，用户可以 source `/workspace/repro/env-direct.sh` 后从教程第 7 节或第 9 节直接启动，不必再次安装或降级重做基线。

服务中断清理期间的 EngineDeadError、资源回收警告也保留在完整日志中；它们出现在本轮请求完成后主动停止服务时，不隐藏，也不与推理响应结果混写。
