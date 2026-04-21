import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR_SCRIPTS = ROOT / 'vendor' / 'XiaohongshuSkills' / 'scripts'
if str(VENDOR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(VENDOR_SCRIPTS))

from cdp_publish import XiaohongshuPublisher


def main():
    publisher = XiaohongshuPublisher()
    publisher.connect()
    js = r"""
    (() => {
      const textOf = (el) => (el && (el.innerText || el.textContent || '') || '').trim();
      const visible = (el) => {
        if (!el) return false;
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      };
      const clickByText = (patterns) => {
        const nodes = Array.from(document.querySelectorAll('button, a, div, span'));
        for (const el of nodes) {
          const text = textOf(el);
          if (!text || !visible(el)) continue;
          if (patterns.some(re => re.test(text))) {
            el.click();
            return { ok: true, clicked: text };
          }
        }
        return { ok: false };
      };

      let step1 = clickByText([/返回/, /离开/, /退出/, /关闭/]);
      if (step1.ok) {
        return { ok: true, stage: 'first_click', detail: step1 };
      }

      let step2 = clickByText([/暂存离开/, /保存草稿并离开/, /保存草稿/, /存草稿/, /暂存/]);
      if (step2.ok) {
        return { ok: true, stage: 'save_click', detail: step2 };
      }

      // fallback: try browser history back to trigger leave modal
      try { history.back(); } catch (e) {}
      return { ok: false, reason: 'no_leave_or_save_button_found' };
    })()
    """
    first = publisher._evaluate(js)
    if first and first.get('ok') and first.get('stage') == 'first_click':
        second_js = r"""
        (() => {
          const textOf = (el) => (el && (el.innerText || el.textContent || '') || '').trim();
          const visible = (el) => {
            if (!el) return false;
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
          };
          const nodes = Array.from(document.querySelectorAll('button, a, div, span'));
          for (const el of nodes) {
            const text = textOf(el);
            if (!text || !visible(el)) continue;
            if (/暂存离开|保存草稿并离开|保存草稿|存草稿|暂存/.test(text)) {
              el.click();
              return { ok: true, clicked: text, stage: 'confirm_save_leave' };
            }
          }
          return { ok: false, reason: 'confirm_button_not_found' };
        })()
        """
        second = publisher._evaluate(second_js)
        if second and second.get('ok'):
            print(f"SAVE_AND_LEAVE_OK: {second}")
            return
        raise SystemExit(f"SAVE_AND_LEAVE_FAILED: first={first}, second={second}")

    if first and first.get('ok'):
        print(f"SAVE_AND_LEAVE_OK: {first}")
        return

    raise SystemExit(f"SAVE_AND_LEAVE_FAILED: {first}")


if __name__ == '__main__':
    main()
