import argparse
from bootstrap import ROOT
from common import read_json, write_json, ensure_dir, append_stage_manifest, iso_now

MAX_SELECTED = 3


def contains_any(text: str, keywords: list[str]) -> bool:
    text = text or ''
    return any(k in text for k in keywords)


def score_heat(item: dict) -> int:
    like_count = int(item.get('like_count', 0) or 0)
    comment_count = int(item.get('comment_count', 0) or 0)
    collect_count = int(item.get('collect_count', 0) or 0)
    score = min(40, int(like_count / 80) + int(comment_count / 25) + int(collect_count / 45))
    return max(0, score)


def score_freshness(publish_time: str) -> int:
    text = str(publish_time or '')
    if contains_any(text, ['7天', '一周', '近7天']):
        return 15
    if contains_any(text, ['30天', '一个月', '近30天']):
        return 11
    if '半年' in text:
        return 8
    if text:
        return 10
    return 6


def score_rewrite_potential(item: dict) -> tuple[int, dict]:
    title = item.get('title') or ''
    summary = item.get('summary') or ''
    comment_signals = item.get('comment_signals') or []
    corpus = f"{title}\n{summary}"

    title_clarity = 4 if len(title.strip()) >= 8 else 2
    focused_topic = 4 if len(summary.strip()) >= 8 else 2
    has_viewpoint = 4 if contains_any(corpus, ['还能做吗', '避坑', '为什么', '怎么做', '值不值得']) else 2
    has_comment_tension = 4 if len(comment_signals) >= 2 else (2 if comment_signals else 0)
    card_friendly = 4 if contains_any(corpus, ['3个', '步骤', '避坑', '清单', '建议']) else 2

    total = min(20, title_clarity + focused_topic + has_viewpoint + has_comment_tension + card_friendly)
    detail = {
        'title_clarity': title_clarity,
        'focused_topic': focused_topic,
        'has_viewpoint': has_viewpoint,
        'has_comment_tension': has_comment_tension,
        'card_friendly': card_friendly,
        'total': total,
    }
    return total, detail


def score_fit(item: dict, keyword: str) -> tuple[int, dict]:
    corpus = f"{item.get('title', '')}\n{item.get('summary', '')}"
    keyword = (keyword or '').strip()
    score = 6
    matched = []
    if keyword and keyword in corpus:
        score += 5
        matched.append('keyword-hit')
    if contains_any(corpus, ['副业', '电商', '运营', '开店']):
        score += 2
        matched.append('commerce-domain')
    if contains_any(corpus, ['避坑', '趋势', '怎么做', '新手']):
        score += 2
        matched.append('content-style-fit')
    return min(15, score), {'matched': matched, 'total': min(15, score)}


def score_risk(item: dict) -> tuple[int, dict]:
    corpus = f"{item.get('title', '')}\n{item.get('summary', '')}"
    penalty = 0
    hits = []
    risk_map = {
        '暴利': 6,
        '躺赚': 6,
        '稳赚': 5,
        '引流': 5,
        '私域': 4,
        '微信': 4,
        'vx': 4,
        '违规': 3,
        '搬运': 4,
    }
    for token, value in risk_map.items():
        if token.lower() in corpus.lower():
            penalty += value
            hits.append(token)
    return min(20, penalty), {'hits': hits, 'total': min(20, penalty)}


def infer_angles(item: dict) -> list[str]:
    corpus = f"{item.get('title', '')}\n{item.get('summary', '')}"
    angles = []
    if contains_any(corpus, ['还能做吗', '趋势', '变化']):
        angles.append('趋势判断型')
    if contains_any(corpus, ['避坑', '违规', '风险', '骗局']):
        angles.append('避坑提醒型')
    if contains_any(corpus, ['步骤', '怎么做', '清单', '教程']):
        angles.append('步骤拆解型')
    if not angles:
        angles = ['趋势判断型', '避坑提醒型']
    return angles


