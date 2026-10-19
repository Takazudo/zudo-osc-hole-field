import copy
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from verify_power import validate_manifest, EXPECTED


def manifest():
    rows=[]
    for role,source,target,net,plane in EXPECTED:
        r={'role':role,'from_pad':source,'net':net}
        if target:r['to_pad']=target
        if plane:r.update(plane=plane,via_mm=[1,2])
        rows.append(r)
    return rows


class PowerManifest(unittest.TestCase):
    def test_exact_six(self):validate_manifest(manifest())
    def test_empty_missing_duplicate_rejected(self):
        rows=manifest()
        for bad in ([],rows[:-1],rows+[rows[0]],rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError):validate_manifest(bad)
    def test_wrong_return_or_plane_rejected(self):
        for field,value in [('plane','In4.Cu'),('from_pad','C3107:1'),('net','+12V')]:
            rows=manifest();rows[-1][field]=value
            with self.assertRaises(ValueError):validate_manifest(rows)
    def test_geometry_role_rejected(self):
        rows=manifest();rows[0]['via_mm']=[1,2]
        with self.assertRaises(ValueError):validate_manifest(rows)

if __name__=='__main__':unittest.main()
