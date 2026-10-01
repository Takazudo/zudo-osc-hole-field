"""Only independently other-board and natively absent rule deltas may differ."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.pcbgen.replay_equivalence import compare, verify_export_provenance


class ReplayEquivalenceTests(unittest.TestCase):
    def test_cached_export_requires_exact_board_project_and_extractor(self):
        with tempfile.TemporaryDirectory() as directory:
            paths=[Path(directory)/name for name in ('board','project','extractor')]
            keys=('board_sha256','project_sha256','extractor_sha256')
            data={'board_id':'right'}
            for path,key in zip(paths,keys):
                path.write_text(path.name)
                data[key]=hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(verify_export_provenance(data,'right',*paths),
                             {key:data[key] for key in keys})
            for key in (*keys,'board_id'):
                stale=dict(data);stale[key]='stale'
                with self.subTest(stale=key),self.assertRaisesRegex(ValueError,'mismatch'):
                    verify_export_provenance(stale,'right',*paths)
            for path in paths:
                original=path.read_bytes();path.write_bytes(original+b' changed')
                with self.subTest(changed=path.name),self.assertRaisesRegex(ValueError,'mismatch'):
                    verify_export_provenance(data,'right',*paths)
                path.write_bytes(original)

    def setUp(self):
        self.partition={'boards':[{'id':'right','board_key':'JR'}],
            'assignment':{'components':[{'ref':'Rleft','board':'JL'}, {'ref':'Rright','board':'JR'}]}}
        self.native={'board_id':'right','outline_mm':[[0,0],[2,0],[2,2]],'coordinate_frame':{},
            'native_project_rules':{'clearance':.25},'stackup':[],'main_rail_members':{},
            'items':[{'uuid':'right-pad','ref':'Rright'}],'holes':[],'zones':[],'clusters':[],
            'routing':{'local_escape_overrides':[{'ref':r,'pad':'1','net':'+5V','width_mm':.25} for r in ('Rleft','Rright')]}}

    def test_proven_other_board_delta_is_explicitly_retained(self):
        replay=copy.deepcopy(self.native);replay['routing']['local_escape_overrides'][0]['width_mm']=.2
        delta=compare(self.native,replay,self.partition)
        self.assertEqual(len(delta),1)
        self.assertEqual(delta[0]['before']['override']['width_mm'],.25)
        self.assertEqual(delta[0]['after']['override']['width_mm'],.2)
        self.assertTrue(delta[0]['after']['native_reference_absent'])

    def test_applicable_override_misassignment_and_geometry_fail(self):
        for defect in ('applicable','misassigned','geometry'):
            replay=copy.deepcopy(self.native)
            if defect=='applicable':replay['routing']['local_escape_overrides'][1]['width_mm']=.2
            elif defect=='misassigned':replay['items'].append({'uuid':'wrong','ref':'Rleft'})
            else:replay['outline_mm'][1][0]=3
            with self.subTest(defect=defect), self.assertRaises(ValueError):compare(self.native,replay,self.partition)


if __name__=='__main__':unittest.main()
