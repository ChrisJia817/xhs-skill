# xhs-trend-to-publish

这是一个把“小红书热点发现、内容改写、出图渲染、发布执行、公众号分支改写”串起来的 workflow。

主链路：

`discover -> score -> rewrite -> markdown -> render -> publish`

扩展链路：

- `xhs + douyin -> merged -> topic brief`
- `topic brief -> wechat rewrite -> markdown -> api publish`

## 仓库里已经带了什么

这个 skill 现在默认依赖的源码已经随仓库一起提供：

- `vendor/XiaohongshuSkills`
- `vendor/Auto-Redbook-Skills`
- `vendor/MediaCrawler`
- `../baoyu-post-to-wechat`

所以新机器上不需要再单独下载这些 skill 或仓库。

仍然需要你自己准备：

- Python
- `uv`
- `bun` 或 `npx`
- Chrome
- 小红书账号的真实 Chrome profile
- 微信公众号凭证和登录相关配置

## 新机器最快启动方式

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-new-machine.ps1
```

然后执行：

```bash
python skills/xhs-trend-to-publish/scripts/check_environment.py
```

如果自检通过，再先跑 mock：

```bash
python scripts/pipeline.py --platform brief --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0
```

## 路径解析默认规则

当前脚本会优先按这个顺序找依赖：

### Douyin / MediaCrawler

1. `XHS_DOUYIN_MEDIACRAWLER_ROOT`
2. `vendor/MediaCrawler`
3. `external/MediaCrawler`

### WeChat API

1. `XHS_WECHAT_API_SCRIPT`
2. `../baoyu-post-to-wechat/scripts/wechat-api.ts`
3. `external/baoyu-post-to-wechat/scripts/wechat-api.ts`

### 小红书账号 profile

1. `XHS_PROFILE_DIR_<ACCOUNT>`
2. `XHS_PROFILE_DIR`
3. `vendor/XiaohongshuSkills/config/accounts.json` 里的 `profile_dir`

## 推荐运行顺序

1. 跑 `scripts/check_environment.py`
2. 跑 `scripts/pipeline.py ... --discover-backend mock`
3. 验证小红书登录
4. 只测草稿或私密发布
5. 最后再测真实公开发布

## 重要说明

- `vendor/XiaohongshuSkills/config/accounts.json` 只适合本地使用，不应直接作为公开模板提交
- 账号模板请看 `config/accounts.template.json`
- 登录态、二维码、公众号凭证和真实发布结果都不应随仓库公开
- 详细迁移说明见 `references/migration-guide.md`
