# Enflame 旧版适配与当前 vLLM 0.32 任务的对照分析

审阅日期：2026-11-02 UTC。当前任务状态取自本次约 03:37–03:39 的日志快照，后续执行可能继续变化。

## 1. 结论与资料边界

用户提供的指南确实包含可复用的 S60 适配经验：固定供应商依赖、核验编译器文件、使用 ModelRunnerFL、保留 GCU dispatch、先 eager 后 Graph、执行两种模型的原始验收场景。它描述的是 **vLLM 0.28** 的验证历史，当前任务迁移到 **vLLM 0.32**，所以旧版通过记录只能作为对照基线。

结合此前的 FlagScale Agent 官方流程审阅，目前继续处理大模型 Graph 兼容性有明确依据。当前 35B Graph 有实际编译失败，不属于用户已接受的 0.6B 数值差异。与此同时，不应继续把旧精度诊断扩展成无限排查，也不应把每次长时间编译都判为卡死。

本次只下载资料、读取现有结果，并执行两个不导入 GPU 包的文件校验脚本；没有修改适配代码、安装依赖、控制任务 Agent，或恢复持续监控。

## 2. 固定来源与本地留档

用户原始链接：

- <https://github.com/flagos-ai/vllm-plugin-FL/blob/0.4.0-dev/docs/usage/enflame.md>

读取时 `0.4.0-dev` 指向提交 `732bdbd61e6f3965fb1017130215e3a96604f953`，提交时间为 2026-10-27 02:57:46 UTC。后文引用固定到该提交，避免移动分支以后改变。

