"""Full-B1 power receipts cannot accept only the old output-loop subset."""
import copy
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace as NS

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('full_b1_power', ROOT/'design/architecture-278/implementation/stage42/full-b1/verify_power.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def paths():
    rows=[]
    for role,src,dst,net,plane in m.EXPECTED:
        r={'role':role,'from_pad':src,'net':net}
        if dst:r['to_pad']=dst
        if plane:r.update(plane=plane,via_mm=[0,0])
        rows.append(r)
    return rows


class FullB1Power(unittest.TestCase):
    def test_all_six_bypasses_required(self):
        rows=paths();self.assertEqual(len(rows),18);m.validate_manifest(rows)
        self.assertEqual(len({r['from_pad'].split(':')[0] for r in rows if r['role']=='bypass ground return'}),6)

    def test_stage41_subset_rejected(self):
        with self.assertRaises(ValueError):m.validate_manifest(paths()[:6])

    def test_missing_duplicate_or_extra_rejected(self):
        rows=paths()
        for wrong in (rows[:-1],rows+[rows[0]],rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError):m.validate_manifest(wrong)

    def test_wrong_pin_or_plane_rejected(self):
        for key,value in [('from_pad','U3101:4'),('net','+5V'),('plane','In2.Cu')]:
            rows=paths();rows[0][key]=value
            with self.assertRaises(ValueError):m.validate_manifest(rows)

    def test_wrong_geometry_kind_rejected(self):
        rows=paths();rows[0]['via_mm']=[0,0]
        with self.assertRaises(ValueError):m.validate_manifest(rows)

    def test_rear_pad_uses_parent_face_not_legacy_pad_layer(self):
        board=NS(GetLayerName=lambda layer:{0:'F.Cu',2:'B.Cu'}[layer])
        pad=NS(GetLayer=lambda:0,GetParentFootprint=lambda:NS(GetLayer=lambda:2),IsOnLayer=lambda layer:layer==2)
        self.assertEqual(m.pad_face(board,pad),'B.Cu')
        pad.IsOnLayer=lambda layer:False
        with self.assertRaises(ValueError):m.pad_face(board,pad)
