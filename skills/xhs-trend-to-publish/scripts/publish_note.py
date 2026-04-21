import argparse
import traceback
from datetime import datetime
from pathlib import Path

from bootstrap import ROOT
from common import write_json, read_json, append_stage_manifest, iso_now
from vendor_paths import XHS_SKILLS_DIR


def ordered_assets(render_dir: Path):
    cover = sorted(render_dir.glob('cover.png'))
    cards = sorted(render_dir.glob('card_*.png'))
    return [str(p) for p in cover + cards]


def resolve_selected_draft(draft_data: dict, draft_index: int | None) -> tuple[int, dict]:
    drafts = draft_data.get('drafts') or []
    if not drafts:
        raise ValueError('No drafts found in draft data')
    if draft_index is None:
        draft_index = draft_data.get('best_draft_index', 0)
    if draft_index < 0 or draft_index >= len(drafts):
        raise IndexError(f'draft_index out of range: {draft_index}')
    return draft_index, drafts[draft_index]


def load_draft(run_id: str, draft_index: int | None = None):
    draft_path = ROOT / 'data' / 'drafts' / f'{run_id}.json'
    if not draft_path.exists():
        raise FileNotFoundError(f'Draft file not found: {draft_path}')
    draft_data = read_json(draft_path)
    selected_index, draft = resolve_selected_draft(draft_data, draft_index)
    return draft_path, draft_data, selected_index, draft


