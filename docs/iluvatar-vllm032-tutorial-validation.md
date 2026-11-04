# 本机纯文本教程实测记录

日期：2026-11-04。执行容器：testtianshuzdh。所有本轮命令都在容器内；没有修改宿主软件、其他任务、共享模型或适配源码。

本轮只做文本，不发送图片或运行图文门禁。沿用现有venv、厂商组件和模型，未重新拉镜像、新建容器、编译FlagCX或重新安装FlagGems/vLLM；这些新机步骤不能算本轮端到端实测。

## 执行结果

| 检查 | 实际结果 |
|---|---|
| 环境、CLI来源、GPU加法和NumPy桥接 | PASS；两张BI-V150，venv来源正确 |
| 双卡FlagCX | 两rank均为[3,3,3,3]，static/127.0.0.1命令退出0 |
| TP1 eager文本 | 非空生成，退出0 |
| TP2 eager文本 | 非空生成，退出0 |
| TP2 FULL graph文本 | 非空生成，退出0；捕获日志见下文 |
| 文本API与流式传输 | transport_passed=True，quality_passed=False；两项分开记录 |
| pip check | 退出1，继承镜像与vLLM声明存在依赖冲突，原始输出保留 |
| 故意退出7的记录器检查 | 正确保存exit_code=7及输出；外层验证通过 |

## 实测发现及修正

- 原--standalone探针因容器hostname无法解析反复重试，终止了仅属于本次的启动器，退出-15原样保留。改为单机static rendezvous、127.0.0.1及空闲端口后成功。
- torch runtime版本为2.10.0，distribution为2.10.0+corex.4.5.0，版本断言已区分。
- 驱动用户态目录补libixthunk；没有执行驱动安装。
- pytest使用venv入口；分布式启动使用python -m，避免全局Python。
- VLLM_ENGINE_ITERATION_TIMEOUT_S、VLLM_RPC_TIMEOUT在0.32不再识别，激活脚本清除这两项旧变量，保留实际支持的VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS。早期日志有旧警告，原样保留。

## 生成内容原样展示

离线smoke只检查非空，不能以其PASS声称知识或数学正确。下列为实际生成：

### tp1-eager

输入：`The capital of France is`

```text
 not Paris. What is it? Also, why is the capital of France not
```

输入：`The speed of light in vacuum is approximately`

```text
 3.00 × 10^8 m/s. What is
```

### tp2-eager

输入：`The capital of France is`

```text
 Paris. The capital of Germany is Berlin. The capital of Italy is Rome.
```

输入：`The speed of light in vacuum is approximately`

```text
 3.00 × 10^8 m/s. What is
```

### tp2-full-graph

输入：`The capital of France is`

```text
 Paris. The capital of Germany is Berlin. The capital of the United Kingdom is
```

输入：`The speed of light in vacuum is approximately`

```text
 3.00 x 10^8 m/s. The speed
```

## 文本API问答检查

| 问题 | 预期 | 实际 | 内容检查 |
|---|---|---|---|
| What is 17 + 25? Answer only with the number. | 42 | 52 | False |
| What is the capital of France? Answer only the city name. | paris | Paris. | True |

## Graph捕获证据

```text
Capturing CUDA graphs (mixed prefill-decode, FULL):   0%|          | 0/3 [00:00<?, ?it/s]/usr/local/lib/python3.12/site-packages/flag_gems/utils/libentry.py:411: RuntimeWarning: active Triton backend does not provide a replay benchmarker; falling back to event timing
Capturing CUDA graphs (mixed prefill-decode, FULL):  33%|███▎      | 1/3 [00:04<00:09,  4.61s/it]/usr/local/lib/python3.12/site-packages/flag_gems/utils/libentry.py:411: RuntimeWarning: active Triton backend does not provide a replay benchmarker; falling back to event timing
Capturing CUDA graphs (mixed prefill-decode, FULL):  67%|██████▋   | 2/3 [00:04<00:02,  2.10s/it]/usr/local/lib/python3.12/site-packages/flag_gems/utils/libentry.py:411: RuntimeWarning: active Triton backend does not provide a replay benchmarker; falling back to event timing
Capturing CUDA graphs (mixed prefill-decode, FULL): 100%|██████████| 3/3 [00:06<00:00,  1.85s/it]
Capturing CUDA graphs (mixed prefill-decode, FULL): 100%|██████████| 3/3 [00:06<00:00,  2.17s/it]
```

## 原始证据与可复查范围

- [结构化汇总及脚本SHA256](../records/u180-tutorial-20261104/summary.json)
- [逐步命令、stdout/stderr和退出码](../records/u180-tutorial-20261104/steps/)
- [文本生成JSON和token IDs](../records/u180-tutorial-20261104/smoke/)
- [文本API服务日志与完整请求/响应](../records/u180-tutorial-20261104/text-api/)
- [Python环境指纹](../records/u180-tutorial-20261104/python-packages.json)

Bash代码块和脚本通过bash -n，Python代码块及脚本通过compile检查，git diff --check通过。本轮没有Ruff，未将其计为已通过。

新机从零安装、FlagTree重编、FlagCX现场编译、上游全部pip依赖满足、模型语义全正确、NVIDIA逐token精度和性能均不在本轮通过范围。此前完整图文矩阵80/104是另一轮历史记录，不混入本轮文本统计。
