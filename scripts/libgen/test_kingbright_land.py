import copy
import json
import unittest
from pathlib import Path
from gen_kingbright_land import derive, outputs, ROOT, SPEC, FOOTPRINT


class KingbrightLandTest(unittest.TestCase):
    def test_exact_two_pad_delta(self):
        spec=json.loads(SPEC.read_bytes());original=(ROOT/spec['original_footprint']).read_bytes()
        result=derive(original,spec)
        reverted=result.replace(b'(at -0.475 0) (size 0.65 0.5)',b'(at -0.45 0) (size 0.7 0.5)').replace(b'(at 0.475 0) (size 0.65 0.5)',b'(at 0.45 0) (size 0.7 0.5)')
        self.assertEqual(reverted,original)
        self.assertEqual(result,outputs()[ROOT/FOOTPRINT])
        for key,value in [('gap',.35),('required_design_clearance',.2),('height',.55),('centre_x_magnitude',.48)]:
            bad=copy.deepcopy(spec);bad['project_mm'][key]=value
            with self.assertRaises(ValueError):derive(original,bad)
        with self.assertRaises(ValueError):derive(original.replace(b'F.SilkS',b'B.SilkS'),spec)

    def test_all_104_fixed_source_instances(self):
        io=json.loads((ROOT/'design/reports/io-partition.json').read_bytes());part=json.loads((ROOT/'design/partition/partition.json').read_bytes())
        assignment={r['ref']:r['board'] for r in part['assignment']['components']}
        rows=[p for p in io['physical_packages'] if p['footprint']=='zudo-osc-hole-field:LED0402-Kingbright-White' and not p['dnp']]
        from collections import Counter
        self.assertEqual(Counter(assignment[r['ref']] for r in rows),{'JL':41,'JR':51,'EL':12})
        self.assertEqual(len({r['panel_uid'] for r in rows}),104)


if __name__=='__main__':unittest.main()
