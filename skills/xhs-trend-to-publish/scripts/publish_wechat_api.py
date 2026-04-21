import argparse
import subprocess
import shutil
from pathlib import Path
from bootstrap import ROOT
from common import read_json, append_stage_manifest, iso_now
from vendor_paths import resolve_wechat_api_script

BAOYU_WECHAT_API = resolve_wechat_api_script()
WORKSPACE_ROOT = ROOT.parent.parent


def resolve_bun_command() -> list[str]:
    bun = shutil.which('bun')
    if bun:
        return [bun]
    npx = shutil.which('npx')
    if npx:
        return [npx, '-y', 'bun']
    raise SystemExit('Neither bun nor npx is available; cannot invoke baoyu wechat API script')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--cover', required=True)
    parser.add_argument('--theme', default='default')
    parser.add_argument('--account', default='')
    args = parser.parse_args()

    article = read_json(args.input)
    markdown_path = ROOT / 'data' / 'wechat-drafts' / f"{article['run_id']}.{article['template']}.md"
    if not markdown_path.exists():
        raise SystemExit(f'Wechat markdown not found: {markdown_path}')

    cmd = [
        *resolve_bun_command(), str(BAOYU_WECHAT_API),
        str(markdown_path),
        '--theme', args.theme,
        '--title', article.get('title', ''),
        '--summary', article.get('summary', ''),
        '--author', article.get('author', ''),
        '--cover', args.cover,
    ]
    if args.account:
        cmd.extend(['--account', args.account])

    result = subprocess.run(
        cmd,
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    stdout = (result.stdout or '').strip()
    stderr = (result.stderr or '').strip()

    append_stage_manifest(article['run_id'], 'wechat-publish-output', {
        'status': 'success' if result.returncode == 0 else 'failed',
        'finished_at': iso_now(),
        'input': args.input,
        'markdown_path': str(markdown_path),
        'cover': args.cover,
        'theme': args.theme,
        'account': args.account,
        'returncode': result.returncode,
        'stdout_tail': stdout[-1200:],
        'stderr_tail': stderr[-1200:],
    })

    if result.returncode != 0:
        raise SystemExit(stderr or stdout or 'WeChat API publish failed')

    print(stdout or 'WeChat API publish finished')


if __name__ == '__main__':
    main()