| 来源 | 用途 |
| --- | --- |
| [Enflame 部署指南](https://github.com/flagos-ai/vllm-plugin-FL/blob/732bdbd61e6f3965fb1017130215e3a96604f953/docs/usage/enflame.md) | 依赖组合、服务参数、验证步骤、已知限制 |
| [镜像配方说明](https://github.com/flagos-ai/vllm-plugin-FL/blob/732bdbd61e6f3965fb1017130215e3a96604f953/docker/enflame/README.md) | 历史实测、编译器适配理由、撤除条件、容量配置 |
| [Dockerfile](https://github.com/flagos-ai/vllm-plugin-FL/blob/732bdbd61e6f3965fb1017130215e3a96604f953/docker/enflame/Dockerfile) | 精确依赖和源码版本、安装顺序、环境变量 |
| [旧版 Inductor 适配](https://github.com/flagos-ai/vllm-plugin-FL/blob/732bdbd61e6f3965fb1017130215e3a96604f953/vllm_fl/dispatch/backends/vendor/gcu/impl/inductor.py) | reduction 接口、i64 编译选项、异常归一化的实际实现 |
| [硬件测试配置](https://github.com/flagos-ai/vllm-plugin-FL/blob/732bdbd61e6f3965fb1017130215e3a96604f953/tests/platforms/enflame.yaml) | 四个 TP2 模式、显存覆盖配置、120 分钟任务时限 |
| [原始 Gate 说明](https://github.com/flagos-ai/vllm-plugin-FL/blob/732bdbd61e6f3965fb1017130215e3a96604f953/tools/adaptation-gate-cases/README.md) | 原始场景、请求级检查和 JSON 验收 |
| [此前 Agent 流程审阅](/workspace/flagscale-agent-official-guide.md) | 生命周期、停止原因、精度接受、完整验收范围 |

下载目录：`/workspace/enflame-previous-adaptation-source/732bdbd61e6f/`，24 个来源文件均下载成功。其中 `manifest.json` 保存下载路径、固定来源 URL 与 SHA-256；`current-environment-check/` 保存此次当前环境校验结果及版本快照。下载的 `case_utils.py` 与三个 Gate 测试 Python 文件均与当前 checkout 字节一致，当前请求检查与这份旧版参考有直接对照基础。

历史硬件通过结果来自上游文档陈述。本次没有在旧版镜像上重跑，也没有独立取得该历史运行的全部原始日志，不能将文档陈述改写成本次实测。

## 3. 旧版验证的确切基线

| 项目 | 旧版指南规定 |
| --- | --- |
| 硬件 / 已验证宿主驱动 | Enflame S60 / `1.10.6` |
| 依赖镜像 | `harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-enflame-ci` |
| 镜像 manifest digest | `sha256:f21e53101ffcf00fa5b70b39913bd401be93c0d1834c0ae8d07684bf0690bc88` |
| vLLM | `0.28.0+empty`，源码提交 `2cf0a6915ce544dc493a0990f2ea38d81601128a` |
| Python | `3.12.8` |
| PyTorch / TorchGCU | `2.11.0+cpu` / `2.11.0+3.8.20260713` |
| FlagTree / Triton GCU | `0.7.0+enflame3.6` / `3.6.0+1.0.20260722` |
| FlagGems | `5.4.0` |
| OpenAI SDK / pandas | `3.28.0` / `3.0.6` |
| 镜像验证所用插件提交 | `2cd00248d3992088b2432201629ab295d4d94034` |

`torch` 的 `+cpu` 是供应商发行版本字符串，实际通过 `torch_gcu` 在 GCU 上执行。FlagTree 的 Enflame 专用 wheel 提供 `triton` Python 命名空间；不能用通用 PyTorch、通用 FlagTree 或上游 Triton wheel 替换后仍沿用这份验证结果。

旧镜像的硬件验证日期记为 2026-10-13；规范镜像标签于 2026-10-20 发布，指向同一内容。指南还特别说明，依赖镜像不包含每个候选提交的插件修改，部署时必须安装所选 checkout 并重新验证。

旧文档报告的硬件结果有两类，需分别引用：

1. 镜像验证：编译器文件检查、12 个冷缓存 FlagGems 普通算子案例，以及 27B inference、35B serving 的 eager/Graph 原生案例通过。
2. 容量/Gate 验证：35B-A3B TP2 Graph 在长度 32768、最大序列数 256、显存比例 0.94、FP32 Mamba state 下，原始五场景通过，共 26 请求、260 检查。

第二项不能自动推广为所有模型、所有模式的全部原始 Gate 历史都已经独立核实。

## 4. 当前环境对照：版本相近，生成代码契约已经变化

当前插件 checkout：`/workspace/vllm-plugin-FL`，分支 `adapt/vllm032-from-050`，HEAD 为 `64c9d216ee6c66acb0b9fc8c097b6c1eab3a4ef4`，存在尚未提交的适配修改。HEAD 或 editable 包版本字符串都不能唯一标识这些未提交文件。

| 项目 | 本次读取的当前环境 | 含义 |
| --- | --- | --- |
| vLLM | `0.32.0+empty`；目标源码 `5df63a7203cdb9328d824a27b682e77c7b9928be` | 已改变核心框架版本，旧版验收不直接继承 |
| torch / torch-gcu | 与旧指南完全相同的版本字符串 | 应优先调查新框架调用、生成代码与旧编译器的组合 |
| FlagTree / triton-gcu / FlagGems | 与旧指南相同 | 尚不能仅凭 metadata 排除文件覆盖 |
| OpenAI SDK / pandas | 与旧指南相同 | 没有发现这两个版本约束偏离 |
| FlagCX metadata | `0.13.0` | 只证明发行包版本，不能单独证明当前服务实际加载的共享库和 collective 路径 |
| dispatch policy | 与所下载旧版 `enflame.yaml` 字节一致 | 注意力 vendor 优先级与原有排除项仍有对照基础 |
| 新增 Graph 条件 | 当前保留 `TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1` | 旧指南未列此设置，不能假定两版生成代码及舍入条件完全相同 |
| 0.32 镜像 / CI | 新镜像未构建发布；当前 Enflame CI registry 为 disabled | 旧版镜像不能改名后视为 0.32 已验证镜像 |

本次实际执行下载的旧版校验器，结果如下：

- `verify_compiler.py`：退出码 0，`passed=true`，验证 390 个发行文件、2,814,450,573 字节，错误数为 0。检查的是实际 Triton 来源和已安装 FlagTree RECORD 文件哈希。
- `verify_index_fill.py`：退出码 0，`passed=true`，FlagGems `5.4.0` 的 `index_fill.py` 与脚本固定的发行字节匹配。
- 这两个脚本与当前 checkout 内的同名脚本字节一致，且都不需要导入 GPU 包或发起设备任务。

因此，此刻没有发现指南特别警告的“安装其他依赖覆盖了 FlagTree 的 Triton 文件”问题。这个结论不等于所有运行库、驱动和编译路径均正确；本次没有重新验证宿主驱动，也没有重新下载 wheel 做完整供应链核验。

## 5. 旧版哪些经验可以直接用于判断

### 5.1 保留固定依赖，先检查实际文件

旧记录指出 `xgrammar` 的依赖解析可能安装上游 Triton，覆盖 FlagTree 的文件，却留下 FlagTree 的 metadata。因而“pip 显示版本正确”不足以排除编译器被替换。

当前两个文件校验器已通过，后续不必无证据地重装整套环境。若发生新的依赖安装，再针对变化重查。旧版 `setup.sh` 明确要求 vLLM 0.28，当前版本应使用适配后的 0.32 setup；不能直接执行旧 setup 或绕过版本检查。

### 5.2 旧编译器桥接有契约与范围

旧版代码已经存在三类供应商适配：

| 适配 | 解决的实际问题 | 对当前工作的启示 |
| --- | --- | --- |
| Persistent reduction 接口桥接 | Torch 与 TorchGCU 参数数量及延迟注册不一致 | 检查首次和重复注册、两个 GCU 模块别名；不能只看安装时接口 |
| i64 编译选项转发 | Torch 选项边界丢弃 GCU 所需的显式 `enable_i64` | 环境开关不能代替编译器真实 options；张量存储和指针类型要一致 |
| 寄存器资源异常归一化 | 供应商抛出普通 Exception，Torch 无法跳过失败 tile | 可以让 autotuner 尝试其他配置，但所有候选都失败时必须继续报错 |

当前把精确匹配的 BF16 linker 错误映射到 Torch 可拒绝候选的异常，沿用了第三项的思路。其有效性取决于实际内核是否还有能够正确编译、正确运行的候选配置。单个 replay 通过不代表全部模型算子都有可用配置。

旧版还要求移除适配前，先转换对应契约测试，再做禁用该适配的真实 S60 冷编译与结果校验。仅凭版本号升级、mock 测试或一次 import，不能删除这些适配。

### 5.3 ModelRunner、attention 与状态精度属于验证条件

旧指南固定 `ModelRunnerFL`，拒绝显式 V2 runner；attention 由 GCU vendor backend 优先提供。hybrid speculative decoding 加 `mamba_cache_mode=align` 的间接指针路径属于明确限制。

旧版 35B Graph 容量记录保留 FP32 Mamba state。后续对照应记录实际生效值，不能通过降低状态精度、改 runner、改变 TP 或降低并发来宣称原配置通过。其他 speculative/cache 组合也没有因配置可接受而自动获得硬件验证。

### 5.4 两套长度配置都合理，分别对应不同验收

部署例子及原生 YAML 使用长度 8192；S60 的有效显存比例由平台配置覆盖为 0.94。原始容量/Gate 的 35B Graph 记录使用长度 32768、最大序列数 256 和 FP32 Mamba state。

所以看到 8192 与 32768 不应直接判定配置错误。后续每份结果必须注明对应合同；缩短到 8192 的启动或冒烟成功，不能替代长度 32768 的原始容量测试。

### 5.5 冷编译时间长有先例，但显式失败无需继续等待

旧版 e2e 任务允许 120 分钟；README 记载一次 35B serving 运行耗时 3607 秒，约 60 分钟。这个数字是该次 serving 运行时长，并非所有当前启动的固定耗时或完成 ETA。

判断应以实际进程、日志阶段与退出结果为依据：

- 仍有编译/预热进展：属于可观察的工作，广播等待警告本身不能证明死锁。
- 已出现最终 `NoTritonConfigsError`、worker 失败与 engine 初始化失败：该次启动已经失败，继续等这一实例不会变成成功。
- Agent 回到输入框：另查 turn 的停止原因；之前达到 200 次迭代上限，与模型编译器失败是两类事件。

## 6. 本次对当前结果的直接核验

### 6.1 eager 请求级结果

本次直接读取以下目录中的全部场景 JSON，而非只引用 Agent 的总结：

- `/workspace/s60-adaptation/gate-results/27b-eager-vocabfix/`
- `/workspace/s60-adaptation/gate-results/35b-eager-paddingfix/`

| 模型 / 模式 | 场景与请求结果 | 判断 |
| --- | --- | --- |
| 27B TP2 eager | 五个 JSON 均 `summary.passed=true`，26/26 请求通过 | 这一轮原始场景通过 |
| 35B-A3B TP2 eager | 四场景通过；单文本场景失败；总计 25/26 请求通过 | 整组未通过 |

35B 单文本 JSON 的 `expected_semantics`、`expected_order` 均为 false，其余输出健康检查通过。已有日志指出缺少要求的 `limitations` 关键字。不能仅凭内容非空、看起来通顺，或将其笼统归为已接受精度差异来放行。当前尚无证据证明它必然是硬件错误，也不能擅自降低原始检查标准。

### 6.2 最新 Graph 重试：两种模型已经出现不同结果

此次读取的服务日志为：

- `/workspace/s60-adaptation/logs/gate-27b-graph-linkerfix.log`
- `/workspace/s60-adaptation/logs/gate-35b-graph-linkerfix.log`

27B 在 03:37:29–03:37:30 记录 backbone 的 `(1, 2048)` 范围编译完成，耗时约 159–161 秒；随后记录总 `torch.compile` 约 182 秒，03:37:56 有 initial profiling/warmup 完成记录。这是新的阶段进展，但尚不能由这些行宣告完整 graph capture、服务请求或全部 Gate 通过。

35B 在 03:37:13 明确终止于：

```text
triton_poi_fused_mul_silu_slice_0
NoTritonConfigsError: No valid triton configs.
R_DTU_ADDR16_LO_ICALL / R_DTU_ADDR16_HI_ICALL
tops_truncf_v2_fp32_to_v1_bf16
Engine core initialization failed
```

这说明此轮失败内核的候选配置最终全部不可用。之前 replay 中“四个配置有三个能编译并通过 CPU oracle”只验证了那个具体 replay，不能推广到这个融合内核。当前窄范围异常适配保留了最终失败，符合“不吞掉所有候选失败”的边界，但并未完成 35B 整模型修复。

linker 的 `recompile with -fPIC` 是工具诊断文字，不是已经验证有效的修复步骤。后续应检查实际生成内核、转换符号、编译 options 与供应商 lowering；未经验证不能直接声称加一个参数就能解决。

## 7. 结合 Agent 官方流程后的后续优先级

1. **完成当前 27B Graph 的结果判定。** 读取同一轮后续服务与测试结果，确认真实 capture、生成和五场景结果。已有进展足以避免无理由重启或重复冷编译；如果失败，保存第一处实际异常。
2. **将 35B Graph 收敛到已失败的融合内核。** 保存生成源码、shape/stride/dtype、全部 tile/options、完整 linker 错误及固定环境。先用该内核验证是否存在可行的精度保持方案，再做整模型重试。与旧版已通过路径对照，区分新框架融合/转换生成变化和供应商能力边界。
3. **保留当前精度条件。** 不能为了越过编译错误而直接关闭 `TORCHINDUCTOR_EMULATE_PRECISION_CASTS` 并宣告原配置通过。任何改算法、改融合或改精度的候选，都要用真实输出检查证明其有效范围。
4. **单独处理 35B eager 的质量失败。** 使用已保存的原始输入、输出、生成参数和检查；如需对照参考，先明确具体假设，避免回到与该失败无关的 0.6B RMS 深挖。
5. **核对完整矩阵，再处理交付阻塞。** 当前原始 Gate 是两模型 × eager/Graph × 五场景，即 20 场景、104 请求。原生 e2e、HTTP 冒烟、算子单测与此矩阵各自保留。新镜像构建、发布和硬件 CI 仍需具备 Docker/runner 的环境；当前容器内反复修改声明不能代替实际运行。
6. **遇到同类失败反复出现，改变诊断方法。** 按 Agent 的 debug-strategy 重新审查假设，用能区分原因的最小实验推进；不因一次局部 replay 成功就长时间重复完整模型，也不因一次失败就宣布后端永远不支持。

这些是后续判断依据，并未作为新指令发送给正在运行的 Agent。

## 8. 用户接受的差异与后续完成标准

用户已经明确接受原 Qwen3-0.6B 任务的数值差异，相关记录应保持“已知差异经用户接受”，而不是写成严格 NVIDIA token 对齐通过。此次阅读旧版资料没有重新开启那条精度排查。

这一接受不自动覆盖 35B 请求检查失败、Graph 无法启动、镜像未构建或 CI 未运行。原始用户限定模型的交付范围，与官方技能完整后端验收范围，应继续分别记录。

后续遇到 `task complete` 或界面停止，应同时检查：原始范围、剩余计划、实际请求 JSON、编译/服务退出信息和 Agent turn 的停止原因。单个完成标记、一个成功内核或一个正常 HTTP 返回，均不足以代表整个适配交付完成。

当前最有价值的方向是大模型 Graph 的具体兼容失败与尚未通过的请求，而不是重新安装已通过文件校验的整套依赖，或继续扩大用户已接受的小模型精度诊断。
