"""Harness-only native sink-monitor observer; never selects a default source."""
import json
import os
import resource
import socket
import subprocess
import tempfile
import time

PROTOCOL = 'rog-atmos-capture-v1'
MAX_PACKET = 2048
MAX_BYTES = 256 * 1024 * 1024
RING_FRAMES = 4096
CONTROL_SECONDS = 2


class CaptureError(AssertionError):
    pass


def capture_capabilities(helper, env):
    with tempfile.TemporaryFile() as output:
        def limits():
            resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_PACKET, MAX_PACKET))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        try:
            result = subprocess.run([str(helper), '--describe'], env=env, stdout=output,
                stderr=subprocess.DEVNULL, timeout=CONTROL_SECONDS, preexec_fn=limits)
            output.seek(0)
            raw = output.read(MAX_PACKET + 1)
            value = json.loads(raw)
            if (result.returncode or len(raw) > MAX_PACKET or not isinstance(value, dict) or
                    value.get('protocol') != PROTOCOL or value.get('ring_frames') != RING_FRAMES or
                    value.get('maximum_file_bytes') != MAX_BYTES or value.get('rate') != 48000 or
                    value.get('channels') != [2, 12]):
                raise ValueError('incompatible observer')
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            raise CaptureError('capture-helper-unavailable-or-incompatible') from exc
    return value


