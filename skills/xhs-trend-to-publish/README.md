# xhs-trend-to-publish

小红书热点发现 → 改写 → 渲染 → 发布，以及多源（XHS + Douyin）topic brief → 微信/XHS 分支改写的一体化 workflow。

## 适用场景

适用于：
- 根据关键词做小红书选题与图文笔记
- 从多平台样本提炼 topic brief
- 将 topic brief 分发到：
  - 小红书改写链
  - 微信公众号改写链

## 当前能力概览

- XHS：discover → score → rewrite → markdown → render → publish
- Douyin：discover → detail enrich → merge → topic brief
- WeChat：topic brief → rewrite → markdown → API publish
- Unified brief：支持 `xhs + douyin -> merged -> topic brief`

## 快速开始

### 1. 准备依赖

请确保本机具备：
- Python
- `uv`
- `bun` 或 `npx`
- Chrome（供 XHS CDP 登录/发布使用）

如果要用 Douyin：
- MediaCrawler 仓库
- 对应登录态

如果要用 WeChat publish：
- `baoyu-post-to-wechat` 对应脚本
- 对应公众号凭证

### 2. 配置环境变量（推荐）

可配置：
- `XHS_DOUYIN_MEDIACRAWLER_ROOT`
- `XHS_DOUYIN_OUTPUT_ROOT`
- `XHS_WECHAT_API_SCRIPT`
- `XHS_PROFILE_DIR`
- `XHS_PROFILE_DIR_<ACCOUNT>`

说明：
- `XHS_PROFILE_DIR` 代表小红书 profile 根目录
- `XHS_PROFILE_DIR_<ACCOUNT>` 可覆盖单账号 profile 路径
- 若不设置环境变量，会回退到 `vendor/XiaohongshuSkills/config/accounts.json`
- 仓库已提供中性模板：`config/accounts.template.json`
  - GitHub 下载后可先复制它，再填自己的账号与 `profile_dir`

### 3. 先跑环境自检

```bash
python scripts/check_environment.py
```

### 4. 跑一个轻量联合 brief 示例

```bash
python scripts/pipeline.py --platform brief --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0
```

### 5. 跑一个 WeChat 分支示例

```bash
python scripts/pipeline.py --platform wechat --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0 --wechat-cover "https://example.com/cover.jpg"
```

## 迁移与新电脑使用

请看：
- `references/migration-guide.md`

## 重要说明

- 仓库中的 `vendor/XiaohongshuSkills/config/accounts.json` 可能在不同使用者环境里不适合直接提交或复用。
- 因此本仓库额外提供：
  - `config/accounts.template.json`
- 首次使用时，请自行配置：
  - 小红书 Chrome profile
  - Douyin 外部抓取路径
  - WeChat API 脚本路径
- 登录态、扫码态、公众号凭证属于外部系统状态，不随仓库自动携带。

## 建议发布到 GitHub 前再确认

- 不提交 `data/` 下的个人运行产物
- 不提交本机账号 profile 路径
- 不提交私人凭证/登录态
- 优先保留：
  - `README.md`
  - `references/`
  - `config/accounts.template.json`
  - `scripts/`
- 发布前可自查：

```bash
git status --short
python scripts/check_environment.py
```

如果你准备把这个 skill 单独公开，请确认工作区里没有：
- 真实发布结果 JSON
- 真实草稿内容
- 本机绝对路径样本
- 带个人用户名的 vendor 历史痕迹
