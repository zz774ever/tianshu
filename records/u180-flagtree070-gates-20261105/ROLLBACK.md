# FlagTree 0.7 升级与回退

用户于2026-11-05明确授权将test_plugin_28升级为FlagTree0.7，更新教程并重新跑四轮原始图文门禁。此前0.6.2的104条原始请求及其失败记录不覆盖。

升级前为0.6.2a3+iluvatar3.6，目标为官方天数构建0.7.0+iluvatar3.6。两个发行版的Triton运行时均显示3.6.0。新wheel来自旧agent容器已验证的FlagOS官方包仓库产物，SHA256：af6a7c9eddf167441fd872c3e6d673e9da572608dee79dba655b0775db740176。

仅停止本次Codex启动的独立agent会话866a5589和其8132服务。其他容器和其他用户任务不动。原先agent容器的0.7升级记录独立保留。

升级前包版本及Torch哈希为before.json；完整旧triton、flagtree及dist-info备份为flagtree-before-0.7.0.tar。旧wheel SHA256：d69473c21763d1c573da2e0f0548fbac006a86d3810f7edecbf55eb5f4908ba2。

需要回退时，先停止本容器使用相关软件的服务，再在容器执行：

```bash
python -m pip install --no-deps --no-index --force-reinstall \
  /workspace/sources/flagtree-0.7.0-iluvatar/flagtree-0.6.2a3+iluvatar3.6-cp312-cp312-linux_x86_64.whl
python -c 'from importlib.metadata import version; print(version("flagtree"))'
```

本次仅记录回退方法，不执行回退；实际复测使用升级后的新进程。
