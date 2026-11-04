# FlagScale-Agent 天数适配：环境建立至 PR/CI 的完整命令与执行审计

归档截止：**2026-11-04T15:52:53.981495+08:00（北京时间）**。主会话：`4761e787`。

本文将实际保存的环境建立、适配、模型测试、诊断、NVIDIA 参考采集、会话恢复、文档和 GitHub/CI 操作整合为一份 Markdown。主会话包含 **7094 条消息、4045 次工具调用、1319 次 shell 调用**；另收录 **446 条 Codex 主助手工具编排**。次数以文末覆盖清单为准。

**阅读方式：**先看第 1–15 节把握执行链，再从第 16 节的阶段表定位逐条命令。所有实际 shell 命令全文保留，不去重、不把失败命令改写成成功命令。脚本创建和修改也保留原始参数，避免只给出 `python script.py` 却缺少脚本内容。

这是一份执行记录，不是可以从第一行到最后一行直接运行的自动安装脚本。历史里包含重复启动、失败安装、旧 PID、删除临时目录、SSH 操作及过期路径；复现时应选择对应阶段，核实前提后执行。凭据替换为 `[REDACTED_...]`，这些位置不能原样用于认证。

## 目录

1. 证据范围、完整性与归档规则
2. 三套环境及路径的区别
3. FlagScale-Agent 本身的安装、配置与启动
4. 从 0.28 旧环境取得 vLLM 0.32 源码
5. 建立天数 EMPTY 隔离环境：逐步操作与踩坑
6. 插件、FlagGems、FlagTree 和 FlagCX
7. 适配修改的先后依赖及验证方法
8. Qwen3-4B：单卡、双卡、eager 与 Graph
9. 27B/35B 图文门禁、服务启动和日志
10. Graph、编译、MoE、视觉与 OCR 诊断
11. NVIDIA A800 参考环境、采集、对比和清理
12. 会话中断、恢复和 agent 自身修复
13. 代码提交、PR #674、CI 与失败修复
14. 11 月 4 日新增操作和当前边界
15. 后续复查、数据读取和复现清单
16. 覆盖统计、分阶段逐条审计、主助手补充、脚本附录

## 1. 证据范围、完整性与归档规则

### 1.1 使用了哪些原始资料

| 资料 | 用途 | 局限 |
|---|---|---|
| `/root/.flagscale/sessions/4761e787/conversation_full.json` | agent 主审计源：所有保存的工具调用及对应返回 | 消息无逐条时间戳；只证明保存的内容 |
| 同会话 `conversation.json`、`plans/` | 当前上下文、活动计划与阶段状态核对 | 上下文会被清理，不能代替 full 历史 |
| Codex 主助手 rollout JSONL | 补充迁移、监控、恢复、清理、代推送 | 与 agent 来源明确区分；时间来自该日志 |
| `/workspace/adapt-logs/` | 服务、测试、采集脚本和原始输出 | 当前脚本可能已被后续修改；日志可能仍在增长 |
| `/workspace/flagscale-agent-monitor/` | 已有执行报告、CI 日志、推送 SHA 核验 | 旧报告只代表各自整理时点 |
| `/workspace/flagscale-agent-migration/` | agent 启动前的安装包、依赖约束、补丁和迁移说明 | 不是“容器从零创建”的完整审计 |
| `/workspace/vllm-plugin-FL/` | 当前适配源码、启动器、CI 脚本 | 与最初运行时文件不一定完全相同 |

原始完整会话含密钥，不上传。归档采用私有快照生成；公开的审计 JSONL 保留所有工具参数和保存结果的脱敏版本，Markdown 中过长结果有明确摘录标记及相同 `record_id`。**命令及写入/修改参数不因篇幅截断。**工具本身曾返回 `[truncated]` 或只读了某个行范围时，无法恢复当时没保存的部分，不伪造缺失输出。

### 1.2 “执行过”不等于“成功”

- `BACKGROUNDED as job...` 只说明作业已交给后台；最终结果要关联后面的 `shell_jobs poll/wait`、日志和产物。
- Guard 拦截表示该次调用未获准继续；后续带说明重试的调用单独保留。
- 没有对应工具返回的调用标为“结果未保存”，不假定它执行成功，也不假定它从未执行。
- 命令以分号串联时，末尾 exit code 不代表之前每个子命令均成功。例如消息 237 中创建 venv 后，错误的 `tools/rust_build.py` 检索使整条命令返回 2，不能据此说 venv 创建失败。
- 真实历史含 `C:\workspace\files\...` 和 DEL 字符等错误路径；原样保留以解释失败，不自动改成一个从未执行过的“正确历史”。修正后的后续调用也保留。
- 完整审计不仅包括 shell，还包括 `write_file`、`edit_file`、`read_file`、后台轮询、计划、记忆、技能和上下文管理。

