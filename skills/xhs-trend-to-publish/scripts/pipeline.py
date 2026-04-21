import argparse
import os
import subprocess
import sys
from pathlib import Path
from common import read_json, append_stage_manifest, iso_now, new_run_id, resolve_wechat_account_settings

SKILL_ROOT = Path(__file__).resolve().parents[1]


def run_stage(cmd: list[str], cwd: str, run_id: str, stage: str, params: dict):
    started_at = iso_now()
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    stdout = (result.stdout or '').strip()
    stderr = (result.stderr or '').strip()
    output = stdout.splitlines()[-1] if stdout else ''
    append_stage_manifest(run_id, stage, {
        'status': 'success' if result.returncode == 0 else 'failed',
        'started_at': started_at,
        'finished_at': iso_now(),
        'command': cmd,
        'params': params,
        'returncode': result.returncode,
        'output': output,
        'stdout_tail': stdout[-800:] if stdout else '',
        'stderr_tail': stderr[-800:] if stderr else '',
    })
    if result.returncode != 0:
        raise SystemExit(stderr or stdout or f'{stage} failed')
    if not output:
        raise SystemExit(f'{stage} completed but returned no output path')
    return output


def run_xhs_branch(python: str, cwd: str, run_id: str, score_out: str, args, brief_input: str = '') -> dict:
    rewrite_input = score_out
    if args.xhs_rewrite_from == 'brief':
        if brief_input:
            brief_out = brief_input
        else:
            brief_out = run_stage([python, 'scripts/build_topic_brief.py', '--input', score_out], cwd, run_id, 'xhs_topic_brief', {
                'input': score_out,
                'platform': 'xhs',
                'rewrite_from': 'brief',
            })
        rewrite_input = brief_out
    rewrite_cmd = [python, 'scripts/rewrite_note.py', '--input', rewrite_input, '--theme', args.theme]
    if args.xhs_rewrite_from == 'brief':
        rewrite_cmd.extend(['--source-format', 'brief'])
    rewrite_out = run_stage(rewrite_cmd, cwd, run_id, 'rewrite', {
        'input': rewrite_input,
        'theme': args.theme,
        'rewrite_from': args.xhs_rewrite_from,
    })

    markdown_cmd = [python, 'scripts/build_render_markdown.py', '--input', rewrite_out, '--theme', args.theme]
    if args.draft_index is not None:
        markdown_cmd.extend(['--draft-index', str(args.draft_index)])
    md_out = run_stage(markdown_cmd, cwd, run_id, 'build_markdown', {
        'input': rewrite_out,
        'draft_index': args.draft_index,
        'theme': args.theme,
    })

    render_out = run_stage([python, 'scripts/render_cards.py', '--run-id', run_id, '--theme', args.theme, '--mode', args.render_mode, '--backend', args.render_backend], cwd, run_id, 'render', {
        'run_id': run_id,
        'theme': args.theme,
        'mode': args.render_mode,
        'backend': args.render_backend,
    })

    publish_cmd = [python, 'scripts/publish_note.py', '--run-id', run_id, '--mode', args.mode, '--backend', args.publish_backend]
    if args.account:
        publish_cmd.extend(['--account', args.account])
    if args.draft_index is not None:
        publish_cmd.extend(['--draft-index', str(args.draft_index)])
    publish_out = run_stage(publish_cmd, cwd, run_id, 'publish', {
        'run_id': run_id,
        'mode': args.mode,
        'backend': args.publish_backend,
        'account': args.account,
        'draft_index': args.draft_index,
        'theme': args.theme,
    })

    outputs = {
        'rewrite': rewrite_out,
        'markdown': md_out,
        'render': render_out,
        'publish': publish_out,
    }
    if args.xhs_rewrite_from == 'brief':
        outputs['xhs_topic_brief'] = rewrite_input
    return outputs


