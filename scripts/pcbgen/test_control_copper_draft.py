import copy
import hashlib
import json
from pathlib import Path
import unittest

from scripts.pcbgen.control_copper_draft import validate


class ControlCopperSourceTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((Path(__file__).resolve().parents[2]/
            'design/partition/control-copper/copper.json').read_text())

    def test_current_source_has_complete_arrays(self):
        rows = validate(self.spec)
        self.assertEqual(sum(r['kind']=='segment' for r in rows),854)
        self.assertEqual(sum(r['kind']=='via' for r in rows),246)
        self.assertEqual(sum(len(a['via_uuids']) for a in self.spec['main_arrays']),150)

    def test_native_views_match_the_retained_board_and_images(self):
        root = Path(__file__).resolve().parents[2]
        receipt = json.loads((root/'design/partition/control-copper/views.json').read_text())
        self.assertEqual(hashlib.sha256((root/receipt['board']).read_bytes()).hexdigest(),receipt['board_sha256'])
        self.assertEqual(len(receipt['renders']),2)
        for render in receipt['renders']:
            self.assertEqual(hashlib.sha256((root/render['path']).read_bytes()).hexdigest(),render['sha256'])

    def test_duplicate_identity_and_wrong_class_width_rejected(self):
        for mode in ('duplicate','width','nonfinite','unknown_field'):
            spec = copy.deepcopy(self.spec)
            row = spec['copper'][0]
            if mode=='duplicate':spec['copper'].append(copy.deepcopy(row))
            if mode=='width':row['width_nm']=100000
            if mode=='nonfinite':row['start_nm'][0]=float('nan')
            if mode=='unknown_field':row['move_footprint']=True
            with self.subTest(mode=mode),self.assertRaises(ValueError):validate(spec)

    def test_array_ownership_drill_and_missing_identity_rejected(self):
        for mode in ('net','missing','drill','unlock','duplicate_owner'):
            spec = copy.deepcopy(self.spec)
            array = spec['main_arrays'][0]
            row = next(r for r in spec['copper'] if r['uuid']==array['via_uuids'][0])
            if mode=='net':row['net']='unrelated'
            if mode=='missing':array['via_uuids'].pop()
            if mode=='drill':row['drill_nm']=600000
            if mode=='unlock':row['locked']=False
            if mode=='duplicate_owner':spec['main_arrays'][1]['via_uuids'][0]=row['uuid']
            with self.subTest(mode=mode),self.assertRaises(ValueError):validate(spec)


if __name__=='__main__':unittest.main()
