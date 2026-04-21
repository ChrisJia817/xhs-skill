import argparse
from bootstrap import ROOT
from common import read_json, ensure_dir, append_stage_manifest, iso_now

MIN_TOTAL_CARDS = 4
MIN_CONTENT_CARDS = 2

THEME_CARD_VOICE = {
    'professional': {
        'subtitle': '把逻辑拆开看',
        'bridge': '换个更稳的说法就是：',
        'outro_prefix': '最后只提醒一句：',
    },
    'default': {
        'subtitle': '先把现实看明白',
        'bridge': '说得再直白一点：',
        'outro_prefix': '最后想留一句：',
    },
    'sketch': {
        'subtitle': '先看框架',
        'bridge': '如果按框架归纳，大概就是：',
        'outro_prefix': '最后做个收束：',
    },
    'playful-geometric': {
        'subtitle': '别急，先拆开看',
        'bridge': '说白了就是：',
        'outro_prefix': '最后再补一句：',
    },
    'botanical': {
        'subtitle': '慢一点看更清楚',
        'bridge': '更温和一点讲，其实就是：',
        'outro_prefix': '最后轻轻提醒一句：',
    },
    'neo-brutalism': {
        'subtitle': '这话得说直一点',
        'bridge': '直接一点说：',
        'outro_prefix': '最后就一句重话：',
    },
    'retro': {
        'subtitle': '回头看会更明白',
        'bridge': '如果拿过往经验对照，其实就是：',
        'outro_prefix': '最后回头看一句：',
    },
    'terminal': {
        'subtitle': '先定位问题',
        'bridge': '如果按链路拆解，问题就在这：',
        'outro_prefix': '最后输出一个结论：',
    },
}

ANGLE_CARD_TEMPLATES = {
    '趋势判断型': {
        'core': [
            '先给结论：{keyword}不是完全没机会，\n但它早就不是靠随便搬一搬就能跑起来的阶段。',
            '为什么最近又有人开始讨论它？\n本质上不是门槛变低了，\n而是很多人又把它想成了低成本快启动。',
            '这段时间最明显的变化有三个：\n规则更细、执行更重、容错更低。',
            '所以它更适合愿意慢慢打磨流程的人，\n不太适合只想找捷径、短期冲结果的人。',
        ],
        'outro': '如果你现在还在看这个方向，\n先别急着问有没有机会，\n先问自己能不能把执行扛住。',
    },
    '避坑提醒型': {
        'core': [
            '最容易踩的误区，不是不会做，\n而是一开始就默认这事门槛低、风险小、来钱快。',
            '很多人会翻车，往往不是因为起步慢，\n而是把隐性成本和规则风险看得太轻。',
            '这类项目真正难的地方，\n常常不在前台动作，而在履约、售后、时效和长期稳定。',
            '如果你是新手，最现实的建议不是立刻开冲，\n而是先把规则、利润和最坏情况算明白。',
        ],
        'outro': '看清坑，比急着进场更重要。\n少交一点学费，往往比多学几个技巧更值。',
    },
    '步骤拆解型': {
        'core': [
            '如果真要开始，第一步不是盲目上手，\n而是先确认目标到底是什么。',
            '开始前至少要准备三样东西：\n稳定的供给、基本规则认知、可承受的售后预期。',
            '真正执行时，顺序最好是：\n先小范围验证，再优化流程，最后才考虑放大。',
            '最常见的错误，不是做得慢，\n而是验证还没完成就急着把规模拉起来。',
        ],
        'outro': '流程跑顺之前，别急着谈放大。\n先做成一遍，再想怎么做快。',
    },
}

