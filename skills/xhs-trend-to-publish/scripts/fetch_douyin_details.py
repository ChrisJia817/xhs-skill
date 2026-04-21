import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
from bootstrap import ROOT
from common import read_json, write_json, ensure_dir, append_stage_manifest, iso_now
from vendor_paths import resolve_mediacrawler_root, resolve_mediacrawler_output, resolve_mediacrawler_save_root

MEDIA_CRAWLER_ROOT = resolve_mediacrawler_root()
MEDIA_CRAWLER_OUTPUT = resolve_mediacrawler_output()
MEDIA_CRAWLER_SAVE_ROOT = resolve_mediacrawler_save_root()
DETAIL_OUTPUT_TIMEOUT_SEC = 30.0


def load_json_file(path: Path):
    text = path.read_text(encoding='utf-8')
    data = json.loads(text)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


def snapshot_files(pattern: str) -> set[str]:
    return {str(p.resolve()) for p in MEDIA_CRAWLER_OUTPUT.glob(pattern)}


def newest_file_from_diff(before: set[str], pattern: str) -> Path | None:
    after = [p for p in MEDIA_CRAWLER_OUTPUT.glob(pattern) if str(p.resolve()) not in before]
    if after:
        return sorted(after, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    existing = sorted(MEDIA_CRAWLER_OUTPUT.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return existing[0] if existing else None


def wait_for_recent_file(before: set[str], pattern: str, started_at: float, timeout_sec: float) -> Path | None:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() <= deadline:
        candidate = newest_file_from_diff(before, pattern)
        if candidate and candidate.exists() and candidate.stat().st_mtime >= started_at - 1e-6:
            return candidate
        time.sleep(1)
    return None


def run_detail_fetch(aweme_id: str, comment_limit: int, login_type: str, headless: bool) -> tuple[Path | None, Path | None, list[str]]:
    before_contents = snapshot_files('detail_contents_*.json')
    before_comments = snapshot_files('detail_comments_*.json')
    started_at = time.time()

    uv = shutil.which('uv')
    if not uv:
        raise SystemExit('uv is not available in PATH; required for MediaCrawler detail fetch.')

    command = [
        uv, 'run', 'main.py',
        '--platform', 'dy',
        '--lt', login_type,
        '--type', 'detail',
        '--specified_id', aweme_id,
        '--save_data_option', 'json',
        '--save_data_path', str(MEDIA_CRAWLER_SAVE_ROOT),
        '--max_comments_count_singlenotes', str(comment_limit),
        '--max_concurrency_num', '1',
        '--get_comment', 'true' if comment_limit > 0 else 'false',
        '--headless', 'true' if headless else 'false',
    ]
    subprocess.run(command, cwd=str(MEDIA_CRAWLER_ROOT), check=True)
    content_file = wait_for_recent_file(before_contents, 'detail_contents_*.json', started_at, DETAIL_OUTPUT_TIMEOUT_SEC)
    comment_file = None
    if comment_limit > 0:
        comment_file = wait_for_recent_file(before_comments, 'detail_comments_*.json', started_at, DETAIL_OUTPUT_TIMEOUT_SEC)
    return (
        content_file,
        comment_file,
        command,
    )


def normalize_comments(comment_items: list[dict], aweme_id: str) -> list[dict]:
    comments = []
    for item in comment_items:
        if not isinstance(item, dict):
            continue
        if str(item.get('aweme_id') or '') != aweme_id:
            continue
        comments.append({
            'comment_id': str(item.get('comment_id') or ''),
            'content': item.get('content') or '',
            'author': item.get('nickname') or '',
            'author_user_id': str(item.get('user_id') or ''),
            'like_count': item.get('like_count') or '0',
            'parent_comment_id': item.get('parent_comment_id') or '0',
            'create_time': item.get('create_time') or '',
            'raw': item,
        })
    return comments


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--comment-limit', type=int, default=5)
    args = parser.parse_args()

    data = read_json(args.input)
    run_id = data['run_id']
    login_type = data.get('login_type') or 'qrcode'
    headless = bool(data.get('headless'))
    candidates = data.get('candidates', [])
    if not candidates:
        append_stage_manifest(run_id, 'douyin_fetch_details', {
            'status': 'failed',
            'finished_at': iso_now(),
            'input': args.input,
            'reason': 'no_candidates_available',
        })
        raise SystemExit('No Douyin candidates available for detail enrichment.')

    fetch_targets = candidates[:max(1, args.limit)]
    collected_detail_items: list[dict] = []
    collected_comment_items: list[dict] = []
    fetch_logs: list[dict] = []

    for item in fetch_targets:
        aweme_id = str(item.get('aweme_id') or '')
        if not aweme_id:
            fetch_logs.append({'aweme_id': '', 'status': 'skipped', 'reason': 'missing_aweme_id'})
            continue
        try:
            content_file, comment_file, command = run_detail_fetch(aweme_id, args.comment_limit, login_type, headless)
            detail_items = load_json_file(content_file) if content_file else []
            comment_items = load_json_file(comment_file) if comment_file else []
            matched_details = [detail for detail in detail_items if str(detail.get('aweme_id') or '') == aweme_id]
            matched_comments = [comment for comment in comment_items if str(comment.get('aweme_id') or '') == aweme_id]
            collected_detail_items.extend(matched_details)
            collected_comment_items.extend(matched_comments)
            fetch_logs.append({
                'aweme_id': aweme_id,
                'status': 'success' if matched_details else 'missing',
                'command': command,
                'detail_file': str(content_file) if content_file else '',
                'comment_file': str(comment_file) if comment_file else '',
                'matched_detail_count': len(matched_details),
                'matched_comment_count': len(matched_comments),
            })
        except subprocess.CalledProcessError as exc:
            fetch_logs.append({
                'aweme_id': aweme_id,
                'status': 'failed',
                'reason': f'mediacrawler_exit_{exc.returncode}',
            })

    detail_by_id = {str(item.get('aweme_id') or ''): item for item in collected_detail_items if isinstance(item, dict)}

    enriched_candidates = []
    details_fetched = 0
    for item in fetch_targets:
        aweme_id = str(item.get('aweme_id') or '')
        detail = detail_by_id.get(aweme_id)
        if not detail:
            enriched_candidates.append({**item, 'detail_status': 'missing'})
            continue
        comments = normalize_comments(collected_comment_items, aweme_id)
        enriched_candidates.append({
            **item,
            'detail_status': 'success',
            'detail': {
                'title': detail.get('title') or detail.get('desc') or '',
                'desc': detail.get('desc') or '',
                'images': [url for url in str(detail.get('note_download_url') or '').split(',') if url],
                'comments': comments,
                'raw': detail,
            },
        })
        details_fetched += 1

    if len(candidates) > len(enriched_candidates):
        enriched_candidates.extend(candidates[len(enriched_candidates):])

    cache_dir = ensure_dir(ROOT / 'data' / 'douyin' / 'detail-cache')
    detail_cache_path = cache_dir / f'{run_id}.details.json'
    comment_cache_path = cache_dir / f'{run_id}.comments.json'
    write_json(detail_cache_path, collected_detail_items)
    write_json(comment_cache_path, collected_comment_items)

    enriched = {
        'run_id': run_id,
        'stage': 'douyin_enriched',
        'status': 'success',
        'generated_at': iso_now(),
        'keyword': data.get('keyword', ''),
        'source_input': args.input,
        'detail_fetch_limit': args.limit,
        'comment_limit': args.comment_limit,
        'candidate_count': len(candidates),
        'detail_success_count': details_fetched,
        'detail_cache_file': str(detail_cache_path),
        'comment_cache_file': str(comment_cache_path),
        'fetch_logs': fetch_logs,
        'candidates': enriched_candidates,
    }

    out_dir = ensure_dir(ROOT / 'data' / 'douyin' / 'enriched')
    out_path = out_dir / f'{run_id}.json'
    write_json(out_path, enriched)
    append_stage_manifest(run_id, 'douyin-enriched-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'input': args.input,
        'output': str(out_path),
        'detail_cache_file': str(detail_cache_path),
        'comment_cache_file': str(comment_cache_path),
        'detail_success_count': details_fetched,
    })
    print(out_path)


if __name__ == '__main__':
    main()
