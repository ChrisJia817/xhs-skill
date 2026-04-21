# 新电脑 5 分钟清单

这份清单只解决一件事：`clone` 之后，怎样把仓库尽快跑起来。

如果你还想看完整背景、目录边界和安全约束，再看 [setup-new-machine.md](setup-new-machine.md)。

## 1. Clone 仓库

```bash
git clone https://github.com/ChrisJia817/xhs-skill.git
cd xhs-skill
```

## 2. 准备最小基础环境

至少准备：

- Python
- `uv`
- `bun` 或 `npx`
- Chrome

## 3. 运行一键安装

仓库已经内置这条工作流需要的关键 skill 和 vendor 依赖源码：

- `skills/xhs-trend-to-publish/vendor/MediaCrawler`
- `skills/xhs-trend-to-publish/vendor/XiaohongshuSkills`
- `skills/xhs-trend-to-publish/vendor/Auto-Redbook-Skills`
- `skills/baoyu-post-to-wechat`

首次 clone 后先执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-new-machine.ps1
```

这个脚本会：

- 安装 `Auto-Redbook-Skills` 的 Python 依赖
- 安装 `XiaohongshuSkills` 的 Python 依赖
- 安装 Python Playwright 的 Chromium 浏览器
- 在 `skills/xhs-trend-to-publish/vendor/MediaCrawler` 下执行 `uv sync`
- 在 MediaCrawler 的 `uv` 环境里安装 Chromium 浏览器
- 在 `skills/baoyu-post-to-wechat/scripts` 下执行 `bun install` 或 `npx -y bun install`
- 创建工作流运行时目录

## 4. 补账号与路径

这一步不再需要额外下载 `MediaCrawler` 或 `baoyu-post-to-wechat`，但仍然需要补你这台机器的账号、登录态和路径。

推荐优先用环境变量：

- `XHS_DOUYIN_MEDIACRAWLER_ROOT`
- `XHS_DOUYIN_OUTPUT_ROOT`
- `XHS_WECHAT_API_SCRIPT`
- `XHS_PROFILE_DIR`
- `XHS_PROFILE_DIR_<ACCOUNT>`

如果你不额外设置路径，仓库默认会优先使用：

- `skills/xhs-trend-to-publish/vendor/MediaCrawler`
- `skills/baoyu-post-to-wechat/scripts/wechat-api.ts`

## 5. 补小红书账号模板

先参考：

- `skills/xhs-trend-to-publish/config/accounts.template.json`

然后在本地填写：

- `skills/xhs-trend-to-publish/vendor/XiaohongshuSkills/config/accounts.json`

至少保证默认账号的 `profile_dir` 指向这台机器上的真实 Chrome profile。

## 6. 跑环境自检

```bash
python skills/xhs-trend-to-publish/scripts/check_environment.py
```

如果这一步失败，不要直接跑发布。

## 7. 先跑 mock 链路

```bash
python skills/xhs-trend-to-publish/scripts/pipeline.py --platform brief --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0
```

这一步通过，说明：

- 仓库内置路径解析正常
- 主工作流能完成最小闭环
- 可以继续验证真实登录和发布

## 8. 最后再碰真实发布

顺序不要反：

1. 先验证小红书登录
2. 先测草稿或私密
3. 最后再测公开发布

## 一句话版

`clone -> 跑 setup-new-machine.ps1 -> 配账号和登录态 -> check_environment -> 跑 mock -> 再测真实登录和草稿发布`
