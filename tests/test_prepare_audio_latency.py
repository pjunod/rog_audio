import copy
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_audio_latency as candidate
from test_inspect_audio import fixture


def inventory():
    f=fixture()
    graph=json.loads(f['probes']['graph']['stdout'])
    graph[1]['info']['props'].update({'node.name':'alsa_output.test.analog-stereo','device.id':42,'card.profile.device':0})
    graph.append({'id':42,'type':'PipeWire:Interface:Device','info':{'params':{'Route':[{'name':'analog-output-speaker','direction':'Output','device':0}]}}})
    f['probes']['graph']['stdout']=json.dumps(graph)
    return f


def generate(f=None,quantum=256):
    return candidate.prepare(f or inventory(),'0'*64,quantum,'alsa_output.test.analog-stereo','analog-output-speaker','pw-play')


class CandidateTests(unittest.TestCase):
    def test_deterministic_and_scoped(self):
        conf,manifest=generate()
        self.assertEqual((conf,manifest),generate())
        self.assertIn('node.latency = "256/48000"',conf)
        self.assertIn('target.object = "alsa_output.test.analog-stereo"',conf)
        self.assertIn('application.process.binary = "pw-play"',conf)
        self.assertNotIn('force-quantum',conf)
        self.assertEqual(manifest['activation_state'],'not-installed')
        self.assertEqual(manifest['validation_state'],'unvalidated')
        self.assertEqual(manifest['observed']['default_quantum_frames'],1024)

    def test_versions_previous_config_and_route_required(self):
        for mutate in (lambda f:f['probes'].pop('wireplumber_version'),
                       lambda f:f.update(user_config={'status':'unavailable'}),
                       lambda f:f['probes']['graph'].update(stdout=f['probes']['graph']['stdout'].replace('analog-output-speaker','headphones'))):
            f=inventory();mutate(f)
            with self.assertRaises(ValueError):generate(f)
        for quantum in (True,0,1024):
            with self.assertRaises(ValueError):generate(quantum=quantum)

    def test_malformed_fields_and_old_client_config_versions_refused(self):
        for key in ('probes','user_config'):
            f=inventory();f[key]=None
            with self.assertRaises(ValueError):generate(f)
        f=inventory();f['probes']['pipewire_version']['stdout']='Compiled with libpipewire 1.2.0'
        with self.assertRaises(ValueError):generate(f)
        f=inventory();g=json.loads(f['probes']['graph']['stdout']);g[-1]['info']['params']['Route']=None;f['probes']['graph']['stdout']=json.dumps(g)
        with self.assertRaises(ValueError):generate(f)

    def test_missing_identifiers_cannot_resolve_by_none_equality(self):
        f=inventory();g=json.loads(f['probes']['graph']['stdout'])
        g[1]['info']['props'].pop('device.id')
        g[1]['info']['props'].pop('card.profile.device')
        g[-1].pop('id');g[-1]['info']['params']['Route'][0].pop('device')
        f['probes']['graph']['stdout']=json.dumps(g)
        with self.assertRaises(ValueError):generate(f)
        f=inventory();g=json.loads(f['probes']['graph']['stdout'])
        g[1]['info']['props']['device.id']=True
        f['probes']['graph']['stdout']=json.dumps(g)
        with self.assertRaises(ValueError):generate(f)

    def test_duplicate_target_refused(self):
        f=inventory();g=json.loads(f['probes']['graph']['stdout']);g.append(copy.deepcopy(g[1]));f['probes']['graph']['stdout']=json.dumps(g)
        with self.assertRaises(ValueError):generate(f)

    def test_bundle_never_overwrites_and_is_private(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bundle';conf,manifest=generate();candidate.write_bundle(path,conf,manifest,inventory())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o700)
            self.assertTrue(all(stat.S_IMODE(p.stat().st_mode)==0o600 for p in path.iterdir()))
            with self.assertRaises(FileExistsError):candidate.write_bundle(path,conf,manifest,inventory())
            self.assertEqual((path/candidate.CONFIG_FILE).read_text(),conf)
            alias=Path(d)/'alias';alias.symlink_to(path)
            with self.assertRaises(FileExistsError):candidate.write_bundle(alias,conf,manifest,inventory())

if __name__ == '__main__':unittest.main()
