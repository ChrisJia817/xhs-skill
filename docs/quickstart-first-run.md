# 新电脑 5 分钟清单

这份清单只管一件事：`clone 后第一时间怎么把仓库跑起来`。

如果你想看完整背景、目录边界和安全约束，再回到 [setup-new-machine.md](setup-new-machine.md)。

## 1. Clone 仓库

```bash
git clone https://github.com/ChrisJia817/xhs-skill.git
cd xhs-skill
```

## 2. 装最小依赖

至少准备：

- Python
- `uv`
- `bun` 或 `npx`
- Chrome

## 3. 补外部依赖

二选一即可。

方案 A：配环境变量

- `XHS_DOUYIN_MEDIACRAWLER_ROOT`
- `XHS_DOUYIN_OUTPUT_ROOT`
- `XHS_WECHAT_API_SCRIPT`
- `XHS_PROFILE_DIR`
- `XHS_PROFILE_DIR_<ACCOUNT>`

方案 B：按仓库约定放到相对目录

- `external/MediaCrawler`
- `external/baoyu-post-to-wechat/scripts/wechat-api.ts`

## 4. 补账号模板

先参考：

- `skills/xhs-trend-to-publish/config/accounts.template.json`

再在本地写入：

- `skills/xhs-trend-to-publish/vendor/XiaohongshuSkills/config/accounts.json`

至少把默认账号的 `profile_dir` 指向你这台机器上的真实 Chrome profile。

## 5. 跑环境自检

```bash
python skills/xhs-trend-to-publish/scripts/check_environment.py
```

如果这一步失败，不要直接跑发布。

## 6. 先跑 mock 链路

```bash
python skills/xhs-trend-to-publish/scripts/pipeline.py --platform brief --sources xhs douyin --keyword "AI" --publish-time "半年内" --discover-backend mock --douyin-detail-limit 0
```

这一步通过，说明：

- 路径解析基本正常
- 主流程可以起跑
- 至少结构化产物链路没断

## 7. 最后再碰真实发布

顺序不要反：

1. 先验证小红书登录
2. 先试草稿或私密
3. 最后再考虑公开发布

## 一句话版

`clone -> 装依赖 -> 配路径/账号 -> check_environment -> 跑 mock -> 再测真实登录和草稿发布`
