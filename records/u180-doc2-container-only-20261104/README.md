# 教程二容器内复现流程修订记录

日期：2026-11-04。执行位置：已有 `testtianshuzdh` 容器。此次没有执行宿主安装、建目录、拉镜像或创建新容器。

## 修改内容

- 教程二只保留宿主 Docker pull/run/exec；其余命令在新容器执行。
- 去掉宿主工作目录及教程仓库下载；必需测试代码直接写入文档。
- 本机模型、FlagCX、驱动材料只读使用，工作文件位于新容器 `/workspace/repro`。
- 固定 vLLM/插件提交；补齐同版驱动用户态依赖，保留 CoreX torch 和 FlagTree。
- vLLM 普通安装到 venv，测试通过 venv Python 启动，双卡通信采用显式回环地址。
- 只做文本 TP1/TP2 eager、FULL graph、API/SSE；回答质量与生成链路分别记录。
- 同步 README 和教程一指向教程二的说明。

## 实际命令及结果

`steps/` 保存本轮 099–104 每步原始 `command.sh`、`output.log`、`metadata.json`；包含起止时间、退出码和实际输出。文件中的旧教程片段属于编辑前读取记录，不是新版操作要求。

| 步骤 | 动作 | 结果 |
| --- | --- | --- |
| 099 | 读取仓库状态、原文档和发布脚本 | 退出 0 |
| 100 | 读取现有验证脚本及辅助包安装器 | 退出 0 |
| 101 | 读取环境检查、实际库目录及插件构建声明 | 退出 0 |
| 102 | 检查本机只读材料路径，搜索旧命令 | 路径存在；容器没有 rg，搜索退出 127；原样保留 |
| 编辑 | 替换教程二、更新入口与交叉引用 | 通过 apply_patch 写容器文件；第一次合并删除/新增同一路径被工具拒绝，随后分开执行成功 |
| 103 | 检查文档代码、链接、命令范围、凭据模式、记录器行为及 git diff | 退出 0 |
| 修正 | 为离线模型脚本加入 main 保护；核对多进程启动入口 | 已写入最终文档 |
| 104 | 重跑静态检查，执行文档内环境检查代码，核对驱动包/库 SHA256 和模型配置存在 | 退出 0，VENDOR_PASS、RUNTIME_PASS |

静态结果：24 个 Bash 代码块、8 个 Python heredoc、2 个 Shell heredoc 全部语法通过。4 个宿主代码块仅为 pull/run/exec。相对链接、禁止项及凭据模式检查通过；git diff --check 通过。

记录器实测：成功命令退出 0，故意失败命令返回并保存 17，stdin heredoc 正常传入；tee 退出码独立保存。

环境代码执行使用已有 venv 和插件目录，未安装新包。GPU 0/1 分别约 31.80 GiB 空闲；厂商版本、编译器归属、GPU 加法、NumPy 桥接、vLLM 0.32 导入路径、插件平台及 FlagCX 动态库检查通过。驱动包和用户态 libcuda 的 SHA256 与教程一致。

此次没有重新执行模型、通信或新容器完整搭建；对应历史实测见上一轮验证记录。没有宣称依赖声明全部满足或生成精度已修复。发布时使用 GitHub Git objects API 更新 main，不强制覆盖；凭据仅在内存中使用，不进入本记录。

## 手动复现发现的终端记录问题

用户在新容器 a20ad38e000a 按第 11 节操作时，客户端记录会话退出 127。读取 `/workspace/repro/logs/client-session-20261104T115918Z.log` 确认错误为 `set: Illegal option -o pipefail` 和 `source: not found`；`text_client.py` 未创建，客户端进程和 API 结果目录均不存在。服务端仍正常，容器内 `/v1/models` 返回 200 和 qwen。

根因是原教程未给 script 指定命令，它按默认 SHELL 启动 sh；外层 docker exec bash 不能保证其子 shell 是 Bash。已将教程两处 script 命令改为显式 `-c 'bash --noprofile --norc -i'`，并说明失败后需重新执行完整客户端代码块。诊断记录位于当前容器 logs 下的 inspect-text-client-status 和 inspect-client-session 步骤目录。此修正只处理 shell 入口，不改变模型测试判据。