### 1.3 没有证据的安装步骤

当前任务开始前，容器已有 CoreX、PyTorch、FlagGems、FlagTree、模型权重、部分共享盘目录和 FlagCX 构建产物。主会话没有这些组件最初安装的每一条命令。本文记录检查它们的命令，并给出“复用已有环境”的前提；**不编造驱动安装、镜像拉取、FlagCX 原始编译或模型初次下载的历史命令**。能从迁移说明找到的安装命令归为“说明中的复现步骤”，不冒充当时实际执行。

## 2. 三套环境及路径的区别

### 2.1 核心目录

| 路径 | 身份和用途 |
|---|---|
| `/workspace/flagscale-agent-migration/FlagScale-Agent` | 当前 agent 的可编辑安装源码；运行它的 Python 属于 agent 层 |
| `/root/.flagscale/agent.yaml` | 私密模型接口配置；仅公开脱敏模板 |
| `/root/.flagscale/sessions/4761e787` | agent 对话、计划、swap 等状态 |
| `/workspace/vllm-plugin-FL` | 被适配的推理插件仓库 |
| `/workspace/sources/vllm-0.32.0` | 下载并解压的精确上游源码 |
| `/workspace/builds/vllm-0.32.0` | 用于安装的构建副本 |
| `/workspace/envs/iluvatar-vllm032` | 天数 CoreX、vLLM 0.32 EMPTY 主隔离环境 |
| `/workspace/envs/iluvatar-ci032-check` | 复查 CI 安装脚本的隔离环境 |
| `/workspace/envs/iluvatar-vllm032-diagnostic` | 11 月 4 日新增的依赖诊断环境；与主环境分开 |
| `/mnt/share/user_homes/iluv/FlagCX` | 本容器验证过的 FlagCX 构建根目录 |
| `/mnt/share/user_homes/models` | 当前容器模型根目录 |
| `/workspace/adapt-logs` | 本地服务、测试、诊断和 JSON 证据 |
| `/root/autodl-tmp/precision-small` | 远程 A800 临时参考测试目录，后来按要求删除 |

### 2.2 软件栈不能互相替代

历史主环境记录：Python 3.12，CoreX 4.5，PyTorch 2.10.0 供应商构建，FlagGems 5.3.5，FlagTree 0.6.2a3+iluvatar3.6，vLLM 0.32.0 EMPTY。原全局 Python 曾保留 vLLM 0.28.0+empty。具体导入位置必须用当次命令核对，不能只看终端中的环境名称。

远程 NVIDIA 参考机实际为 **A800-SXM4-80GB**；不是将 NVIDIA 运行环境装到当前 BI-V150 卡上。参考采集结果记录了 PyTorch 2.13.0+cu130、Transformers 5.19.0、原生 vLLM 0.32.0；目标侧当时记录的 Transformers 为 5.14.1。两端依赖不同是结果解释的限制，不能只因为 vLLM 版本号相同就宣称软件栈完全一致。

## 3. FlagScale-Agent 本身的安装、配置与启动

### 3.1 迁移包与安装来源

迁移包目录已有 `BASE_COMMIT.txt`、`flagscale-agent-responses.patch`、`SOURCE_MANIFEST.json`、`constraints-tested.txt` 和 `VALIDATION.txt`。基准提交为 `4dff90ce84a7e8cfaac1af9a83f558baacc28d51`。迁移包验证记录：349 个源码文件与保存副本一致，相关回归 126 passed；这些数字属于 agent 协议迁移快照，不属于 vLLM 模型测试。

迁移说明中的安装路径如下，属于**可复现步骤**；实际主助手执行版本见补充审计：

```bash
cd /workspace
tar -xzf flagscale-agent-migration.tar.gz
cd /workspace/flagscale-agent-migration/FlagScale-Agent
python -m pip install -e .
flagscale-agent --help
```

可编辑安装使运行命令直接加载这份源码，源码目录被移动后要重新安装。原包没有 `.git`，不能把源码目录当成可直接提交的官方 clone。

### 3.2 配置

迁移说明要求将 `openai_api` 设为 `responses`。脱敏配置示意：

```yaml
provider: openai
model: gpt-6.1-sol
api_key: "[REDACTED_CREDENTIAL]"
base_url: https://api.codexzh.com/v1
openai_api: responses
max_iterations: 200
max_continuations: 200
max_context_tokens: 0
max_output_tokens: 8192
thinking_budget: 0
```

