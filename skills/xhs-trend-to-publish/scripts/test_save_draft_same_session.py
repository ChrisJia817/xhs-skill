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


def ordered_assets(render_dir: Path) -> list[str]:
    cover = sorted(render_dir.glob('cover.png'))
    cards = sorted(render_dir.glob('card_*.png'))
    return [str(p) for p in cover + cards]


def upload_images_resilient(publisher: XiaohongshuPublisher, assets: list[str]):
    attempts = []
    for timeout in (60.0, 120.0, 180.0):
        try:
            original_wait = publisher._wait_for_uploaded_images

            def patched_wait(expected_count: int, timeout_seconds: float = 60.0):
                return original_wait(expected_count, timeout_seconds=max(timeout_seconds, timeout))

            publisher._wait_for_uploaded_images = patched_wait
            publisher._upload_images(assets)
            return {'ok': True, 'timeout_used': timeout, 'assets': assets}
        except Exception as exc:
            attempts.append({'timeout': timeout, 'error': repr(exc)})
            try:
                publisher._navigate(XHS_CREATOR_URL)
                time.sleep(2)
                publisher._click_image_text_tab()
                time.sleep(2)
            except Exception as nav_exc:
                attempts.append({'timeout': timeout, 'stage': 'reset', 'error': repr(nav_exc)})
        finally:
            try:
                publisher._wait_for_uploaded_images = original_wait
            except Exception:
                pass

    return {'ok': False, 'attempts': attempts, 'assets': assets}


def save_to_draft_box(publisher: XiaohongshuPublisher):
    script = r"""
(() => {
  const visible = (node) => {
    if (!node) return false;
    const r = node.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const textOf = (node) => ((node && (node.innerText || node.textContent || '')) || '').trim();
  const all = Array.from(document.querySelectorAll('button, div, span, a')).filter(visible);

  const saveBtn = all.find(node => /暂存离开|保存草稿并离开|保存草稿|存草稿|暂存/.test(textOf(node)));
  if (saveBtn) {
    const text = textOf(saveBtn);
    saveBtn.click();
    return { ok: true, stage: 'save_clicked', clicked: text };
  }

  const leaveBtn = all.find(node => /返回|离开|退出|关闭/.test(textOf(node)));
  if (leaveBtn) {
    const text = textOf(leaveBtn);
    leaveBtn.click();
    return { ok: true, stage: 'leave_clicked', clicked: text };
  }

  return {
    ok: false,
    reason: 'no_draft_button_found',
    candidates: all.map(node => textOf(node)).filter(Boolean).slice(0, 120)
  };
})()
"""
    first = publisher._evaluate(script)
    if not first or not first.get('ok'):
        return first

    if first.get('stage') == 'leave_clicked':
        time.sleep(1.5)
        confirm_script = r"""
(() => {
  const visible = (node) => {
    if (!node) return false;
    const r = node.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const textOf = (node) => ((node && (node.innerText || node.textContent || '')) || '').trim();
  const all = Array.from(document.querySelectorAll('button, div, span, a')).filter(visible);
  const saveBtn = all.find(node => /暂存离开|保存草稿并离开|保存草稿|存草稿|暂存/.test(textOf(node)));
  if (saveBtn) {
    const text = textOf(saveBtn);
    saveBtn.click();
    return { ok: true, stage: 'confirm_save_clicked', clicked: text };
  }
  return {
    ok: false,
    reason: 'confirm_save_not_found',
    candidates: all.map(node => textOf(node)).filter(Boolean).slice(0, 120)
  };
})()
"""
        return {
            'first': first,
            'second': publisher._evaluate(confirm_script)
        }

    return {'first': first}


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
    assets = ordered_assets(render_dir)

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
    upload_result = upload_images_resilient(publisher, assets)
    if not upload_result.get('ok'):
        print(json.dumps({
            'run_id': args.run_id,
            'keyword': keyword,
            'generated_tags': tags,
            'upload_result': upload_result,
        }, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    time.sleep(2)
    publisher._fill_title(draft['title'][:20])
    time.sleep(1)
    publisher._fill_content(body_without_tags)
    time.sleep(1)
    topic_result = select_topics(publisher, tags)
    time.sleep(1)
    draft_result = save_to_draft_box(publisher)

    print(json.dumps({
        'run_id': args.run_id,
        'keyword': keyword,
        'assets': assets,
        'generated_tags': tags,
        'upload_result': upload_result,
        'topic_result': topic_result,
        'draft_result': draft_result,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
