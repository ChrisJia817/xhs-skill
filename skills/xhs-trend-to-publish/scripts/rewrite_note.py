import argparse
import random
from bootstrap import ROOT
from common import read_json, write_json, ensure_dir, iso_now, append_stage_manifest

THEME_VOICE = {
    'professional': {
        'title_suffix': '先把逻辑讲清楚',
        'intro_style': '稳健分析',
        'cta_tone': '理性讨论',
    },
    'default': {
        'title_suffix': '先把现实看清楚',
        'intro_style': '平衡表达',
        'cta_tone': '开放交流',
    },
    'sketch': {
        'title_suffix': '先看框架，再谈结论',
        'intro_style': '清单框架',
        'cta_tone': '一起补充',
    },
    'playful-geometric': {
        'title_suffix': '别急，先拆开看',
        'intro_style': '轻松直给',
        'cta_tone': '轻松互动',
    },
    'botanical': {
        'title_suffix': '慢一点看，会更清楚',
        'intro_style': '温和提醒',
        'cta_tone': '温柔交流',
    },
    'neo-brutalism': {
        'title_suffix': '有些话得说得直一点',
        'intro_style': '强观点表达',
        'cta_tone': '态度讨论',
    },
    'retro': {
        'title_suffix': '回头看，很多事早有信号',
        'intro_style': '复盘口吻',
        'cta_tone': '经验交流',
    },
    'terminal': {
        'title_suffix': '先看系统问题出在哪',
        'intro_style': '技术拆解',
        'cta_tone': '问题定位',
    },
}

TITLE_PATTERNS = {
    'risk': [
        '{keyword}别急着冲，这几个坑不先看清很容易白忙',
        '{keyword}看起来门槛低，但真正容易亏在这几步',
        '{keyword}不是不能碰，是很多人一上来就踩错了点',
    ],
    'trend': [
        '{keyword}现在还能做吗？我把难听的实话放前面',
        '{keyword}还能不能做，关键不是机会而是执行细节',
        '{keyword}现在还有机会，但真没想象中那么轻松',
    ],
    'generic': [
        '{keyword}值不值得做，先别急着下结论',
        '{keyword}这事到底能不能做，我更想先聊现实一点的部分',
        '{keyword}别光看表面热度，真正卡人的地方在后面',
    ],
}

THEME_INTROS = {
    'professional': [
        '如果只看表面热度，很容易判断失真。把链路拆开看，问题往往会更清楚。',
        '这件事真正值得讨论的，不是能不能做，而是成本、风险和执行条件是不是匹配。',
    ],
    'default': [
        '最近围绕“{keyword}”的讨论又多了起来，但热度归热度，真正决定结果的还是后面的细节。',
        '很多人看到这个方向会先看机会，我反而更想先聊聊它背后的代价和门槛。',
    ],
    'sketch': [
        '先别急着下结论，这件事可以先拆成几个部分看：机会、门槛、风险、执行。',
        '如果用框架去看“{keyword}”，很多模糊的地方其实会一下子清楚很多。',
    ],
    'playful-geometric': [
        '这事看着像很好上手，但真拆开看，坑和门槛其实一点都不少。',
        '别被表面那点轻松感骗了，很多难点只是没有在第一眼露出来。',
    ],
    'botanical': [
        '这类事情往往越着急越容易看偏，慢一点看，反而更容易看清值不值得做。',
        '很多时候不是你不够努力，而是你太早把一件事想成了简单模式。',
    ],
    'neo-brutalism': [
        '有些话不太好听，但这件事要是继续按“低门槛、快起量”的想法看，基本还会有人继续踩坑。',
        '这个方向不是不能做，但如果还拿旧红利思路去看，翻车几乎是迟早的事。',
    ],
    'retro': [
        '回头看，这类项目每一轮热起来时，信号其实都差不多，只是很多人总在同样的地方交学费。',
        '很多问题不是今天才出现，只是每次热度一上来，大家又会选择性忽略它。',
    ],
    'terminal': [
        '如果把这件事当成一个系统问题看，真正的瓶颈通常不在入口，而在后面的稳定性。',
        '表面上像是能不能开始的问题，实际上更像是链路里哪几个环节最容易失稳。',
    ],
}

