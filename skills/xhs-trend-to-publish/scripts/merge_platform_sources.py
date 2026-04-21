import argparse
from bootstrap import ROOT
from common import read_json, write_json, ensure_dir, append_stage_manifest, iso_now

MAX_SELECTED = 3


def normalize_xhs_candidate(item: dict) -> dict:
    detail = item.get('detail') or {}
    return {
        'source_platform': 'xhs',
        'item_id': item.get('note_id', ''),
        'title': item.get('title', ''),
        'summary': item.get('summary', ''),
        'body': detail.get('desc', ''),
        'author': item.get('author', ''),
        'publish_time': item.get('publish_time', ''),
        'like_count': item.get('like_count', 0),
        'comment_count': item.get('comment_count', 0),
        'collect_count': item.get('collect_count', 0),
        'share_count': detail.get('raw', {}).get('detail', {}).get('note', {}).get('interactInfo', {}).get('shareCount', 0),
        'comments': detail.get('comments', []),
        'detail_status': 'success' if detail else '',
        'raw': item,
    }


def normalize_douyin_candidate(item: dict) -> dict:
    detail = item.get('detail') or {}
    return {
        'source_platform': 'douyin',
        'item_id': item.get('aweme_id', ''),
        'title': item.get('title', ''),
        'summary': item.get('summary', ''),
        'body': detail.get('desc', ''),
        'author': item.get('author', ''),
        'publish_time': item.get('publish_time', ''),
        'like_count': item.get('like_count', 0),
        'comment_count': item.get('comment_count', 0),
        'collect_count': item.get('collect_count', 0),
        'share_count': item.get('share_count', 0),
        'comments': detail.get('comments', []),
        'detail_status': item.get('detail_status', ''),
        'raw': item,
    }


def first_non_empty(*values):
    for value in values:
        if value not in (None, '', []):
            return value
    return ''


def candidate_key(item: dict) -> tuple[str, str]:
    return str(item.get('source_platform') or ''), str(item.get('item_id') or '')


def raw_score_total(item: dict) -> int | float:
    raw = item.get('raw') or {}
    score = raw.get('score') if isinstance(raw, dict) else {}
    if isinstance(score, dict):
        total = score.get('total', 0)
        if isinstance(total, (int, float)):
            return total
    if isinstance(score, (int, float)):
        return score
    return 0


def interaction_proxy_score(item: dict) -> int:
    like_count = int(item.get('like_count', 0) or 0)
    comment_count = int(item.get('comment_count', 0) or 0)
    collect_count = int(item.get('collect_count', 0) or 0)
    share_count = int(item.get('share_count', 0) or 0)
    base = min(65, int(like_count / 80) + int(comment_count / 20) + int(collect_count / 30) + int(share_count / 20))
    if item.get('detail_status') == 'success':
        base += 10
    if item.get('comments'):
        base += min(10, len(item.get('comments') or []))
    return min(100, base)


def selection_score(item: dict) -> int | float:
    raw_total = raw_score_total(item)
    if raw_total:
        return raw_total
    return interaction_proxy_score(item)


def dedupe_candidates(items: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for item in items:
        key = candidate_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def sort_candidates(items: list[dict]) -> list[dict]:
    return sorted(
        dedupe_candidates(items),
        key=lambda item: (
            selection_score(item),
            int(item.get('like_count', 0) or 0),
            int(item.get('comment_count', 0) or 0),
            int(item.get('collect_count', 0) or 0),
        ),
        reverse=True,
    )


def select_balanced_candidates(xhs_items: list[dict], douyin_items: list[dict], limit: int = MAX_SELECTED) -> list[dict]:
    ranked_xhs = sort_candidates(xhs_items)
    ranked_douyin = sort_candidates(douyin_items)

    if not ranked_xhs:
        return ranked_douyin[:limit]
    if not ranked_douyin:
        return ranked_xhs[:limit]

    selected = []
    selected_keys = set()

    for candidate in (ranked_xhs[0], ranked_douyin[0]):
        key = candidate_key(candidate)
        if key not in selected_keys:
            selected.append(candidate)
            selected_keys.add(key)

    remaining = sort_candidates(ranked_xhs[1:] + ranked_douyin[1:])
    for candidate in remaining:
        if len(selected) >= limit:
            break
        key = candidate_key(candidate)
        if key in selected_keys:
            continue
        selected.append(candidate)
        selected_keys.add(key)

    return selected[:limit]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--xhs-input', default='')
    parser.add_argument('--douyin-input', default='')
    parser.add_argument('--run-id', default='')
    args = parser.parse_args()

    merged_candidates = []
    prioritized_xhs = []
    prioritized_douyin = []
    run_id = args.run_id
    keyword = ''
    publish_time = ''

    if args.xhs_input:
        xhs_data = read_json(args.xhs_input)
        run_id = run_id or xhs_data.get('run_id', '')
        keyword = first_non_empty(keyword, xhs_data.get('keyword'))
        publish_time = first_non_empty(publish_time, xhs_data.get('publish_time'))
        for item in xhs_data.get('candidates', []):
            merged_candidates.append(normalize_xhs_candidate(item))
        for item in xhs_data.get('selected') or xhs_data.get('candidates', []):
            prioritized_xhs.append(normalize_xhs_candidate(item))

    if args.douyin_input:
        dy_data = read_json(args.douyin_input)
        run_id = run_id or dy_data.get('run_id', '')
        keyword = first_non_empty(keyword, dy_data.get('keyword'))
        publish_time = first_non_empty(publish_time, dy_data.get('publish_time'))
        for item in dy_data.get('candidates', []):
            merged_candidates.append(normalize_douyin_candidate(item))
        for item in dy_data.get('selected') or dy_data.get('candidates', []):
            prioritized_douyin.append(normalize_douyin_candidate(item))

    if not run_id:
        raise SystemExit('run_id could not be resolved from inputs; provide --run-id explicitly.')

    selected = select_balanced_candidates(prioritized_xhs, prioritized_douyin, MAX_SELECTED)
    if not selected:
        selected = sort_candidates(merged_candidates)[:MAX_SELECTED]

    out = {
        'run_id': run_id,
        'stage': 'merged_sources',
        'status': 'success',
        'generated_at': iso_now(),
        'keyword': keyword,
        'publish_time': publish_time,
        'candidate_count': len(merged_candidates),
        'selected_count': len(selected),
        'candidates': merged_candidates,
        'selected': selected,
    }

    out_dir = ensure_dir(ROOT / 'data' / 'merged')
    out_path = out_dir / f'{run_id}.json'
    write_json(out_path, out)
    append_stage_manifest(run_id, 'merge-platform-sources-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'output': str(out_path),
        'keyword': keyword,
        'publish_time': publish_time,
        'candidate_count': len(merged_candidates),
        'selected_count': len(selected),
        'selected_platforms': [item.get('source_platform', '') for item in selected],
    })
    print(out_path)


if __name__ == '__main__':
    main()
