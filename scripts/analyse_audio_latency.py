#!/usr/bin/env python3
"""Offline latency trial analysis; never captures sound or changes audio state.

Strict v1 JSON is documented in AUDIO_LATENCY_BUILD.md. Output remains private:
neutral aliases are supplied by the operator, not inferred from device names.
"""

import argparse
import hashlib
import json
import math
import os
import re
import stat
import statistics
import sys

MAX_BYTES = 8 * 1024 * 1024
MAX_TRIALS = 10000
KINDS = {"round-trip", "event-to-output", "idle-onset", "av-offset"}
REASONS = {"clipping", "ambiguous-detection", "xrun", "missing-trigger",
           "clock-invalid", "operator-rejected", "capture-incomplete"}
FLAGS = {"clipping", "ambiguous-detection", "xrun", "missing-trigger"}
ALIAS = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")


class TrialError(Exception):
    """Only fixed reason codes; input values and paths never enter errors."""


def require(condition, reason):
    if not condition:
        raise TrialError(reason)


def fields(value, required):
    require(isinstance(value, dict) and set(value) == set(required), "invalid_fields")


def alias(value):
    require(isinstance(value, str) and ALIAS.fullmatch(value) is not None,
            "invalid_alias")
    return value


def number(value, low, high, reason="invalid_number"):
    require(type(value) in (int, float) and low <= value <= high and
            (type(value) is int or math.isfinite(value)), reason)
    return value


def integer(value, low, high, reason):
    require(type(value) is int and low <= value <= high, reason)
    return value


def enum(value, choices, reason):
    require(isinstance(value, str) and value in choices, reason)
    return value


def milliseconds(value, unit, rate, signed=False, sample_count=False):
    enum(unit, {"ms", "s", "samples"}, "invalid_unit")
    number(value, -1e12 if signed else 0, 1e12, "invalid_delay")
    if unit == "samples":
        require(rate is not None, "samples_require_rate")
        if sample_count:
            require(type(value) is int, "invalid_sample_count")
        result = value * 1000 / rate
    else:
        result = value * (1000 if unit == "s" else 1)
    return number(result, -1e9 if signed else 0, 1e9, "delay_out_of_range")


def clock_model(value):
    require(isinstance(value, dict), "invalid_clock")
    relationship = enum(value.get("relationship"),
                        {"same-clock", "synchronised", "unsynchronised"},
                        "invalid_clock")
    if relationship == "synchronised":
        fields(value, {"relationship", "model_id", "offset_ms", "uncertainty_ms"})
        alias(value["model_id"])
        number(value["offset_ms"], -1e9, 1e9, "invalid_clock_offset")
        number(value["uncertainty_ms"], 0, 1e9, "invalid_clock_uncertainty")
    else:
        fields(value, {"relationship"})
    return relationship


def correction_models(values):
    require(isinstance(values, list) and len(values) <= 16, "invalid_corrections")
    seen = set()
    for value in values:
        fields(value, {"model_id", "kind", "delay_ms", "uncertainty_ms"})
        model_id = alias(value["model_id"])
        require(model_id not in seen, "duplicate_correction")
        seen.add(model_id)
        enum(value["kind"], {"converter", "propagation", "trigger"},
             "invalid_correction_kind")
        number(value["delay_ms"], 0, 1e9, "invalid_correction_delay")
        number(value["uncertainty_ms"], 0, 1e9, "invalid_correction_uncertainty")
    return sorted(values, key=lambda value: value["model_id"])


