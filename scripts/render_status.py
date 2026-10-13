#!/usr/bin/env python3
"""Render the ledger's headings, paragraphs, tables and inline Markdown."""
from html import escape
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
INLINE = re.compile(r'`([^`\n]+)`|\*\*([^*\n]+)\*\*|\[([^\]\n]+)\]\(([^()\s]+)\)')


def safe_link(target):
    """Keep authored relative links and ordinary web/mail links inert otherwise."""
    if any(ord(c) < 32 for c in target) or target.startswith('//') or '\\' in target:
        return False
    try:
        return urlsplit(target).scheme.lower() in ('', 'https', 'http', 'mailto')
    except ValueError:
        return False


def inline(text):
    out = []
    offset = 0
    for match in INLINE.finditer(text):
        out.append(escape(text[offset:match.start()]))
        code, strong, label, target = match.groups()
        if code is not None:
            out.append('<code>' + escape(code) + '</code>')
        elif strong is not None:
            out.append('<strong>' + inline(strong) + '</strong>')
        elif safe_link(target):
            out.append('<a href="' + escape(target, quote=True) + '">' + inline(label) + '</a>')
        else:
            out.append(escape(match.group()))
        offset = match.end()
    out.append(escape(text[offset:]))
    return ''.join(out)


def render(text):
    out = []
    paragraph = []
    table = False

    def flush_paragraph():
        if paragraph:
            out.append('<p>' + inline(' '.join(paragraph)) + '</p>')
            paragraph.clear()

    for line in text.splitlines():
        line = line.strip()
        if line.startswith('|'):
            flush_paragraph()
            if set(line.replace('|', '').replace(' ', '')) <= {'-', ':'}:
                continue
            tag = 'td' if table else 'th'
            if not table:
                out.append('<div class="table-scroll"><table>')
                table = True
            cells = line.strip('|').split('|')
            out.append('<tr>' + ''.join('<' + tag + '>' + inline(c.strip()) + '</' + tag + '>' for c in cells) + '</tr>')
            continue
        if table:
            out.append('</table></div>')
            table = False
        if not line:
            flush_paragraph()
            continue
        heading = re.match(r'^(#{1,6}) (.+)$', line)
        if heading:
            flush_paragraph()
            tag = 'h' + str(len(heading[1]))
            out.append('<' + tag + '>' + inline(heading[2]) + '</' + tag + '>')
        else:
            paragraph.append(line)
    flush_paragraph()
    if table:
        out.append('</table></div>')
    return '\n'.join(out)


if __name__ == '__main__':
    body = render((ROOT / 'docs/STATUS.md').read_text())
    (ROOT / 'docs/STATUS.html').write_text('''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ROG audio status</title><style>
body{font:16px/1.55 system-ui,sans-serif;margin:3rem auto;padding:0 1.5rem;max-width:1050px;background:#101823;color:#edf2f7}
h1{font-size:2rem}h2{color:#91d7ee;margin-top:2rem}a{color:#91d7ee}p{margin:1rem 0}code{font-size:.9em;background:#1e3047;padding:.1em .25em;border-radius:.2em;overflow-wrap:anywhere}
.table-scroll{overflow-x:auto;margin:2rem 0}table{border-collapse:collapse;width:100%;min-width:600px}td,th{border-bottom:1px solid #3b4b60;padding:.8rem;text-align:left;vertical-align:top}th{font-weight:700;background:#1e3047}
</style></head><body><main>''' + body + '<p><a href="https://github.com/pjunod/rog_audio/blob/main/docs/STATUS.md">GitHub progress ledger</a></p></main></body></html>\n')
