# S60 当前环境：27B / 35B-A3B 四轮原始适配门禁复测

执行日期：2026-11-05（UTC）。本次按用户澄清在当前环境测试，Iluvatar 文档仅作记录格式参考，不沿用其机器、容器、参数或结果。本文的结果以本轮原始 JSON 为准；功能门禁不是 NVIDIA 逐 token 精度对照或性能基准。

## 环境与版本

- 主机：`vllm-plugin-fl`，Ubuntu 24.04.3 LTS、Linux 6.8.0-117-generic、x86_64；AMD EPYC 9754，256 个逻辑 CPU。
- 硬件：当前 S60/GCU 环境，`torch.gcu.is_available()` 为 True，8 张可见卡；每卡运行时报告 43,878,711,296 字节总显存。启动前 5、6 号卡各空闲 43,793,776,640 字节，原有服务使用其他卡，未停止。
- 使用系统 Python 3.12.8，无新 venv、无重新安装依赖。PyTorch `2.11.0+cpu`、torch-gcu `2.11.0+3.8.20260713`、vLLM `0.32.0+empty`、FlagGems `5.4.0`；完整包版本见本轮 manifest。
- 测试脚本来源：`/workspace/vllm-plugin-FL`，提交 `547b0abae1fd3ceb74c1c7481c66c57113744b7d`。
- 实际加载的插件：`/workspace/vllm-plugin-FL/vllm_fl`，提交 `547b0abae1fd3ceb74c1c7481c66c57113744b7d`。通过与调度器相同 `PYTHONPATH=/workspace/vllm-plugin-FL` 的新 Python 子进程核对 `find_spec('vllm_fl').origin`，并与运行时异常栈路径交叉确认。系统 editable 安装元数据指向另一工作区 `/workspace/pr675-fix`，但不代表该环境变量下的实际导入来源；本次不能宣称验证了该工作区的 PR675 修复。
- 模型：`/models/Qwen3.6-27B` 为 `Qwen3_5ForConditionalGeneration`；`/models/Qwen3.6-35B-A3B` 为 `Qwen3_5MoeForConditionalGeneration`。使用完整多模态模型，未启用 language-model-only。

## 执行约束

原始 `run_serve_eager.sh`、`run_serve_graph.sh` 和 `run_test.sh` 未修改。原始三个 pytest 文件、8 张 PNG 和质量断言保持不变，测试前后核对 SHA-256。每轮独立目录，不重跑覆盖失败。没有终端录屏，没有单独保存完整服务日志；仅将实际配置、捕获和错误行观察写入 manifest。

五个场景：文本单条 1、文本并发 8、图像单条 1、图像并发 8、混合并发 8。每轮计划 26 请求，四轮计划 104 请求。温度、thinking、生成长度、质量判定均采用原始用例；客户端请求超时 600 秒，服务就绪超时 1800 秒。

## 原始判定标准

`case_utils.py` 对每个响应记录原始 OpenAI 响应、输出文本、延迟和全部 checks。使用 `temperature=0.0`、`enable_thinking=False`；长文本单条最多 512 token、至少 256 字符，并依次检查 large language model / training / inference / limitations，其他请求默认最多 128 token。

质量检查同时要求非空、最小长度、关键词语义和顺序、无 `!!!`、无乱码和非法控制字符、无连续 8 个相同非空白字符、无连续三次重复词或短语。数字英文零到九会归一化为数字。每个场景所有请求的全部 checks 通过才算该场景通过；请求异常保存 error 并判失败。

图像单条使用原图 `image_05.png` 精确 OCR，要求 hello / vllm；图像并发中的同图按原用例询问是否有可见文字，要求 yes，并非同一个 OCR 断言。混合并发是 4 条文本加前 4 张图片。本次没有生成替代图片，也没有把失败检查放宽。

## 实际执行命令

调度器：`python -m py_compile /workspace/run_current_gates.py && python /workspace/run_current_gates.py`，源码随记录归档。每轮在原始用例目录执行，公共环境如下：

```bash
cd /workspace/vllm-plugin-FL/tools/adaptation-gate-cases
export TOPS_VISIBLE_DEVICES=5,6 VLLM_PLUGINS=fl
export FLAGCX_PATH=/workspace/s60-adaptation/flagcx-runtime
export TORCHINDUCTOR_EMULATE_PRECISION_CASTS=1
export PYTHONPATH=/workspace/vllm-plugin-FL
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export LD_LIBRARY_PATH="/usr/local/lib/openmpi:${LD_LIBRARY_PATH:-}"
export TENSOR_PARALLEL_SIZE=2 MAX_MODEL_LEN=32768 PORT=18120
export SERVED_MODEL_NAME=qwen SERVICE_TIMEOUT=1800 REQUEST_TIMEOUT=600
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=7200
export NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1
export PYTEST_ADDOPTS='-p no:cacheprovider'
unset BASE_URL GPU_MEMORY_UTILIZATION GRAPH_COMPILATION_CONFIG
```

结果根目录：`/workspace/adaptation-gate-results/current-20261105T043526Z`。逐轮设置 `MODEL_PATH`、`RESULTS_DIR=<根目录>/<轮次>`、`SERVER_PID_FILE="$RESULTS_DIR/server.pid"`，启动服务后另一个进程执行客户端，完成后仅停止该轮进程组。

