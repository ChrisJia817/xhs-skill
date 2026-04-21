# AGENTS.md - GitHub Workspace

这个仓库是给 OpenClaw / Codex 类 agent 直接读取的工作区，不是运行时状态备份。

## Session Startup

进入仓库后，按这个顺序读：

1. `README.md`
2. `SOUL.md`
3. `USER.md`
4. `MEMORY.md`
5. 如果任务涉及小红书工作流：`skills/xhs-trend-to-publish/README.md`
6. 然后读：`skills/xhs-trend-to-publish/SKILL.md`
7. 如果任务涉及微信公众号分支：`skills/baoyu-post-to-wechat/SKILL.md`
8. 如果是在新电脑落地或环境异常：`docs/setup-new-machine.md`

## Working Rules

- 把这个仓库视为 workflow 的源码和规则来源。
- 把环境变量、Chrome profile、登录态、发布账号、二维码、运行产物视为本机私有状态。
- 不要把 secrets、私人记忆、真实发布结果、抓取缓存提交回仓库。
- 本地缺少 `data/`、`temp/`、`memory/` 之类运行目录时，可以创建，但保持未跟踪。
- 发布流程出问题时，优先修 adapter、配置或 vendor 兼容层；不要先推翻主流程。
- 如果你修改了共享规则，更新对应文档，而不是只在对话里“记住”。

## Workflow Defaults

- 小红书主流程默认顺序：`discover -> score -> rewrite -> markdown -> render -> publish`
- 默认优先 `draft` 或 `private`，公开发布必须明确指定
- 草稿箱目标必须走同 session 的“暂存离开”路径，不要把“点击发布”误判为“已经存草稿”
- Douyin 链路默认使用仓库内 vendored `MediaCrawler`
- WeChat 链路默认使用仓库内 `skills/baoyu-post-to-wechat`
- 内容样本池默认合并三路：
  1. 关键词搜索结果
  2. 高热视频/笔记作者主页样本
  3. 首页/推荐页图文样本

## GitHub Hygiene

- 模板可以提交，私人化内容默认不要提交。
- 如果你在本机补了 `USER.md`、`IDENTITY.md`、`MEMORY.md` 的私人内容，推送前先确认是否需要改回模板版。
