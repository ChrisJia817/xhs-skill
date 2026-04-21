import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from bootstrap import ROOT
from common import write_json, ensure_dir, new_run_id, append_stage_manifest, iso_now
from vendor_paths import resolve_mediacrawler_output, resolve_mediacrawler_root, resolve_mediacrawler_save_root

MEDIA_CRAWLER_OUTPUT = resolve_mediacrawler_output()
MEDIA_CRAWLER_ROOT = resolve_mediacrawler_root()
MEDIA_CRAWLER_SAVE_ROOT = resolve_mediacrawler_save_root()


def find_latest_search_file() -> Path:
    files = sorted(MEDIA_CRAWLER_OUTPUT.glob('search_contents_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit('No MediaCrawler Douyin search output file found.')
    return files[0]


def snapshot_files(pattern: str) -> set[str]:
    ensure_dir(MEDIA_CRAWLER_OUTPUT)
    return {str(path.resolve()) for path in MEDIA_CRAWLER_OUTPUT.glob(pattern)}


def newest_file_from_diff(before: set[str], pattern: str) -> Path | None:
    after = [path for path in MEDIA_CRAWLER_OUTPUT.glob(pattern) if str(path.resolve()) not in before]
    if after:
        return sorted(after, key=lambda path: path.stat().st_mtime, reverse=True)[0]
    existing = sorted(MEDIA_CRAWLER_OUTPUT.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return existing[0] if existing else None


def run_search_fetch(keyword: str, login_type: str, headless: bool) -> tuple[Path, list[str]]:
    uv = shutil.which('uv')
    if not uv:
        raise SystemExit('uv is not available in PATH; required for MediaCrawler Douyin search.')
    if not MEDIA_CRAWLER_ROOT.exists():
        raise SystemExit(f'MediaCrawler root not found: {MEDIA_CRAWLER_ROOT}')

    before_contents = snapshot_files('search_contents_*.json')
    ensure_dir(MEDIA_CRAWLER_OUTPUT)

    command = [
        uv, 'run', 'main.py',
        '--platform', 'dy',
        '--lt', login_type,
        '--type', 'search',
        '--keywords', keyword,
        '--save_data_option', 'json',
        '--save_data_path', str(MEDIA_CRAWLER_SAVE_ROOT),
        '--get_comment', 'false',
        '--max_concurrency_num', '1',
        '--headless', 'true' if headless else 'false',
    ]
    subprocess.run(command, cwd=str(MEDIA_CRAWLER_ROOT), check=True)
    time.sleep(1)

    source_path = newest_file_from_diff(before_contents, 'search_contents_*.json')
    if not source_path:
        raise SystemExit(f'No MediaCrawler Douyin search output file found under {MEDIA_CRAWLER_OUTPUT}.')
    return source_path, command


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
    parser.add_argument('--backend', default='file', choices=['file', 'mock', 'mediacrawler'])
    parser.add_argument('--login-type', default=os.environ.get('XHS_DOUYIN_LOGIN_TYPE', 'qrcode') or 'qrcode')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()

    run_id = args.run_id or new_run_id('dy')
    source_file = ''
    search_command: list[str] = []
    if args.backend == 'mock':
        candidates = build_mock_candidates(args.keyword, args.limit)
    elif args.backend == 'mediacrawler':
        source_path, search_command = run_search_fetch(args.keyword, args.login_type, args.headless)
        source_file = str(source_path)
        items = load_json_file(source_path)
        candidates = [normalize_item(item) for item in items[:max(1, args.limit)] if isinstance(item, dict)]
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
        'login_type': args.login_type if args.backend == 'mediacrawler' else '',
        'headless': args.headless if args.backend == 'mediacrawler' else False,
        'candidate_count': len(candidates),
        'source_file': source_file,
        'search_command': search_command,
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
        'login_type': args.login_type if args.backend == 'mediacrawler' else '',
        'headless': args.headless if args.backend == 'mediacrawler' else False,
        'source_file': source_file,
        'search_command': search_command,
        'output': str(out_path),
        'candidate_count': len(candidates),
    })
    print(out_path)


if __name__ == '__main__':
    main()
