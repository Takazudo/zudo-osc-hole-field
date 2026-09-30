"""Host-side router configuration and report contract checks."""
import contextlib,hashlib,io,json,tempfile,unittest
from unittest.mock import patch
from types import SimpleNamespace
from scripts.pcbgen import route
from pathlib import Path
from scripts.pcbgen.definition import load_definition
from scripts.pcbgen.route import read_env,memory_mb,unrouted_names

ROOT=Path(__file__).resolve().parents[2]
class RouterContractTest(unittest.TestCase):
    def test_fixture_layer_and_zone_contract(self):
        for case,layers,zone_layers in (('one',2,{'F.Cu','B.Cu'}),('six',2,{'F.Cu'}),('four',4,{'In1.Cu','In2.Cu'}),('dense',4,{'F.Cu','In1.Cu','In2.Cu'})):
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
    def test_complete_connectivity_does_not_hide_rule_or_parity_failures(self):
        definition = load_definition(ROOT/'design/boards/fixture-route-dense.json')
        spec_hash = hashlib.sha256(json.dumps(dict(routing=definition.routing,
            outline=definition.outline, layers=definition.layers), sort_keys=True,
            separators=(',', ':')).encode()).hexdigest()
        for failure in (None, 'rule', 'parity'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                board = root/'fixture.kicad_pcb'
                board.write_text('unchanged copper')
                report = root/'reports/routing.json'
                report.parent.mkdir()
                report.write_text(json.dumps(dict(routing_spec_sha256=spec_hash)))
                drc = dict(violations=[dict(severity='error')] if failure == 'rule' else [],
                    unconnected_items=[], schematic_parity=[{}] if failure == 'parity' else [])
                def inspect(command, **kwargs):
                    self.assertIn('inspect', command)
                    (root/command[-1]).write_text(json.dumps(dict(via_count=1, via_nets=['GND'],
                        total_track_length_mm=1, track_uuids=['owner'], zone_count=2)))
                with patch.object(route, 'ROOT', root), \
                     patch.object(route, 'load_definition', return_value=definition), \
                     patch.object(route, 'read_env', return_value=('image', 1024, 60)), \
                     patch.object(route, 'drc', return_value=drc), \
                     patch.object(route, 'run', side_effect=inspect), \
                     patch('sys.argv', ['route.py', 'fixture-route-dense', '--board', str(board)]), \
                     contextlib.redirect_stdout(io.StringIO()):
                    code = route.main()
                self.assertEqual(code, 2 if failure else 0)
                self.assertEqual(json.loads(report.read_text())['status'],
                    'INCOMPLETE DRAFT' if failure else 'UNCHANGED DRAFT')
                self.assertEqual(board.read_text(), 'unchanged copper')

    def test_failed_oracle_cannot_reuse_stale_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root/'drc.json'
            path.write_text(json.dumps(dict(kicad_version='10.0.6', violations=[], unconnected_items=[])))
            with patch.object(route, 'ROOT', root), \
                 patch.object(route, 'run', return_value=SimpleNamespace(returncode=1)):
                with self.assertRaisesRegex(RuntimeError, 'KiCad DRC failed'):
                    route.drc(root/'board.kicad_pcb', path)
            self.assertFalse(path.exists())

    def test_bad_routing_zone_rejected(self):
        original=json.loads((ROOT/'design/boards/fixture-route-one.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'fixture-route-one.json'
            original['routing']['zones'][0]['layers']=['In1.Cu'];path.write_text(json.dumps(original))
            with self.assertRaises(ValueError):load_definition(path)
if __name__=='__main__':unittest.main()
