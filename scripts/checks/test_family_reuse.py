"""Architecture-source checks; no physical or electrical qualification."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'design/architecture-278/implementation/stage37/family-reuse'
spec=importlib.util.spec_from_file_location('family_reuse',HERE/'generate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class FamilyReuse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p=m.build()

    def test_determinism(self):
        self.assertEqual(self.p,json.loads((HERE/'proposal.json').read_text()))
        self.assertEqual(m.svg(self.p),(HERE/'comparison.svg').read_text())

    def test_complete_physical_packages_and_sensitive_locality(self):
        self.assertEqual(self.p['families']['AO']['region_counts'],{'core':29,'jack':59,'control':2})
        self.assertEqual(self.p['families']['MULT']['region_counts'],{'jack':36})
        for f in self.p['families'].values():
            self.assertTrue(all(len(r)==1 for r in f['declared_sensitive_net_regions'].values()))
            for p in f['packages'].values():
                units=[u['unit'] for u in p['units']]
                self.assertEqual(len(units),len(set(units)))
        # Real complete five-unit quad amplifiers, never a separately exported channel.
        self.assertEqual(len(self.p['families']['MULT']['packages']['U3102']['units']),5)
        self.assertEqual(self.p['families']['AO']['packages']['U7106']['region'],'jack')

    def test_pin_coverage_no_missing_signal_or_spurious_net(self):
        f=self.p['families']['AO'];maps=self.p['pinouts']
        for destination,link in [('control','AO-C10'),('jack','AO-J10')]:
            required={n for n,r in f['crossing_nets'].items() if destination in r and 'core' in r and n not in ('+12V','-12V','AGND')}
            self.assertEqual(set(maps[link].values())-{'AGND'},required)
            self.assertEqual([maps[link][str(i)] for i in (2,4,6,8,10)],['AGND']*5)
        self.assertIsNone(maps['P8-core']['5'])
        self.assertEqual([maps['P8'][str(i)] for i in (7,8)],[None,None])
        self.assertEqual(f['declared_sensitive_net_regions']['SUM_NODE'],['core'])
        self.assertNotIn('SUM_NODE',maps['AO-J10'].values())

    def test_panel_translation_and_exact_coverage(self):
        lock=json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']
        ids={*self.p['families']['AO']['instances'],*self.p['families']['MULT']['instances']}
        self.assertEqual(self.p['fixed_markers'],[p for p in lock if p['block'] in ids])
        self.assertEqual(len(self.p['fixed_markers']),64)
        for first,second,dx in [('A01','A06',85),('B1','B2',34)]:
            a={p['uid'].split('.',1)[1]:p for p in lock if p['block']==first}
            b={p['uid'].split('.',1)[1]:p for p in lock if p['block']==second}
            self.assertEqual(set(a),set(b))
            for k in a:
                self.assertAlmostEqual(b[k]['x_mm']-a[k]['x_mm'],dx)
                self.assertEqual(a[k]['y_mm'],b[k]['y_mm'])

    def test_trial_clearance_and_unknowns_fail_closed(self):
        self.assertEqual(self.p['trial_pair_hits'],[])
        self.assertEqual(len(self.p['occupied_unknown_projection_hits']),95)
        self.assertIn('KEEP_K1402_INCUMBENT',self.p['unmodeled_occupied'])
        self.assertTrue(self.p['integrated_fit'].startswith('BLOCKED'))
        a,b=self.p['rear_capacity_trials'][:2]
        self.assertFalse(m.overlap(m.grow(a['xy'],2),m.grow(b['xy'],2)))
        self.assertTrue(m.overlap(m.grow(a['xy'],3),m.grow(b['xy'],3)))
        for box in self.p['rear_capacity_trials']:
            x,y,x2,y2=box['xy'];self.assertTrue(0<=x<x2<=318 and 0<=y<y2<=298)

    def test_rejected_passive_front_keeps_electrical_risks_visible(self):
        r=self.p['rejected_passive_front']
        self.assertEqual(len(r['AO']['crossing_nets']),17)
        self.assertEqual(len(r['MULT']['crossing_nets']),7)
        self.assertIn('C14ce55_LED_K',r['MULT']['crossing_nets'])
        self.assertIn('OUT_1_TIP',r['MULT']['crossing_nets'])
        self.assertEqual(r['AO']['region_counts'],{'rear':81,'front':9})
        self.assertFalse(self.p['adopted'])

    def test_scoped_counts_do_not_claim_instrument_reduction(self):
        c=self.p['comparison'];self.assertEqual(c['baseline']['signal_bundles_touching_families'],23)
        self.assertEqual(c['baseline']['signal_header_ends_touching_families'],46)
        for k,n in [('individual',20),('shared_strips',10)]:
            self.assertEqual(c[k]['family_boards'],n)
            self.assertEqual(c[k]['all_cables'],c[k]['signal_cables']+c[k]['power_cables'])
            self.assertEqual(c[k]['header_ends_including_distribution'],2*c[k]['all_cables'])
            self.assertNotIn('whole_instrument_boards',c[k])

if __name__=='__main__':unittest.main()
