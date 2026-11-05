# 燧原教程核验记录：2026-11-05

教程：`/root/enflame-pr675-test-guide-20261105.md`。

## 后续更新：已开始新容器逐条实测

用户要求实际建容器后，本次已使用固定 digest 的官方镜像创建独立容器，先在空闲卡 `5,6` 执行，用户通知 `0–3` 空闲后重新检查并并行验证。安装、全部必选依赖检查、编译器文件校验、真实 TP2 all-reduce、4B 及修正后四组大模型图文请求均已通过。27B 原 Inductor Graph 配置实际启动失败，推荐改为实测 FULL_DECODE_ONLY；35B 保留 Inductor Graph 并完成两类捕获。首次 eager 超时保留为失败，缓存重试成功不改写原结果。发现并修正了网络下载重试、发行包与导入版本的检查差异、端口预检等文档问题，并增加超时采样和分段微测证据。

新容器的完整结果、实际配置及失败记录见 [新容器逐步实测记录](enflame-pr675-fresh-container-test-20261105.md)。下文保留的是此前核验阶段的证据和限制；“没有新建容器”等描述只属于该较早阶段。不得将下文的旧服务短请求、历史 Gate 数字混入新容器结果。

## 前期直接执行

- GitHub PR API：PR 675 为 `feat(enflame): adapt S60 backend to vLLM 0.32.0`，open，head 为 `5efa61dc4e9f86dc18d265adaa0cb9dc60397322`；本地 `/workspace/pr675-fix` HEAD 相同。
- Harbor：使用匿名 pull token 获取官方 `v0.28.0-enflame-ci` manifest，响应 digest 和对响应体自行计算的 SHA-256 均为 `f21e53101ffcf00fa5b70b39913bd401be93c0d1834c0ae8d07684bf0690bc88`。
- 宿主：Ubuntu 24.04.4、x86_64、AMD EPYC 9754、256 个逻辑 CPU；内核模块版本文件为 1.9.10。当前受限环境执行 `efsmi` 报 driver not loaded，该输出与下面的可用设备、在线服务证据不一致，教程已要求用户在正常宿主终端再次核对。
- 容器设备：`torch.gcu.is_available()` 为 True；8 张卡，每张 `total_memory=43878764544` bytes，即 41846.05 MiB。
- `TOPS_VISIBLE_DEVICES=5,6`：新 Python 进程只看到两张卡；`torch.gcu.mem_get_info()` 可调用，查询时第一个可见设备约有 40.8 GiB 空闲。
- 当前平台对象：`device_type=gcu`，`vendor_name=enflame`。
- `verify_compiler.py`：PASS，390 个发行文件、2,814,450,573 bytes，0 errors。校验不导入 GPU 包。
- `verify_index_fill.py`：PASS，FlagGems 5.4.0，11609 bytes，SHA-256 为 `37aacdee85e497881f47a813b5489d26972b335ba89df312dbd74be5b1a2e07c`。
- FlagCX：当前 wheel 版本 0.13.0，库可由 ctypes 加载；当前 PR 的 wrapper 导入可用，`FLAGCXLibrary` 实例化后 `devHandle` 非空。
- 匹配 wrapper SHA-256：`e6e4bdb2c0d0034100d861e132d5092a381cdab5764db7b2a3775b56efc1ff27`。教程从已有容器复制此文件，使用新容器镜像中的库，不下载未固定的最新 wrapper。
- FlagGems-vllm 的 `direct_url.json` 来源为官方仓库，commit 为 `b5c2c2249319277ccda4d41aa0f65164bd9b2a19`；metadata 版本仍是 0.1.0。
- 真实 TP2 collective：`TOPS_VISIBLE_DEVICES=5,6`，`torchrun --standalone --nnodes=1 --nproc-per-node=2 /workspace/s60-adaptation/collective.py`，当前 PR 的 `PyFlagcxCommunicator` 通过真实 FlagCX/ECCL all-reduce；两个 rank 输入分别为全 1 / 全 2，输出均为 16 个 3.0，进程退出码 0。日志报告 ECCL 3.7.1.2。

## 发现的依赖问题

当前安装的 vLLM metadata、当前固定源码的 `requirements/common.txt` 和 GitHub 官方相同提交的文件一致：要求 `transformers>=5.16.1,<5.20.0`，但当前容器实际安装 5.6.0。已有生成请求成功不代表满足官方声明。

因此教程单独安装 common 依赖并在最终门禁逐条检查 vLLM 必选依赖。依赖解析 dry-run 已观察到需要升级 Transformers、requests、tokenizers、aiohttp 等。没有实际升级当前容器，也没有将当前在线服务结果当作升级后结果。

## 前期 HTTP 短请求

在已有服务上执行，沿用原问题和原图像 URL，`max_tokens=32`、`temperature=0`、`enable_thinking=false`。没有重启或修改这些服务。

| 已有服务 | 请求 | HTTP | 耗时 | 返回内容 |
|---|---|---|---|---|
| 27B，18100，现有启动命令为 Graph 配置 | 文本 | 200 | 9.20 秒 | 非空，介绍人工智能 |
| 27B，18100 | 图像 | 200 | 31.33 秒 | 非空，描述黑白几何图形 |
| 35B-A3B，18101，现有启动命令为 eager | 文本 | 200 | 97.32 秒 | 非空，介绍人工智能 |
| 35B-A3B，18101 | 图像 | 200 | 98.28 秒 | 非空，描述黑白几何图形 |

两组 `/health` 和 `/v1/models` 均正常，模型实际别名分别为 `/models/Qwen3.6-27B` 和 `/models/Qwen3.6-35B-A3B`。教程的新服务统一使用 `qwen`，请求也统一使用 `qwen`。

这些进程早于本次 PR 最新 checkout，短请求不证明当前 head 的新容器、完整 256-token 测试或四组 Gate 全部通过。请求耗时也不能用于 eager/Graph 性能对比。

## 历史结果复核

直接读取 `/workspace/s60-adaptation/gate-results/` 下四组五场景 JSON：

- `27b-eager-vocabfix`：26/26。
- `27b-graph-linkerfix`：26/26。
- `35b-eager-paddingfix`：25/26，单文本 summary.passed=false。
- `35b-graph-silu-dispatch`：26/26。

共 103/104，不是 104/104。这些是历史适配轮次证据，不是本次对最新提交完整重跑。

## 命令检查与未执行边界

教程最终 26 个 Bash 代码块通过 `bash -n`，6 个内嵌 Python 片段通过 AST 语法解析。

前期核验时没有新拉取完整镜像层、创建新容器、执行安装、启动 4B 或重跑完整四组大模型。对 Docker inspect 和部分批量执行形式的尝试被当前运行环境权限限制拒绝，因此当时不能声称已经从零逐条执行教程。后续复用已存在的隔离 daemon 创建了新容器；实际安装和模型结果另见上方链接，不覆盖本段历史边界。

common 依赖解析 dry-run 已完成，退出码 0。使用官方 PyPI 和与教程相同的厂商约束，未安装任何包。拟安装：aiohttp 3.14.5、certifi 2026.10.23、mcp 2.3.0、mcp-types 2.3.0、oss-harmony 0.0.12、pillow 13.0.0、requests 2.34.2、safetensors 0.8.0、tokenizers 0.23.3、transformers 5.19.0、triton 3.6.0、yarl 1.25.1。

这也实证了 xgrammar 的依赖会引入上游 Triton。教程保留了下载固定哈希 FlagTree wheel、卸载上游 Triton、重装 FlagTree 和校验实际文件的顺序。dry-run 使用的是当前容器，不能代替新容器的安装成功或升级后推理验证。