THEME_ANGLE_CARD_VARIANTS = {
    '趋势判断型': {
        'professional': [
            '先看结论：这已经不是一个单纯拼速度的方向，\n而是更考验链路稳定性的方向。',
            '如果只看热度，会误以为门槛下降了；\n但拆到执行层，难点其实比以前更清楚。',
            '这类内容最值得看的是变化信号：\n规则、履约、售后，哪个都不能轻看。',
            '真正适合入场的人，往往不是最着急的人，\n而是愿意把流程一点点磨稳的人。',
        ],
        'default': [
            '先把结论说清楚：这方向不是没机会，\n只是已经不适合拿轻松预期去做了。',
            '现在最明显的变化，不只是热度，\n而是执行要求比很多人想的高得多。',
            '真正决定结果的，还是规则理解、履约稳定和长期细节。',
            '所以值不值得做，关键要看你能不能把这些麻烦都接住。',
        ],
        'sketch': [
            '先把结论放在前面：这事要先看框架，\n不是先看情绪。',
            '框架上可以拆成三块：入口、执行、留存。\n只看入口，判断一定会偏。',
            '真正变化最大的部分，不只是流量，\n而是执行成本和风险暴露速度。',
            '所以适不适合做，关键要看你能不能把这三块同时兜住。',
        ],
        'playful-geometric': [
            '看起来像还有路，真走进去就会发现路没你想得那么平。',
            '门槛不是没有，只是很多时候被“好像能做”这层感觉盖住了。',
            '真正在拉开差距的，从来不是谁先冲，而是谁能把那些麻烦细节接住。',
            '所以别急着判断它好不好做，先想清楚你愿不愿意跟这些麻烦长期相处。',
        ],
        'botanical': [
            '这件事不是完全没有可能，只是更适合慢慢看、慢慢做。',
            '很多时候一着急，就会把那些真正重要的难点看得太轻。',
            '可一旦走进去，最先考验的反而不是热情，而是稳定和耐心。',
            '所以先让自己安静一点，再去判断它值不值得投入，通常会更准。',
        ],
        'neo-brutalism': [
            '直接说结论：这方向没死，但轻松版本早就死了。',
            '很多人以为现在还能复制以前的路子，\n问题是环境和容错已经不是以前那个环境。',
            '变化不是一点点，是整条链路都更容易把侥幸心态放大成事故。',
            '如果还只想走捷径，那这事对你来说就不叫机会，叫延迟爆雷。',
        ],
        'retro': [
            '回头看，结论其实不难下：它不是突然变难，\n而是很多老问题一直都在。',
            '每一轮热起来时，总有人以为门槛回到了从前，\n但最后吃亏的地方几乎都一样。',
            '真正值得记住的变化，不只是平台规则，\n还有大家对难度的错觉越来越大。',
            '所以适不适合做，还是得回到老问题：你能不能长期把基本动作做稳。',
        ],
        'terminal': [
            '如果按系统视角看，先下一个结论：\n这个方向的瓶颈不在入口，而在后端稳定。',
            '从链路看，热度回升不等于系统变简单，\n只代表更多人重新把请求打进来了。',
            '当前变化最大的，不是表面机会，而是规则命中率和履约容错。',
            '所以真正适配的人，是能把多个节点一起压稳的人，不是只会起步的人。',
        ],
    },
    '避坑提醒型': {
        'professional': [
            '先看误区本身：风险不在“会不会做”，\n而在有没有把隐性成本纳入判断。',
            '很多人踩坑，不是因为动作错，而是因为评估模型从第一天就漏项。',
            '真正的风险点通常不显眼，但一旦叠加，\n就会直接把利润和节奏一起拖垮。',
            '所以最现实的建议从来不是快，而是先把坑位盘清楚。',
        ],
        'default': [
            '最容易忽略的坑，往往不是表面动作，\n而是后面那些看起来不急、其实很伤的细节。',
            '很多人会翻车，不是因为不会开始，\n而是因为把风险想得太轻，把代价想得太晚。',
            '真正难受的地方通常都在后面：规则、售后、时效、利润。',
            '所以越想少踩坑，越应该先把现实问题一件件想明白。',
        ],
        'sketch': [
            '如果按避坑框架拆，这类问题通常有三层：\n认知误区、执行误区、后果误区。',
            '认知误区让你低估门槛，执行误区让你放大问题，\n后果误区让你以为还能补回来。',
            '很多人不是只踩一个坑，而是三层一起踩。',
            '所以越想避坑，越要先把结构看明白。',
        ],
        'playful-geometric': [
            '很多坑看着像小坑，真掉进去才发现每个都挺费劲。',
            '最容易出事的地方，不是不会，而是以为“这一步应该没事”。',
            '结果就是前面图省事，后面全在补救。',
            '所以先把最烦的地方找出来，真的比闷头冲省力。',
        ],
        'botanical': [
            '有些坑不是特别隐蔽，只是你太着急的时候，很容易选择先不看。',
            '可越是这样，后面真正让人难受的损耗反而越容易累积起来。',
            '如果能先慢一点，把最不舒服的风险提前想一遍，后面通常会稳很多。',
            '所以避坑有时候不是学会更快，而是允许自己先停一下。',
        ],
        'neo-brutalism': [
            '把话说死一点：很多坑不是藏得深，\n而是你从一开始就不想认真看。',
            '轻资产不等于不用交代价，低门槛也不等于你能安全上桌。',
            '真正会翻车的人，往往都是先把风险当空气，\n后面再被现实一拳打醒。',
            '所以别问坑在哪，先问自己是不是又准备靠侥幸混过去。',
        ],
        'retro': [
            '回头看，很多坑其实都不新鲜，\n只是每一轮都会换个说法重新出现。',
            '有人把它叫机会，有人把它叫捷径，\n但最后踩进去时，代价通常也还是那些老代价。',
            '问题从来不是坑有没有更新，\n而是人会不会在旧坑前面再次失忆。',
            '所以真想避坑，先把以前那些教训捡回来。',
        ],
        'terminal': [
            '如果按故障排查思路看，这类坑基本都属于“前面正常、后面连锁出错”。',
            '问题不在某一个动作，而在多个节点一起失控：规则、时效、售后、利润。',
            '只看单点会觉得小事，连起来看才知道它为什么致命。',
            '所以避坑最有效的方法，不是背词，而是先定位哪段链路最容易把你拖死。',
        ],
    },
    '步骤拆解型': {
        'professional': [
            '如果按正确顺序做，第一步永远是确认目标，\n而不是先把动作堆起来。',
            '第二步要确认输入条件够不够：供给、规则理解、售后承压。',
            '第三步才是小范围验证，\n用最小成本把不确定性先打出来。',
            '最后再谈放大，否则你只是把未验证的问题扩散。',
        ],
        'default': [
            '这类事最怕的不是不会做，而是顺序一乱，后面全在返工。',
            '先确认目标，再准备条件，再小范围验证，最后才考虑是不是值得放大。',
            '很多问题并不是后面突然冒出来的，而是前面该确认的东西根本没确认。',
            '所以步骤真正的价值，不是让你看起来专业，而是帮你少走弯路。',
        ],
        'sketch': [
            '这类动作最适合按框架走：\n目标 → 条件 → 验证 → 放大。',
            '每一步都要有通过条件，\n否则你只是看起来在推进，实际上在跳步。',
            '很多人做乱，不是因为不会，而是因为没把顺序写清楚。',
            '顺序一旦清楚，很多焦虑自然就会下降。',
        ],
        'playful-geometric': [
            '很多人一上来就想快，结果最后反而更慢。',
            '先试一下、再修一下、再推大一点，其实比一步冲到底轻松得多。',
            '顺序对了，很多复杂事都会变简单。',
            '顺序乱了，再简单的事也能把人做烦。',
        ],
        'botanical': [
            '如果你准备开始，最好的节奏不是快，而是稳。',
            '一步一步把目标、准备、验证和放大理顺，比急着证明自己更重要。',
            '很多慌张其实都来自前面跳步，后面只能一直补。',
            '所以允许自己慢一点，往往反而更容易把事情做长。',
        ],
        'neo-brutalism': [
            '如果你打算上来就放大，那这套步骤对你基本等于白看。',
            '真正该做的是先验证，再修正，再扩张，\n不是一边心里没底一边硬冲规模。',
            '很多人把自己做崩，不是步骤太复杂，\n而是嫌步骤太慢，于是把该做的全跳了。',
            '顺序错了，后面所有努力都只是在替冲动擦屁股。',
        ],
        'retro': [
            '回头看，很多真正做成的人都不神秘，\n只是他们老老实实把该走的顺序走完了。',
            '目标、准备、验证、放大，这几个步骤听着土，\n但土往往就意味着经得住反复验证。',
            '越是看起来简单的项目，越容易让人跳步。',
            '所以别怕慢，怕的是你用快把自己送进返工。',
        ],
        'terminal': [
            '如果按执行链路设计，这套步骤至少要先过四个节点：目标、输入、验证、扩容。',
            '任何一个节点没有通过条件，\n后面都可能把小问题放成系统故障。',
            '所以步骤的价值不是流程感，而是把不确定性锁在前面。',
            '节点稳定了，再追求速度，才不是拿事故换效率。',
        ],
    },
}

