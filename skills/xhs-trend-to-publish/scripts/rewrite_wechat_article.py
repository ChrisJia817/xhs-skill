import argparse
from bootstrap import ROOT
from common import read_json, write_json, ensure_dir, append_stage_manifest, iso_now, resolve_wechat_account_settings

GENERIC_OLD_WAYS = [
    '看到热点就跟',
    '看到别人出结果就学',
    '一上来就堆动作',
]


def paragraph(lines: list[str]) -> str:
    return '\n\n'.join(line.strip() for line in lines if line and line.strip())


def normalize_keyword(keyword: str) -> str:
    text = (keyword or '').strip()
    return text.upper() if text.isascii() else text


def infer_focus_word(brief: dict) -> str:
    keyword = normalize_keyword(brief.get('keyword', ''))
    topic = brief.get('topic', keyword)
    if 'AI' in topic.upper() or 'AI' in keyword.upper():
        return '工具和方法'
    if '电商' in topic or '无货源' in topic:
        return '玩法和判断'
    if '运营' in topic or '流量' in topic:
        return '动作和节奏'
    return '方法和思路'


def infer_common_traps(brief: dict) -> list[tuple[str, str]]:
    topic = brief.get('topic', '')
    keyword = brief.get('keyword', '')
    if '无货源' in topic or '无货源' in keyword:
        return [
            ('只盯流量，不看履约', '很多人前面只想着怎么拿流量，却没把发货、售后、规则这些后端问题提前算清楚。'),
            ('只看玩法，不算成本', '看别人做起来很快，就以为自己也能轻松复制，但真正的成本常常藏在细节和试错里。'),
            ('把平台差异当不存在', '不同平台、不同类目、不同阶段的打法完全不一样，一套动作照抄到底，通常只会越做越乱。'),
        ]
    if 'AI' in topic.upper() or 'AI' in keyword.upper() or 'ai' in keyword.lower():
        return [
            ('只追新工具，不看真实问题', '表面上学了很多 AI 工具，实际上一直没有回答清楚：这些工具到底帮你解决什么问题。'),
            ('只学技巧，不做判断', '看到什么火就学什么，最后动作很多，但没有形成自己的方法和标准。'),
            ('把平台差异当不存在', '小红书和公众号看似都在讲同一个主题，但表达方式完全不同，一稿硬发两端，最后往往两边都不够好。'),
        ]
    return [
        ('只追热点，不做判断', '看到什么火就跟什么，最后内容很多，但没有一条真正形成自己的判断。'),
        ('只学方法，不看问题', '表面上学了很多东西，实际上却一直没有回答清楚：这些方法到底帮你解决什么问题。'),
        ('把平台差异当不存在', '不同平台看似都在讲同一个主题，但表达方式完全不同，一稿硬发两端，最后往往两边都不够好。'),
    ]


def build_title(brief: dict) -> str:
    keyword = normalize_keyword(brief.get('keyword', ''))
    common_questions = brief.get('common_questions') or []
    pain_points = brief.get('pain_points') or []

    if common_questions:
        q = common_questions[0]
        if '怎么做' in q:
            return f'做{keyword}的人，最后往往都卡在这一步'
        if '有没有机会' in q or '值不值得' in q:
            return f'现在做{keyword}，很多人一开始就判断错了'
    if pain_points:
        return f'做{keyword}，真正卡住大多数人的不是工具，而是思路'
    return f'做{keyword}，别再用老办法硬推了'


def build_summary(brief: dict) -> str:
    pain_points = brief.get('pain_points') or []
    if pain_points:
        text = pain_points[0]
        return text[:118] + ('…' if len(text) > 118 else '')
    return '这是一篇基于真实热点与高热样本提炼出的公众号文章。'


