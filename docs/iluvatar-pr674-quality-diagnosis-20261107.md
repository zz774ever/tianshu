# PR #674：35B Graph 输出异常定位与待合入项

日期：2026-11-07。对应仓库：`flagos-ai/vllm-plugin-FL`。

## 1. 结论及证据边界

GitHub API 再次确认 PR #674 的最新提交仍为
`7a94aeec80fbb795d5596569eb7d40cfe5460106`，没有更新的提交可拉取。

35B 的错误已经再次复现，不能归结为一次没有证据的“偶发模型回答不佳”。
当前证据将问题缩小到 **Inductor 编译结果与 CUDA Graph 回放的组合路径**。
保留编译、关闭回放，以及关闭编译、保留 decode Graph 的对照均没有出现同类错误。
但还没有找到第一个产生错误的模型层、具体内核或越界地址，因此不能直接指定是
FlagGems、FlagGems-vllm、FlagTree、vLLM、插件或 CoreX 运行库中某一个项目的缺陷。

进一步关闭 Inductor 的缓冲区复用及 inplace buffers、同时保留编译和 Graph 后，
两次原始完整 gate 加 50 个额外诊断请求共 102 个请求通过，已经整理成限定范围的
平台兼容补丁。这证明该开关组合在已测条件下能够避开问题，
还没有证明具体是哪一块缓冲区发生了覆盖、越界或过早释放。

已确认的另外一个独立问题是 gate 的数字答案检查过宽，会把包含 `42` 的错误回答
判为通过。该检查已有待合入补丁和回归测试。

另一个已验证的绕过方式是关闭 Inductor 并保留 decode Graph。
这些配置对照不是已经找到了编译器中具体错误指令的证据。

## 2. 本次固定环境

沿用已搭建的最小容器 `fl-gate-minimal-20261107`，使用系统 Python，不建 venv，
未重新拉镜像，也未重新安装 NVIDIA 环境。

核对了容器 `vllm_fl/` 下 273 个 Python 源文件的 SHA256；与 PR 工作树相比，
只有安装时生成的 `_version.py` 不同。其余 272 个运行时源文件一致，
没有依赖一组尚未合入 PR 的插件源码热补丁才能跑这些对照。

| 项目 | 本次实际值 |
|---|---|
| 镜像基底 | `harbor.baai.ac.cn/plugin/vllm-plugin-fl@sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18` |
| GPU | Iluvatar BI-V150；每个服务 TP=4 |
| Python | 系统 Python `3.12.11` |
| PyTorch | `2.10.0+corex.4.5.0` |
| vLLM | `0.32.0+empty` |
| 插件 | PR `7a94aeec80fbb795d5596569eb7d40cfe5460106` |
| FlagGems | `5.5.0.dev0`；`2bcfe2656dad0b654077fcfe7d66e6a93542afab` |
| FlagGems-vllm | `0.3.0.dev1`；`b434eafb1715849d1019ddcd480c5fc39461665c` |
| FlagTree | `0.7.0+iluvatar3.6` |
| FlagCX | `6143384797219733aee89bd3118b2cb184ad4959` 的运行时 |
| 模型 | `/models/Qwen3.6-35B-A3B` |
| 服务模型名 | `qwen-gate` |
| 最大长度 | `32768` |
| 算子排除 | `slice,mm,mm_out`，所有对照保持一致 |

所有 Graph 对照都保留用户指定的 capture sizes：`[1,2,4,8,16,32]`。
没有通过降低原始 gate 并发、缩短原始长文本用例或更换测试图片来报告通过。
额外的短文本与算子测试是独立诊断，单独计数。

原始出错服务及后续 IR 包装对照使用物理卡 `4,5,6,7`、端口 `8145`；
关闭 Inductor 的对照使用 `8,9,10,11`、端口 `8146`；
关闭回放的对照使用 `12,13,14,15`、端口 `8147`。
这些设备均为同一服务器的 BI-V150。不同 GPU 组是对照实验的限制，
不能把这些有限实验描述为已经证明所有设备、并发顺序和执行次数都稳定。

本机仍使用前一轮已经验证的 `libcuda/libixthunk/libcudart` 只读覆盖挂载。
其他机器驱动、分配和最小 Graph 捕获本来正常时，不应照搬这些覆盖文件。
这次输出异常发生在服务就绪后的推理阶段，与之前启动时的运行库初始化失败有不同证据。

## 3. 原始失败具体是什么

原始 35B Graph 完整 gate 第一轮为 `25/26`。失败请求是：

