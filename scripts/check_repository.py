#!/usr/bin/env python3
"""Check tracked project docs and evidence without machine side effects."""
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

def main():
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    errors = []
    for name in filter(None, files):
        path = ROOT / name
        if name.startswith(('private/', 'work/', 'artifacts/')):
            errors.append(f'private/build path tracked: {name}')
        if path.suffix == '.json':
            try:
                json.loads(path.read_text())
            except (ValueError, UnicodeError, OSError) as exc:
                errors.append(f'{name}: invalid JSON: {type(exc).__name__}')
        if path.suffix == '.md':
            content = path.read_text()
            for target in re.findall(r'\]\(([^\s)]+)\)', content):
                if '://' in target or target.startswith(('#', 'mailto:')):
                    continue
                target = unquote(target.split('#')[0])
                if target and not (path.parent / target).exists():
                    errors.append(f'{name}: missing link {target}')
    for error in errors:
        print(error)
    if errors:
        return 1
    print('Repository documentation, tracked-path and JSON checks passed.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
