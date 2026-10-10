import hashlib,json,subprocess,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from scripts.pcbgen.zone_fixture_validation import native_fixture_check,isolated_fixture_check,worker

class FixtureValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.fixture=Path(self.tmp.name)/'osc-core.kicad_pcb';self.fixture.write_text('fixture')
        for suffix in ('.kicad_pro','.kicad_dru'):self.fixture.with_suffix(suffix).write_text(suffix)
        poly=SimpleNamespace(ArcCount=lambda:0,Format=lambda:'exact shape')
        uid=lambda v:SimpleNamespace(AsString=lambda:v)
        text=SimpleNamespace(m_Uuid=uid('text'),GetShownText=lambda enabled:'rendered')
        fp=SimpleNamespace(m_Uuid=uid('art'),Pads=lambda:[],GetFields=lambda:[text],GraphicalItems=lambda:[])
        zone=SimpleNamespace(m_Uuid=uid('zone'),GetFilledPolysList=lambda layer:poly)
        self.board=SimpleNamespace(Zones=lambda:[zone],GetTracks=lambda:[],GetFootprints=lambda:[fp],GetDrawings=lambda:[])
        self.native=SimpleNamespace(LoadBoard=lambda path:self.board,Edge_Cuts=44)
        self.shape=hashlib.sha256(b'exact shape').hexdigest()
    def validate(self):
        return native_fixture_check(self.fixture,'zone',0,['art'],{'text':'rendered'},self.shape,self.native)
    def test_original_native_geometry_scope_and_rendering_pass(self):
        self.assertEqual(self.validate(),self.shape)
    def test_track_pad_uuid_rendering_and_shape_mutations_fail_closed(self):
        mutations=[('GetTracks',lambda:['track']),('GetFootprints',lambda:[SimpleNamespace(m_Uuid=SimpleNamespace(AsString=lambda:'art'),Pads=lambda:['pad'])]),('GetDrawings',lambda:[SimpleNamespace(m_Uuid=SimpleNamespace(AsString=lambda:'art'),GetLayer=lambda:0)])]
        for name,value in mutations:
            old=getattr(self.board,name);setattr(self.board,name,value)
            with self.assertRaises(ValueError):self.validate()
            setattr(self.board,name,old)
        with self.assertRaisesRegex(ValueError,'rendered'):native_fixture_check(self.fixture,'zone',0,['art'],{'text':'different'},self.shape,self.native)
        with self.assertRaisesRegex(ValueError,'shape'):native_fixture_check(self.fixture,'zone',0,['art'],{'text':'rendered'},'wrong',self.native)
    def fake_child(self,args,**kwargs):
        request=json.loads(Path(args[-1]).read_text());self.assertEqual(request['version'],'10.0.6');self.assertEqual(request['item_uids'],['art'])
        return SimpleNamespace(stdout=json.dumps({k:request[k] for k in ('version','fixture_sha256','context_sha256')}|{'native_geometry_sha256':self.shape}))
    def test_each_fixture_uses_a_fresh_child_and_bound_request(self):
        with patch('scripts.pcbgen.zone_fixture_validation.subprocess.run',side_effect=self.fake_child) as call:
            for _ in range(2):self.assertEqual(isolated_fixture_check(self.fixture,'zone',0,['art'],{'text':'rendered'},self.shape),self.shape)
            self.assertEqual(call.call_count,2)
            self.assertTrue(all(c.kwargs['check'] for c in call.call_args_list))
    def test_failed_or_invalid_child_never_produces_validation_success(self):
        for child in (subprocess.CalledProcessError(137,['worker']),SimpleNamespace(stdout='{}')):
            with patch('scripts.pcbgen.zone_fixture_validation.subprocess.run',side_effect=child if isinstance(child,Exception) else None,return_value=child):
                with self.assertRaises((subprocess.CalledProcessError,ValueError)):
                    isolated_fixture_check(self.fixture,'zone',0,['art'],{'text':'rendered'},self.shape)
    def test_worker_refuses_changed_fixture_context_and_native_version(self):
        with patch('scripts.pcbgen.zone_fixture_validation.subprocess.run',side_effect=self.fake_child):isolated_fixture_check(self.fixture,'zone',0,['art'],{'text':'rendered'},self.shape)
        request=self.fixture.parent/'native-validation-request.json'
        with self.assertRaisesRegex(ValueError,'version'):worker(request,self.native,'10.0.5')
        self.fixture.with_suffix('.kicad_pro').write_text('changed')
        with self.assertRaisesRegex(ValueError,'context'):worker(request,self.native,'10.0.6')

if __name__=='__main__':unittest.main()
