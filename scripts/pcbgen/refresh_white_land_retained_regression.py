import json
from pathlib import Path
import unittest
from scripts.pcbgen.refresh_white_land import refresh

ROOT=Path(__file__).resolve().parents[2]


class RefreshWhiteLandTest(unittest.TestCase):
    def test_all_actual_native_copies_and_negatives(self):
        partition=json.loads((ROOT/'design/partition/partition.json').read_bytes());io=json.loads((ROOT/'design/reports/io-partition.json').read_bytes());spec=json.loads((ROOT/'design/mechanical/kingbright-white-land.json').read_bytes());original=(ROOT/spec['original_footprint']).read_bytes()
        for board,path,count in [('osc-jack-left','boards/osc-jack-left/osc-jack-left.kicad_pcb',41),('osc-jack-right','boards/osc-jack-right/osc-jack-right.kicad_pcb',51),('osc-stage-optical','boards/osc-stage-optical/osc-stage-optical-bare-prerequisite-v1.kicad_pcb',12)]:
            text=(ROOT/path).read_text();new,receipt=refresh(text,board,partition,io,spec,original)
            self.assertEqual(len(receipt['footprints']),count)
            # No old footprint had these revised fields; reversing only the
            # declared two fields reconstructs EVERY byte of the original.
            self.assertEqual(new.replace('(at -0.475 0)','(at -0.45 0)').replace('(at 0.475 0)','(at 0.45 0)').replace('(size 0.65 0.5)','(size 0.7 0.5)'),text)
            with self.assertRaises(ValueError):refresh(new,board,partition,io,spec,original)
        wrong=text.replace('(size 0.7 0.5)','(size 0.69 0.5)',1)
        with self.assertRaises(ValueError):refresh(wrong,board,partition,io,spec,original)


if __name__=='__main__':unittest.main()