GENERIC_FILLERS = [
    '别只盯着表面热度，\n真正拉开差距的，往往是后面的执行细节。',
    '很多人不是方向错了，\n而是低估了把一件事长期做稳的难度。',
    '如果现在还在观望，\n先把预期放低一点，反而更容易看清现实。',
]

MARKDOWN_FALLBACK_CARDS = {
    'summary': '总结一下：\n这件事不是不能做，\n而是不能拿过于轻松的预期去做。',
    'risk': '真正该提前想到的，\n不是能不能开始，\n而是出了问题后你能不能扛住。',
    'cta': '如果你也在观察这个方向，\n最想先确认的一件事是什么？',
}


def clean_for_cards(text: str) -> str:
    text = (text or '').strip()
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        lines.append(line)
    return '\n'.join(lines).strip()


def split_paragraphs(text: str) -> list[str]:
    text = clean_for_cards(text)
    if not text:
        return []
    return [part.strip() for part in text.split('\n\n') if part.strip()]


def infer_keyword(draft: dict) -> str:
    hashtags = draft.get('hashtags') or []
    for tag in hashtags[::-1]:
        if tag not in ['小红书运营', '电商', '副业', '无货源', '电商避坑', '新手入门', '避坑指南']:
            return tag
    title = draft.get('title') or ''
    for token in ['无货源', '副业', '电商']:
        if token in title:
            return token
    return '这个方向'


