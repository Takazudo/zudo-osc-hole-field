"""PTH wall/face identity, missing material and source-drift negatives."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.pcbgen.pth_source_geometry import certify,run,ROOT,native_physical_stack


class PTHSourceGeometryTest(unittest.TestCase):
    def fixture(self):
        layers=['F.Cu','In1.Cu','In2.Cu','B.Cu']
        p={'kind':'circle','centre_nm':[0,0],'half_size_nm':[850000,850000],'corner_radius_nm':0,'quarter_turns':0}
        pad={'ref':'RV1','pad':'1','uuid':'pth','net':'AGND','copper':{l:[] for l in layers},'analytic_primitives':{l:dict(p) for l in layers}}
        hole={'uuid':'pth','net':'AGND','plated':True,'xy_mm':[0,0],'size_mm':[1,1],'copper_layers':layers}
        raw=('RV1','(pad "1" thru_hole circle (drill 1) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (net "AGND") (uuid "pth"))')
        stack={'depth_nm':1600000,'enabled_layers':layers,'bands':[{'layer':l,'z_nm':[z,z+70000],'thickness_nm':70000} for l,z in zip(layers,[0,130000,1400000,1530000])]}
        outline=[(-2000000,-2000000),(2000000,-2000000),(2000000,2000000),(-2000000,2000000)]
        return pad,hole,raw,stack,[hole],outline

    def test_actual_native_drift_rejects_without_output(self):
        base=ROOT/'.circuit-cache/issue38-recovery'
        args=[base/'own-source-flux-boundaries-v2.json',base/'single-drill-cover-certificate-v2.json',base/'multi-drill-cover-certificate-v2.json']
        original=Path.read_bytes;target=ROOT/'boards/osc-jack-left/osc-jack-left-parallel-feeds.kicad_pcb'
        def changed(path):
            data=original(path)
            return data+b'\n' if path.resolve()==target else data
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'receipt.json'
            with patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(ValueError,'dependency drift'):
                run(*args,output)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