ANGLE_THEME_MIDDLES = {
    '趋势判断型': {
        'professional': [
            ['先看结论，这个方向并没有彻底消失，但进入门槛已经从“会不会做”转向“能不能稳定做”。', '最近又热起来，更多是因为讨论声量回来了，不代表实际难度下降了。', '真正拉开差距的，还是选品、履约、售后和规则理解这些执行面。'],
            ['如果按业务链路看，这事现在更像一场精细化运营，而不是单纯的信息差游戏。', '所以别只看有没有机会，更要看自己是不是具备持续执行和纠错能力。', '很多人不是败在起点，而是败在把难度判断得太轻。'],
        ],
        'default': [
            ['说白了，这个方向不是完全不能做，但也早就不是“随便搬一搬就能出单”的阶段了。', '现在更吃执行细节：选品是不是稳，供应链是不是跟得上，售后能不能扛住，平台规则有没有认真看。', '很多新手真正卡住的，不是不会开店，而是低估了这件事对耐心和细节的要求。'],
            ['它不是没有机会，只是机会早就从“野蛮红利”变成了“细节红利”。', '以前很多人靠信息差就能试错，现在更考验你能不能把流程跑稳、把风险看清。', '所以问题从来不是“还能不能做”，而是你有没有能力把它做成一件长期能扛住的事。'],
        ],
        'sketch': [
            ['如果按框架拆，这类方向可以先看三件事：流量、履约、规则。', '流量决定有没有入口，履约决定能不能活下来，规则决定你能不能长期留在场上。', '只看前端机会、不看后端稳定，判断几乎一定会失真。'],
        ],
        'playful-geometric': [
            ['表面上看像还有戏，真拆开看，门槛一点都不低。', '能做不代表好做，更不代表适合急着找结果的人。', '很多坑不是突然出现的，只是你一开始没把它们当回事。'],
            ['它看起来像一条能快速上手的小路，真走进去才发现每一步都在考验耐心。', '很多人不是没机会，而是太想立刻看到结果，所以把真正该重视的细节都略过去了。', '所以别急着问好不好做，先问自己愿不愿意把麻烦都接住。'],
        ],
        'botanical': [
            ['它不是完全没机会，只是更适合慢慢做、稳稳做。', '如果一上来就把预期拉太高，后面反而更容易因为落差而焦虑。', '先把现实看清楚，再决定要不要投入，通常会更舒服一点。'],
            ['很多事情不是没有可能，只是不适合在着急的时候做决定。', '越想马上得到答案，越容易忽略那些真正会影响长期感受和结果的细节。', '所以先让自己慢一点，再去判断值不值得走下去。'],
        ],
        'neo-brutalism': [
            ['直接说，这个方向最大的问题不是能不能做，而是很多人到现在还在用过时的幻想看它。', '你以为机会还跟以前一样，实际上规则、成本和容错早就不是一个级别了。', '还想拿轻松心态进来的人，大概率还是会把学费交一遍。'],
        ],
        'retro': [
            ['回头看，每次这种方向重新热起来，外面最先被放大的，总是“还有没有机会”这类问题。', '但真正决定结果的那几件事，其实一直没变：规则、执行、心态、耐心。', '很多人不是没看见信号，而是每次都更愿意相信轻松版本的故事。'],
        ],
        'terminal': [
            ['如果按链路排查，这事最脆弱的部分通常不在入口，而在后端稳定性。', '入口看起来总能找到办法，但履约、售后、规则命中率这些地方才是真正的故障点。', '所以它不是“能不能起步”的问题，而是“系统能不能长期不失稳”的问题。'],
        ],
    },
    '避坑提醒型': {
        'professional': [
            ['先说最核心的风险：很多人会踩坑，不是因为不会操作，而是因为把风险成本漏算了。', '前端看着轻，后端却包含规则、时效、售后、利润波动等一整串变量。', '如果这些变量没有提前算清楚，后面翻车只是时间问题。'],
        ],
        'default': [
            ['最容易踩的，不是不会上架，也不是不会找品，而是刚开始就默认这事“低门槛、来钱快、风险小”。', '但现在平台规则越来越细，履约、售后、发货链路，哪个环节出问题都可能把店拖垮。', '如果只是被“轻资产”“不用囤货”打动，十有八九会在后面补学费。'],
            ['很多人刚进来时只盯着“前端成本低”，却没把售后、时效、违规和利润波动这些隐性成本算进去。', '表面看像是轻资产，实际更像把风险拆散了，分摊到每一个执行环节里。', '只要其中一个环节不稳，前面看起来省下的钱，后面往往会用别的方式还回去。'],
        ],
        'sketch': [
            ['如果按避坑框架看，最该先排查的是三类风险：规则风险、履约风险、预期风险。', '规则风险决定会不会违规，履约风险决定能不能稳定交付，预期风险决定你会不会因为误判而硬扛。', '很多翻车其实不是单点失误，而是三类风险同时被低估。'],
        ],
        'playful-geometric': [
            ['很多坑看起来不大，真踩进去就会发现每个都很费钱费心。', '最麻烦的地方不是“不会做”，而是你以为简单，结果每一步都在补作业。', '所以这类事最怕的不是慢，是轻敌。'],
            ['有些坑乍一看像小失误，真累积起来会把人直接拖崩。', '你以为只是少想了一步，结果后面会发现其实每一步都连着代价。', '所以别急着冲，先把最容易翻车的地方找出来，真的能省很多事。'],
        ],
        'botanical': [
            ['如果你是新手，最先要保护的不是速度，而是自己的判断。', '很多坑并不是看不见，只是你太急着开始，所以没留时间把它们想明白。', '慢一点进入，反而会少掉很多后面补不回来的损耗。'],
            ['很多损耗其实不是突然发生的，而是前面忽略得太久，后来一起找上门。', '如果能给自己多一点时间，把风险想得细一点，通常会轻松很多。', '所以避坑有时候不是学更多技巧，而是先学会不着急。'],
        ],
        'neo-brutalism': [
            ['说得难听一点，很多人根本不是不会做，而是从第一天就想用侥幸心态绕过代价。', '轻资产不等于低风险，不囤货也不等于不用承担后果。', '如果连这一层都想不明白，后面踩坑基本是必然。'],
        ],
        'retro': [
            ['每次看这类项目翻车，原因其实都差不多：轻信、心急、预期过高。', '这些坑不是今年才有，过去有，现在有，后面大概率也还会有。', '区别只是有人记住了教训，有人每次都觉得这回能例外。'],
        ],
        'terminal': [
            ['如果按故障排查看，最容易出问题的节点通常是规则命中、时效控制和售后承压。', '这些地方只要有一个长期失稳，前面看起来顺的链路就会开始连锁出错。', '所以避坑不是记几个词，而是先定位哪个环节最容易把系统拖垮。'],
        ],
    },
    '步骤拆解型': {
        'professional': [
            ['如果真的要开始，最合理的顺序一定不是上来就冲规模，而是先做小样本验证。', '先验证供给、规则理解和售后承接，再考虑是否值得继续加码。', '把顺序搞反，很多后面的成本都会成倍放大。'],
        ],
        'default': [
            ['如果真要开始，第一步不是盲目上手，而是先确认目标到底是什么。', '开始前至少要准备三样东西：稳定的供给、基本规则认知、可承受的售后预期。', '真正执行时，顺序最好是：先小范围验证，再优化流程，最后才考虑放大。'],
            ['最常见的错误，不是做得慢，而是验证还没完成就急着把规模拉起来。', '很多问题在小阶段其实都能暴露，但只要心态一急，就会把“验证”直接跳成“扩张”。', '这也是为什么很多人不是不会做，而是把顺序做反了。'],
        ],
        'sketch': [
            ['如果按步骤看，可以拆成四段：目标确认、条件准备、小范围验证、放大决策。', '每一步都对应一个判断：值不值得做、能不能开始、能不能稳定、该不该放大。', '顺序清楚以后，很多焦虑其实都会少很多。'],
        ],
        'playful-geometric': [
            ['别一上来就想一步到位，这类事最怕的就是还没摸清路就开始猛冲。', '先试、再改、再放大，听着慢，但反而更省事。', '很多人把自己做累，不是因为流程复杂，而是因为顺序乱了。'],
            ['看着像是多走了几步，实际上是在帮你少返工很多次。', '先摸清楚、再一点点推，往往比一开始就想跑快更轻松。', '顺序稳了，很多原本让人头大的问题其实都会变小。'],
        ],
        'botanical': [
            ['如果你准备开始，先给自己留一点试错空间。', '不用急着证明自己能不能一把做成，先把每一步走顺会更重要。', '节奏稳一点，后面反而更容易真正做长。'],
            ['有些步骤看起来慢，其实是在替后面省掉很多慌乱。', '如果能允许自己先小范围试一试，再慢慢往前推，通常会更安心。', '把节奏放稳，不代表保守，很多时候反而是更长久的开始。'],
        ],
        'neo-brutalism': [
            ['流程上最蠢的一种做法，就是验证没做完就开始想放大。', '你以为自己是在提速，实际上是在把还没暴露的问题成倍放大。', '顺序一旦错了，后面的努力大概率都在给前面的冲动买单。'],
        ],
        'retro': [
            ['回过头看，很多做成的人并不是动作最快，而是顺序最稳。', '目标、准备、验证、放大，这几个步骤听着老套，但老套往往就是因为它真有用。', '越是看起来简单的事，越要防止自己在顺序上偷懒。'],
        ],
        'terminal': [
            ['如果按执行链路拆，这套动作至少要先过四个节点：目标、输入、验证、扩容。', '每个节点都应该有明确通过条件，否则你只是把不确定性往后推。', '系统化一点做，速度未必更慢，但事故率通常会低很多。'],
        ],
    },
}