def try_import_save_to_draft():
    import sys
    vendor_scripts = XHS_SKILLS_DIR / 'scripts'
    if str(vendor_scripts) not in sys.path:
        sys.path.insert(0, str(vendor_scripts))
    try:
        from test_save_draft_same_session import save_to_draft_box
        return save_to_draft_box, None
    except Exception as exc:
        return None, repr(exc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--account', default='')
    parser.add_argument('--accounts', nargs='*', default=[])
    parser.add_argument('--mode', default='draft', choices=['draft', 'private', 'public', 'scheduled'])
    parser.add_argument('--backend', default='cdp', choices=['mock', 'cookie', 'cdp'])
    parser.add_argument('--draft-index', type=int, default=None)
    args = parser.parse_args()

    render_dir = ROOT / 'data' / 'renders' / args.run_id
    assets = ordered_assets(render_dir)
    account_targets = args.accounts or ([args.account] if args.account else [''])

    status = 'skipped'
    note_id = ''
    url = ''
    selected_draft_index = None
    selected_draft_title = ''
    details = {
        'fill': None,
        'topics': None,
        'save_and_leave': None,
        'publish': None,
        'exceptions': [],
        'dependency_checks': {},
    }

    try:
        draft_path, draft_data, selected_draft_index, draft = load_draft(args.run_id, args.draft_index)
        selected_draft_title = draft.get('title', '')
        if not assets:
            raise ValueError(f'No assets found under {render_dir}')

        if args.backend == 'cdp':
            if args.mode != 'draft':
                raise NotImplementedError(f'{args.mode} mode is not fully implemented for cdp backend; currently only draft is supported safely')
            from topic_helper import extract_topic_tags_from_last_line, select_topics
            from topic_strategy import build_topic_tags
            import sys
            vendor_scripts = XHS_SKILLS_DIR / 'scripts'
            if str(vendor_scripts) not in sys.path:
                sys.path.insert(0, str(vendor_scripts))
            from cdp_publish import XiaohongshuPublisher, XHS_CREATOR_URL

            save_to_draft_box, draft_import_error = try_import_save_to_draft()
            details['dependency_checks']['save_to_draft_box'] = {
                'available': save_to_draft_box is not None,
                'error': draft_import_error,
            }
            if args.mode == 'draft' and save_to_draft_box is None:
                raise ImportError(f'Draft mode requested but save_to_draft_box is unavailable: {draft_import_error}')

            keyword = draft_data.get('keyword', '')
            body_without_tags, _ = extract_topic_tags_from_last_line(draft.get('body', ''))
            tags = build_topic_tags(keyword, draft.get('title', ''), draft.get('body', ''))

            details['fill'] = {
                'returncode': 0,
                'title': (draft.get('title') or '')[:20],
                'assets': assets,
                'account': account_targets[0],
                'accounts': account_targets,
                'draft_path': str(draft_path),
                'draft_index': selected_draft_index,
            }

            publish_runs = []
            for current_account in account_targets:
                run_detail = {'account': current_account, 'status': 'pending'}
                publisher = None
                try:
                    publisher_kwargs = {}
                    if current_account:
                        publisher_kwargs['account_name'] = current_account
                    publisher = XiaohongshuPublisher(**publisher_kwargs)
                    publisher.connect()
                    publisher._navigate(XHS_CREATOR_URL)
                    publisher._sleep(2, minimum_seconds=1.0)
                    publisher._click_image_text_tab()
                    publisher._sleep(2, minimum_seconds=1.0)
                    publisher._upload_images(assets)
                    publisher._sleep(2, minimum_seconds=1.0)
                    publisher._fill_title((draft.get('title') or '')[:20])
                    publisher._sleep(1, minimum_seconds=0.5)
                    publisher._fill_content(body_without_tags)
                    publisher._sleep(1, minimum_seconds=0.5)
                    topic_result = select_topics(publisher, tags)
                    run_detail['topics'] = topic_result
                    if not topic_result.get('ok'):
                        run_detail['status'] = 'failed'
                    elif args.mode == 'draft':
                        draft_result = save_to_draft_box(publisher)
                        run_detail['save_and_leave'] = draft_result
                        first = draft_result.get('first') if isinstance(draft_result, dict) else None
                        second = draft_result.get('second') if isinstance(draft_result, dict) else None
                        run_detail['status'] = 'success' if first and first.get('ok') and (second is None or second.get('ok')) else 'failed'
                    else:
                        run_detail['status'] = 'success'
                except Exception as account_exc:
                    run_detail['status'] = 'failed'
                    run_detail['error'] = repr(account_exc)
                    run_detail['traceback'] = traceback.format_exc()
                finally:
                    if publisher is not None:
                        try:
                            publisher.disconnect()
                        except Exception:
                            pass
                publish_runs.append(run_detail)

            details['publish_runs'] = publish_runs
            status = 'success' if publish_runs and all(run.get('status') == 'success' for run in publish_runs) else 'failed'
        elif args.backend == 'mock':
            status = 'success'
            note_id = f'mock-{args.run_id}'
            url = f'https://www.xiaohongshu.com/explore/mock-{args.run_id}'
        else:
            raise NotImplementedError('cookie backend is declared but not implemented yet')
    except Exception as exc:
        status = 'failed'
        details['exceptions'].append({
            'stage': 'main',
            'error': repr(exc),
            'traceback': traceback.format_exc(),
        })

    out = {
        'run_id': args.run_id,
        'stage': 'publish',
        'backend': args.backend,
        'mode': args.mode,
        'status': status,
        'published_at': datetime.now().isoformat(),
        'note_id': note_id,
        'url': url,
        'selected_draft_index': selected_draft_index,
        'selected_draft_title': selected_draft_title,
        'assets': assets,
        'detail': details,
    }
    out_path = ROOT / 'data' / 'publish-results' / f'{args.run_id}.json'
    write_json(out_path, out)
    append_stage_manifest(args.run_id, 'publish-output', {
        'status': status,
        'finished_at': iso_now(),
        'backend': args.backend,
        'mode': args.mode,
        'selected_draft_index': selected_draft_index,
        'selected_draft_title': selected_draft_title,
        'output': str(out_path),
        'asset_count': len(assets),
        'note_id': note_id,
        'url': url,
        'exceptions': details['exceptions'],
        'dependency_checks': details['dependency_checks'],
    })
    print(out_path)


if __name__ == '__main__':
    main()
