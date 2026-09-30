"""Host-side validation of optional placement region definitions."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts.pcbgen.definition import load_definition

ROOT=Path(__file__).resolve().parents[2]

class RegionDefinitionTest(unittest.TestCase):
    def test_existing_definition_without_regions(self):
        self.assertEqual(load_definition(ROOT/'design/boards/fixture-jacks.json').regions,())

    def test_placement_fixtures_have_valid_regions(self):
        for case,count in (('one',1),('six',6),('island',1),('overflow',1)):
            with self.subTest(case=case):
                definition=load_definition(ROOT/'design/boards'/f'fixture-place-{case}.json')
                self.assertEqual(len(definition.regions),count)
                self.assertEqual({r['side'] for r in definition.regions},{'B.Cu'})

    def test_invalid_region_rejected(self):
        original=json.loads((ROOT/'design/boards/fixture-place-one.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fixture-place-one.json'
            for change in ({'rect':[7,43,7,76]},{'side':'Internal.Cu'},{'edge_clearance_mm':-1}):
                data=json.loads(json.dumps(original));data['regions'][0].update(change)
                path.write_text(json.dumps(data))
                with self.subTest(change=change),self.assertRaises(ValueError):load_definition(path)

if __name__=='__main__':unittest.main()