def run_wechat_branch(python: str, cwd: str, run_id: str, brief_input: str, args) -> dict:
    account_settings = resolve_wechat_account_settings(args.wechat_account)
    resolved_wechat_account = account_settings.get('alias') or args.wechat_account
    rewrite_cmd = [python, 'scripts/rewrite_wechat_article.py', '--input', brief_input, '--template', args.wechat_template]
    rewrite_out = run_stage(rewrite_cmd, cwd, run_id, 'wechat_rewrite', {
        'input': brief_input,
        'template': args.wechat_template,
        'account': resolved_wechat_account,
        'account_settings': account_settings,
    })

    md_out = run_stage([python, 'scripts/format_wechat_markdown.py', '--input', rewrite_out, '--cover', args.wechat_cover], cwd, run_id, 'wechat_format_markdown', {
        'input': rewrite_out,
        'cover': args.wechat_cover,
    })

    outputs = {
        'rewrite': rewrite_out,
        'markdown': md_out,
    }

    if args.wechat_publish:
        publish_cmd = [python, 'scripts/publish_wechat_api.py', '--input', rewrite_out, '--cover', args.wechat_cover, '--theme', args.wechat_theme]
        if resolved_wechat_account:
            publish_cmd.extend(['--account', resolved_wechat_account])
        publish_out = run_stage(publish_cmd, cwd, run_id, 'wechat_publish', {
            'input': rewrite_out,
            'cover': args.wechat_cover,
            'theme': args.wechat_theme,
            'account': resolved_wechat_account,
            'account_settings': account_settings,
        })
        outputs['publish'] = publish_out

    return outputs


