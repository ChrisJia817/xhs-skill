import argparse
from collections import Counter
from bootstrap import ROOT
from common import read_json, write_json, ensure_dir, append_stage_manifest, iso_now

TOP_COMMON_QUESTIONS = 5
TOP_PAIN_POINTS = 5
TOP_EVIDENCE = 8


def contains_any(text: str, keywords: list[str]) -> bool:
    text = text or ''
    return any(k in text for k in keywords)


def item_comments(item: dict) -> list[dict]:
    comments = item.get('comments')
    if isinstance(comments, list):
        return [c for c in comments if isinstance(c, dict)]
    detail = item.get('detail') or {}
    detail_comments = detail.get('comments')
    if isinstance(detail_comments, list):
        return [c for c in detail_comments if isinstance(c, dict)]
    return []


def item_detail_desc(item: dict) -> str:
    if item.get('body'):
        return item.get('body') or ''
    detail = item.get('detail') or {}
    return detail.get('desc') or ''


def item_source_id(item: dict) -> str:
    return item.get('item_id') or item.get('note_id') or item.get('aweme_id') or ''


def item_source_type(item: dict) -> str:
    return item.get('source_type') or item.get('source_platform') or ''


def item_detail_status(item: dict) -> str:
    if item.get('detail_status'):
        return item.get('detail_status')
    if item.get('body') or item_comments(item):
        return 'success'
    return ''


def item_score_total(item: dict) -> int | float:
    score = item.get('score') or {}
    if isinstance(score, dict):
        return score.get('total', 0)
    if isinstance(score, (int, float)):
        return score
    return 0


def merge_text(item: dict) -> str:
    title = item.get('title') or ''
    summary = item.get('summary') or ''
    comment_signals = item.get('comment_signals') or []
    desc = item_detail_desc(item)
    comments = item_comments(item)
    comment_texts = ' '.join((c.get('content') or '') for c in comments)
    return f"{title}\n{summary}\n{' '.join(comment_signals)}\n{desc}\n{comment_texts}"


def infer_pain_points(item: dict, keyword: str) -> list[str]:
    corpus = merge_text(item)
    points = []

    if contains_any(corpus, ['爆款', '万赞', '流量']):
        points.append(f'很多人看到{keyword}相关内容很火，但不知道结果到底怎么稳定做出来')
    if contains_any(corpus, ['代替不了', '取代', '趋势']):
        points.append(f'用户对{keyword}的发展趋势有强烈判断焦虑，担心跟错方向')
    if contains_any(corpus, ['修图', '怎么做', '喂饭版', '教程', '步骤', '用的什么做', '怎么弄']):
        points.append(f'用户希望得到关于{keyword}的可执行步骤，而不是只看概念')
    if contains_any(corpus, ['新手', '入门', '小白', '想学习', '入坑']):
        points.append(f'新手想进入{keyword}领域，但不知道第一步该从哪里开始')
    if contains_any(corpus, ['成本', '变现', '盈利', '赔', '亏', '预算多少']):
        points.append(f'用户担心投入学习{keyword}后，结果和回报并不匹配')
    if contains_any(corpus, ['避坑', '风险', '违规', '翻车']):
        points.append(f'用户对{keyword}的风险、踩坑和违规问题非常敏感')

    if not points:
        points.append(f'用户关注{keyword}，但缺少可执行、可判断的落地方案')
    return points


def infer_common_questions(item: dict, keyword: str) -> list[str]:
    corpus = merge_text(item)
    questions = []

    if contains_any(corpus, ['还能做吗', '有没有机会', '趋势', '代替不了']):
        questions.append(f'{keyword}这个方向现在到底还有没有机会？')
    if contains_any(corpus, ['怎么做', '步骤', '教程', '喂饭版', '用的什么做', '怎么弄']):
        questions.append(f'{keyword}具体应该怎么做，步骤到底是什么？')
    if contains_any(corpus, ['爆款', '流量', '万赞']):
        questions.append(f'别人做{keyword}内容为什么能出结果，我为什么做不出来？')
    if contains_any(corpus, ['修图', '工具']):
        questions.append(f'{keyword}工具学了不少，为什么还是做不出稳定结果？')
    if contains_any(corpus, ['避坑', '风险', '违规', '翻车']):
        questions.append(f'{keyword}最容易踩的坑到底是什么？')
    if contains_any(corpus, ['想学习', '入坑', '预算多少']):
        questions.append(f'如果现在开始学{keyword}，预算和门槛大概是什么水平？')
    if not questions:
        questions.append(f'{keyword}这个方向到底值不值得投入？')
    return questions