这表示使用 OpenAI SDK 的协议适配器，请求实际发往配置中的服务地址；不据此判断服务商支持其他模型。迁移说明也给出从 `OPENAI_API_KEY` 环境变量加载的方式，此时 YAML 里不能残留优先级更高的占位密钥。

```bash
mkdir -p /root/.flagscale
chmod 600 /root/.flagscale/agent.yaml
flagscale-agent --config /root/.flagscale/agent.yaml "只回复 OK"
flagscale-agent --config /root/.flagscale/agent.yaml "使用 shell 工具运行 uname -s，并告诉我输出"
```

上述是配置后的检查步骤，不包含真实密钥。完整迁移说明和配置模板收在文件快照附录。

### 3.3 会话启动与终端保活

历史中实际使用过：

```bash
cd /workspace/vllm-plugin-FL
flagscale-agent --config /root/.flagscale/agent.yaml
```

恢复原会话并让网络断开不直接终止进程的操作：

```bash
tmux new-session -d -s flagscale-agent -c /workspace/vllm-plugin-FL \
  'flagscale-agent --config /root/.flagscale/agent.yaml --auto-resume=4761e787'
tmux attach -t flagscale-agent
```

已存在同名 tmux 时直接 attach；不能为同一会话反复启动并发写入进程。分离终端使用 `Ctrl+b` 后按 `d`。agent 内部的 `/resume`、`/session`、`/reload` 是交互命令，不是 Bash。`/reload` 会保存并重启进程，使源码修复生效。

## 4. 从 0.28 旧环境取得 vLLM 0.32 源码

### 4.1 初始检查

最初检查仓库状态、已有 Iluvatar 文档、`ixsmi`、Python 包、共享盘模型和源码缓存。直接 GitHub、PyPI 和若干镜像下载曾遇 DNS/连接失败；共享盘离线副本为 0.13、0.19 等版本，不能拿它们代替要求的 0.32。

### 4.2 实际下载命令：消息 167

```bash
mkdir -p /workspace/sources && \
curl --fail --location --retry 2 --connect-timeout 10 --max-time 240 \
  --dump-header /workspace/sources/vllm-v0.32.0-download.headers \
  -o /workspace/sources/vllm-v0.32.0.tar.gz.part \
  https://githubproxy.cc/https://github.com/vllm-project/vllm/archive/refs/tags/v0.32.0.tar.gz && \
gzip -t /workspace/sources/vllm-v0.32.0.tar.gz.part && \
mv /workspace/sources/vllm-v0.32.0.tar.gz.part /workspace/sources/vllm-v0.32.0.tar.gz
```

原调用转入 `job12`，后面另有轮询。`.part` 经 gzip 检查后才重命名；HTTP 响应头也被保存。

### 4.3 解压与校验：消息 175、177、188

```bash
tar -xzf /workspace/sources/vllm-v0.32.0.tar.gz -C /workspace/sources
sha256sum /workspace/sources/vllm-v0.32.0.tar.gz
```

实际记录的 SHA256：

```text
bf592c132f27bbb5f65cff0bbd2ee873eae722b79c8286934fd5b5cf88b43d61
```

同时检查 `setup.py`、`pyproject.toml`、`vllm/config/vllm.py` 和版本生成规则。标签压缩包没有普通 clone 的 Git 元数据，构建版本号需要明确的版本变量；不能改包中的字符串来冒充实际源码版本。

## 5. 建立天数 EMPTY 隔离环境：逐步操作与踩坑

### 5.1 创建 venv：消息 237

```bash
python3 -m venv --system-site-packages /workspace/envs/iluvatar-vllm032
```

使用 `--system-site-packages` 是为了继承容器里已可用的 CoreX PyTorch、FlagGems 和 FlagTree。它并不等于完全锁定依赖的独立环境，也会带来继承旧包和全局路径抢先导入的风险。

### 5.2 首次构建与可编辑安装：消息 242

```bash
mkdir -p /workspace/adapt-logs /workspace/builds && \
cp -a /workspace/sources/vllm-0.32.0 /workspace/builds/vllm-0.32.0 && \
VLLM_TARGET_DEVICE=empty SETUPTOOLS_SCM_PRETEND_VERSION=0.32.0 \
  /workspace/envs/iluvatar-vllm032/bin/python -m pip install \
  --no-deps --no-build-isolation -e /workspace/builds/vllm-0.32.0 \
  > /workspace/adapt-logs/empty032-install.log 2>&1
```

原调用为 `job13`。`empty` 避免安装 NVIDIA 的 upstream CUDA 扩展；`--no-deps` 避免 pip 覆盖厂商 torch/Triton；`--no-build-isolation` 使用当前构建工具。构建副本用于隔离对源码归档的修改。

