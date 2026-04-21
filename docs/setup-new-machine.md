# 新电脑部署

这份文档的目标不是“恢复旧电脑状态”，而是“让新电脑拥有同样的 workflow 能力”。

## 1. Clone 仓库

把 `openclaw-workspace` clone 到新电脑，直接作为 agent 的工作区使用。

## 2. 安装基础依赖

至少准备：

- Python
- `uv`
- `bun` 或 `npx`
- Chrome

如果要跑对应分支，再补：

- Douyin：MediaCrawler 及其依赖
- WeChat：`baoyu-post-to-wechat` 对应脚本与凭证

## 3. 补本机专属配置

优先用环境变量，不要把真实路径写回仓库：

- `XHS_DOUYIN_MEDIACRAWLER_ROOT`
- `XHS_DOUYIN_OUTPUT_ROOT`
- `XHS_WECHAT_API_SCRIPT`
- `XHS_PROFILE_DIR`
- `XHS_PROFILE_DIR_<ACCOUNT>`

推荐顺序：

1. 先参考 `skills/xhs-trend-to-publish/config/accounts.template.json`
2. 再把本机账号信息写到本地的 `vendor/XiaohongshuSkills/config/accounts.json`
3. 能用环境变量覆盖的路径，尽量走环境变量

如果你不想配环境变量，也可以按下面的仓库相对目录放外部依赖：

- `external/MediaCrawler`
- `external/baoyu-post-to-wechat/scripts/wechat-api.ts`

这样 `vendor_paths.py` 也能自动找到它们。

## 4. 先跑环境自检

```bash
python skills/xhs-trend-to-publish/scripts/check_environment.py
```

这一步不通过，不要直接跑正式发布。

## 5. 先跑 mock 链路

```bash
python skills/xhs-trend-to-publish/scripts/pipeline.py --platform brief --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0
```

确认结构化产物和流程都能走通，再碰真实账号。

## 6. 再验证真实登录和发布

如果要跑小红书：

- 先确认 Chrome profile 存在
- 必要时重新登录
- 先验证草稿或私密发布
- 最后再考虑公开发布

## 7. 推送前检查

推 GitHub 之前，至少检查一次：

- 没有把 `data/`、`temp/`、`memory/*.md` 加进去
- 没有把 `accounts.json`、token、二维码、cookie、profile 路径加进去
- 没有把真实发布结果和抓取缓存加进去
