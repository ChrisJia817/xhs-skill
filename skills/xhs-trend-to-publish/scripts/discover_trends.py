import argparse
import subprocess
import json
import re
from bootstrap import ROOT
from common import new_run_id, write_json, ensure_dir, append_stage_manifest, iso_now


def build_mock_candidates(keyword: str, publish_time: str):
    return [
        {
            "note_id": "mock-note-001",
            "title": f"{keyword}现在还能做吗",
            "url": "https://www.xiaohongshu.com/explore/mock-note-001",
            "author": "mock-author-a",
            "publish_time": publish_time,
            "like_count": 1280,
            "comment_count": 196,
            "collect_count": 402,
            "summary": f"围绕{keyword}的趋势判断与实操争议",
            "comment_signals": ["还能不能做", "新手能不能入场", "现在风险大不大"],
            "source_type": "mock-search"
        },
        {
            "note_id": "mock-note-002",
            "title": f"做{keyword}最容易踩的3个坑",
            "url": "https://www.xiaohongshu.com/explore/mock-note-002",
            "author": "mock-author-b",
            "publish_time": "30天内",
            "like_count": 860,
            "comment_count": 88,
            "collect_count": 260,
            "summary": f"新手做{keyword}时常见误区与避坑提醒",
            "comment_signals": ["是不是违规", "容易翻车在哪", "新手先做什么"],
            "source_type": "mock-search"
        }
    ]


def discover_mock(keyword: str, publish_time: str):
    candidates = build_mock_candidates(keyword, publish_time)
    return candidates, {
        'backend': 'mock',
        'raw_items': len(candidates),
        'parsed_items': len(candidates),
        'kept_candidates': len(candidates),
        'parse_status': 'ok',
        'stdout_tail': '',
    }


def safe_int(value) -> int:
    text = str(value or '0').replace(',', '').strip()
    digits = re.sub(r'[^\d]', '', text)
    return int(digits or 0)


def infer_comment_signals(title: str, summary: str) -> list[str]:
    corpus = f"{title}\n{summary}"
    signals = []
    for token in ['还能做吗', '能不能做', '新手', '入门', '避坑', '风险', '违规', '怎么做', '步骤']:
        if token in corpus:
            signals.append(token)
    return signals[:5]