CLOSE_PATTERNS = {
    'risk': [
        '所以真想入场的话，先别急着问怎么起店，先把规则、利润和售后成本算明白。',
        '真要开始之前，先把最容易被忽略的坑列出来，比盲目冲进去更有用。',
    ],
    'trend': [
        '如果你现在还在观望，我反而建议先把预期放低一点，先学会活下来，再考虑放大。',
        '所以别急着只问有没有机会，先确认自己能不能把执行这件事长期扛住。',
    ],
    'generic': [
        '别急着冲，先把关键问题想明白，再决定值不值得投入。',
        '先想清楚自己要承担什么，再决定要不要进场，通常比上来就做更重要。',
    ],
}

THEME_CTA_SUFFIX = {
    'professional': '欢迎从成本、风险和执行三个角度聊聊。',
    'default': '你怎么看，也欢迎说说。',
    'sketch': '如果你愿意，也可以按“机会 / 风险 / 执行”来补充。',
    'playful-geometric': '要不要一起把这事拆得更明白一点？',
    'botanical': '如果你也在犹豫，不妨慢慢聊。',
    'neo-brutalism': '如果你不同意，也欢迎直接说观点。',
    'retro': '你有没有见过类似的老问题反复出现？',
    'terminal': '如果按链路看，你觉得最容易失稳的是哪一段？',
}

