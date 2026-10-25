"""Focused numerical/preservation regressions, not native or physical acceptance."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('mechanical', HERE/'build.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MechanicalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((HERE/'candidates.json').read_text())
        cls.inputs = m.load_inputs()
        cls.report = m.build(cls.cfg, cls.inputs)

    def test_filesystem_enumeration_does_not_change_any_generated_bytes(self):
        # Fresh checkouts need not enumerate identical files in creation order.
        normal = m.outputs(self.cfg, self.inputs)
        original = Path.glob
        with patch.object(Path, 'glob', lambda path, pattern: iter(reversed(list(original(path, pattern))))):
            reversed_order = m.outputs(self.cfg, self.inputs)
        self.assertEqual(set(normal), set(reversed_order))
        for name in normal:
            with self.subTest(output=name):
                self.assertEqual(normal[name], reversed_order[name])

    def test_power_contract_ownership_corridors_and_limits(self):
        for alt in self.report['alternatives']:
            contract = alt['power_reconciliation']
            self.assertEqual(contract['existing_main_lands_owner'], 'KA')
            self.assertEqual(contract['protection_owner'], 'KA')
            self.assertEqual(len(alt['power_bounds']), 18)
            self.assertTrue(all(p['feed_core']=='KA' for p in alt['power_bounds']))
            count = 1 if alt['partition']=='two' else 2
            self.assertEqual(len(contract['new_feeds']), count)
            self.assertEqual(len(contract['endpoint_clearance_screens']), 2*count)
            for feed in contract['new_feeds']:
                self.assertEqual([w['net'] for w in feed['wires']], ['+12V','-12V','+5V','AGND','AGND','AGND'])
                self.assertTrue(all(w['maximum_cut_length_mm']==110 for w in feed['wires']))
            for endpoint in contract['endpoint_clearance_screens']:
                self.assertIsNone(endpoint['global_origin_mm'])
                self.assertEqual(endpoint['land_row_reserve_mm'], [91,6])
                if endpoint['board']!='KA':
                    self.assertEqual(endpoint['bare_face_gap_mm'], 24.4)
                    self.assertEqual(endpoint['normal_corridor_deficit_mm'], 3.6)
            for passage in alt['through_loom_passages']+alt['connector_service_passages']:
                if passage.get('board', passage.get('blocking_board'))!='KA':
                    self.assertFalse(any(c['kind']=='protection-feed-reserve' for c in passage['other_reservation_conflicts']))

    def test_harness_pin_and_pose_mutations_fail(self):
        baseline = self.inputs['partition']
        frozen = m.freeze_interfaces(baseline)
        for field, replacement in [('pcb_reference', 'J999999'), ('pin_map', {'1': 'NC'}),
                                   ('center_mm', [0, 0]), ('rotation_deg', 1)]:
            changed = copy.deepcopy(baseline)
            changed['connectors'][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                m.assert_interfaces(frozen, changed)
        changed = copy.deepcopy(baseline)
        changed['harnesses'][0]['id'] = 'different'
        with self.assertRaises(ValueError):
            m.assert_interfaces(frozen, changed)

    def test_all_interfaces_and_complete_pin_maps_retained(self):
        frozen = self.report['frozen_interfaces']
        self.assertEqual(len(frozen), 195)
        self.assertEqual(sum(any(e['board']=='K' for e in h['endpoints']) for h in frozen),191)
        counts = {'signals':0,'AGND':0,'rail':0,'NC':0}
        for harness in frozen:
            a,b=harness['endpoints']
            self.assertEqual(a['pin_map'],b['pin_map'])
            for net in a['pin_map'].values():
                if net is None or str(net).startswith('NC'): counts['NC']+=1
                elif net=='AGND': counts['AGND']+=1
                elif net in ('+12V','-12V','+5V'): counts['rail']+=1
                else: counts['signals']+=1
        self.assertEqual(counts,{'signals':513,'AGND':380,'rail':18,'NC':4})

    def test_expected_epic_assignment(self):
        for a in self.report['alternatives']:
            two=a['partition']=='two'
            self.assertEqual(a['summary']['harnesses_by_core'],{'KA':106,'KB':85} if two else {'KA':58,'KB':70,'KC':63})
            self.assertEqual(a['summary']['trimmers_by_core'],{'KA':64,'KB':36} if two else {'KA':31,'KB':33,'KC':36})
            self.assertEqual(sum(b['master_package_count_including_dnp'] for b in a['boards']),3385)
            self.assertEqual(sum(h['unchanged'] for h in a['harnesses']),4)

    def test_continuous_bounds_and_rejected_short_span(self):
        for span in (2.8,20,40,73.8,126):
            _,radius,chord,upper=m.axial_route(0,0,0,span)
            points=[[0,4*math.sin(math.pi*i/10000)**2,span*i/10000] for i in range(10001)]
            dense=sum(math.dist(a,b) for a,b in zip(points,points[1:]))
            self.assertLessEqual(chord,dense+1e-10)
            self.assertLessEqual(dense,upper)
            self.assertAlmostEqual(radius,span**2/(8*math.pi**2))
        rejected=next(a for a in self.report['alternatives'] if a['id']=='three-120mm-rejected')
        self.assertEqual(rejected['summary']['hard_conflicts']['bend-radius'],58)

    def test_dimensioned_support_conflict_is_retained(self):
        a=next(a for a in self.report['alternatives'] if a['id']=='three-compact')
        p=next(p for p in a['through_loom_passages'] if p['id']=='K-P-10' and p['board']=='KA')
        c=next(c for c in p['other_reservation_conflicts'] if c['kind']=='support')
        self.assertEqual(c['overlap_mm'][:2],[253.9,287.9])
        self.assertGreater(c['overlap_mm'][2]-c['overlap_mm'][0],1.5)

    def test_labels_are_separate_and_inside_notched_outline(self):
        for a in self.report['alternatives']:
            for i,t in enumerate(a['trimmers']):
                q=t['label_reservation_mm']
                self.assertFalse(t['label_conflicting_refs'])
                for conflict in a['hard_conflicts']:
                    if conflict.get('board') == t['board'] and 'box_mm' in conflict:
                        self.assertFalse(m.rect_overlap(q, conflict['box_mm']))
                self.assertGreaterEqual(q[0],4.3)
                self.assertGreaterEqual(q[1],8.3)
                self.assertLessEqual(q[2],313.7)
                self.assertLessEqual(q[3],291.7)
                self.assertFalse(q[2]>257.7 and q[3]>245.7)
                self.assertGreaterEqual(q[2]-q[0],len(t['label_lines'][1])*.7+2-1e-8)
                for other in a['trimmers'][i+1:]:
                    if (t['board'],t['mounted_face'])==(other['board'],other['mounted_face']):
                        self.assertFalse(m.rect_overlap(q,other['label_reservation_mm']))

    def test_invalid_family_and_planes_rejected(self):
        with self.assertRaises(ValueError):m.owner('invented',self.cfg['partitions']['two'])
        cfg=copy.deepcopy(self.cfg)
        cfg['alternatives'][0]['front_z_mm']['KA']=float('nan')
        with self.assertRaises(ValueError):m.build(cfg,self.inputs)
        cfg['alternatives'][0]['front_z_mm']['KA']=-100
        with self.assertRaises(ValueError):m.build(cfg,self.inputs)

    def test_physical_and_native_stay_unqualified(self):
        self.assertTrue(self.report['physical_fit'].startswith('NOT RUN'))
        self.assertTrue(self.report['native_acceptance'].startswith('NOT RUN'))
        self.assertEqual(self.report['trimmer_unresolved_mpn_count'],23)
        for a in self.report['alternatives']:
            self.assertEqual(sum(t['mounted_face']=='F.Cu' for t in a['trimmers']),44)
            self.assertEqual(sum(t['mounted_face']=='B.Cu' for t in a['trimmers']),56)
            self.assertTrue(all(t['tool_proposal']['free_length_mm']==60 for t in a['trimmers']))


if __name__=='__main__':unittest.main()