def get_theme_voice(theme: str) -> dict:
    return THEME_CARD_VOICE.get(theme or 'default', THEME_CARD_VOICE['default'])


def get_angle_theme_card_core(angle: str, theme: str) -> list[str]:
    theme_bucket = THEME_ANGLE_CARD_VARIANTS.get(angle, {})
    if theme in theme_bucket:
        return theme_bucket[theme]
    return ANGLE_CARD_TEMPLATES.get(angle, ANGLE_CARD_TEMPLATES['趋势判断型'])['core']


def build_cover_subtitle(title: str, angle: str, theme: str) -> str:
    theme_subtitle = get_theme_voice(theme).get('subtitle')
    if theme_subtitle:
        return theme_subtitle
    if angle == '趋势判断型':
        return '先把现实看明白'
    if angle == '避坑提醒型':
        return '这几个坑先别踩'
    if angle == '步骤拆解型':
        return '先把顺序想清楚'
    if '真心话' in title or '真实' in title:
        return '说点不太好听的'
    return '先想清楚再入场'


def summarize_body_points(body: str) -> list[str]:
    paragraphs = split_paragraphs(body)
    points = []
    for part in paragraphs:
        clean = part.replace('“', '').replace('”', '').strip()
        if clean.startswith('#'):
            continue
        points.append(clean)
    return points


def build_semantic_sections(draft: dict, theme: str) -> tuple[list[str], dict]:
    angle = draft.get('angle') or '趋势判断型'
    keyword = infer_keyword(draft)
    theme_voice = get_theme_voice(theme)
    bridge = theme_voice.get('bridge', '说白了就是：')
    core_sections = get_angle_theme_card_core(angle, theme)
    body_points = summarize_body_points(draft.get('body', ''))

    sections = []
    template_hits = 0
    for idx, base in enumerate(core_sections):
        rendered = base.format(keyword=keyword)
        if idx < len(body_points) and body_points[idx]:
            source_line = body_points[idx]
            trimmed = source_line[:40] + ('…' if len(source_line) > 40 else '')
            rendered = rendered + f'\n\n{bridge}{trimmed}'
            template_hits += 1
        sections.append(rendered)

    if not sections:
        sections = [filler for filler in GENERIC_FILLERS[:MIN_CONTENT_CARDS]]

    deduped = []
    seen = set()
    for sec in sections:
        key = sec.replace('\n', '').strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(sec)

    return deduped, {
        'angle': angle,
        'theme': theme,
        'template_core_count': len(core_sections),
        'body_point_count': len(body_points),
        'template_hits': template_hits,
    }


