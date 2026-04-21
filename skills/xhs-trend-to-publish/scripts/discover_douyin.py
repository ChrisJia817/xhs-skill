import argparse
import json
from pathlib import Path
from bootstrap import ROOT
from common import write_json, ensure_dir, new_run_id, append_stage_manifest, iso_now
from vendor_paths import resolve_mediacrawler_output

MEDIA_CRAWLER_OUTPUT = resolve_mediacrawler_output()


def find_latest_search_file() -> Path:
    files = sorted(MEDIA_CRAWLER_OUTPUT.glob('search_contents_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit('No MediaCrawler Douyin search output file found.')
    return files[0]


def load_json_file(path: Path):
    text = path.read_text(encoding='utf-8')
    data = json.loads(text)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


def normalize_item(item: dict) -> dict:
    return {
        'source_platform': 'douyin',
        'aweme_id': str(item.get('aweme_id') or ''),
        'title': item.get('title') or item.get('desc') or '',
        'summary': item.get('desc') or '',
        'author': item.get('nickname') or '',
        'publish_time': item.get('create_time') or '',
        'like_count': int(str(item.get('liked_count') or 0).replace(',', '') or 0),
        'comment_count': int(str(item.get('comment_count') or 0).replace(',', '') or 0),
        'collect_count': int(str(item.get('collected_count') or 0).replace(',', '') or 0),
        'share_count': int(str(item.get('share_count') or 0).replace(',', '') or 0),
        'url': item.get('aweme_url') or '',
        'cover_url': item.get('cover_url') or '',
        'source_type': 'douyin-search',
        'raw': item,
    }


def build_mock_candidates(keyword: str, limit: int) -> list[dict]:
    total = max(1, limit)
    items = []
    for idx in range(total):
        items.append({
            'source_platform': 'douyin',
            'aweme_id': f'mock-aweme-{idx + 1}',
            'title': f'{keyword} mock douyin sample {idx + 1}',
            'summary': f'模拟抖音样本 {idx + 1}，用于新机器上的 workflow 自检。',
            'author': f'mock-author-{idx + 1}',
            'publish_time': '2026-01-01T00:00:00',
            'like_count': 1000 - idx * 10,
            'comment_count': 120 - idx * 3,
            'collect_count': 80 - idx * 2,
            'share_count': 60 - idx,
            'url': f'https://www.douyin.com/video/mock-{idx + 1}',
            'cover_url': f'https://example.com/mock-douyin-cover-{idx + 1}.png',
            'source_type': 'douyin-search-mock',
            'raw': {
                'mock': True,
                'keyword': keyword,
                'index': idx + 1,
            },
        })
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', required=True)
    parser.add_argument('--run-id', default='')
    parser.add_argument('--limit', type=int, default=15)
    parser.add_argument('--backend', default='file', choices=['file', 'mock'])
    args = parser.parse_args()

    run_id = args.run_id or new_run_id('dy')
    source_file = ''
    if args.backend == 'mock':
        candidates = build_mock_candidates(args.keyword, args.limit)
    else:
        source_path = find_latest_search_file()
        source_file = str(source_path)
        items = load_json_file(source_path)
        candidates = [normalize_item(item) for item in items[:max(1, args.limit)] if isinstance(item, dict)]

    payload = {
        'run_id': run_id,
        'stage': 'douyin_discover',
        'status': 'success',
        'generated_at': iso_now(),
        'keyword': args.keyword,
        'backend': args.backend,
        'candidate_count': len(candidates),
        'source_file': source_file,
        'candidates': candidates,
    }

    out_dir = ensure_dir(ROOT / 'data' / 'douyin' / 'raw')
    out_path = out_dir / f'{run_id}.json'
    write_json(out_path, payload)
    append_stage_manifest(run_id, 'douyin-discover-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'keyword': args.keyword,
        'backend': args.backend,
        'source_file': source_file,
        'output': str(out_path),
        'candidate_count': len(candidates),
    })
    print(out_path)


if __name__ == '__main__':
    main()