```text
scenario: text_concurrent_8
request_id: text-01
prompt: Compute 19 + 23. Reply with the number only.
expected: 42
actual: 4ally
temperature: 0
```

同配置重新启动后的原始 gate 记为 `26/26`，但同题实际回答：

```text
4\n                    \n42
```

它含有 `42`，却不是完整、正确的“只回答数字”。历史原始 JSON 与通过状态保留，
没有被新的检查或对照结果覆盖。

## 4. 额外复现及 token 证据

在原来包含 Inductor 和回放的配置下，额外执行两批诊断：

| 文件 | 请求数 | 原有检查失败 | 严格数字格式失败 |
|---|---:|---:|---:|
| `requests.json` | 26 | 2 | 2 |
| `requests-extended.json` | 50 | 0 | 1 |

第一批同一道题出现 `4a`、`4 excerise`；第二批出现
`4en19 + 23 = 42`，后者再次绕过了原来的子串检查。

诊断保留了逐 token 的前五项 logprobs。单请求回答 `42` 时，第二个 token `2`
的 logprob 约为 `-0.00002`，与其他候选有明显距离。
出现 `4a` 时，第二个 token `a` 的 logprob 为 `-5.5091`，前五候选变为
`a/nal/itt/E/on`，正确的 `2` 不在前五项中。

这表明异常在第二个生成 token 的分布处已经出现，不能仅归咎于客户端显示、
文本拼接或“模型正常地选择了另一个等价答案”。它仍不能定位首次出错的模型层。

诊断脚本还包含请求顺序反转、把算术题放到最后、8 个相同算术请求等对照。
这些形式在已执行的批次中返回正确答案，说明请求组合和执行状态值得继续追踪；
不能据此保证调整顺序后永远正确，更不能把调整顺序当作修复。

## 5. 已做的隔离实验

### 5.1 保留 decode Graph，关闭 Inductor

```json
{"mode":0,"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,8,16,32]}
```

结果：50 个额外诊断请求正确；原始 gate 全部 26 个请求通过。
原始文本并发和图文混合中的算术题均为严格的 `42`。

证据：`requests-decode.json`、`decode-gate/`、`diagnose-decode-gate.log`。

### 5.2 保留 Inductor，关闭 Graph 回放

```json
{"mode":3,"cudagraph_mode":"NONE","cudagraph_capture_sizes":[1,2,4,8,16,32]}
```

启动后的实际配置把 capture sizes 清空，这是 `cudagraph_mode=NONE` 的正常结果。
结果：50 个额外诊断请求正确。此项未另外执行完整 gate，不能写成完整 gate 已通过。

证据：`requests-compiled.json`、`diagnose-compiled-server.log`。

### 5.3 仅关闭 IR torch 包装：不能作为修复

```json
{"ir_enable_torch_wrap":false,"cudagraph_capture_sizes":[1,2,4,8,16,32]}
```

结果：最初 50 个短诊断请求均正确，但随后执行完整原始 gate 时，文本并发仍返回
`4inda`，最终为 `25/26`。因此“短请求对照通过”不足以作为修复结论。

为这一候选设置临时准备的平台默认值修改已经撤回，没有放进待合入补丁。
没有宣称它一定是长文本触发的，因为本实验尚未单独隔离长文本这个变量。

证据：`requests-no-wrap.json`、`no-wrap-gate/`、`diagnose-no-wrap-gate.log`。

### 5.4 关闭编译缓冲区复用

```json
{"inductor_compile_config":{"allow_buffer_reuse":false,"inplace_buffers":false},"cudagraph_capture_sizes":[1,2,4,8,16,32]}
```

与原始出错服务使用相同物理卡 `4,5,6,7`。启动日志确认仍为 `mode=3`、
`FULL_AND_PIECEWISE`、`ir_enable_torch_wrap=true`，没有关闭编译或 Graph。

执行顺序及结果：

| 顺序 | 实验 | 结果 |
|---|---|---|
| 1 | 完整原始 gate | 26/26 |
| 2 | 额外短请求诊断，包括变换顺序和相同请求并发 | 50/50，严格数字检查无异常 |
| 3 | 同一服务再执行完整原始 gate | 26/26 |

两次原始 gate 的文本并发与混合场景均严格回答 `42`。
合计 102 个请求通过，结果与仅关闭 IR 包装后完整 gate 再次失败形成对照。
两次完整 gate 在同一服务中执行，不是两次重新启动服务的稳定性测试。

