import shutil
import subprocess
from pathlib import Path
from vendor_paths import resolve_mediacrawler_root, resolve_mediacrawler_output, resolve_wechat_api_script
from vendor_paths import XHS_CONFIG_DIR
from common import read_json, resolve_account_profile_dir


def check_path(name: str, path: Path) -> tuple[str, bool, str]:
    exists = path.exists()
    return name, exists, str(path)


def check_command(name: str, cmd: list[str]) -> tuple[str, bool, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        ok = result.returncode == 0
        tail = (result.stdout or result.stderr or '').strip()[-300:]
        return name, ok, tail or f'returncode={result.returncode}'
    except Exception as exc:
        return name, False, repr(exc)


def main():
    checks = []
    uv = shutil.which('uv')
    checks.append(('uv', uv is not None, uv or 'missing'))
    bun = shutil.which('bun')
    npx = shutil.which('npx')
    checks.append(('bun_or_npx', bool(bun or npx), bun or npx or 'missing'))

    mc_root = resolve_mediacrawler_root()
    mc_output = resolve_mediacrawler_output()
    wechat_api = resolve_wechat_api_script()

    checks.append(check_path('mediacrawler_root', mc_root))
    checks.append(check_path('mediacrawler_output', mc_output))
    checks.append(check_path('wechat_api_script', wechat_api))

    accounts_file = XHS_CONFIG_DIR / 'accounts.json'
    checks.append(check_path('xhs_accounts_config', accounts_file))

    if accounts_file.exists():
        try:
            data = read_json(accounts_file)
            default_key = data.get('default_account', '')
            configured_profile = ((data.get('accounts') or {}).get(default_key) or {}).get('profile_dir') or ''
            profile_dir = resolve_account_profile_dir(default_key, configured_profile)
            checks.append(('xhs_default_profile_dir', profile_dir.exists(), str(profile_dir)))
        except Exception as exc:
            checks.append(('xhs_accounts_parse', False, repr(exc)))

    if uv:
        checks.append(check_command('uv_version', [uv, '--version']))
        if mc_root.exists():
            checks.append(check_command('mediacrawler_uv_smoke', [uv, 'run', 'python', '--version']))
    if bun:
        checks.append(check_command('bun_version', [bun, '--version']))
    elif npx:
        checks.append(check_command('npx_version', [npx, '--version']))

    print('environment_check')
    print('hint: set XHS_DOUYIN_MEDIACRAWLER_ROOT / XHS_DOUYIN_OUTPUT_ROOT / XHS_WECHAT_API_SCRIPT / XHS_PROFILE_DIR if paths differ on this machine.')
    failed = 0
    for name, ok, detail in checks:
        status = 'OK' if ok else 'FAIL'
        if not ok:
            failed += 1
        print(f'[{status}] {name}: {detail}')

    if failed:
        raise SystemExit(f'{failed} environment check(s) failed')


if __name__ == '__main__':
    main()
