"""Host-side router configuration and report contract checks."""
import json,tempfile,unittest
from pathlib import Path
from scripts.pcbgen.definition import load_definition
from scripts.pcbgen.route import read_env,memory_mb,unrouted_names

ROOT=Path(__file__).resolve().parents[2]
class RouterContractTest(unittest.TestCase):
    def test_fixture_layer_and_zone_contract(self):
        for case,layers,zone_layers in (('one',2,{'F.Cu','B.Cu'}),('six',2,{'F.Cu'}),('four',4,{'In1.Cu','In2.Cu'}),('dense',4,{'In1.Cu','In2.Cu'})):
            with self.subTest(case=case):
                d=load_definition(ROOT/'design/boards'/f'fixture-route-{case}.json')
                self.assertEqual(d.layers,layers)
                self.assertEqual({l for z in d.routing['zones'] for l in z['layers']},zone_layers)
                self.assertTrue(all(c['track_width_mm']>d.routing['min_track_width_mm'] for c in d.routing['net_classes']))
                classes={c['name']:c for c in d.routing['net_classes']}
                self.assertTrue({'+12V','-12V','+5V'}.issubset(classes['Rails']['nets']))
                self.assertGreater(classes['Rails']['track_width_mm'],classes['Default']['track_width_mm'])
                self.assertGreater(classes['Ground']['track_width_mm'],classes['Default']['track_width_mm'])
    def test_digest_pin_and_memory_unit(self):
        image,heap,timeout=read_env()
        self.assertIn('@sha256:',image)
        self.assertEqual(heap,2048)
        self.assertEqual(memory_mb('0.5GiB / 3GiB'),512)
    def test_unrouted_names_from_kicad_descriptions(self):
        data={'unconnected_items':[{'items':[{'description':'Pad 1 [/C1/DRIVE] of R103'},{'description':'Track [/C1/DRIVE] on B.Cu'}]}]}
        self.assertEqual(unrouted_names(data),['/C1/DRIVE'])
    def test_bad_routing_zone_rejected(self):
        original=json.loads((ROOT/'design/boards/fixture-route-one.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'fixture-route-one.json'
            original['routing']['zones'][0]['layers']=['In1.Cu'];path.write_text(json.dumps(original))
            with self.assertRaises(ValueError):load_definition(path)
if __name__=='__main__':unittest.main()
