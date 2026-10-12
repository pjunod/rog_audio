#!/usr/bin/env python3
"""Render the small Markdown progress ledger into a standalone workboard."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def render(text):
    out = []
    table = False
    for line in text.splitlines():
        if line.startswith('|'):
            if set(line.replace('|', '').replace(' ', '')) <= {'-', ':'}:
                continue
            if not table:
                out.append('<table>')
                table = True
            out.append('<tr>' + ''.join('<td>' + escape(c.strip()) + '</td>' for c in line.strip('|').split('|')) + '</tr>')
            continue
        if table:
            out.append('</table>')
            table = False
        if not line:
            continue
        if line.startswith('# '):
            out.append('<h1>' + escape(line[2:]) + '</h1>')
        elif line.startswith('## '):
            out.append('<h2>' + escape(line[3:]) + '</h2>')
        else:
            out.append('<p>' + escape(line) + '</p>')
    if table:
        out.append('</table>')
    return '\n'.join(out)

if __name__ == '__main__':
    body = render((ROOT / 'docs/STATUS.md').read_text())
    (ROOT / 'docs/STATUS.html').write_text('''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>ROG audio status</title><style>
body{font:16px/1.55 system-ui,sans-serif;margin:3rem auto;padding:0 1.5rem;max-width:1050px;background:#101823;color:#edf2f7}
h1{font-size:2rem}h2{color:#91d7ee}a{color:#91d7ee}table{border-collapse:collapse;width:100%;margin:2rem 0}td{border-bottom:1px solid #3b4b60;padding:.8rem;vertical-align:top}tr:first-child{font-weight:700;background:#1e3047}p{margin:.5rem 0}
</style><main>''' + body + '<p><a href="https://github.com/pjunod/rog_audio/blob/main/docs/STATUS.md">GitHub progress ledger</a></p></main></html>\n')
