"""Analytical and mutation tests, NOT native KiCad acceptance."""
import copy
import importlib.util
import math
from pathlib import Path
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('joined_check',Path(__file__).with_name('check.py'))
j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)


def edge(ident,a,b,r):
    return {'id':ident,'a':a,'b':b,'r':r}


class Arithmetic(unittest.TestCase):
    def test_series_parallel_and_disconnected(self):
        self.assertAlmostEqual(j.effective_resistance([edge('a','x','y',.003)],'x','y'),.003)
        self.assertAlmostEqual(j.effective_resistance([edge('a','x','y',.003),edge('b','x','y',.006)],'x','y'),.002)
        self.assertAlmostEqual(j.effective_resistance([edge('a','x','z',.003),edge('b','z','y',.006)],'x','y'),.009)
        self.assertTrue(math.isinf(j.effective_resistance([edge('a','x','z',.003)],'x','y')))
        self.assertEqual(j.bound(4.6,.001,math.inf),4.6)

    def test_same_net_labels_are_not_edges(self):
        nodes=['KA/AGND','KB/AGND']
        self.assertTrue(math.isinf(j.effective_resistance([], *nodes)))
        wrong=edge('wire','KA/AGND','KC/AGND',.001)
        self.assertTrue(math.isinf(j.effective_resistance([wrong], *nodes)))
        self.assertAlmostEqual(j.effective_resistance([edge('wire',*nodes,.001)],*nodes),.001)

    def test_unequal_sharing_and_monotonic_bound(self):
        self.assertAlmostEqual(j.bound(4.6,.003,.006),4.6*2/3)
        self.assertGreater(j.bound(4.6,.002,.006),j.bound(4.6,.003,.006))
        self.assertGreater(j.bound(4.6,.003,.009),j.bound(4.6,.003,.006))
        threshold=.5*.01/(4.6-.5)
        self.assertAlmostEqual(j.bound(4.6,.01,threshold),.5)
        self.assertGreater(j.bound(4.6,.01,threshold+1e-9),.5)

    def test_invalid_and_duplicate_resistors_reject(self):
        for r in [0,-.1,math.nan,math.inf]:
            with self.subTest(r=r),self.assertRaises(ValueError):
                j.effective_resistance([edge('x','a','b',r)],'a','b')
        with self.assertRaises(ValueError):
            j.effective_resistance([edge('x','a','b',.1),edge('x','a','b',.1)],'a','b')

    def test_global_drop_no_restarted_copper(self):
        d=j.read('design/partition/partition-input.json')['load_distribution']
        self.assertAlmostEqual(j.path_drop(2.1,4.6,[110],[110],d),15.321)
        self.assertAlmostEqual(j.path_drop(2.1,4.6,[110,110],[110,110],d),26.242)
        with self.assertRaises(ValueError):
            j.path_drop(2.1,4.6,[110],[110],d,return_copper=.001)
        with self.assertRaises(ValueError):
            j.path_drop(2.1,4.6,[110.00001],[110],d)
        length=j.budgets(d)['+12V']['two_section_total_cut_limit_for_both_rail_and_return_mm']/2
        self.assertAlmostEqual(j.path_drop(2.1,4.6,[length,length],[length,length],d),20)
        self.assertGreater(j.path_drop(2.1,4.6,[length+.001,length],[length,length],d),20)

    def test_every_missing_return_combination(self):
        d=j.read('design/partition/partition-input.json')['load_distribution']
        gh=j.read('design/partition/harness-wire-evidence.json')['proposal']
        es=[edge(str(i),'KA','KB',.001)|{'kind':'main'} for i in range(3)]
        es.append(edge('gh','KA','KB',.1)|{'kind':'GH','minimum_r':.01})
        scenarios=j.return_scenarios(es,d,gh)
        self.assertEqual(CounterLengths(scenarios),{0:1,1:3,2:3,3:1})
        self.assertEqual(scenarios[-1]['worst']['upper_current_A'],4.6)
        self.assertIn('BLOCKED',scenarios[-1]['fault_eligibility'])


