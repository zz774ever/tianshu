# S60 当前环境四轮原始门禁复测

本轮使用本机真实环境，不沿用 Iluvatar 参考文档的机器、卡数或结果。

执行窗口（UTC）：2026-11-05T04:35:26.736960+00:00 至 2026-11-05T05:10:06.102983+00:00。

| 模型/模式 | 文本单条 | 文本并发8 | 图像单条 | 图像并发8 | 混合并发8 | 通过场景 | 通过请求 | 退出码 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 27b-eager | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | 5/5 | 26/26 | 0 |
| 27b-graph | 1/1 | 8/8 | 1/1 | 8/8 | 8/8 | 5/5 | 26/26 | 0 |
| 35b-a3b-eager | 0/1 | 8/8 | 1/1 | 8/8 | 8/8 | 4/5 | 25/26 | 1 |
| 35b-a3b-graph | 未生成 | 未生成 | 未生成 | 未生成 | 未生成 | 未执行（启动失败） | 未执行 26 | -15 |

总计：`{"scenarios": 15, "passed_scenarios": 14, "requests": 78, "passed_requests": 77, "errors": 0}`。

原始 JSON 按字节复制；manifest.json 包含逐文件 SHA-256、原脚本/图片哈希、版本、实际环境、退出码及启动/捕获观察；failures.json 仅为失败索引，不替代原始响应。没有保存独立完整服务日志或终端录像。

完整命令与环境：[复测报告](../../docs/s60-adaptation-gates-20261105-current.md)。

## 原始 JSON 文件

- [27b-eager/Qwen3.6-27B/port-18120/text_single.json](27b-eager/Qwen3.6-27B/port-18120/text_single.json) · SHA-256 `7dcb671e30f0b401854e7d8a23f9a2a3d0235cb858e99bead5955f0110d87771`
- [27b-eager/Qwen3.6-27B/port-18120/text_concurrent_8.json](27b-eager/Qwen3.6-27B/port-18120/text_concurrent_8.json) · SHA-256 `1a489a119fdf4be8a2853cbbf74bf23f666b29ad84e600bbba84af0f833eec0c`
- [27b-eager/Qwen3.6-27B/port-18120/image_single.json](27b-eager/Qwen3.6-27B/port-18120/image_single.json) · SHA-256 `d78e772d21e0819b08580dd3d8a0338caa980e828b72d6448270dcdb46aa86e5`
- [27b-eager/Qwen3.6-27B/port-18120/image_concurrent_8.json](27b-eager/Qwen3.6-27B/port-18120/image_concurrent_8.json) · SHA-256 `90845f8bc60256361ccc7d0478d57baaee96803f85e6417415a762c660b70846`
- [27b-eager/Qwen3.6-27B/port-18120/mixed_concurrent_8.json](27b-eager/Qwen3.6-27B/port-18120/mixed_concurrent_8.json) · SHA-256 `21f6b7aa74002ba925b8ae378f8cd62afe69a5b5f0bf68c9f3ec0c647db49507`
- [27b-graph/Qwen3.6-27B/port-18120/text_single.json](27b-graph/Qwen3.6-27B/port-18120/text_single.json) · SHA-256 `295b7052d3f8981e1606df7deb73f08d59016bc49f29e3e229a77a9031b54ef7`
- [27b-graph/Qwen3.6-27B/port-18120/text_concurrent_8.json](27b-graph/Qwen3.6-27B/port-18120/text_concurrent_8.json) · SHA-256 `3805bac32a7c320a31c247737d1793b6ecc2db1f2531445fe9cda6d1bda63a95`
- [27b-graph/Qwen3.6-27B/port-18120/image_single.json](27b-graph/Qwen3.6-27B/port-18120/image_single.json) · SHA-256 `863935872e2587a1c7296cfcf3f08feaadb9035cc9c20640af4daa470baa5f31`
- [27b-graph/Qwen3.6-27B/port-18120/image_concurrent_8.json](27b-graph/Qwen3.6-27B/port-18120/image_concurrent_8.json) · SHA-256 `1c4533ce841e80703740e5e5f7b3e99bad84b68812477f34cda124177f98691c`
- [27b-graph/Qwen3.6-27B/port-18120/mixed_concurrent_8.json](27b-graph/Qwen3.6-27B/port-18120/mixed_concurrent_8.json) · SHA-256 `4bcf91d3605c6196c805b920110ebb9b3178b742eeb4bf84f9d54365a06f14e6`
- [35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/text_single.json](35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/text_single.json) · SHA-256 `390e00fc10f9ccee3720e8d15a77909399aabd66fede19ff51a8b96a19ff73f7`
- [35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/text_concurrent_8.json](35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/text_concurrent_8.json) · SHA-256 `77868eadb19fbfd3d98605405a8890e5c4c86e7d5aa5c2ee7ad4052607f3f936`
- [35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/image_single.json](35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/image_single.json) · SHA-256 `4514727cbb17b0d6523626337c56d8d27072618351539952c102cb2bc89de00f`
- [35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/image_concurrent_8.json](35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/image_concurrent_8.json) · SHA-256 `fd74731d7b54a6cf2e834cac761cd8ce786053f6e24508c4ce5e3ee07abd648d`
- [35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/mixed_concurrent_8.json](35b-a3b-eager/Qwen3.6-35B-A3B/port-18120/mixed_concurrent_8.json) · SHA-256 `bb3e420b48eff3fa2c8688d87857c9f7307492d52a928157ab837f634b7c9062`