### 5.3 改为普通安装：消息 262

```bash
VLLM_TARGET_DEVICE=empty SETUPTOOLS_SCM_PRETEND_VERSION=0.32.0 \
  /workspace/envs/iluvatar-vllm032/bin/python -m pip install \
  --no-deps --no-build-isolation --force-reinstall /workspace/builds/vllm-0.32.0 \
  > /workspace/adapt-logs/empty032-install-regular.log 2>&1
```

普通安装之后仍出现导入旧全局 vLLM 的情况。排查分别打印 `sys.prefix`、`sys.path`、`find_spec('vllm')`、`PYTHONPATH` 和 `.pth` 文件，确认不能仅靠解释器路径认定导入正确。

### 5.4 导入路径修正：消息 276、278 及后续

```bash
env -u PYTHONPATH /workspace/envs/iluvatar-vllm032/bin/python -c \
  "import vllm; print(vllm.__version__, vllm.__file__)"
```

运行插件源码时，实际形成以下调用前缀：

```bash
env -u PYTHONPATH \
  PYTHONPATH=/workspace/vllm-plugin-FL \
  PATH=/workspace/envs/iluvatar-vllm032/bin:$PATH \
  /workspace/envs/iluvatar-vllm032/bin/python ...
```

这段是从多条历史启动命令中归纳的模式，末尾 `...` 是待替换的程序，不是一条已经运行的完整命令。完整实参见逐条审计。服务 shell 启动器会再调用 `python`，因此它们需要同时固定 `PATH`。

### 5.5 CI 安装验证环境：消息 1250

另创建 `/workspace/envs/iluvatar-ci032-check`，使用 `VLLM_SOURCE_ARCHIVE` 指向已经校验过的本地压缩包，实际调用 `.github/scripts/iluvatar/install_vllm.sh`。该脚本的当前版本以 `VLLM_VERSION_OVERRIDE=0.32.0` 设置版本，与早期手工安装中的 `SETUPTOOLS_SCM_PRETEND_VERSION` 不是同一条历史命令，不能把二者混写。

所有构建、依赖安装、失败检查和后续安装脚本的调用都在阶段 03、04 的完整审计中；当前 `install_vllm.sh` 和 `setup.sh` 全文在附录。

## 6. 插件、FlagGems、FlagTree 和 FlagCX

### 6.1 插件安装：消息 294

```bash
/workspace/envs/iluvatar-vllm032/bin/python -m pip install \
  --no-deps --no-build-isolation /workspace/vllm-plugin-FL \
  > /workspace/adapt-logs/plugin032-install.log 2>&1
```

安装快照随后有源码修改，因此后续实机启动明确给仓库根目录 `PYTHONPATH`，否则可能运行已安装的旧插件副本。文末保留每次导入路径打印结果。

### 6.2 FlagGems-vLLM 接口：消息 546

```bash
env -u PYTHONPATH /workspace/envs/iluvatar-vllm032/bin/python \
  .github/scripts/install_flaggems_vllm.py \
  > /workspace/adapt-logs/install-flaggems-vllm.log 2>&1
```

FlagTree 提供的 Triton 与 standalone Triton distribution 不能混为一谈。记录中同时检查 distribution 版本与 `triton.__file__`，避免包名正确却导入另一份实现。

### 6.3 FlagCX 复用与依赖检查

实际复用路径 `/mnt/share/user_homes/iluv/FlagCX`。历史查到提交短号 `6143384`，且目录中已有 `build/`。主会话不包含该构建根目录最早的 clone/make 命令，不能替它编造安装过程。

双卡通信探针的实际调用（消息 728）：

```bash
env -u PYTHONPATH PYTHONPATH=/workspace/vllm-plugin-FL \
  FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX \
  COREX_VISIBLE_DEVICES=4,5 CUDA_VISIBLE_DEVICES=4,5 \
  /workspace/envs/iluvatar-vllm032/bin/python -m torch.distributed.run \
  --standalone --nproc_per_node=2 /workspace/adapt-logs/probe_flagcx032.py \
  > /workspace/adapt-logs/probe-flagcx032.log 2>&1
```

历史结果记录双卡 AllReduce 的 1024 个元素都为预期值 3。探针成功是通信证据，不等于所有模型的完整 TP/Graph 验收通过。

## 7. 适配修改的先后依赖及验证方法

实际演进大致为：平台初始化/runner 选择 → worker 的 0.32 API → 独立 Iluvatar runner → 缺失扩展和 IR/CachedOp 路径 → FlagCX 与分布式 → zeros 分配 → Graph/编译/MoE → 视觉精度与请求判定 → 安装/CI → 跨平台单测修复。

