import argparse
import subprocess
import json
import re
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
        raise SystemExit('Could not parse JSON payload from list-feeds output.')
    return json.loads(match.group(1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='')
    parser.add_argument('--account', default='')
    args = parser.parse_args()

    run_id = args.run_id or new_run_id('xhs-home')
    cmd = ['python', str(XHS_SCRIPTS_DIR / 'cdp_publish.py')]
    if args.account:
        cmd.extend(['--account', args.account])
    cmd.append('list-feeds')

    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    stdout = (result.stdout or '').strip()
    stderr = (result.stderr or '').strip()
    if result.returncode != 0:
        raise SystemExit(stderr or stdout or 'list-feeds failed')

    payload = parse_result(stdout, 'LIST_FEEDS_RESULT:')
    out = {
        'run_id': run_id,
        'stage': 'xhs_home_feeds',
        'status': 'success',
        'generated_at': iso_now(),
        'account': args.account,
        'source': 'vendor-list-feeds',
        'payload': payload,
    }
    out_dir = ensure_dir(ROOT / 'data' / 'trends' / 'home-feeds')
    out_path = out_dir / f'{run_id}.json'
    write_json(out_path, out)
    append_stage_manifest(run_id, 'xhs-home-feeds-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'account': args.account,
        'output': str(out_path),
    })
    print(out_path)


if __name__ == '__main__':
    main()
