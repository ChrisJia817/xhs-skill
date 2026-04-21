import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR_SCRIPTS = ROOT / 'vendor' / 'XiaohongshuSkills' / 'scripts'
if str(VENDOR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(VENDOR_SCRIPTS))

from cdp_publish import XiaohongshuPublisher, XHS_CREATOR_URL
from topic_helper import extract_topic_tags_from_last_line, select_topics
from topic_strategy import build_topic_tags


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--account', default='')
    args = parser.parse_args()

    draft_path = ROOT / 'data' / 'drafts' / f'{args.run_id}.json'
    render_dir = ROOT / 'data' / 'renders' / args.run_id
    draft_data = json.loads(draft_path.read_text(encoding='utf-8'))
    keyword = draft_data.get('keyword', '')
    draft = draft_data['drafts'][0]
    assets = [str(p) for p in sorted(render_dir.glob('*.png'))]

    body_without_tags, _ = extract_topic_tags_from_last_line(draft['body'])
    tags = build_topic_tags(keyword, draft['title'], draft['body'])

    publisher_kwargs = {}
    if args.account:
        publisher_kwargs['account_name'] = args.account
    publisher = XiaohongshuPublisher(**publisher_kwargs)
    publisher.connect()
    publisher._navigate(XHS_CREATOR_URL)
    time.sleep(2)
    publisher._click_image_text_tab()
    time.sleep(2)
    publisher._upload_images(assets)
    time.sleep(2)
    publisher._fill_title(draft['title'][:20])
    time.sleep(1)
    publisher._fill_content(body_without_tags)
    time.sleep(1)
    topic_result = select_topics(publisher, tags)
    print(json.dumps({
        'run_id': args.run_id,
        'keyword': keyword,
        'generated_tags': tags,
        'topic_result': topic_result,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
