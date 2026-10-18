import copy
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('pilot_acceptance',ROOT/'design/architecture-278/implementation/stage41/native-pilot/acceptance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def state():
    return {'objects': {k: {'net': 'PRIVATE' if k in ('p','q','old') else 'AGND'} for k in ('p','q','old','f','g')},
            'groups': {'PRIVATE': [['p','q','old']], 'AGND': [['f'],['g']]}, 'native_open_edges':1}


class CompleteConnectivity(unittest.TestCase):
    def test_exact_reroute_preserves_foreign_partitions(self):
        a=state();b=copy.deepcopy(a);del b['objects']['old'];b['objects']['new']={'net':'PRIVATE'}
        b['groups']['PRIVATE']=[['p','q','new']]
        self.assertTrue(m.connectivity_gate(a,b,['old'],['new'],['PRIVATE'])['accepted_connectivity_only'])

    def test_foreign_merge_is_rejected_even_if_open_count_improves(self):
        a=state();b=copy.deepcopy(a);b['groups']['AGND']=[['f','g']];b['native_open_edges']=0
        r=m.connectivity_gate(a,b,target_nets=['PRIVATE'])
        self.assertFalse(r['accepted_connectivity_only']);self.assertEqual(r['changed_retained_nets'],['AGND'])

    def test_private_split_cannot_be_offset_by_foreign_merge(self):
        a=state();b=copy.deepcopy(a);b['groups']['PRIVATE']=[['p','old'],['q']];b['groups']['AGND']=[['f','g']]
        self.assertFalse(m.connectivity_gate(a,b,target_nets=['PRIVATE'])['accepted_connectivity_only'])

    def test_padless_added_island_rejected(self):
        a=state();b=copy.deepcopy(a);b['objects']['new']={'net':'PRIVATE'};b['groups']['PRIVATE'].append(['new']);b['native_open_edges']=2
        r=m.connectivity_gate(a,b,added=['new'],target_nets=['PRIVATE'])
        self.assertFalse(r['accepted_connectivity_only']);self.assertEqual(len(r['new_only_islands']),1)

    def test_unknown_delta_or_duplicate_membership_fails_closed(self):
        a=state()
        with self.assertRaises(ValueError):m.connectivity_gate(a,a,retired=['missing'])
        b=copy.deepcopy(a);b['groups']['PRIVATE'][0].append('p')
        with self.assertRaises(ValueError):m.connectivity_gate(a,b)

    def test_net_rename_is_not_a_valid_partition(self):
        a=state();b=copy.deepcopy(a);b['objects']['old']['net']='AGND'
        with self.assertRaises(ValueError):m.connectivity_gate(a,b)

    def test_missing_baseline_object_rejected(self):
        a=state();b=copy.deepcopy(a);del b['objects']['old'];b['groups']['PRIVATE'][0].remove('old')
        self.assertFalse(m.connectivity_gate(a,b)['accepted_connectivity_only'])

    def test_forged_count_or_empty_component_rejected(self):
        a=state();b=copy.deepcopy(a);b['native_open_edges']=0
        with self.assertRaises(ValueError):m.connectivity_gate(a,b)
        b=copy.deepcopy(a);b['groups']['PRIVATE'].append([]);b['native_open_edges']=2
        with self.assertRaises(ValueError):m.connectivity_gate(a,b)

if __name__=='__main__':unittest.main()