| 修改范围 | 触发问题 | 验证和记录方式 |
|---|---|---|
| `vllm_fl/__init__.py`、`platform.py` | 0.32 runner 默认值、V2 限制、OOT/EMPTY 扩展假设 | runner selection、配置契约、真实导入 |
| `worker/worker.py` | batch invariant、PP metadata、异步句柄和 routed-expert API 变化 | worker PP 单测、模型启动 |
| `worker/iluvatar_model_runner.py` | 旧 runner 与精确 0.32 不兼容 | 从精确 upstream 迁移、差异 patch、导入与生成 |
| Iluvatar 专用 patches | 缓存懒解析、MoE、视觉和 Graph 生命周期差异 | 算子探针、图捕获、请求级结果与逐层 trace |
| dispatch YAML/算子策略 | 大 backing allocation、视觉 NaN 等实测失败 | zeros/SDPA 探针、黑名单回归 |
| gate 启动/清理/结果脚本 | 串行完整矩阵、显存回收、失败日志 | 启动器测试、真实服务和 JSON |
| CI 安装与 discovery | 旧镜像包抢先导入、平台没被发现 | 精确源码校验、环境断言与 GitHub job 日志 |

为了避免遗漏“改了哪个脚本”和“用什么命令应用改动”，本记录全文保留 `write_file` 的 content、`edit_file` 的 old/new string，以及 shell 中的 patch/Python 修改命令。既有详细技术报告可辅助理解原因，但不替代本文的执行链。

## 8. Qwen3-4B：单卡、双卡、eager 与 Graph

### 8.1 第一次最小生成

`/workspace/adapt-logs/smoke032.py` 使用真实 Qwen3-4B，BF16、TP1、eager、512 上下文、max_num_seqs=1、显存利用率 0.65；提示为 `The capital of France is`，temperature=0、max_tokens=16。它在每次生成前打印 vLLM 版本和导入位置。

早期日志依次暴露 worker API、IR、batch invariant、runner、auxiliary 等兼容问题，故出现多个 `smoke032-...log`。这些命令均保留，不能把最后一次成功当成之前所有尝试成功。

### 8.2 TP/Graph 矩阵

`smoke032_matrix.py` 引入 `--tp`、`--graph` 和 JSON 输出。消息 627 的 TP2 先因 FlagCX/zeros 路径出现问题，后续消息 751、782 使用修复后的路径继续验证。

示例实际调用（消息 751）：

```bash
env -u PYTHONPATH PYTHONPATH=/workspace/vllm-plugin-FL \
  FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX \
  COREX_VISIBLE_DEVICES=4,5 CUDA_VISIBLE_DEVICES=4,5 \
  VLLM_USE_V2_MODEL_RUNNER=0 \
  /workspace/envs/iluvatar-vllm032/bin/python /workspace/adapt-logs/smoke032_matrix.py \
  --tp 2 --output /workspace/adapt-logs/tp2-flagcx-zerosfix.json \
  > /workspace/adapt-logs/tp2-flagcx-zerosfix.log 2>&1
```

Qwen3-4B 是文本模型；这些操作不包含图片输入，不能据此说小模型完成图片精度验证。图片测试发生在后面的多模态模型阶段。

## 9. 27B/35B 图文门禁、服务启动和日志

### 9.1 完整矩阵

两模型为 `Qwen3.6-27B`、`Qwen3.6-35B-A3B`，每个 eager/graph 各一组。每组场景包含：文本单请求 1、文本并发 8、图片单请求 1、图片并发 8、混合并发 8，共 26 请求。完整 2×2 矩阵共 104 请求。检查内容包括非空、长度、关键词顺序、重复、乱码、控制字符及图片内容。

### 9.2 实际启动模式

历史使用设备 8–11、TP4、4096 上下文、0.70 显存利用率和端口 8132 的调用形式（完整具体调用在消息 782 等审计项）如下：

```bash
env -u PYTHONPATH \
  PATH=/workspace/envs/iluvatar-vllm032/bin:$PATH \
  PYTHONPATH=/workspace/vllm-plugin-FL \
  FLAGCX_PATH=/mnt/share/user_homes/iluv/FlagCX \
  COREX_VISIBLE_DEVICES=8,9,10,11 CUDA_VISIBLE_DEVICES=8,9,10,11 \
  VLLM_USE_V2_MODEL_RUNNER=0 \
  MODEL_PATH=/mnt/share/user_homes/models/Qwen3.6-27B \
  PORT=8132 TENSOR_PARALLEL_SIZE=4 MAX_MODEL_LEN=4096 GPU_MEMORY_UTILIZATION=0.70 \
  bash tools/adaptation-gate-cases/run_serve_eager.sh
```

