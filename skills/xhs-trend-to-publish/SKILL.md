---
name: xhs-trend-to-publish
description: 小红书热点发现→改写→出图→发布的一体化 workflow。适用于根据关键词自动抓取热点、筛选候选、生成笔记正文与渲染 Markdown、输出封面/卡片图片，并按草稿/私密/公开策略发布。默认先走可审计、可回看、可中断的流水线；优先私密发布，不默认高风险自动公开。
---

# xhs-trend-to-publish

这是一个把“小红书热点发现、内容改写、图片生成、发布执行、结果归档”串起来的 workflow skill。

## 适用场景

当用户想做以下事情时使用：
- 根据关键词自动搜索小红书热点
- 从搜索结果里筛选值得做的选题
- 将热点改写成小红书图文笔记
- 自动生成封面和正文卡片图片
- 以草稿 / 私密 / 公开 / 定时方式发布
- 为后续数据回收保留结构化产物

## 默认原则

1. **先搜后写再发**，不要直接从关键词跳到发布。
2. **热点不等于选题**，必须先评分和筛选。
3. **先产出结构化中间文件**，不要只在内存里流转。
4. **默认使用草稿或私密发布**，公开发布必须明确指定。
5. **发布后保留 run 记录**，便于复盘和重跑。
6. **图片总数不少于 4 张**（至少满足：封面 + 至少 2 张内容卡 + 1 张收束/结尾卡；内容需要时可以超过 4 张）。
7. **文案要更像真人表达**，避免明显模板腔、过度套路化、空泛结论式表述。
8. **最终正文末尾必须带话题标签**，用于发布时保留话题曝光入口。

## 目录约定

- `config/`：账号、persona、pipeline 参数
- `data/incoming/`：原始输入
- `data/trends/`：搜索结果与评分结果
- `data/drafts/`：改写稿
- `data/renders/`：渲染 Markdown 与图片输出
- `data/publish-results/`：发布结果
- `data/metrics/`：回收指标
- `scripts/`：执行脚本
- `references/`：规则与模板参考
- `vendor/`：第三方参考实现或适配层

## 推荐主流程

### 1. 发现热点
运行：

```bash
python scripts/discover_trends.py --keyword "无货源" --publish-time "半年内"
```

输出：`data/trends/raw/<run_id>.json`

### 2. 评分筛选
运行：

```bash
python scripts/score_trends.py --input data/trends/raw/<run_id>.json
```

输出：`data/trends/scored/<run_id>.json`

### 3. 改写笔记
运行：

```bash
python scripts/rewrite_note.py --input data/trends/scored/<run_id>.json
```

输出：`data/drafts/<run_id>.json`

### 4. 生成渲染 Markdown
运行：

```bash
python scripts/build_render_markdown.py --input data/drafts/<run_id>.json
```

输出：`data/renders/<run_id>/content.md`

### 5. 渲染图片
运行：

```bash
python scripts/render_cards.py --run-id <run_id>
```

输出：
- `data/renders/<run_id>/cover.png`
- `data/renders/<run_id>/card_1.png`...

### 6. 发布
运行：

```bash
python scripts/publish_note.py --run-id <run_id> --mode private --backend cdp
```

输出：`data/publish-results/<run_id>.json`

### 7. 全流程一键跑
运行：

```bash
python scripts/pipeline.py --keyword "无货源" --publish-time "半年内" --mode private --backend cdp
```

## 当前实现范围（MVP）

当前版本是可用骨架，目标是：
- 先把结构、产物和执行链条立起来
- 默认提供稳定的中间文件格式
- 搜索 / 出图 / 发布优先走适配器与占位逻辑
- 允许后续接入 CDP 搜索与真实渲染/发布引擎

## 何时读取 references

- 需要调评分规则时：读 `references/scoring-rules.md`
- 需要调改写模板时：读 `references/rewrite-templates.md`
- 需要调主题路由时：读 `references/theme-routing.md`
- 需要看风险边界时：读 `references/risk-guardrails.md`

## 风险控制

- 公开发布不是默认值
- 草稿与私密模式优先
- 任何失败都应保留已经生成的中间文件
- 不要在没有图片时发布图文
- 不要在没有标题和正文时执行发布
- 不要把“点击发布”误当成“已进草稿箱”；如果目标是草稿箱，必须显式走 **暂存离开** 路径并记录结果
