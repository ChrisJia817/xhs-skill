import argparse
import json
import re
import subprocess
import sys
from bootstrap import ROOT
from common import write_json, ensure_dir, new_run_id, append_stage_manifest, iso_now
from vendor_paths import XHS_SCRIPTS_DIR


def parse_result(stdout: str, marker: str) -> dict:
    text = (stdout or '').strip()
    idx = text.find(marker)
    if idx == -1:
        raise SystemExit(f'Could not find marker in output: {marker}')
    payload_text = text[idx + len(marker):].strip()
    match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])\s*$', payload_text)
    if not match:
        raise SystemExit(f'Could not parse JSON payload for marker: {marker}')
    return json.loads(match.group(1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='')
    parser.add_argument('--account', default='')
    parser.add_argument('--profile-url', default='')
    parser.add_argument('--user-id', default='')
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--max-scrolls', type=int, default=10)
    parser.add_argument('--snapshot', action='store_true')
    args = parser.parse_args()

    if not args.profile_url and not args.user_id:
        raise SystemExit('Either --profile-url or --user-id is required.')

    run_id = args.run_id or new_run_id('xhs-profile')
    cmd = [sys.executable, str(XHS_SCRIPTS_DIR / 'cdp_publish.py')]
    if args.account:
        cmd.extend(['--account', args.account])

    if args.snapshot:
        cmd.append('profile-snapshot')
        marker = 'PROFILE_SNAPSHOT_RESULT:'
    else:
        cmd.append('notes-from-profile')
        cmd.extend(['--limit', str(args.limit), '--max-scrolls', str(args.max_scrolls)])
        marker = 'PROFILE_NOTES_RESULT:'

    if args.profile_url:
        cmd.extend(['--profile-url', args.profile_url])
    else:
        cmd.extend(['--user-id', args.user_id])

    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    stdout = (result.stdout or '').strip()
    stderr = (result.stderr or '').strip()
    if result.returncode != 0:
        raise SystemExit(stderr or stdout or 'profile fetch failed')

    payload = parse_result(stdout, marker)
    out = {
        'run_id': run_id,
        'stage': 'xhs_profile_snapshot' if args.snapshot else 'xhs_profile_notes',
        'status': 'success',
        'generated_at': iso_now(),
        'account': args.account,
        'profile_url': args.profile_url,
        'user_id': args.user_id,
        'source': 'vendor-profile',
        'payload': payload,
    }
    folder = 'profile-snapshots' if args.snapshot else 'profile-notes'
    out_dir = ensure_dir(ROOT / 'data' / folder)
    out_path = out_dir / f'{run_id}.json'
    write_json(out_path, out)
    append_stage_manifest(run_id, 'xhs-profile-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'account': args.account,
        'profile_url': args.profile_url,
        'user_id': args.user_id,
        'snapshot': args.snapshot,
        'output': str(out_path),
    })
    print(out_path)


if __name__ == '__main__':
    main()
