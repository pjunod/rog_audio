"""Exercise exact-source staging inside an unrelated Git checkout."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_easyeffects_runtime as build

class SourcePreparationTests(unittest.TestCase):
    def test_pinned_objects_exclude_working_tree_and_patches_apply_inside_git(self):
        upstream=os.environ.get('ROG_EASYEFFECTS_GIT')
        if not upstream:raise unittest.SkipTest('ROG_EASYEFFECTS_GIT selects pinned public Git objects')
        with tempfile.TemporaryDirectory(prefix='rog-ee-source-test-') as temporary:
            root=Path(temporary);repository=root/'public-git'
            subprocess.run(['git','clone','--shared','--no-checkout',upstream,str(repository)],check=True,capture_output=True)
            (repository/'ignored-owner-data').write_bytes(b'PRIVATE MARKER NEVER ENTERS BUILD')
            parent=repository/'nested';parent.mkdir();source=build.source_snapshot(repository,parent/'source')
            self.assertFalse((source/'ignored-owner-data').exists())
            self.assertFalse((source/'.git').exists())
            self.assertIn('org.rog_audio.SpeakerEffects',(source/'src/tags_app.hpp').read_text())
            self.assertIn('RogAudioSpeakerEffectsServer',(source/'src/tags_local_server.hpp').read_text())
            self.assertTrue((source/'src/speaker_routing.hpp').is_file())
            self.assertTrue((source/'src/output_route_cache.hpp').is_file())
            self.assertTrue((source/'src/programme_makeup_gain.hpp').is_file())
            self.assertIn('settings->maximumGain()', (source/'src/autogain.cpp').read_text())
            self.assertIn('maximum-gain', (source/'src/autogain_preset.cpp').read_text())
            self.assertIn('current_output_node',(source/'src/stream_output_effects.cpp').read_text())
            self.assertIn('list[row].profile_device = new_info.profile_device;',
                          (source/'src/pw_model_nodes.cpp').read_text())
            self.assertIn('GNU',(source/'LICENSE').read_text())
            self.assertNotIn('webrtc-audio-processing-2',(source/'CMakeLists.txt').read_text())
            with self.assertRaises(build.BuildError):build.source_snapshot(repository,source)

if __name__=='__main__':unittest.main()
