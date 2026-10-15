"""Bounded control protocol for the colocated native playback helper."""
import json
import resource
import socket
import subprocess
import tempfile
import time

PROTOCOL = 'rog-atmos-pw-v1'
RING_FRAMES = 4096
MAX_PACKET = 2048
CONTROL_SECONDS = 2


class NativeError(Exception):
    pass


def capabilities(helper, env):
    """Describe without connecting to PipeWire; never select a fallback player."""
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
                    value.get('rate') != 48000 or value.get('channels') != [2, 12] or
                    value.get('format') != 'f32le' or value.get('final_buffer_policy') != 'fill-request'):
                raise ValueError('incompatible helper')
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            raise NativeError('native-helper-unavailable-or-incompatible') from exc
    return value


class NativeControl:
    """One BEGIN/ACK and one terminal packet, on a separate nonblocking socket."""
    def __init__(self, endpoint, report):
        self.endpoint = endpoint
        self.endpoint.setblocking(False)
        self.report = report
        self.boundary = None
        self.started = None
        self.ready = False
        self.final = None
        self.disconnected = False

    def begin(self, priming_frames, media_frames):
        if (self.boundary is not None or type(priming_frames) is not int or
                not 0 <= priming_frames <= 2160000 or type(media_frames) is not int or
                not 0 < media_frames <= 4320000):
            raise NativeError('native-control-invalid-boundary')
        value = f'BEGIN 1 {priming_frames} {media_frames}\n'.encode()
        try:
            if self.endpoint.send(value) != len(value):
                raise NativeError('native-control-send-failure')
        except OSError as exc:
            raise NativeError('native-control-send-failure') from exc
        self.boundary = (priming_frames, media_frames)
        self.started = time.monotonic()

    def poll(self):
        if self.started is not None and not self.ready and time.monotonic() - self.started >= CONTROL_SECONDS:
            raise NativeError('native-control-ack-timeout')
        # At most ACK + FINAL can be valid. A third packet is a protocol error.
        for _ in range(3):
            try:
                value, _ancillary, flags, _address = self.endpoint.recvmsg(MAX_PACKET)
            except BlockingIOError:
                break
            except OSError as exc:
                raise NativeError('native-control-read-failure') from exc
            if not value:
                self.disconnected = True
                if self.final is None:
                    raise NativeError('native-control-disconnected')
                break
            if flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
                raise NativeError('native-control-oversize')
            if value.startswith(b'ACK '):
                expected = (f'ACK 1 {self.boundary[0]} {self.boundary[1]}\n'.encode()
                            if self.boundary is not None else None)
                if self.ready or value != expected or self.final is not None:
                    raise NativeError('native-control-invalid-ack')
                self.ready = True
            elif value.startswith(b'FINAL '):
                if self.final is not None:
                    raise NativeError('native-control-duplicate-final')
                try:
                    final = json.loads(value[6:])
                    counters = ('input_frames', 'consumed_frames', 'media_frames',
                        'stdin_priming_frames', 'startup_silence_frames', 'prefill_silence_frames', 'tail_padding_frames',
                        'underflow_events', 'missing_media_frames', 'maximum_ring_frames',
                        'maximum_callback_frames')
                    if (not isinstance(final, dict) or final.get('protocol') != PROTOCOL or
                            not isinstance(final.get('status'), str) or not 0 < len(final['status']) <= 64 or
                            final.get('ring_capacity_frames') != RING_FRAMES or
                            any(type(final.get(key)) is not int or not 0 <= final[key] <= 100000000
                                for key in counters) or
                            any(type(final.get(key)) is not bool for key in ('input_eof', 'ring_consumed', 'drained')) or
                            final['maximum_ring_frames'] > RING_FRAMES or
                            final['maximum_callback_frames'] > RING_FRAMES or
                            (final['tail_padding_frames'] and
                             final['tail_padding_frames'] >= final['maximum_callback_frames'])):
                        raise ValueError('invalid native counters')
                except (ValueError, TypeError) as exc:
                    raise NativeError('native-control-invalid-final') from exc
                self.final = final
                self.report['native_playback'] = final
                if final['status'] != 'completed':
                    raise NativeError(final['status'])
            else:
                raise NativeError('native-control-invalid-packet')
        return self.ready

    def finish(self, priming_frames, media_frames):
        deadline = time.monotonic() + CONTROL_SECONDS
        while self.final is None:
            self.poll()
            if time.monotonic() >= deadline:
                raise NativeError('native-control-final-timeout')
            if self.final is None:
                time.sleep(.01)
        final = self.final
        if (not self.ready or self.boundary != (priming_frames, media_frames) or
                final['input_frames'] != priming_frames + media_frames or
                final['consumed_frames'] != priming_frames + media_frames or
                final['stdin_priming_frames'] != priming_frames or final['media_frames'] != media_frames or
                final['underflow_events'] or final['missing_media_frames'] or
                not final['maximum_callback_frames'] or
                not all(final[key] for key in ('input_eof', 'ring_consumed', 'drained'))):
            raise NativeError('native-playback-completion-mismatch')

    def close(self):
        # A failure/cancellation may still have produced useful bounded counters.
        try:
            self.poll()
        except NativeError:
            pass
        finally:
            self.endpoint.close()
