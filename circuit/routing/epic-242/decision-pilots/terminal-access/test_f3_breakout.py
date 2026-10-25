"""Bounded breakout regressions: synthetic inputs only, no saved-board routing."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import f3_adapter as adapter
import f3_breakout as repair
from test_f3_adapter import toy, BUDGET, POLICY
from test_exact_access import pad


def fixture():
    d, domain, pool = toy()
    anchor = domain['targets']['signal']['anchor_records'][1]
    card = {'schema': 'f3-exact-terminal-breakout-1', 'id': 'toy-breakout', 'board': 'toy',
        'input_board_sha256': d['board_sha256'], 'input_dump_canonical_sha256': adapter.digest(d),
        'bounds_mm': domain['common_bounds_mm'], 'net': 'N', 'anchor_uuid': anchor['uuid'],
        'ref': anchor['ref'], 'pad': anchor['pad'], 'start_nm': [20000000,10000000],
        'via_nm': [18000000,10000000], 'landing_layer': 'In2.Cu',
        'dimensions': {k:BUDGET[k] for k in ('signal_width_mm','clearance_mm','via_diameter_mm','via_drill_mm','raster_mm')}}
    return d, domain, pool, card


def prepare(d, domain, pool, card):
    return repair.prepare(d, domain, pool, BUDGET, POLICY, 'toy', card)


class BreakoutTests(unittest.TestCase):
    def test_only_signal_source_pool_changes_and_physical_input_stays_original(self):
        d, domain, pool, card = fixture(); before = copy.deepcopy(d); oldpool = copy.deepcopy(pool)
        # Preserve second-to-first direction while adding one source alternative.
        pool['signal']['a'].append({'start_nm':[10000000,10100000],'end_nm':[12000000,10100000],'via':True})
        oldpool = copy.deepcopy(pool)
        out, receipt = prepare(d, domain, pool, card)
        self.assertEqual(d, before); self.assertEqual(pool, oldpool)
        out['signal']['b'].pop(); self.assertEqual(out, pool)
        self.assertEqual(len(receipt['preview_copper']), 2)
        self.assertFalse(receipt['accepted']); self.assertFalse(receipt['native_exact_pair_closed'])

    def test_identity_dimensions_and_double_install_fail_closed(self):
        d, domain, pool, card = fixture()
        pool['signal']['a'].append({'start_nm':[10000000,10100000],'end_nm':[12000000,10100000],'via':True})
        for key,value in [('input_dump_canonical_sha256','0'*64),('board','other'),('anchor_uuid','a'),
                          ('net','other'),('landing_layer','B.Cu')]:
            bad=copy.deepcopy(card);bad[key]=value
            with self.assertRaises(ValueError):prepare(d,domain,pool,bad)
        bad=copy.deepcopy(card);bad['dimensions']['clearance_mm']=.1
        with self.assertRaisesRegex(ValueError,'dimension'):prepare(d,domain,pool,bad)
        out,_=prepare(d,domain,pool,card)
        with self.assertRaisesRegex(ValueError,'already installed'):prepare(d,domain,out,card)

    def test_real_foreign_copper_and_self_hole_are_not_bypassed(self):
        for kind in ('foreign','self-hole'):
            d,domain,pool,card=fixture()
            if kind=='foreign':d['pads'].append(pad('blocker','X',18,10,layer='In2.Cu',half=.1))
            else:d['vias'].append({'uuid':'staged-via','net':'N','xy':[18000000,10000000],'diameter':600000,'drill':300000})
            card['input_dump_canonical_sha256']=adapter.digest(d)
            with self.assertRaisesRegex(ValueError,'geometry rejected'):prepare(d,domain,pool,card)

    def test_source_marker_is_single_layer_not_fake_through_copper(self):
        d,domain,pool,card=fixture()
        pool['signal']['a'].append({'start_nm':[10000000,10100000],'end_nm':[12000000,10100000],'via':True})
        out,receipt=prepare(d,domain,pool,card)
        self.assertEqual(receipt['source_record']['pad']['layers'],['In2.Cu'])
        self.assertTrue(all(p[3]==0 for p in receipt['source_record']['path']))
        groups,records,_=adapter.portals(d,domain['targets']['signal'],out['signal'],BUDGET,domain['common_bounds_mm'])
        derived=copy.deepcopy(d);derived['pads'].extend(records[u]['pad'] for g in groups for u in g)
        raster=adapter.grid.Raster(derived,.1,bounds_mm=domain['common_bounds_mm'])
        mask=adapter.grid.island_mask(raster,derived,groups[1]);y,x=raster.cell(*card['via_nm'])
        self.assertTrue(mask[raster.layers.index('In2.Cu'),y,x]);self.assertFalse(mask[:,y,x].all())

    def test_selected_attachment_emitted_once_only_after_complete_pair(self):
        d,domain,pool,card=fixture()
        pool['signal']['a'].append({'start_nm':[10000000,10100000],'end_nm':[12000000,10100000],'via':True})
        out,receipt=prepare(d,domain,pool,card)
        def route(derived,**kwargs):
            groups=derived['islands']['N'];pads={p['uuid']:p for p in derived['pads']}
            source=pads[receipt['source_marker']];goal=next(pads[u] for u in groups[0] if pads[u]['layers']==['In2.Cu'])
            return [{'net':'N','path':[['In2.Cu',*source['xy'],0],['In2.Cu',*goal['xy'],0]]}],[]
        result=adapter.run(d,domain,out,BUDGET,POLICY,'toy',router=route)
        self.assertEqual(len(result['links']),1)
        at=[r for r in result['copper'] if r['kind']=='via' and r['at_nm']==card['via_nm']]
        self.assertEqual(len(at),1);self.assertFalse(result['accepted'])
        self.assertEqual(len(result['demands']),4)
        result=adapter.run(d,domain,out,BUDGET,POLICY,'toy',router=lambda *a,**kw:([{'path':None}],[]))
        self.assertEqual(result['copper'],[]);self.assertEqual(result['links'],[])

    def test_wrong_numerical_environment_refuses_before_input_read(self):
        with patch('importlib.metadata.version', return_value='0.0.0'):
            with self.assertRaisesRegex(ValueError, 'numerical versions drift'):
                repair.source_binding(Path(__file__).parent, Path('/nonexistent-input'), Path('/nonexistent-card'))

    def test_fill_veto_and_direction_reversal_refuse_preparation(self):
        d,domain,pool,card=fixture()
        with patch.object(adapter,'cumulative_fill_ok',return_value=False):
            with self.assertRaisesRegex(ValueError,'fill veto'):prepare(d,domain,pool,card)
        with self.assertRaisesRegex(ValueError,'reverse'):prepare(d,domain,pool,card)


if __name__=='__main__':unittest.main()
