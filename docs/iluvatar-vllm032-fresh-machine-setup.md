# 教程二：官方天数镜像安装 vLLM 0.32，直接做文本问答

更新：2026-11-05。针对当前天数机器。只在宿主执行 Docker 命令，安装和测试都在容器里进行。**不建 venv，不下载教程仓库，不录制终端，不保存日志。输出直接显示，自行截图。**

终端 A 启动服务，终端 B 进入同一个容器执行 curl。所有手工文本问答统一使用问题：**详细介绍下人工智能**。第 5.1 节补充当前容器已执行的 FlagTree 0.7 升级；图文原始门禁的重新测试另见[测试说明](iluvatar-vllm032-flagtree070-retest.md)。

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

### 5.1 升级天数版 FlagTree 至 0.7

2026-11-05 已按用户要求在 `test_plugin_28` 的系统 Python 执行，从 `0.6.2a3+iluvatar3.6` 升级到 `0.7.0+iluvatar3.6`。旧 agent 容器此前已单独升级；容器间不会自动同步。两版的 `triton.__version__` 都是 `3.6.0`，须以 `importlib.metadata.version("flagtree")` 区分发行版本。

先停止该容器中需要使用 FlagTree 的本轮服务；已安装目标版本则无需重复安装。在容器执行，使用 FlagOS 包仓库的天数 Python 3.12 / x86_64 wheel：

```bash
cd /workspace
mkdir -p sources/flagtree-0.7.0-iluvatar
cd sources/flagtree-0.7.0-iluvatar
export FLAGTREE_WHEEL=flagtree-0.7.0+iluvatar3.6-cp312-cp312-linux_x86_64.whl
export FLAGTREE_BASE=https://resource.flagos.net/repository/flagos-pypi-hosted
curl --fail --location --connect-timeout 10 --max-time 300 \
  -o "$FLAGTREE_WHEEL" \
  "$FLAGTREE_BASE/packages/flagtree/0.7.0+iluvatar3.6/$FLAGTREE_WHEEL"
echo "af6a7c9eddf167441fd872c3e6d673e9da572608dee79dba655b0775db740176  $FLAGTREE_WHEEL" \
  | sha256sum --check -
```

确认校验通过，再执行安装和新进程版本核验：

```bash
python -m pip install --no-deps --no-index "$FLAGTREE_WHEEL"
python -c 'from importlib.metadata import version; import triton; print("FlagTree:", version("flagtree")); print("Triton:", triton.__version__, triton.__file__)'
```

应输出 FlagTree `0.7.0+iluvatar3.6`、Triton `3.6.0`。本轮实际安装复用了已在旧 agent 容器下载并核实的同一 wheel，重新核对 SHA-256 后安装；上述下载命令供新机器复现。`--no-deps` 只替换 FlagTree，不重装 CoreX PyTorch、FlagGems、vLLM 或插件。升级前后包清单核对显示仅 FlagTree 版本变化，Torch 文件哈希相同。新进程下 FP32 / FP16 / BF16、长度 1 / 257 / 100003 的最小编译加法共 9 项通过；这只是设备编译检查，模型测试结果单独记录。

当前测试容器的旧安装快照、旧 wheel、前后包清单和回退方法位于 `/workspace/adaptation-gate-upgrade-20261105/` 及 `/workspace/sources/flagtree-0.7.0-iluvatar/`。旧服务不会自动改用新版本，必须重启；本轮复测服务均为升级后的新进程。

#### 为什么升级后 Triton 仍显示 3.6.0

已直接解包核对新旧两个 wheel：它们的 `METADATA` 分别声明 FlagTree `0.6.2a3+iluvatar3.6` 和 `0.7.0+iluvatar3.6`，但各自的 `triton/__init__.py` 都明确写着 `__version__ = '3.6.0'`。FlagTree 是从 Triton 派生的编译器，发行版继续提供 `triton` 导入命名空间；FlagTree 发行号与该模块版本号不同。`flagtree/__init__.py` 还通过 `from triton import __version__` 导出同一值，所以 `flagtree.__version__` 也不能用于查询本次发行号。

本机的 `triton`、`flagtree` 两个导入命名空间均归 `flagtree` 分发包所有，没有独立的 `triton` 分发包。已将安装后的 377 个包文件逐个与 0.7 wheel 比较 SHA-256，全部一致，零缺失、零差异。核心 `triton/_C/libtriton.so` 的哈希已由旧版的 `508b9492…` 改为新版的 `5757e276…`，并与新版 wheel 一致。这证明编译器文件已替换，不只更新了版本标签。完整证据见[安装核验 JSON](../records/u180-flagtree070-gates-20261105/installation-verification.json)及[核验脚本](../records/u180-flagtree070-gates-20261105/verify_installation.py)。

日常检查使用上面的 `importlib.metadata.version("flagtree")`；不要根据 `triton.__version__` 是否改变判断升级成败。模型复测见[0.7 复测记录](iluvatar-vllm032-flagtree070-retest.md)。

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

同日按第 5.1 节将当前容器升级到 FlagTree `0.7.0+iluvatar3.6` 后，重新执行同一四轮原始图文门禁，20/20 场景、104/104 请求通过，两轮 Graph 均完成 35/35 捕获。完整[升级核验、复测步骤与结果](iluvatar-vllm032-flagtree070-retest.md)另页记录，保留旧版失败，不把一次复测通过当作偶发 OCR 根因已证明。
