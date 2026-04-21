import re


def normalize_tag(tag: str) -> str:
    tag = (tag or '').strip()
    if not tag:
        return ''
    if not tag.startswith('#'):
        tag = '#' + tag
    return tag


def extract_inline_tags(text: str) -> list[str]:
    tags = re.findall(r'#[^\s#]+', text or '')
    return [normalize_tag(t) for t in tags if normalize_tag(t)]


def generate_related_tags(keyword: str, title: str, body: str) -> list[str]:
    base = []
    keyword = (keyword or '').strip()
    title = title or ''
    body = body or ''

    if keyword:
        base.append(f'#{keyword}')

    corpus = f'{keyword}\n{title}\n{body}'

    if '无货源' in corpus:
        base += ['#电商副业', '#副业干货', '#电商避坑', '#开店经验', '#副业观察']
        if '闲鱼' in corpus:
            base.append('#闲鱼无货源')
        if '拼多多' in corpus or 'pdd' in corpus.lower():
            base.append('#拼多多无货源')

    if any(x in corpus for x in ['副业', '搞钱', '赚钱']):
        base += ['#副业项目', '#副业思路']

    if any(x in corpus for x in ['新手', '入门', '小白']):
        base += ['#新手入门', '#电商入门']

    if any(x in corpus for x in ['避坑', '风险', '骗局']):
        base += ['#避坑指南']

    if any(x in corpus for x in ['趋势', '变化', '还能做吗']):
        base += ['#趋势判断']

    if any(x in corpus for x in ['教程', '步骤', '怎么做']):
        base += ['#实操干货']

    seen = set()
    out = []
    for tag in base:
        tag = normalize_tag(tag)
        key = tag.lower()
        if tag and key not in seen:
            seen.add(key)
            out.append(tag)
    return out[:8]


def build_topic_tags(keyword: str, title: str, body: str) -> list[str]:
    explicit = extract_inline_tags(body)
    related = generate_related_tags(keyword, title, body)
    merged = []
    seen = set()
    for tag in explicit + related:
        tag = normalize_tag(tag)
        key = tag.lower()
        if tag and key not in seen:
            seen.add(key)
            merged.append(tag)
    return merged[:8]
