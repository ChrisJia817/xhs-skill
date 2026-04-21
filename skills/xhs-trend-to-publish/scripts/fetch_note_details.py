import argparse
import json
import re
import subprocess
import sys
from bootstrap import ROOT
from common import read_json, write_json, ensure_dir, append_stage_manifest, iso_now


def parse_detail_payload(text: str) -> dict:
    text = (text or '').strip()
    match = re.search(r'(\{[\s\S]*\})\s*$', text)
    if not match:
        raise SystemExit('Could not parse detail JSON from get-feed-detail output.')
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise SystemExit('Feed detail payload is not an object.')
    return payload


def extract_note_content(payload: dict) -> dict:
    detail_root = payload.get('detail') or {}
    note = detail_root.get('note') or payload.get('note') or payload.get('noteCard') or payload.get('note_card') or {}
    comments_root = detail_root.get('comments') or payload.get('comments') or payload.get('commentList') or {}
    interact = note.get('interactInfo') or {}

    desc = note.get('desc') or note.get('description') or ''
    title = note.get('title') or note.get('displayTitle') or payload.get('title') or ''

    content_images = []
    image_list = note.get('imageList') or note.get('imagesList') or []
    if isinstance(image_list, list):
        for item in image_list[:12]:
            if isinstance(item, dict):
                img_url = item.get('urlDefault') or item.get('url') or item.get('urlPre') or ''
                if not img_url:
                    info_list = item.get('infoList') or []
                    if isinstance(info_list, list):
                        for info in info_list:
                            if isinstance(info, dict) and info.get('url'):
                                img_url = info.get('url')
                                break
                if img_url:
                    content_images.append(img_url)

    extracted_comments = []
    comment_list = comments_root.get('list') if isinstance(comments_root, dict) else comments_root
    if isinstance(comment_list, list):
        for item in comment_list[:20]:
            if not isinstance(item, dict):
                continue
            text = item.get('content') or item.get('text') or ''
            user = item.get('userInfo') or item.get('user') or {}
            sub_comments = item.get('subComments') or []
            extracted_comments.append({
                'content': text,
                'author': user.get('nickname') or user.get('nickName') or '',
                'sub_comments': [
                    {
                        'content': sub.get('content') or '',
                        'author': (sub.get('userInfo') or {}).get('nickname') or '',
                    }
                    for sub in sub_comments[:5] if isinstance(sub, dict)
                ],
            })

    return {
        'title': title,
        'desc': desc,
        'like_count': note.get('likeCount') or interact.get('likedCount') or 0,
        'comment_count': note.get('commentCount') or interact.get('commentCount') or 0,
        'collect_count': note.get('collectCount') or interact.get('collectedCount') or 0,
        'images': content_images,
        'comments': extracted_comments,
        'raw': payload,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--account', default='')
    parser.add_argument('--limit', type=int, default=5)
    args = parser.parse_args()

    data = read_json(args.input)
    candidates = data.get('candidates', [])
    if not candidates:
        append_stage_manifest(data.get('run_id', 'unknown'), 'fetch_note_details', {
            'status': 'failed',
            'finished_at': iso_now(),
            'input': args.input,
            'reason': 'no_candidates_available',
        })
        raise SystemExit('No candidates available for detail enrichment.')

    enriched_candidates = []
    details_fetched = 0
    for item in candidates[:max(1, args.limit)]:
        note_id = item.get('note_id', '')
        xsec_token = item.get('xsec_token', '')
        if not note_id or not xsec_token:
            enriched_candidates.append({
                **item,
                'detail_status': 'skipped-missing-id-or-token',
            })
            continue

        cmd = [
            sys.executable,
            str(ROOT / 'vendor' / 'XiaohongshuSkills' / 'scripts' / 'cdp_publish.py'),
        ]
        if args.account:
            cmd.extend(['--account', args.account])
        cmd.extend([
            'get-feed-detail',
            '--feed-id', note_id,
            '--xsec-token', xsec_token,
        ])

        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        stdout = (result.stdout or '').strip()
        stderr = (result.stderr or '').strip()

        if result.returncode != 0:
            enriched_candidates.append({
                **item,
                'detail_status': 'failed',
                'detail_error': stderr or stdout,
            })
            continue

        try:
            payload = parse_detail_payload(stdout)
            detail = extract_note_content(payload)
            enriched_candidates.append({
                **item,
                'detail_status': 'success',
                'detail': detail,
            })
            details_fetched += 1
        except Exception as exc:
            enriched_candidates.append({
                **item,
                'detail_status': 'parse-failed',
                'detail_error': repr(exc),
            })

    if len(candidates) > len(enriched_candidates):
        enriched_candidates.extend(candidates[len(enriched_candidates):])

    out = {
        'run_id': data['run_id'],
        'stage': 'enriched',
        'status': 'success',
        'generated_at': iso_now(),
        'keyword': data.get('keyword', ''),
        'publish_time': data.get('publish_time', ''),
        'backend': data.get('backend', ''),
        'account': args.account or data.get('account', ''),
        'source_input': args.input,
        'detail_fetch_limit': args.limit,
        'detail_success_count': details_fetched,
        'candidate_count': len(candidates),
        'candidates': enriched_candidates,
    }

    out_dir = ensure_dir(ROOT / 'data' / 'trends' / 'enriched')
    out_path = out_dir / f"{data['run_id']}.json"
    write_json(out_path, out)
    append_stage_manifest(data['run_id'], 'fetch-note-details-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'input': args.input,
        'output': str(out_path),
        'detail_success_count': details_fetched,
        'candidate_count': len(candidates),
        'account': out['account'],
    })
    print(out_path)


if __name__ == '__main__':
    main()
