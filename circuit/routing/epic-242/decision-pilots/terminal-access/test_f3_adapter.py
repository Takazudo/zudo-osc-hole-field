"""Toy source regressions only; never search a retained board or run KiCad/C A*."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import f3_adapter as a
from test_exact_access import fixture, pad

SPEC = json.loads((Path(__file__).parent.parent/'matching-spec.json').read_text())
BUDGET, POLICY = SPEC['budget'], SPEC['route_policy']


def toy():
    d = fixture(); d['layers'] = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
    d['board_sha256'] = 'toy'; d['pads'] = [pad('a', 'N', 10, 10), pad('b', 'N', 20, 10)]
    targets = {}; pool = {}
    for kind, net, y in [('positive_supply', '+12V', 3), ('negative_supply', '-12V', 6), ('return', 'AGND', 23)]:
        pair = [pad(kind+'a', net, 5, y), pad(kind+'b', net, 25, y)]
        d['pads'].extend(pair); targets[kind] = {'net_token': net, 'anchor_records': pair}
        pool[kind] = {p['uuid']: [] for p in pair}
    targets['signal'] = {'net_token': 'N', 'anchor_records': d['pads'][:2]}
    pool['signal'] = {'a': [{'start_nm': [10000000, 10000000], 'end_nm': [12000000, 10000000], 'via': True}],
                      'b': [{'start_nm': [20000000, 10000000], 'end_nm': [18000000, 10000000], 'via': False}]}
    d['islands'] = {t['net_token']: [[p['uuid']] for p in t['anchor_records']] for t in targets.values()}
    return d, {'targets': targets, 'common_bounds_mm': [1, 1, 29, 29]}, pool


def mock_router(dump, **kwargs):
    net = kwargs['nets'][0]; groups = dump['islands'][net]; pads = {p['uuid']: p for p in dump['pads']}
    goal, source = (pads[g[0]] for g in groups)
    path = [[source['layers'][0], *source['xy'], 0]]
    if source['layers'] != goal['layers']:
        path.append([goal['layers'][0], *source['xy'], 0])
    path.append([goal['layers'][0], *goal['xy'], 0])
    return [{'net': net, 'path': path}], []


class AdapterTests(unittest.TestCase):
    def test_guard_refuses_driver_without_admission_before_import_or_fixture(self):
        import os
        env = {k:v for k,v in os.environ.items() if not k.startswith('EPIC242_NATIVE_')}
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('route_f3_access.py')),
                                 '--board', 'K1402', '--fixture', '/nonexistent', '--fixture-lock-sha256', '0'*64], capture_output=True, text=True, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires separately admitted', result.stderr)

    def test_complete_chain_and_original_demands_never_equal_native_credit(self):
        d, domain, pool = toy(); before = copy.deepcopy(d)
        result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=mock_router)
        self.assertEqual(d, before)
        self.assertEqual(len(result['demands']), 4)
        self.assertEqual(len(result['links']), 1)
        self.assertEqual(result['demands'][-1]['status'], 'UNCHECKED_COMPLETE_PAIR_PROPOSAL')
        self.assertEqual(len([r for r in result['copper'] if r['kind']=='via']), 2)
        self.assertFalse(result['coupled_connectivity_success'])
        self.assertFalse(result['accepted'])
        self.assertTrue(all(not s['native_exact_pair_closed'] for s in result['demands']))
        self.assertNotIn('ACCESS', json.dumps(result['copper']))
        self.assertEqual(set(result['links'][0]['anchor_uuids']), {'a', 'b'})

    def test_shared_router_toy_uses_python_astar_and_exercises_portal_handoff(self):
        d, domain, pool = toy()
        with patch.object(a.grid, 'astar', a.grid.astar_py), patch.object(a.grid, 'native_astar', side_effect=AssertionError('C forbidden')):
            result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=a.grid.route)
        self.assertEqual(result['demands'][-1]['status'], 'UNCHECKED_COMPLETE_PAIR_PROPOSAL')
        self.assertFalse(result['links'][0]['native_exact_pair_closed'])

    def test_foreign_copper_inside_named_anchor_does_not_get_virtual_override(self):
        d, domain, pool = toy(); d['pads'].append(pad('foreign', 'X', 10, 10, half=.1))
        with patch.object(a.grid, 'route', side_effect=AssertionError('no search for blocked anchor')) as router:
            result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=router)
        self.assertFalse(result['copper'])
        self.assertEqual(result['demands'][-1]['portal_counts'][0], 0)

    def test_new_prior_foreign_copper_blocks_saved_witness(self):
        d, domain, pool = toy()
        d['tracks'].append({'uuid':'prior','net':'X','a':[11000000,9000000],'b':[11000000,11000000],'width':300000,'layer':'F.Cu'})
        groups, _, rejected = a.portals(d, domain['targets']['signal'], pool['signal'], BUDGET, domain['common_bounds_mm'])
        self.assertFalse(groups[0]); self.assertTrue(rejected)
        self.assertEqual(rejected[0]['failure']['failing_owners']['foreign_copper_uuid'], 'prior')

    def test_landing_depletion_cannot_reverse_source_direction(self):
        d, domain, pool = toy()
        pool['signal']['b'].append({'start_nm':[20000000,10100000], 'end_nm':[18000000,10100000], 'via':False})
        with patch.object(a.grid, 'route', side_effect=AssertionError('direction must not reverse')) as router:
            result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=router)
        self.assertFalse(result['copper'])
        self.assertTrue(result['demands'][-1]['status'].startswith('LANDING_CENSUS'))

    def test_offgrid_rounding_bridge_is_checked(self):
        d, domain, pool = toy()
        pool['signal']['a'][0]['end_nm'] = [12049999, 10000000]
        groups, records, _ = a.portals(d, domain['targets']['signal'], pool['signal'], BUDGET, domain['common_bounds_mm'])
        path = records[groups[0][0]]['path']
        self.assertEqual(path[-1][1:3], [12000000, 10000000])
        self.assertEqual(path[-2][1:3], [12049999, 10000000])
        self.assertTrue(all(p[3]==0 for p in path))

    def test_unexplained_through_and_discontinuous_layer_change_rejected(self):
        d, domain, pool = toy()
        for mode in ('through', 'diagonal'):
            def bad_router(dump, **kwargs):
                results, removed = mock_router(dump, **kwargs)
                if mode == 'through': results[0]['path'][0][3] = 1
                else: results[0]['path'][1][1] += 100000
                return results, removed
            result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=bad_router)
            self.assertFalse(result['copper']); self.assertFalse(result['links'])
            self.assertTrue(result['demands'][-1]['status'].startswith('REJECTED_ATOMICALLY'))

    def test_clear_grid_endpoints_do_not_allow_crossing_foreign_middle(self):
        d, domain, pool = toy(); d['pads'].append(pad('mid', 'X', 15, 10, layer='In2.Cu'))
        result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=mock_router)
        self.assertFalse(result['copper'])
        self.assertIn('collision', result['demands'][-1]['reason'])

    def test_complete_grid_chain_cannot_leave_common_bounds(self):
        d, domain, pool = toy()
        def bad_router(dump, **kwargs):
            results, removed = mock_router(dump, **kwargs)
            results[0]['path'].insert(2, ['In2.Cu', 30000000, 10000000, 0])
            return results, removed
        result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=bad_router)
        self.assertFalse(result['copper'])
        self.assertIn('outside common bounds', result['demands'][-1]['reason'])

    def test_new_same_net_vias_cannot_hide_spacing_failure(self):
        d, domain, pool = toy()
        result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=mock_router)
        rows = copy.deepcopy(result['copper']); via = copy.deepcopy(next(r for r in rows if r['kind']=='via'))
        via['uuid']='another'; via['at_nm'][0] += 500000; rows.append(via)
        with self.assertRaisesRegex(ValueError, 'new vias'):
            a.validate_rows(d, rows, domain['targets']['signal'], BUDGET)

    def test_emitted_disconnected_rows_or_missing_real_terminal_rejected(self):
        d, domain, pool = toy(); result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=mock_router)
        rows = [r for r in result['copper'] if r['kind'] != 'via']
        with self.assertRaisesRegex(ValueError, 'do not join'):
            a.validate_rows(d, rows, domain['targets']['signal'], BUDGET)

    def test_new_copper_cannot_alias_original_identity(self):
        d, domain, pool = toy(); result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=mock_router)
        result['copper'][0]['uuid'] = 'a'
        with self.assertRaisesRegex(ValueError, 'aliases'):
            a.validate_rows(d, result['copper'], domain['targets']['signal'], BUDGET)

    def test_cumulative_fill_veto_discards_entire_pair(self):
        d, domain, pool = toy()
        with patch.object(a, 'cumulative_fill_ok', return_value=False) as guard:
            result = a.run(d, domain, pool, BUDGET, POLICY, 'toy', router=mock_router)
        self.assertFalse(result['copper']); self.assertFalse(result['links'])
        self.assertIs(guard.call_args.args[0], d)
        self.assertGreater(len(guard.call_args.args[1]), 0)

    def test_fill_disappearance_and_arrival_layer_via_disk(self):
        d, domain, _ = toy()
        d['pads'].append(pad('plane', 'AGND', 15, 15, layer='In1.Cu', half=.1))
        rows = [{'kind':'via','net':'N','uuid':'v','at_nm':[15000000,15000000], 'diameter_nm':600000,'drill_nm':300000}]
        self.assertFalse(a.cumulative_fill_ok(d, rows, BUDGET, POLICY, domain['common_bounds_mm']))


if __name__ == '__main__':
    unittest.main()
