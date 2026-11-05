# PR 675 教程：从官方镜像新建容器实测

开始日期：2026-11-05 UTC。

配套 [手工教程](enflame-pr675-test-guide-20261105.md)；原始请求、响应、逐组结果和压缩服务日志的文件哈希见 [证据清单](../records/enflame-pr675-fresh-container-20261105/manifest.json)。`status=passed` 的自动条件是 HTTP 200 且内容非空；人工内容检查与完整适配 Gate 的边界另行说明。

## 范围

严格复核手动教程的系统 Python 安装、环境门禁、真实通信、4B 与两种大模型 eager / Graph。只有实际执行成功的阶段记为 PASS。

新容器：`test_plugin_32_enflame_20261105_manual`。

当前执行环境无法直接操作宿主 Docker 创建接口，因此复用原适配工作目录中**已经存在**的独立 daemon：`unix:///workspace/s60-adaptation/docker.sock`。未启动新 daemon，未修改宿主 Docker、驱动、系统 Python、已有源码或已有服务。该执行入口与用户宿主终端的 `docker` 不同；容器镜像和容器内步骤按教程执行。

镜像：`harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-enflame-ci@sha256:f21e53101ffcf00fa5b70b39913bd401be93c0d1834c0ae8d07684bf0690bc88`。

重新执行 pull 成功，digest 一致，层已缓存。新建容器成功，PID 1 为 sleep，独立 PID 命名空间，32 GiB 共享内存。

模型 `/models` 只读挂载。任务输出挂载为 `/test-output`，仅此目录可写回本次外层工作目录 `/workspace/enflame-manual-20261105`。使用创建前确认空闲的逻辑卡 `5,6`。

## 原始镜像发现

- Python 3.12.8，Ubuntu 24.04.3。
- vLLM 0.28.0+empty。
- **不包含 vllm-plugin-fl**。原始 0.28 的 GCU 服务基线不具备 FL 插件运行条件，不能直接记为成功。
- torch 2.11.0+cpu / torch-gcu 2.11.0+3.8.20260713。
- FlagTree 0.7.0+enflame3.6 / triton-gcu 3.6.0+1.0.20260722。
- FlagGems 5.4.0，FlagCX 0.13.0，NumPy 2.3.5。

## 本次进度

设备检查 PASS：恰好两张可见卡，每卡约 41765 MiB 空闲；`torch.ones((32,32), device='gcu:0')` 执行并同步成功，求和为 1024。

源码获取遇到网络问题：首次完整插件 clone 为 GnuTLS -110；改为 HTTP/1.1 浅 clone 后分支获取成功，但直连 GitHub 获取固定提交仍连接失败。只对该次 fetch 使用 `https://gh-proxy.com/https://github.com/flagos-ai/vllm-plugin-FL.git` 后，固定提交获取成功。未修改全局 Git 配置。

vLLM 直连下载约 5 分钟仍未完成，停止的仅是本次新容器中的下载进程；改用单次代理 clone 后下载完成，源码提交核对正确。

官方 common 依赖安装 PASS，随后 `VLLM_TARGET_DEVICE=empty python -m pip install -v --no-build-isolation --no-deps -e .` 成功，包为 `0.32.0+empty`。未创建 venv，未修改外层系统 Python。

FlagTree 固定哈希 wheel 下载、卸载上游 Triton、恢复厂商编译器、两项文件校验均 PASS。插件固定提交安装成功；因浅克隆 metadata 为 `0.0.0+g5efa61dc4`，来源以 Git commit 和导入路径核验。辅助算子通过进程级代理下载并完成固定提交校验，未修改全局 Git 配置。FlagCX 布局创建和 ldd 检查 PASS。

