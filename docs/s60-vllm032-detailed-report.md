# Enflame S60 / vLLM 0.32.0 适配详细报告

文档整理日期：2026-11-02，时间均使用 UTC。主要实验发生于 2026-10-30 至 2026-11-02。

本文面向需要审阅代码、复现实验、接手后续工作的人，详细说明版本差异、逐文件修改、问题成因、验证结果、失败尝试和交付边界。内容来自实际 Git 差异、保存的日志、请求结果 JSON、精度审计及交付快照。本次编写报告没有重新启动模型、重跑硬件 Gate 或修改适配代码。

## 阅读导航

- [1. 最终结论与状态定义](#1-最终结论与状态定义)
- [2. 适配对象、版本与依赖](#2-适配对象版本与依赖)
- [3. 旧版与新版的实质差异](#3-旧版与新版的实质差异)
- [4. 执行过程与关键转折](#4-执行过程与关键转折)
- [5. 全部 36 个改动文件](#5-全部-36-个改动文件)
- [6. Worker、Runner 与 KV cache 迁移](#6-workerrunner-与-kv-cache-迁移)
- [7. 整数 ABI、编译器和缓存修复](#7-整数-abi编译器和缓存修复)
- [8. 词表 mask 与 MoE 路由](#8-词表-mask-与-moe-路由)
- [9. TP2 与 Graph 的修复链](#9-tp2-与-graph-的修复链)
- [10. 数值精度：差在哪里、差多少](#10-数值精度差在哪里差多少)
- [11. 大模型正式 Gate 的完整结果](#11-大模型正式-gate-的完整结果)
- [12. 单元测试与证据覆盖](#12-单元测试与证据覆盖)
- [13. 镜像、FlagTree 与 CI](#13-镜像flagtree-与-ci)
- [14. 已尝试但未采用的方法](#14-已尝试但未采用的方法)
- [15. 未做、未通过与已接受事项](#15-未做未通过与已接受事项)
- [16. 复查和复现方法](#16-复查和复现方法)
- [17. 后续工作的建议顺序](#17-后续工作的建议顺序)
- [18. Agent 停止与任务完成的判断](#18-agent-停止与任务完成的判断)
- [19. 代码及证据的追溯关系](#19-代码及证据的追溯关系)
- [20. 常见问题](#20-常见问题)

## 1. 最终结论与状态定义

### 1.1 可以确认完成了什么

本次建立了官方 vLLM 0.32.0 EMPTY 构建与 FL 插件在 Enflame S60 上的实际运行路径，并处理了框架接口、KV 布局、编译整数类型、词表 mask、MoE padding、FlagCX Graph 边界和部分 BF16 编译候选失败等问题。

Qwen3-0.6B 已有真实权重上的 eager、Graph、TP2、HTTP 并发和流式生成记录；还完成了官方 NVIDIA 环境的保存输出对照。Qwen3.6-27B、Qwen3.6-35B-A3B 完成了 TP2 eager/Graph 四组正式请求，共 20 个场景、104 个请求，其中 103 个通过原始检查。

适配源代码已在本地插件仓库形成提交：

```text
提交：41ca547b36d0a9e4c0fdbbcb3267c82b9dd8431e
父提交：64c9d216ee6c66acb0b9fc8c097b6c1eab3a4ef4
分支：adapt/enflame-s60-vllm032
提交时间：2026-11-02 11:51:22 UTC
标题：feat(enflame): adapt S60 backend to vLLM 0.32.0
差异：36 files changed, 1915 insertions(+), 1510 deletions(-)
```

这里的“本地提交”不等于已经合入 `flagos-ai/vllm-plugin-FL` 官方仓库。本报告与证据上传到 `zz774ever/tianshu`，也不自动证明插件代码已在官方上游发布。

### 1.2 当前不能写成什么

不能写成“所有适配验收全部通过”“严格精度完全对齐”“104/104”“新镜像已发布”或“硬件 CI 已通过”。这些表述都超过已有证据。

| 维度 | 实际结论 | 解释 |
| --- | --- | --- |
| 0.6B 基础功能 | 有成功证据 | 仅覆盖保存的配置和输入 |
| S60 eager 与 Graph 输出 | 指定选项下 160/160 token 一致 | 同硬件模式比较 |
| 0.6B 对 NVIDIA 严格精度 | 未通过，差异已由用户接受 | 接受差异不能改写原始对比结果 |
| 27B eager / Graph | 各 26/26 | 正式请求组通过 |
| 35B eager | 25/26，特定例外已接受 | 原单文本结果仍为 FAIL |
| 35B Graph | 26/26 | 使用显式 FL SiLU 配置 |
| 聚焦回归 | 有 115 passed 记录 | 不是完整测试套件全部通过 |
| Harbor 拉取及依赖构建 | 用户授权 SKIPPED | 没有得到可验证的新镜像 |
| 镜像发布、runner CI | 未验证 | CI 保持禁用 |

### 1.3 本文使用的状态含义

- **通过**：对应实验或请求的原始检查通过，只适用于该实验的输入、版本和配置。
- **失败**：原始断言或运行失败；即使后来接受风险，也保留失败事实。
- **已接受差异/例外**：用户在知悉具体问题后接受该范围的交付，不代表技术问题被消除。
- **跳过**：有明确决定不执行，不能当作通过。
- **未验证**：缺少完成该项所需的证据，不能根据相邻步骤成功推断。
- **诊断**：用于定位原因或排除假设，不能直接替代原配置的正式验收。

## 2. 适配对象、版本与依赖

### 2.1 适配范围

| 项目 | 本次范围 |
| --- | --- |
| 加速器 | Enflame S60，GCU 后端 |
| 插件 | `vllm-plugin-FL`，FL 平台与厂商 dispatch |
| 目标框架 | 官方 vLLM `v0.32.0` |
| 目标源码提交 | `5df63a7203cdb9328d824a27b682e77c7b9928be` |
| 构建方式 | `VLLM_TARGET_DEVICE=empty` |
| 小模型 | Qwen3-0.6B，BF16 |
| 大模型 | Qwen3.6-27B、Qwen3.6-35B-A3B，TP2 |
| 已测模式 | eager、编译/Graph、在线服务、部分离线生成、FlagCX 通信 |
| 不包含的结论 | 所有模型架构支持、所有量化支持、所有分布式拓扑支持、生产性能认证 |

EMPTY 表示上游 vLLM 的构建目标，不表示模型在 CPU 上执行。设备注册、算子实现和实际硬件执行由插件及厂商运行时提供。

### 2.2 依赖版本及其角色

| 组件 | 版本/位置 | 为什么需要记录 |
| --- | --- | --- |
| Python | `3.12.8` | wheel 与 ABI 基线 |
| PyTorch | `2.11.0+cpu`，厂商配套构建 | `+cpu` 字符串不能被解释为本次使用 CPU 推理 |
| torch-gcu | `2.11.0+3.8.20260713` | 提供 `torch.gcu`、设备运行时及编译接入 |
| FlagTree | `0.7.0+enflame3.6` | Enflame 专用构建，提供实际 `triton` Python 命名空间 |
| triton-gcu | `3.6.0+1.0.20260722` | 配套 GCU 编译组件 |
| FlagGems | `5.4.0` | FL 路径使用的通用/厂商算子实现 |
| FlagCX | 元数据版本 `0.13.0` | 仍需核对实际加载的 Python 包及动态库 |
| FlagCX 运行目录 | `/workspace/s60-adaptation/flagcx-runtime` | 本次真实通信使用的路径，不随公开归档发布 |
| OpenAI SDK | `3.28.0` | 旧 SDK 缺失新 vLLM 导入所需的 `NamespaceTool` |
| pandas | `3.0.6` | 避免旧二进制包与 NumPy 2 的 ABI 冲突 |
| flaggems-vllm | `v0.2.0`，提交 `b5c2c2249319277ccda4d41aa0f65164bd9b2a19` | 安装和复现时固定扩展源码 |

上述 SDK、pandas、编译器保护等部分是原依赖配方已有内容，不是这次 36 文件差异全部新建的功能。保留配方与实际检查，同样是升级成立的前提。

历史 0.28 镜像曾在宿主驱动 `1.10.6` 上验证。基础镜像长名称里的 `driver_1.9.10` 是镜像名称的一部分，不能据此推断当前宿主驱动，也不能当作本次重新实测了驱动版本。

### 2.3 安装原则

本次采用官方上游源码，加插件适配；没有把修改已安装的上游 vLLM 源码作为交付方案。安装插件使用 `--no-build-isolation --no-deps`，避免依赖解析顺手替换厂商 Torch 或编译器。

这不意味着可以跳过依赖准备：必须先按固定配方准备依赖，再禁止安装阶段擅自升级它们。`pip list` 显示版本匹配，也不足以证明同名模块的文件没有被其他 wheel 覆盖。

## 3. 旧版与新版的实质差异

### 3.1 对照对象要分清

本报告同时涉及三个基线：

1. **历史 Enflame 已验证环境**：vLLM `0.28.0+empty` 与旧镜像、旧使用说明。
2. **本次插件 Git 父提交**：`64c9d216...`，用于准确计算 36 文件差异；它已经包含共享框架升级及既有 GCU 保护逻辑。
3. **本次目标上游**：官方 vLLM `0.32.0` 的固定提交。

所以，不能把父提交理解为“完全没有 GCU 适配”，也不能把当前文件里出现的所有保护都说成是本次新增。历史说明、完整当前代码与本次 diff 是不同层面的材料。

### 3.2 版本差异表

| 方面 | 历史 0.28 路径 | 本次 0.32 路径 | 实际影响 |
| --- | --- | --- | --- |
| 上游版本 | `0.28.0+empty` | `0.32.0+empty` | Worker/Runner、模块路径和数据契约需要同步 |
| 上游源码 | `2cf0a6915ce544dc493a0990f2ea38d81601128a` | `5df63a7203cdb9328d824a27b682e77c7b9928be` | 只改版本字符串不够 |
| KV cache 绑定 | 旧代码使用 K/V 领先的五维组织 | 标准化 `[B,H,N,2D]` 绑定，再形成厂商 K/V 视图 | cache 写入必须尊重新 stride |
| KV 分配与绑定 | Runner 中较多私有布局代码 | 使用目标版 `allocate_kv_cache` 等公共工具 | 减少重复实现，匹配目标接口 |
| PP 通信 | 旧 `all_gather_tensors` 调用参数及句柄处理 | 按目标版收发契约调整 | 旧签名会造成兼容问题 |
| 模块导入 | 旧 batch-invariant 等路径 | determinism、DCP 等目标版路径 | 导入成功是最基础前提 |
| GCU IR provider | 不能照搬 CUDA provider 选择 | 使用已注册的 `native` provider | 避免选择 GCU 上不存在的 `vllm_c` |
| 编译整数类型 | 厂商 helper 的全局替换风险仍存在 | 保留整数指针 ABI，启用所需 i64 编译能力 | 避免查表读错地址 |
| 编译精度条件 | 旧说明不能直接证明新代码的舍入行为 | 已测配置保留精度仿真选项 | eager 与编译模式仍需实测对比 |
| TP Graph collective | Enflame/GCU 未进入 custom-op 策略名单 | 增加厂商策略，隔离 Python stream 操作 | 解决 Dynamo 跟踪 Python 对象失败 |
| 词表 mask | 新上游表达式触发 GCU 不支持转换 | 厂商作用域 Triton mask | 保持上游返回类型与分片语义 |
| MoE padding | 非空 mask 可能转入上游 CUDA 实现 | softmax 保留 FL 路径并屏蔽 padded expert ID | 避免 `_moe_C` 调用 |
| 35B Graph SiLU | native 编译路径可能没有有效候选 | 显式选择 `SiluAndMul` FL 实现 | 这是实际通过配置的一部分 |
| 镜像 | 有历史已发布 digest | 只有更新后的配方，未完成新镜像验证 | 旧镜像不能直接改标签冒充新验收 |
| 验收状态 | 历史结果属于历史提交 | 本次功能结果与精度差异分别记录 | 两版测试结果不能互相替代 |

其中 `B` 为 cache block 数、`H` 为 KV head 数、`N` 为 block size、`D` 为 head size。形状相同也不代表物理内存布局相同，stride 是这次适配的关键。

### 3.3 从旧文档继承了什么

旧文档仍可用于理解设备挂载、厂商依赖、FlagTree 防覆盖、FlagCX、模型目录和 CI 拓扑。但是，旧版镜像通过过某个模型，不能证明 0.32 的新接口和新生成代码也通过。

参考资料：

- [旧版使用说明的归档副本](../records/s60-vllm032/usage/enflame.md)。
- [用户指定的 0.4.0-dev 说明](https://github.com/flagos-ai/vllm-plugin-FL/blob/0.4.0-dev/docs/usage/enflame.md)，分支内容可能继续变化。
- [已保存的旧版适配对照分析](../records/s60-vllm032/workspace-reports/enflame-previous-adaptation-reference.md)。该分析含阶段性状态，最终结论以本报告及最新状态段落为准。

## 4. 执行过程与关键转折

### 4.1 阶段时间线

| 时间/阶段 | 做了什么 | 得到的结果或下一步原因 |
| --- | --- | --- |
| 2026-10-30，框架迁移与小模型验证 | 同步 0.32 Worker/Runner、导入与 KV 契约；运行 0.6B | eager 基础生成、TP2、Graph 和服务路径逐步建立 |
| 2026-10-30，编译正确性定位 | 比较 eager、编译无 capture、Graph 子图、RoPE 和索引 | 发现整数指针类型改写会导致实质查表错误 |
| 2026-10-30，舍入条件定位 | 在修正索引后比较编译/Graph 与 eager | 保留精度仿真选项后，小模型五提示 160/160 一致 |
| 2026-10-30 至后续精度阶段 | 建立 NVIDIA 参考、保存候选概率、定位 norm/head/KV | 严格 NVIDIA 对齐仍失败；部分局部误差原因得到解释 |
| 用户接受 0.6B 数值差异 | 关闭该范围的继续深挖 | 保留严格失败与诊断记录，不自动豁免其他任务 |
| 2026-11-02，02 时段，27B/35B eager | 修复词表 mask 和 MoE padding 后重试 | 27B 26/26，35B 25/26 |
| 2026-11-02，Graph 首轮 | 发现 FlagCX stream bridge 被 Dynamo 跟踪 | 添加 collective custom-op 策略 |
| 2026-11-02，Graph 后续 | 发现特定 BF16 linker 候选失败 | 收窄识别错误并让 autotuner 尝试剩余候选 |
| 2026-11-02，03:49–03:51 | 27B Graph 正式请求 | 26/26，FULL capture 35/35 shapes |
| 2026-11-02，35B Graph 重试 | native SiLU 所有候选失败，选择 FL SiLU | 实际 worker 非零探针通过，再进行正式请求 |
| 2026-11-02，04:35–04:42 | 35B Graph 正式请求 | 26/26，PIECEWISE 与 FULL capture 完成 |
| 2026-11-02，05:08–05:11 | 用 CI FL SiLU 配置重测 35B eager 原单文本 | 仍失败，排除“改了 SiLU 配置便自动解决”的推断 |
| 后续受控诊断 | 同一单文本请求提交两个并发副本 | 两份通过且彼此一致，说明上下文敏感；不替换原失败 |
| 镜像阶段 | 启动隔离 Docker，尝试精确基础镜像拉取 | 仓库拒绝授权；用户决定跳过拉取及依赖构建 |
| 2026-11-02 05:53:34 | 保存交付快照 | 25 个 tracked 修改和 11 个 untracked 新文件 |
| 2026-11-02 11:51:22 | 插件本地形成提交 `41ca547...` | 36 文件改动；快照与提交内容关系见第 19 节 |
| 本报告整理 | 核对实际差异、JSON、日志与快照一致性 | 没有用文档整理冒充新的模型复验 |

前述小时区间来自对应请求结果的 `started_at`、`finished_at`。它们不是总适配用时，也不能简单相加后估算未来项目工时；其中包含并行服务、冷编译、诊断和等待。

### 4.2 为什么修复后还会出现新的错误

这一过程有明确的层次：导入成功后才能加载模型；模型能运行后才会覆盖实际词表与 MoE；eager 成功后，Graph 才进一步触及 Dynamo、Inductor、collective 和特定布局编译；编译通过后，还需要检查生成内容。

因此，前一个错误消失后暴露下一个错误并不奇怪。但每次都必须证明新修复解决了原问题，并检查没有改变原验收条件。只看到服务不再报同一个异常，不足以宣称适配完成。

## 5. 全部 36 个改动文件

本节统计严格对应 `64c9d216...` 到 `41ca547...` 的 Git 差异。`+/-` 为新增/删除行数，不是功能数量。路径相对插件仓库，**不是本报告仓库中的源码路径**。

完整代码证据见[tracked 补丁](../records/s60-vllm032/records/handoff/20261102T055334Z/tracked-changes.patch)及[11 个新增文件归档](../records/s60-vllm032/records/handoff/20261102T055334Z/untracked-files.tar.gz)。第 19 节说明它们与当前提交的逐字节核对结果。

### 5.1 构建与安装：4 个文件

| 文件 | + / - | 实际修改 | 为什么要改、验证到哪一步 |
| --- | --- | --- | --- |
| `.github/scripts/enflame/setup.sh` | +3 / -3 | 检查目标从 0.28 EMPTY 改为 0.32 EMPTY，更新提示 | 防止 CI 使用旧依赖镜像时误放行；已有安装检查成功记录，但不代表远端 CI 运行成功 |
| `docker/build.sh` | +1 / -1 | `ENFLAME_VLLM_VERSION` 默认值改为 0.32.0 | 避免构建入口向 Dockerfile 传入旧 0.28 值，覆盖正确默认值；有实际参数转发回归 |
| `docker/enflame/Dockerfile` | +4 / -4 | 固定 0.32.0 及官方源码 SHA，更新版本说明 | 让配方可追溯；厂商依赖保持原固定组合；镜像本身没有完成构建验收 |
| `docker/enflame/README.md` | +20 / -8 | 解释新版配方、历史镜像、候选构建和 CI 状态 | 防止旧镜像被误认为新镜像；其中“Docker unavailable”等文字属于较早阶段，最终阻碍已变为 Harbor 授权失败 |

### 5.2 使用文档与测试配置：4 个文件

| 文件 | + / - | 实际修改 | 为什么要改、验证到哪一步 |
| --- | --- | --- | --- |
| `docs/usage/enflame-vllm032.md` | +162 / -0 | 新建目标版本状态、编译条件、精度与 Gate 限制说明 | 让使用者知道已测配置及未通过项；本文是在该说明上的详细扩展 |
| `docs/usage/enflame.md` | +4 / -0 | 增加 0.32 入口，并声明下方镜像属于 0.28 | 保留历史可用说明，避免版本误用 |
| `tests/platforms/enflame.yaml` | +3 / -0 | S60 overlay 增加 FL SiLU 选择及精度仿真环境项 | 将实机通过需要的配置带入四个 Qwen3.6 TP2 测试；没有改共享 CUDA 模型用例 |
| `tests/utils/model_config.py` | +3 / -1 | 字典 CLI 参数由 `str()` 改为 `json.dumps()` | 服务 CLI 要求 JSON；离线 Python 接口仍接收原字典，嵌套布尔/null/引号需正确序列化 |

### 5.3 运行时与算子：12 个文件

| 文件 | + / - | 实际修改 | 为什么要改、验证到哪一步 |
| --- | --- | --- | --- |
| `vllm_fl/worker/worker.py` | +426 / -180 | 同步 0.32 初始化、内存配置、KV、PP、profiler、sleep/权重接口等契约 | 这是框架迁移主体；GCU 避开 CUDA allocator 查询；有接口回归及模型运行证据，但未逐项覆盖所有新增上游功能 |
| `vllm_fl/worker/model_runner.py` | +394 / -1149 | 同步目标版 Runner；公共 KV 分配/绑定、JIT warmup、reload、输出与位置契约等 | 旧复制实现不能继续机械沿用；删除包含过时 API 和重复私有逻辑，不表示同等数量功能已被实机验证 |
| `vllm_fl/platform.py` | +18 / -2 | GCU cache 标识、collective custom-op 策略、IR provider 默认值 | 分别处理旧编译缓存、Python stream 被跟踪和不可用 CUDA provider；有针对性回归 |
| `vllm_fl/distributed/device_communicators/flagcx.py` | +7 / -0 | 适配 GCU device/current stream，桥接 `gcu_stream` | 满足 FlagCX Python 适配器的 `cuda_stream` 字段接口；真实双 rank all-reduce 及 TP2 已运行 |
| `vllm_fl/dispatch/backends/vendor/gcu/impl/attention.py` | +14 / -36 | 导入路径、block-size 查询契约、标准 KV 视图；移除旧布局接口 | 目标版绑定方式改变；将 K/V 正确视图传给 cache writer 和 attention |
| `vllm_fl/dispatch/backends/vendor/gcu/impl/reshape_and_cache.py` | +38 / -4 | 为标准交错布局增加按 stride 写入，更新布局与地址跨度校验 | 不能把非连续 K/V 视图当连续内存；已有 packed 路径和 slot/grid 保护继续保留 |
| `vllm_fl/dispatch/backends/vendor/gcu/impl/inductor.py` | +55 / -17 | 保留类型的 codegen、内部 i64 选项、缓存盐、特定 linker 候选错误识别 | 修复实际索引错误和部分候选失败；原有 reduction/resource/namespace 适配继续保留，不能全算新增 |
| `vllm_fl/dispatch/backends/vendor/gcu/impl/normalization.py` | +21 / -13 | FP32 norm/weight 运算、残差舍入位置、参数契约 | 对齐目标算子运算顺序；局部回归通过，但 NVIDIA 端到端严格精度仍有差异 |
| `vllm_fl/dispatch/backends/flaggems/impl/normalization.py` | +6 / -0 | GCU 的 FlagGems RMS 分发转交厂商适配 | 避免从另一 dispatch 路径绕过 GCU norm 契约 |
| `vllm_fl/dispatch/backends/vendor/gcu/impl/vocab_mask.py` | +63 / -0 | 新建厂商 mask kernel 与 ABI 检查 | 避免不支持的 bool→i64 表达式，保持分片、padding、added vocab 语义和 int64 输出 |
| `vllm_fl/dispatch/backends/vendor/gcu/patch.py` | +2 / -0 | 将词表 mask 安装函数接入 GCU patch 注册 | 单独写 kernel 不会自动被模型使用，必须完成作用域内接线 |
| `vllm_fl/ops/fused_moe/router.py` | +5 / -6 | softmax padding 留在 FL 分发，padded expert ID 置 -1 | 避开 CUDA-only `_moe_C.topk_softmax`；保留权重/源行语义和 sigmoid 路径 |

### 5.4 回归测试：16 个文件

| 文件 | + / - | 主要检查内容 | 覆盖边界 |
| --- | --- | --- | --- |
| `tests/unit_tests/dispatch/test_gcu_codegen.py` | +50 / -0 | codegen 不改写整数 dtype；未知 ABI 拒绝 | 验证适配边界，不等于任意模型编译都正确 |
| `tests/unit_tests/dispatch/test_gcu_inductor.py` | +63 / -1 | i32 参数中的内部 i64、精确 linker 错误转换、未知错误保留 | 在既有 GCU 适配测试上扩展；不能把全部当前测试都说成本次新写 |
| `tests/unit_tests/dispatch/test_gcu_kv_zeroer.py` | +6 / -9 | 新标准布局的虚拟块地址、alias 与 builder 契约 | 旧后端 shape-helper 调用断言随接口更新 |
| `tests/unit_tests/dispatch/test_gcu_normalization.py` | +59 / -0 | dtype、残差、weight、partial variance、BF16 双重舍入 | 算子语义检查，无法替代完整模型精度 |
| `tests/unit_tests/dispatch/test_gcu_reshape_and_cache.py` | +23 / -0 | 标准布局实际设备写入/读回 | 既有长 prefill、负 slot、越界校验测试继续保留 |
| `tests/unit_tests/dispatch/test_gcu_vocab_mask.py` | +50 / -0 | 六参 ABI、重复安装、空输入、非法输入、非目标厂商 | 真正的数值覆盖还需设备 CPU-oracle 探针 |
| `tests/unit_tests/distributed/test_flagcx_gcu.py` | +31 / -0 | GCU stream 字段桥接和其他设备不变 | 不以 mock 代替真实通信，因此另有实机 all-reduce |
| `tests/unit_tests/ops/test_fused_moe_router_padding.py` | +38 / -0 | softmax padding、ID dtype、FL 调用和 sigmoid 路径 | 与已有 router 测试、实机探针共同使用 |
| `tests/unit_tests/test_enflame_ci_version.py` | +62 / -0 | EMPTY 版本、厂商依赖漂移、构建入口默认值与覆盖传递 | 入口用替身捕获实参，不构建镜像 |
| `tests/unit_tests/test_enflame_collectives.py` | +46 / -0 | 厂商策略和 fullgraph CPU 代理 | 检查 Python stream 操作不进入图；真实 Graph 结果另列 |
| `tests/unit_tests/test_enflame_compilation_config.py` | +23 / -0 | GCU codegen 版本使缓存失效，保留用户 additional config | 扩展既有编译配置检查；其他厂商不增加该键 |
| `tests/unit_tests/test_enflame_ir_priority.py` | +21 / -0 | eager/编译时选择已注册的 provider | 防止 GCU 误选 `vllm_c` |
| `tests/unit_tests/test_model_config.py` | +38 / -0 | 四个 S60 用例的离线/服务配置传递，嵌套 JSON | 验证配置传播，不表示启动了四个硬件任务 |
| `tests/unit_tests/worker/test_model_runner.py` | +7 / -75 | 删除过期 SP 私有方法测试，位置契约改为 MRoPE indexed | 测试按目标接口更新，未宣称 XDRoPE 或任意 SP 组合已获支持 |
| `tests/unit_tests/worker/test_worker.py` | +1 / -1 | Runner 选择逻辑检查入口改到 `_make_model_runner` | 对应代码结构迁移 |
| `tests/unit_tests/worker/test_worker_v032.py` | +148 / -0 | 目标导入、block size、PP 签名、KV 参数、GCU allocator、KV views、预热 guard | 部分为 mock/AST 检查；模型 Gate 负责补真实端到端证据 |

### 5.5 数量如何理解

合计为 4 个构建文件、4 个文档/配置文件、12 个运行时文件、16 个测试文件，共 36 个。净增加 405 行。

Runner 文件删除量大，主要与目标版本的公共接口及代码组织同步有关；不能单看“删除 1149 行”就认定功能被削减，也不能反过来保证所有历史功能保持支持。特别是旧输出字段、XDRoPE、SP 私有方法等，必须依据目标版契约和实际覆盖逐项判断。本次没有这些功能的完整设备矩阵。

## 6. Worker、Runner 与 KV cache 迁移

### 6.1 为什么不是只修改 import

Worker 和 Runner 位于调度、模型、缓存、通信、编译的交界处。上游改变函数签名、返回字段、内存布局后，即使修到“可以 import”，执行仍可能在第一次 prefill、decode、PP 传输或 Graph capture 时失败。

本次同步包括目标版 profiler 工厂及参数、sleep backend 接口、部分权重管理方法、JIT warmup 注册、KV 分配参数和 PP 句柄处理。这些属于兼容目标框架的结构更新；没有针对 sleep、在线权重更新、弹性 EP 等逐项完成硬件验收，应在后续按使用需求补测。

### 6.2 KV cache 的关键变化

旧代码中的 cache 组织为：

```text
[2, B, N, H, D]
 ^
 K/V 维
```

目标版绑定的标准形式为：

```text
[B, H, N, 2D]
```

厂商 attention 所需的 K/V 各自形状为 `[B,N,H,D]`，由标准 cache 经 `transpose(1, 2)` 和最后一维 `split(D)` 得到。K、V 共享原始 storage，是带 stride 的视图，不能假定各自拥有紧凑连续的 `B*N*H*D` 存储。

实际写入地址依赖：

```text
block = slot // N
position = slot % N
offset = block * block_stride
       + position * token_stride
       + head * head_stride
       + feature
```

若继续使用旧连续布局假设，可能写错 K/V 区域或 head/position。服务即便不崩溃，也可能产生错误历史状态，随后表现为输出差异。

### 6.3 写 cache 的处理方式

对于原有 packed 布局，继续使用既有 FlagGems cache kernel；对于目标版标准交错视图，使用明确按 stride 计算地址的 GCU Triton kernel。

校验保留/补充了 dtype、device、维数、输入 token 内连续 head、K/V 相同 stride、支持的布局、真实地址跨度及 int32 可寻址范围。这里必须检查最大实际 offset，不能只检查 `numel()`，因为带间隔视图的地址跨度可能大于元素总数。

已有 slot 转换保护继续保留负数 sentinel 的语义，避免例如 `-2**32` 低位截断后被当成 slot 0。已有分块 launch 将 grid 的 X 维限制到 65535，以覆盖长 prefill。合法非负 slot 值仍由上游调用契约保证；本次没有增加逐元素主机同步检查。

量化 KV cache 不在该 writer 支持范围内，遇到不支持类型应明确报错，不进行静默转换。

### 6.4 公共工具与运行时预热

Runner 使用目标版 `allocate_kv_cache`、`bind_kv_cache`、`map_kv_caches_to_kernel_blocks`、`customize_attention_spec` 等工具。Worker 将 block/hash/alignment 等配置传入新接口，分配 context 也随参数传递。

GCU/NPU 编译前解析 CachedOps 的预热逻辑在父提交中已经存在，本次保留并新增 guard 回归。它用于让 Dynamo 跟踪前完成带 RLock 的惰性分发解析。不能因为这段代码在当前 Runner 中，就把它说成本次 diff 新增。

GCU 不应调用 CUDA allocator 设置查询；对应测试将 CUDA 查询替换为必然报错函数，验证 GCU 路径不会触及它。这是平台隔离的检查，不等于在 GCU 上实现了 CUDA allocator 功能。

## 7. 整数 ABI、编译器和缓存修复

### 7.1 发现的是地址解释错误

厂商旧 codegen helper 会对生成源码作全局 `int64/i64 → int32/i32` 文本替换，包含指针签名。然而输入 tensor 的实际 storage 并没有随文本改写而变成 int32。

以 int64 数组 `[7,8,9]` 为例，小端存储按 int32 观察可能成为 `[7,0,8,0,9,0]`。如果 kernel 把 int64 指针当 int32 指针读取，就会产生错位索引。这种错误应先解决，不能解释为普通 BF16 舍入。

真实编译 `index_select` 探针出现的最大绝对误差达到 FP32 的 2304、BF16 的 2312；实际 RoPE 局部探针在受控索引 ABI 处理后，最大误差从 7.46875 降到 0.03125。这些是特定探针误差，不是全模型误差比例。

### 7.2 修改如何生效

GCU helper 改为使用 Torch `GraphLowering._compile_to_module`，保留整数类型及当前 artifact 协议，并在安装适配时检查已知 ABI。非 GCU 不应用这一修改；未知接口应报错，不能盲目套用。

编译选项不能仅依据输入参数签名是否出现 i64 来决定。Inductor 的 embedding 可能在 kernel 内部把 i32 index 扩展成 i64，因此即使外部签名全是 i32，内部仍需 i64 编译能力。新逻辑为此启用 `enable_i64`，并保留调用者显式提供的 `enable_i64` / `ENABLE_I64` 设置。

这不代表 GCU 原生 Torch 的所有 int64 运算都已支持，也不意味着应该把所有模型张量全局改成 int32。

### 7.3 为什么同时改两层缓存

旧 cache 内可能保存了已经生成错误指针 ABI 的 artifact。只修 codegen，仍可能在进入新 codegen 前命中旧 artifact。

因此同时增加：

| 层次 | 标识 | 目的 |
| --- | --- | --- |
| Torch compiler cache | `fl_gcu_preserve_dtype_v1` | 区分旧类型改写与新 codegen，保留已有用户 tag，重复安装不反复追加 |
| vLLM additional config | `fl_gcu_codegen: preserve_dtype_v1` | 使 vLLM 自己的编译缓存也区分两种行为 |

`additional_config` 需为字典，修改保留用户已有键。该变化针对 GCU/Enflame；不会给其他厂商强加同一个标记。

### 7.4 尚未证明的事

局部索引错误消失，不等于所有剩余精度差异都由索引问题造成。保存的子图比较仍有 BF16 差异，后续 norm、head、历史 KV 和执行上下文诊断正是因此继续进行。

相关证据：[索引比较日志](../records/s60-vllm032/records/logs/index-diff.log)、[保留类型后的比较](../records/s60-vllm032/records/logs/index-diff-preserve-fresh.log)、[子图比较](../records/s60-vllm032/records/logs/codegen-subgraph-v2.log)。

## 8. 词表 mask 与 MoE 路由

### 8.1 27B 词表 mask 为什么失败

TP2 词表 embedding 需要判断 token 是否属于当前 shard 的原词表或新增词表，并产生本地 index 与 mask。目标路径的布尔转 int64 运算会生成 GCU 不支持的转换符号。

曾尝试移除 compiled wrapper，让表达式 eager 运行；真实设备探针随后因原生 int64 比较不支持而中止。因此“取消编译”不是可用 fallback，也没有采用把数据搬到 CPU 的生产方案。

### 8.2 新 mask 的契约

新实现限制在 Enflame patch 作用域中，检查上游六个参数的 ABI，并使用 Triton `tl.where` 避开不支持的表达式。

必须保留的行为包括：原词表区间、原词表 padding、新增词表区间、分片偏移、无效 token 的 mask，以及空输入。输入可为连续 int32 或 int64；输出 index **始终为 int64**，mask 为 bool，不能因为输入是 int32 就改变上游返回类型。

实机 CPU-oracle 压力探针通过 24 个 case，包含大于 int32 范围的 ID。这既验证了算术语义，也防止“为绕过错误而截断输入”的错误修复。之后 27B TP2 eager 正式请求达到 26/26。

证据：[mask 压力探针](../records/s60-vllm032/records/logs/probe-vocab-mask-stress-v2.log)、[修复后 27B eager 结果](../records/s60-vllm032/records/gate-results/27b-eager-vocabfix/)。

### 8.3 35B MoE padding 为什么走错后端

旧 FL router 在有 `padding_mask` 时，把 softmax 路由交给上游函数；上游调用 CUDA 专用 `_moe_C.topk_softmax`，GCU 上不可用。

修复保持 softmax 路径使用 FL 分发，并按上游 CUDA 语义将 padded 行的 expert ID 设为 `-1`：

```python
topk_ids = torch.where(padding_mask[:, None], -1, topk_ids)
```

权重与 source rows 维持原契约，sigmoid 路径仍交给原上游处理。不能为了使程序继续运行，随意给 padding 行赋一个真实 expert ID。

已有/新增 router 单元组合 12 项通过；实际 GCU 对照覆盖 int32/int64 ID 及两种 renormalization 模式。完整 35B eager 随后能够执行全部场景，但仍有独立的单文本内容断言失败。

证据：[router 单测](../records/s60-vllm032/records/logs/unit-router-padding.log)、[设备对照](../records/s60-vllm032/records/logs/probe-router-padding.log)。

## 9. TP2 与 Graph 的修复链

### 9.1 FlagCX stream 适配与真实通信

GCU 使用 `torch.gcu.device` 和 `torch.gcu.current_stream`。当前 FlagCX Python adaptor 接口读取 `cuda_stream`，GCU legacy stream 提供 `gcu_stream`，因此桥接字段满足接口要求。这是 Python adaptor 的字段兼容，不表示实际通信变成了 CUDA。

真实双 rank all-reduce 已完成：每个 rank 的 16 个输出都为 3.0。0.6B TP2 还保存了两条各 16 token 与 TP1 一致的生成结果。单独的 all-reduce 只能说明该通信操作成立，模型级 TP2 证据还需结合真实推理。

证据：[真实 all-reduce](../records/s60-vllm032/records/logs/flagcx-collective.log)、[TP2 生成](../records/s60-vllm032/records/results-tp2-flagcx.json)。

### 9.2 Graph 第一关：Python stream 不应被跟踪

27B Graph 初次启动时，Dynamo 跟踪到 FlagCX stream 桥接，因 `SimpleNamespace.__new__` 失败。上游已有 registered collective custom op，平台策略未包含 Enflame/GCU，导致没有使用所需边界。

修改 `PlatformFL.use_custom_op_collectives()`，增加 `enflame` 和 `gcu`。custom op 边界使 Python stream 管理留在图外，而 collective 按注册算子参与编译。CPU fullgraph 代理和编译配置相关组合 18 项通过；随后继续用真实设备启动确认下一阶段。

### 9.3 Graph 第二关：BF16 linker 候选错误

后续真实编译报错涉及：

```text
R_DTU_ADDR16_LO_ICALL / R_DTU_ADDR16_HI_ICALL
tops_truncf_v2_fp32_to_v1_bf16
```

受控重放显示，这与具体生成布局有关，部分候选可以编译并计算正确。因此修复不是捕获所有异常后返回，而是仅把**已确认的 GCU plain Exception、精确首行错误**转换为 Torch autotuner 能识别的候选编译失败类型 `PTXASError`。

其行为边界为：

- 精确匹配该错误：拒绝当前候选，由已有 autotuner 尝试其他候选。
- 非 GCU、未知符号、不同错误类型或未知异常：保留失败并向上抛出。
- 所有候选都失败：仍然编译失败，不制造输出。
- 不关闭精度仿真来绕开错误。

真实 Torch precompile worker 重放厂商生成的四个配置，三个成功；成功者都通过含负索引的非零 CPU-oracle 比较。第四个候选失败被正确拒绝。对应聚焦回归为 70 项通过。

之后 27B Graph 完成 FULL decode capture 的 35/35 shapes，并完成正式 26/26 请求。

证据：[真实候选重放](../records/s60-vllm032/records/logs/probe-graph-autotune-v2.log)、[27B Graph 服务日志](../records/s60-vllm032/records/logs/gate-27b-graph-linkerfix.log)。

### 9.4 Graph 第三关：35B shared expert 的 SiLU

35B Graph 的 native SiLU 融合 kernel `triton_poi_fused_mul_silu_slice_0` 中，全部候选仍失败。这说明上一节的处理只解决“部分候选有效”这一类情况，不是万能 linker 修复。

已有 FL SiLU 可以通过显式配置选择：

```json
{"custom_ops": ["none", "+SiluAndMul"]}
```

实际 worker 探针确认命中 `SiluAndMulFL.forward_oot`，三个非零 BF16 GCU/CPU 检查通过。大小写敏感：`+silu_and_mul` 不会启用同一个注册类。

带该配置的 35B Graph 完成 PIECEWISE 和 FULL decode capture，FULL 为 35/35 shapes；之后才进行完整请求，最终 26/26。HTTP `/health` 返回 200 是启动阶段证据，不能独立替代这一请求结果。

S60 YAML overlay 随后加入相同 custom-op 选择及 `TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1`，确保测试入口传入已验证的条件。

证据：[实际 worker 分发探针](../records/s60-vllm032/records/logs/probe-silu-dispatch-v3.log)、[35B Graph 服务日志](../records/s60-vllm032/records/logs/gate-35b-graph-silu-dispatch.log)。

### 9.5 重复 TLE MLIR 错误为什么没有判成死循环

服务日志出现过 TLE dialect/MLIR parse 诊断。最小实机探针在 8 rows 的 MoE alignment atomic 路径捕获 `Pipeline run failed: Failed to parse input MLIR`；它不是此前假设的 allocator 无限重试异常。

已有四阶段 fallback 对 1、8、512 rows 的 token/expert/padding CPU-oracle 检查通过，完整服务也继续进入 capture 和请求处理。所以本次没有新增生产 MoE alignment workaround，更没有把重复日志本身当成必须杀进程的依据。

证据：[失败路径探针](../records/s60-vllm032/records/logs/probe-moe-align-inspect.log)、[既有 fallback 检查](../records/s60-vllm032/records/logs/probe-moe-align-legacy.log)。

## 10. 数值精度：差在哪里、差多少

### 10.1 四种不同指标不能混用

| 指标 | 本次例子 | 能说明什么 |
| --- | --- | --- |
| 提示词完整 token 一致数 | 原五条中 3/5 完整一致 | 有多少条生成序列完全相同 |
| 首次 token 分歧位置 | 算术第 7 个，代码第 13 个 | 自回归轨迹从何处开始不同 |
| 局部张量最大绝对误差 | 历史 KV 最大 0.0625 | 指定张量、指定输入的数值差异 |
| 请求检查通过率 | 103/104，约 99.04% | 该请求集的断言通过比例 |

这些都不是“模型准确率损失了多少”。目前没有本任务的大规模任务基准，可以把所有差异归结为统一的模型误差百分比。

### 10.2 参考端是否真的建立了

已经建立。参考端为 NVIDIA RTX 4090、官方 vLLM `0.32.0+cu129`、Torch `2.13+cu129`、BF16、TP1；目标为 S60、vLLM `0.32.0+empty`。历史记录包含 10 个权重/tokenizer/config 文件的 SHA256 一致性证据。

使用 greedy，即 `temperature=0`，每提示词保存最多 32 token，以及逐步候选信息。NVIDIA V1 和 V2 Runner 的原五条输出一致，共 160 token，因此更换参考端 Runner 没有消除本次差异。

本次写报告没有重新连接参考设备或重新计算远端模型哈希；依据是已保存产物。

### 10.3 不同配置的结果

| 对照配置 | 完整一致 | 首次分歧，按 1 起算 | 应如何解读 |
| --- | --- | --- | --- |
| 原 BF16，NVIDIA 对 S60 | 3/5 提示词 | 算术 7；代码 13 | 严格 token 对齐失败；Paris、fox、中文各 32 token 一致 |
| 生产 RMS 候选，原 BF16 head | 3/5 | 算术 7；Paris 11 | 代码修复了，但新出现 Paris 差异，整体仍失败 |
| RMS 候选 + native FP32 head，原五条 | 5/5，160/160 token | 无 | 仅说明改变后的配置通过这五条 |
| 同一 FP32-head 候选，扩展十条 | 8/10 | Japan 14；JSON 16 | 原五条通过不足以外推 |
| S60 eager 对 S60 Graph，已测五条 | 5/5，160/160 token | 无 | 在精度仿真选项开启时，两种 S60 模式一致 |

所有上述保存输出每例长度均为 32；比较没有只取较短共同前缀而忽略剩余长度。也不能把 3/5 直接叫作“模型只有 60% 精度”。

### 10.4 首次分歧时的 logit 意味着什么

原始算术首次分歧附近，NVIDIA 候选存在并列；目标 GCU 的领先差距为 0.125，参考 token 在 GCU 候选中为第 2 名。它支持“候选很接近、数值差异能改变 greedy 选择”这一解释，不能证明后面所有位置都满足 Top-5，也不能转成全模型误差率。

一旦双方选出不同 token，下一步输入历史也不同。继续比较相同序号的 logits，不能不加条件地当作同一输入下的算子精度测试；严格定位需要固定前缀或受控重放。

### 10.5 RMSNorm 修改的目标和限制

RMSNorm 的基本形式为：

```text
variance = mean(x.float() ** 2)
normalized = x.float() * rsqrt(variance + epsilon)
output = cast(normalized * weight.float(), original_dtype)
```

实际实现还包含 residual、`variance_size_override`、`pass_weight`、`pass_weight_add` 等契约。残差加法应在约定边界先舍入回原 dtype，再计算方差；weight 乘法保持 FP32 后一次输出转换，避免先把 normalized 转成 BF16 再乘 weight 的双重舍入。

修改这些顺序能修复局部语义问题，但生产 RMS 候选仍为原五条 3/5 完整一致，并出现新的 Paris 分歧。代码里写“匹配 CUDA 契约”不能替代实际端到端严格对齐结果。

### 10.6 进一步诊断究竟定位到了哪里

| 诊断 | 实际观察 | 证明范围 |
| --- | --- | --- |
| 编译但不 capture | 仍可出现坏输出 | 问题不能只归因于 Graph replay |
| lm_head 实际输入重放 | 抽样投影与 CPU FP64 后 BF16 舍入参考相符 | 没有证明双方所有 hidden state 相同 |
| Japan 单条与 batch | 单条跨设备 32 token 相同；S60 batch 从第 14 token 不同 | 观察到目标执行上下文敏感 |
| Japan layer 7 cache | 当前 Q 相同；25 个历史位置中只有位置 1 不同，554 个 BF16 元素，最大 0.0625 | attention 的历史输入并未全部对齐 |
| 固定 Q、仅交换历史 KV | 重放精确复现 44 个 attention 输出差异，最大 0.001953125 | 该历史 KV 差异足以解释这次 attention 输出差异 |
| prefill 层边界 | 层 0–5 相同；层 6 norm 输出一个 BF16 元素差 0.0009765625 | 差异在更早 norm 边界出现，不能直接怪当前 decode attention |
| 相同输入 norm 独立重放 | 多次相同，单独 batch 大小不能重现全部现场差异 | batch size 单一原因尚未成立 |
| 启用 FL 后的 reduction | mean 阶段 6 个 FP32 值最大差 5.96e-8，传播为一个 BF16 差异 | 定位了局部 reduction 来源，但端到端仍未闭环 |
| 禁用 `mean,mean_dim` | 局部结果恢复；原 BF16 仍 3/5、FP32-head stress 7/10 | 不支持把全局 blacklist 当生产修复 |
| CPU FP64 norm 诊断 | 原 BF16 2/5，FP32-head stress 9/10 | 更高精度算术也不自动等于 NVIDIA fused 算子结果 |
| 官方 NVIDIA fused RMS 边界重放 | NVIDIA 与独立 GCU 均为 -0.2080078125；CPU FP64 为 -0.208984375 | CPU FP64 单点不能证明 GCU 违反 NVIDIA 参考 |

这些诊断显著缩小了若干问题范围，但没有给出“所有剩余差异都由某一算子导致”的最终证明。

证据：[精度审计](../records/s60-vllm032/workspace-reports/precision-alignment-audit-20261102.md)、[审计 JSON](../records/s60-vllm032/workspace-reports/precision-alignment-audit-20261102.json)、[历史 KV 分析](../records/s60-vllm032/records/logs/japan-cache-analysis.log)、[cache 交换重放](../records/s60-vllm032/records/logs/japan-attention-cache-swap.log)、[prefill 层定位](../records/s60-vllm032/records/logs/japan-prefill-layer6-analysis.log)、[NVIDIA RMS 边界](../records/s60-vllm032/records/logs/cuda-rms-boundary.log)。

### 10.7 按精度等级是否通过

| 等级/要求 | 结论 | 原因 |
| --- | --- | --- |
| Tier 1，严格 token，尤其前 10 个 | 未通过 | 算术第 7 token 已分歧 |
| Tier 2，适用位置参考 token 在 Top-5 | 缺少完整通过证据 | 首次分歧处 rank 2 不等于每个适用位置都通过；双方生成轨迹也会分开 |
| Tier 3，限定条件下逐提示语义评审 | 没有完整逐条结论 | 用户接受差异不自动生成全套语义评审 |
| 用户对 0.6B 差异的接受 | 有明确决定 | “这个精度差异是可以接受的”，因此结束该范围的深挖 |
| 27B/35B NVIDIA 对照 | 未完成对应证据闭环 | 0.6B TP1 结果不能外推至大模型 TP2 和多模态 |

原五条提示含自选算术、中文、代码等，并非逐条完整复现官方精度技能的全部标准提示集。如果后续验收要求严格使用标准集，需把覆盖差异明确列入补测。

### 10.8 接受差异之后是否还应该一直调试

对于已披露并被接受的 0.6B 数值差异，本次已结束无边界的继续排查。重新开启应有新的明确目标，例如指定模型、标准提示、前缀重放协议、验收等级和调试预算。

但这个决定没有自动豁免后续大模型、镜像或 CI。35B eager 的特定单文本例外后来是另一次明确接受，不能把两次决定合并成“用户同意全部不测”。

## 11. 大模型正式 Gate 的完整结果

### 11.1 104 个请求是如何组成的

两种模型 × 两种模式 = 四组。每组五个场景：

| 场景文件 | 请求数 | 检查方向 |
| --- | --- | --- |
| `text_single.json` | 1 | 单文本生成及原内容断言 |
| `text_concurrent_8.json` | 8 | 八路文本并发 |
| `image_single.json` | 1 | 单图片理解/输出 |
| `image_concurrent_8.json` | 8 | 八路图片并发 |
| `mixed_concurrent_8.json` | 8 | 文本与图片混合并发 |
| 每组小计 | 26 | 五个场景 |
| 四组合计 | 104 | 20 个场景 |

这里的“20 个场景”不是 20 个请求。该请求集包含内容、异常字符、重复输出等检查，但不是完整模型学术 benchmark。

### 11.2 每组每场景结果

| 模型/模式 | 单文本 | 并发文本 | 单图片 | 并发图片 | 混合并发 | 合计 |
| --- | --- | --- | --- | --- | --- | --- |
| 27B eager | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | **26/26** |
| 27B Graph | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | **26/26** |
| 35B-A3B eager | 0/1 | 8/8 | 1/1 | 8/8 | 8/8 | **25/26** |
| 35B-A3B Graph | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | **26/26** |
| 合计 | 3/4 | 32/32 | 4/4 | 32/32 | 32/32 | **103/104** |

正式结果目录：

- [27B eager：vocabfix](../records/s60-vllm032/records/gate-results/27b-eager-vocabfix/Qwen3.6-27B/port-18100/)。
- [27B Graph：linkerfix](../records/s60-vllm032/records/gate-results/27b-graph-linkerfix/Qwen3.6-27B/port-18100/)。
- [35B eager：paddingfix](../records/s60-vllm032/records/gate-results/35b-eager-paddingfix/Qwen3.6-35B-A3B/port-18101/)。
- [35B Graph：silu-dispatch](../records/s60-vllm032/records/gate-results/35b-graph-silu-dispatch/Qwen3.6-35B-A3B/port-18101/)。

### 11.3 35B eager 失败具体是什么

原请求要求详细介绍 LLM，涉及训练、推理、能力、局限及负责任使用，且至少 256 字符。检查器要求的字面词包括：

```text
large language model
training
inference
limitations
```

原输出非空、连贯，讨论了 hallucinations、bias 等风险，但缺少字面 `limitations`。因此 `expected_semantics` 和 `expected_order` 为 false，其余八项检查为 true。

不能只因检查名叫 `expected_semantics` 就把失败理解为模型完全没有谈局限；也不能因为人读起来能理解，就擅自修改原断言或记为 PASS。报告保留自动检查失败及其实际触发条件。

随后用 CI 的 FL SiLU 配置重新跑同一个单请求，仍然失败。这意味着该内容问题没有被 SiLU 配置修复。重测结果见[原单文本复测 JSON](../records/s60-vllm032/records/gate-results/35b-eager-ci-dispatch-single/Qwen3.6-35B-A3B/port-18101/text_single.json)。

### 11.4 并发两个副本通过为何不能算补齐

诊断将完全相同的原单文本请求提交两份并发，保持同 endpoint 和解码设置。两份响应相互一致、不同于历史单请求，均通过十项原检查。

它证明了观察到的执行上下文敏感性，但没有隔离具体 kernel、batch shape、调度或数值路径，也没有建立硬件根因。它改变了“单请求”场景，因此不能替代原失败，将统计改成 104/104。

证据：[受控并发诊断](../records/s60-vllm032/records/diagnostics/35b-eager-batch-context.json)。

### 11.5 用户接受的范围

在明确披露原始失败后，用户接受了这个具体 35B eager 单文本例外。当前可写为：“四组 103/104，通过特定例外接受交付。”原 FAIL、未确定的根因及未验证 CI 都应继续保留。

### 11.6 不从这些结果推出性能结论

请求 JSON 含实际耗时，eager 与 Graph 的耗时也明显不同；但这些运行有冷编译、不同上下文、不同时间窗口和并发条件，不构成严格控制的吞吐、TTFT、TPOT 或稳定性 benchmark。

本报告不计算生产加速比，不声称性能达到某个发布目标，也不把长输出期间客户端无新 stdout 视为程序停止。

## 12. 单元测试与证据覆盖

### 12.1 主要保存结果

| 日志 | 结果 | 实际覆盖/含义 |
| --- | --- | --- |
| [unit-delivery-final.log](../records/s60-vllm032/records/logs/unit-delivery-final.log) | **115 passed，4 warnings，12.38s** | GCU Inductor、mask、router、collective、编译配置、版本及模型配置选择集 |
| [unit-enflame-build-version.log](../records/s60-vllm032/records/logs/unit-enflame-build-version.log) | **7 passed，1 warning，0.08s** | 构建版本及参数转发选择集 |
| [unit-final-silu-retry.log](../records/s60-vllm032/records/logs/unit-final-silu-retry.log) | 107 passed | SiLU 重试阶段的聚焦回归 |
| [unit-ci-config-final.log](../records/s60-vllm032/records/logs/unit-ci-config-final.log) | 13 passed | 配置传播及入口相关回归 |
| [unit-delivery-accepted.log](../records/s60-vllm032/records/logs/unit-delivery-accepted.log) | 76 passed | 0.6B 接受差异收尾时的较早选择集 |
| [unit-gate-fixes-final.log](../records/s60-vllm032/records/logs/unit-gate-fixes-final.log) | 19 passed | mask/router 组合 |
| [unit-full032-final.log](../records/s60-vllm032/records/logs/unit-full032-final.log) | **1159 passed，229 skipped，2 warnings，1 error** | 较早全量 unit 尝试，存在收集错误，不能当全套通过 |

不同阶段选择集重叠，**不把 115、107、76、19 等直接相加**。`115 passed` 的日志也没有包含本表列出的所有 Worker、normalization 测试文件；相关早期测试有自己的日志。后续新增构建入口用例后，重新执行计数可能变化。

状态文档中还记录过其他全量阶段的 1160、1165 passed，它们对应不同时间与测试集合，不与 `unit-full032-final.log` 的 1159 混写。报告优先链接具体日志，让数字有确定出处。

### 12.2 完整测试为什么没有标绿

较早全量 unit 运行在收集 Ascend 词表测试时缺少可选依赖 `torch_npu`。`pytest tests/ -q` 也曾以收集错误退出，退出码 2。因此已有大量通过与 skip，不代表完整 suite 的命令成功。

这不是本次要顺手修复的 S60 算子问题，但它确实影响“整个仓库测试全部通过”的声明。若要获得完整 suite 结论，应在明确依赖和平台排除策略的环境中重新运行，并保留实际退出码。

### 12.3 mock、设备探针和模型 Gate 分别负责什么

| 层次 | 能有效发现的问题 | 不能单独证明的事 |
| --- | --- | --- |
| import/AST/mock 回归 | API 移动、参数遗漏、分发选择、错误作用域 | 真实 GCU 编译与数值正确 |
| 实际设备算子探针 | 当前输入/shape/dtype 的执行、CPU-oracle 结果 | 完整模型输出与长期稳定性 |
| 模型生成/请求 Gate | 已测完整路径、原内容断言和并发请求 | 未测架构、严格 NVIDIA 精度、生产性能 |
| 镜像内验证与 CI | 环境可重建、目标提交可在 runner 执行 | 不能从主容器成功推断，必须实际运行 |

本次按这些层次保存证据，没有把 CPU 代理 fullgraph 测试称为真实 S60 Graph 验收。

## 13. 镜像、FlagTree 与 CI

### 13.1 镜像到底是做什么的

依赖镜像提供系统库、厂商 Torch/GCU、FlagTree、FlagGems、FlagCX、Python 及 vLLM 等环境。它用于在 S60 宿主机创建容器，也可作为 CI 作业的运行基础。

历史 CI 依赖镜像并不自动包含每一次候选插件修改；通常还需在容器里安装要测试的插件 checkout。现在这个容器里能运行适配，不等于已经生成了别人可以拉取并复现的 0.32 新镜像。

### 13.2 历史镜像与本次候选的区别

| 项目 | 历史已发布内容 | 本次状态 |
| --- | --- | --- |
| 标签 | `harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-enflame-ci` | 不能当作 0.32 发布标签 |
| manifest digest | `sha256:f21e53101ffcf00fa5b70b39913bd401be93c0d1834c0ae8d07684bf0690bc88` | 历史内容标识，不因修改 Dockerfile 而变化 |
| 历史实机插件 | `2cd00248d3992088b2432201629ab295d4d94034` | 与本次提交不同 |
| 历史验证 | 2026-10-13，后于 10-20 形成 canonical tag | 不代替本次硬件 Gate |
| 本次配方 | 源码版本与 SHA 已更新为 0.32 | 未成功完成新镜像构建、发布及验证 |

### 13.3 本次有没有 FlagTree、是什么版本

当前适配环境及配方要求 FlagTree **`0.7.0+enflame3.6`**。它是 Enflame 专用版本，不能替换成通用 `+triton3.6` 构建。

FlagTree 提供 `triton` 命名空间，这解释了为什么 `import triton` 的名字不能单独说明安装的是独立 upstream Triton。其他依赖安装 upstream Triton 时，可能覆盖相同文件却保留 FlagTree 的 distribution metadata。

已有两项只读核查：

- `verify_compiler.py`：校验实际模块来源和 FlagTree RECORD 文件；390 个发行文件、2,814,450,573 字节，错误数 0。
- `verify_index_fill.py`：FlagGems 5.4.0 的固定 `index_fill.py` 发行字节校验通过。

它们说明核查时未发现特定文件覆盖问题，不代表重新验证了全部运行库、宿主驱动或所有编译路径。检查依据见[旧版对照分析](../records/s60-vllm032/workspace-reports/enflame-previous-adaptation-reference.md)。

### 13.4 构建为什么没有完成

早期没有可用 Docker daemon；后期已经启动隔离 Docker 28.5.2，采用 workspace 内状态目录和 VFS。此后拉取精确 Harbor 基础镜像时收到仓库授权拒绝。

用户说明没有该账号，并明确授权跳过拉取及依赖它的构建。所以最终阻碍不能继续只写“没有 Docker”，也不应再反复要求用户提供不存在的凭据。

| 步骤 | 最终状态 |
| --- | --- |
| Docker daemon 可用性 | 后期已有成功启动记录 |
| 指定 Harbor 基础镜像拉取 | 失败后按授权 SKIPPED |
| 依赖该基础镜像的构建 | SKIPPED |
| 0.32 镜像发布 | 未验证 |
| 镜像内完整硬件复验 | 未验证 |
| GitHub runner CI | 未验证，后端禁用 |

证据：[隔离 Docker 日志](../records/s60-vllm032/records/logs/dockerd-isolated.log)、[基础镜像拉取](../records/s60-vllm032/records/logs/docker-base-pull.log)。

### 13.5 CI 配置改了什么、没改什么

修改了 setup 的版本校验、构建默认版本及 S60 测试 overlay。`.github/configs/enflame.yml` 仍指向历史 0.28 digest，平台注册仍 disabled；保留原 runner label、设备及挂载约定，没有把旧镜像改名后强行启用。

CI setup 真实执行曾因 GitHub GnuTLS 连接中止失败，后用浅克隆官方源码作为传输方式，并核对固定 commit 后完成检查。这证明了该安装路径成功，不证明远程 runner workflow 已完成。

## 14. 已尝试但未采用的方法

| 尝试/想法 | 观察结果 | 最终处理及理由 |
| --- | --- | --- |
| 把全局 int64 文本改成 int32 视为正常兼容 | 实际 storage 未变，索引可错位 | 改为保留 ABI；不接受静默地址解释错误 |
| 只依据外部签名启用 i64 | 全 i32 签名内部仍可能扩展成 i64 | 修正编译选项策略 |
| 只修 codegen，不区分缓存 | 可能复用旧 artifact | 同时标记 Torch 与 vLLM cache |
| 关闭词表函数编译 | 原生 GCU int64 比较也失败 | 未采用，编写厂商 mask kernel |
| 把 FP32 head 五条通过当最终精度修复 | 扩展十条仍仅 8/10 | 仅保留诊断，不替代原 BF16 验收 |
| CPU FP64 norm 当生产参考/fallback | 端到端仍失败，且边界值不等于 NVIDIA fused RMS | 未设为生产默认 |
| 全局禁用 FlagGems mean | 局部改善，端到端仍失败/改变分歧 | 未加入生产默认 blacklist |
| 认为当前 decode attention 自身错误 | 历史 KV 不同可重放全部局部差异 | 不作此根因结论，继续追溯 prefill |
| 关闭精度仿真绕过 BF16 linker | 会改变已经建立的精度条件 | 真实通过路径保留仿真，采用候选级错误识别 |
| 对 linker 异常全部吞掉 | 无法保证存在正确候选 | 未采用；未知异常与候选耗尽仍失败 |
| 使用小写 `+silu_and_mul` | 没有选中目标 FL 类 | 使用实际注册名 `+SiluAndMul` |
| 认为候选 adapter 能解决全部 SiLU | 35B native SiLU 全部候选失败 | 明确选择已存在且实机验证的 FL SiLU |
| 因重复 TLE 报错新增 alignment workaround | 既有 fallback 和完整服务能继续通过 | 未新增生产 workaround |
| 将并发两副本通过替换单请求失败 | 测试上下文已经改变 | 仅作为诊断，保持正式 103/104 |
| 修改原 gate 字面断言以获得 PASS | 会改变验收口径 | 未改；用户接受特定例外并保留 FAIL |
| 把历史 0.28 镜像重新标成 0.32 | 不包含新环境验证 | 未采用 |
| 为了“完成 CI”直接启用后端 | 新镜像和 runner 未验证 | 保持 disabled |

这里记录未采用的方法，是为了避免接手者重复同样的排查，并区分局部有效、端到端有效及正式验收有效这三件事。

## 15. 未做、未通过与已接受事项

### 15.1 未闭环清单

| 编号 | 事项 | 状态 | 缺少的证据/结果 |
| --- | --- | --- | --- |
| R1 | 0.6B 原 BF16 严格 NVIDIA token 对齐 | 未通过，已接受差异 | 完整严格通过结果；若重开需限定协议与目标 |
| R2 | Tier 2 全适用位置 Top-5 | 未完成完整结论 | 不能只用首次分歧 rank 2 |
| R3 | 官方标准提示完整覆盖 | 覆盖存在差别 | 原实际自选集不能冒充完全一致标准集 |
| R4 | 27B/35B NVIDIA 逐 token、多模态参考 | 未闭环 | 同权重、同配置、同输入参考及等级判断 |
| R5 | 27B/35B 独立 offline 全套 | 证据不完整 | 在线 Gate 不能独立证明所有离线路径 |
| R6 | 35B eager 单文本 | 原 FAIL，特定例外已接受 | 不改变场景的通过结果及已隔离根因 |
| R7 | 0.32 镜像构建 | 授权跳过 | 可访问基础镜像、构建日志和内容 digest |
| R8 | 镜像发布与镜像内复验 | 未验证 | 实际发布及容器内测试记录 |
| R9 | 硬件 runner CI | 未验证、禁用 | 对目标插件提交的真实 workflow 结果 |
| R10 | 完整 pytest | 未完整通过 | 收集策略/依赖齐全、实际成功退出的全套结果 |
| R11 | 最终提交的全部验收矩阵复跑 | 未执行新的整套复跑 | 已有历史测试与代码快照一致，不等于提交后重跑 |
| R12 | FlagGems 缺失算子上游清单 | 尚未完整闭环 | 每项复现、归属、版本、issue/PR、验证状态 |
| R13 | 性能与长期稳定性 | 未做完整基准 | TTFT/TPOT/吞吐、长稳、资源与失败恢复测量 |
| R14 | 其他架构及未测功能 | 未验证 | V2、量化 KV、其他 speculative/分布式组合等各自证据 |

### 15.2 明确没有做的“捷径”

没有以修改上游 vLLM 源码作为最终交付；没有通过替换模型权重、小模型代跑大模型或 CPU FP64 生产 fallback 来宣称通过；没有修改原失败请求断言；没有把诊断数据覆盖正式失败；没有发布一个未经构建验证的 0.32 镜像；没有把 disabled CI 标成通过。

当前 Enflame 路径保留以 `ModelRunnerFL` 为主的限制。显式 V2 选择、hybrid speculative align 等已有配置保护不等于功能支持；其他 speculative/cache 组合即使配置被接受，也还需独立设备验证。

### 15.3 已接受不代表永久不需要处理

用户决定使这次任务可以按限定边界收尾。若以后目标变为上游合入、公开发布、严格精度验收或生产部署，需重新评估接受的差异是否满足那个目标，并按新的合同补齐，而不能沿用“上一次用户接受过”作为所有后续工作的豁免。

## 16. 复查和复现方法

以下命令分为只读核查、已记录配置和未来重跑入口。它们用于交接，不表示本次写报告时执行了其中全部命令。涉及启动服务或构建的部分，应在目标设备和依赖就绪、且不与其他任务抢卡时运行。

### 16.1 核对插件代码范围

在持有本次提交的插件 checkout 中：

```bash
git show --no-patch --format=fuller 41ca547b36d0a9e4c0fdbbcb3267c82b9dd8431e
git diff --stat 64c9d216ee6c66acb0b9fc8c097b6c1eab3a4ef4 41ca547b36d0a9e4c0fdbbcb3267c82b9dd8431e
git diff --numstat 64c9d216ee6c66acb0b9fc8c097b6c1eab3a4ef4 41ca547b36d0a9e4c0fdbbcb3267c82b9dd8431e
git diff --check 64c9d216ee6c66acb0b9fc8c097b6c1eab3a4ef4 41ca547b36d0a9e4c0fdbbcb3267c82b9dd8431e
```

如果只克隆本报告仓库，没有插件本地提交，使用第 19 节的归档补丁和新增文件审阅。不能假设官方 upstream 能直接 fetch 到这个本地 SHA。

### 16.2 只读检查依赖版本

```bash
python - <<'PY'
from importlib.metadata import version

for package in (
    "vllm", "torch", "torch-gcu", "flagtree", "triton-gcu",
    "flag-gems", "flagcx", "openai", "pandas",
):
    print(package, version(package))
PY
```

版本元数据之外，继续使用插件源码里的 compiler/index-fill 校验器：

```bash
python docker/enflame/verify_compiler.py
python docker/enflame/verify_index_fill.py
```

这些检查不替代真实 kernel 编译。部署时还应记录实际模块 `__file__`、FlagCX 加载路径及宿主设备可见性，避免同名包或其他进程环境导致混淆。

### 16.3 已测的大模型关键配置

历史 Gate 使用真实模型路径 `/models/Qwen3.6-27B` 和 `/models/Qwen3.6-35B-A3B`，TP2、最大长度 32768、显存利用率 0.94；设备组使用过 0/1 与 2/3，端口使用过 18100 与 18101。

```bash
export VLLM_PLUGINS=fl
export FLAGCX_PATH=/workspace/s60-adaptation/flagcx-runtime
export ENABLE_I64_CHECK=0
export TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1
```

最后交付的 S60 overlay 带有：

```yaml
compilation_config:
  custom_ops: ["none", "+SiluAndMul"]
```

对应服务 CLI 字典必须传合法 JSON：

```text
--compilation-config '{"custom_ops":["none","+SiluAndMul"]}'
```

这只是关键参数片段，不是完整通用启动命令。其余参数、图片素材和 Gate 调用遵循插件内真实测试入口及[归档使用说明](../records/s60-vllm032/usage/enflame-vllm032.md)。`ENABLE_I64_CHECK=0` 是历史环境设置，不代表关闭了所有整数正确性要求。

eager 应明确使用该版本支持的 enforce-eager 入口；Graph 应保留相应编译配置。不能只因去掉 eager 参数，就断言成功 capture；仍需检查服务日志中的模式和 shapes。

### 16.4 聚焦回归入口

下列选择集对应主要修复域，实际计数以重跑时 checkout 为准，不承诺总数固定为历史 115：

```bash
pytest -q \
  tests/unit_tests/dispatch/test_gcu_inductor.py \
  tests/unit_tests/dispatch/test_gcu_vocab_mask.py \
  tests/unit_tests/ops/test_fused_moe_router_padding.py \
  tests/unit_tests/test_enflame_collectives.py \
  tests/unit_tests/test_enflame_compilation_config.py \
  tests/unit_tests/test_enflame_ci_version.py \
  tests/unit_tests/test_model_config.py
```

Worker、codegen、norm、cache writer 和真实设备 probes 按受影响域另行选择。不要只重复快的单测而省略真正需要的模型路径复验。

### 16.5 从归档重新汇总正式请求

在本报告仓库根目录运行下面的只读 JSON 汇总，不发起请求：

```bash
python - <<'PY'
import json
from pathlib import Path

root = Path("records/s60-vllm032/records/gate-results")
groups = (
    ("27b-eager-vocabfix", "Qwen3.6-27B", "18100"),
    ("27b-graph-linkerfix", "Qwen3.6-27B", "18100"),
    ("35b-eager-paddingfix", "Qwen3.6-35B-A3B", "18101"),
    ("35b-graph-silu-dispatch", "Qwen3.6-35B-A3B", "18101"),
)
total_requests = 0
total_passed = 0
for group, model, port in groups:
    folder = root / group / model / f"port-{port}"
    request_count = 0
    passed_count = 0
    paths = sorted(folder.glob("*.json"))
    assert len(paths) == 5, (group, len(paths))
    for path in paths:
        summary = json.loads(path.read_text())["summary"]
        request_count += summary["request_count"]
        passed_count += summary["passed_count"]
    print(group, f"{passed_count}/{request_count}")
    total_requests += request_count
    total_passed += passed_count
print("TOTAL", f"{total_passed}/{total_requests}")
PY
```

应得到 26/26、26/26、25/26、26/26，合计 103/104。不要把更早失败重试目录、单请求复测或诊断副本重复计入分母。

### 16.6 未来镜像构建入口

在已具备指定基础镜像访问权限的 S60 构建环境中，可使用配方中的候选入口：

```bash
docker/build.sh --platform enflame --target ci \
  --image-name local/vllm-plugin-fl \
  --image-tag v0.32.0-enflame-candidate
```

这是未来构建配方，**本次没有完成它的成功验证**。该命令也不表示已经推送镜像。后续应记录基础 digest、所有 build args、插件 SHA、构建日志及最终内容 digest，再进入容器复验。

## 17. 后续工作的建议顺序

### 17.1 如果目标只是保存这次工作并交接

保留本报告、原始成功/失败记录、代码补丁、模型/依赖版本和接受边界即可。已接受的精度问题无需因“任务还可以继续”而无限重开。交接者应能独立看到剩余项，而不是只得到一个笼统的 task complete。

### 17.2 如果目标是官方合入或公开发布

1. 明确提交代码、目标模型、验收等级和允许例外，审阅 36 文件差异，尤其是跨后端 Worker/Runner 契约。
2. 整理厂商运行时/FlagGems 缺失算子清单，附最小复现、精确版本、错误与影响范围，区分插件缺陷和厂商编译问题。
3. 取得可用基础镜像或已授权等价构建材料，完成真正 0.32 镜像构建、发布及镜像内校验。
4. 在最终待提交代码和新镜像上，完成要求范围内的回归、四组 Gate；明确如何处理原 35B eager 例外。
5. 若要求严格精度，补足标准输入集和大模型/多模态 NVIDIA 参考，不能用现有功能 Gate 替代。
6. 更新 CI image digest，确认 runner、设备、挂载与超时，启用后保存实际 workflow 结果。

### 17.3 如果目标是生产部署

还需部署模型自己的输入集、长上下文、多用户负载、吞吐与时延、长稳、内存峰值、服务重启恢复及版本回退验证。当前少量功能请求不覆盖这些目标。

时间估计应按确定的工作拆分。镜像授权和 runner 属于外部条件；未知精度根因没有可靠固定 ETA。不能据“只剩一个失败”保证很快完成，也不应把潜在长期研究伪装成必须立即继续的收尾。

## 18. Agent 停止与任务完成的判断

### 18.1 Agent 没有输出，不一定是模型任务停止

本次出现过终端中断、上下文清理后未继续、等待用户输入、远程拉取授权失败，以及非流式请求期间客户端没有新日志等不同情形。它们不能统一解释为同一个程序缺陷。

一次实际误判发生在 35B eager 诊断：非流式 client 被监控判为 idle，但服务日志显示继续生成，原 child 最后正常完成并写出 JSON。处理方式是读取原结果，而不是反复重发请求。

### 18.2 每次判断应核对什么

- Agent 最近的消息/工具是否已经返回，是否在等待输入。
- 实际 server、worker、test child 是否存在，日志是否推进。
- 编译、权重加载、capture 和请求输出是否出现阶段进展。
- 当前 GPU 工作是否属于这个任务，而不是旧服务或其他进程。
- 是否写出完整结果文件、原断言和退出码，而不仅是 `/health` 或端口开放。

上下文清理完成、Plan 标记 done、`[TASK_COMPLETE]` 都不是模型验收的替代证据。完整官方流程及暂停/恢复判断见[FlagScale Agent 流程审阅](../records/s60-vllm032/workspace-reports/flagscale-agent-official-guide.md)。

### 18.3 Agent 工具修复与模型适配分开记

此前对 Agent 的频繁停止问题做过单独的运行循环/上下文恢复处理；这些是 Agent 工具自身的工作，不属于本文 36 个插件文件，也不能把其测试数加进插件回归。安装文件变化是否在旧进程中生效，仍取决于是否重载了相应 Python 代码。

本次文档任务没有为刷新工具而中断正在运行的服务或强制重启 Agent。

## 19. 代码及证据的追溯关系

### 19.1 历史快照与当前提交没有冲突

05:53 的交付快照记录 HEAD 为 `64c9d216...`，分支为 `adapt/vllm032-from-050`，并说明修改尚未提交。11:51 的实际插件仓库已形成 `41ca547...`，当前分支为 `adapt/enflame-s60-vllm032`。

这些描述发生在不同时间；应保存历史事实，同时补充当前状态，不能继续把“现在尚未提交”当成最终结论，也不应回写历史日志伪装当时已提交。

本次报告整理进行了以下只读核对：

| 核对 | 结果 |
| --- | --- |
| 历史 `tracked-changes.patch` 的文件数 | 25 |
| 按这 25 路径从父提交到当前提交重新生成 diff | 与归档 patch **逐字节相同** |
| 历史 `untracked-files.tar.gz` 普通文件数 | 11 |
| 11 个成员内容与当前源码 | **全部 SHA256 相同** |
| 在当前源码上反向 `git apply --check` | 成功，仅检查，没有应用修改 |

因此，历史 25 个 tracked 修改加 11 个新文件，正好覆盖当前提交的 36 文件内容。这是代码追溯核对，**不是新的一轮硬件测试**。

该归档 tracked patch 的 SHA256：

```text
075945ba1006ab01a4c186ce9e5408639642285ae8f20cda7248746d6dcae07f
```

### 19.2 推荐证据阅读顺序

| 材料 | 用途 | 阅读注意 |
| --- | --- | --- |
| [归档 README](../records/s60-vllm032/README.md) | 内容、隐私、验收边界 | 先理解脱敏和排除规则 |
| [STATUS.md](../records/s60-vllm032/records/STATUS.md) | 完整追加时间线 | 早期结论有后续更新，不能只读开头 |
| [0.32 使用说明](../records/s60-vllm032/usage/enflame-vllm032.md) | 已测配置与阶段结果 | 正文中也保留历史阶段描述 |
| [精度审计](../records/s60-vllm032/workspace-reports/precision-alignment-audit-20261102.md) | 独立核对精度证据 | 较早关于 35B 尚未接受的描述由后续明确接受更新 |
| [最终快照目录](../records/s60-vllm032/records/handoff/20261102T055334Z/) | 代码补丁、新文件和当时状态 | 快照是提交之前的时间点 |
| [Gate 目录](../records/s60-vllm032/records/gate-results/) | 请求输入、输出、checks、summary | 采用第 11 节指定四组，避免混入重试 |
| [诊断目录](../records/s60-vllm032/records/diagnostics/) | 受控探针 | 不作为正式 Gate 的替代 |
| [日志目录](../records/s60-vllm032/records/logs/) | 编译、服务、回归与失败 | 同时保留成功和失败 |

### 19.3 公开归档与容器原始目录

容器里的 `/workspace/s60-adaptation/` 对应公开归档的 `records/s60-vllm032/records/`。`usage/` 和 `workspace-reports/` 是补充说明与审计。GitHub 读者应使用本文相对链接，而不是尝试访问容器绝对路径。

初次归档提交 `304873cfea82270286619a11278616ef9f7f5307` 保存 744 份记录，记录文件约 208 MB。这个数字描述那次归档，不是仓库今后永久固定的文件总数。

### 19.4 完整性和隐私边界

公开内容为脱敏副本；原始文件保留在容器。凭据和内部 IPv4 已处理，原始聊天会话、运行时、依赖下载、第三方源码缓存、socket/PID 等不公开。

诊断 `.pt` 张量以 `.pt.gz` 无损压缩保存，它们不是模型权重；归档过程没有反序列化这些张量。审阅者不需要加载张量就能阅读报告、日志和 JSON。

| 元数据 | 作用 |
| --- | --- |
| [MANIFEST.json](../records/s60-vllm032/MANIFEST.json) | 公开文件大小、SHA256、原文件 SHA256 |
| [EXCLUSIONS.json](../records/s60-vllm032/EXCLUSIONS.json) | 排除项及原因 |
| [REDACTIONS.json](../records/s60-vllm032/REDACTIONS.json) | 发生脱敏的文件 |

历史快照内嵌 hash 可能对应原始未脱敏文件，不能拿它要求每个公开副本字节相同；公开归档整体以根目录 manifest 为准。本文第 19.1 节只对明确核对过的代码补丁和 11 个新增源码文件作一致性声明，不外推所有日志。

## 20. 常见问题

### 为什么代码已经能生成，仍然说没有完整验收？

生成只是其中一层。严格 NVIDIA 精度、全部原请求断言、新镜像、最终提交的完整复跑与真实 CI 各有独立证据要求。已有成功不能自动补上其他缺失项。

### 误差到底有多大，能给一个百分比吗？

可以准确给出已测提示的完整一致数、首个分歧位置和某张量的误差，但无法据此给出可靠的“全模型精度下降百分比”。103/104 是请求检查比例；一个 BF16 元素差异也是局部数据，不能叫模型准确率。

### 为什么 FP32 或 CPU FP64 也不能直接证明正确？

本次参考是官方 NVIDIA 实际算子和生成路径。更高精度算术与具体 fused kernel 的舍入位置、归约顺序不同；实际边界重放已经显示 NVIDIA 和 GCU 相同，而 CPU FP64 不同。

### 35B eager 那一个失败是不是硬件算子错误？

没有建立该根因。已确认的是漏掉字面关键词、单请求与并发上下文输出不同。需要固定输入前缀、受控重放和算子边界对照，才能进一步作因果结论。

### 现在能不能直接拿旧镜像用？

旧镜像对应已验证的 0.28 配方，不能声称它已经完成 0.32 验证。若在它之上重新安装新框架和插件，会形成新的环境，仍需检查依赖是否被覆盖，并重新验收。

### 当前有 FlagTree，为什么还会有编译问题？

安装与文件校验通过只能排除特定包覆盖问题。编译器仍可能不支持某个 lowering、布局、符号或 kernel；本次 BF16 linker 和 TLE 路径就是需要单独验证的例子。

### 后续最重要的事情是什么？

先确定目标：若是本次限定交付，已有记录和接受边界足以交接；若是发布，则优先补镜像、最终提交复验和 CI，并明确是否仍允许精度及 35B eager 例外。不要在没有目标的情况下反复扩大精度诊断范围。