CTA_PATTERNS = {
    'risk': [
        '你见过最离谱的无货源坑，是什么？',
        '如果让你提醒新手一句，你最想劝他们先避开什么？',
    ],
    'trend': [
        '你觉得现在做无货源，最大的门槛是在选品、执行，还是规则？',
        '如果现在重新开始，你觉得最该先补的是哪个环节？',
    ],
    'generic': [
        '如果是你，会先补哪一块能力？',
        '站在现在这个阶段看，你觉得最容易低估的成本是什么？',
    ],
}


def pick(options: list, seed_text: str):
    rng = random.Random(seed_text)
    return options[rng.randrange(len(options))]


def normalize_keyword(keyword: str) -> str:
    return (keyword or '').strip()


def brief_to_scored_like(brief: dict) -> dict:
    keyword = normalize_keyword(brief.get('keyword', ''))
    pain_points = brief.get('pain_points') or []
    common_questions = brief.get('common_questions') or []
    selected = brief.get('selected') or []
    evidence = brief.get('evidence') or []
    evidence_by_id = {}
    for evidence_item in evidence:
        if not isinstance(evidence_item, dict):
            continue
        evidence_by_id[str(evidence_item.get('source_note_id') or '')] = evidence_item
    candidates = []
    for index, item in enumerate(selected[:3]):
        raw = item.get('raw') or {}
        raw_item = raw if isinstance(raw, dict) else {}
        item_id = str(item.get('item_id') or raw_item.get('note_id') or '')
        evidence_item = evidence_by_id.get(item_id, {})
        title = item.get('title') or raw_item.get('title') or f'{keyword}值得做吗'
        summary_parts = []
        if index < len(common_questions):
            summary_parts.append(common_questions[index])
        if index < len(pain_points):
            summary_parts.append(pain_points[index])
        summary = '；'.join(part for part in summary_parts if part) or item.get('summary') or raw_item.get('summary') or title
        angles = raw_item.get('angles') or item.get('angles') or brief.get('platform_angles', {}).get('xhs') or ['趋势判断型']
        candidates.append({
            'note_id': item_id or f'brief-{index + 1}',
            'title': title,
            'url': raw_item.get('url') or '',
            'author': item.get('author') or raw_item.get('author') or '',
            'publish_time': item.get('publish_time') or brief.get('publish_time') or '',
            'like_count': item.get('like_count', 0),
            'comment_count': item.get('comment_count', 0),
            'collect_count': item.get('collect_count', 0),
            'summary': summary,
            'comment_signals': common_questions[:3],
            'source_type': f"brief-{item.get('source_platform') or 'merged'}",
            'source_platform': item.get('source_platform') or evidence_item.get('source_type') or '',
            'evidence_source_type': evidence_item.get('source_type') or '',
            'evidence_title': evidence_item.get('title') or title,
            'score': raw_item.get('score') or {'total': 0},
            'decision': raw_item.get('decision') or 'keep',
            'angles': angles,
        })
    return {
        'run_id': brief['run_id'],
        'stage': 'score',
        'status': 'success',
        'generated_at': brief.get('generated_at') or iso_now(),
        'keyword': keyword,
        'publish_time': brief.get('publish_time', ''),
        'source_input': brief.get('source_input', ''),
        'candidate_count': len(candidates),
        'selected_count': len(candidates),
        'selection_mode': 'brief-adapted',
        'candidates': candidates,
        'selected': candidates,
    }


