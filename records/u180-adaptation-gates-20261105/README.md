# u180 图文适配门禁原始结果

日期：2026-11-05。执行容器：`test_plugin_28`。[测试环境、完整步骤和结果说明](../../docs/iluvatar-vllm032-adaptation-gate-test.md)。原始结果位于执行容器 `/workspace/adaptation-gate-results/20261105-112054`，本目录保存 20 份原始 JSON 的字节副本。

使用 `/workspace/vllm-plugin-FL/tools/adaptation-gate-cases` 的原始服务和客户端脚本。没有改题目、图片、断言或生成长度。TP4，GPU 0–3，32768 上下文，显存预算 0.70，端口 8132；Graph 配置为 `{"mode":0,"cudagraph_mode":"FULL_DECODE_ONLY"}`。请求超时 600 秒，服务就绪超时 1800 秒。

## 结果

| 模型 / 模式 | 通过场景 | 通过请求 | 结论 |
| --- | ---: | ---: | --- |
| 27B eager | 2/5 | 13/26 | 13 条图片全部未通过 |
| 27B Graph | 3/5 | 17/26 | 9 条图片未通过 |
| 35B-A3B eager | 5/5 | 26/26 | 全部通过 |
| 35B-A3B Graph | 4/5 | 25/26 | 单图 OCR 将 VLLM 识别为 VLIM |

总计 14/20 场景、81/104 请求通过。52 条文本全部通过；52 条图片通过 29 条。所有请求正常返回，finish_reason 全为 stop；失败均为回答质量检查未通过。两轮 Graph 均完成 35/35 捕获。没有修改断言或覆盖失败结果。

## 20 份原始 JSON

每份 JSON 包含输入、原始 API 响应、耗时、逐条检查和汇总。[manifest.json](manifest.json) 保存来源提交、原测试脚本和图片哈希、20 份报告哈希及汇总计数。

| 模型 / 模式 | 文本单条 | 文本并发 8 | 图像单条 | 图像并发 8 | 图文混合 8 |
| --- | --- | --- | --- | --- | --- |
| 27B eager | [JSON](Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/text_single.json) | [JSON](Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/text_concurrent_8.json) | [JSON](Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/image_single.json) | [JSON](Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/image_concurrent_8.json) | [JSON](Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/mixed_concurrent_8.json) |
| 27B Graph | [JSON](Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/text_single.json) | [JSON](Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/text_concurrent_8.json) | [JSON](Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/image_single.json) | [JSON](Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/image_concurrent_8.json) | [JSON](Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/mixed_concurrent_8.json) |
| 35B-A3B eager | [JSON](Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/text_single.json) | [JSON](Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/text_concurrent_8.json) | [JSON](Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/image_single.json) | [JSON](Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/image_concurrent_8.json) | [JSON](Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/mixed_concurrent_8.json) |
| 35B-A3B Graph | [JSON](Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/text_single.json) | [JSON](Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/text_concurrent_8.json) | [JSON](Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/image_single.json) | [JSON](Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/image_concurrent_8.json) | [JSON](Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/mixed_concurrent_8.json) |

本轮没有录制终端，也没有单独保存 server.log / tests.log。Graph 捕获情况来自执行时终端观察，JSON 记录请求及质量检查。本轮只反映上述配置的一次门禁结果，不是完整精度或性能评测。
