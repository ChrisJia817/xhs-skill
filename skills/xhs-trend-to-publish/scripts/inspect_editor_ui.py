import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR_SCRIPTS = ROOT / 'vendor' / 'XiaohongshuSkills' / 'scripts'
if str(VENDOR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(VENDOR_SCRIPTS))

from cdp_publish import XiaohongshuPublisher, XHS_CREATOR_URL


def main():
    publisher = XiaohongshuPublisher()
    publisher.connect()
    publisher.navigate(XHS_CREATOR_URL)
    js = r"""
    (() => {
      const nodes = Array.from(document.querySelectorAll('button, div, span, a'));
      const items = nodes
        .map((el, idx) => {
          const text = (el.innerText || el.textContent || '').trim();
          if (!text) return null;
          const rect = el.getBoundingClientRect();
          return {
            idx,
            tag: el.tagName,
            text,
            className: (el.className || '').toString(),
            id: el.id || '',
            role: el.getAttribute('role') || '',
            visible: !!(rect.width > 0 && rect.height > 0),
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            w: Math.round(rect.width),
            h: Math.round(rect.height),
          };
        })
        .filter(Boolean)
        .filter(x => x.visible)
        .filter(x => /暂存|保存|草稿|离开|返回|退出|取消|继续编辑|确认|发布/.test(x.text));
      return {
        url: location.href,
        title: document.title,
        matches: items.slice(0, 300)
      };
    })()
    """
    result = publisher._evaluate(js)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