def get_theme_voice(theme: str) -> dict:
    return THEME_VOICE.get(theme or 'default', THEME_VOICE['default'])


def classify_angle(source_title: str, item: dict) -> tuple[str, str]:
    source_title = (source_title or '').strip()
    angle = item.get('angles')[0] if item.get('angles') else '趋势判断型'
    preferred_angle = item.get('preferred_angle') or ''
    if preferred_angle:
        angle = preferred_angle
    if angle == '避坑提醒型' or any(flag in source_title for flag in ['避坑', '骗局', '打击', '违规', '风险']):
        return 'risk', '避坑提醒型'
    if angle == '步骤拆解型':
        return 'generic', '步骤拆解型'
    if any(flag in source_title for flag in ['能不能做', '还能做吗']) or angle == '趋势判断型':
        return 'trend', '趋势判断型'
    return 'generic', angle


def get_middle_variants(angle_name: str, theme: str, lane: str):
    theme_bucket = ANGLE_THEME_MIDDLES.get(angle_name, {})
    if theme in theme_bucket:
        return theme_bucket[theme]
    if 'default' in theme_bucket:
        return theme_bucket['default']
    if lane == 'risk':
        return RISK_MIDDLES
    if lane == 'trend':
        return TREND_MIDDLES
    return GENERIC_MIDDLES


def build_title(keyword: str, item: dict, lane: str, theme: str) -> str:
    keyword = normalize_keyword(keyword)
    seed = f"title|{keyword}|{item.get('title', '')}|{lane}|{theme}"
    title = pick(TITLE_PATTERNS[lane], seed).format(keyword=keyword)
    theme_suffix = get_theme_voice(theme).get('title_suffix', '')
    if theme in ['neo-brutalism', 'terminal'] and theme_suffix:
        max_base_len = 20
        if len(title) > max_base_len:
            title = title[:max_base_len].rstrip('，。！？；：、—- ')
        return f"{title}｜{theme_suffix}"
    return title


