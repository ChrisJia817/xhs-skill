import argparse
from collections import OrderedDict
from bootstrap import ROOT
from common import read_json, write_json, ensure_dir, append_stage_manifest, iso_now, new_run_id


def normalize_candidate(item: dict, source_type: str) -> dict:
    raw = item.get('raw') or item
    note_id = item.get('note_id') or item.get('item_id') or raw.get('id') or raw.get('note_id') or ''
    title = item.get('title') or raw.get('title') or raw.get('displayTitle') or ''
    summary = item.get('summary') or raw.get('summary') or title
    author = item.get('author') or raw.get('author') or ((raw.get('user') or {}).get('nickname') if isinstance(raw, dict) else '') or ''
    return {
        'note_id': note_id,
        'title': title,
        'summary': summary,
        'author': author,
        'publish_time': item.get('publish_time') or raw.get('publish_time') or '',
        'like_count': item.get('like_count', 0),
        'comment_count': item.get('comment_count', 0),
        'collect_count': item.get('collect_count', 0),
        'source_type': source_type,
        'raw': raw,
    }


def add_unique(target: OrderedDict, candidates: list[dict], source_type: str):
    for item in candidates:
        normalized = normalize_candidate(item, source_type)
        key = normalized.get('note_id') or f"{source_type}:{normalized.get('title','')}:{normalized.get('author','')}"
        if key not in target:
            target[key] = normalized


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='')
    parser.add_argument('--keyword', required=True)
    parser.add_argument('--search-input', default='')
    parser.add_argument('--home-feeds-input', default='')
    parser.add_argument('--profile-notes-inputs', nargs='*', default=[])
    args = parser.parse_args()

    run_id = args.run_id or new_run_id('xhs-read')
    merged = OrderedDict()
    publish_time = ''

    if args.search_input:
        search_data = read_json(args.search_input)
        publish_time = search_data.get('publish_time', '')
        add_unique(merged, search_data.get('candidates', []), 'xhs-search')

    if args.home_feeds_input:
        home_data = read_json(args.home_feeds_input)
        payload = home_data.get('payload') or {}
        feeds = payload.get('feeds') or []
        add_unique(merged, feeds, 'xhs-home-feed')

    for profile_input in args.profile_notes_inputs:
        profile_data = read_json(profile_input)
        payload = profile_data.get('payload') or {}
        notes = payload.get('notes') or payload.get('items') or payload.get('feeds') or []
        add_unique(merged, notes, 'xhs-profile-notes')

    out = {
        'run_id': run_id,
        'stage': 'xhs_reading_pool',
        'status': 'success',
        'generated_at': iso_now(),
        'keyword': args.keyword,
        'publish_time': publish_time,
        'candidate_count': len(merged),
        'candidates': list(merged.values()),
        'inputs': {
            'search_input': args.search_input,
            'home_feeds_input': args.home_feeds_input,
            'profile_notes_inputs': args.profile_notes_inputs,
        },
    }

    out_dir = ensure_dir(ROOT / 'data' / 'reading-pool')
    out_path = out_dir / f'{run_id}.json'
    write_json(out_path, out)
    append_stage_manifest(run_id, 'xhs-reading-pool-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'output': str(out_path),
        'candidate_count': len(merged),
    })
    print(out_path)


if __name__ == '__main__':
    main()
