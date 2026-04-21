# 微信公众号分支体系设计（第一版）

## 目标

在不破坏现有小红书工作流的前提下，为同一主题新增一条微信公众号内容分支：

- 前半段复用：discover → score
- 中间新增：topic brief（平台无关主题简报）
- 后半段分叉：
  - 小红书：继续原有图文卡片链路
  - 微信公众号：走模板驱动长文改写 + 富文本/API 草稿发布
- 多公众号接入按原 `baoyu-post-to-wechat` 的方式保留扩展口：`accounts + alias + --account`。

## 总体结构

```text
raw trends
  -> scored trends
  -> topic brief
      ├─ xhs branch
      │   -> rewrite_note.py
      │   -> build_render_markdown.py
      │   -> render_cards.py
      │   -> publish_note.py (xhs draft)
      └─ wechat branch
          -> rewrite_wechat_article.py
          -> format_wechat_richtext.py / md-to-wechat bridge
          -> publish_wechat_api.py (wechat draft)
```

## 原则

1. 不把微信公众号直接塞进现有小红书后半段。
2. 共享选题理解，不共享最终成稿。
3. 微信公众号优先走 API draft（草稿箱）路径。
4. 微信文案不直接复用小红书卡片稿，而是复用 topic brief。
5. 微信模板由用户提供的公众号样文抽象而来，不臆造风格。

## 待实现模块

### 1. build_topic_brief.py
输入：
- `data/trends/raw/<run_id>.json`
- `data/trends/scored/<run_id>.json`

输出：
- `data/briefs/<run_id>.json`

职责：
- 提炼主题、核心痛点、常见误区、用户问题、证据素材、平台分支角度。

### 2. 微信模板资产
建议目录：
- `references/wechat-templates/`

包含：
- 模板 schema 说明
- 模板实例（例如 pain-method-conversion）
- 样文分析结果

### 3. rewrite_wechat_article.py
输入：
- `data/briefs/<run_id>.json`
- 模板名 / 模板结构

输出：
- `data/wechat-drafts/<run_id>.<template>.md`
- 或 HTML 中间稿

职责：
- 基于 brief 与模板结构生成微信公众号长文，不复用小红书卡片文案。

### 4. publish_wechat_api.py
输入：
- 微信稿件（md/html）
- 标题、摘要、作者、封面策略
- AppID / AppSecret
- 可选：`--account <alias>`

职责：
- 调用原 `baoyu-post-to-wechat` 的 API 路径，将文章写入公众号草稿箱。
- 多公众号时，发布层通过 `--account <alias>` 选择目标账号，具体凭证解析继续复用原 skill 的逻辑。

## 需要用户补充的前置条件

1. `WECHAT_APP_ID`
2. `WECHAT_APP_SECRET`
3. 2~3 篇微信公众号模板文章
4. 默认封面策略（手工给 / 首图 / 后续生成）
5. 评论默认值：
   - `need_open_comment`
   - `only_fans_can_comment`

## 多公众号扩展约定

为避免后续多公众号接入时推翻现有实现，当前公众号分支先保留与原 skill 一致的扩展口：

- 配置层支持 `accounts` 数组
- 每个账号最少包含：`name`、`alias`
- 建议支持字段：
  - `default`
  - `default_publish_method`
  - `default_author`
  - `need_open_comment`
  - `only_fans_can_comment`
  - `app_id`
  - `app_secret`
  - `chrome_profile_path`
- 发布脚本统一支持：`--account <alias>`
- 凭证层优先按 alias 解析，例如：
  - `WECHAT_MAIN_APP_ID`
  - `WECHAT_MAIN_APP_SECRET`
  - `WECHAT_AI_TOOLS_APP_ID`
  - `WECHAT_AI_TOOLS_APP_SECRET`
- 若未指定 `--account`，应优先使用 `default: true` 的账号；若只有一个账号则自动选中。

## 说明

当前阶段先搭体系，不直接并入现有 pipeline，也不直接重写 vendor skill。
