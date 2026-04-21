import argparse
import json
from pathlib import Path
from bootstrap import ROOT
from common import read_json, append_stage_manifest, iso_now


def build_markdown(article: dict, cover_path: str) -> str:
    title = article.get('title', '未命名文章')
    author = article.get('author', '')
    summary = article.get('summary', '')
    body = article.get('body_markdown', '')

    body = body.replace('ai', 'AI').replace('Ai', 'AI')
    structured_lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            structured_lines.append('')
            continue
        if stripped.startswith('第一步：') or stripped.startswith('第二步：') or stripped.startswith('第三步：') or stripped.startswith('这里最容易做错的地方') or stripped.startswith('所以回到最开始那个问题') or stripped.startswith('如果要把这件事讲透') or stripped.startswith('最后想说一句'):
            structured_lines.append(f'## **{stripped}**')
        else:
            structured_lines.append(line)

    lines = [
        '---',
        f'title: "{title}"',
        f'author: "{author}"',
        f'description: "{summary}"',
        f'coverImage: "{cover_path}"',
        '---',
        '',
        f'# {title}',
        '',
        '\n'.join(structured_lines),
        '',
    ]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--cover', required=True)
    args = parser.parse_args()

    article = read_json(args.input)
    markdown = build_markdown(article, args.cover)
    out_dir = ROOT / 'data' / 'wechat-drafts'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{article['run_id']}.{article['template']}.md"
    out_path.write_text(markdown, encoding='utf-8')

    append_stage_manifest(article['run_id'], 'wechat-format-output', {
        'status': 'success',
        'finished_at': iso_now(),
        'input': args.input,
        'output': str(out_path),
        'cover': args.cover,
    })
    print(out_path)


if __name__ == '__main__':
    main()