此结果支持在当前栈中采用禁用编译缓冲区复用的兼容处理，
但两个开关目前一起测试，尚未分别确定哪一个是必要条件。
禁用这些优化可能增加内存占用或影响性能；没有做专门性能测量。
日志记录的本轮 Graph 捕获增量仍约为 `0.06 GiB`，这不能替代完整峰值内存测量。

证据：`no-reuse-gate/`、`requests-no-reuse.json`、`no-reuse-gate-repeat/`，
以及相应 server/test 日志。

### 5.5 MoE 算子独立数值检查

在空闲的物理卡 0 上执行，独立于模型服务：

- 256 experts、top-k=8，分别测试 1/2/4/8/16/32 行。
- `topk_softmax` 与 PyTorch CPU 参考对照，包括改变输入后的 5 次 Graph 回放。
- `moe_align_block_size_triton` 校验路由覆盖、专家分组和 padding，包括 5 次改变路由后的回放。
- MoE 第一段 GEMM 与 `moe_sum`，测试 1/2/4/8 行，以及每种 3 次回放。
- GEMM 另外测试捕获时所有 expert IDs 为 `-1`、回放时改成有效专家的路径。

上述已执行的检查均通过。GEMM 的输入形状为 BF16、K=2048、N=256、256 experts，
报告的最大绝对差为 `0.00390625`；比较容差和详细值记录在诊断脚本及日志中。
这些检查没有覆盖整个模型、所有真实权重和 MoE 第二段 GEMM，因此只能排除这些
已测的简单复现，不能据此证明 MoE 全部实现都正确。

## 6. PR 需要一并处理什么

### 6.1 35B 编译与回放组合

待合入的 `vllm_fl/platform.py` 修改仅在以下条件成立时禁用两项复用优化：

- 厂商为 `iluvatar`。
- 文本模型类型为 `qwen3_5_moe_text`，对应这次的 35B MoE。
- 后端是 Inductor、编译模式非 NONE，且使用 full Graph。

它保留编译、Graph、capture sizes 和 IR 包装设置；不对 dense 27B、其他厂商、
eager 或关闭回放的配置追加此设置。新增单元用例检查这些边界。
该变更属于有测试依据的兼容处理；底层内存生命周期缺陷仍需继续追到具体张量。

尚未合入补丁时，可在服务终端手动使用等价参数：

```bash
source /opt/gate/gate-env.sh
cd /opt/vllm-plugin-FL
export MODEL_PATH=/models/Qwen3.6-35B-A3B
export SERVED_MODEL_NAME=qwen-gate
export PORT=8145
export GRAPH_COMPILATION_CONFIG='{"inductor_compile_config":{"allow_buffer_reuse":false,"inplace_buffers":false},"cudagraph_capture_sizes":[1,2,4,8,16,32]}'
bash tools/adaptation-gate-cases/run_serve_graph.sh
```

另一个终端执行原始测试：

```bash
source /opt/gate/gate-env.sh
cd /opt/vllm-plugin-FL
export MODEL_PATH=/models/Qwen3.6-35B-A3B
export SERVED_MODEL_NAME=qwen-gate
export PORT=8145
export RESULTS_DIR=/results/35b-decode-graph-verified
bash tools/adaptation-gate-cases/run_test.sh
```

这是当前最小容器的路径。其他机器应替换模型路径、源码目录、设备编号、FlagCX 路径
及空闲端口；无运行库故障的机器不添加本机的驱动覆盖。

已有打包脚本 `/opt/gate/run-one.sh` 会无条件重写 `GRAPH_COMPILATION_CONFIG`。
因此不能仅在外面 export 新值后就直接调用原版本 `run-one.sh`；应采用上面直接调用
原始 serve/test 脚本的方式，或先让包装脚本支持配置覆盖。
本次没有重建、替换之前导出的镜像或安装输入归档。

如果需要另一个已验证的回退配置，可改用第 5.1 节的 `mode=0`、
`FULL_DECODE_ONLY`；它减少了编译覆盖范围，应单独记录。

### 6.2 数字检查漏洞：已有待合入补丁

修改 `tools/adaptation-gate-cases/case_utils.py`：

- 为数字文本题 `42/7/30` 增加 `expected_exact`。
- 检查完整答案在 Unicode NFKC 规范化并去掉首尾空白后是否等于预期数字。
- `mixed_concurrent_8` 使用同一个文本请求构造器，也会保留这项检查。
- 原有图片、长文本、语义与顺序检查保留。
- 不更换题目、图片、并发或 token 限制，不重写历史结果。

新增 `tests/unit_tests/test_adaptation_gate_quality.py`，包含错误的额外数字、
多余字符、历史异常字符串和正确答案等 11 个回归用例。