上面的换行整理是便于阅读的等价模式；归档命令保留实际 PID 文件、重定向及其他参数。Graph 另使用 `run_serve_graph.sh` 和相应 `GRAPH_COMPILATION_CONFIG`。服务 ready 之后才由 `run_test.sh` 发请求，ready 不等于验收通过。

### 9.3 历史结果与时点

11 月 2 日报告中的收尾证据：27B FULL Graph 26/26；27B eager 有历史 26/26，但收尾未重跑；35B eager/Graph 各 25/26，图片 OCR 的 `HELLO VLLM` 输出为 `HELLO VLM`。最近可比三组合计 76/78。不能将不同时间、不同配置的结果拼成一次 104/104。

当前 CI runner 模型路径示例是 `/data/models/Qwen/...`；它与当前容器 `/mnt/share/user_homes/models/...` 通过挂载关系对应，不应在没有验证时互相替换。

## 10. Graph、编译、MoE、视觉与 OCR 诊断

### 10.1 为什么启动多次

先后探索了 default/Inductor、custom ops、FULL/PIECEWISE graph、关闭编译但保留 FULL graph、图引用清理及内存策略。历史最终 gate 配置采用：

```json
{"mode":0,"cudagraph_mode":"FULL","custom_ops":["all"],"ir_enable_torch_wrap":false}
```

该配置让 FULL graph 路径继续参与，不能把 `mode=0` 解释为“从未做 Graph”。各次诊断的参数不同，因此必须按对应 log 与 JSON 看结果。

### 10.2 视觉、MoE 和 trace

历史包括视觉 SDPA/NaN、MoE activation/routing、FP32 head 对照、eager/graph 输出、服务 logprob、单步 token、同步/异步 trace 等实验。`compare_ocr_logprobs032.py`、`compare_layer_trace032.py`、`compare_serving_ocr032.py`、`compare_sync_trace032.py` 等脚本的创建和执行均被保留。模型输出差异并不自动证明由版本适配导致，旧版本正常的记录也不自动证明同一个图片样本长期稳定。

### 10.3 范围调整

消息 4810 用户明确要求停止继续排查 35B OCR，将其归因未定并保存证据；后续阶段整理报告、完成 NVIDIA 小模型对照和 CI。11 月 4 日又出现新的依赖/门禁诊断记录，应按后续任务的证据单独列出，不能反过来改写早期“停止排查时尚未归因”的结论。

## 11. NVIDIA A800 参考环境、采集、对比和清理

### 11.1 实际范围

后续要求先只做小模型精度。历史使用远程 A800-SXM4-80GB，测试目录 `/root/autodl-tmp/precision-small`；本地证据回收到 `/workspace/adapt-logs/precision-small-a800/`。远程连接、SFTP 传输和命令通常嵌在 Python/SSH shell 脚本中；完整命令保留，密码已脱敏。

环境建立、模型准备、哈希校验、原生 vLLM 安装和采集所有保存的调用都位于阶段 08。`download_model.sh`、`verify_model.py`、`collect.py`、`compare.py`、`run_reference.sh` 在附录保留当前全文。早期失败的远程安装/传输同样保留，不能只列最终运行命令。

### 11.2 固定输入和推理参数

13 个模型文件完整 SHA256 一致，包含 3 个权重分片、配置和 tokenizer。双端 TP1、BF16、eager、seed=0、temperature=0、top_p=1、max_tokens=32、关闭 prefix cache、512 token budget、max_num_seqs=1、0.65 显存利用率。输入使用相同模板和 `enable_thinking=False`，比较器还校验输入 token IDs。

NVIDIA 原生环境关闭插件：`VLLM_PLUGINS=""`，清理 `PYTHONPATH`；目标侧开启 `VLLM_PLUGINS=fl`、FlagGems、FlagCX。参考端先执行 1 请求/4 token smoke，再执行 7 请求完整采集。

### 11.3 结果复查命令

```bash
cd /workspace/adapt-logs/precision-small-a800
python compare.py --reference nvidia-reference.json --target target.json --output comparison.json
```

实际结果为 4/7 请求生成 token 完全一致，144 个比较位置中 56 个一致，`all_exact=false`。这是自由生成比较，不是 teacher-forced 数值精度验收。比较脚本退出 0 表示报告生成成功，不能代替读取 JSON 的最终判定。

### 11.4 清理