第一次完整环境检查失败在教程自己的断言：`vllm.__version__` 没有 `+empty`。实际 metadata 是 `0.32.0+empty`，导入版本是 `0.32.0`，源码提交正确。上游 `get_vllm_version()` 先由 setuptools-scm 写入基础版本文件，再对返回给发行包的版本追加 empty，解释了差异。已修正文档与检查脚本：对 metadata 核验 empty，对导入版本核验相同基础版本。未修改任何上游版本文件，未重装或伪造版本。

修正检查逻辑后，完整环境门禁 PASS：全部必选 vLLM 依赖满足声明，固定 Git 提交及辅助算子来源正确，平台为 gcu / enflame，两张卡可用，FlagCX wrapper 与库句柄初始化成功。

新容器真实 TP2 FlagCX all-reduce PASS：两个 rank 均得到 16 个 3.0，退出码 0，日志报告 ECCL 3.7.1.2。

## 模型实测

| 模型 / 模式 | 启动 | 请求结果 | 耗时 |
|---|---|---|---|
| Qwen3-4B eager，4096 / max-seqs 4 / batch 512 / memory 0.70 | PASS | 中文请求 HTTP 200，256 completion tokens，内容正常介绍 AI | 冷启动 400.017 秒；首次请求 281.056 秒 |
| Qwen3.6-27B TP2 eager，32768 / memory 0.94，首次 600 秒客户端预算 | PASS | 文本、图像均超时，没有响应体，不能记为生成通过 | 启动 1120.042 秒；文本 600.007 秒、图像 600.101 秒超时 |
| Qwen3.6-27B TP2 eager，相同模型参数、1800 秒客户端预算重试 | PASS | 两条均 HTTP 200；文本生成 256 tokens，图像生成 222 tokens 后自然停止 | 启动 160.010 秒；文本 145.167 秒，图像 128.025 秒 |
| Qwen3.6-35B-A3B TP2 eager，首次 600 秒客户端预算 | PASS | 文本 HTTP 200，256 tokens；图像超时，该轮整体 FAIL | 启动 1000.035 秒；文本 546.251 秒，图像 600.101 秒超时 |
| Qwen3.6-27B TP2 decode Graph，mode 0 / FULL_DECODE_ONLY | PASS，FULL capture 35/35 | 两条均 HTTP 200；文本 256 tokens，图像 222 tokens | 启动 1360.043 秒；文本 136.463 秒，图像 120.234 秒 |
| Qwen3.6-35B-A3B TP2 eager，1800 秒预算重试 | PASS | 两条均 HTTP 200，均 256 tokens | 启动 220.012 秒；文本 263.970 秒，图像 317.653 秒 |
| Qwen3.6-35B-A3B TP2 Inductor Graph，显式 FL SiLU | PASS，PIECEWISE 51/51、FULL 35/35 | 两条均 HTTP 200，均 256 tokens | 启动 1200.047 秒；文本 255.916 秒，图像 256.918 秒 |

4B 服务收到本次测试进程组的 SIGINT 后正常退出，退出码 0。首次推理前存在内核冷编译，因此这不是稳定吞吐/时延基准。

大模型均按 TP2 / 32768 / memory 0.94 / 显式 FL SiLU 执行；27B Graph 的编译模式修正和原失败单列在下文，客户端超时预算也逐轮保留。

首次 27B eager 请求阶段可见活跃编译器，后段生成吞吐持续约 3.4 tokens/s；客户端在 600 秒超时，服务按本次脚本的 SIGINT 正常退出 0。该证据支持冷编译和请求预算不足这一排查方向，但未取得响应，不能把该轮判为 PASS。另以 case `qwen36-27b-eager-long-timeout` 重启同配置，客户端改为 1800 秒；保留原来的失败结果和完整日志。两轮共享同一新容器的编译缓存，不能作为冷启动时延对比。

重试完整通过，服务正常退出 0。人工对照原图：图像回答识别出中央正方形、左下/右上两个大圆、左上/右下两个小圆及黑线白底，主要内容与图片一致。文本正常介绍人工智能。这里只是这两个提示的功能冒烟，不是完整精度 Gate。