def CounterLengths(rows):
    from collections import Counter
    return dict(Counter(len(r['removed']) for r in rows))


class Interfaces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.joined,cls.owner=j.join_sources()
        cls.power=j.read(j.POWER+'contract.json')

    def mutated_source(self,path,mutate):
        original=j.read
        data=copy.deepcopy(original(path));mutate(data)
        with patch.object(j,'read',side_effect=lambda p:data if p==path else original(p)):
            with self.assertRaises(ValueError):j.join_sources()

    def test_census_and_unrealized_terminals(self):
        for option,cores in [('two',2),('three',3)]:
            result=self.joined[option]
            self.assertEqual(len(result['new_conductors']),6*(cores-1))
            self.assertEqual(len(result['old_main_lands']['KA']),18)
            self.assertEqual(result['new_native_terminal_count'],0)
            self.assertTrue(all(w['end_to_end_continuity']=='BLOCKED' for w in result['new_conductors']))
            self.assertEqual(sum(c['net']=='AGND' for c in result['legacy_conductors']),380)
            self.assertTrue(all(not c['wired'] for c in result['legacy_conductors'] if c['net']=='NC'))

    def test_pin_swap_wrong_owner_and_duplicate_terminal_reject(self):
        feed=self.power['options']['two']['new_feeds'][0]
        for mutate in [lambda f:f['wires'][0].update(net='-12V'),
                       lambda f:f['endpoint_envelopes'][1].update(board='KC'),
                       lambda f:f['wires'][1].update(terminal_ids=f['wires'][0]['terminal_ids']),
                       lambda f:f['wires'][0].update(net='+12V_IN')]:
            with self.subTest(mutate=mutate):
                f=copy.deepcopy(feed);mutate(f)
                with self.assertRaises(ValueError):j.matched_feed(f)

    def test_missing_and_changed_candidate_endpoints_reject(self):
        p=j.PREFIX+'candidates/two.json'
        self.mutated_source(p,lambda d:d['boards']['two-A']['core_endpoints'].pop())
        self.mutated_source(p,lambda d:d['boards']['two-A']['core_endpoints'][0].update(pcb_reference='J999999'))

    def test_missing_duplicate_feeds_reject(self):
        # Patch mechanical byte equality only indirectly: these in-memory data changes
        # test the semantic gate independently of the immutable-source file gate.
        self.mutated_source(j.POWER+'contract.json',lambda d:d['options']['two'].update(new_feeds=[]))
        self.mutated_source(j.POWER+'contract.json',lambda d:d['options']['two']['new_feeds'].append(copy.deepcopy(d['options']['two']['new_feeds'][0])))

    def test_coordinated_wrong_board_pair_rejects(self):
        def change(d):
            feed=d['options']['two']['new_feeds'][0]
            feed['boards'][1]='KC'
            feed['endpoint_envelopes'][1]['board']='KC'
        self.mutated_source(j.POWER+'contract.json',change)

    def test_main_land_identity_not_just_count(self):
        def rename(d):
            next(p for p in d['boards']['two-A']['placements'] if p['ref']=='TP990002')['ref']='TP990999'
        self.mutated_source(j.PREFIX+'candidates/two.json',rename)

    def test_duplicate_mechanical_routes_reject(self):
        a=j.read(j.PREFIX+'mechanical/generated/comparison.json')['alternatives'][0]
        a['harnesses'].append(copy.deepcopy(a['harnesses'][0]))
        with self.assertRaises(ValueError):
            j.network(a,self.joined,self.owner,
                j.read('design/partition/partition-input.json')['load_distribution'],
                j.read('design/partition/harness-wire-evidence.json')['proposal'])


if __name__=='__main__':unittest.main()