11 月 2 日按用户要求，主助手确认远端无测试进程后删除约 26GB 的远程测试目录；保留本地 JSON、日志和模型清单。未删除远端基础驱动/系统环境，也没有通过云平台释放实例。删除命令与远端检查属于补充审计，不冒充 agent 命令。

## 12. 会话中断、恢复和 agent 自身修复

### 12.1 恢复前检查

观察进程、tmux、已有服务和 PID 文件，先确认同一任务是否仍在运行；不能因为窗口断开就重启模型。原会话可能恢复到上下文维护计划，需要读 `plan_status` 和 full log 找回真实目标。

### 12.2 三类 agent 故障

1. 早期 Responses/Chat Completions 协议与配置覆盖：迁移包做了真实请求格式、工具定义、流式和 reasoning 状态适配。
2. 11 月 3 日，recall 将 JSON 工具文本反序列化成 list/dict；直接作为 Responses 输出发送，报缺少 `input[...].output[0].type`。修复在 API 边界将工具结果序列化为文本，保留源历史。协议回归 39 passed，kernel/context 等 30 passed。
3. 随后恢复历史存在五个未保存返回的工具调用，报 `No tool output found for function call ...`。主助手增加显式未知错误返回，要求先核实副作用再重试；未伪造成功结果。相关 73 项回归通过，并以真实 agent 请求验证恢复。

### 12.3 备份与恢复方式

原会话和修改前源码备份保存在 `/root/.flagscale/recovery-backups/`；这些备份含私密历史，不公开上传。先避免并发写入，再在 agent 中 `/reload`，继续原会话。11 月 3 日 20:55 之后的真实请求、read_file、git status、plan_update 和 memory_write 成功证明当次恢复，而不是仅凭 agent 说“我会继续”。相关命令在主助手补充审计中。

## 13. 代码提交、PR #674、CI 与失败修复

### 13.1 两个仓库用途不同

- 适配代码分支：`luoyc123/vllm-plugin-FL:adapt/iluvatar-vllm032`，PR `flagos-ai/vllm-plugin-FL#674`。
- 本执行文档归档目标：`zz774ever/tianshu`。

向个人 fork 推送不等于 PR 合并；向文档仓库更新不等于把完整模型代码迁到那个仓库。

### 13.2 已有修复链

归档时插件 HEAD：`c17d866e08b583f63998cbd47bc39fe3e57efce0`。历史包含适配提交、unsupported speculative decoding 控制流修复、上游 0.5.0-dev 同步和冲突处理、Iluvatar discovery、精确版本 fixture、FlagCX 前置检查及 A100 跨平台单测修复。每次 git add/commit/push、失败网络重试和 API head 核对均保留。

精确 0.32 的 fixture `decoder_replay_cudagraph_capture_sizes=None` 曾导致 TypeError。改为空列表后目标文件 51 passed，六组相关回归 211 passed、1 warning。不能用当前较新默认环境上的通过去替代精确 0.32 的结果。

### 13.3 CUDA A100 的两项失败

旧提交 `ea978cf...` 上 CUDA unit 为 1970 passed、82 skipped、2 failed：

- `test_iluvatar_runner032.py::test_target_runner_import`：导入类定义时立即求值 `current_platform.torch_device_fn.Stream`，当时 API 为 None。
- `test_iluvatar_zeros_config.py::test_iluvatar_native_zero_dependency_is_excluded`：设置的 `VLLM_FL_DISPATCH_CONFIG` 未被真实加载器读取，NVIDIA 上选中了 NVIDIA YAML。

实际做了“修改前复现 2 failed/4 passed → 修改后相同条件 6 passed”，另外验证逆序和恢复平台状态；相关回归 31 passed、1 既有 skipped。修复提交 `c17d866e08b583f63998cbd47bc39fe3e57efce0` 仅修改两项测试，不新增 skip/xfail，不改变模型生产路径。

### 13.4 网络超时后的实际上传

普通 Git HTTPS 多次超时。主助手使用 GitHub Git Data API 上传与本地完全相同的 blob、tree、commit 对象，逐层核对 SHA，然后用 `force=false` 快进更新个人 fork 分支，再核对 fork、PR、本地 HEAD 一致。不是强推、不是另造内容相似但 SHA 不同的提交，也没有合并 PR。执行过程和原 API 脚本调用属于主助手补充记录。

### 13.5 尚未解除的外部 CI 阻塞

Iluvatar gate 之前因上游 Actions 变量 `ILUVATAR_FLAGCX_PATH` 为空，在模型启动前退出；随后 artifact 目录不存在是连带现象。当前容器里有可用 FlagCX，并不证明 CI runner 的容器挂载里也有同一路径。需维护者提供已验证的容器内根目录、确认 `.so` 与 Python wrapper 和其依赖可加载，再设置变量后重跑。没有用 skip、空库、猜测路径来掩盖失败。

