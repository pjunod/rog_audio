"""Bounded private JSON I/O shared by offline audio tools."""
import hashlib
import json
import os
from pathlib import Path
import stat
import argparse
import sys

LIMIT = 8 * 1024 * 1024


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def read_bytes(path):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError('input must be a regular file')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError('input exceeds size limit')
        return data
    finally:
        os.close(fd)


def load_json(path):
    data = read_bytes(path)
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON'))), digest(data)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_private(path, value):
    data = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'
    if len(data.encode('utf-8')) > LIMIT:
        raise ValueError('encoded output exceeds size limit')
    write_text(path, data)


def write_text(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        stream.write(data)


def schema(value, name):
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value['schema_version'] != 1 or value.get('kind') != name:
        raise ValueError('unsupported audio schema')


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, _message):
        self.print_usage(sys.stderr)
        self.exit(2, "audio tool failed: invalid arguments\n")