35B eager 的首次图像请求也超过 600 秒预算，原结果、文本响应和日志保留；另建 `qwen36-35b-a3b-eager-long-timeout` 按 1800 秒预算重试，模型参数及提示不变。该组启动和推理中可见 MoE 对齐内核的 MLIR 候选编译诊断，但已就绪并成功返回文本，不能把这些单独当作最终引擎失败。

35B eager 重试及原推荐的 35B Inductor Graph 均完成图文请求，服务正常退出 0。图像回答识别出正方形和四个圆的主要布局，但关于角点相切和大小的细节不完全严谨，本次只判功能冒烟成功，不宣称精确几何理解验收。35B Graph 实际完成 PIECEWISE 51/51、FULL decode 35/35；初始化日志报告引擎阶段 1071.54 秒，其中 compilation 337.56 秒。

切换服务时，测试脚本的端口预检首次报 Address already in use，尚未进入模型启动。随后检查没有 8070 监听或遗留推理进程，检查时 TIME_WAIT 也已不在。按停服后 TCP 状态可能导致的预检误判，为预检加入 SO_REUSEADDR 后重试成功；未证明首次报错的唯一原因。没有杀其他服务，也没有修改模型配置。

## 并行与设备边界

用户询问并行测试后，读取实际显存：卡 0/1 约剩 1.8 GiB，2/3 约剩 2.3 GiB，4 约剩 10.6 GiB，5/6 正用于本次 TP2，只有卡 7 空闲约 40.8 GiB。不具备另一组空闲两卡。用户明确要求不释放旧服务、不做全局操作，因此继续只用 5/6 顺序执行模型/模式，每组内文本与图像请求并发。不重跑已经通过的 4B 来制造并行工作。

用户随后通知卡 `0–3` 应已可用。2026-11-05 08:19 UTC 重新实测，这四张卡每卡约 41765 MiB 空闲；卡 `4` 仍只剩约 10852 MiB，保持不动。在同一新容器内，按进程分别设置 `TOPS_VISIBLE_DEVICES`，使用独立端口并行：`0,1 / 8071` 跑 27B Graph，`2,3 / 8072` 跑 35B eager，原 `5,6 / 8070` 的 27B eager 请求继续。没有由本次任务释放此前服务。

## 新发现：原 Graph 配置启动失败

27B Graph 初次使用教程中的 `custom_ops=["none","+SiluAndMul"]` 和默认 `VLLM_COMPILE / FULL_AND_PIECEWISE`。160.010 秒后启动退出 1，未就绪、未执行请求、未观察到 capture 完成。

首错为 `torch._dynamo.exc.Unsupported: torch.* op returned non-Tensor`；调用链为 `qwen3_next → qwen2_moe → SiluAndMulFL.forward_oot → silu_and_mul_flaggems → silu_and_mul_kernel → pointwise_dynamic.prepare_args → type_promotion → elementwise_dtypes`，Dynamo 报 `getitem` 返回 dtype。这里不能用历史通过结果声称相同配置在本次官方镜像已经通过，也不能把错误归因于缺少 EMPTY 构建的 `vllm._C` warning。

保留原 case 的完整 server log 和 result JSON，另建 `qwen36-27b-graph-decode-only` 尝试：显式 `mode=0 / FULL_DECODE_ONLY`，保留 `custom_ops=["none","+SiluAndMul"]`、精度仿真、TP2/32768/0.94 和完整多模态请求。该尝试验证 GCU 上解耦 Inductor 与 decode Graph 是否可行；在实际捕获和请求成功前不记为通过。不修改后端源码或现有在线服务。

该独立配置已完成验证：两个 worker 均完成 FULL decode 35/35 capture，文本和图像 HTTP 200，内容与 27B eager 的主要描述一致，服务正常退出 0。推荐教程的 27B Graph 命令据此修正，但原 Inductor 配置仍记启动 FAIL，不能将 decode Graph 的成功反写成原配置通过。

