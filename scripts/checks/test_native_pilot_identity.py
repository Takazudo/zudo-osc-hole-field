"""Regression for native reassignment of copper touching a moved pad."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS
import sys

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('pilot_identity', ROOT / 'design/architecture-278/implementation/stage41/native-pilot/identity_guard.py')
g = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(g)


def board(net='-12V', second_net='SIGNAL', extra='', zone_net='-12V'):
    return f'''(kicad_pcb
(segment (start 1 2) (end 2 2) (width .4) (layer "F.Cu") (net "{net}") (uuid "duplicate"))
(segment (start 3 2) (end 4 2) (width .4) (layer "F.Cu") (net "{second_net}") (uuid "duplicate"))
(footprint "R" (uuid "fp") (property "Reference" "R1")
 (pad "1" smd rect (at 1 2) (uuid "pad") (net "-12V")))
(zone\n(net "{zone_net}") (uuid "zone") (layer "In3.Cu") (filled_polygon (layer "In3.Cu") (pts (xy 1 2))))
(zone\n(uuid "rule") (layer "F.Cu") (keepout\n(tracks not_allowed)))
{extra})'''


class NativeIdentity(unittest.TestCase):
    def test_retirement_hash_must_match_claimed_occurrence(self):
        raw = board()
        spans = list(g.top_level_spans(raw))
        first = raw[spans[0][0]:spans[0][1]]
        second = raw[spans[1][0]:spans[1][1]]
        row = {'index': 0, 'kind': 'segment', 'uuid': 'duplicate', 'net': '-12V', 'sha256': g.digest(first)}
        receipt = {'retired_private_copper': [row]}
        self.assertEqual(g.bound_retirements(receipt, raw), [row])
        for bad in ({**row, 'sha256': g.digest(second)}, {**row, 'uuid': 'different'}, {**row, 'index': 1}):
            with self.assertRaises(ValueError):g.bound_retirements({'retired_private_copper': [bad]}, raw)

    def test_local_supply_retirement_cannot_include_shared_via(self):
        rows = [{'uuid': uid, 'net': net} for uid, net in g.LOCAL_SUPPLY_RETIREMENTS.items()]
        receipt = {'retired_private_copper': [], 'retired_local_supply_copper': rows}
        self.assertEqual(g.retirement_rows(receipt), rows)
        for invalid in (rows[:-1], rows + [rows[0]], rows[:-1] + [{'uuid': 'f2390319-3bbf-503b-8ce7-f134408e6163', 'net': '+12V'}]):
            with self.assertRaises(ValueError):
                g.retirement_rows({**receipt, 'retired_local_supply_copper': invalid})

    def test_all_three_observed_native_net_mutations_are_rejected(self):
        fixture = json.loads((ROOT / 'design/architecture-278/implementation/stage41/native-pilot/net-propagation-regression.json').read_text())
        a = '(kicad_pcb ' + '\n'.join(fixture['before']) + ')'
        b = '(kicad_pcb ' + '\n'.join(fixture['after']) + ')'
        result = g.compare(g.inventory(a), g.inventory(b))
        self.assertFalse(result['accepted'])
        self.assertEqual(len(result['missing_copper']), 3)
        self.assertEqual(len(result['unexpected_copper']), 3)
        self.assertEqual({r[3] for r in result['missing_copper']}, {'-12V'})
        self.assertEqual({r[3] for r in result['unexpected_copper']}, {'X229EA3F52C3EA7BD2189'})

    def test_no_change_and_zone_refill(self):
        a = board(); b = a.replace('(pts (xy 1 2))', '(pts (xy 4 5))')
        self.assertTrue(g.compare(g.inventory(a), g.inventory(b))['accepted'])
        self.assertEqual(sum(g.inventory(a)['rules'].values()), 1)

    def test_native_rail_to_existing_signal_reassignment_rejected(self):
        r = g.compare(g.inventory(board()), g.inventory(board('SIGNAL')))
        self.assertFalse(r['accepted'])
        self.assertEqual(len(r['missing_copper']), 1)

    def test_duplicate_uuid_occurrences_cannot_collapse_or_swap_nets(self):
        self.assertEqual(sum(g.inventory(board())['copper'].values()), 2)
        self.assertFalse(g.compare(g.inventory(board()), g.inventory(board('SIGNAL', '-12V')))['accepted'])

    def test_pad_net_merge_and_zone_net_change_rejected(self):
        a = board()
        for b in (a.replace('(uuid "pad") (net "-12V")', '(uuid "pad") (net "SIGNAL")'), board(zone_net='SIGNAL')):
            self.assertFalse(g.compare(g.inventory(a), g.inventory(b))['accepted'])

    def test_only_exact_retirement_allowed(self):
        a = board(); i = g.inventory(a)
        raw = next(a[x:y] for x, y in g.top_level_spans(a) if a[x:y].startswith('(segment'))
        b = a.replace(raw, '')
        self.assertFalse(g.compare(i, g.inventory(b))['accepted'])
        self.assertTrue(g.compare(i, g.inventory(b), [g.digest(raw)])['accepted'])
        with self.assertRaises(ValueError): g.compare(i, g.inventory(b), ['unknown'])

    def test_new_object_requires_exact_net_geometry_and_unique_uuid(self):
        a = board(); addition = '(via (at 5 5) (size .7) (drill .3) (layers "F.Cu" "B.Cu") (net "-12V") (uuid "new"))'
        b = board(extra=addition); before = g.inventory(a); after = g.inventory(b)
        new = list((after['copper'] - before['copper']).elements())
        self.assertFalse(g.compare(before, after)['accepted'])
        self.assertTrue(g.compare(before, after, allowed_new=new)['accepted'])
        renamed = g.inventory(b.replace('(net "-12V") (uuid "new")', '(net "SIGNAL") (uuid "new")'))
        self.assertFalse(g.compare(before, renamed, allowed_new=new)['accepted'])
        with self.assertRaises(ValueError): g.compare(before, after, allowed_new=[next(iter(before['copper']))])

    def test_native_memory_guard_rejects_relabelled_or_missing_occurrences(self):
        fake = NS(PCB_TRACE_T=1, PCB_VIA_T=2, F_Cu=0, GetBuildVersion=lambda: '10.0.6')
        spec = importlib.util.spec_from_file_location('pilot_native_guard_test', ROOT / 'design/architecture-278/implementation/stage41/native-pilot/native_guard.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'pcbnew': fake, 'identity_guard': g}):
            spec.loader.exec_module(module)
        raw = board(); inv = g.inventory(raw); tracks = []
        for _, uid, shape, net in inv['native_contract']:
            a, b, width, layer = shape
            obj = NS(net=net, m_Uuid=NS(AsString=lambda u=uid: u), Type=lambda: 1,
                     GetStart=lambda a=a: NS(x=a[0], y=a[1]), GetEnd=lambda b=b: NS(x=b[0], y=b[1]),
                     GetWidth=lambda w=width: w[0], GetLayer=lambda l=layer: l)
            obj.GetNetname = lambda o=obj: o.net
            tracks.append(obj)
        pad = NS(m_Uuid=NS(AsString=lambda: 'pad'), GetNumber=lambda: '1', GetNetname=lambda: '-12V')
        fp = NS(m_Uuid=NS(AsString=lambda: 'fp'), GetReference=lambda: 'R1', Pads=lambda: [pad])
        zones = [NS(m_Uuid=NS(AsString=lambda u=u: u), GetNetname=lambda n=n: n) for u, n, _ in inv['zones']]
        native = NS(GetTracks=lambda: tracks, GetFootprints=lambda: [fp], Zones=lambda: zones, GetLayerName=lambda l: l)
        self.assertTrue(all(module.check_native(native, raw).values()))
        tracks[0].net = 'SIGNAL'
        with self.assertRaises(ValueError): module.check_native(native, raw)
        tracks.pop()
        with self.assertRaises(ValueError): module.check_native(native, raw)
        fake.GetBuildVersion = lambda: '9.0.2'
        with self.assertRaises(ValueError): module.check_native(native, raw)

    def test_routing_cannot_change_prepared_pad_shape_or_board_outline(self):
        a = board(); before = g.inventory(a)
        changed = a.replace('(pad "1" smd rect', '(pad "1" smd oval')
        self.assertFalse(g.structure_matches(before, g.inventory(changed), {}))
        prepared = g.inventory(changed)
        self.assertTrue(g.structure_matches(before, prepared, prepared['footprints']))
        altered_again = changed.replace('smd oval', 'smd circle')
        self.assertFalse(g.structure_matches(before, g.inventory(altered_again), prepared['footprints']))
        with_outline = board(extra='(gr_line (start 0 0) (end 4 0) (layer "Edge.Cuts"))')
        different = with_outline.replace('(end 4 0)', '(end 5 0)')
        self.assertFalse(g.compare(g.inventory(with_outline), g.inventory(different))['accepted'])

    def test_rule_bytes_and_reference_identity_protected(self):
        a = board()
        for b in (a.replace('tracks not_allowed', 'tracks allowed'), a.replace('"R1"', '"R2"')):
            self.assertFalse(g.compare(g.inventory(a), g.inventory(b))['accepted'])

if __name__ == '__main__': unittest.main()