def infer_platform_angles(selected: list[dict]) -> dict:
    xhs_angles = []
    wechat_angles = []
    for item in selected:
        angles = item.get('angles') or []
        for angle in angles:
            if angle not in xhs_angles:
                xhs_angles.append(angle)
            if angle == '趋势判断型' and '趋势分析 / 认知升级型' not in wechat_angles:
                wechat_angles.append('趋势分析 / 认知升级型')
            elif angle == '避坑提醒型' and '痛点诊断 + 方法拆解型' not in wechat_angles:
                wechat_angles.append('痛点诊断 + 方法拆解型')
            elif angle == '步骤拆解型' and '实操步骤 / 经验复盘型' not in wechat_angles:
                wechat_angles.append('实操步骤 / 经验复盘型')

        source_platform = item.get('source_platform') or ''
        if source_platform == 'douyin':
            if '趋势判断型' not in xhs_angles:
                xhs_angles.append('趋势判断型')
            if '趋势分析 / 认知升级型' not in wechat_angles:
                wechat_angles.append('趋势分析 / 认知升级型')
            if item_comments(item) and '实操步骤 / 经验复盘型' not in wechat_angles:
                wechat_angles.append('实操步骤 / 经验复盘型')
    return {
        'xhs': xhs_angles or ['趋势判断型', '避坑提醒型'],
        'wechat': wechat_angles or ['痛点诊断 + 方法拆解型'],
    }


def top_items(counter_values: list[str], limit: int) -> list[str]:
    counter = Counter(counter_values)
    return [item for item, _ in counter.most_common(limit)]


def infer_topic_title(keyword: str, selected: list[dict]) -> str:
    titles = ' '.join((item.get('title') or '') for item in selected)
    if contains_any(titles, ['爆款', '流量', '万赞']):
        return f'{keyword}内容结果与流量获取'
    if contains_any(titles, ['修图', '教程', '怎么做', '用的什么做']):
        return f'{keyword}工具落地与实操路径'
    if contains_any(titles, ['代替不了', '趋势']):
        return f'{keyword}趋势判断与认知升级'
    return keyword


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    args = parser.parse_args()

    data = read_json(args.input)
    candidates = data.get('candidates', [])
    selected = data.get('selected', candidates[:3])
    if not selected:
        append_stage_manifest(data.get('run_id', 'unknown'), 'topic_brief', {
            'status': 'failed',
            'finished_at': iso_now(),
            'input': args.input,
            'reason': 'no_selected_candidates',
        })
        raise SystemExit('No selected candidates available to build topic brief.')

    keyword = data.get('keyword', '')
    all_pain_points = []
    all_questions = []
    evidence = []
    for item in selected:
        all_pain_points.extend(infer_pain_points(item, keyword))
        all_questions.extend(infer_common_questions(item, keyword))
        detail_excerpt = item_detail_desc(item)
        evidence.append({
            'source_note_id': item_source_id(item),
            'title': item.get('title', ''),
            'summary': item.get('summary', ''),
            'author': item.get('author', ''),
            'score': item_score_total(item),
            'publish_time': item.get('publish_time', ''),
            'source_type': item_source_type(item),
            'detail_status': item_detail_status(item),
            'detail_excerpt': detail_excerpt[:280],
            'comment_count_sampled': len(item_comments(item)),
        })

    brief = {
        'run_id': data['run_id'],
        'stage': 'topic_brief',
        'status': 'success',
        'generated_at': iso_now(),
        'keyword': keyword,
        'publish_time': data.get('publish_time', ''),
        'source_input': args.input,
        'topic': infer_topic_title(keyword, selected),
        'source_note_count': len(selected),
        'pain_points': top_items(all_pain_points, TOP_PAIN_POINTS),
        'common_questions': top_items(all_questions, TOP_COMMON_QUESTIONS),
        'platform_angles': infer_platform_angles(selected),
        'evidence': evidence[:TOP_EVIDENCE],
        'selected': selected,
    }

    out_dir = ensure_dir(ROOT / 'data' / 'briefs')
    out_path = out_dir / f"{data['run_id']}.json"
    write_json(out_path, brief)
    append_stage_manifest(data['run_id'], 'topic_brief-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'input': args.input,
        'output': str(out_path),
        'pain_point_count': len(brief['pain_points']),
        'question_count': len(brief['common_questions']),
        'topic': brief['topic'],
    })
    print(out_path)


if __name__ == '__main__':
    main()
