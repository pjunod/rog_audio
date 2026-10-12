#!/usr/bin/env python3
"""Check tracked project docs and evidence without machine side effects."""
import hashlib
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
    manifests = [ROOT / name for name in files
                 if name.startswith('profiles/') and name.endswith('/manifest.json')]
    for manifest_path in manifests:
        try:
            manifest = json.loads(manifest_path.read_text())
            if not isinstance(manifest['files'], list) or not manifest['files']:
                raise ValueError('empty file inventory')
            seen = set()
            for record in manifest['files']:
                name = record.get('path', record.get('name'))
                if not isinstance(name, str) or name != Path(name).name or name in seen:
                    raise ValueError('invalid or duplicate file name')
                seen.add(name)
                path = manifest_path.parent / name
                if (path.is_symlink() or not path.is_file()
                        or str(path.relative_to(ROOT)) not in files):
                    errors.append(f'invalid profile manifest path: {path.relative_to(ROOT)}')
                    continue
                data = path.read_bytes()
                if len(data) != record['size_bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
                    errors.append(f'profile artifact hash/size mismatch: {path.relative_to(ROOT)}')
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            errors.append(f'invalid provenance manifest: {manifest_path.relative_to(ROOT)}')
    for error in errors:
        print(error)
    if errors:
        return 1
    print('Repository documentation, tracked-path and JSON checks passed.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