def validate_trial(value, setup_ids):
    fields(value, {"trial_id", "setup_id", "configuration_id", "kind", "delay",
                   "unit", "sample_rate_hz", "method", "route", "clock",
                   "uncertainty", "power_state", "load_state", "dsp_state",
                   "valid", "rejection_reason", "flags", "corrections", "graph"})
    for name in ("trial_id", "setup_id", "configuration_id", "method", "route",
                 "power_state", "load_state", "dsp_state"):
        alias(value[name])
    require(value["setup_id"] in setup_ids, "unknown_setup")
    enum(value["kind"], KINDS, "invalid_measurement_kind")
    rate = value["sample_rate_hz"]
    if rate is not None:
        integer(rate, 1, 768000, "invalid_sample_rate")
    raw = milliseconds(value["delay"], value["unit"], rate,
                       signed=value["kind"] == "av-offset", sample_count=True)
    uncertainty = value["uncertainty"]
    fields(uncertainty, {"bound", "unit"})
    bound = milliseconds(uncertainty["bound"], uncertainty["unit"], rate)
    relationship = clock_model(value["clock"])
    corrections = correction_models(value["corrections"])
    require(type(value["valid"]) is bool, "invalid_validity")
    if value["valid"]:
        require(value["rejection_reason"] is None, "inconsistent_validity")
    else:
        enum(value["rejection_reason"], REASONS, "missing_rejection_reason")
    flags = value["flags"]
    require(isinstance(flags, list) and len(flags) <= len(FLAGS), "invalid_flags")
    for flag in flags:
        enum(flag, FLAGS, "invalid_flag")
    require(len(flags) == len(set(flags)), "duplicate_flag")
    graph = value["graph"]
    period = None
    if graph is not None:
        fields(graph, {"quantum_frames", "rate_hz"})
        quantum = integer(graph["quantum_frames"], 1, 1048576, "invalid_quantum")
        graph_rate = integer(graph["rate_hz"], 1, 768000, "invalid_graph_rate")
        period = quantum * 1000 / graph_rate
    reasons = set(flags)
    if not value["valid"]:
        reasons.add(value["rejection_reason"])
    if relationship == "unsynchronised":
        reasons.add("clock-invalid")
    offset = value["clock"].get("offset_ms", 0)
    corrected = raw - offset - sum(model["delay_ms"] for model in corrections)
    bound += value["clock"].get("uncertainty_ms", 0)
    bound += sum(model["uncertainty_ms"] for model in corrections)
    number(corrected, -1e10, 1e10, "corrected_delay_out_of_range")
    number(bound, 0, 1e10, "combined_uncertainty_out_of_range")
    # A negative non-AV result signals a broken model, even if uncertainty spans zero.
    if value["kind"] != "av-offset" and corrected < 0:
        reasons.add("negative-corrected-delay")
    group = {name: value[name] for name in ("setup_id", "configuration_id", "kind",
             "method", "route", "sample_rate_hz", "power_state", "load_state", "dsp_state")}
    group.update({"clock_model": value["clock"], "corrections": corrections, "graph": graph})
    row = {"trial_id": value["trial_id"], "raw_delay": value["delay"],
           "raw_unit": value["unit"], "raw_delay_ms": raw,
           "corrected_delay_ms": corrected if relationship != "unsynchronised" else None,
           "measurement_uncertainty_bound_ms": milliseconds(uncertainty["bound"],
                                                            uncertainty["unit"], rate),
           "combined_uncertainty_bound_ms": bound if relationship != "unsynchronised" else None,
           "clock": value["clock"], "corrections": corrections,
           "input_valid": value["valid"],
           "input_rejection_reason": value["rejection_reason"], "input_flags": sorted(flags),
           "included": not reasons, "exclusion_reasons": sorted(reasons)}
    return group, period, row


