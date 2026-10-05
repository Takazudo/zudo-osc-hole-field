import unittest

from scripts.pcbgen.route_shards import area_plan, copper_blocks, delta, disjoint, merge_text, plan

U = ['00000000-0000-4000-8000-%012d' % i for i in range(10)]


def seg(uid, net, layer='F.Cu', x=0):
    return (f'\t(segment\n\t\t(start {x} 0)\n\t\t(end {x} 1)\n\t\t(width 0.2)\n\t\t(layer "{layer}")\n'
            f'\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n')


def via(uid, net):
    return f'\t(via\n\t\t(at 1 1)\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n'


def board(*items):
    return '(kicad_pcb\n\t(version 20250000)\n' + ''.join(items) + ')\n'


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
