# 教程二：官方天数镜像安装 vLLM 0.32，直接做文本问答

更新：2026-11-04。针对当前天数机器。只在宿主执行 Docker 命令，安装和测试都在容器里进行。**不建 venv，不下载教程仓库，不录制终端，不保存日志。输出直接显示，自行截图。**

终端 A 启动服务，终端 B 进入同一个容器执行 curl。所有文本问答统一使用问题：**详细介绍下人工智能**。本次仅修改指令并检查语法，不重新运行模型，下面步骤由你手动执行。

## 1. 拉取官方镜像、创建容器

在宿主执行：

```bash
docker pull harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-iluvatar-ci

docker run --shm-size=32g -itd \
  -v /dev:/dev \
  -v /mnt/share/user_homes/:/mnt/share/user_homes/:ro \
  --mount type=bind,src=/usr/local/corex-4.5.0.20260509/lib64/libcuda.so.1,dst=/usr/local/corex/lib64/libcuda.so.1,readonly \
  --mount type=bind,src=/usr/local/corex-4.5.0.20260509/lib64/libixml.so,dst=/usr/local/corex/lib64/libixml.so,readonly \
  --privileged --net=host \
  --name test_plugin_28 \
  --entrypoint /bin/bash \
  harbor.baai.ac.cn/plugin/vllm-plugin-fl:v0.28.0-iluvatar-ci

docker exec -it test_plugin_28 bash
```

