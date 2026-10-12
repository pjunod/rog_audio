"""Synthetic latency schema, clock, statistics and private-file regressions."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/analyse_audio_latency.py"
SPEC = importlib.util.spec_from_file_location("analyse_audio_latency", SCRIPT)
latency = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(latency)


def trial(index=1, delay=10, **changes):
    value = {"trial_id": "trial-" + str(index), "setup_id": "rig-a",
             "configuration_id": "baseline", "kind": "idle-onset", "delay": delay,
             "unit": "ms", "sample_rate_hz": 48000, "method": "cross-correlation",
             "route": "internal-speakers", "clock": {"relationship": "same-clock"},
             "uncertainty": {"bound": 0.25, "unit": "ms"}, "power_state": "ac",
             "load_state": "idle", "dsp_state": "stock", "valid": True,
             "rejection_reason": None, "flags": [], "corrections": [],
             "graph": {"quantum_frames": 1024, "rate_hz": 48000}}
    value.update(changes)
    return value


def document(trials=None, evidence="synthetic"):
    return {"schema_version": 1, "evidence_class": evidence,
            "setups": [{"setup_id": "rig-a", "system": "lab5-gu605mz",
                        "os": "linux-test", "interface": "built-in"}],
            "trials": [trial()] if trials is None else trials}


def group(trials):
    result = latency.analyse(document(trials))
    if len(result["groups"]) != 1:
        raise AssertionError("Expected one synthetic group")
    return result["groups"][0]


class AnalysisTests(unittest.TestCase):
    def bad(self, value, reason=None):
        with self.assertRaises(latency.TrialError) as caught:
            latency.analyse(value)
        if reason:
            self.assertEqual(str(caught.exception), reason)
        self.assertNotIn("PRIVATE", str(caught.exception))

    def test_hand_computable_nearest_rank_and_even_median(self):
        rows = [trial(index, index) for index in range(1, 21)]
        stats = group(rows)["statistics"]
        self.assertEqual(stats["corrected_ms"], {"min": 1, "median": 10.5,
                                                "p95": 19, "max": 20})
        self.assertEqual(stats["raw_ms"], stats["corrected_ms"])
        self.assertEqual(stats["included_count"], 20)
        self.assertEqual(stats["uncertainty"]["corrected_statistic_bounds_ms"]["p95"],
                         [18.75, 19.25])
        for count, expected in ((1, 1), (2, 2), (3, 3), (19, 19), (21, 20)):
            self.assertEqual(group([trial(i, i) for i in range(1, count + 1)])
                             ["statistics"]["raw_ms"]["p95"], expected)

    def test_mixed_units_share_statistics_without_graph_subtraction(self):
        values = [trial(1, 10), trial(2, 0.020, unit="s"),
                  trial(3, 1440, unit="samples", uncertainty={"bound": 12, "unit": "samples"})]
        result = group(values)
        self.assertEqual(result["statistics"]["raw_ms"]["median"], 20)
        self.assertAlmostEqual(result["graph_period_ms"], 1024 / 48)
        self.assertEqual([row["raw_delay_ms"] for row in result["trials"]], [10, 20, 30])
        self.assertEqual([row["raw_unit"] for row in result["trials"]], ["ms", "s", "samples"])

    def test_corrections_and_clock_offsets_are_explicit_and_bounds_add(self):
        clock = {"relationship": "synchronised", "model_id": "clock-a",
                 "offset_ms": 2, "uncertainty_ms": 0.5}
        corrections = [{"model_id": "cable-a", "kind": "propagation",
                        "delay_ms": 1, "uncertainty_ms": 0.1},
                       {"model_id": "adc-a", "kind": "converter",
                        "delay_ms": 3, "uncertainty_ms": 0.2}]
        result = group([trial(delay=20, clock=clock, corrections=corrections)])
        row = result["trials"][0]
        self.assertEqual(row["raw_delay_ms"], 20)
        self.assertEqual(row["corrected_delay_ms"], 14)
        self.assertAlmostEqual(row["combined_uncertainty_bound_ms"], 1.05)
        self.assertEqual(row["clock"], clock)
        self.assertEqual([value["model_id"] for value in row["corrections"]], ["adc-a", "cable-a"])
        self.assertEqual(result["statistics"]["corrected_ms"]["median"], 14)

    def test_unsynchronised_clock_is_excluded_and_has_no_corrected_result(self):
        result = group([trial(clock={"relationship": "unsynchronised"})])
        self.assertEqual(result["statistics"]["included_count"], 0)
        self.assertEqual(result["trials"][0]["exclusion_reasons"], ["clock-invalid"])
        self.assertIsNone(result["trials"][0]["corrected_delay_ms"])
        self.assertIsNone(result["statistics"]["corrected_ms"])

    def test_signed_av_offset_and_negative_non_av_model_result(self):
        result = group([trial(delay=-5, kind="av-offset")])
        self.assertEqual(result["statistics"]["corrected_ms"]["median"], -5)
        self.bad(document([trial(delay=-5)]), "invalid_delay")
        correction = [{"model_id": "adc", "kind": "converter", "delay_ms": 11,
                       "uncertainty_ms": 2}]
        row = group([trial(corrections=correction)])["trials"][0]
        self.assertEqual(row["corrected_delay_ms"], -1)
        self.assertEqual(row["exclusion_reasons"], ["negative-corrected-delay"])

    def test_flags_force_exclusion_despite_valid_boolean_and_keep_all_reasons(self):
        result = group([trial(1), trial(2, 10000, flags=["clipping", "xrun"]),
                        trial(3, 30000, valid=False, rejection_reason="operator-rejected")])
        self.assertEqual(result["statistics"]["corrected_ms"]["max"], 10)
        self.assertEqual(result["statistics"]["excluded_count"], 2)
        self.assertEqual(result["statistics"]["exclusion_reason_counts"],
                         {"clipping": 1, "operator-rejected": 1, "xrun": 1})
        self.assertTrue(result["trials"][1]["input_valid"])
        self.assertEqual(result["trials"][1]["input_flags"], ["clipping", "xrun"])
        self.assertFalse(result["trials"][2]["input_valid"])

    def test_each_confounded_dimension_produces_a_separate_group(self):
        alternatives = [{"route": "usb-interface"}, {"kind": "round-trip"},
                        {"configuration_id": "candidate-256"}, {"power_state": "battery"},
                        {"load_state": "bounded-load"}, {"dsp_state": "candidate-eq"},
                        {"method": "threshold-onset"}, {"sample_rate_hz": 44100},
                        {"graph": {"quantum_frames": 256, "rate_hz": 48000}},
                        {"graph": None}, {"clock": {"relationship": "unsynchronised"}},
                        {"corrections": [{"model_id": "adc-a", "kind": "converter",
                                          "delay_ms": 1, "uncertainty_ms": 0.1}]}]
        for changes in alternatives:
            with self.subTest(changes=changes):
                self.assertEqual(len(latency.analyse(document([trial(1), trial(2, **changes)]))
                                     ["groups"]), 2)
        value = document([trial(1), trial(2, setup_id="rig-b")])
        value["setups"].append({"setup_id": "rig-b", "system": "m4-air",
                                "os": "macos-test", "interface": "shared-interface"})
        self.assertEqual(len(latency.analyse(value)["groups"]), 2)

    def test_bound_order_statistics_account_for_heterogeneous_uncertainty(self):
        stats = group([trial(1, 10, uncertainty={"bound": 100, "unit": "ms"}),
                       trial(2, 20, uncertainty={"bound": 1, "unit": "ms"}),
                       trial(3, 30, uncertainty={"bound": 2, "unit": "ms"})])["statistics"]
        self.assertEqual(stats["uncertainty"]["corrected_statistic_bounds_ms"]["median"],
                         [19, 32])
        self.assertEqual(stats["uncertainty"]["sampling_confidence_interval"], "not-estimated")

    def test_synthetic_never_qualifies_even_with_one_hundred_trials(self):
        trials = [trial(i) for i in range(100)]
        result = latency.analyse(document(trials))
        self.assertEqual(result["evidence_class"], "synthetic")
        self.assertEqual(result["qualification"], "not-established")
        self.assertEqual(result["groups"][0]["onset_trial_count_gate"]["status"], "synthetic-only")
        real = latency.analyse(document(trials, evidence="physical-measurement"))
        self.assertEqual(real["groups"][0]["onset_trial_count_gate"]["status"], "count-met")
        self.assertEqual(real["qualification"], "not-established")
        trials[-1]["flags"] = ["xrun"]
        real = latency.analyse(document(trials, evidence="physical-measurement"))
        self.assertEqual(real["groups"][0]["onset_trial_count_gate"]["status"], "insufficient-trials")

    def test_zero_trials_and_all_excluded_are_not_zero_latency(self):
        result = latency.analyse(document([]))
        self.assertEqual(result["total_count"], 0)
        self.assertEqual(result["groups"], [])
        result = group([trial(valid=False, rejection_reason="capture-incomplete")])
        self.assertIsNone(result["statistics"]["raw_ms"])
        self.assertIsNone(result["statistics"]["uncertainty"])

    def test_schema_unknown_fields_bool_rates_and_nonfinite_values_fail_closed(self):
        for changes in ({"delay": float("nan")}, {"delay": float("inf")},
                        {"delay": float("-inf")}, {"delay": True}, {"delay": 10 ** 400},
                        {"sample_rate_hz": 0}, {"sample_rate_hz": -1},
                        {"sample_rate_hz": True}, {"sample_rate_hz": 48000.0},
                        {"sample_rate_hz": 1000000}, {"unit": "PRIVATE_UNIT"},
                        {"unit": "samples", "sample_rate_hz": None},
                        {"unit": "samples", "delay": 1.5}, {"valid": 1},
                        {"valid": False}, {"rejection_reason": "clipping"},
                        {"flags": ["xrun", "xrun"]}, {"flags": ["PRIVATE_FLAG"]},
                        {"route": "/home/PRIVATE/device"}, {"method": "PRIVATE\nERROR"},
                        {"clock": {"relationship": "same-clock", "offset_ms": 1}},
                        {"clock": {"relationship": "synchronised"}},
                        {"clock": {"relationship": ["PRIVATE"]}},
                        {"graph": {"quantum_frames": 0, "rate_hz": 48000}},
                        {"graph": {"quantum_frames": 256, "rate_hz": True}},
                        {"uncertainty": {"bound": -1, "unit": "ms"}},
                        {"PRIVATE_FIELD": "PRIVATE_VALUE"}):
            with self.subTest(changes=changes):
                self.bad(document([trial(**changes)]))
        for version in (True, 2, "1"):
            value = document()
            value["schema_version"] = version
            self.bad(value, "unsupported_schema")
        value = document()
        value["PRIVATE_FIELD"] = "PRIVATE_VALUE"
        self.bad(value, "invalid_fields")

    def test_duplicate_unknown_setups_trials_and_correction_models_rejected(self):
        self.bad(document([trial(), trial()]), "duplicate_trial_id")
        self.bad(document([trial(setup_id="missing")]), "unknown_setup")
        value = document()
        value["setups"] *= 2
        self.bad(value, "duplicate_setup")
        correction = {"model_id": "adc", "kind": "converter", "delay_ms": 1,
                      "uncertainty_ms": 0}
        self.bad(document([trial(corrections=[correction, correction])]), "duplicate_correction")
        self.bad(document([trial(corrections=[dict(correction, delay_ms=-1)])]),
                 "invalid_correction_delay")
        self.bad(document([trial(corrections=[dict(correction, uncertainty_ms=float("nan"))])]),
                 "invalid_correction_uncertainty")

    def test_output_order_is_deterministic_without_mutating_input(self):
        value = document([trial(3), trial(1), trial(2, route="usb")])
        original = copy.deepcopy(value)
        first = latency.analyse(value)
        value["trials"].reverse()
        second = latency.analyse(value)
        self.assertEqual(first, second)
        value["trials"].reverse()
        self.assertEqual(value, original)

    def test_json_duplicate_keys_nonfinite_and_malformed_payloads_are_controlled(self):
        for data, reason in ((b'{"schema_version":1,"schema_version":2}', "duplicate_json_key"),
                             (b'{"delay": NaN}', "nonfinite_json"),
                             (b'{"delay": Infinity}', "nonfinite_json"),
                             (b'PRIVATE_NOT_JSON', "invalid_json"),
                             (b'\xff', "invalid_json"),
                             (b'[' * 2000 + b']' * 2000, "json_nesting_limit")):
            with self.subTest(reason=reason):
                with self.assertRaises(latency.TrialError) as caught:
                    latency.parse_input(data)
                self.assertEqual(str(caught.exception), reason)

    def test_tracked_synthetic_example_matches_its_source_hash_and_analysis(self):
        root = SCRIPT.parents[1]
        source = (root / "tests/audio/synthetic-trials.json").read_bytes()
        expected = json.loads((root / "evidence/audio-latency-synthetic-analysis.json").read_text())
        actual = latency.analyse(latency.parse_input(source), hashlib.sha256(source).hexdigest())
        self.assertEqual(actual, expected)
        self.assertEqual(actual["evidence_class"], "synthetic")
        self.assertEqual(actual["groups"][0]["statistics"]["corrected_ms"]["p95"], 19)

    def test_distinct_clock_calibrations_are_separate_and_quotes_do_not_count_depth(self):
        clock = {"relationship": "synchronised", "model_id": "clock-a",
                 "offset_ms": 1, "uncertainty_ms": 0.1}
        values = [trial(1, clock=clock), trial(2, clock=dict(clock, offset_ms=2)),
                  trial(3, clock=dict(clock, uncertainty_ms=0.2))]
        self.assertEqual(len(latency.analyse(document(values))["groups"]), 3)
        encoded = json.dumps({"PRIVATE": '[' * 100 + '\\"' + ']' * 100}).encode()
        self.assertEqual(latency.parse_input(encoded)["PRIVATE"], '[' * 100 + '\\"' + ']' * 100)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "PRIVATE-trials.json"
        self.source.write_text(json.dumps(document()))
        self.output = self.root / "result.json"

    def run_cli(self, source=None, output=None):
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            code = latency.main(["--input", str(source or self.source),
                                 "--output", str(output or self.output)])
        self.assertNotIn("PRIVATE", errors.getvalue())
        self.assertNotIn(str(self.root), errors.getvalue())
        return code, errors.getvalue()

    def test_new_report_is_exclusive_private_and_hashes_exact_source(self):
        original = self.source.read_bytes()
        self.assertEqual(self.run_cli(), (0, ""))
        result = json.loads(self.output.read_text())
        self.assertEqual(result["input_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o600)
        self.assertEqual(self.source.read_bytes(), original)
        previous = self.output.read_bytes()
        self.assertEqual(self.run_cli(), (1, "Latency analysis error: output_write_failed\n"))
        self.assertEqual(self.output.read_bytes(), previous)
        self.assertEqual(self.run_cli(output=self.source)[0], 1)
        self.assertEqual(self.source.read_bytes(), original)

    def test_invalid_or_missing_input_produces_no_output_or_private_error_text(self):
        self.source.write_text("PRIVATE_NOT_JSON")
        self.assertEqual(self.run_cli(), (2, "Latency analysis error: invalid_json\n"))
        self.assertFalse(self.output.exists())
        self.assertEqual(self.run_cli(source=self.root / "PRIVATE_missing")[0], 2)
        with mock.patch.object(latency.os, "open", side_effect=PermissionError("PRIVATE_ERROR")):
            self.assertEqual(self.run_cli()[0], 2)

    def test_special_files_and_symlinks_never_block_or_overwrite_targets(self):
        link = self.root / "PRIVATE_link"
        link.symlink_to(self.source)
        self.assertEqual(self.run_cli(source=link)[0], 2)
        self.assertEqual(self.run_cli(source=self.root)[0], 2)
        self.assertEqual(self.run_cli(output=link)[0], 1)
        fifo = self.root / "PRIVATE_fifo"
        os.mkfifo(fifo)
        result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(fifo),
                                 "--output", str(self.output)], timeout=5, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, b"Latency analysis error: input_not_regular_file\n")
        self.assertFalse(self.output.exists())

    def test_oversized_and_concurrently_changed_inputs_fail(self):
        with self.source.open("wb") as output:
            output.truncate(latency.MAX_BYTES + 1)
        self.assertEqual(self.run_cli(), (2, "Latency analysis error: input_too_large\n"))
        self.source.write_text(json.dumps(document()))
        original_read = latency.os.read
        calls = []

        def changing_read(fd, length):
            data = original_read(fd, length)
            if not calls:
                calls.append(True)
                with self.source.open("ab") as output:
                    output.write(b" ")
            return data

        with mock.patch.object(latency.os, "read", side_effect=changing_read):
            self.assertEqual(self.run_cli(), (2, "Latency analysis error: input_changed_during_read\n"))

    def test_argument_errors_do_not_echo_private_unknown_arguments(self):
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors), self.assertRaises(SystemExit) as caught:
            latency.main(["--input", "PRIVATE_INPUT", "--output", "PRIVATE_OUTPUT",
                          "--PRIVATE_FLAG"])
        self.assertEqual(caught.exception.code, 2)
        self.assertNotIn("PRIVATE", errors.getvalue())
        self.assertIn("invalid_arguments", errors.getvalue())

    def test_no_commands_are_run_by_offline_cli(self):
        with mock.patch.object(subprocess, "run", side_effect=AssertionError("No subprocess")), \
             mock.patch.object(os, "system", side_effect=AssertionError("No shell")):
            self.assertEqual(self.run_cli(), (0, ""))


if __name__ == "__main__":
    unittest.main()
