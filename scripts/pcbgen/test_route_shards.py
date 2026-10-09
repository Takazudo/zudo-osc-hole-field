import unittest
import json,tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.pcbgen.route_shards import area_plan, copper_blocks, delta, disjoint, merge_text, plan

U = ['00000000-0000-4000-8000-%012d' % i for i in range(10)]


def seg(uid, net, layer='F.Cu', x=0):
    return (f'\t(segment\n\t\t(start {x} 0)\n\t\t(end {x} 1)\n\t\t(width 0.2)\n\t\t(layer "{layer}")\n'
            f'\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n')


def via(uid, net):
    return f'\t(via\n\t\t(at 1 1)\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n'


def board(*items):
    return '(kicad_pcb\n\t(version 20250000)\n' + ''.join(items) + ')\n'


class MergeAcceptanceTests(unittest.TestCase):
    def test_complete_native_observations_do_not_bypass_errors_splits_or_failed_evidence(self):
        from scripts.pcbgen import route_shards,route_jack_grid as driver
        from scripts.pcbgen.test_grid_router import crossing_board
        from scripts.pcbgen.complete_native_warnings import append_observations
        old=('hole_to_hole','warning',('old-a','old-b'))
        shifted=('hole_to_hole','warning',('old-c','old-d'))
        def report(item):
            return {'violations':[dict(type=item[0],severity=item[1],items=[{'uuid':u} for u in item[2]])],'schematic_parity':[]}
        for failure in ('none','evidence','error','split','fresh'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);target=root/'boards/osc-jack-left/osc-jack-left.kicad_pcb'
                target.parent.mkdir(parents=True);original=board(seg(U[0],'A'));target.write_text(original)
                proposal=root/'delta.json';proposal.write_text(json.dumps(delta(original,board(seg(U[0],'A'),seg(U[1],'B')))))
                before={**crossing_board(),'open_edges':3,'islands':{'A':[['a0','a1']],'B':[['b0'],['b1']]}}
                after={**before,'open_edges':1,'islands':{}}
                if failure=='split':after['islands']={'A':[['a0'],['a1']]}
                fresh=after if failure!='fresh' else {**after,'islands':{'B':[['b0'],['b1']]}}
                bd,ad=report(old),report(shifted)
                if failure=='error':ad['violations'].append(dict(type='clearance',severity='error',items=[]))
                def workspace(board_id,name):
                    folder=root/name;folder.mkdir();return folder
                def evidence(*args):
                    if failure=='evidence':raise ValueError('fixture context changed')
                    return append_observations(bd,{old,shifted}),append_observations(ad,{old,shifted}),{'status':'test native observations'}
                with patch.object(route_shards,'ROOT',root),patch.object(driver,'workspace',side_effect=workspace),\
                     patch.object(driver,'check',side_effect=[(bd,before),(report(shifted),after),(ad,fresh)]),\
                     patch('scripts.pcbgen.complete_native_warnings.audit_current_reports',side_effect=evidence):
                    receipt=route_shards.merge('osc-jack-left',[proposal],'complete',complete_native_warnings=True)
                self.assertFalse(receipt['raw_promotion_gate']['adopted'])
                self.assertEqual(receipt['adopted'],failure=='none')
                if failure!='none':self.assertEqual(target.read_text(),original)
                if failure=='evidence':self.assertEqual(receipt['rejection_reason'],'incomplete_native_warning_evidence')

    def test_reverted_geometry_and_native_error_evidence_survive_next_attempt(self):
        from scripts.pcbgen import route_shards,route_jack_grid as driver
        from scripts.pcbgen.test_grid_router import crossing_board
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);target=root/'boards/osc-jack-left/osc-jack-left.kicad_pcb'
            target.parent.mkdir(parents=True);original=board(seg(U[0],'A'));target.write_text(original)
            proposal=root/'delta.json';proposal.write_text(json.dumps(delta(original,board(seg(U[0],'A'),seg(U[1],'B')))))
            state={**crossing_board(),'open_edges':2};clean={'violations':[],'schematic_parity':[]}
            violation={'severity':'error','type':'clearance','items':[{'uuid':U[1]}]}
            dirty={'violations':[violation],'schematic_parity':[]};checks=iter([clean,dirty,clean,clean])
            def workspace(board_id,name):
                folder=root/name
                if folder.exists():route_shards.shutil.rmtree(folder)
                folder.mkdir();return folder
            def check(path):
                drc=next(checks);path.with_name('drc.json').write_text(json.dumps(drc))
                path.with_name('dump.json').write_text(json.dumps(state));return drc,state
            with patch.object(route_shards,'ROOT',root),patch.object(driver,'workspace',side_effect=workspace),\
                 patch.object(driver,'check',side_effect=check):
                receipt=route_shards.merge('osc-jack-left',[proposal],'retention')
            self.assertFalse(receipt['adopted']);self.assertEqual(target.read_text(),original)
            self.assertEqual(receipt['copper_added'],0);self.assertEqual(receipt['drc_errors'],0)
            rejected=receipt['rejected_attempts'];self.assertEqual(len(rejected),1)
            self.assertEqual(rejected[0]['native_errors'],[violation])
            self.assertEqual(rejected[0]['reverted_nets'],['B'])
            saved=root/rejected[0]['workspace']
            self.assertIn(U[1],(saved/target.name).read_text())
            self.assertEqual(json.loads((saved/'drc.json').read_text()),dirty)
            self.assertEqual(len(json.loads((saved/'candidate-replay.json').read_text())['added']),1)
            checks=iter([clean,dirty,clean,clean])
            with patch.object(route_shards,'ROOT',root),patch.object(driver,'workspace',side_effect=workspace),\
                 patch.object(driver,'check',side_effect=check):
                again=route_shards.merge('osc-jack-left',[proposal],'retention-again')
            self.assertNotEqual(again['rejected_attempts'][0]['workspace'],rejected[0]['workspace'])
            self.assertEqual(json.loads((saved/'drc.json').read_text()),dirty)

    def test_recovered_signal_gain_must_restore_split_return_membership(self):
        from scripts.pcbgen import route_shards,route_jack_grid as driver
        from scripts.pcbgen.test_grid_router import crossing_board
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);target=root/'boards/osc-jack-left/osc-jack-left.kicad_pcb'
            target.parent.mkdir(parents=True);original=board(seg(U[0],'AGND'));target.write_text(original)
            definition=root/'design/boards/osc-jack-left.json';definition.parent.mkdir(parents=True);definition.write_text('{}')
            proposal=root/'delta.json';proposal.write_text(json.dumps(delta(original,board(seg(U[0],'AGND'),seg(U[1],'B')))))
            before=crossing_board();before['pads']=[{**p,'net':'AGND' if p['net']=='A' else p['net']} for p in before['pads']]
            before['islands']={'AGND':[['a0','a1']],'B':[['b0'],['b1'],['copper-fragment']]};before['open_edges']=2
            split={**before,'islands':{'AGND':[['a0'],['a1']]},'open_edges':1}
            joined={**before,'islands':{},'open_edges':0};clean={'violations':[],'schematic_parity':[]}
            states=iter([before,split,joined])
            def workspace(board_id,name):
                folder=root/name;folder.mkdir();return folder
            def check(path):
                state=next(states);path.with_name('dump.json').write_text(json.dumps(state));path.with_name('drc.json').write_text(json.dumps(clean));return clean,state
            def stitch(board_id,base,candidate,*args):
                result=workspace(board_id,'stitched')/target.name
                result.write_text(board(seg(U[0],'AGND'),seg(U[1],'B'),seg(U[2],'AGND')))
                result.with_name('dump.json').write_text(json.dumps(joined));result.with_name('drc.json').write_text(json.dumps(clean))
                return result,{'agnd_stitch':{'links_added':1}}
            with patch.object(route_shards,'ROOT',root),patch.object(driver,'workspace',side_effect=workspace),patch.object(driver,'check',side_effect=check),patch.object(driver,'stitched',side_effect=stitch) as repair:
                receipt=route_shards.merge('osc-jack-left',[proposal],'recovery',repair_ground=True)
            repair.assert_called_once();self.assertTrue(receipt['adopted']);self.assertEqual(receipt['copper_added'],2)
            self.assertEqual(receipt['split_pad_groups'],[])

    def test_fresh_copy_drift_or_native_error_cannot_promote(self):
        from scripts.pcbgen import route_shards,route_jack_grid as driver
        from scripts.pcbgen.test_grid_router import crossing_board
        for failure in ('none','connectivity','drc'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);target=root/'boards/osc-jack-left/osc-jack-left.kicad_pcb'
                target.parent.mkdir(parents=True);original=board(seg(U[0],'A'));target.write_text(original)
                proposal=root/'delta.json';proposal.write_text(json.dumps(delta(original,board(seg(U[0],'A'),seg(U[1],'B')))))
                before={**crossing_board(),'open_edges':2}
                after={**before,'open_edges':1,'islands':{'B':[['b0'],['b1']]}}
                fresh=after if failure!='connectivity' else {**after,'islands':{'A':[['a0'],['a1']]}}
                clean={'violations':[],'schematic_parity':[]}
                drc=clean if failure!='drc' else {'violations':[{'severity':'error','type':'clearance','items':[]}],'schematic_parity':[]}
                def workspace(board_id,name):
                    folder=root/name;folder.mkdir();return folder
                with patch.object(route_shards,'ROOT',root),patch.object(driver,'workspace',side_effect=workspace),patch.object(driver,'check',side_effect=[(clean,before),(clean,after),(drc,fresh)]):
                    receipt=route_shards.merge('osc-jack-left',[proposal],'test')
                self.assertEqual(receipt['adopted'],failure=='none')
                if failure=='none':self.assertIn('copper_replay',receipt)
                else:self.assertEqual(target.read_text(),original)
                if failure=='drc':self.assertEqual(receipt['drc_errors'],1)