| 轮次 | MODEL_PATH | 服务命令 | 客户端命令 |
| --- | --- | --- | --- |
| 27b-eager | `/models/Qwen3.6-27B` | `bash run_serve_eager.sh` | `bash run_test.sh` |
| 27b-graph | `/models/Qwen3.6-27B` | `bash run_serve_graph.sh` | `bash run_test.sh` |
| 35b-a3b-eager | `/models/Qwen3.6-35B-A3B` | `bash run_serve_eager.sh` | `bash run_test.sh` |
| 35b-a3b-graph | `/models/Qwen3.6-35B-A3B` | `bash run_serve_graph.sh` | `bash run_test.sh` |

本地原脚本不读取 `GPU_MEMORY_UTILIZATION` 或 `GRAPH_COMPILATION_CONFIG`，未使用参考文档中的显存 0.70、TP4 或 `mode=0/FULL_DECODE_ONLY`。实际采用原脚本 TP2/32768 和本机默认配置。Eager 观察为 BF16、GCU、enforce_eager=True，编译和 Graph 均关闭；27B Graph 初始化观察为 VLLM_COMPILE、custom_ops=['none']、FULL_AND_PIECEWISE、最大捕获 512。初始化配置不等于捕获成功，最终观察另列。

## 结果与原始证据

执行窗口（UTC）：2026-11-05T04:35:26.736960+00:00 至 2026-11-05T05:10:06.102983+00:00。

| 轮次 | 文本单条 | 文本并发8 | 图像单条 | 图像并发8 | 混合并发8 | 通过场景 | 通过请求 | 客户端退出码 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 27b-eager | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | 5/5 | 26/26 | 0 |
| 27b-graph | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | 5/5 | 26/26 | 0 |
| 35b-a3b-eager | 0/1 | 8/8 | 1/1 | 8/8 | 8/8 | 4/5 | 25/26 | 1 |
| 35b-a3b-graph | 未生成 | 未生成 | 未生成 | 未生成 | 未生成 | 未执行（启动失败） | 未执行 26 | -15 |

共生成 15 份原始 JSON；场景通过 14/15，请求通过 77/78，带 error 的请求 0 条。

### Graph 实际观察

- `27b-graph`：服务启动完成=True，捕获完成观察如下。完整筛选观察保存在 manifest，而非另存完整服务日志。
```text
Capturing CUDA graphs (mixed prefill-decode, PIECEWISE): 100%|██████████| 51/51 [01:00<00:00,  2.64it/s]
Capturing CUDA graphs (mixed prefill-decode, PIECEWISE): 100%|██████████| 51/51 [01:00<00:00,  1.18s/it]
Capturing CUDA graphs (decode, FULL): 100%|██████████| 35/35 [00:32<00:00,  2.65it/s]
Capturing CUDA graphs (decode, FULL): 100%|██████████| 35/35 [00:32<00:00,  1.09it/s]
```

- `35b-a3b-graph`：服务启动完成=False，捕获完成观察如下。完整筛选观察保存在 manifest，而非另存完整服务日志。
```text
```

### 失败与边界

- `35b-a3b-eager/text_single/text-llm-details`：失败检查 `['expected_semantics', 'expected_order']`，错误 `None`；完整原始输出见 JSON。
- 失败细节 `35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/text_single.json/text-llm-details`：未出现的必需字面词 `['limitations']`；finish_reason=`stop`，usage=`{'completion_tokens': 256, 'prompt_tokens': 65, 'total_tokens': 321, 'completion_tokens_details': None, 'prompt_tokens_details': None}`。这是输出与原断言的直接比较，不推断硬件根因。

### 35B-A3B Graph 启动失败（26 请求未执行）

- 服务在就绪前退出 1，没有生成该轮 JSON，也没有观察到 Graph 捕获完成。错误链为 `InductorError / NoTritonConfigs / PTXASError`，涉及 `triton_poi_fused_mul_silu_slice_0`；链接器报告 `tops_truncf_v2_fp32_to_v1_bf16` 的 `R_DTU_ADDR16_LO/HI_ICALL` relocation，提示 `recompile with -fPIC`。这是捕获到的错误，不等同于已定位根因。
- 原始 run_test.sh 的 kill -0 就绪检查仍把僵尸服务视为存活。因此确认服务已退出后，仅 SIGTERM 本轮等待客户端 PID 1552463；客户端退出 -15 是人工结束就绪等待，不是 pytest 失败码。服务退出 1 与客户端干预均保留。没有重跑、补造响应或以 0/0 宣称通过。
- 四轮计划 104 请求，实际执行 78，通过 77，质量检查失败 1，启动失败未执行 26。

- 启动期间有缺少 `vllm._C` 的 warning；当前安装为 EMPTY vLLM，使用 GCU 插件，不能将该 warning 单独记为请求失败。
- Eager 清理后的服务退出码与客户端测试退出码分别记录；SIGINT 停服务的退出码不替代 pytest 结果。
- 本次仅停止自己的 18120 端口服务；原有其他卡和端口服务保留。没有修改测试断言、图片或原始脚本，没有失败后覆盖重跑。
- 没有建立 NVIDIA 参考输出对照；不能把该结果称为精度对齐或吞吐性能验收。

### 可访问原始记录

- [15 份实际生成的原始 JSON 与逐轮索引](../records/s60-adaptation-gates-20261105-current/README.md)
- [环境、退出码、SHA-256 与捕获观察](../records/s60-adaptation-gates-20261105-current/manifest.json)
- [失败索引](../records/s60-adaptation-gates-20261105-current/failures.json)
- [实际四轮调度器源码](../records/s60-adaptation-gates-20261105-current/run_current_gates.py)

原始 JSON 按字节复制并逐份校验 SHA-256；原脚本、用例与图片在测试后全部重新校验，结果记录为 `inputs_unchanged_after_tests=true`。所有记录均来自本轮当前环境，不引用 Iluvatar 机器的旧结果。
