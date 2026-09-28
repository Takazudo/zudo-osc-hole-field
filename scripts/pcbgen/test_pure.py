"""Pure Python tests for board contracts and UUID ownership boundaries."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware
from scripts.pcbgen.geometry import outline_segments
from scripts.pcbgen.netlist import Component,is_abstract_boundary,read_netlist
from scripts.pcbgen.uuid_tools import stable_uuid,top_level_spans,normalize

ROOT=Path(__file__).resolve().parents[2]

class AbstractBoundaryTests(unittest.TestCase):
    def test_netlisted_requirement_is_not_a_board_part(self):
        fields=(('AbstractBoundary','true'),('Implementation','REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE'),('MPN',''))
        abstract=Component('CN301','REQUIREMENT ONLY','','/POWER','/x','x',fields)
        self.assertTrue(is_abstract_boundary(abstract))
        with self.assertRaisesRegex(ValueError,'malformed abstract boundary'):
            is_abstract_boundary(Component('CN301','REQUIREMENT ONLY','vendor:guessed','/POWER','/x','x',fields))
        with self.assertRaisesRegex(ValueError,'malformed abstract boundary'):
            is_abstract_boundary(Component('J101','jack','','/POWER','/x','x',fields))
        with self.assertRaisesRegex(ValueError,'unmarked footprintless power boundary'):
            is_abstract_boundary(Component('CN301','unknown','','/POWER','/x','x',()))

    def test_board_reader_removes_abstract_pin_nodes(self):
        sample='''(export (components
          (comp (ref "CN301") (value "REQUIREMENT ONLY")
            (sheetpath (names "/POWER") (tstamps "/x")) (tstamps "a")
            (property (name "AbstractBoundary") (value "true"))
            (property (name "Implementation") (value "REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE"))
            (property (name "MPN")))
          (comp (ref "R301") (value "2.2k") (footprint "zudo:r")
            (sheetpath (names "/POWER") (tstamps "/x")) (tstamps "b")))
          (nets (net (name "+12V_IN") (node (ref "CN301") (pin "1")))
                (net (name "+12V") (node (ref "R301") (pin "1")))))'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'native.net';path.write_text(sample)
            components,nets=read_netlist(path)
            self.assertEqual([c.ref for c in components],['R301'])
            self.assertNotIn(('CN301','1'),nets)
            self.assertEqual(nets[('R301','1')],'+12V')
            native,_=read_netlist(path,include_abstract=True)
            self.assertEqual({c.ref for c in native},{'CN301','R301'})

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
