import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import stage16_handoff as m
class Handoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inp=json.loads((m.OUT/'inputs-report.json').read_text())
    def obs(self):
        return {'oracle_version':'10.0.6','candidate_input_sha256':m.common.digest(m.OUT/'inputs-report.json'),'kind':'schematic_pin_net_observation','artifact_sha256':'a'*64,'packages':{ref:{'pins':copy.deepcopy(p['pins']),'selected_mpn':p['selected_mpn']} for ref,p in self.inp['packages'].items()}}
    def test_comparison_never_attests_execution(self):
        r=m.compare_observation(self.obs(),self.inp)
        self.assertFalse(r['provenance_verified']);self.assertFalse(r['native_execution_authorized']);self.assertFalse(r['hardware_acceptance'])
    def test_wrong_pad_net_rejected(self):
        o=self.obs();o['packages']['RN7101']['pins']['9']='WRONG'
        with self.assertRaises(ValueError):m.compare_observation(o,self.inp)
    def test_missing_nc_pin_rejected(self):
        o=self.obs();del o['packages']['RN7102']['pins']['3']
        with self.assertRaises(ValueError):m.compare_observation(o,self.inp)
    def test_version_and_input_binding_rejected(self):
        for key,val in [('oracle_version','10.0.5'),('candidate_input_sha256','0'*64)]:
            o=self.obs();o[key]=val
            with self.assertRaises(ValueError):m.compare_observation(o,self.inp)
    def test_no_path_escape(self):
        for value in ('../canonical','a/b','/tmp/x',''):
            with self.assertRaises(ValueError):m.run_path(value)
        with self.assertRaises(ValueError):m.safe_source('../outside')
    def test_export_roundtrip_and_no_overwrite(self):
        # Keep real source manifest/artifacts; redirect only export directory to disposable local state.
        with tempfile.TemporaryDirectory() as t,patch.object(m,'run_path',return_value=Path(t)/'run'):
            m.export_run('unit');m.verify_export('unit')
            with self.assertRaises(FileExistsError):m.export_run('unit')
            p=Path(t)/'run/manifest.json';r=json.loads(p.read_text());r['files'].pop('bom.csv');p.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'inventory'):m.verify_export('unit')
    def test_export_payload_cannot_be_rehashed_to_hide_change(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,'run_path',return_value=Path(t)/'run'):
            dest=m.export_run('unit');p=dest/'candidate.json';r=json.loads(p.read_text());r['packages'].pop('RN7101');p.write_text(json.dumps(r))
            q=dest/'manifest.json';r=json.loads(q.read_text());r['files']['candidate.json']=m.common.digest(p);q.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'payload'):m.verify_export('unit')
if __name__=='__main__':unittest.main()