def ensure_min_total_cards(sections: list[str], outro: str, draft: dict) -> tuple[list[str], int, list[str]]:
    needed_content_cards = max(MIN_CONTENT_CARDS, MIN_TOTAL_CARDS - 2)
    out = sections[:]
    added = 0
    added_card_types = []

    cta_text = (draft.get('cta') or '').strip()
    structured_pool = [
        ('summary', MARKDOWN_FALLBACK_CARDS['summary']),
        ('risk', MARKDOWN_FALLBACK_CARDS['risk']),
        ('cta', cta_text or MARKDOWN_FALLBACK_CARDS['cta']),
    ]

    for card_type, candidate in structured_pool:
        if len(out) >= needed_content_cards:
            break
        candidate_key = candidate.replace('\n', '').strip()
        if candidate_key and candidate not in out and candidate_key not in outro.replace('\n', ''):
            out.append(candidate)
            added += 1
            added_card_types.append(card_type)

    idx = 0
    while len(out) < needed_content_cards:
        candidate = GENERIC_FILLERS[idx % len(GENERIC_FILLERS)]
        if candidate not in out and candidate.replace('\n', '') not in outro.replace('\n', ''):
            out.append(candidate)
            added += 1
            added_card_types.append('generic-filler')
        idx += 1
    return out, added, added_card_types


def build_outro_card(draft: dict, theme: str) -> str:
    angle = draft.get('angle') or '趋势判断型'
    template = ANGLE_CARD_TEMPLATES.get(angle, ANGLE_CARD_TEMPLATES['趋势判断型'])
    cta = (draft.get('cta') or '').strip()
    outro_prefix = get_theme_voice(theme).get('outro_prefix', '')
    outro = template['outro']
    if outro_prefix:
        outro = f'{outro_prefix}\n{outro}'
    if cta:
        outro = outro + f'\n\n{cta}'
    return outro


def pick_draft(data: dict, draft_index: int | None) -> tuple[int, dict]:
    drafts = data.get('drafts', [])
    if not drafts:
        raise ValueError('No drafts available in rewrite output.')
    if draft_index is None:
        draft_index = data.get('best_draft_index', 0)
    if draft_index < 0 or draft_index >= len(drafts):
        raise IndexError(f'draft_index out of range: {draft_index}')
    return draft_index, drafts[draft_index]


def make_markdown(draft: dict, theme: str) -> tuple[str, dict]:
    title = (draft.get('title') or '未命名标题')[:15]
    angle = draft.get('angle') or '趋势判断型'
    subtitle = build_cover_subtitle(draft.get('title', ''), angle, theme)
    sections, semantic_meta = build_semantic_sections(draft, theme)
    outro = build_outro_card(draft, theme)
    sections, filler_added, added_card_types = ensure_min_total_cards(sections, outro, draft)
    md = [
        '---',
        'emoji: "📌"',
        f'title: "{title}"',
        f'subtitle: "{subtitle}"',
        '---',
        '',
    ]
    for sec in sections:
        md.append(sec)
        md.append('')
        md.append('---')
        md.append('')
    md.append(outro)
    md.append('')
    meta = {
        'title': title,
        'subtitle': subtitle,
        'angle': angle,
        'theme': theme,
        'final_content_cards': len(sections),
        'filler_added': filler_added,
        'added_card_types': added_card_types,
        'total_cards': len(sections) + 2,
        'semantic_meta': semantic_meta,
    }
    return '\n'.join(md), meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--draft-index', type=int, default=None)
    parser.add_argument('--theme', default='professional')
    args = parser.parse_args()

    data = read_json(args.input)
    drafts = data.get('drafts', [])
    if not drafts:
        append_stage_manifest(data.get('run_id', 'unknown'), 'build_markdown', {
            'status': 'failed',
            'finished_at': iso_now(),
            'input': args.input,
            'reason': 'no_drafts_available',
        })
        raise SystemExit('No drafts available to build render markdown.')

    selected_index, draft = pick_draft(data, args.draft_index)
    theme = draft.get('theme') or data.get('theme') or args.theme
    run_dir = ensure_dir(ROOT / 'data' / 'renders' / data['run_id'])
    content, meta = make_markdown(draft, theme)
    versioned_name = f"content.draft-{selected_index}.{theme}.md"
    versioned_path = run_dir / versioned_name
    versioned_path.write_text(content, encoding='utf-8')
    out_path = run_dir / 'content.md'
    out_path.write_text(content, encoding='utf-8')
    append_stage_manifest(data['run_id'], 'build_markdown-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'input': args.input,
        'output': str(out_path),
        'versioned_output': str(versioned_path),
        'selected_draft_index': selected_index,
        'selected_draft_title': draft.get('title', ''),
        'meta': meta,
    })
    print(out_path)


if __name__ == '__main__':
    main()