class PlanTest(unittest.TestCase):
    def test_every_net_has_one_owner_and_load_is_balanced(self):
        regions = [((0, 0), (1, 1), 9), ((5, 5), (6, 6), 5), ((9, 9), (10, 10), 4), ((20, 0), (21, 1), 1)]
        nets_of = [{'A', 'B'}, {'B', 'C'}, {'C', 'D'}, {'A'}]
        shards = plan(regions, nets_of, 2)
        owned = [set(s['nets']) for s in shards]
        self.assertFalse(owned[0] & owned[1])
        self.assertEqual(owned[0] | owned[1], {'A', 'B', 'C', 'D'})
        self.assertEqual([s['stranded_pins'] for s in shards], [10, 9])
        for s in shards:
            for nets in s['region_nets']:
                self.assertTrue(set(nets) <= set(s['nets']))

    def test_regions_overlapping_within_the_margin_share_a_shard(self):
        regions = [((0, 0), (4, 4), 5), ((50, 50), (54, 54), 8), ((7, 0), (9, 2), 3), ((12, 0), (14, 2), 3)]
        apart = plan(regions, [{'A'}, {'B'}, {'C'}, {'D'}], 2, margin=1)
        together = plan(regions, [{'A'}, {'B'}, {'C'}, {'D'}], 2, margin=2)
        self.assertEqual([s['nets'] for s in apart], [['B', 'D'], ['A', 'C']])
        # A and C join; D would push that group past the even share (10 of 19 pins), so it stays apart.
        self.assertEqual([s['nets'] for s in together], [['A', 'C', 'D'], ['B']])

    def test_overlap_groups_stop_at_an_even_share(self):
        chain = [((3 * i, 0), (3 * i + 2, 2), 1) for i in range(8)]
        shards = plan(chain, [{f'N{i}'} for i in range(8)], 4, margin=1)
        self.assertEqual([s['stranded_pins'] for s in shards], [2, 2, 2, 2])

    def test_area_plan_balances_open_edges_and_keeps_neighbours(self):
        points = {f'L{i}': (i, 0, 1) for i in range(4)}
        points.update({f'R{i}': (100 + i, 0, 1) for i in range(4)})
        points['closed-left'] = (1.5, 0, 0)
        left, right = area_plan(points, 2)
        self.assertEqual(set(left), {'L0', 'L1', 'L2', 'L3', 'closed-left'})
        self.assertEqual(set(right), {'R0', 'R1', 'R2', 'R3'})
        shards = area_plan(points, 4)
        self.assertEqual(sorted(len([n for n in s if n.startswith(('L', 'R'))]) for s in shards), [2, 2, 2, 2])
        self.assertEqual(sorted(n for s in shards for n in s), sorted(points))

    def test_more_shards_than_regions_leaves_empty_shards(self):
        shards = plan([((0, 0), (1, 1), 3)], [{'A'}], 3)
        self.assertEqual([len(s['regions']) for s in shards], [1, 0, 0])
        self.assertEqual(shards[1]['nets'], [])