def build_hashtags(keyword: str, item: dict) -> list[str]:
    base = ['小红书运营', '电商', '副业']
    corpus = '\n'.join([
        keyword or '',
        item.get('title') or '',
        item.get('summary') or '',
    ])
    if '无货源' in corpus:
        base.extend(['无货源', '电商避坑'])
    if any(x in corpus for x in ['新手', '小白', '入门']):
        base.append('新手入门')
    if any(x in corpus for x in ['风险', '避坑', '违规']):
        base.append('避坑指南')
    if keyword:
        base.append(keyword)

    seen = set()
    out = []
    for tag in base:
        clean = (tag or '').strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out[:8]


def join_hashtags(tags: list[str]) -> str:
    return ' '.join(f"#{tag}" for tag in tags if tag)


def build_body(keyword: str, item: dict, hashtags: list[str], lane: str, angle_name: str, theme: str):
    keyword = normalize_keyword(keyword)
    title_seed = f"body|{keyword}|{item.get('title', '')}|{lane}|{theme}|{angle_name}"
    theme_intro_pool = THEME_INTROS.get(theme, THEME_INTROS['default'])
    intro = pick(theme_intro_pool, title_seed + '|theme-intro').format(keyword=keyword)

    middle_variants = get_middle_variants(angle_name, theme, lane)
    middle = pick(middle_variants, title_seed + '|middle')

    close = pick(CLOSE_PATTERNS[lane], title_seed + '|close')
    cta = pick(CTA_PATTERNS[lane], title_seed + '|cta')
    cta_suffix = THEME_CTA_SUFFIX.get(theme, THEME_CTA_SUFFIX['default'])
    body = '\n\n'.join([intro] + middle + [close, join_hashtags(hashtags)])
    themed_cta = f"{cta} {cta_suffix}".strip()
    return body, themed_cta, angle_name


def build_body_from_brief(keyword: str, item: dict, brief_context: dict, hashtags: list[str], lane: str, angle_name: str, theme: str):
    keyword = normalize_keyword(keyword)
    title_seed = f"brief-body|{keyword}|{item.get('title', '')}|{lane}|{theme}|{angle_name}"
    theme_intro_pool = THEME_INTROS.get(theme, THEME_INTROS['default'])
    intro = pick(theme_intro_pool, title_seed + '|theme-intro').format(keyword=keyword)

    pain_points = brief_context.get('pain_points') or []
    common_questions = brief_context.get('common_questions') or []
    evidence_items = brief_context.get('evidence') or []
    xhs_titles = [e.get('title', '') for e in evidence_items if e.get('source_type') == 'xhs' and e.get('title')][:2]
    dy_titles = [e.get('title', '') for e in evidence_items if e.get('source_type') == 'douyin' and e.get('title')][:2]
    evidence_titles = [e.get('title', '') for e in evidence_items if e.get('title')][:3]
    evidence_line = '、'.join(evidence_titles) if evidence_titles else (item.get('title') or keyword)

    first_question = common_questions[0] if common_questions else f'{keyword}这个方向到底值不值得投入？'
    second_question = common_questions[1] if len(common_questions) > 1 else ''
    first_pain = pain_points[0] if pain_points else f'很多人关注{keyword}，但缺少可执行、可判断的落地方案。'
    second_pain = pain_points[1] if len(pain_points) > 1 else ''

    platform_line = ''
    if xhs_titles and dy_titles:
        platform_line = f'放在一起看，这些样本虽然表达方式不同，但最后都在把同一类问题不断放大：{first_question}'
    elif xhs_titles:
        platform_line = f'把这批样本放在一起看，会发现大家兜兜转转，最后其实都在问同一个问题：{first_question}'
    elif dy_titles:
        platform_line = f'这些高热样本看起来各讲各的，但真正被反复放大的，还是同一类决策焦虑：{first_question}'

    middle = [
        f'这次把不同平台里围绕“{keyword}”的内容放在一起看，反复出现的核心问题其实很集中：{first_question}',
        f'很多人真正卡住的点，不是信息不够，而是{first_pain}',
    ]
    if second_pain:
        middle.append(f'再往下拆一步，会发现第二层焦虑通常是：{second_pain}')
    if second_question:
        middle.append(f'而且当讨论继续往下走时，大家真正会追问的，往往是：{second_question}')
    if platform_line:
        middle.append(platform_line)
    if angle_name == '避坑提醒型':
        middle.append('这也说明，做成避坑提醒型内容时，重点不该放在吓人结论，而是要把“到底哪里最容易翻车”拆得足够具体。')
    elif angle_name == '步骤拆解型':
        middle.append('如果要把这类主题写成步骤拆解型内容，重点应该是把判断顺序、起步动作和最小验证讲清楚，而不是直接给结论。')
    else:
        middle.append('所以这类内容改写成小红书时，不该只重复“有机会”或“别焦虑”，而是要把真正影响行动决策的那一层说透。')
    middle.append(f'从样本里看，不管是 {evidence_line}，本质上都在指向同一个现实：热度可以很高，但真正决定结果的还是判断和执行。')

    close = pick(CLOSE_PATTERNS[lane], title_seed + '|close')
    cta = pick(CTA_PATTERNS[lane], title_seed + '|cta')
    cta_suffix = THEME_CTA_SUFFIX.get(theme, THEME_CTA_SUFFIX['default'])
    body = '\n\n'.join([intro] + middle + [close, join_hashtags(hashtags)])
    themed_cta = f"{cta} {cta_suffix}".strip()
    return body, themed_cta, angle_name