这是 [FlagOS 官方插件项目文档](https://github.com/flagos-ai/vllm-plugin-FL/blob/0.5.0-dev/docs/usage/iluvatar.md)使用的镜像。两条驱动库只读挂载使用本机实际路径，不安装或更换宿主驱动。共享模型也只读挂载。不需要 `--pid=host`、`--cap-add=ALL` 或编译内核模块的挂载。

容器名称已存在时直接进入它；已经升级过的容器不能再作为原始 0.28 环境。

## 2. 查看容器原始环境

下面开始全部在容器内执行：

```bash
cd /workspace
python --version
python -m pip show vllm vllm-plugin-fl torch flagtree flag-gems numpy openai
ldd /usr/local/corex/lib64/libcuda.so.1
```

本次升级前实际版本：Python 3.12.11、vLLM 0.28.0+empty、插件 0.3.0rc0+g13eb9be69、CoreX PyTorch 2.10.0+corex.4.5.0、FlagTree 0.6.2a3+iluvatar3.6、FlagGems 5.3.5、NumPy 1.26.4。截图你这次的真实输出即可。

**只有明确提示 `libixthunk.so => not found` 时**，执行下面的容器内依赖补齐；没有缺库就跳过：

```bash
bash /mnt/share/user_homes/yubenjie/0509/corex-driver-linux64-4.5.0.20260509_x86_64.run \
  --noexec --target /workspace/driver-extracted
export LD_LIBRARY_PATH="/workspace/driver-extracted/corex/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

`--noexec` 只解包、不执行驱动安装器。这是本机挂载库的依赖搜索问题，不要求更新宿主驱动。目录已解包时只执行 export；以后新开容器终端需要这套库时，也执行该 export。

## 3. 原始环境基础验证：终端 A

先查看卡占用情况：

```bash
ixsmi
```

本轮实际用过 0、1、2、3 卡，执行前确认仍空闲，或改成你选定的空闲卡。本机模型在 `/mnt/share/user_homes/models/`，不是旧参考中的 zyp 目录。

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3
export VLLM_ENGINE_ITERATION_TIMEOUT_S=72000
export VLLM_RPC_TIMEOUT=72000000
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=7200

vllm serve /mnt/share/user_homes/models/Qwen3-4B/ \
  --served-model-name qwen --enforce-eager --port 8070 --max-model-len 32768
```

这条 4B 命令默认 TP1；可见四张卡不等于 TP4。服务启动完成后才去终端 B 发请求。

此前原始 0.28 环境启动报 `fused_moe` 没有 `FusedMoE` 属性，是镜像内旧插件与旧 vLLM 的接口不匹配。遇到同样错误就截图，基线记为失败，再进入第 5 节升级；接口未启动时 curl 也不会成功。

## 4. 文本问答：终端 B

在另一个宿主终端进入**同一个容器**：

```bash
docker exec -it test_plugin_28 bash
```

然后在容器终端 B 执行：

```bash
curl --noproxy '*' --fail-with-body -sS --max-time 300 \
  http://localhost:8070/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "详细介绍下人工智能"}],
    "temperature": 1.0,
    "max_tokens": 256,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
```

回答在返回 JSON 的 `choices[0].message.content` 中。请求不流式输出，要等生成完成后才显示；大模型 eager 生成 256 token 可能需要几分钟。连接失败先看终端 A 是否启动成功。

后面的 4B、27B、35B 都在服务就绪后执行这一条 curl，不换问题或 model 名称。每组测试完成，在终端 A Ctrl+C 停止当前服务，再安装或启动下一组。端口 8070 必须空闲，不停止其他人的服务。

## 5. 容器内直接升级 vLLM / vllm-plugin-FL

在终端 A 执行，不激活任何 venv。每条安装命令成功后再继续，失败就停下看错误。

```bash
cd /workspace
git clone --depth 1 --branch v0.32.0 \
  https://gh-proxy.org/https://github.com/vllm-project/vllm.git
cd /workspace/vllm
python -m pip install --no-deps 'wheel==0.48.0'
VLLM_TARGET_DEVICE=empty VLLM_VERSION_OVERRIDE=0.32.0 \
  python -m pip install -v --no-build-isolation --no-deps -e .

cd /workspace
git clone --branch 0.5.0-dev \
  https://gh-proxy.com/https://github.com/flagos-ai/vllm-plugin-FL.git
cd /workspace/vllm-plugin-FL
git fetch origin refs/pull/674/head
git checkout --detach FETCH_HEAD
python -m pip install --no-build-isolation --no-deps -e .
```

已有源码目录时不要重复 clone。fetch/checkout 直接检出 PR 674，避免 pull 产生合并。两处 `--no-deps` 保留镜像的 CoreX PyTorch 和天数 FlagTree，避免安装普通 CUDA 包。

安装 PR 配套的辅助算子，原始镜像没有这个包，不能省略：

```bash
git config --global \
  url.https://gh-proxy.org/https://github.com/.insteadOf https://github.com/
python /workspace/vllm-plugin-FL/.github/scripts/install_flaggems_vllm.py
hash -r
```

Git 设置只写入容器。helper 下载并核对固定提交。此前验证的 PR 674 提交是 `c17d866e08b583f63998cbd47bc39fe3e57efce0`；PR 后续更新需重新验证。

## 6. 新环境运行设置

终端 A 执行：

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3
export VLLM_PLUGINS=fl
export USE_FLAGGEMS=1
export GEMS_VENDOR=iluvatar
export FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX
export LD_LIBRARY_PATH="/workspace/driver-extracted/corex/lib64:$FLAGCX_PATH/build/lib:/usr/local/corex/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export VLLM_ENGINE_ITERATION_TIMEOUT_S=72000
export VLLM_RPC_TIMEOUT=72000000
export VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=7200

python -c 'import vllm; print(vllm.__version__, vllm.__file__)'
```

应导入 0.32.0。FlagCX 使用本机已有的通信库，后面的 TP4 依赖它。第 2 节解包得到的目录必须保持在库搜索路径最前面：当前镜像与驱动包中的 `libcudart.so.10.2.89` 文件名相同、内容不同，将 `/usr/local/corex/lib64` 放在解包目录前会使最小 Graph 测试在 `capture_begin()` 报 `ixErrorNotSupported`。运行 Graph 前必须完成第 2 节的解包，即使 `ldd` 没有提示缺库。新开终端 A 时重新执行本节设置；终端 B 仅执行 curl。

## 7. 新环境 4B 验证

终端 A：

```bash
vllm serve /mnt/share/user_homes/models/Qwen3-4B/ \
  --served-model-name qwen --enforce-eager --port 8070 --max-model-len 32768
```

启动完成后，终端 B 执行第 4 节的 curl，查看“详细介绍下人工智能”的回答。

## 8. 27B 文本测试

终端 A 先 Ctrl+C 停止 4B，确认显存释放，再启动 27B：

```bash
vllm serve /mnt/share/user_homes/models/Qwen3.6-27B/ \
  -tp 4 --served-model-name qwen --port 8070 \
  --dtype bfloat16 --language-model-only --enforce-eager \
  --max-model-len 4096 --max-num-seqs 4 --max-num-batched-tokens 512 \
  --gpu-memory-utilization 0.70
```

服务启动完成后，终端 B 仍执行第 4 节同一条 curl。

## 9. 35B-A3B 文本测试

终端 A 先 Ctrl+C 停止 27B，确认显存释放，再启动 35B：

```bash
vllm serve /mnt/share/user_homes/models/Qwen3.6-35B-A3B/ \
  -tp 4 --served-model-name qwen --port 8070 \
  --dtype bfloat16 --language-model-only --enforce-eager \
  --max-model-len 4096 --max-num-seqs 4 --max-num-batched-tokens 512 \
  --gpu-memory-utilization 0.70
```

服务启动完成后，终端 B 仍执行第 4 节同一条 curl。测完在终端 A Ctrl+C 停止服务。

大模型先使用此前本机验证过的 4096 上下文和显存预算；你的 32768 配置尚未按本轮参数验证。`--language-model-only` 用于纯文本。四张卡都要空闲，35B-A3B 权重也不能按 3B 估算显存。

此前 4B、27B、35B eager 的[实际验证记录](../records/u180-direct-install-20261104/README.md)继续保留。历史实测使用端口 8060 和默认 temperature；本页按你的示例改成 8070 和 temperature=1.0，仅检查指令语法，没有重跑，不把调整后的组合写成已实测。

2026-11-05 新增[27B / 35B-A3B 原始图文适配测试步骤与结果](iluvatar-vllm032-adaptation-gate-test.md)：使用 TP4、32768 上下文和完整多模态模型，分别运行 eager 与 FULL_DECODE_ONLY。共 104 条请求，文本全部通过，图片存在失败，详细结果和原始 JSON 独立记录。
