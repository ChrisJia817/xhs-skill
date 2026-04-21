import argparse
from bootstrap import ROOT
from common import read_json, write_json, ensure_dir, append_stage_manifest, iso_now


def normalize_xhs_candidate(item: dict) -> dict:
    detail = item.get('detail') or {}
    return {
        'source_platform': 'xhs',
        'item_id': item.get('note_id', ''),
        'title': item.get('title', ''),
        'summary': item.get('summary', ''),
        'body': detail.get('desc', ''),
        'author': item.get('author', ''),
        'publish_time': item.get('publish_time', ''),
        'like_count': item.get('like_count', 0),
        'comment_count': item.get('comment_count', 0),
        'collect_count': item.get('collect_count', 0),
        'share_count': detail.get('raw', {}).get('detail', {}).get('note', {}).get('interactInfo', {}).get('shareCount', 0),
        'comments': detail.get('comments', []),
        'raw': item,
    }


def normalize_douyin_candidate(item: dict) -> dict:
    detail = item.get('detail') or {}
    return {
        'source_platform': 'douyin',
        'item_id': item.get('aweme_id', ''),
        'title': item.get('title', ''),
        'summary': item.get('summary', ''),
        'body': detail.get('desc', ''),
        'author': item.get('author', ''),
        'publish_time': item.get('publish_time', ''),
        'like_count': item.get('like_count', 0),
        'comment_count': item.get('comment_count', 0),
        'collect_count': item.get('collect_count', 0),
        'share_count': item.get('share_count', 0),
        'comments': detail.get('comments', []),
        'raw': item,
    }


def first_non_empty(*values):
    for value in values:
        if value not in (None, '', []):
            return value
    return ''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--xhs-input', default='')
    parser.add_argument('--douyin-input', default='')
    parser.add_argument('--run-id', default='')
    args = parser.parse_args()

    merged_candidates = []
    run_id = args.run_id
    keyword = ''
    publish_time = ''

    if args.xhs_input:
        xhs_data = read_json(args.xhs_input)
        run_id = run_id or xhs_data.get('run_id', '')
        keyword = first_non_empty(keyword, xhs_data.get('keyword'))
        publish_time = first_non_empty(publish_time, xhs_data.get('publish_time'))
        for item in xhs_data.get('candidates', []):
            merged_candidates.append(normalize_xhs_candidate(item))

    if args.douyin_input:
        dy_data = read_json(args.douyin_input)
        run_id = run_id or dy_data.get('run_id', '')
        keyword = first_non_empty(keyword, dy_data.get('keyword'))
        publish_time = first_non_empty(publish_time, dy_data.get('publish_time'))
        for item in dy_data.get('candidates', []):
            merged_candidates.append(normalize_douyin_candidate(item))

    if not run_id:
        raise SystemExit('run_id could not be resolved from inputs; provide --run-id explicitly.')

    out = {
        'run_id': run_id,
        'stage': 'merged_sources',
        'status': 'success',
        'generated_at': iso_now(),
        'keyword': keyword,
        'publish_time': publish_time,
        'candidate_count': len(merged_candidates),
        'candidates': merged_candidates,
    }

    out_dir = ensure_dir(ROOT / 'data' / 'merged')
    out_path = out_dir / f'{run_id}.json'
    write_json(out_path, out)
    append_stage_manifest(run_id, 'merge-platform-sources-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'output': str(out_path),
        'keyword': keyword,
        'publish_time': publish_time,
        'candidate_count': len(merged_candidates),
    })
    print(out_path)


if __name__ == '__main__':
    main()
