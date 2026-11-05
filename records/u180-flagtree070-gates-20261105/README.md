# u180：FlagTree 0.7 原始图文门禁复测证据

执行容器 `test_plugin_28`，日期 2026-11-05。完整步骤、环境、结果和限制见[复测说明](../../docs/iluvatar-vllm032-flagtree070-retest.md)，升级命令见[环境教程](../../docs/iluvatar-vllm032-fresh-machine-setup.md#51-升级天数版-flagtree-至-07)。原始 0.6.2 的失败结果继续保留在[独立目录](../u180-adaptation-gates-20261105/README.md)。

## 原始测试 JSON

每行对应同一轮原始 `run_test.sh` 生成的五份文件，按字节复制，不修改输入、响应或通过状态。

四轮各 5/5 场景、26/26 请求通过，共 20/20 场景、104/104 请求；文本 52/52、图像 52/52，全部 `finish_reason=stop`。两轮 Graph 均在终端确认捕获 35/35。请求阶段没有异常或超时；启动及主动停服诊断另见观察文件。

| 轮次 | 文本单条 | 文本并发 8 | 图像单条 OCR | 图像并发 8 | 图文混合并发 8 |
| --- | --- | --- | --- | --- | --- |
| 27B eager | [JSON](results/Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/text_single.json) | [JSON](results/Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/text_concurrent_8.json) | [JSON](results/Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/image_single.json) | [JSON](results/Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/image_concurrent_8.json) | [JSON](results/Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/mixed_concurrent_8.json) |
| 27B Graph | [JSON](results/Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/text_single.json) | [JSON](results/Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/text_concurrent_8.json) | [JSON](results/Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/image_single.json) | [JSON](results/Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/image_concurrent_8.json) | [JSON](results/Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/mixed_concurrent_8.json) |
| 35B-A3B eager | [JSON](results/Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/text_single.json) | [JSON](results/Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/text_concurrent_8.json) | [JSON](results/Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/image_single.json) | [JSON](results/Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/image_concurrent_8.json) | [JSON](results/Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/mixed_concurrent_8.json) |
| 35B-A3B Graph | [JSON](results/Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/text_single.json) | [JSON](results/Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/text_concurrent_8.json) | [JSON](results/Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/image_single.json) | [JSON](results/Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/image_concurrent_8.json) | [JSON](results/Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/mixed_concurrent_8.json) |

## 版本与执行证据

- [before.json](before.json) / [after.json](after.json)：升级前后包版本与 Torch 文件哈希。
- [installation-verification.json](installation-verification.json)：两个 wheel 的真实版本字段、核心库哈希，以及新版安装文件逐项比对；[核验脚本](verify_installation.py)。
- [device-verification.json](device-verification.json)：独立新缓存下 9/9 设备编译检查；[设备脚本](verify_device.py)。
- [matrix.json](matrix.json)：逐轮起止时间、退出码和场景结果；[执行驱动](run_matrix.py)。
- [terminal-observations.json](terminal-observations.json)：Graph 捕获、TLE 编译诊断、停服提示和运行中编译库核对。这是终端观察记录，没有单独保存完整服务日志。
- [cleanup-verification.json](cleanup-verification.json)：端口释放与本轮 GPU 显存检查。
- [manifest.json](manifest.json)：原始结果与证据文件 SHA-256、请求汇总、原测试脚本及图片哈希、源码提交和结束时状态；[汇总脚本](summarize.py)。
- [fingerprint.py](fingerprint.py)：包版本和 Torch 哈希采集；[ROLLBACK.md](ROLLBACK.md)：旧版回退办法，本轮未执行回退。

原始路径为 `/workspace/adaptation-gate-upgrade-20261105/`。未上传 wheel、旧版完整安装备份 tar、编译缓存或 agent 私有配置。归档的执行脚本固定了本轮目录，直接重复执行会因目录已存在而拒绝覆盖；再次测试请按教程设置新的 `RESULTS_DIR`。功能门禁和最小编译检查不能代替完整精度或稳定性评估。
