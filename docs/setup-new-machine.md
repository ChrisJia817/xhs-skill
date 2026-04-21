# 新电脑部署

这份文档解决的是“如何在另一台机器上恢复同样的 workflow 能力”，不是“怎么把旧电脑的运行态整个搬过来”。

如果你只想用最短路径跑起来，先看：

- [5 分钟清单](quickstart-first-run.md)

这份文档是详细版。

## 原则

迁移时只迁移三类东西：

- 规则
- 脚本
- 模板

这些东西不要跟着仓库迁移：

- token、cookie、app secret、二维码
- Chrome 登录态
- 真实发布结果
- 抓取缓存
- OpenClaw 本机状态目录

## 1. Clone 仓库

```bash
git clone https://github.com/ChrisJia817/xhs-skill.git
cd xhs-skill
```

## 2. 安装基础依赖

至少准备：

- Python
- `uv`
- `bun` 或 `npx`
- Chrome

如果要跑具体分支，再补：

- Douyin：MediaCrawler 及其依赖
- WeChat：`baoyu-post-to-wechat` 对应脚本与凭证

## 3. 决定你的路径策略

建议优先用环境变量，因为跨机器最稳。

### 方案 A：环境变量优先

建议设置：

- `XHS_DOUYIN_MEDIACRAWLER_ROOT`
- `XHS_DOUYIN_OUTPUT_ROOT`
- `XHS_WECHAT_API_SCRIPT`
- `XHS_PROFILE_DIR`
- `XHS_PROFILE_DIR_<ACCOUNT>`

### 方案 B：按仓库相对目录放外部依赖

如果你不想配环境变量，也可以按约定路径放：

- `external/MediaCrawler`
- `external/baoyu-post-to-wechat/scripts/wechat-api.ts`

当前 `skills/xhs-trend-to-publish/scripts/vendor_paths.py` 会优先找环境变量，其次找这些相对目录。

## 4. 补账号配置

先参考：

- `skills/xhs-trend-to-publish/config/accounts.template.json`

然后在本地填写：

- `skills/xhs-trend-to-publish/vendor/XiaohongshuSkills/config/accounts.json`

至少要保证默认账号的 `profile_dir` 指向这台机器上的真实 Chrome profile。

## 5. 跑环境自检

```bash
python skills/xhs-trend-to-publish/scripts/check_environment.py
```

这一步会检查：

- `uv`
- `bun` / `npx`
- MediaCrawler 路径
- WeChat API 脚本路径
- 小红书账号配置
- 默认账号 profile 是否存在

如果这一步不通过，不要直接跑正式发布。

## 6. 先跑 mock 链路

```bash
python skills/xhs-trend-to-publish/scripts/pipeline.py --platform brief --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0
```

mock 通过再继续，别反过来。

## 7. 再验证真实账号

推荐顺序：

1. 先确认 Chrome profile 存在
2. 必要时重新登录
3. 先测草稿或私密
4. 最后再测公开发布

## 8. 推送前检查

推 GitHub 之前，至少确认：

- 没有把 `data/`、`temp/`、`memory/*.md` 加进去
- 没有把 `accounts.json`、token、cookie、profile 路径加进去
- 没有把真实发布结果和抓取缓存加进去

## 9. 推荐阅读顺序

如果是新电脑上的 agent，建议按这个顺序读：

1. `README.md`
2. `AGENTS.md`
3. `docs/quickstart-first-run.md`
4. `skills/xhs-trend-to-publish/README.md`
5. `skills/xhs-trend-to-publish/SKILL.md`
