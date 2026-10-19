from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from metrics import extract


class CopperMetrics(unittest.TestCase):
    def test_duplicate_uuid_occurrences_both_count(self):
        raw='''(kicad_pcb
(segment (start 0 0) (end 3 4) (width .2) (layer "F.Cu") (net "N") (uuid "duplicate"))
(segment (start 0 0) (end 0 2) (width .2) (layer "B.Cu") (net "N") (uuid "duplicate"))
(via (at 0 0) (size .7) (drill .3) (layers "F.Cu" "B.Cu") (net "N") (uuid "v")))'''
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'board';p.write_text(raw);r=extract(p,['N'])['nets']['N']
        self.assertEqual(r['segment_centerline_mm'],7)
        self.assertEqual((r['segments'],r['vias']),(2,1))
        self.assertEqual(r['by_layer_mm'],{'F.Cu':5,'B.Cu':2})
    def test_unsupported_arc_not_silently_omitted(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'board';p.write_text('(kicad_pcb (arc (net "N")))')
            with self.assertRaises(ValueError):extract(p,['N'])

if __name__=='__main__':unittest.main()