def build_body(brief: dict, template_name: str) -> str:
    keyword = normalize_keyword(brief.get('keyword', ''))
    topic = brief.get('topic', keyword)
    pain_points = brief.get('pain_points') or [f'很多人关注{keyword}，但一直做不出稳定结果。']
    common_questions = brief.get('common_questions') or [f'{keyword}这个方向到底值不值得投入？']
    evidence = brief.get('evidence') or []
    focus_word = infer_focus_word(brief)
    traps = infer_common_traps(brief)

    sample_titles = [e.get('title', '') for e in evidence[:3] if e.get('title')]
    sample_line = '、'.join(sample_titles) if sample_titles else f'{keyword}相关高热内容'

    intro = paragraph([
        f'做{keyword}这件事，你是不是也有过这种感觉：',
        '学了不少、看了不少、试了不少，表面上每天都很忙，但结果就是迟迟出不来。',
        f'有时候你会觉得，问题是不是出在{focus_word}不够新、方法不够多、执行还不够狠。',
        f'但如果把这次抓到的真实内容摊开来看，比如：{sample_line}，你会发现真正让人持续卡住的，往往不是这些表层动作。',
        f'真正的问题，更接近这一句：你不是没在做，而是一直缺一条能落地、能验证、能持续的路径。',
    ])

    thesis = paragraph([
        '如果要把这件事讲透，核心其实就一句话：',
        f'真正卡住大多数人的，从来不是不够努力，而是一开始就把{keyword}想得太简单了。',
    ])

    why_old_way_fails = paragraph([
        '很多人现在最常见的做法，其实都很像一种“看起来很努力，结果却很慢”的路径。',
        f"{'、'.join(GENERIC_OLD_WAYS)}，结果折腾了很久，最后还是回到那个问题：{common_questions[0]}",
        '问题不是你做得不够多，而是你一直在用一种低效率的方法，试图换来高确定性的结果。',
    ])

    step1 = paragraph([
        '第一步：先别急着追方法，先确认自己真正卡在哪',
        f'从这次提炼出来的高频痛点看，最靠前的几个问题其实很集中：{'；'.join(pain_points[:2])}。',
        '也就是说，很多人不是没有努力，而是根本没有先把自己的真实问题定义清楚。问题定义错了，后面做什么都像在补漏。',
    ])

    questions_text = list(common_questions[:3])
    if ('无货源' in topic or '无货源' in keyword) and len(questions_text) < 3:
        fallback_questions = [
            '新手到底该从哪里开始？',
            '这个模式最容易踩的坑是什么？',
            '怎么判断自己是在赚钱，还是只是在白忙？',
        ]
        for q in fallback_questions:
            if q not in questions_text:
                questions_text.append(q)
            if len(questions_text) >= 3:
                break
    questions_for_text = '；'.join(questions_text) if len(questions_text) > 1 else questions_text[0]
    step2 = paragraph([
        '第二步：别只看单篇爆文，要看它们反复在回答什么问题',
        f'把高热内容放在一起看，你会发现大家真正反复关心的，并不是某一个具体动作，而是这些问题：{questions_for_text}。',
        '这说明用户真正想买单的，往往不是零散技巧，而是一套能帮他减少试错、提升判断的清晰路径。',
        '换句话说，读者想要的从来不只是“告诉我怎么做”，而是“告诉我先做什么、别做什么、做到什么程度才算走对了”。',
    ])

    step3 = paragraph([
        '第三步：同一个主题，不同平台要用不同写法',
        '这一点很多人也容易忽略。小红书更适合切片、钩子、强痛点；微信公众号更适合展开、解释、建立认知。',
        '如果你总想着一篇稿子同时解决所有平台的问题，最后大概率就是两个平台都不够好。',
    ])

    pitfall_lines = ['这里最容易做错的地方，基本就三种：', '']
    numerals = ['一', '二', '三']
    for idx, (title, desc) in enumerate(traps[:3]):
        pitfall_lines.append(f'**{numerals[idx]}、{title}**')
        pitfall_lines.append(desc)
        pitfall_lines.append('')
    pitfalls = paragraph(pitfall_lines)

    closing = paragraph([
        f'所以回到最开始那个问题：{common_questions[0]}',
        f'如果你总觉得自己在{topic}这件事上已经很努力了，但还是没有走顺，不妨先停下来重新看一遍：你到底是在解决真正的问题，还是只是在做一些看起来很像努力的动作？',
        '很多时候，方向一旦对了，后面的效率会比你想象中高很多。',
    ])

    cta = paragraph([
        f'如果你现在卡住的，也是{topic}里的这些问题——不知道该从哪里开始，不知道哪些动作值得做，也不知道怎么把结果真正跑出来——那说明你缺的可能不是某个小技巧，而是一套完整闭环。',
        '尤其是无货源电商这类项目，真正决定结果的，不只是起店，而是后面的选品、履约、引流、转化能不能接得住。',
        '如果你想系统把这件事学明白，少走一些试错弯路，那后面这一部分内容你可以重点看。',
        '',
        '**【此处插入成交案例图】**',
        '**【此处插入课程海报图】**',
        '**【此处插入课程大纲图】**',
        '**【此处插入微信二维码图】**',
    ])

    sections = [intro, thesis, why_old_way_fails, step1, step2, step3, pitfalls, closing, cta]
    return '\n\n'.join(sections)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--template', default='pain-method-conversion')
    args = parser.parse_args()

    brief = read_json(args.input)
    account_settings = resolve_wechat_account_settings()
    author = account_settings.get('default_author') or '大人助理'
    title = build_title(brief)
    summary = build_summary(brief)
    body = build_body(brief, args.template)

    out = {
        'run_id': brief['run_id'],
        'stage': 'wechat_rewrite',
        'status': 'success',
        'generated_at': iso_now(),
        'template': args.template,
        'keyword': brief.get('keyword', ''),
        'title': title,
        'author': author,
        'summary': summary,
        'body_markdown': body,
        'source_brief': args.input,
        'cover_strategy': 'frontmatter_or_first_image',
        'need_open_comment': account_settings.get('need_open_comment', 1),
        'only_fans_can_comment': account_settings.get('only_fans_can_comment', 0),
        'wechat_account_alias': account_settings.get('alias', ''),
    }

    out_dir = ensure_dir(ROOT / 'data' / 'wechat-drafts')
    out_path = out_dir / f"{brief['run_id']}.{args.template}.json"
    write_json(out_path, out)
    append_stage_manifest(brief['run_id'], 'wechat-rewrite-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'input': args.input,
        'output': str(out_path),
        'template': args.template,
        'title': title,
    })
    print(out_path)


if __name__ == '__main__':
    main()
