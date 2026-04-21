# xhs-trend-to-publish 迁移说明

## 目标

把本工作流迁移到另一台电脑时，尽量做到：
- 不改业务脚本主体
- 只调整环境变量 / 账号配置 / 外部依赖路径
- 先自检，再正式运行

---

## 必备依赖

目标机器至少需要：
- Python
- `uv`
- `bun` 或 `npx`
- Chrome（供小红书 CDP / 账号登录使用）
- MediaCrawler（若要跑 Douyin discover/detail）
- `baoyu-post-to-wechat` 对应脚本（若要跑公众号 API publish）

---

## 推荐迁移步骤

### 1. 同步 workspace

把整个 `skills/xhs-trend-to-publish` 连同 `vendor/` 一起带到新机器。

### 2. 配置环境变量

推荐按新机器实际路径设置：

- `XHS_DOUYIN_MEDIACRAWLER_ROOT`
  - MediaCrawler 仓库根目录
- `XHS_DOUYIN_OUTPUT_ROOT`
  - MediaCrawler Douyin JSON 输出目录
- `XHS_WECHAT_API_SCRIPT`
  - `baoyu-post-to-wechat/scripts/wechat-api.ts` 的实际路径
- `XHS_PROFILE_DIR`
  - 小红书 Chrome profile 根目录；若配置此变量，会自动按账号名拼子目录
- 或单账号覆盖：
  - `XHS_PROFILE_DIR_DEFAULT`
  - `XHS_PROFILE_DIR_XHS2`
  - `XHS_PROFILE_DIR_SECOND`

说明：
- 单账号覆盖优先级高于 `XHS_PROFILE_DIR`
- 若两者都没配，则回退到 `accounts.json` 里的 `profile_dir`

### 3. 校正账号 profile

账号模板文件：
- `config/accounts.template.json`

vendor 当前实际读取文件：
- `vendor/XiaohongshuSkills/config/accounts.json`

推荐做法：
- 先参考 `config/accounts.template.json` 填好你的账号结构
- 再复制到 `vendor/XiaohongshuSkills/config/accounts.json`
- 或优先使用环境变量覆盖（更适合跨机器）

推荐环境变量：
- `XHS_PROFILE_DIR`
- `XHS_PROFILE_DIR_<ACCOUNT>`

说明：
- 单账号覆盖优先级高于 `XHS_PROFILE_DIR`
- 若两者都没配，则回退到 `accounts.json` 里的 `profile_dir`

```bash
python scripts/check_environment.py
```

此脚本会检查：
- `uv`
- `bun/npx`
- MediaCrawler 路径
- WeChat API 脚本路径
- XHS accounts 配置
- 默认账号 profile 是否存在
- `uv --version`
- MediaCrawler 目录下 `uv run python --version`

全部通过后，再跑正式 pipeline。

---

## 常见问题

### 1. Douyin detail 跑不动

优先检查：
- `XHS_DOUYIN_MEDIACRAWLER_ROOT`
- `XHS_DOUYIN_OUTPUT_ROOT`
- `uv` 是否可执行
- MediaCrawler 依赖是否安装完整

### 2. WeChat publish 跑不动

优先检查：
- `XHS_WECHAT_API_SCRIPT`
- `bun` / `npx`
- 公众号凭证与上游 skill 依赖

### 3. XHS 登录态丢失

优先检查：
- `accounts.json` 的默认账号
- `profile_dir` 是否指向新机器真实存在的 Chrome profile
- 是否需要重新登录：
  - `python vendor/XiaohongshuSkills/scripts/cdp_publish.py --account <name> login`

---

## 建议的迁移后验证顺序

1. `python scripts/check_environment.py`
2. `python scripts/pipeline.py --platform brief --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0`
3. `python scripts/pipeline.py --platform wechat --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0 --wechat-cover "https://example.com/cover.jpg"`
4. 需要真实发小红书时，再验证 XHS 登录与发布链

---

## 发布到 GitHub 前的清理建议

建议至少执行一次：

```bash
git status --short
python scripts/check_environment.py
```

重点确认：
- `data/` 运行产物不要公开提交
- `vendor/**/.git/` 不要带上游克隆历史
- `accounts.template.json` 可以提交
- `vendor/XiaohongshuSkills/config/accounts.json` 若含个人路径，不要作为默认公开样板
- 不要带私人凭证、登录态、二维码缓存、真实发布结果

仓库已提供可提交、可复制的中性模板：
- `config/accounts.template.json`

用途：
- 给 GitHub 下载者一个不绑定任何本机路径的起始配置
- 复制后填入自己的账号与 profile_dir，再放到 vendor 实际读取位置