def discover_cdp(
    keyword: str,
    publish_time: str,
    account: str = '',
    run_id: str = 'unknown',
    sort_by: str = '最多点赞',
    note_type: str = '图文',
    search_scope: str = '不限',
    location: str = '不限',
):
    cmd = [
        'python',
        str(ROOT / 'vendor' / 'XiaohongshuSkills' / 'scripts' / 'cdp_publish.py'),
    ]
    if account:
        cmd.extend(['--account', account])
    cmd.extend([
        'search-feeds',
        '--keyword', keyword,
        '--sort-by', sort_by,
        '--note-type', note_type,
        '--publish-time', publish_time,
        '--search-scope', search_scope,
        '--location', location,
    ])
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    stdout = (result.stdout or '').strip()
    stderr = (result.stderr or '').strip()
    if result.returncode != 0:
        append_stage_manifest(run_id, 'discover', {
            'status': 'failed',
            'finished_at': iso_now(),
            'backend': 'cdp',
            'keyword': keyword,
            'account': account,
            'sort_by': sort_by,
            'note_type': note_type,
            'publish_time': publish_time,
            'search_scope': search_scope,
            'location': location,
            'returncode': result.returncode,
            'stdout_tail': stdout[-800:],
            'stderr_tail': stderr[-800:],
        })
        raise SystemExit(result.stderr or result.stdout)

    m = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])\s*$', stdout)
    if not m:
        fallback = [{
            'note_id': '',
            'title': f'真实搜索执行成功，但暂未解析出 JSON：{keyword}',
            'url': '',
            'author': 'system',
            'publish_time': publish_time,
            'like_count': 0,
            'comment_count': 0,
            'collect_count': 0,
            'summary': stdout[-500:],
            'comment_signals': [],
            'source_type': 'cdp-search-unparsed'
        }]
        return fallback, {
            'backend': 'cdp',
            'raw_items': 0,
            'parsed_items': 0,
            'kept_candidates': 1,
            'parse_status': 'unparsed-json-fallback',
            'stdout_tail': stdout[-800:],
            'stderr_tail': stderr[-800:],
        }

    try:
        payload = json.loads(m.group(1))
    except Exception as exc:
        fallback = [{
            'note_id': '',
            'title': f'真实搜索结果解析失败：{keyword}',
            'url': '',
            'author': 'system',
            'publish_time': publish_time,
            'like_count': 0,
            'comment_count': 0,
            'collect_count': 0,
            'summary': stdout[-500:],
            'comment_signals': [],
            'source_type': 'cdp-search-json-decode-failed'
        }]
        return fallback, {
            'backend': 'cdp',
            'raw_items': 0,
            'parsed_items': 0,
            'kept_candidates': 1,
            'parse_status': 'json-decode-failed',
            'json_error': repr(exc),
            'stdout_tail': stdout[-800:],
            'stderr_tail': stderr[-800:],
        }

    items = payload if isinstance(payload, list) else payload.get('items') or payload.get('feeds') or payload.get('data') or []
    if not isinstance(items, list):
        fallback = [{
            'note_id': '',
            'title': f'真实搜索结果结构异常：{keyword}',
            'url': '',
            'author': 'system',
            'publish_time': publish_time,
            'like_count': 0,
            'comment_count': 0,
            'collect_count': 0,
            'summary': stdout[-500:],
            'comment_signals': [],
            'source_type': 'cdp-search-structure-invalid'
        }]
        return fallback, {
            'backend': 'cdp',
            'raw_items': 0,
            'parsed_items': 0,
            'kept_candidates': 1,
            'parse_status': 'json-structure-invalid',
            'stdout_tail': stdout[-800:],
            'stderr_tail': stderr[-800:],
        }
    candidates = []
    filtered_out = 0
    for item in items[:20]:
        if not isinstance(item, dict):
            filtered_out += 1
            continue
        if item.get('modelType') != 'note' or not item.get('noteCard'):
            filtered_out += 1
            continue
        note = item.get('noteCard') or {}
        user = note.get('user') or {}
        interact = note.get('interactInfo') or {}
        corner = note.get('cornerTagInfo') or []
        publish_label = publish_time
        if corner and isinstance(corner, list) and isinstance(corner[0], dict):
            publish_label = corner[0].get('text') or publish_time
        title = note.get('displayTitle') or '未命名笔记'
        summary = note.get('displayTitle') or ''
        candidates.append({
            'note_id': item.get('id') or '',
            'title': title,
            'url': f"https://www.xiaohongshu.com/explore/{item.get('id')}?xsec_token={item.get('xsecToken','')}&xsec_source=pc_feed" if item.get('id') and item.get('xsecToken') else '',
            'author': user.get('nickname') or user.get('nickName') or '',
            'publish_time': publish_label,
            'like_count': safe_int(interact.get('likedCount', 0)),
            'comment_count': safe_int(interact.get('commentCount', 0)),
            'collect_count': safe_int(interact.get('collectedCount', 0)),
            'summary': summary,
            'comment_signals': infer_comment_signals(title, summary),
            'xsec_token': item.get('xsecToken') or '',
            'source_type': 'cdp-search'
        })
    return candidates, {
        'backend': 'cdp',
        'raw_items': len(items),
        'parsed_items': len(items),
        'kept_candidates': len(candidates),
        'filtered_out': filtered_out,
        'parse_status': 'ok',
        'stdout_tail': stdout[-800:],
        'stderr_tail': stderr[-800:],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', required=True)
    parser.add_argument('--publish-time', default='半年内')
    parser.add_argument('--backend', default='mock', choices=['mock', 'cdp'])
    parser.add_argument('--account', default='')
    parser.add_argument('--run-id', default='')
    parser.add_argument('--sort-by', default='最多点赞')
    parser.add_argument('--note-type', default='图文')
    parser.add_argument('--search-scope', default='不限')
    parser.add_argument('--location', default='不限')
    args = parser.parse_args()

    run_id = args.run_id or new_run_id('xhs')
    out_dir = ensure_dir(ROOT / 'data' / 'trends' / 'raw')
    if args.backend == 'cdp':
        candidates, discover_meta = discover_cdp(
            args.keyword,
            args.publish_time,
            args.account,
            run_id=run_id,
            sort_by=args.sort_by,
            note_type=args.note_type,
            search_scope=args.search_scope,
            location=args.location,
        )
    else:
        candidates, discover_meta = discover_mock(args.keyword, args.publish_time)

    payload = {
        'run_id': run_id,
        'stage': 'discover',
        'status': 'success',
        'generated_at': iso_now(),
        'keyword': args.keyword,
        'publish_time': args.publish_time,
        'backend': args.backend,
        'account': args.account,
        'candidate_count': len(candidates),
        'discover_meta': {
            **discover_meta,
            'sort_by': args.sort_by,
            'note_type': args.note_type,
            'search_scope': args.search_scope,
            'location': args.location,
        },
        'candidates': candidates,
    }
    out_path = out_dir / f'{run_id}.json'
    write_json(out_path, payload)
    append_stage_manifest(run_id, 'discover-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'keyword': args.keyword,
        'publish_time': args.publish_time,
        'backend': args.backend,
        'account': args.account,
        'output': str(out_path),
        'candidate_count': len(candidates),
        'discover_meta': discover_meta,
    })
    print(out_path)


if __name__ == '__main__':
    main()
