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


def _normalize_mediacrawler_output(path: Path | None) -> Path | None:
    if path is None:
        return None

    expanded = path.expanduser()
    path_name = expanded.name.lower()
    parent_name = expanded.parent.name.lower() if expanded.parent else ''

    if path_name == 'json':
        return expanded
    if path_name == 'douyin':
        return expanded / 'json'
    if parent_name == 'douyin':
        return expanded
    return expanded / 'douyin' / 'json'


def resolve_mediacrawler_root() -> Path:
    return _resolve_path(
        'XHS_DOUYIN_MEDIACRAWLER_ROOT',
        [
            VENDOR_DIR / 'MediaCrawler',
            WORKSPACE_ROOT / 'external' / 'MediaCrawler',
        ],
    )


def resolve_mediacrawler_output() -> Path:
    defaults = [
        ROOT / 'data' / 'douyin' / 'json',
        WORKSPACE_ROOT / 'external-data' / 'douyin' / 'json',
    ]
    env_path = _normalize_mediacrawler_output(_env_path('XHS_DOUYIN_OUTPUT_ROOT'))
    candidates = [env_path, *[_normalize_mediacrawler_output(path) for path in defaults]]
    for path in candidates:
        if path and path.exists():
            return path
    return env_path or candidates[1]


def resolve_mediacrawler_save_root() -> Path:
    output_root = resolve_mediacrawler_output()
    if output_root.name.lower() == 'json' and output_root.parent.name.lower() == 'douyin':
        return output_root.parent.parent
    if output_root.name.lower() == 'douyin':
        return output_root.parent
    return output_root


def resolve_wechat_api_script() -> Path:
    return _resolve_path(
        'XHS_WECHAT_API_SCRIPT',
        [
            WORKSPACE_ROOT / 'skills' / 'baoyu-post-to-wechat' / 'scripts' / 'wechat-api.ts',
            WORKSPACE_ROOT / 'external' / 'baoyu-post-to-wechat' / 'scripts' / 'wechat-api.ts',
        ],
    )