def score_candidate(item: dict, keyword: str):
    heat = score_heat(item)
    freshness = score_freshness(item.get('publish_time', ''))
    rewrite, rewrite_detail = score_rewrite_potential(item)
    fit, fit_detail = score_fit(item, keyword)
    risk_penalty, risk_detail = score_risk(item)
    total = max(0, min(100, heat + freshness + rewrite + fit - risk_penalty))
    item['score'] = {
        'heat': heat,
        'freshness': freshness,
        'rewrite': rewrite,
        'fit': fit,
        'risk_penalty': risk_penalty,
        'rewrite_detail': rewrite_detail,
        'fit_detail': fit_detail,
        'risk_detail': risk_detail,
        'total': total,
    }
    item['decision'] = 'keep' if total >= 60 else 'drop'
    item['angles'] = infer_angles(item)
    return item


def fallback_select(scored: list[dict]) -> list[dict]:
    if not scored:
        return []
    kept = [x for x in scored if x.get('decision') == 'keep'][:MAX_SELECTED]
    if kept:
        return kept
    fallback = []
    for item in scored:
        fallback.append({
            **item,
            'decision': 'fallback-keep',
            'fallback_reason': 'no_candidate_reached_keep_threshold',
        })
        if len(fallback) >= min(MAX_SELECTED, len(scored)):
            break
    return fallback


def normalize_reading_pool_candidates(data: dict) -> list[dict]:
    normalized = []
    for item in data.get('candidates', []):
        raw = item.get('raw') or {}
        raw_note = raw.get('noteCard') or raw
        title = item.get('title') or raw_note.get('displayTitle') or raw_note.get('title') or ''
        summary = item.get('summary') or title
        author = item.get('author') or ((raw_note.get('user') or {}).get('nickname') if isinstance(raw_note, dict) else '') or ''
        normalized.append({
            'note_id': item.get('note_id') or raw.get('id') or '',
            'title': title,
            'url': item.get('url') or '',
            'author': author,
            'publish_time': item.get('publish_time', ''),
            'like_count': item.get('like_count', 0),
            'comment_count': item.get('comment_count', 0),
            'collect_count': item.get('collect_count', 0),
            'summary': summary,
            'comment_signals': item.get('comment_signals') or [],
            'source_type': item.get('source_type', 'xhs-reading-pool'),
        })
    return normalized


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    args = parser.parse_args()

    data = read_json(args.input)
    candidates = data.get('candidates', [])
    if data.get('stage') == 'xhs_reading_pool':
        candidates = normalize_reading_pool_candidates(data)
    if not candidates:
        append_stage_manifest(data.get('run_id', 'unknown'), 'score', {
            'status': 'failed',
            'finished_at': iso_now(),
            'input': args.input,
            'reason': 'no_candidates_available',
        })
        raise SystemExit('No candidates available for scoring.')

    scored = [score_candidate(item, data.get('keyword', '')) for item in candidates]
    scored.sort(key=lambda x: x['score']['total'], reverse=True)
    selected = fallback_select(scored)
    out = {
        'run_id': data['run_id'],
        'stage': 'score',
        'status': 'success',
        'generated_at': iso_now(),
        'keyword': data['keyword'],
        'publish_time': data['publish_time'],
        'source_input': args.input,
        'candidate_count': len(scored),
        'selected_count': len(selected),
        'selection_mode': 'keep' if any(x.get('decision') == 'keep' for x in selected) else 'fallback',
        'candidates': scored,
        'selected': selected,
    }
    out_dir = ensure_dir(ROOT / 'data' / 'trends' / 'scored')
    out_path = out_dir / f"{data['run_id']}.json"
    write_json(out_path, out)
    append_stage_manifest(data['run_id'], 'score-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'input': args.input,
        'output': str(out_path),
        'candidate_count': len(scored),
        'selected_count': len(selected),
        'selection_mode': out['selection_mode'],
        'top_scores': [x['score']['total'] for x in scored[:3]],
    })
    print(out_path)


if __name__ == '__main__':
    main()
