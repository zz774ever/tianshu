# 天数 FlagTree 0.7 升级与原始图文门禁复测

日期：2026-11-05。执行容器：`test_plugin_28`。用户要求将当前容器升级到 FlagTree 0.7、写入教程、重新跑测试。本轮只替换 FlagTree，原始 0.6.2 的报告和失败 JSON 保持原样。

## 1. 版本与升级

| 项目 | 升级前 | 升级后 |
| --- | --- | --- |
| FlagTree 分发包 | `0.6.2a3+iluvatar3.6` | `0.7.0+iluvatar3.6` |
| Triton 模块 | `3.6.0` | `3.6.0` |
| CoreX PyTorch | `2.10.0+corex.4.5.0` | 相同，文件哈希一致 |
| vLLM / 插件 | 0.32.0 / `c17d866e08b583f63998cbd47bc39fe3e57efce0` | 相同 |
| FlagGems / FlagGems-vllm | 5.3.5 / 0.1.0 | 相同 |
| Transformers / NumPy | 5.14.1 / 1.26.4 | 相同 |

两个容器使用同一基础镜像，但旧 `vllm-fl-iluvatar-agent` 会话此前收到“更新为flagtree0.7.0”指令，已在当天 10:01 左右单独升级。那次升级没有改变 `test_plugin_28`，所以之前 104 条门禁实际使用 0.6.2，原报告版本正确。本次按新授权将测试容器也升级到 0.7。

