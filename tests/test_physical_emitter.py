"""New emitter tests use Node with synthetic DOM/audio; no browser IO or sound."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PhysicalEmitterTests(unittest.TestCase):
    def case(self, name):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node.js is required; missing runtime is not a skip')
        result = subprocess.run([node, str(ROOT/'tests/physical_emitter_cases.js'), name],
                                capture_output=True, text=True, timeout=15, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {'case': name, 'passed': True})

    def test_no_autoplay_and_invalid_arm(self): self.case('no_autoplay_and_invalid_arm')
    def test_signal_bounds_taper_and_actual_rate(self): self.case('signal_bounds_taper_and_actual_rate')
    def test_trusted_key_repeat_modifiers_and_cooldown(self): self.case('trusted_key_repeat_modifiers_and_cooldown')
    def test_warm_stream_log_is_diagnostic_and_export_is_detached(self): self.case('warm_stream_log_is_diagnostic_and_export_is_detached')
    def test_reference_wave_is_actual_preloaded_stereo_signal(self): self.case('reference_wave_is_actual_preloaded_stereo_signal')
    def test_stop_cancels_owned_nodes_without_touching_other_audio(self): self.case('stop_cancels_owned_nodes_without_touching_other_audio')
    def test_pending_arm_cancel_and_stale_state_event(self): self.case('pending_arm_cancel_and_stale_state_event')
    def test_failures_do_not_leave_warm_or_chirp_sources(self): self.case('failures_do_not_leave_warm_or_chirp_sources')
    def test_close_in_progress_blocks_rearm_and_event_limit_stops(self): self.case('close_in_progress_blocks_rearm_and_event_limit_stops')
    def test_browser_wiring_focus_and_hidden_disarm_without_autoplay(self): self.case('browser_wiring_focus_and_hidden_disarm_without_autoplay')


if __name__ == '__main__':
    unittest.main()