## 14. 11 月 4 日新增操作和当前边界

本次整理时另外发现 agent 仍有新诊断进程，日志在增长。已保存主会话末段包括主环境版本复查、`pip check`、原始要求检索、27B 当前服务启动、Transformers 版本查询和语义门禁规则修改。归档时仓库还有 `tools/adaptation-gate-cases/case_utils.py` 修改和 `tests/unit_tests/test_gate_semantics.py` 未跟踪文件；这些不属于已上传的 `c17d866`。

磁盘上另有 diagnostic venv、依赖 B 服务、prefix trace 和 27B Graph 新日志。附录以当前文件快照列出其脚本，但其原始建立/运行命令若不在截止时保存的 full 历史中，就只说明“磁盘观察到”，不将当前内容冒充未保存的执行历史。正在运行的进程也不因本次归档被停止或重启。

该阶段的完成状态只能按对应最新日志判断，不能复用 11 月 2 日报告直接宣称当前全部验收完成。本文固定截止快照，之后的新命令不自动纳入本版。

## 15. 后续复查、数据读取和复现清单

### 15.1 先看导入来源

以下是从实际排查中归纳的建议检查，**不是新执行的模型测试**：

```bash
env -u PYTHONPATH /workspace/envs/iluvatar-vllm032/bin/python -c \
  'import sys,vllm,torch; print(sys.executable); print(vllm.__version__,vllm.__file__); print(torch.__version__,torch.__file__)'
```

确认 vLLM 为精确 0.32、Torch 为厂商版本后，再决定是否复用当前隔离环境。依赖诊断 venv 与主环境应分别检查，不能只看 PATH 名字。

### 15.2 读取本地证据

```bash
ls -lh /workspace/adapt-logs
cat /workspace/adapt-logs/precision-small-a800/STATUS.md
cat /workspace/adapt-logs/precision-small-a800/comparison.json
cat /workspace/flagscale-agent-monitor/pr674-ci-20261104/push-verification.json
git -C /workspace/vllm-plugin-FL status --short
git -C /workspace/vllm-plugin-FL log -6 --oneline
```

日志和 JSON 中的路径属于执行容器；GitHub 文档不能直接访问它们。本文包含原始命令和脚本，不包含模型权重、数百 MB 的逐层 tensor dump 或完整服务日志。

### 15.3 复现顺序

1. 准备已验证的 CoreX 容器和已存在的厂商依赖，先核对硬件、版本和共享盘挂载。
2. 校验精确源码归档，创建继承厂商依赖的隔离 venv，按对应安装阶段构建 EMPTY。
3. 安装插件及 FlagGems-vLLM 接口，排除 PYTHONPATH 抢先导入旧环境。
4. 用真实 FlagCX 路径做依赖和通信检查；跨机器路径必须单独验证。
5. 先导入/单元和 Qwen3-4B TP1，再按需求扩展 TP/Graph 或多模态门禁。
6. 分别保存每组 server log、test log、JSON、配置、版本、源码提交和权重校验。
7. 阅读失败样本，区分启动失败、判据失败、数值差异和语义差异；不以服务 ready 代替测试通过。
8. 对照原始用户范围决定是否继续大模型/图片/性能实验；此处顺序是复现建议，不授权新的测试任务。
9. 提交前看 diff 和相关检查，推送后核对远端 SHA，再单独观察新 CI，避免拿旧 head 的绿勾作新提交证据。

### 15.4 如何查单条命令

全文搜索日志名、脚本名、`pip install`、`-m venv`、`FLAGCX_PATH`、`ssh`、`git commit` 或 job_id。每条对应一个稳定 `record_id`，如 `agent-m242-c1`；同一编号在脱敏 JSONL 中有完整保存结果，可供程序进一步查询。原始消息索引从 0 开始，不是终端时间戳。

由于逐条保留命令和脚本，此文件可能超过 GitHub 网页的 Markdown 渲染限制。可以通过 GitHub 的 Raw/Download 下载整份 `.md`，在本地编辑器打开；不能把网页只展示前一部分误认为归档不完整。仓库另有覆盖清单供核对数量与 SHA256。


## 完整逐条审计下载

- [完整单份 Markdown（含每条命令和脚本）](flagscale-agent-complete-command-history.md)；文件较大，使用 Raw/Download 下载后打开。
- [归档、覆盖清单与完整脱敏结果](../records/flagscale-agent-command-history-20261104/README.md)。
