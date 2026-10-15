#!/usr/bin/env python3
"""Summarise private signed click/chirp annotations; no capture or audio access."""
import argparse
import hashlib
import json
import math
import os
import re
import stat
import statistics
import sys

MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_RECORDING_BYTES = 2 * 1024 * 1024 * 1024
MAX_TRIALS = 10000
MAX_FRAMES = 2 ** 40
ALIAS = re.compile(r'[a-z][a-z0-9_-]{0,63}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
REASONS = {'missing-click', 'missing-chirp', 'ambiguous-onset', 'clipping',
           'xrun', 'overlapping-sound', 'incomplete-capture', 'operator-rejected'}


class AnnotationError(Exception):
    """Fixed reason codes only; never interpolate private input or paths."""


def require(condition, reason):
    if not condition:
        raise AnnotationError(reason)


def fields(value, names):
    require(isinstance(value, dict) and set(value) == set(names), 'invalid_fields')


def alias(value):
    require(isinstance(value, str) and ALIAS.fullmatch(value) is not None,
            'invalid_alias')
    return value


def integer(value, low, high):
    require(type(value) is int and low <= value <= high, 'invalid_integer')
    return value


def unique_records(values, key, names):
    require(isinstance(values, list) and 1 <= len(values) <= 128,
            'invalid_inventory_count')
    result = {}
    for value in values:
        fields(value, names)
        identity = alias(value[key])
        require(identity not in result, 'duplicate_inventory_id')
        result[identity] = value
    return result


def regular_bytes(path, limit, digest_only=False):
    """Open nonblocking, refuse special files/symlinks, detect concurrent writes."""
    try:
        path_stat = os.lstat(path)
        require(stat.S_ISREG(path_stat.st_mode), 'input_not_regular_file')
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode), 'input_not_regular_file')
            require((before.st_dev, before.st_ino) == (path_stat.st_dev, path_stat.st_ino),
                    'input_changed_before_open')
            require(0 <= before.st_size <= limit, 'input_too_large')
            chunks, length, digest = [], 0, hashlib.sha256()
            while True:
                chunk = os.read(fd, min(65536, limit + 1 - length))
                if not chunk:
                    break
                length += len(chunk)
                require(length <= limit, 'input_too_large')
                digest.update(chunk)
                if not digest_only:
                    chunks.append(chunk)
            after = os.fstat(fd)
            require(length == before.st_size == after.st_size and
                    before.st_mtime_ns == after.st_mtime_ns and
                    before.st_ctime_ns == after.st_ctime_ns,
                    'input_changed_during_read')
            return (digest.hexdigest(), length) if digest_only else b''.join(chunks)
        finally:
            os.close(fd)
    except (OSError, ValueError, OverflowError):
        raise AnnotationError('input_read_failed') from None


def parse_input(data):
    require(len(data) <= MAX_INPUT_BYTES, 'input_too_large')
    depth, quoted, escaped = 0, False, False
    for byte in data:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            require(depth <= 32, 'json_nesting_limit')
        elif byte in (93, 125):
            depth -= 1

    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, 'duplicate_json_key')
            result[key] = value
        return result

    def constant(_value):
        raise AnnotationError('nonfinite_json')

    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, ValueError, RecursionError):
        raise AnnotationError('invalid_json') from None


def onset(value, frames):
    if value is None:
        return None
    fields(value, {'sample', 'lower', 'upper'})
    for number in value.values():
        integer(number, 0, frames - 1)
    require(value['lower'] <= value['sample'] <= value['upper'], 'invalid_onset_range')
    return value


