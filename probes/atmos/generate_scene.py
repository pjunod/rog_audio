#!/usr/bin/env python3
"""Create a deterministic moving sine object, never an encoded Dolby payload."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
scene = {
    'schema_version': 1, 'sample_rate': 48000, 'samples': 8192,
    'objects': [{'amplitude': 0.125, 'frequency_hz': 997, 'keyframes': [
        {'sample': 0, 'position': [-1, 0, 1]},
        {'sample': 8191, 'position': [1, 1, -1]},
    ]}],
}
payload = (json.dumps(scene, indent=2) + '\n').encode()
with args.output.open('xb') as output:
    output.write(payload)
print(hashlib.sha256(payload).hexdigest())
