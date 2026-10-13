#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""Ask the exact service process to quit, then await its exit before systemd signals it.

Linux pidfds and authenticated Unix peer credentials prevent a stale PID/socket
from addressing a replacement or foreign process. No signals are sent here;
systemd retains its normal timeout and final kill policy.
"""
import argparse
import os
from pathlib import Path
import select
import socket
import struct
import sys
import time

BINARY = '/opt/rog-audio/easyeffects/bin/easyeffects'
CONTRACT = 'owned-synchronous-exit-v1'

class StopError(Exception):
    pass


def identity(pid, binary):
    root = Path('/proc')/str(pid)
    if root.stat().st_uid != os.geteuid():
        raise StopError('foreign process owner')
    executable = os.readlink(root/'exe')
    if executable.removesuffix(' (deleted)') != os.path.realpath(binary):
        raise StopError('foreign process executable')
    # The command name may contain spaces and closing parentheses.
    fields = (root/'stat').read_text().rsplit(')', 1)[1].split()
    return fields[19]  # Linux /proc stat field 22: start time.


def stop_process(pid, socket_path, timeout=10.0, binary=BINARY):
    if type(pid) is not int or pid < 0 or not 0 < timeout <= 10:
        raise StopError('invalid stop request')
    if pid == 0:
        return 'already-exited'
    if not hasattr(os, 'pidfd_open') or not hasattr(socket, 'SO_PEERCRED'):
        raise StopError('Linux process identity unavailable')
    deadline = time.monotonic()+timeout
    try:
        pidfd = os.pidfd_open(pid)
    except ProcessLookupError:
        return 'already-exited'
    try:
        poller = select.poll(); poller.register(pidfd, select.POLLIN)
        if poller.poll(0):
            return 'already-exited'
        before = identity(pid, binary)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(max(0.001, deadline-time.monotonic()))
            client.connect(str(socket_path))
            peer_pid, peer_uid, _ = struct.unpack('3i', client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if peer_pid != pid or peer_uid != os.geteuid():
                raise StopError('foreign or replacement socket peer')
            if poller.poll(0):
                return 'already-exited'
            if identity(pid, binary) != before:
                raise StopError('process identity changed')
            # Match the accepted native LocalServer protocol. Never launch a
            # secondary binary, which could become a new primary after exit.
            client.sendall(b'quit_app\n')
        while True:
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise StopError('owned process exit timed out')
            if poller.poll(max(1, int(remaining*1000))):
                return 'exited'
    except (FileNotFoundError, ProcessLookupError):
        if poller.poll(0):
            return 'already-exited'
        raise
    finally:
        os.close(pidfd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, default=os.environ.get('MAINPID') or '0',
                        help='systemd MAINPID; absent means no running primary')
    parser.add_argument('--socket', required=True)
    args = parser.parse_args(argv)
    try:
        result = stop_process(args.pid, args.socket)
        print('speaker-stop: '+result)
        return 0
    except (StopError, OSError, ValueError, IndexError) as error:
        print('speaker-stop: refused or incomplete: '+str(error), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
