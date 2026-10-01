import copy
import json
import tempfile
import unittest
from pathlib import Path
from scripts.pcbgen.generate_peripheral_ground import generate,source_contacts
from scripts.pcbgen.peripheral_project_source import derive,fresh_sync_project
from scripts.pcbgen.native_companion_binding import verify
import hashlib

BASE=Path('design/partition/peripheral-ground-feasibility')


class PeripheralGroundSourceTests(unittest.TestCase):
    def test_exact_observed_fresh_native_stage_and_foreign_rule_rejection(self):
        bid='osc-octave-1';name=bid+'-ground-prerequisite-v1.kicad_pro'
        template=Path('boards/osc-jack-left/osc-jack-left.kicad_pro').read_bytes()
        final,_=derive(template,Path('boards',bid,bid+'.kicad_pro').read_bytes(),(BASE/(bid+'.json')).read_bytes(),name)
        intermediate=fresh_sync_project(final,template)
        # Exact actual failed-v1 bytes are evidence of the narrow native stage,
        # not a source for choosing the expected value.
        self.assertEqual(intermediate,Path('boards',bid,name).read_bytes())
        self.assertNotEqual(final,intermediate)
        bad_template=json.loads(template)
        next(c for c in bad_template['net_settings']['classes'] if c['name']=='Default')['line_style']=1
        with self.assertRaisesRegex(ValueError,'pinned constructor'):
            fresh_sync_project(final,json.dumps(bad_template).encode())
        with tempfile.TemporaryDirectory() as folder:
            stem=Path(folder)/'candidate';expected={}
            for suffix,data in [('.kicad_pro',intermediate),('.kicad_sch',b'source schematic'),('.kicad_dru',b'(version 1)\n')]:
                path=stem.with_suffix(suffix);path.write_bytes(data);expected[str(path)]=hashlib.sha256(data).hexdigest()
            verify(expected)
            changed=json.loads(intermediate);changed['board']['design_settings']['rules']['min_copper_edge_clearance']=.4
            stem.with_suffix('.kicad_pro').write_text(json.dumps(changed,indent=2,sort_keys=True)+'\n')
            with self.assertRaisesRegex(ValueError,'changed from retained'):verify(expected)


if __name__ == '__main__':
    unittest.main()
