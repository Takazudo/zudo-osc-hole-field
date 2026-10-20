"""Stage57 gate controls on synthetic snapshots; no route, no physical claims."""
from pathlib import Path
import copy, importlib.util, unittest
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('stage57_accept', HERE/'accept.py'); a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)


def fixture():
    objects = {'source': dict(kind='pad', ref='R8248', pin='2', net=a.NET), 'target': dict(kind='pad', ref='U8215', pin='3', net=a.NET)}
    main = ['target']
    for i in range(a.TARGET_SIZE - 1):
        k = 'track%d' % i; main.append(k); objects[k] = dict(kind='segment', uuid=k, net=a.NET)
    groups = {a.NET: [['source'], main]}
    for rail, sizes in a.RAILS.items():
        groups[rail] = []
        for gi, n in enumerate(sizes):
            g = ['%s-%d-%d' % (rail, gi, i) for i in range(n)]
            for k in g: objects[k] = dict(kind='pad', ref=k, pin='1', net=rail)
            groups[rail].append(g)
    used = sum(len(g) - 1 for g in groups.values())
    groups['OTHER'] = []
    for i in range(a.OPENS_BEFORE - used + 1):
        k = 'other%d' % i; groups['OTHER'].append([k]); objects[k] = dict(kind='pad', ref=k, pin='1', net='OTHER')
    old = dict(objects=objects, groups=groups, native_open_edges=a.OPENS_BEFORE)
    new = copy.deepcopy(old); new['groups'][a.NET] = [['source'] + main + ['new0', 'new1']]; new['native_open_edges'] = a.OPENS_AFTER
    for k in ['new0', 'new1']: new['objects'][k] = dict(kind='segment', uuid=k, net=a.NET)
    copper = [dict(uuid=k, kind='segment', layer='B.Cu', net=a.NET) for k in ['new0', 'new1']]
    return old, new, dict(copper=copper, removed_uuids=[], board_sha256=a.BASE)


class Stage57Gate(unittest.TestCase):
    def setUp(self): self.old, self.new, self.p = fixture()

    def test_exact_merge(self):
        r = a.connectivity(self.old, self.new, self.p)
        self.assertEqual((r['old_opens'], r['new_opens'], r['merged_retained_members']), (115, 114, 163))

    def test_minus12v_split_rejected(self):
        g = self.new['groups']['-12V'][0]; self.new['groups']['-12V'] = [g[:15], g[15:]]; self.new['native_open_edges'] += 1
        with self.assertRaises(ValueError): a.connectivity(self.old, self.new, self.p)

    def test_plus12v_split_rejected(self):
        g = self.new['groups']['+12V'][0]; self.new['groups']['+12V'] = [g[:1], g[1:]]; self.new['native_open_edges'] += 1
        with self.assertRaises(ValueError): a.connectivity(self.old, self.new, self.p)

    def test_other_partition_merge_rejected(self):
        self.new['groups']['OTHER'][0] += self.new['groups']['OTHER'].pop(); self.new['native_open_edges'] -= 1
        with self.assertRaises(ValueError): a.connectivity(self.old, self.new, self.p)

    def test_wrong_target_size(self):
        self.old['groups'][a.NET][1].pop(); del self.old['objects']['track0']
        with self.assertRaises(ValueError): a.connectivity(self.old, self.new, self.p)

    def test_new_only_island(self):
        self.new['groups'][a.NET][0].remove('new0'); self.new['groups'][a.NET].append(['new0']); self.new['native_open_edges'] += 1
        with self.assertRaises(ValueError): a.connectivity(self.old, self.new, self.p)

    def test_inner_layer_rejected(self):
        for layer in ('In1.Cu', 'In2.Cu', 'In3.Cu'):
            self.p['copper'][0]['layer'] = layer
            with self.assertRaises(ValueError): a.layer_gate(self.p)

    def test_outer_layers_pass_layer_gate(self):
        a.layer_gate(self.p)

    def test_in4_only_inner_layer_allowed(self):
        self.p['copper'][0]['layer'] = 'In4.Cu'; a.layer_gate(self.p)
        self.assertEqual(a.ALLOWED_TRACK_LAYERS, ('F.Cu', 'B.Cu', 'In4.Cu'))

    def test_unbound_proposal_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact authorized proposal'): a.bound_proposal(self.p)


if __name__ == '__main__':
    unittest.main()
