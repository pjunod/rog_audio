#!/usr/bin/env python3
"""Summarise explicit Atmos-probe float WAVs; channel energy is not fidelity."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import stat
import struct

RATE = 48000
MAX_SECONDS = 90
CHANNELS = {
    2: ['FL', 'FR'],
    12: ['FL', 'FR', 'FC', 'LFE', 'BL', 'BR', 'SL', 'SR',
         'TFL', 'TFR', 'TBL', 'TBR'],
}
FLOAT_GUID = bytes.fromhex('0300000000001000800000aa00389b71')


def identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def analyse(path, window_ms=250):
    if not isinstance(window_ms, int) or isinstance(window_ms, bool) or not 20 <= window_ms <= 1000:
        raise ValueError('window must be an integer from20 through1000ms')
    with Path(path).open('rb') as source:
        import os
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or not 68 <= before.st_size <= MAX_SECONDS * RATE * 12 * 4 + 68:
            raise ValueError('input size or type outside probe WAV contract')
        header = source.read(68)
        if (len(header) != 68 or header[:4] != b'RIFF' or header[8:16] != b'WAVEfmt '
                or header[60:64] != b'data' or header[44:60] != FLOAT_GUID
                or struct.unpack_from('<I', header, 4)[0] + 8 != before.st_size
                or struct.unpack_from('<I', header, 16)[0] != 40):
            raise ValueError('requires the probe contiguous extensible float32 WAV')
        tag, channels, rate, byte_rate, alignment, bits, extension, valid_bits, mask = struct.unpack_from('<HHIIHHHHI', header, 20)
        if (tag != 0xfffe or channels not in CHANNELS or rate != RATE
                or byte_rate != RATE * channels * 4 or alignment != channels * 4
                or bits != 32 or extension != 22 or valid_bits != 32
                or mask != (3 if channels == 2 else 0x2d63f)):
            raise ValueError('unsupported probe WAV layout or encoding')
        data_bytes = struct.unpack_from('<I', header, 64)[0]
        if data_bytes != before.st_size - 68 or data_bytes % alignment:
            raise ValueError('invalid PCM length')
        samples = data_bytes // alignment
        if not 1 <= samples <= MAX_SECONDS * RATE:
            raise ValueError('encoded duration outside90-second bound')
        digest = hashlib.sha256(header)
        total_energy, total_peaks = [0.0] * channels, [0.0] * channels
        windows = []
        window_samples = RATE * window_ms // 1000
        for start in range(0, samples, window_samples):
            count = min(window_samples, samples - start)
            raw = source.read(count * alignment)
            if len(raw) != count * alignment:
                raise ValueError('truncated PCM')
            digest.update(raw)
            energy, peaks = [0.0] * channels, [0.0] * channels
            for index, (value,) in enumerate(struct.iter_unpack('<f', raw)):
                if not math.isfinite(value) or abs(value) > 1:
                    raise ValueError('nonfinite or clipping PCM')
                channel = index % channels
                energy[channel] += value * value
                peaks[channel] = max(peaks[channel], abs(value))
            for channel in range(channels):
                total_energy[channel] += energy[channel]
                total_peaks[channel] = max(total_peaks[channel], peaks[channel])
            dominant = max(range(channels), key=energy.__getitem__)
            windows.append({'start_sample': start, 'samples_per_channel': count,
                            'rms': [math.sqrt(value / count) for value in energy],
                            'peak': peaks,
                            'dominant_channel': CHANNELS[channels][dominant] if energy[dominant] else None})
        if source.read(1) or identity(os.fstat(source.fileno())) != identity(before):
            raise ValueError('input changed during analysis')
    return {'schema_version': 1, 'evidence_class': 'private-offline',
            'analysis': 'observed-channel-energy', 'input_sha256': digest.hexdigest(),
            'input_bytes': before.st_size, 'sample_rate': RATE,
            'channels': CHANNELS[channels], 'samples_per_channel': samples,
            'duration_seconds': samples / RATE, 'window_ms': window_ms,
            'rms': [math.sqrt(value / samples) for value in total_energy],
            'peak': total_peaks, 'windows': windows,
            'reference_fidelity_compared': False, 'physical_measurement': False,
            'limitations': ['Activity and dominant-channel windows are observations, not an independently aligned reference comparison.',
                            'No decoder-delay, gain, localization, acoustic or Dolby certification result.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--window-ms', type=int, default=250)
    args = parser.parse_args()
    try:
        report = analyse(args.input, args.window_ms)
        with args.report.open('x') as output:
            json.dump(report, output, indent=2, allow_nan=False)
            output.write('\n')
    except (OSError, ValueError):
        parser.exit(2, 'analysis failed: input unavailable/unsupported or report collision\n')
    print('observed-channel-energy; reference fidelity and physical delay unmeasured')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
