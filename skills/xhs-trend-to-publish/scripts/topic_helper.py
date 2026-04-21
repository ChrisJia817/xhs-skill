import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR_SCRIPTS = ROOT / 'vendor' / 'XiaohongshuSkills' / 'scripts'
if str(VENDOR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(VENDOR_SCRIPTS))

from cdp_publish import XiaohongshuPublisher

MAX_TIMING_JITTER_RATIO = 0.7


def _normalize_timing_jitter(value: float) -> float:
    return max(0.0, min(MAX_TIMING_JITTER_RATIO, value))


def _jitter_ms(base_ms: int, jitter_ratio: float, minimum_ms: int = 0) -> int:
    base = max(minimum_ms, int(base_ms))
    if jitter_ratio <= 0:
        return base
    delta = int(round(base * jitter_ratio))
    low = max(minimum_ms, base - delta)
    high = max(low, base + delta)
    return random.randint(low, high)


def extract_topic_tags_from_last_line(content: str) -> tuple[str, list[str]]:
    lines = content.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return content, []
    last_line = lines[-1].strip()
    parts = [p for p in last_line.split() if p]
    if not parts:
        return content, []
    if not all(re.fullmatch(r"#[^\s#]+", part) for part in parts):
        return content, []
    body = "\n".join(lines[:-1]).strip()
    return body, parts


def select_topics(publisher: XiaohongshuPublisher, tags: list[str], timing_jitter: float = 0.25):
    if not tags:
        return {'ok': True, 'selected': [], 'failed': []}

    print(f"[topic_helper] Selecting {len(tags)} topic tag(s) with upstream logic...")
    failed_tags = []
    selected_tags = []
    timing_jitter = _normalize_timing_jitter(timing_jitter)

    for tag in tags:
        normalized_tag = tag.lstrip('#').strip()
        if not normalized_tag:
            continue

        hash_pause_ms = _jitter_ms(180, timing_jitter, minimum_ms=90)
        suggest_wait_ms = _jitter_ms(3000, timing_jitter, minimum_ms=1600)
        after_enter_ms = _jitter_ms(260, timing_jitter, minimum_ms=120)

        escaped_tag = json.dumps(normalized_tag)
        newline_literal = json.dumps("\n")
        hash_literal = json.dumps("#")

        result = publisher._evaluate(f"""
            (async function() {{
                var editor = document.querySelector(
                    'div.tiptap.ProseMirror, div.ProseMirror[contenteditable="true"]'
                );
                if (!editor) {{
                    return {{ ok: false, reason: 'editor_not_found' }};
                }}

                function sleep(ms) {{
                    return new Promise(function(resolve) {{ setTimeout(resolve, ms); }});
                }}

                function moveCaretToEditorEnd(el) {{
                    el.focus();
                    var selection = window.getSelection();
                    if (!selection) return;
                    var range = document.createRange();
                    range.selectNodeContents(el);
                    range.collapse(false);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }}

                function insertTextAtCaret(text) {{
                    var inserted = false;
                    try {{
                        inserted = document.execCommand('insertText', false, text);
                    }} catch (e) {{}}

                    if (!inserted) {{
                        var selection = window.getSelection();
                        if (selection && selection.rangeCount > 0) {{
                            var range = selection.getRangeAt(0);
                            var node = document.createTextNode(text);
                            range.insertNode(node);
                            range.setStartAfter(node);
                            range.collapse(true);
                            selection.removeAllRanges();
                            selection.addRange(range);
                        }} else {{
                            editor.appendChild(document.createTextNode(text));
                        }}
                    }}
                    editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}

                function pressEnter(el) {{
                    var evt = {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        cancelable: true,
                    }};
                    ['keydown', 'keypress', 'keyup'].forEach(function(type) {{
                        el.dispatchEvent(new KeyboardEvent(type, evt));
                    }});
                }}

                moveCaretToEditorEnd(editor);
                insertTextAtCaret({newline_literal});
                insertTextAtCaret({hash_literal});
                await sleep({hash_pause_ms});
                insertTextAtCaret({escaped_tag});
                await sleep({suggest_wait_ms});
                pressEnter(editor);
                await sleep({after_enter_ms});
                return {{ ok: true, tag: {escaped_tag} }};
            }})()
        """)

        if result and result.get('ok'):
            selected_tags.append(normalized_tag)
        else:
            failed_tags.append({'tag': normalized_tag, 'result': result})

    return {
        'ok': len(failed_tags) == 0,
        'selected': selected_tags,
        'failed': failed_tags,
    }