class CaptureObserver:
    def __init__(self, helper, path, channels, env):
        if type(channels) is not int or channels not in (2, 12):
            raise CaptureError('capture-channel-count-invalid')
        self.capabilities = capture_capabilities(helper, env)
        self.path = path
        self.channels = channels
        self.child = None
        self.endpoint, inherited = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.endpoint.setblocking(False)
        self.pending = self.acknowledged = 0
        self.arm_requested = self.stop_requested = False
        self.final = None
        self.cleanup_error = None
        output = None
        try:
            output = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            def limits():
                resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_BYTES, MAX_BYTES))
                resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            self.child = subprocess.Popen([str(helper), '--channels', str(channels),
                '--output-fd', str(output), '--control-fd', str(inherited.fileno())],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env=env, pass_fds=(output, inherited.fileno()), preexec_fn=limits)
        except BaseException:
            self.endpoint.close()
            raise
        finally:
            inherited.close()
            if output is not None:
                os.close(output)

    def _request(self, sequence):
        if (self.pending or sequence not in (1, 2) or
                (sequence == 1 and self.arm_requested) or
                (sequence == 2 and (self.acknowledged != 1 or self.stop_requested))):
            raise CaptureError('capture-control-order-invalid')
        command = b'ARM 1\n' if sequence == 1 else b'STOP 2\n'
        try:
            if self.endpoint.send(command) != len(command):
                raise CaptureError('capture-control-send-failure')
        except OSError as exc:
            raise CaptureError('capture-control-send-failure') from exc
        self.pending = sequence
        if sequence == 1:
            self.arm_requested = True
        else:
            self.stop_requested = True

    def poll(self, *, allow_source_end=False):
        for _ in range(4):
            try:
                raw, _ancillary, flags, _address = self.endpoint.recvmsg(MAX_PACKET)
            except BlockingIOError:
                break
            except OSError as exc:
                raise CaptureError('capture-control-read-failure') from exc
            if not raw:
                if self.final is None:
                    raise CaptureError('capture-control-disconnected')
                break
            if flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
                raise CaptureError('capture-control-oversize')
            if raw.startswith(b'ACK '):
                if not self.pending or raw != f'ACK {self.pending}\n'.encode() or self.final is not None:
                    raise CaptureError('capture-control-invalid-ack')
                self.acknowledged = self.pending
                self.pending = 0
            elif raw.startswith(b'FINAL '):
                if self.final is not None:
                    raise CaptureError('capture-control-duplicate-final')
                try:
                    value = json.loads(raw[6:])
                    counters = ('callback_received_frames', 'ring_accepted_frames', 'writer_taken_frames',
                        'written_bytes', 'written_complete_frames', 'maximum_ring_frames', 'rejected_frames',
                        'ignored_before_arm_frames', 'overflow_events', 'writer_io_errors', 'clock_observations', 'unavailable_clock_observations',
                        'clock_gap_events', 'header_observations', 'unavailable_pts_observations',
                        'sequence_regressions', 'pts_regressions', 'header_discontinuities')
                    unsigned64 = ('first_ticks', 'last_ticks', 'first_sequence', 'last_sequence')
                    if (not isinstance(value, dict) or value.get('protocol') != PROTOCOL or
                            type(value.get('complete')) is not bool or
                            type(value.get('metadata_request_accepted')) is not bool or
                            not isinstance(value.get('status'), str) or not 0 < len(value['status']) <= 64 or
                            value.get('ring_capacity_frames') != RING_FRAMES or
                            any(type(value.get(key)) is not int or not 0 <= value[key] <= 0xffffffff for key in counters) or
                            any(value.get(key) is not None and (type(value[key]) is not int or not 0 <= value[key] <= 0xffffffffffffffff) for key in unsigned64) or
                            type(value.get('largest_sequence_step')) is not int or not 0 <= value['largest_sequence_step'] <= 0xffffffffffffffff or
                            any(value.get(key) is not None and (type(value[key]) is not int or not -(1 << 63) <= value[key] < (1 << 63))
                                for key in ('first_pts', 'last_pts')) or
                            value['maximum_ring_frames'] > RING_FRAMES or value['written_bytes'] > MAX_BYTES):
                        raise ValueError('invalid capture accounting')
                except (ValueError, TypeError) as exc:
                    raise CaptureError('capture-control-invalid-final') from exc
                self.final = value
            else:
                raise CaptureError('capture-control-invalid-packet')
        if self.final is not None:
            if self.final['status'] != 'completed' and not (
                    allow_source_end and self.final['status'] == 'capture-pipewire-failure' and
                    not self.final['overflow_events'] and not self.final['writer_io_errors']):
                raise CaptureError(self.final['status'])
        elif self.child.poll() is not None:
            raise CaptureError('capture-ended-without-receipt')

    def arm(self):
        self._request(1)
        deadline = time.monotonic() + CONTROL_SECONDS
        while self.acknowledged != 1:
            self.poll()
            if self.final is not None or time.monotonic() >= deadline:
                raise CaptureError('capture-arm-ack-timeout')
            time.sleep(.01)

    def finish(self, *, require_complete=True):
        self.poll(allow_source_end=not require_complete)
        if self.final is None:
            self._request(2)
        deadline = time.monotonic() + CONTROL_SECONDS
        while self.final is None:
            self.poll(allow_source_end=not require_complete)
            if time.monotonic() >= deadline:
                raise CaptureError('capture-stop-timeout')
            if self.final is None:
                time.sleep(.01)
        try:
            self.child.wait(timeout=CONTROL_SECONDS)
        except subprocess.TimeoutExpired as exc:
            raise CaptureError('capture-exit-timeout') from exc
        value = self.final
        if require_complete:
            frames = value['ring_accepted_frames']
            if (self.acknowledged != 2 or not value['complete'] or self.child.returncode != 0 or
                    value['status'] != 'completed' or value['callback_received_frames'] != frames or
                    value['writer_taken_frames'] != frames or value['written_complete_frames'] != frames or
                    value['written_bytes'] != frames * self.channels * 4 or
                    self.path.stat().st_size != value['written_bytes'] or
                    any(value[key] for key in ('rejected_frames', 'overflow_events', 'writer_io_errors', 'clock_gap_events', 'sequence_regressions',
                                              'pts_regressions', 'header_discontinuities'))):
                raise CaptureError('capture-completion-accounting-mismatch')
        return value

    def receipt(self):
        return {'capabilities': self.capabilities, 'native': self.final,
                'arm_acknowledged': self.acknowledged >= 1, 'stop_acknowledged': self.acknowledged == 2,
                'cleanup_error': self.cleanup_error,
                'exit_code': self.child.poll() if self.child else None,
                'continuity_scope': 'Usable fixed-rate callback clock and optional header signals; not all server/device xruns.'}

    def close(self):
        try:
            if self.child is not None:
                if self.arm_requested:
                    try:
                        self.finish(require_complete=False)
                    except CaptureError as exc:
                        self.cleanup_error = str(exc)
                if self.child.poll() is None:
                    self.child.terminate()
                    try:
                        self.child.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        self.child.kill()
                        self.child.wait(timeout=CONTROL_SECONDS)
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.cleanup_error = type(exc).__name__
        finally:
            self.endpoint.close()
