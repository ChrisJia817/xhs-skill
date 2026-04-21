# xhs-skill

一个给 agent 直接读取的、小红书内容工作流仓库。

它不是 OpenClaw 的整机备份，也不是运行时状态快照。它的目标更简单：

- 把可复用的 workflow、规则、脚本和模板放进 GitHub
- 让新电脑上的 agent clone 下来后，读几份文档就知道怎么继续工作

## 这个仓库能做什么

当前核心 workflow 是 [`skills/xhs-trend-to-publish`](skills/xhs-trend-to-publish/README.md)，主链路是：

`discover -> score -> rewrite -> markdown -> render -> publish`

它能覆盖这些能力：

- 从小红书和抖音发现热点与样本
- 合并样本池并生成 topic brief
- 改写成小红书图文文案
- 生成渲染 Markdown 和卡片图片
- 以草稿、私密或公开方式发布到小红书
- 把同一份 brief 分支改写成微信公众号文章

## 仓库定位

这份仓库里放的是“可迁移能力”，不放“本机状态”。

适合进 GitHub 的内容：

- 规则文档
- 工作流脚本
- 参考资料
- 示例配置模板
- vendor 代码和适配层

不应该进 GitHub 的内容：

- token、cookie、app secret、二维码、登录态
- `config/openclaw.json`
- `.openclaw/`、`state/`、`startup/`、`downloads/`
- `skills/xhs-trend-to-publish/data/`、`temp/`
- 私人记忆和真实发布结果

## 新电脑最快上手

如果你只是想把仓库 clone 到新电脑然后尽快跑起来，先看：

- [5 分钟清单](docs/quickstart-first-run.md)

如果你要看完整说明，再看：

- [详细部署文档](docs/setup-new-machine.md)

## Agent 入口

给 agent 的推荐阅读顺序在这里：

- [AGENTS.md](AGENTS.md)

对 agent 来说，进入仓库后的最小启动顺序是：

1. 读 `README.md`
2. 读 `SOUL.md`
3. 读 `USER.md`
4. 读 `MEMORY.md`
5. 涉及小红书 workflow 时再读 `skills/xhs-trend-to-publish/README.md` 和 `SKILL.md`

## 目录结构

- `AGENTS.md`: agent 启动顺序和共享规则
- `SOUL.md`: 行为原则
- `USER.md`: 用户偏好模板
- `MEMORY.md`: 共享的长期 workflow 偏好
- `docs/`: 新机落地和快速启动文档
- `scripts/`: 工作区级辅助脚本
- `skills/xhs-trend-to-publish/`: 业务 workflow 本体

## 最短验证路径

在新电脑上，推荐按这个顺序验证：

1. 跑环境自检

```bash
python skills/xhs-trend-to-publish/scripts/check_environment.py
```

2. 跑 mock 链路

```bash
python skills/xhs-trend-to-publish/scripts/pipeline.py --platform brief --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0
```

3. mock 通过后，再碰真实账号登录和草稿发布

## 从旧机器同步更新

如果旧机器上还有持续演进的 OpenClaw 工作区，可以用这个脚本重新同步 skill：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_from_local_openclaw.ps1
```

默认同步源是 `D:\OpenClaw\.openclaw\workspace`，会自动排除：

- `data/`
- `temp/`
- `__pycache__/`
- vendor 内嵌 `.git/`
- vendor 的 `tmp/` 和 `demos/`

## 相关文档

- [快速上手](docs/quickstart-first-run.md)
- [详细部署](docs/setup-new-machine.md)
- [小红书 workflow README](skills/xhs-trend-to-publish/README.md)
- [小红书 workflow SKILL](skills/xhs-trend-to-publish/SKILL.md)
