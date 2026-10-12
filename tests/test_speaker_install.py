"""Invented bundles and temp trees; no live installs, commands or sound."""
import copy
import json
from pathlib import Path
import stat
import struct
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import speaker_install as kit


def inventory(subsystem='10431c63'):
    graph=[{'type':'PipeWire:Interface:Node','info':{'props':{
        'node.name':'alsa_output.test.analog-stereo','media.class':'Audio/Sink','device.api':'alsa',
        'api.alsa.pcm.card':3,'device.id':42,'card.profile.device':0}}},
        {'id':42,'type':'PipeWire:Interface:Device','info':{'params':{'Route':[
         {'device':0,'direction':'Output','name':'analog-output-speaker','description':'Speakers'}]}}}]
    return {'schema_version':1,'kind':'audio-inventory','probes':{'graph':{'status':'ok','stdout':json.dumps(graph)}},
            'user_config':{'status':'ok','files':[]},'files':{'/proc/asound/card3/codec#0':{'status':'ok',
             'text':'Vendor Id: 0x10ec0285\nSubsystem Id: 0x'+subsystem+'\n'}}}


def synthetic_bundle(root):
    root.mkdir();(root/'irs').mkdir()
    samples=struct.pack('<8192f',.5,.5,*([0.]*(8192-2)))
    stem='speaker-'+kit.sha(samples)[:16]
    fmt=struct.pack('<HHIIHH',3,2,48000,384000,8,32)
    chunks=b'fmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(samples))+samples
    wav=b'RIFF'+struct.pack('<I',len(chunks)+4)+b'WAVE'+chunks
    order=['convolver#0','limiter#0']
    out={'plugins_order':order,'blocklist':[],'convolver#0':{'bypass':False,'input-gain':0,'output-gain':0,'autogain':False,'kernel-name':stem},
         'limiter#0':{'bypass':False,'input-gain':0,'output-gain':0}}
    files={'preset.json':kit.encoded({'output':out}),
           'field-mapping.json':kit.encoded({'schema_version':1,'complete_equivalence':False,
           'fields':[{'output_stage':'convolver#0','status':'mapped-static-approximation'}],
           'stages':[{'name':n,'bypassed':False} for n in order]}),'irs/'+stem+'.irs':wav}
    manifest={'schema_version':1,'activation_state':'not-installed','qualification':'offline-candidate-unqualified',
        'converter_commit':kit.speaker.PIN,'sample_rate_hz':48000,'channels':['FL','FR'],
        'hardware':{'codec':'10ec0285','subsystem':'10431c63','amplifiers':'CS35L56','count':2,'speaker_id':0},
        'selection':{'endpoint':'internal_speaker','mode':'normal','profile':'music','voicing':'balanced'},
        'inputs':{'xml_sha256':'0'*64,'inf_sha256':'0'*64,'inventory_sha256':'0'*64,'duplicate_xml':'not-verified'},
        'outputs':{n:kit.sha(b) for n,b in files.items()},'preset':'preset.json','mapping_report':'field-mapping.json','impulse':'irs/'+stem+'.irs'}
    for name,data in files.items():(root/name).write_bytes(data)
    (root/'manifest.json').write_bytes(kit.encoded(manifest))
    return root


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.bundle=synthetic_bundle(self.root/'source')
        self.runtime=self.root/'runtime';self.runtime.write_bytes(b'synthetic-runtime-never-executed')
        self.runtime_manifest=self.root/'runtime.json';self.runtime_manifest.write_bytes(kit.encoded({
            'schema_version':1,'source_commit':'6d9b1220d3dcebb154ba759a05600662bc0af549',
            'routing_contract':'exact-device-route-v1','binary_sha256':kit.sha(self.runtime.read_bytes())}))
        self.inv=inventory();self.locations={'data':self.root/'data','config':self.root/'config'}
        self.destination=self.root/'kit';self.snapshot=self.root/'snapshot'
        kit.prepare(self.bundle,self.inv,self.destination,self.runtime_manifest)

    def test_prepare_composes_verified_bundle_and_exact_description_autoload(self):
        _,manifest=kit.load_kit(self.destination)
        self.assertEqual(manifest['binding']['route_name'],'analog-output-speaker')
        autoload=json.loads(next((self.destination/'data/autoload/output').glob('*.json')).read_text())
        self.assertEqual(autoload['device-profile'],'Speakers')
        self.assertEqual(autoload['device'],'alsa_output.test.analog-stereo')
        self.assertEqual(manifest['activation_state'],'not-installed')
        self.assertEqual(kit.observed_route(inventory('17aa2276'),{'codec':'10ec0285','subsystem':'17aa2276'})['subsystem'],'17aa2276')

    def test_install_remove_restores_prior_bytes_and_retains_later_config(self):
        before=b'[Window]\notherPreference=unchanged\n\n[EffectsPipelines]\nprocessAllInputs=true\n'
        path=self.locations['config']/'db/easyeffectsrc';path.parent.mkdir(parents=True);path.write_bytes(before)
        original_inv=copy.deepcopy(self.inv)
        # The supplied runtime is never executed by install.
        result=kit.install(self.destination,self.snapshot,self.runtime,self.inv,self.locations)
        self.assertFalse(result['runtime_started']);self.assertEqual(self.inv,original_inv)
        path.write_bytes(path.read_bytes()+b'\n[NewUserSection]\nnewPreference=retain\n')
        archive=self.root/'remove-archive'
        removed=kit.remove(self.snapshot,archive,self.inv,self.locations)
        self.assertEqual(path.read_bytes(),before)
        self.assertTrue(removed['post_install_state_retained'])
        self.assertIn(b'newPreference=retain',(archive/'before/config/db/easyeffectsrc').read_bytes())
        self.assertEqual(kit.status(self.snapshot,self.locations)['status'],'removed')
        self.assertEqual(kit.status(self.snapshot,self.locations)['changed_owned_file_count'],0)

    def test_edited_owned_data_refuses_removal_without_erasing_user_work(self):
        kit.install(self.destination,self.snapshot,self.runtime,self.inv,self.locations)
        target=next((self.locations['data']/'output').glob('*.json'));target.write_bytes(b'user edit')
        with self.assertRaises(kit.InstallError) as error:
            kit.remove(self.snapshot,self.root/'archive',self.inv,self.locations)
        self.assertEqual(error.exception.reason,'owned_payload_changed');self.assertEqual(target.read_bytes(),b'user edit')

    def test_journal_recovers_file_written_before_installed_list_update(self):
        root,manifest=kit.load_kit(self.destination)
        directory,state=kit.snapshot(self.snapshot,self.locations,self.inv,manifest)
        payload={name:kit.read(root/name) for name in manifest['files']}
        state['planned']={n:kit.sha(b) for n,b in payload.items()};state['state']='installing'
        kit.replace(directory/'snapshot.json',kit.encoded(state))
        name=next(iter(payload));key,relative=name.split('/',1)
        target=self.locations[key]/relative;kit.mkdir(target.parent);kit.replace(target,payload[name])
        # Crash occurred before journalling this file in installed[].
        self.assertEqual(state['installed'],[])
        kit.remove(directory,self.root/'archive',self.inv,self.locations)
        self.assertFalse(target.exists())

    def test_wrong_route_runtime_running_and_symlink_are_refused(self):
        bad=copy.deepcopy(self.inv);g=json.loads(bad['probes']['graph']['stdout']);g[1]['info']['params']['Route'][0]['name']='analog-output-headphones';bad['probes']['graph']['stdout']=json.dumps(g)
        with self.assertRaises(kit.InstallError):kit.install(self.destination,self.snapshot,self.runtime,bad,self.locations)
        self.assertFalse(self.snapshot.exists())
        self.runtime.write_bytes(b'not the validated runtime')
        with self.assertRaises(kit.InstallError):kit.install(self.destination,self.snapshot,self.runtime,self.inv,self.locations)
        self.assertFalse(self.snapshot.exists())
        alias=self.root/'alias';alias.symlink_to(self.destination)
        with self.assertRaises(kit.InstallError):kit.load_kit(alias)
        running=copy.deepcopy(self.inv);g=json.loads(running['probes']['graph']['stdout']);g.append({'type':'PipeWire:Interface:Client','info':{'props':{'application.id':'org.rog_audio.SpeakerEffects'}}});running['probes']['graph']['stdout']=json.dumps(g)
        with self.assertRaises(kit.InstallError):kit.idle(running)

    def test_snapshot_bounds_permissions_and_tampered_escape(self):
        kit.install(self.destination,self.snapshot,self.runtime,self.inv,self.locations)
        self.assertEqual(stat.S_IMODE(self.snapshot.stat().st_mode),0o700)
        self.assertEqual(stat.S_IMODE((self.snapshot/'snapshot.json').stat().st_mode),0o600)
        p=self.snapshot/'snapshot.json';state=json.loads(p.read_text());state['planned']['data/../../outside']='0'*64;p.write_bytes(kit.encoded(state))
        with self.assertRaises(kit.InstallError):kit.remove(self.snapshot,self.root/'archive',self.inv,self.locations)


    def test_candidate_paths_and_stock_presence_are_separate(self):
        locations=kit.roots({'XDG_STATE_HOME':str(self.root/'state'),
                             'XDG_CONFIG_HOME':str(self.root/'stock-config'),
                             'XDG_DATA_HOME':str(self.root/'stock-data')})
        self.assertEqual(locations['config'],self.root/'state/rog-audio/easyeffects/config/easyeffects')
        stock=copy.deepcopy(self.inv);g=json.loads(stock['probes']['graph']['stdout'])
        g.append({'type':'PipeWire:Interface:Client','info':{'props':{'application.id':'com.github.wwmm.easyeffects','application.process.binary':'easyeffects'}}})
        stock['probes']['graph']['stdout']=json.dumps(g)
        kit.idle(stock)


    def test_bundle_hardware_cannot_be_relabelled_for_another_laptop(self):
        path=self.destination/'kit.json';manifest=json.loads(path.read_text())
        manifest['hardware']['subsystem']='17aa2276';manifest['binding']['subsystem']='17aa2276'
        path.write_bytes(kit.encoded(manifest))
        with self.assertRaises(kit.InstallError):kit.load_kit(self.destination)


    def test_settings_payload_uses_the_snapshot_preimage(self):
        path=self.locations['config']/'db/easyeffectsrc';path.parent.mkdir(parents=True)
        path.write_bytes(b'[Window]\npreference=old\n')
        fresh=b'[Window]\npreference=latest\n'
        original=kit.snapshot
        def edit_before_snapshot(*args):
            path.write_bytes(fresh)
            return original(*args)
        with mock.patch.object(kit,'snapshot',side_effect=edit_before_snapshot):
            kit.install(self.destination,self.snapshot,self.runtime,self.inv,self.locations)
        self.assertIn(b'preference=latest',path.read_bytes())
        self.assertEqual((self.snapshot/'before/config/db/easyeffectsrc').read_bytes(),fresh)

    def test_settings_edit_after_snapshot_aborts_without_overwriting_it(self):
        path=self.locations['config']/'db/easyeffectsrc';path.parent.mkdir(parents=True)
        path.write_bytes(b'[Window]\npreference=old\n')
        fresh=b'[Window]\npreference=latest\n'
        original=kit.snapshot
        def edit_after_snapshot(*args):
            result=original(*args);path.write_bytes(fresh);return result
        with mock.patch.object(kit,'snapshot',side_effect=edit_after_snapshot):
            with self.assertRaises(kit.InstallError) as error:
                kit.install(self.destination,self.snapshot,self.runtime,self.inv,self.locations)
        self.assertEqual(error.exception.reason,'concurrent_target_change')
        self.assertEqual(path.read_bytes(),fresh)
        self.assertEqual(json.loads((self.snapshot/'snapshot.json').read_text())['state'],'install-incomplete')

    def test_backup_sync_failure_prevents_install_and_restore_mutations(self):
        path=self.locations['config']/'db/easyeffectsrc';path.parent.mkdir(parents=True)
        before=b'[Window]\npreference=retain\n';path.write_bytes(before)
        real_sync=kit.os.fsync
        def fail_file_sync(fd):
            if stat.S_ISREG(kit.os.fstat(fd).st_mode):raise OSError('injected backup sync failure')
            return real_sync(fd)
        with mock.patch.object(kit.os,'fsync',side_effect=fail_file_sync):
            with self.assertRaises(OSError):kit.install(self.destination,self.snapshot,self.runtime,self.inv,self.locations)
        self.assertEqual(path.read_bytes(),before);self.assertFalse(self.locations['data'].exists())
        kit.install(self.destination,self.snapshot,self.runtime,self.inv,self.locations)
        installed={key:kit.tree(root) for key,root in self.locations.items()}
        with mock.patch.object(kit.os,'fsync',side_effect=fail_file_sync):
            with self.assertRaises(OSError):kit.remove(self.snapshot,self.root/'failed-archive',self.inv,self.locations)
        self.assertEqual({key:kit.tree(root) for key,root in self.locations.items()},installed)

    def test_invalid_snapshot_lifecycle_is_never_returned_by_status(self):
        kit.install(self.destination,self.snapshot,self.runtime,self.inv,self.locations)
        path=self.snapshot/'snapshot.json';original=json.loads(path.read_text())
        for value in ('/private/operator/diagnostics',{'private':'nested detail'}):
            with self.subTest(state=value):
                state=copy.deepcopy(original);state['state']=value;path.write_bytes(kit.encoded(state))
                with self.assertRaises(kit.InstallError) as error:kit.status(self.snapshot,self.locations)
                self.assertEqual(error.exception.reason,'invalid_snapshot_state')

if __name__=='__main__':unittest.main()
