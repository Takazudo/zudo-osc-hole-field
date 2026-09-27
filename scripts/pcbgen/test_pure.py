"""Pure Python tests for board contracts and UUID ownership boundaries."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware
from scripts.pcbgen.geometry import outline_segments
from scripts.pcbgen.uuid_tools import stable_uuid,top_level_spans,normalize

ROOT=Path(__file__).resolve().parents[2]

class DefinitionTests(unittest.TestCase):
    def test_fixture_definition_and_fixed_coordinates(self):
        d=load_definition(ROOT/'design/boards/fixture-jacks.json')
        selected=selected_hardware(d,load_lock(ROOT/'design/grid/placements.lock.json'))
        self.assertEqual(len(selected),10)
        self.assertEqual([p['ref'] for p in selected],[f'J{n}' for n in range(101,111)])
        self.assertEqual([(p['x_mm'],p['y_mm']) for p in selected],[(14.5,29+14*n) for n in range(10)])

    def test_rejects_bad_definition_and_forged_uid(self):
        source=json.loads((ROOT/'design/boards/fixture-jacks.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'fixture-jacks.json'
            for change in ({'corner_radius_mm':-1},{'outline':[[0,0],[0,0],[1,1]]},{'layers':3},{'netlist':'../outside.net'}):
                trial={**source,**change};path.write_text(json.dumps(trial))
                with self.assertRaises(ValueError):load_definition(path)
        d=load_definition(ROOT/'design/boards/fixture-jacks.json')
        with self.assertRaises(ValueError):selected_hardware(d,{'not-a-uid':{}})

class GeometryTests(unittest.TestCase):
    def test_square_with_radius(self):
        pieces=outline_segments(((0,0),(20,0),(20,10),(0,10)),1)
        self.assertEqual(len(pieces),8)
        self.assertEqual(sum(p[0]=='arc' for p in pieces),4)
        with self.assertRaises(ValueError):outline_segments(((0,0),(20,0),(20,10),(0,10)),6)

class UUIDTests(unittest.TestCase):
    def test_stable_domain_separated_uuid(self):
        self.assertEqual(stable_uuid('b','footprint:J101','root'),stable_uuid('b','footprint:J101','root'))
        self.assertNotEqual(stable_uuid('b','footprint:J101','root'),stable_uuid('b','outline','J101'))
        with self.assertRaises(ValueError):stable_uuid('','item','key')

    def test_new_board_without_board_uuid_preserves_first_footprint_owner(self):
        board='(kicad_pcb (paper "A4") (footprint "x" (uuid "22222222-2222-4222-8222-222222222222") (property "Reference" "C106")))'
        out=normalize(board,'b',{'C106'},{},True)
        self.assertIn(stable_uuid('b','footprint:C106','root'),out)
        self.assertNotIn(stable_uuid('b','board','root'),out)

    def test_normalize_only_owned_objects(self):
        board='(kicad_pcb (paper "A4") (uuid "11111111-1111-4111-8111-111111111111")\n(footprint "x" (uuid "22222222-2222-4222-8222-222222222222") (property "Reference" "J101") (pad "1" (uuid "33333333-3333-4333-8333-333333333333")))\n(segment (uuid "44444444-4444-4444-8444-444444444444"))\n(gr_text "owner (silk)" (uuid "55555555-5555-4555-8555-555555555555"))\n)'
        out=normalize(board,'b',{'J101'},{},True)
        self.assertIn(stable_uuid('b','footprint:J101','root'),out)
        self.assertIn('44444444-4444-4444-8444-444444444444',out)
        self.assertIn('55555555-5555-4555-8555-555555555555',out)
        self.assertEqual(normalize(out,'b',{'J101'},{},False),out)
        self.assertEqual(len(list(top_level_spans(out))),5)
        self.assertIn('(paper "A2")',out)

if __name__=='__main__':unittest.main()
