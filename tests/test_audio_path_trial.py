"""File-only private trial safety; invented captures, no services or audio."""
import copy
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parent/'audio'))
import audio_path_trial as trial
import run_path_units as units
from audio_path_fixture import setup


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.kit, self.binary, self.env, self.inv, self.capture = setup(self.root)
        self.bundle = self.root/'trial'; self.snapshot = self.root/'trial-snapshot'
        self.config = self.root/'state/config/pipewire'
        self.target = self.config/trial.FILE
        self.overrides = {'status': 'ok', 'current': {}, 'manager': {}, 'unit': {}}

    def prepare(self): return trial.prepare(self.capture, '0'*64, 256, self.bundle)
    def install(self):
        return trial.install(self.bundle, self.kit, self.binary, self.snapshot,
                             self.inv, self.overrides, self.env,
                             refresh_inventory=lambda: copy.deepcopy(self.inv),
                             refresh_overrides=lambda: copy.deepcopy(self.overrides))

    def test_one_private_filter_changes_no_dsp_and_restores_absent_file(self):
        self.prepare()
        original = copy.deepcopy(self.capture['speaker_before'])
        result = self.install()
        self.assertFalse(result['runtime_started'])
        content = self.target.read_bytes()
        self.assertIn(b'filter.rules', content)
        self.assertIn(b'node.latency = "256/48000"', content)
        for value in (trial.path.APP, trial.path.FILTER, trial.path.GROUP, 'media.role = "DSP"'):
            self.assertIn(value.encode(), content)
        self.assertNotIn(b'force-quantum', content)
        self.assertNotIn(b'stream.rules', content)
        self.assertEqual(trial.path.state_snapshot(self.kit, self.binary, self.env)['payload'], original['payload'])
        self.assertEqual(trial.path.state_snapshot(self.kit, self.binary, self.env)['rc'], original['rc'])
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o600)
        result = trial.remove(self.snapshot, self.root/'archive', self.inv, self.env)
        self.assertFalse(result['runtime_started'])
        self.assertFalse(self.target.exists())
        self.assertEqual(trial.status(self.snapshot, self.env)['status'], 'removed')
        self.assertEqual((self.root/'archive/quarantine/removed-rule.conf').read_bytes(), content)

    def test_replacement_after_archive_is_restored_without_deleting_user_file(self):
        self.prepare(); self.install()
        real = trial.rename_absent
        replacement = self.root/'replacement'; replacement.write_bytes(b'new-user-rule')
        changed = [False]
        def swap(parent, name, destination, moved):
            if not changed[0]:
                changed[0] = True; replacement.replace(self.target)
            return real(parent, name, destination, moved)
        with mock.patch.object(trial, 'rename_absent', side_effect=swap):
            with self.assertRaises(trial.RemovalConflict) as error:
                trial.remove(self.snapshot, self.root/'archive', self.inv, self.env)
        self.assertEqual(error.exception.recovery, 'restored-original-path')
        self.assertEqual(self.target.read_bytes(), b'new-user-rule')
        self.assertEqual(trial.status(self.snapshot, self.env)['status'], 'installed')

    def test_replacement_during_restore_preserves_both_user_inodes(self):
        self.prepare(); self.install()
        real = trial.rename_absent
        replacement = self.root/'replacement'; replacement.write_bytes(b'first-new-user-rule')
        calls = [0]
        def swap(parent, name, destination, moved):
            calls[0] += 1
            if calls[0] == 1: replacement.replace(self.target)
            if calls[0] == 2: self.target.write_bytes(b'second-new-user-rule')
            return real(parent, name, destination, moved)
        with mock.patch.object(trial, 'rename_absent', side_effect=swap):
            with self.assertRaises(trial.RemovalConflict) as error:
                trial.remove(self.snapshot, self.root/'archive', self.inv, self.env)
        self.assertEqual(error.exception.recovery, 'retained-in-archive')
        self.assertEqual(self.target.read_bytes(), b'second-new-user-rule')
        self.assertEqual((self.root/'archive/quarantine/removed-rule.conf').read_bytes(), b'first-new-user-rule')
        self.assertEqual(json.loads((self.root/'archive/removal.json').read_bytes())['state'], 'retained-in-archive')

    def test_retained_removed_inode_preserves_later_open_descriptor_writes(self):
        self.prepare(); self.install()
        with self.target.open('r+b', buffering=0) as writer:
            original_inode = self.target.stat().st_ino
            trial.remove(self.snapshot, self.root/'archive', self.inv, self.env)
            writer.seek(0); writer.write(b'late-user-write'); writer.flush()
        retained = self.root/'archive/quarantine/removed-rule.conf'
        self.assertEqual(retained.stat().st_ino, original_inode)
        self.assertTrue(retained.read_bytes().startswith(b'late-user-write'))
        self.assertFalse(self.target.exists())

    def test_override_changed_during_snapshot_refuses_publication(self):
        for key, scope in (('PIPEWIRE_LATENCY', 'manager'), ('PIPEWIRE_QUANTUM', 'unit')):
            with self.subTest(key=key):
                root = self.root/key.lower(); root.mkdir()
                kit, binary, env, inv, capture = setup(root)
                bundle, snapshot = root/'trial', root/'trial-snapshot'
                trial.prepare(capture, '0'*64, 256, bundle)
                overrides = copy.deepcopy(self.overrides)
                real = trial.speaker.snapshot
                def mutate(*args, **kwargs):
                    result = real(*args, **kwargs)
                    overrides[scope][key] = '1024/48000'
                    return result
                with mock.patch.object(trial.speaker, 'snapshot', side_effect=mutate):
                    with self.assertRaises(ValueError):
                        trial.install(bundle, kit, binary, snapshot, inv, overrides, env,
                                      refresh_inventory=lambda: copy.deepcopy(inv),
                                      refresh_overrides=lambda: copy.deepcopy(overrides))
                self.assertFalse((root/'state/config/pipewire'/trial.FILE).exists())
                self.assertEqual(trial.status(snapshot, env)['status'], 'install-incomplete')

    def test_candidate_restarted_during_snapshot_refuses_publication(self):
        self.prepare(); real = trial.speaker.snapshot
        def mutate(*args, **kwargs):
            result = real(*args, **kwargs)
            graph = json.loads(self.inv['probes']['graph']['stdout'])
            graph.append({'type': 'PipeWire:Interface:Node', 'info': {'props': {'application.id': trial.path.APP}}})
            self.inv['probes']['graph']['stdout'] = json.dumps(graph)
            return result
        with mock.patch.object(trial.speaker, 'snapshot', side_effect=mutate):
            with self.assertRaises(trial.speaker.InstallError): self.install()
        self.assertFalse(self.target.exists())
        self.assertEqual(trial.status(self.snapshot, self.env)['status'], 'install-incomplete')

    def test_preexisting_and_new_unrelated_config_survive(self):
        self.config.mkdir(parents=True); (self.config/'stock.conf').write_bytes(b'stock=unchanged')
        current = trial.path.state_snapshot(self.kit, self.binary, self.env)
        self.capture['speaker_before'] = current; self.capture['speaker_after'] = copy.deepcopy(current)
        self.prepare(); self.install()
        (self.config/'later.conf').write_bytes(b'later=user-edit')
        trial.remove(self.snapshot, self.root/'archive', self.inv, self.env)
        self.assertEqual((self.config/'stock.conf').read_bytes(), b'stock=unchanged')
        self.assertEqual((self.config/'later.conf').read_bytes(), b'later=user-edit')
        self.assertEqual((self.snapshot/'before/pipewire/stock.conf').read_bytes(), b'stock=unchanged')

    def test_route_drift_or_runtime_change_refuses_installation(self):
        self.prepare()
        bad = copy.deepcopy(self.inv); graph = json.loads(bad['probes']['graph']['stdout'])
        graph[0]['info']['props']['node.name'] = 'alsa_output.test.analog-surround-40'
        bad['probes']['graph']['stdout'] = json.dumps(graph)
        with self.assertRaises(ValueError): trial.install(self.bundle, self.kit, self.binary, self.snapshot, bad, self.overrides, self.env)
        self.assertFalse(self.target.exists())
        self.binary.write_bytes(b'new-runtime')
        with self.assertRaises(ValueError): self.install()
        self.assertFalse(self.target.exists())

    def test_process_manager_unit_or_unknown_overrides_are_conflicts(self):
        for mutate in (lambda c:c['process_environment']['values'].update(PIPEWIRE_LATENCY='1024/48000'),
                       lambda c:c['restart_environment']['manager'].update(PIPEWIRE_QUANTUM='64/48000'),
                       lambda c:c['restart_environment'].update(status='unavailable')):
            candidate = copy.deepcopy(self.capture); mutate(candidate)
            with self.assertRaises(ValueError): trial.prepare(candidate, '0'*64, 256, self.bundle)
        self.prepare(); self.overrides['unit']['PIPEWIRE_PROPS'] = 'node.force-quantum=64'
        with self.assertRaises(ValueError): self.install()
        self.assertFalse(self.target.exists())

    def test_occupied_path_and_racing_creation_are_never_overwritten(self):
        self.prepare()
        real = trial.publish_absent
        def race(target, content):
            target.write_bytes(b'concurrent-user-config')
            return real(target, content)
        with mock.patch.object(trial, 'publish_absent', side_effect=race):
            with self.assertRaises(FileExistsError): self.install()
        self.assertEqual(self.target.read_bytes(), b'concurrent-user-config')
        self.assertEqual(trial.status(self.snapshot, self.env)['status'], 'install-incomplete')

    def test_snapshot_fsync_failure_prevents_live_file_publication(self):
        self.prepare()
        with mock.patch.object(trial.speaker, 'durable_new_file', side_effect=OSError('fsync failed')):
            with self.assertRaises(OSError): self.install()
        self.assertFalse(self.target.exists())

    def test_incomplete_publication_journal_can_remove_exact_owned_file(self):
        self.prepare(); original = trial.speaker.replace; count = [0]
        def interrupted(target, content, *args):
            count[0] += 1
            if count[0] == 3: raise OSError('crash after complete file publication')
            return original(target, content, *args)
        with mock.patch.object(trial.speaker, 'replace', side_effect=interrupted):
            with self.assertRaises(OSError): self.install()
        self.assertTrue(self.target.exists())
        self.assertEqual(trial.status(self.snapshot, self.env)['status'], 'install-incomplete')
        trial.remove(self.snapshot, self.root/'archive', self.inv, self.env)
        self.assertFalse(self.target.exists())

    def test_edited_rule_or_archive_fsync_failure_preserves_live_bytes(self):
        self.prepare(); self.install()
        original = self.target.read_bytes(); self.target.write_bytes(original+b'# user edit\n')
        with self.assertRaises(ValueError): trial.remove(self.snapshot, self.root/'archive', self.inv, self.env)
        self.assertIn(b'user edit', self.target.read_bytes())
        self.target.write_bytes(original)
        with mock.patch.object(trial.speaker, 'durable_new_file', side_effect=OSError('archive fsync failed')):
            with self.assertRaises(OSError): trial.remove(self.snapshot, self.root/'archive', self.inv, self.env)
        self.assertEqual(self.target.read_bytes(), original)

    def test_bundle_rule_or_capture_tampering_is_refused(self):
        self.prepare(); candidate = self.bundle/'candidate.conf'; candidate.write_bytes(b'global-forcing-is-not-this-trial')
        with self.assertRaises(ValueError): self.install()
        candidate.write_bytes(trial.rule(256))
        capture = self.bundle/'baseline-capture.json'; capture.write_bytes(b'{}')
        with self.assertRaises(ValueError): self.install()
        self.assertFalse(self.target.exists())

    def test_baseline_edit_and_active_candidate_refuse_installation(self):
        self.prepare()
        active = copy.deepcopy(self.inv); graph = json.loads(active['probes']['graph']['stdout'])
        graph.append({'type': 'PipeWire:Interface:Node', 'info': {'props': {'application.id': trial.path.APP}}})
        active['probes']['graph']['stdout'] = json.dumps(graph)
        with self.assertRaises(trial.speaker.InstallError): trial.install(self.bundle, self.kit, self.binary, self.snapshot, active, self.overrides, self.env)
        rc = self.root/'state/config/easyeffects/db/limiterrc'; rc.write_bytes(b'user limiter change')
        with self.assertRaises(ValueError): self.install()
        self.assertFalse(self.target.exists())

    def test_symlink_or_arbitrary_snapshot_scope_cannot_direct_removal(self):
        self.prepare(); self.install()
        journal = self.snapshot/'snapshot.json'; state = json.loads(journal.read_bytes())
        state['roots']['pipewire'] = str(self.root/'unrelated')
        journal.write_bytes(trial.speaker.encoded(state))
        with self.assertRaises(ValueError): trial.remove(self.snapshot, self.root/'archive', self.inv, self.env)
        self.assertTrue(self.target.exists())
        link = self.root/'snapshot-link'; link.symlink_to(self.snapshot)
        with self.assertRaises(trial.speaker.InstallError): trial.status(link, self.env)

    def test_corrupt_lifecycle_is_rejected_without_echoing_payload(self):
        self.prepare(); self.install()
        journal = self.snapshot/'snapshot.json'; state = json.loads(journal.read_bytes())
        state['state'] = {'secret': 'private-corrupt-payload'}
        journal.write_bytes(trial.speaker.encoded(state))
        with self.assertRaises(ValueError): trial.status(self.snapshot, self.env)

    def test_acceptance_selector_rejects_invalid_ids_empty_and_skipped_results(self):
        for identifiers in (['test_inspect_audio_path.PathTests.test_missing'],
                            ['os.system'],
                            ['test_audio_path_trial.TrialTests.test_missing'],
                            ['test_audio_path_trial.TrialTests.test_missing']*2):
            with self.assertRaises(ValueError): units.suite('unit-trial', identifiers)
        result = unittest.TestResult()
        self.assertFalse(units.accepted(result))
        result.testsRun = 1; result.skipped = [('synthetic-id', 'synthetic skip')]
        self.assertFalse(units.accepted(result))

    def test_subtest_failure_and_skip_return_parent_retry_id(self):
        class Example(unittest.TestCase):
            def exercise(self):
                with self.subTest(text='synthetic subtest with spaces'):
                    self.fail('deliberate nested failure')
                with self.subTest(text='synthetic skipped subtest'):
                    self.skipTest('deliberate nested skip')
        case = Example('exercise')
        result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=units.RetryResult).run(case)
        self.assertEqual(result.failed_ids, {case.id()})
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(len(result.skipped), 1)
        self.assertFalse(units.accepted(result))


if __name__ == '__main__': unittest.main()
