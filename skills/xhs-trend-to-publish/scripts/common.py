import os
import json
import uuid
import importlib.util
from datetime import datetime
from pathlib import Path



def now_ts() -> str:
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def iso_now() -> str:
    return datetime.now().isoformat()


def new_run_id(prefix: str = 'xhs') -> str:
    return f"{prefix}-{now_ts()}-{uuid.uuid4().hex[:6]}"


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path: str | Path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return p


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_module(module_name: str, file_path: str | Path):
    file_path = str(file_path)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f'Cannot load module from {file_path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def account_env(account: str | None) -> dict:
    env = {}
    if account and account.strip():
        env['XHS_ACCOUNT'] = account.strip()
    return env


def resolve_account_profile_dir(account: str, configured_path: str | None) -> Path:
    account = (account or 'default').strip() or 'default'
    env_specific = os.environ.get(f'XHS_PROFILE_DIR_{account.upper()}', '').strip()
    if env_specific:
        return Path(env_specific).expanduser()
    env_default = os.environ.get('XHS_PROFILE_DIR', '').strip()
    if env_default:
        return Path(env_default).expanduser() / account
    if configured_path:
        return Path(configured_path).expanduser()
    return Path.home() / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'XiaohongshuProfiles' / account


def load_pipeline_config() -> dict:
    config_path = skill_root() / 'config' / 'pipeline.example.json'
    if not config_path.exists():
        return {}
    try:
        return read_json(config_path)
    except Exception:
        return {}


def resolve_wechat_account_settings(explicit_account: str | None = None) -> dict:
    config = load_pipeline_config()
    wechat = config.get('wechat') or {}
    accounts = wechat.get('accounts') or []
    if not isinstance(accounts, list):
        accounts = []

    chosen = None
    explicit = (explicit_account or '').strip()
    if explicit:
        for account in accounts:
            if (account.get('alias') or '').strip() == explicit:
                chosen = account
                break
        if chosen is None:
            return {'alias': explicit}
    elif len(accounts) == 1:
        chosen = accounts[0]
    else:
        for account in accounts:
            if account.get('default') is True:
                chosen = account
                break

    if chosen is None:
        return {}

    return {
        'alias': (chosen.get('alias') or '').strip(),
        'name': chosen.get('name') or '',
        'default_author': chosen.get('default_author') or '',
        'need_open_comment': chosen.get('need_open_comment'),
        'only_fans_can_comment': chosen.get('only_fans_can_comment'),
        'default_publish_method': chosen.get('default_publish_method') or '',
    }


def append_stage_manifest(run_id: str, stage: str, record: dict) -> Path:
    manifest_dir = ensure_dir(skill_root() / 'data' / 'runs')
    manifest_path = manifest_dir / f'{run_id}.json'
    if manifest_path.exists():
        manifest = read_json(manifest_path)
    else:
        manifest = {
            'run_id': run_id,
            'created_at': iso_now(),
            'stages': [],
        }
    manifest.setdefault('stages', []).append({
        'stage': stage,
        **record,
    })
    manifest['updated_at'] = iso_now()
    write_json(manifest_path, manifest)
    return manifest_path
