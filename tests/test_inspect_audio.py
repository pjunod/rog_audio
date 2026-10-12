import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import inspect_audio as audio
from audio_common import load_json, write_private


def fixture():
    return {'schema_version':1,'kind':'audio-inventory','probes':{
        'graph':{'status':'ok','stdout':json.dumps([
            {'type':'PipeWire:Interface:Core','info':{'props':{'default.clock.rate':48000,'default.clock.quantum':1024,'secret':'private-host'}}},
            {'type':'PipeWire:Interface:Node','info':{'state':'suspended','props':{'media.class':'Audio/Sink','audio.channels':2,'device.api':'alsa','node.name':'private-host','node.serial':'secret','nested':{'username':'PRIVATE_SECRET'}}}},
            {'type':'PipeWire:Interface:Client','info':{'props':{'application.name':'PRIVATE_SECRET'}}}])},
        'threads':{'status':'private-host','stderr':'PRIVATE_SECRET'},
        'pipewire_version':{'status':'ok','stdout':'Compiled with libpipewire 1.6.8\nLinked with libpipewire 1.6.8'},
        'wireplumber_version':{'status':'ok','stdout':'Compiled with libwireplumber 0.5.17'}},
        'user_config':{'status':'ok','files':[]}}


class InspectorTests(unittest.TestCase):
    def test_allowlist(self):
        out=audio.public_summary(fixture(),'0'*64)
        text=json.dumps(out)
        for secret in ('private-host','PRIVATE_SECRET','username','serial','application.name'):
            self.assertNotIn(secret,text)
        self.assertEqual(out['graph_default']['graph_period_ms'],1024/48)
        self.assertIsNone(out['physical_latency_ms'])
        self.assertEqual(out['versions']['pipewire'],'1.6.8')
        self.assertEqual(out['probes']['threads'],'parse-error')

    def test_platform_and_missing_bus(self):
        runner=mock.Mock(return_value={'status':'unavailable'})
        result=audio.collect(runner,system='Darwin')
        runner.assert_not_called()
        self.assertEqual(result['collection_status'],'unsupported-platform')
        with tempfile.TemporaryDirectory() as d:
            result=audio.collect(runner,system='Linux',environment={},home=d)
        self.assertEqual(result['probes']['graph']['status'],'unavailable')
        self.assertFalse(any(call.args[0][0] in ('pw-dump','pw-metadata') for call in runner.call_args_list))
        for call in runner.call_args_list:
            self.assertNotIn('set',call.args[0])

    def test_real_bounded_runner(self):
        self.assertEqual(audio.run_command([sys.executable,'-c','import time; time.sleep(2)'],.02)['status'],'timeout')
        self.assertEqual(audio.run_command([sys.executable,'-c','print("x"*5000000)'],2)['status'],'parse-error')
        with mock.patch.object(audio.subprocess,'Popen',side_effect=FileNotFoundError):
            self.assertEqual(audio.run_command(['absent'])['status'],'unavailable')
        with mock.patch.object(audio.subprocess,'Popen',side_effect=PermissionError):
            self.assertEqual(audio.run_command(['denied'])['status'],'permission-denied')

    def test_private_io(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out'
            write_private(p,fixture())
            self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600)
            with self.assertRaises(FileExistsError):write_private(p,{})
            alias=Path(d)/'alias';alias.symlink_to(p)
            with self.assertRaises(FileExistsError):write_private(alias,{})
            fifo=Path(d)/'fifo';os.mkfifo(fifo)
            self.assertEqual(audio.file_probe(fifo)['status'],'parse-error')
            p.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):load_json(p)

    def test_malformed_graph_and_schema(self):
        for graph in ('{}','[null]','[{"info":null}]','[{"info":{"props":"PRIVATE"}}]' ,'invalid'):
            f=fixture();f['probes']['graph']['stdout']=graph
            self.assertEqual(audio.public_summary(f,'0'*64)['probes']['graph'],'parse-error')
        f=fixture();f['schema_version']=True
        with self.assertRaises(ValueError):audio.public_summary(f,'0'*64)

    def test_malformed_envelopes_fail_without_raw_payload(self):
        for key,value in (('probes',None),('probes',[]),('user_config',None)):
            f=fixture();f[key]=value
            with self.assertRaises(ValueError):audio.public_summary(f,'0'*64)
        f=fixture();f['probes']['graph']['stdout']=None
        with self.assertRaises(ValueError):audio.public_summary(f,'0'*64)

    def test_legacy_and_final_encoded_budget(self):
        with self.assertRaises(ValueError):
            audio.import_legacy({'captured_at':'x','commands':{'graph':None}})
        f=fixture();f['probes']['graph']['stdout']='\x00'*(2*1024*1024)
        f['files']={};f['kernel_log']={'status':'ok','text':'secret'}
        result=audio.bound_report(f)
        self.assertEqual(result['collection_status'],'partial')
        self.assertEqual(result['kernel_log']['status'],'parse-error')
        self.assertNotIn('secret',json.dumps(result))

    def test_configuration_entry_and_byte_budgets(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'pipewire').mkdir()
            for n in range(1025):(root/'pipewire'/str(n)).mkdir()
            self.assertEqual(audio.configs(root)['status'],'parse-error')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'pipewire').mkdir()
            for n in range(17):(root/'pipewire'/str(n)).write_text('x'*65536)
            self.assertEqual(audio.configs(root)['status'],'parse-error')

    def test_configuration_symlink_is_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'.config').mkdir();(root/'.config/pipewire').symlink_to(root)
            self.assertEqual(audio.configs(root/'.config')['status'],'parse-error')

if __name__ == '__main__':unittest.main()
