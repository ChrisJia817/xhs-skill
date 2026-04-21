import argparse
import subprocess
import os
import shutil
from bootstrap import ROOT
from vendor_paths import AUTO_REDBOOK_DIR
from common import append_stage_manifest, iso_now

MIN_TOTAL_IMAGES = 4


def ensure_min_images(run_dir):
    pngs = sorted(run_dir.glob('*.png'))
    count = len(pngs)
    if count >= MIN_TOTAL_IMAGES:
        return count, [], False

    needed = MIN_TOTAL_IMAGES - count
    existing_cards = sorted(run_dir.glob('card_*.png'))
    next_idx = 1
    if existing_cards:
        nums = []
        for p in existing_cards:
            stem = p.stem.replace('card_', '')
            if stem.isdigit():
                nums.append(int(stem))
        if nums:
            next_idx = max(nums) + 1

    source_candidates = []
    cover = run_dir / 'cover.png'
    if cover.exists() and cover.stat().st_size > 0:
        source_candidates.append(cover)
    for p in existing_cards:
        if p.exists() and p.stat().st_size > 0:
            source_candidates.append(p)

    if not source_candidates:
        raise SystemExit('No non-empty rendered images available for fallback duplication.')

    duplicated = []
    idx = 0
    for _ in range(needed):
        source = source_candidates[idx % len(source_candidates)]
        target = run_dir / f'card_{next_idx}.png'
        shutil.copyfile(source, target)
        duplicated.append({'from': str(source), 'to': str(target)})
        next_idx += 1
        idx += 1

    return len(sorted(run_dir.glob('*.png'))), duplicated, True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--theme', default='professional')
    parser.add_argument('--mode', default='auto-split')
    parser.add_argument('--backend', default='upstream', choices=['upstream', 'placeholder'])
    args = parser.parse_args()

    run_dir = ROOT / 'data' / 'renders' / args.run_id
    md_path = run_dir / 'content.md'
    if not md_path.exists():
        append_stage_manifest(args.run_id, 'render', {
            'status': 'failed',
            'finished_at': iso_now(),
            'reason': 'markdown_missing',
            'markdown_path': str(md_path),
        })
        raise SystemExit(f'Markdown not found: {md_path}')

    for p in run_dir.glob('cover.png'):
        p.unlink(missing_ok=True)
    for p in run_dir.glob('card_*.png'):
        p.unlink(missing_ok=True)

    render_stdout = ''
    render_stderr = ''
    if args.backend == 'placeholder':
        for name in ['cover.png', 'card_1.png', 'card_2.png', 'card_3.png']:
            (run_dir / name).write_bytes(b'placeholder')
    else:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        cmd = [
            'python',
            str(AUTO_REDBOOK_DIR / 'scripts' / 'render_xhs.py'),
            str(md_path),
            '--output-dir', str(run_dir),
            '--theme', args.theme,
            '--mode', args.mode,
        ]
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore', env=env)
        render_stdout = (result.stdout or '').strip()
        render_stderr = (result.stderr or '').strip()
        if result.returncode != 0:
            append_stage_manifest(args.run_id, 'render', {
                'status': 'failed',
                'finished_at': iso_now(),
                'reason': 'renderer_failed',
                'backend': args.backend,
                'stdout_tail': render_stdout[-800:],
                'stderr_tail': render_stderr[-800:],
            })
            raise SystemExit(result.stderr or result.stdout)

    final_count, duplicated, degraded_by_duplication = ensure_min_images(run_dir)
    manifest = run_dir / 'render_manifest.txt'
    manifest.write_text(
        f'theme={args.theme}\nmode={args.mode}\nsource={md_path}\nbackend={args.backend}\nstatus=rendered\nimage_count={final_count}\nduplicated_count={len(duplicated)}\ndegraded_by_duplication={str(degraded_by_duplication).lower()}\n',
        encoding='utf-8'
    )
    append_stage_manifest(args.run_id, 'render-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'backend': args.backend,
        'theme': args.theme,
        'mode': args.mode,
        'output_dir': str(run_dir),
        'image_count': final_count,
        'duplicated_assets': duplicated,
        'degraded_by_duplication': degraded_by_duplication,
        'stdout_tail': render_stdout[-800:],
        'stderr_tail': render_stderr[-800:],
    })
    print(run_dir)


if __name__ == '__main__':
    main()
