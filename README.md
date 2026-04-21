# OpenClaw Workflow Workspace

这个目录是给 GitHub 和新电脑用的“可读工作区”。

目标只有两个：

- 新电脑上的 agent clone 下来后，先读 `AGENTS.md` 就知道该看什么、该怎么跑。
- 真正可复用的 workflow 跟仓库走；账号、密钥、登录态、运行产物只留在本机。

## 目录说明

- `AGENTS.md`：agent 进入仓库后的启动顺序和工作规则
- `SOUL.md`：行为原则
- `IDENTITY.md`：agent 身份占位
- `USER.md`：用户偏好占位
- `MEMORY.md`：这套 workflow 的长期偏好和约束
- `docs/setup-new-machine.md`：新电脑落地步骤
- `skills/xhs-trend-to-publish`：去敏后的业务 workflow 快照
- `scripts/sync_from_local_openclaw.ps1`：从旧机器的 OpenClaw 工作区重新同步 skill

## 这类内容可以进 GitHub

- 规则文档、说明文档、参考资料
- `skills/xhs-trend-to-publish` 里的 `scripts/`、`references/`、`config/` 模板、vendor 代码
- 通用占位文件和新机部署脚本

## 这类内容不要进 GitHub

- `config/openclaw.json`
- `.openclaw/`、`state/`、`startup/`、`downloads/`、`tools/`
- `memory/*.md` 里的私人会话记录
- `skills/xhs-trend-to-publish/data/`
- `skills/xhs-trend-to-publish/temp/`
- token、app secret、二维码、cookie、Chrome 登录态、真实发布结果

## 新机使用

1. 把这个目录 clone 到新电脑。
2. 先读 `AGENTS.md`。
3. 按 `docs/setup-new-machine.md` 补本机依赖、环境变量和账号配置。
4. 需要跑小红书工作流时，再读 `skills/xhs-trend-to-publish/README.md` 和 `SKILL.md`。

## 从旧机器更新 workflow

在当前仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_from_local_openclaw.ps1
```

默认会从 `D:\OpenClaw\.openclaw\workspace` 同步 `xhs-trend-to-publish`，并自动排除 `data/`、`temp/`、`__pycache__/`、vendor 内嵌 `.git/` 等不该提交的内容。
