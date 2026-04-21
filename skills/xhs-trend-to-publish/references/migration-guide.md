# xhs-trend-to-publish 迁移说明

## 目标

把这套 workflow 搬到另一台电脑时，尽量做到：

- 不改业务脚本主体
- 优先复用仓库里已经 vendored 的 skill
- 只调整环境变量、账号配置和登录态
- 先自检，再跑真实链路

## 已随仓库提供的依赖

当前仓库已经包含：

- `vendor/XiaohongshuSkills`
- `vendor/Auto-Redbook-Skills`
- `vendor/MediaCrawler`
- `../../baoyu-post-to-wechat`

因此迁移到新机器时，不需要再额外 clone 这些依赖仓库。

## 仍然需要本机补齐的东西

- Python
- `uv`
- `bun` 或 `npx`
- Chrome
- 小红书 Chrome profile
- 微信公众号凭证和登录态

建议先在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-new-machine.ps1
```

## 推荐环境变量

建议按新机器实际路径设置：

- `XHS_DOUYIN_MEDIACRAWLER_ROOT`
- `XHS_DOUYIN_OUTPUT_ROOT`
- `XHS_WECHAT_API_SCRIPT`
- `XHS_PROFILE_DIR`
- `XHS_PROFILE_DIR_<ACCOUNT>`

说明：

- 单账号覆盖优先级高于 `XHS_PROFILE_DIR`
- 如果都不设置，脚本会回退到仓库内置默认路径

## 账号配置

模板文件：

- `../config/accounts.template.json`

本地实际使用文件：

- `../vendor/XiaohongshuSkills/config/accounts.json`

推荐做法：

1. 先从模板复制结构
2. 填自己的账号名和 `profile_dir`
3. 不把真实账号路径提交回 GitHub

## 自检命令

```bash
python ../scripts/check_environment.py
```

它会检查：

- `python`
- `uv`
- `bun` / `npx`
- `MediaCrawler` 路径
- `Auto-Redbook-Skills` 渲染器路径
- `XiaohongshuSkills` 脚本路径
- `WeChat API` 脚本路径
- 当前 Python 环境能否导入核心依赖
- `MediaCrawler` 的 `uv` 运行环境
- 小红书 `accounts.json`
- 默认账号 `profile_dir`

## 建议验证顺序

1. `python ../scripts/check_environment.py`
2. `python ../scripts/pipeline.py --platform brief --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0`
3. 验证小红书登录
4. 验证草稿或私密发布
5. 需要时再验证公众号 API 发布

## 常见问题

### 1. Douyin detail 跑不动

优先检查：

- `XHS_DOUYIN_MEDIACRAWLER_ROOT`
- `XHS_DOUYIN_OUTPUT_ROOT`
- `uv` 是否可用
- `MediaCrawler` 的 `uv sync` 是否成功

### 2. 小红书发布跑不动

优先检查：

- `vendor/XiaohongshuSkills/config/accounts.json`
- 默认账号 `profile_dir` 是否真实存在
- 是否需要重新登录：

```bash
python ../vendor/XiaohongshuSkills/scripts/cdp_publish.py --account <name> login
```

### 3. WeChat API 分支跑不动

优先检查：

- `XHS_WECHAT_API_SCRIPT`
- `skills/baoyu-post-to-wechat/scripts` 下的 Bun 依赖是否已安装
- 公众号凭证是否完整