def summary(rows):
    """Nearest-rank p95, with conservative bounds on each order statistic."""
    included = [row for row in rows if row["included"]]
    counts = {}
    for row in rows:
        for reason in row["exclusion_reasons"]:
            counts[reason] = counts.get(reason, 0) + 1
    result = {"total_count": len(rows), "included_count": len(included),
              "excluded_count": len(rows) - len(included),
              "exclusion_reason_counts": dict(sorted(counts.items()))}
    if not included:
        result.update({"raw_ms": None, "corrected_ms": None,
                       "uncertainty": None})
        return result

    def stats(values):
        values = sorted(values)
        return {"min": values[0], "median": statistics.median(values),
                "p95": values[(95 * len(values) + 99) // 100 - 1], "max": values[-1]}

    raw = [row["raw_delay_ms"] for row in included]
    corrected = [row["corrected_delay_ms"] for row in included]
    bounds = [row["combined_uncertainty_bound_ms"] for row in included]
    lower = stats([value - bound for value, bound in zip(corrected, bounds)])
    upper = stats([value + bound for value, bound in zip(corrected, bounds)])
    result.update({"raw_ms": stats(raw), "corrected_ms": stats(corrected),
                   "uncertainty": {"method": "additive-conservative-bound",
                       "max_trial_bound_ms": max(bounds),
                       "corrected_statistic_bounds_ms": {
                           name: [lower[name], upper[name]] for name in lower},
                       "sampling_confidence_interval": "not-estimated"}})
    return result


def analyse(document, input_sha256=None):
    fields(document, {"schema_version", "evidence_class", "setups", "trials"})
    require(type(document["schema_version"]) is int and document["schema_version"] == 1,
            "unsupported_schema")
    evidence = enum(document["evidence_class"], {"synthetic", "physical-measurement"},
                    "invalid_evidence_class")
    setups = document["setups"]
    require(isinstance(setups, list) and 1 <= len(setups) <= 128, "invalid_setups")
    setup_ids = set()
    for setup in setups:
        fields(setup, {"setup_id", "system", "os", "interface"})
        for value in setup.values():
            alias(value)
        require(setup["setup_id"] not in setup_ids, "duplicate_setup")
        setup_ids.add(setup["setup_id"])
    trials = document["trials"]
    require(isinstance(trials, list) and len(trials) <= MAX_TRIALS, "invalid_trial_count")
    groups, trial_ids = {}, set()
    for value in trials:
        group, period, row = validate_trial(value, setup_ids)
        require(row["trial_id"] not in trial_ids, "duplicate_trial_id")
        trial_ids.add(row["trial_id"])
        key = json.dumps(group, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if key not in groups:
            groups[key] = {"dimensions": group, "graph_period_ms": period, "trials": []}
        groups[key]["trials"].append(row)
    output_groups = []
    for key in sorted(groups):
        group = groups[key]
        group["trials"].sort(key=lambda row: row["trial_id"])
        group["statistics"] = summary(group["trials"])
        group["onset_trial_count_gate"] = {
            "required_count": 100,
            "status": "synthetic-only" if evidence == "synthetic" else
                      "not-applicable" if group["dimensions"]["kind"] not in
                      {"idle-onset", "event-to-output"} else
                      "count-met" if group["statistics"]["included_count"] >= 100
                      else "insufficient-trials"}
        output_groups.append(group)
    return {"schema_version": 1, "tool": "analyse_audio_latency", "tool_version": 1,
            "evidence_class": evidence, "input_sha256": input_sha256,
            "setups": sorted(setups, key=lambda setup: setup["setup_id"]),
            "total_count": len(trials), "groups": output_groups,
            "p95_estimator": "nearest-rank: sorted[ceil(0.95*n)-1]",
            "av_offset_sign": "audio-minus-video; positive means audio late",
            "qualification": "not-established",
            "limitations": ["Input evidence and uncertainty bounds are operator declarations.",
                            "Graph period is not physical latency.",
                            "No one-way delay is inferred from round-trip delay.",
                            "No load-run, audible-gap or same-path Mac gate is evaluated.",
                            "Reports are private until aliases and results are reviewed."]}


def read_input(path):
    """Reject special files before reading, cap bytes, and detect concurrent edits."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0))
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode), "input_not_regular_file")
            require(before.st_size <= MAX_BYTES, "input_too_large")
            chunks, length = [], 0
            while True:
                chunk = os.read(fd, min(65536, MAX_BYTES + 1 - length))
                if not chunk:
                    break
                chunks.append(chunk)
                length += len(chunk)
                require(length <= MAX_BYTES, "input_too_large")
            after = os.fstat(fd)
            require(length == before.st_size == after.st_size and
                    before.st_mtime_ns == after.st_mtime_ns and
                    before.st_ctime_ns == after.st_ctime_ns, "input_changed_during_read")
            return b"".join(chunks)
        finally:
            os.close(fd)
    except (OSError, ValueError):
        raise TrialError("input_read_failed") from None


def parse_input(data):
    require(len(data) <= MAX_BYTES, "input_too_large")
    # Bound nesting independently of the interpreter's recursion limit. Ignore
    # braces in strings; malformed escapes/structure remain json.loads' job.
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
            require(depth <= 32, "json_nesting_limit")
        elif byte in (93, 125):
            depth -= 1

    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, "duplicate_json_key")
            result[key] = value
        return result

    def constant(_value):
        raise TrialError("nonfinite_json")

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, ValueError, RecursionError):
        raise TrialError("invalid_json") from None


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, _message):
        # argparse normally echoes unrecognised argument text and private paths.
        self.print_usage(sys.stderr)
        self.exit(2, "Latency analysis error: invalid_arguments\n")


def write_result(result, path):
    encoded = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                 getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(encoded)


def main(argv=None):
    parser = PrivateArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="private v1 trial JSON")
    parser.add_argument("--output", required=True, help="new private result JSON (0600)")
    args = parser.parse_args(argv)
    try:
        data = read_input(args.input)
        result = analyse(parse_input(data), hashlib.sha256(data).hexdigest())
    except TrialError as error:
        print("Latency analysis error: " + str(error), file=sys.stderr)
        return 2
    try:
        write_result(result, args.output)
    except (OSError, ValueError):
        print("Latency analysis error: output_write_failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