def score_draft_quality(draft: dict) -> dict:
    title = draft.get('title') or ''
    body = draft.get('body') or ''
    hashtags = draft.get('hashtags') or []
    angle = draft.get('angle') or ''
    theme = draft.get('theme') or 'default'

    title_score = 15 if 12 <= len(title) <= 24 else (10 if len(title) >= 8 else 6)
    body_paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
    body_score = min(30, 8 + len(body_paragraphs) * 4 + min(10, len(body) // 45))
    hashtag_score = min(12, len(hashtags) * 2 + (4 if body.splitlines() and body.splitlines()[-1].startswith('#') else 0))
    angle_score = 12 if angle in ['趋势判断型', '避坑提醒型', '步骤拆解型'] else 8

    theme_markers = {
        'sketch': ['框架', '拆成', '归纳'],
        'neo-brutalism': ['直接说', '难听', '侥幸'],
        'retro': ['回头看', '以前', '每次'],
        'terminal': ['链路', '系统', '节点', '失稳'],
        'botanical': ['慢一点', '温和', '舒服'],
    }
    theme_alignment_score = 10
    if any(marker in body for marker in theme_markers.get(theme, [])):
        theme_alignment_score = 16
    humanized_score = 16 if any(x in body for x in ['说白了', '我反而', '很多人', '先别急着', '链路', '框架']) else 10
    total = min(100, title_score + body_score + hashtag_score + angle_score + humanized_score + theme_alignment_score)
    return {
        'title_score': title_score,
        'body_score': body_score,
        'hashtag_score': hashtag_score,
        'angle_score': angle_score,
        'humanized_score': humanized_score,
        'theme_alignment_score': theme_alignment_score,
        'total': total,
    }


def rewrite_one(keyword: str, item: dict, draft_index: int, theme: str, brief_context: dict | None = None):
    source_title = item.get('title') or ''
    if brief_context and not item.get('preferred_angle'):
        preferred_angles = brief_context.get('platform_angles', {}).get('xhs') or []
        if preferred_angles:
            item = {**item, 'preferred_angle': preferred_angles[min(draft_index, len(preferred_angles) - 1)]}
    lane, angle_name = classify_angle(source_title, item)
    hashtags = build_hashtags(keyword, item)
    title = build_title(keyword, item, lane, theme)
    if brief_context:
        body, cta, angle = build_body_from_brief(keyword, item, brief_context, hashtags, lane, angle_name, theme)
    else:
        body, cta, angle = build_body(keyword, item, hashtags, lane, angle_name, theme)
    draft = {
        'draft_index': draft_index,
        'source_note_id': item.get('note_id', ''),
        'source_title': source_title,
        'angle': angle,
        'theme': theme,
        'title': title,
        'body': body,
        'hashtags': hashtags,
        'cta': cta,
        'rewrite_meta': {
            'lane': lane,
            'theme': theme,
            'theme_voice': get_theme_voice(theme),
            'generated_at': iso_now(),
        },
    }
    draft['quality'] = score_draft_quality(draft)
    return draft


def select_best_draft(drafts: list[dict]) -> tuple[int, dict]:
    ranked = sorted(
        enumerate(drafts),
        key=lambda pair: (
            pair[1].get('quality', {}).get('total', 0),
            pair[1].get('quality', {}).get('theme_alignment_score', 0),
            len(pair[1].get('hashtags', [])),
            len(pair[1].get('body', '')),
        ),
        reverse=True,
    )
    best_index, best_draft = ranked[0]
    return best_index, {
        'selected_index': best_index,
        'selected_title': best_draft.get('title', ''),
        'selected_quality': best_draft.get('quality', {}),
        'ranked_indexes': [idx for idx, _ in ranked],
    }


def choose_best_output(score_drafts: list[dict], brief_drafts: list[dict]) -> tuple[list[dict], dict]:
    candidates = []
    if score_drafts:
        idx, meta = select_best_draft(score_drafts)
        candidates.append({'mode': 'score', 'index': idx, 'meta': meta, 'drafts': score_drafts})
    if brief_drafts:
        idx, meta = select_best_draft(brief_drafts)
        candidates.append({'mode': 'brief', 'index': idx, 'meta': meta, 'drafts': brief_drafts})
    ranked = sorted(
        candidates,
        key=lambda item: (
            item['meta'].get('selected_quality', {}).get('total', 0),
            item['meta'].get('selected_quality', {}).get('theme_alignment_score', 0),
            1 if item['mode'] == 'brief' else 0,
        ),
        reverse=True,
    )
    winner = ranked[0]
    return winner['drafts'], {
        'winner_mode': winner['mode'],
        'winner_index': winner['index'],
        'winner_quality': winner['meta'].get('selected_quality', {}),
        'candidates': [
            {
                'mode': item['mode'],
                'selected_index': item['index'],
                'selected_quality': item['meta'].get('selected_quality', {}),
            }
            for item in ranked
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--theme', default='professional')
    parser.add_argument('--source-format', default='score', choices=['score', 'brief'])
    args = parser.parse_args()

    if args.source_format == 'brief':
        brief = read_json(args.input)
        data = brief_to_scored_like(brief)
        brief_context = brief
    else:
        data = read_json(args.input)
        brief_context = None
    selected = data.get('selected', [])
    if not selected:
        append_stage_manifest(data.get('run_id', 'unknown'), 'rewrite', {
            'status': 'failed',
            'finished_at': iso_now(),
            'input': args.input,
            'reason': 'no_selected_candidates',
        })
        raise SystemExit('No selected candidates available for rewrite.')

    score_drafts = [rewrite_one(data.get('keyword', ''), item, idx, args.theme) for idx, item in enumerate(selected)]
    brief_drafts = [rewrite_one(data.get('keyword', ''), item, idx, args.theme, brief_context=brief_context) for idx, item in enumerate(selected)] if brief_context else []
    drafts, comparison_meta = choose_best_output(score_drafts, brief_drafts) if brief_context else (score_drafts, {'winner_mode': 'score-only'})
    best_draft_index, selection_meta = select_best_draft(drafts)
    out = {
        'run_id': data['run_id'],
        'stage': 'rewrite',
        'status': 'success',
        'generated_at': iso_now(),
        'keyword': data['keyword'],
        'theme': args.theme,
        'source_input': args.input,
        'draft_count': len(drafts),
        'best_draft_index': best_draft_index,
        'selection_meta': selection_meta,
        'comparison_meta': comparison_meta,
        'drafts': drafts,
    }
    out_dir = ensure_dir(ROOT / 'data' / 'drafts')
    out_path = out_dir / f"{data['run_id']}.json"
    write_json(out_path, out)
    append_stage_manifest(data['run_id'], 'rewrite-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'input': args.input,
        'output': str(out_path),
        'theme': args.theme,
        'draft_count': len(drafts),
        'best_draft_index': best_draft_index,
        'selection_meta': selection_meta,
        'comparison_meta': comparison_meta,
    })
    print(out_path)


if __name__ == '__main__':
    main()
