# 新电脑部署

这份文档解决的是“如何在另一台机器上恢复同样的 workflow 能力”，不是“把旧电脑的运行态整机搬过来”。

如果你只想看最短路径，先看：

- [5 分钟清单](quickstart-first-run.md)

## 原则

迁移时只迁移三类东西：

- 规则
- 脚本
- 模板

这些内容不要跟着仓库迁移：

- token、cookie、app secret、二维码、登录态
- Chrome profile 本体
- 真实发布结果和抓取缓存
- OpenClaw 本机状态目录

## 仓库内已包含的关键 skill

当前仓库已经带上：

- `skills/xhs-trend-to-publish/vendor/MediaCrawler`
- `skills/xhs-trend-to-publish/vendor/XiaohongshuSkills`
- `skills/xhs-trend-to-publish/vendor/Auto-Redbook-Skills`
- `skills/baoyu-post-to-wechat`

所以新机器上不需要再单独 clone 这些源码仓库，但仍然需要安装它们的运行依赖。

## 1. Clone 仓库

```bash
git clone https://github.com/ChrisJia817/xhs-skill.git
cd xhs-skill
```

## 2. 准备基础工具

至少准备：

- Python
- `uv`
- `bun` 或 `npx`
- Chrome

建议：

- MediaCrawler 对 Python 版本要求更严格，优先使用 Python 3.11+
- 如果你习惯虚拟环境，先激活你自己的 Python venv，再执行仓库脚本

## 3. 安装仓库内依赖

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-new-machine.ps1
```

这个脚本会安装和准备：

- `Auto-Redbook-Skills` 的 Python 依赖
- `XiaohongshuSkills` 的 Python 依赖
- Python Playwright Chromium
- `MediaCrawler` 的 `uv` 环境和 Chromium
- `baoyu-post-to-wechat` 的 Bun 依赖
- 工作流默认运行目录

## 4. 决定路径策略

推荐优先用环境变量，因为跨机器最稳。

建议设置：

- `XHS_DOUYIN_MEDIACRAWLER_ROOT`
- `XHS_DOUYIN_OUTPUT_ROOT`
- `XHS_WECHAT_API_SCRIPT`
- `XHS_PROFILE_DIR`
- `XHS_PROFILE_DIR_<ACCOUNT>`

如果你完全不配这些环境变量，当前工作流默认会优先落到：

- Douyin：`skills/xhs-trend-to-publish/vendor/MediaCrawler`
- WeChat：`skills/baoyu-post-to-wechat/scripts/wechat-api.ts`

## 5. 补小红书账号配置

先参考模板：

- `skills/xhs-trend-to-publish/config/accounts.template.json`

再在本地填写实际文件：

- `skills/xhs-trend-to-publish/vendor/XiaohongshuSkills/config/accounts.json`

最少需要确认：

- `default_account`
- 默认账号的 `profile_dir`
- 这条 `profile_dir` 在新机器上真实存在

## 6. 跑环境自检

```bash
python skills/xhs-trend-to-publish/scripts/check_environment.py
```

当前自检会检查：

- `python`
- `uv`
- `bun` / `npx`
- `MediaCrawler` 路径
- `Auto-Redbook-Skills` 渲染器路径
- `XiaohongshuSkills` 脚本路径
- `WeChat API` 脚本路径
- Python 依赖导入是否正常
- `MediaCrawler` 的 `uv run python --version`
- 小红书 `accounts.json`
- 默认账号 `profile_dir`

如果这里不过，不要直接进真实发布。

## 7. 建议验证顺序

先跑最轻量的链路：

```bash
python skills/xhs-trend-to-publish/scripts/pipeline.py --platform brief --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0
```

然后再按顺序验证：

1. 小红书登录
2. 草稿或私密发布
3. 微信分支
4. 最后才是公开发布

## 8. 推送前检查

推到 GitHub 之前，至少确认：

- 没有把 `data/`、`temp/`、缓存目录加进去
- 没有把 `accounts.json`、token、cookie、profile 路径加进去
- 没有把真实发布结果和抓取缓存加进去

## 9. 新机器上 agent 的阅读顺序

推荐：

1. `README.md`
2. `AGENTS.md`
3. `docs/quickstart-first-run.md`
4. `skills/xhs-trend-to-publish/README.md`
5. `skills/xhs-trend-to-publish/SKILL.md`
6. `skills/baoyu-post-to-wechat/SKILL.md`