### 6.3 安装脚本和检查脚本必须与新依赖对齐

截至所查 PR 提交，仍存在：

| 路径 | 当前行为 | 要复现本轮新依赖时的要求 |
|---|---|---|
| `.github/scripts/install_flaggems_vllm.py` | 固定 `v0.2.0` / `b5c2c224...` | 为 Iluvatar 新栈明确安装 `b434eafb...`，避免又降回旧 helper |
| `.github/scripts/iluvatar/setup.sh` | 调用上述共享脚本，未显式升级为本轮 FlagGems | 明确安装本轮验证的 FlagGems 源码版本与 helper |
| `.github/scripts/iluvatar/verify_stack.py` | 断言 FlagGems `5.3.5` | 与所选择的 `5.5.0.dev0` 新栈保持一致，并验证 helper 来源提交 |
| `docs/usage/iluvatar.md` | 基础镜像表仍为旧栈，新旧路径容易混淆 | 分开写镜像原装值和升级后的测试值、安装方式及结果边界 |

`git pull` 更新插件源码，不会更新已经安装的独立 Python 依赖。
也不应直接升级所有厂商共享的 helper 默认 pin，再假定其他平台都兼容。
可采用 Iluvatar 专用版本配置或共享安装器的显式参数，并配套检查来源提交。

### 6.4 不应无证据追加的修改

- 不把 `slice/mm/mm_out` 当作已经修好；所有模型对照仍依赖相同排除设置。
- 不因为本题失败就盲目重装全部 Python 依赖、替换健康机器驱动或加 NVIDIA 依赖。
- 不把有限 MoE 小算子测试通过写成已经完成模型精度对齐。
- 不把第二次通过覆盖第一次失败，也不把“命中子串”写成格式和内容都正确。

## 7. 代码交付和复核方式

待合入变更位于独立工作树：

```text
/workspace/pr674-quality-diagnosis-20261107
```

它基于同一个 PR head，包含范围限定的缓冲区兼容设置、严格数字检查、
相应回归测试及使用文档补充。
没有把未经完整验证的 IR 包装设置留在平台默认值中。
补丁文件 `pr674-quality-followup.patch` 可在 PR 仓库根目录使用：

```bash
git apply --check /path/to/pr674-quality-followup.patch
git apply /path/to/pr674-quality-followup.patch
```

本次没有替用户提交或推送到上游 PR 分支。诊断文档和补丁会同步到已授权的
`zz774ever/tianshu` 仓库，便于后续合并。

硬件请求对照使用原 PR 运行时代码和显式参数完成。之后将平台兼容设置及严格 gate
检查复制到该最小容器，并用真实 `EngineArgs.create_engine_config()` 检查默认参数
能否自动生效；这一配置构造验证不加载模型权重，单独记录。
检查结果：35B 的两个复用开关自动设为 false，27B 不添加这两个开关；
两者都保留编译模式、FULL_AND_PIECEWISE、IR 包装和指定 capture sizes。
两个真实配置构造检查均通过。补丁的数字答案及平台范围回归测试共 22 项通过。
之前导出的镜像文件不包含后补的平台及 gate 检查修改。

原始门禁结果位于此前文档对应的 `records/minimal-gate-container-20261107/`；
本次新增诊断证据独立放在 `records/pr674-quality-diagnosis-20261107/`。
测试配置、错误输出和未通过的候选方案都保留，以免把诊断记录误当成验收结果。

## 8. 为什么之前可能没有发现

1. 原始完整 gate 每轮只有 26 个请求，35B 文本算术题的并发路径样本很少。
   本次同配置的结果也会变化，一次成功不能证明长期稳定。
2. 原来的检查只查找子串，历史输出 `4\n                    \n42` 会被记为通过。
   所以“全部用例显示 PASSED”不必然代表已经检查了数字答案的完整内容。
3. PR 的 `.github/scripts/iluvatar/run_gates.sh` 默认采用 `mode=0`、FULL Graph、
   `custom_ops=["all"]`、`ir_enable_torch_wrap=false`，而直接调用原始
   `run_serve_graph.sh`、仅指定 capture sizes 时会进入 `mode=3` 的编译路径。
   两种“Graph 测试”的编译设置并不相同。
4. 过去和本轮的依赖版本、运行库、模型与请求顺序也可能不完全一致。
   尚未对“旧依赖和新依赖、其他设置完全一致”做完整回归对照，
   因此不能认定该缺陷由 FlagGems 升级或此次插件适配引入。
