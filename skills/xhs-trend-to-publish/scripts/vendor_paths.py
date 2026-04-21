import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent.parent
VENDOR_DIR = ROOT / 'vendor'
XHS_SKILLS_DIR = VENDOR_DIR / 'XiaohongshuSkills'
AUTO_REDBOOK_DIR = VENDOR_DIR / 'Auto-Redbook-Skills'
XHS_SCRIPTS_DIR = XHS_SKILLS_DIR / 'scripts'
XHS_CONFIG_DIR = XHS_SKILLS_DIR / 'config'


def _env_path(name: str) -> Path | None:
    value = os.environ.get(name, '').strip()
    return Path(value).expanduser() if value else None


def _resolve_path(env_name: str, defaults: list[Path]) -> Path:
    env_path = _env_path(env_name)
    candidates = [env_path, *defaults]
    for path in candidates:
        if path and path.exists():
            return path
    return env_path or defaults[0]


def resolve_mediacrawler_root() -> Path:
    return _resolve_path(
        'XHS_DOUYIN_MEDIACRAWLER_ROOT',
        [
            WORKSPACE_ROOT / 'external' / 'MediaCrawler',
            VENDOR_DIR / 'MediaCrawler',
        ],
    )


def resolve_mediacrawler_output() -> Path:
    return _resolve_path(
        'XHS_DOUYIN_OUTPUT_ROOT',
        [
            ROOT / 'data' / 'douyin' / 'raw',
            WORKSPACE_ROOT / 'external-data' / 'douyin' / 'json',
        ],
    )


def resolve_wechat_api_script() -> Path:
    return _resolve_path(
        'XHS_WECHAT_API_SCRIPT',
        [
            WORKSPACE_ROOT / 'external' / 'baoyu-post-to-wechat' / 'scripts' / 'wechat-api.ts',
            WORKSPACE_ROOT / 'skills' / 'baoyu-post-to-wechat' / 'scripts' / 'wechat-api.ts',
        ],
    )