def run_unified_brief_pipeline(python: str, cwd: str, run_id: str, args) -> dict:
    outputs = {}
    xhs_score_out = ''
    douyin_enriched_out = ''

    if 'xhs' in args.sources:
        discover_cmd = [python, 'scripts/discover_trends.py', '--keyword', args.keyword, '--publish-time', args.publish_time, '--backend', args.discover_backend, '--run-id', run_id]
        if args.account:
            discover_cmd.extend(['--account', args.account])
        xhs_discover_out = run_stage(discover_cmd, cwd, run_id, 'discover-bootstrap', {
            'keyword': args.keyword,
            'publish_time': args.publish_time,
            'backend': args.discover_backend,
            'account': args.account,
            'source': 'xhs',
        })
        if args.xhs_reading_sources:
            home_out = ''
            profile_inputs = []
            if 'home' in args.xhs_reading_sources:
                home_cmd = [python, 'scripts/discover_home_feeds.py', '--run-id', run_id]
                if args.account:
                    home_cmd.extend(['--account', args.account])
                home_out = run_stage(home_cmd, cwd, run_id, 'xhs_home_feeds', {
                    'account': args.account,
                })
            if 'profiles' in args.xhs_reading_sources:
                scored_seed = run_stage([python, 'scripts/score_trends.py', '--input', xhs_discover_out], cwd, run_id, 'xhs_seed_score', {
                    'input': xhs_discover_out,
                })
                seed_data = read_json(scored_seed)
                for idx, item in enumerate(seed_data.get('selected', [])[:2]):
                    raw_user = ((item.get('raw') or {}).get('noteCard') or {}).get('user') or {}
                    user_id = raw_user.get('userId') or raw_user.get('user_id') or ''
                    if not user_id:
                        continue
                    profile_cmd = [python, 'scripts/fetch_profile_notes.py', '--run-id', f'{run_id}-profile-{idx}', '--user-id', str(user_id), '--limit', '10', '--max-scrolls', '3']
                    if args.account:
                        profile_cmd.extend(['--account', args.account])
                    profile_out = run_stage(profile_cmd, cwd, run_id, f'xhs_profile_notes_{idx}', {
                        'account': args.account,
                        'user_id': str(user_id),
                    })
                    profile_inputs.append(profile_out)
            reading_pool_cmd = [python, 'scripts/build_xhs_reading_pool.py', '--run-id', run_id, '--keyword', args.keyword]
            if 'search' in args.xhs_reading_sources or not args.xhs_reading_sources:
                reading_pool_cmd.extend(['--search-input', xhs_discover_out])
            if home_out:
                reading_pool_cmd.extend(['--home-feeds-input', home_out])
            if profile_inputs:
                reading_pool_cmd.extend(['--profile-notes-inputs', *profile_inputs])
            xhs_reading_pool_out = run_stage(reading_pool_cmd, cwd, run_id, 'xhs_reading_pool', {
                'search_input': xhs_discover_out,
                'home_feeds_input': home_out,
                'profile_notes_inputs': profile_inputs,
                'reading_sources': args.xhs_reading_sources,
            })
            xhs_score_out = run_stage([python, 'scripts/score_trends.py', '--input', xhs_reading_pool_out], cwd, run_id, 'score', {
                'input': xhs_reading_pool_out,
                'source': 'xhs-reading-pool',
            })
            outputs['xhs_reading_pool'] = xhs_reading_pool_out
        else:
            xhs_score_out = run_stage([python, 'scripts/score_trends.py', '--input', xhs_discover_out], cwd, run_id, 'score', {
                'input': xhs_discover_out,
                'source': 'xhs',
            })
        outputs['xhs_discover'] = xhs_discover_out
        outputs['xhs_score'] = xhs_score_out

    if 'douyin' in args.sources:
        dy_backend = 'mock' if args.discover_backend == 'mock' else 'mediacrawler'
        dy_discover_cmd = [python, 'scripts/discover_douyin.py', '--keyword', args.keyword, '--run-id', run_id, '--limit', str(args.douyin_limit), '--backend', dy_backend]
        if dy_backend == 'mediacrawler':
            dy_discover_cmd.extend(['--login-type', args.douyin_login_type])
            if args.douyin_headless:
                dy_discover_cmd.append('--headless')
        douyin_raw_out = run_stage(dy_discover_cmd, cwd, run_id, 'douyin_discover', {
            'keyword': args.keyword,
            'limit': args.douyin_limit,
            'backend': dy_backend,
            'login_type': args.douyin_login_type if dy_backend == 'mediacrawler' else '',
            'headless': args.douyin_headless if dy_backend == 'mediacrawler' else False,
            'source': 'douyin',
        })
        if args.douyin_detail_limit > 0:
            douyin_enriched_out = run_stage([python, 'scripts/fetch_douyin_details.py', '--input', douyin_raw_out, '--limit', str(args.douyin_detail_limit), '--comment-limit', str(args.douyin_comment_limit)], cwd, run_id, 'douyin_fetch_details', {
                'input': douyin_raw_out,
                'limit': args.douyin_detail_limit,
                'comment_limit': args.douyin_comment_limit,
                'source': 'douyin',
            })
        else:
            douyin_enriched_out = run_stage([python, 'scripts/merge_platform_sources.py', '--douyin-input', douyin_raw_out, '--run-id', run_id], cwd, run_id, 'douyin_prepare_mergeable', {
                'douyin_input': douyin_raw_out,
                'run_id': run_id,
                'reason': 'detail_fetch_skipped_by_zero_limit',
            })
        outputs['douyin_discover'] = douyin_raw_out
        outputs['douyin_enriched'] = douyin_enriched_out

    if len(args.sources) == 1 and args.sources[0] == 'xhs':
        brief_input = xhs_score_out
    elif len(args.sources) == 1 and args.sources[0] == 'douyin':
        merge_cmd = [python, 'scripts/merge_platform_sources.py', '--douyin-input', douyin_enriched_out, '--run-id', run_id]
        brief_input = run_stage(merge_cmd, cwd, run_id, 'merge_sources', {
            'douyin_input': douyin_enriched_out,
            'run_id': run_id,
        })
        outputs['merged'] = brief_input
    else:
        merge_cmd = [python, 'scripts/merge_platform_sources.py', '--run-id', run_id]
        if xhs_score_out:
            merge_cmd.extend(['--xhs-input', xhs_score_out])
        if douyin_enriched_out:
            merge_cmd.extend(['--douyin-input', douyin_enriched_out])
        brief_input = run_stage(merge_cmd, cwd, run_id, 'merge_sources', {
            'xhs_input': xhs_score_out,
            'douyin_input': douyin_enriched_out,
            'run_id': run_id,
        })
        outputs['merged'] = brief_input

    brief_out = run_stage([python, 'scripts/build_topic_brief.py', '--input', brief_input], cwd, run_id, 'topic_brief', {
        'input': brief_input,
        'sources': args.sources,
    })
    outputs['topic_brief'] = brief_out
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', required=True)
    parser.add_argument('--publish-time', default='半年内')
    parser.add_argument('--account', default='')
    parser.add_argument('--discover-backend', default='mock', choices=['mock', 'cdp'])
    parser.add_argument('--render-backend', default='upstream', choices=['upstream', 'placeholder'])
    parser.add_argument('--publish-backend', default='mock', choices=['mock', 'cookie', 'cdp'])
    parser.add_argument('--mode', default='private', choices=['draft', 'private', 'public', 'scheduled'])
    parser.add_argument('--theme', default='professional')
    parser.add_argument('--render-mode', default='auto-split')
    parser.add_argument('--draft-index', type=int, default=None)
    parser.add_argument('--collect-metrics', action='store_true')
    parser.add_argument('--platform', default='xhs', choices=['xhs', 'wechat', 'brief'])
    parser.add_argument('--sources', nargs='+', default=['xhs'], choices=['xhs', 'douyin'])
    parser.add_argument('--xhs-reading-sources', nargs='*', default=[], choices=['search', 'home', 'profiles'])
    parser.add_argument('--douyin-limit', type=int, default=10)
    parser.add_argument('--douyin-detail-limit', type=int, default=3)
    parser.add_argument('--douyin-comment-limit', type=int, default=5)
    parser.add_argument('--douyin-login-type', default=os.environ.get('XHS_DOUYIN_LOGIN_TYPE', 'qrcode') or 'qrcode')
    parser.add_argument('--douyin-headless', action='store_true')
    parser.add_argument('--wechat-template', default='pain-method-conversion')
    parser.add_argument('--wechat-cover', default='')
    parser.add_argument('--wechat-theme', default='default')
    parser.add_argument('--wechat-account', default='')
    parser.add_argument('--wechat-publish', action='store_true')
    parser.add_argument('--xhs-rewrite-from', default='score', choices=['score', 'brief'])
    args = parser.parse_args()

    if args.publish_backend == 'cdp' and args.mode != 'draft':
        raise SystemExit('cdp backend currently supports draft mode only; use --mode draft or switch publish backend')

    if args.platform == 'wechat' and not args.wechat_cover:
        raise SystemExit('wechat branch requires --wechat-cover to build frontmatter and API publish payload')

    cwd = str(SKILL_ROOT)
    python = sys.executable or 'python'
    run_id = new_run_id('xhs' if args.platform == 'xhs' else 'topic')

    append_stage_manifest(run_id, 'pipeline', {
        'status': 'running',
        'started_at': iso_now(),
        'params': {
            'keyword': args.keyword,
            'publish_time': args.publish_time,
            'account': args.account,
            'discover_backend': args.discover_backend,
            'render_backend': args.render_backend,
            'publish_backend': args.publish_backend,
            'mode': args.mode,
            'theme': args.theme,
            'render_mode': args.render_mode,
            'draft_index': args.draft_index,
            'collect_metrics': args.collect_metrics,
            'platform': args.platform,
            'sources': args.sources,
            'xhs_reading_sources': args.xhs_reading_sources,
            'douyin_limit': args.douyin_limit,
            'douyin_detail_limit': args.douyin_detail_limit,
            'douyin_comment_limit': args.douyin_comment_limit,
            'douyin_login_type': args.douyin_login_type,
            'douyin_headless': args.douyin_headless,
            'wechat_template': args.wechat_template,
            'wechat_cover': args.wechat_cover,
            'wechat_theme': args.wechat_theme,
            'wechat_account': args.wechat_account,
            'wechat_publish': args.wechat_publish,
            'xhs_rewrite_from': args.xhs_rewrite_from,
        },
    })

    outputs = {}

    if args.platform == 'brief':
        outputs.update(run_unified_brief_pipeline(python, cwd, run_id, args))
    elif args.platform == 'wechat':
        outputs.update(run_unified_brief_pipeline(python, cwd, run_id, args))
        outputs.update(run_wechat_branch(python, cwd, run_id, outputs['topic_brief'], args))
    else:
        if args.xhs_reading_sources:
            outputs.update(run_unified_brief_pipeline(python, cwd, run_id, args))
            outputs.update(run_xhs_branch(python, cwd, run_id, outputs['xhs_score'], args, brief_input=outputs.get('topic_brief', '')))
        else:
            discover_cmd = [python, 'scripts/discover_trends.py', '--keyword', args.keyword, '--publish-time', args.publish_time, '--backend', args.discover_backend, '--run-id', run_id]
            if args.account:
                discover_cmd.extend(['--account', args.account])
            discover_out = run_stage(discover_cmd, cwd, run_id, 'discover-bootstrap', {
                'keyword': args.keyword,
                'publish_time': args.publish_time,
                'backend': args.discover_backend,
                'account': args.account,
                'platform': args.platform,
            })

            discover_data = read_json(discover_out)
            run_id = discover_data['run_id']
            score_out = run_stage([python, 'scripts/score_trends.py', '--input', discover_out], cwd, run_id, 'score', {
                'input': discover_out,
            })
            outputs = {
                'discover': discover_out,
                'score': score_out,
            }
            outputs.update(run_xhs_branch(python, cwd, run_id, score_out, args))

            if args.collect_metrics:
                metrics_out = run_stage([python, 'scripts/collect_metrics.py', '--run-id', run_id], cwd, run_id, 'metrics', {
                    'run_id': run_id,
                })
                outputs['metrics'] = metrics_out

    append_stage_manifest(run_id, 'pipeline', {
        'status': 'success',
        'finished_at': iso_now(),
        'outputs': outputs,
    })

    print('run_id=' + run_id)
    for key, value in outputs.items():
        print(f'{key}={value}')


if __name__ == '__main__':
    main()