## 超时定位与性能边界

用户要求进一步定位后，在本次新容器内仅针对本次 worker 进行只读 `py-spy` 快照和两次各 20 秒、49 Hz 的采样，没有更改 worker 代码或采样参数。一次非阻塞快照因进程状态变化报 Bad address，未将它视为成功采样；两份统计采样均退出 0。

已证实的证据链：

1. 新环境首次 eager 请求存在活跃的厂商编译器和持续产生的 Triton 缓存文件；27B 请求初段的 `shm_broadcast` 等待并非足以证明死锁。35B Graph 运行时直接报告多条 `Triton kernel JIT compilation during inference ... causes a latency spike`，包括 `true_div_func_kernel_rank_1`、`softmax_kernel_inner`、`argmax_kernel`、`_bilinear_pos_embed_kernel_gcu` 和 `linear_kernel`。服务就绪不代表所有真实输入的内核已预热。
2. 同模型参数、同完整图文提示、同 256-token 上限，在保留编译缓存后重启服务：27B 从两条均超过 600 秒变为约 145/128 秒；35B 从文本 546 秒、图像超过 600 秒变为约 264/318 秒。重试也有其他组并行，因此不是精确的单变量性能基准，但与明确的 JIT 日志一起支持冷编译是超时的重要原因。
3. 模型 `generation_config.json` 的 `top_k=20 / top_p=0.95` 会触发 PR 的 GCU CPU 过滤兼容路径。35B eager 的活跃 Python 样本中 494/708 位于 `_apply_top_k_top_p_on_cpu`，Graph 为 158/214，多数叶帧是厂商 `.to()` 包装；该路径包含等待 GPU 工作，不能把这些比例等同于 CPU 计算占比。
4. 在已空闲的卡 `0` 上，以独立进程、CPU 单线程，对相同 248320 词表进行分段微测，预热 3 次后测 10 次。batch 1 总中位数 27.23 ms；batch 2 总中位数 57.28 ms，其中 CPU 过滤 56.20 ms、GCU→CPU 0.44 ms、CPU→GCU 0.64 ms。微测前同步设备，排除了前序模型 GPU 工作，故它不能直接替代真实请求的阶段归因。CPU 过滤有开销，但不足以单独解释数百秒；单凭 `.to()` 栈热点声称“CPU 排序导致全部超时”是不成立的。

判断：首轮 600 秒超时不能当作稳定推理的正常表现，当前预热覆盖不足是实际适配问题；1800 秒是功能复现的等待预算，不是性能修复。缓存后的完整请求成功，没有看到本轮 worker 因通信或 OOM 崩溃，但当前实现的推理性能也不能据此宣称已经优化正常。逐 GCU 内核、设备执行和主机同步的完整性能归因尚未完成，不将其包装成已修复问题。

原始证据包含 `diagnostic-profile-summary.json`、两份 collapsed stack profile、`diagnostic-sampler-stages.json` 和缓存时间线，随本轮响应及日志一同归档。完整手工教程补充了首次请求单独留档、同一服务再次预热请求和反复超时不得判通过的说明。

## 结束检查

本次模型服务均由对应测试脚本定向停止，返回码均为 0；失败的 27B Inductor 启动单独返回 1。结束后 8070/8071/8072 可绑定，新容器没有活跃推理 worker；`Z` 状态的已退出子进程不计为仍占卡的服务。本轮所用 0/1/2/3/5/6 每卡恢复约 41765 MiB 空闲。原 GPU 4 上 18080/18081 两服务 `/health` 均为 HTTP 200。新建容器保留，没有停止其他服务或修改宿主全局配置。

修订后的教程 29 个 Bash 块均通过 `bash -n`，6 个内嵌 Python 片段通过 AST 解析。此语法检查不替代上面的实际硬件和 HTTP 结果。