def statistics_of(values):
    values = sorted(values)
    return {'min': values[0], 'median': statistics.median(values),
            'p95': values[(95 * len(values) + 99) // 100 - 1], 'max': values[-1]}


def summary(rows):
    included = [row for row in rows if row['included']]
    reasons = {}
    for row in rows:
        for reason in row['rejection_reasons']:
            reasons[reason] = reasons.get(reason, 0) + 1
    result = {'attempted_count': len(rows), 'included_count': len(included),
              'rejected_count': len(rows) - len(included),
              'rejection_reason_counts': dict(sorted(reasons.items())),
              'raw_signed_ms': None, 'annotation_statistic_bounds_ms': None,
              'annotation_and_declared_timebase_statistic_bounds_ms': None,
              'sampling_confidence_interval': 'not-estimated'}
    if not included:
        return result
    result['raw_signed_ms'] = statistics_of([row['raw_signed_ms'] for row in included])
    for row_key, result_key in (
            ('annotation_bounds_ms', 'annotation_statistic_bounds_ms'),
            ('annotation_and_declared_timebase_bounds_ms',
             'annotation_and_declared_timebase_statistic_bounds_ms')):
        if any(row[row_key] is None for row in included):
            continue
        lower = statistics_of([row[row_key][0] for row in included])
        upper = statistics_of([row[row_key][1] for row in included])
        result[result_key] = {name: [lower[name], upper[name]] for name in lower}
    return result


def analyse(document, input_sha256=None):
    fields(document, {'schema_version', 'evidence_class', 'recordings', 'conditions', 'trials'})
    require(type(document['schema_version']) is int and document['schema_version'] == 1,
            'unsupported_schema')
    evidence = document['evidence_class']
    require(isinstance(evidence, str) and evidence in {'synthetic', 'physical-measurement'},
            'invalid_evidence_class')
    recordings = unique_records(document['recordings'], 'recording_id',
        {'recording_id', 'sha256', 'sample_rate_hz', 'frame_count',
         'timebase_scale_bound_ppm', 'preprocessing', 'unquantified_biases'})
    for recording in recordings.values():
        require(isinstance(recording['sha256'], str) and
                DIGEST.fullmatch(recording['sha256']) is not None, 'invalid_digest')
        integer(recording['sample_rate_hz'], 1, 768000)
        integer(recording['frame_count'], 1, MAX_FRAMES)
        bound = recording['timebase_scale_bound_ppm']
        require(bound is None or (type(bound) in (int, float) and
                0 <= bound <= 100000 and math.isfinite(bound)), 'invalid_timebase_bound')
        alias(recording['preprocessing'])
        biases = recording['unquantified_biases']
        require(isinstance(biases, list) and len(biases) <= 16, 'invalid_biases')
        for bias in biases:
            alias(bias)
        require(len(set(biases)) == len(biases), 'duplicate_bias')
    condition_names = {'condition_id', 'setup_id', 'route', 'settings_id', 'method_id',
                       'keyboard_id', 'geometry_id', 'signal_id', 'power_state',
                       'load_state', 'phase'}
    conditions = unique_records(document['conditions'], 'condition_id', condition_names)
    for condition in conditions.values():
        for name, value in condition.items():
            alias(value)
        require(condition['phase'] in {'pilot', 'formal'}, 'invalid_phase')
    trials = document['trials']
    require(isinstance(trials, list) and len(trials) <= MAX_TRIALS, 'invalid_trial_count')
    groups, trial_ids, clicks, chirps = {}, set(), set(), set()
    for index, trial in enumerate(trials):
        fields(trial, {'trial_id', 'recording_id', 'condition_id', 'block_id',
                       'click', 'chirp', 'valid', 'rejection_reasons'})
        for name in ('trial_id', 'recording_id', 'condition_id', 'block_id'):
            alias(trial[name])
        require(trial['trial_id'] not in trial_ids, 'duplicate_trial_id')
        trial_ids.add(trial['trial_id'])
        require(trial['recording_id'] in recordings, 'unknown_recording')
        require(trial['condition_id'] in conditions, 'unknown_condition')
        recording = recordings[trial['recording_id']]
        click, chirp = (onset(trial[name], recording['frame_count'])
                        for name in ('click', 'chirp'))
        reasons = trial['rejection_reasons']
        require(isinstance(reasons, list) and len(reasons) <= len(REASONS), 'invalid_reasons')
        require(all(isinstance(reason, str) and reason in REASONS for reason in reasons),
                'invalid_reasons')
        require(len(set(reasons)) == len(reasons), 'duplicate_reason')
        require(type(trial['valid']) is bool, 'invalid_validity')
        require((trial['valid'] and not reasons and click is not None and chirp is not None)
                or (not trial['valid'] and bool(reasons)), 'inconsistent_validity')
        key = (trial['condition_id'], trial['recording_id'])
        if trial['valid']:
            click_key, chirp_key = key + (click['sample'],), key + (chirp['sample'],)
            require(click_key not in clicks and chirp_key not in chirps,
                    'duplicate_included_onset')
            clicks.add(click_key); chirps.add(chirp_key)
        row = dict(trial, input_index=index, included=trial['valid'],
                   raw_signed_samples=None, raw_signed_ms=None,
                   annotation_bounds_samples=None, annotation_bounds_ms=None,
                   annotation_and_declared_timebase_bounds_ms=None)
        if click is not None and chirp is not None:
            samples = chirp['sample'] - click['sample']
            bounds = [chirp['lower'] - click['upper'], chirp['upper'] - click['lower']]
            scale = 1000 / recording['sample_rate_hz']
            row.update(raw_signed_samples=samples, raw_signed_ms=samples * scale,
                       annotation_bounds_samples=bounds,
                       annotation_bounds_ms=[value * scale for value in bounds])
            ppm = recording['timebase_scale_bound_ppm']
            if ppm is not None:
                fraction = ppm / 1000000
                products = [value * factor for value in row['annotation_bounds_ms']
                            for factor in (1 - fraction, 1 + fraction)]
                row['annotation_and_declared_timebase_bounds_ms'] = [min(products), max(products)]
        if key not in groups:
            groups[key] = {'dimensions': conditions[key[0]],
                           'recording_id': key[1], 'trials': []}
        groups[key]['trials'].append(row)
    output_groups = []
    for key in sorted(groups):
        group = groups[key]
        blocks = {}
        for row in group['trials']:
            blocks.setdefault(row['block_id'], []).append(row)
        group['blocks'] = [{'block_id': block, 'statistics': summary(rows)}
                           for block, rows in blocks.items()]
        group['statistics'] = summary(group['trials'])
        count = group['statistics']['included_count']
        group['onset_count_status'] = ('synthetic-only' if evidence == 'synthetic' else
            'pilot' if group['dimensions']['phase'] == 'pilot' else
            'count-met' if count >= 100 else 'insufficient-trials')
        output_groups.append(group)
    used_recordings = {key[1] for key in groups}
    used_conditions = {key[0] for key in groups}
    return {'schema_version': 1, 'tool': 'analyse_manual_annotations', 'tool_version': 1,
            'input_sha256': input_sha256, 'declared_evidence_class': evidence,
            'qualification': 'not-established', 'physical_validity': 'not-verified',
            'recordings': [dict(recording, byte_verification='not-requested',
                                verified_file_sha256=None, verified_file_bytes=None,
                                rate_frame_count_and_onsets='operator-declared')
                           for recording in recordings.values()],
            'unused_recording_ids': sorted(set(recordings) - used_recordings),
            'unused_condition_ids': sorted(set(conditions) - used_conditions),
            'attempted_count': len(trials), 'groups': output_groups,
            'p95_estimator': 'nearest-rank: sorted[ceil(0.95*n)-1]',
            'sign': 'chirp-minus-click; negative intervals are retained',
            'limitations': ['Recording hashes, rates, frame counts, onsets and conditions are declarations.',
                'Optional file hashing verifies bytes only, not rate, frame count or physical evidence.',
                'Bounds cover declared annotation ranges and optional time-per-sample scale only.',
                'Unquantified biases remain unquantified; no propagation or graph delay is subtracted.',
                'Different recordings and conditions are never pooled; blocks remain visible.',
                'Sampling confidence, acoustic accuracy and Mac parity are not established.']}


def verify_recordings(result, bindings):
    recordings = {row['recording_id']: row for row in result['recordings']}
    seen = set()
    for binding in bindings:
        identity, separator, path = binding.partition('=')
        require(separator and identity in recordings and path, 'invalid_recording_binding')
        require(identity not in seen, 'duplicate_recording_binding')
        seen.add(identity)
        digest, length = regular_bytes(path, MAX_RECORDING_BYTES, digest_only=True)
        row = recordings[identity]
        require(digest == row['sha256'], 'recording_digest_mismatch')
        row.update(byte_verification='digest-matched-explicit-file',
                   verified_file_sha256=digest, verified_file_bytes=length)


def write_result(result, path):
    encoded = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW |
                 os.O_NONBLOCK, 0o600)
    with os.fdopen(fd, 'wb') as output:
        os.fchmod(output.fileno(), 0o600)
        require(stat.S_ISREG(os.fstat(output.fileno()).st_mode), 'output_not_regular_file')
        output.write(encoded)
        output.flush()
        os.fsync(output.fileno())


class PrivateParser(argparse.ArgumentParser):
    def error(self, _message):
        self.print_usage(sys.stderr)
        self.exit(2, 'Annotation analysis error: invalid_arguments\n')


def main(argv=None):
    parser = PrivateParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--verify-recording', action='append', default=[], metavar='ID=PATH')
    args = parser.parse_args(argv)
    try:
        data = regular_bytes(args.input, MAX_INPUT_BYTES)
        result = analyse(parse_input(data), hashlib.sha256(data).hexdigest())
        require(len(args.verify_recording) <= 128, 'invalid_recording_binding_count')
        verify_recordings(result, args.verify_recording)
    except AnnotationError as error:
        print('Annotation analysis error: ' + str(error), file=sys.stderr)
        return 2
    try:
        write_result(result, args.output)
    except (OSError, ValueError, AnnotationError):
        print('Annotation analysis error: output_write_failed', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