升级命令、官方下载地址、SHA-256 与核验方法见[环境教程第 5.1 节](iluvatar-vllm032-fresh-machine-setup.md#51-升级天数版-flagtree-至-07)。实际安装为 `python -m pip install --no-deps --no-index` 指定天数 wheel。升级前后全包版本比较仅 FlagTree 变化，Torch 哈希一致；没有新建 venv，也没有升级其他依赖或修改推理源码。

新进程设备编译检查：FP32、FP16、BF16，各测试长度 1、257、100003 的加法，9/9 通过。使用新的独立 Triton 缓存目录验证新编译，不以包导入成功代替设备或模型测试。

用户进一步要求确认升级是否真正生效，因此另做 wheel 与安装文件核验：新旧 wheel 的 Triton 模块都明确标为 3.6.0，但 FlagTree 发行元数据分别为 0.6.2 与 0.7；`flagtree.__version__` 本身也从 Triton 导入，不能代替分发包版本查询。实际安装的 377 个包文件全部与 0.7 wheel 的 SHA-256 一致，零差异；核心 `libtriton.so` 与旧版哈希不同，匹配新版。没有独立 `triton` 分发包覆盖导入路径。核验脚本和[完整 JSON](../records/u180-flagtree070-gates-20261105/installation-verification.json)随结果归档。

## 2. 复测步骤

与[原始门禁步骤](iluvatar-vllm032-adaptation-gate-test.md)相同：GPU 0–3、TP4、32768 上下文、显存预算 0.70、模型名 qwen、端口 8132，Graph 为 `{"mode":0,"cudagraph_mode":"FULL_DECODE_ONLY"}`。分别用原始 `run_serve_eager.sh` / `run_serve_graph.sh` 启动两个模型，再执行原始 `run_test.sh`。每轮 5 场景、26 请求，共 104 请求。

请求超时 600 秒、服务就绪超时 1800 秒。图片、题目、并发、生成长度、temperature=0、thinking=false 及检查条件全部保持，不加入 `--language-model-only`，也不把序列数限制为 4。服务和客户端在终端输出，不另存日志；原脚本 JSON 逐轮保存。

本轮输出目录：`/workspace/adaptation-gate-upgrade-20261105/results/`。`before.json` / `after.json` 记录包版本和 Torch 哈希，`device-verification.json` 记录设备检查，`matrix.json` 记录逐轮退出码。

## 3. 本轮结果

四轮均已完成，20/20 场景、104/104 请求通过。其中文本 52/52、图片 52/52；104 条响应的 `finish_reason` 均为 `stop`，没有请求异常、超时或达到 token 上限。四轮客户端退出码均为 0，整个驱动进程退出 0。

以下五个场景列均为“通过请求数 / 请求总数”。

| 模型 / 模式 | 文本单条 | 文本并发 8 | 图像单条 | 图像并发 8 | 混合并发 8 | 通过场景 | 通过请求 | 退出码 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 27B eager | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | 5/5 | 26/26 | 0 |
| 27B FULL_DECODE_ONLY | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | 5/5 | 26/26 | 0 |
| 35B-A3B eager | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | 5/5 | 26/26 | 0 |
| 35B-A3B FULL_DECODE_ONLY | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | 5/5 | 26/26 | 0 |

四轮 `image_single` 的精确 OCR 回答均为 `HELLO` 换行 `VLLM`，通过原始检查。原始 0.6.2 首轮矩阵的请求通过数依次为 13/26、17/26、26/26、25/26；本轮依次均为 26/26。旧结果不覆盖，也没有用重跑替换某个失败 JSON。

本轮执行时间为北京时间 15:22:13 至 16:03:20。逐轮耗时（含加载、编译、预热、服务等待和请求）为 675.07、447.05、539.06、780.09 秒，仅用于追溯执行，不能据此比较升级前后推理性能。每轮起止时间、退出码见 [matrix.json](../records/u180-flagtree070-gates-20261105/matrix.json)，[20 份原始结果索引](../records/u180-flagtree070-gates-20261105/README.md)及 [SHA-256 清单](../records/u180-flagtree070-gates-20261105/manifest.json)可直接查看。

### 启动与停服观察

两轮 Graph 均实际完成 35/35 捕获并启动成功，未重现 `capture_begin()` 的 `ixErrorNotSupported`。期间出现 replay benchmarker 不可用、退回 event timing 的警告；27B 还出现一次共享内存 broadcast 等待提示，随后捕获和启动均完成。

35B Graph 的预热出现 `iluvatar_tle.distributed_barrier ... requires cooperative grid launch` 编译诊断，位置为安装包 `moe_align_block_size.py:178`。已只读核对实际安装文件与 `/workspace/FlagGems-vllm/src/flaggems_vllm/ops/moe_align_block_size.py` 完全一致。原有 `_run_tle_atomic_fused()` 在 TLE 分支捕获异常、必要时缩小 grid，失败后返回并走 `_moe_align_block_size_triton_4stage()`；本轮未修改这些逻辑。不能因为服务继续运行就声称该 TLE 优化分支已受支持，最终功能结果以完整门禁为准。

27B Graph 与 35B eager 在全部请求完成、驱动脚本主动发送 SIGINT 停服后，终端出现 `AsyncLLM output_handler failed / EngineDeadError`。这两个客户端均已退出 0，应与请求处理阶段失败分开记录。完整[终端观察说明](../records/u180-flagtree070-gates-20261105/terminal-observations.json)随原始 JSON 归档；没有另存完整服务日志。

## 4. 结论边界

本次确认当前容器已完整升级到 FlagTree 0.7，并且两个模型的 eager / FULL_DECODE_ONLY 原始功能门禁全部通过。没有改推理源码、算子源码或测试断言，也没有额外宣称修复了 TLE 优化路径。

原始 0.6.2 测试共 81/104 请求通过；之后独立排查时，未改推理实现的 27B eager、27B Graph、35B Graph 也分别出现过 26/26 通过。因此本轮升级后全部通过，仍不能仅凭一次通过宣称已证明 FlagTree 旧版是唯一根因，或已经消除全部偶发 OCR 问题。这是原始功能门禁通过，不等于完成 NVIDIA 逐 token 精度对照或长期稳定性验证。

## 5. 收尾与再次复测

只停止了本轮驱动启动的服务，端口 8132 已释放；只读检查时 GPU 0–3 空闲显存分别为 32424、32564、32564、32564 MiB，检查用临时 Python 进程随后退出。vLLM、插件、FlagGems-vllm、FlagGems 四个源码工作区均干净。当前容器保留 FlagTree 0.7，未执行回退，其他容器的服务未停止。

再次测试按[原始门禁说明第 3–5 节](iluvatar-vllm032-adaptation-gate-test.md#3-终端-a公共环境)设置相同环境、逐轮启服务并运行 `run_test.sh`，每轮使用新的 `RESULTS_DIR`。本轮归档驱动固定了输出目录，重复运行会拒绝覆盖已存在目录。旧版 wheel 和完整安装备份仅留在测试容器，公开仓库只保存步骤、脚本、JSON 和校验信息。