class DeltaMergeTest(unittest.TestCase):
    def test_legacy_duplicate_ids_are_preserved_but_cannot_hide_removed_geometry(self):
        original=board(seg(U[0],'A'),seg(U[0],'A',x=2))
        changed=board(seg(U[0],'A'),seg(U[0],'A',x=2),seg(U[1],'B'))
        d=delta(original,changed)
        self.assertEqual(len(d['added']),1);self.assertEqual(d['removed'],[])
        self.assertEqual(merge_text(original,[d]).count(f'(uuid "{U[0]}")'),2)
        with self.assertRaisesRegex(ValueError,'ambiguous duplicate'):
            delta(original,board(seg(U[0],'A',x=2)))

    def test_merge_rejects_new_uuid_alias_of_surviving_copper(self):
        d=delta(board(),board(seg(U[0],'B')))
        with self.assertRaisesRegex(ValueError,'collides'):
            merge_text(board(seg(U[0],'A')),[d])

    def setUp(self):
        self.base = board(seg(U[0], 'A'), seg(U[1], 'B'), via(U[2], 'C'), seg(U[3], 'GND', 'In1.Cu'))

    def test_delta_records_removed_and_added_copper(self):
        final = board(seg(U[1], 'B'), via(U[2], 'C'), seg(U[3], 'GND', 'In1.Cu'), seg(U[4], 'A', 'B.Cu', 3))
        d = delta(self.base, final)
        self.assertEqual([r['uuid'] for r in d['removed']], [U[0]])
        self.assertEqual([(a['uuid'], a['layer']) for a in d['added']], [(U[4], 'B.Cu')])
        self.assertEqual(d['nets'], ['A'])

    def test_in_place_edits_are_rejected(self):
        with self.assertRaises(ValueError):
            delta(self.base, self.base.replace('(width 0.2)', '(width 0.3)', 1))

    def test_merge_applies_disjoint_deltas_and_reverts_nets(self):
        a = delta(self.base, board(seg(U[1], 'B'), via(U[2], 'C'), seg(U[3], 'GND', 'In1.Cu'), seg(U[4], 'A', x=4)))
        b = delta(self.base, board(seg(U[0], 'A'), via(U[2], 'C'), seg(U[3], 'GND', 'In1.Cu'), via(U[5], 'B')))
        merged = copper_blocks(merge_text(self.base, [a, b]))
        self.assertEqual(set(merged), {U[2], U[3], U[4], U[5]})
        self.assertEqual(merged[U[4]][1], 'F.Cu')
        reverted = copper_blocks(merge_text(self.base, [a, b], reverted={'B'}))
        self.assertEqual(set(reverted), {U[1], U[2], U[3], U[4]})
        # The merged text stays a parseable board with every surviving block intact.
        self.assertEqual(copper_blocks(merge_text(self.base, [])), copper_blocks(self.base))

    def test_a_net_claimed_twice_goes_to_the_first_delta(self):
        a = delta(self.base, board(seg(U[1], 'B'), via(U[2], 'C'), seg(U[3], 'GND', 'In1.Cu'), seg(U[4], 'A')))
        b = delta(self.base, board(seg(U[1], 'B'), via(U[2], 'C'), seg(U[3], 'GND', 'In1.Cu'), seg(U[5], 'A')))
        self.assertEqual(disjoint([a, b]), [{'A'}, set()])
        self.assertEqual(set(copper_blocks(merge_text(self.base, [a, b]))), {U[1], U[2], U[3], U[4]})


if __name__ == '__main__':
    unittest.main()
