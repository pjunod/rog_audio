"""Focused container orchestration contracts; no engine, network or audio access."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_easyeffects_runtime as build

class RuntimeBuildTests(unittest.TestCase):
    def fixture(self,engine='podman',change=None,compile_failure=False,timeout=False):
        temporary=tempfile.TemporaryDirectory(prefix='rog-build-contract-')
        self.addCleanup(temporary.cleanup)
        parent=Path(temporary.name);output=parent/'artifact'
        binary=b'compiled native binary';deb=b'packaged native binary'
        manifest={'binary_sha256':build.sha(binary),'package':build.package.PACKAGE+'_'+build.package.VERSION+'_amd64.deb',
                  'package_version':build.package.VERSION,'package_sha256':build.sha(deb),
                  'source_manifest_sha256':build.sha((build.ROOT/'patches/easyeffects/source.json').read_bytes()),
                  'programme_loudness_contract':'bounded-programme-makeup-v1',
                  'stop_contract':'owned-synchronous-exit-v1',
                  'stop_helper_sha256':build.sha((build.ROOT/'scripts/stop_speaker_effects.py').read_bytes()),
                  'stop_helper_license_sha256':build.sha((build.ROOT/'LICENSE').read_bytes())}
        if change:manifest.update(change)
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w') as tar:
            for name,data in ((build.package.PACKAGE+'_'+build.package.VERSION+'_amd64.deb',deb),
                              ('runtime.json',json.dumps(manifest).encode())):
                member=tarfile.TarInfo(name);member.size=len(data);tar.addfile(member,io.BytesIO(data))
        calls=[];contexts=[];self.build_environments=[]
        def stage(source,destination):
            self.assertEqual(source,parent/'public-git')
            destination.mkdir();(destination/'LICENSE').write_text('Retained source licence')
            return destination
        def execute(argv,**kwargs):
            calls.append(argv)
            if argv[1:3]==['image','inspect']:return subprocess.CompletedProcess(argv,1,b'',b'')
            if argv[1]=='build':
                self.build_environments.append(kwargs.get('env'))
                contexts.append(Path(argv[-1]))
                self.assertEqual(contexts[-1].parent,output)
                self.assertTrue((contexts[-1]/'easyeffects/LICENSE').exists())
                self.assertFalse((contexts[-1]/'easyeffects/.git').exists())
                if timeout:raise subprocess.TimeoutExpired(argv,1800,output=b'partial compile',stderr=b'compiler timeout')
                return subprocess.CompletedProcess(argv,1 if compile_failure else 0,b'compiler log',b'')
            return subprocess.CompletedProcess(argv,0,b'',b'')
        def export(argv,**kwargs):
            calls.append(argv)
            if argv[1]=='create':return b'owned-export-id\n'
            if argv[1]=='cp':
                destination=Path(argv[-1]);(destination/'bin').mkdir(parents=True)
                (destination/'bin/easyeffects').write_bytes(binary);return b''
            if argv[1]=='run':
                helper=(build.ROOT/'scripts/stop_speaker_effects.py').read_bytes()
                self.assertIn(helper.hex().encode(), kwargs['input'])
                self.assertIn((build.ROOT/'LICENSE').read_bytes().hex().encode(),kwargs['input'])
                return stream.getvalue()
            raise AssertionError(argv)
        with patch.object(build,'source_snapshot',side_effect=stage),patch.object(build.subprocess,'run',side_effect=execute),patch.object(build,'run',side_effect=export):
            try:result=build.build(parent/'public-git',output,'owned-candidate',engine)
            except build.BuildError as error:result=error
        self.assertTrue((output/'source/LICENSE').exists())
        self.assertTrue(all(not directory.exists() for directory in contexts))
        self.assertFalse(any(output.glob('rog-ee-context-*')))
        return output,result,calls

    def test_podman_native_build_and_export_are_bounded_and_durable(self):
        output,result,calls=self.fixture()
        self.assertEqual(self.build_environments,[None])
        self.assertEqual(result['status'],'runtime-built')
        command=next(c for c in calls if c[1]=='build')
        self.assertEqual(command[command.index('--cpu-quota')+1],'200000')
        self.assertEqual(command[command.index('--cpu-period')+1],'100000')
        self.assertEqual(command[command.index('--memory')+1],'6g')
        self.assertEqual(command[command.index('--memory-swap')+1],'6g')
        self.assertEqual(command[command.index('--jobs')+1],'1')
        for action in ('create','run'):
            command=next(c for c in calls if c[1]==action)
            self.assertEqual(command[command.index('--network')+1],'none')
            self.assertEqual(command[command.index('--cpus')+1],'2')
            self.assertEqual(command[command.index('--memory')+1],'6g')
            self.assertEqual(command[command.index('--pids-limit')+1],'2048')
        self.assertIn(['podman','rm','owned-export-id'],calls)
        self.assertTrue((output/'patches/ubuntu/COPYRIGHT').exists())
        self.assertTrue((output/'source-manifest.json').exists())

    def test_docker_uses_the_same_bounds_without_podman_jobs(self):
        with patch.dict(build.os.environ,{'DOCKER_BUILDKIT':'1','ROG_BUILD_SENTINEL':'retain'}):
            _,result,calls=self.fixture(engine='docker')
            self.assertEqual(build.os.environ['DOCKER_BUILDKIT'],'1')
        self.assertEqual(self.build_environments[0]['DOCKER_BUILDKIT'],'0')
        self.assertEqual(self.build_environments[0]['ROG_BUILD_SENTINEL'],'retain')
        self.assertEqual(result['status'],'runtime-built')
        self.assertNotIn('--jobs',next(c for c in calls if c[1]=='build'))
        self.assertTrue(all(c[0]=='docker' for c in calls))

    def test_existing_image_is_a_conflict_without_creating_output(self):
        with tempfile.TemporaryDirectory(prefix='rog-build-conflict-') as directory:
            output=Path(directory)/'new'
            with patch.object(build.subprocess,'run',return_value=subprocess.CompletedProcess([],0)):
                with self.assertRaisesRegex(build.BuildError,'image_tag_exists'):build.build('unused',output,'existing','podman')
            self.assertFalse(output.exists())

    def test_unknown_engine_cannot_execute_or_create_output(self):
        with tempfile.TemporaryDirectory(prefix='rog-build-engine-') as directory:
            output=Path(directory)/'new'
            with patch.object(build.subprocess,'run') as execute:
                with self.assertRaisesRegex(build.BuildError,'unsupported_container_engine'):build.build('unused',output,engine='shell')
                execute.assert_not_called()
            self.assertFalse(output.exists())

    def test_failed_compile_retains_source_log_and_cleans_only_owned_context(self):
        output,result,calls=self.fixture(compile_failure=True)
        self.assertEqual(str(result),'compiler_build_failed')
        self.assertEqual((output/'build.log').read_bytes(),b'compiler log')
        self.assertFalse(any(c[1] in ('create','run','rm') for c in calls))

    def test_compile_timeout_retains_partial_diagnostics(self):
        output,result,_=self.fixture(timeout=True)
        self.assertEqual(str(result),'compiler_build_timed_out')
        self.assertEqual((output/'build.log').read_bytes(),b'partial compilecompiler timeout')

    def test_exported_binary_mismatch_fails_and_removes_owned_container(self):
        _,result,calls=self.fixture(change={'binary_sha256':'0'*64})
        self.assertEqual(str(result),'exported_binary_mismatch')
        self.assertIn(['podman','rm','owned-export-id'],calls)

    def test_exported_package_mismatch_fails(self):
        _,result,_=self.fixture(change={'package_sha256':'0'*64})
        self.assertEqual(str(result),'exported_package_mismatch')

    def test_exported_old_package_version_fails(self):
        _,result,_=self.fixture(change={'package_version':'8.2.8+rog1'})
        self.assertEqual(str(result),'exported_package_version_mismatch')

    def test_exported_source_manifest_mismatch_fails(self):
        _,result,_=self.fixture(change={'source_manifest_sha256':'0'*64})
        self.assertEqual(str(result),'exported_source_manifest_mismatch')

    def test_exported_programme_contract_mismatch_fails(self):
        _,result,calls=self.fixture(change={'programme_loudness_contract':None})
        self.assertEqual(str(result),'exported_programme_contract_mismatch')
        self.assertIn(['podman','rm','owned-export-id'],calls)

    def test_exported_stop_contract_mismatch_fails(self):
        _,result,calls=self.fixture(change={'stop_contract':None})
        self.assertEqual(str(result),'exported_stop_contract_mismatch')
        self.assertIn(['podman','rm','owned-export-id'],calls)

    def test_exported_stop_helper_bytes_mismatch_fails(self):
        for field in ('stop_helper_sha256','stop_helper_license_sha256'):
            with self.subTest(field=field):
                _,result,_=self.fixture(change={field:'0'*64})
                self.assertEqual(str(result),'exported_stop_contract_mismatch')
