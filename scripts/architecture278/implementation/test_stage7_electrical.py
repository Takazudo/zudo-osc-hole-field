import copy
import math
import unittest
from unittest.mock import patch
import stage7_electrical as e

class Electrical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import stage7_interfaces as iface,json
        spec=json.loads((e.OUT/'interface-input.json').read_text())
        packages=json.loads((e.hosting.a.OUT/'stage6/hosting-report.json').read_text())['placements']
        for p in packages.values():p['conditional_pad_depth_mm']=21.6 if p['side']=='rear'else 20
        cls.interface=iface.build_from(spec,{'placements':packages})
        cls.baseline=json.loads((e.hosting.a.OUT/'stage6/candidate-report.json').read_text())

    def test_source_trace(self):
        rows=e.source_trace();self.assertEqual(len(rows),18)
        self.assertEqual(next(r for r in rows if r['ref']=='U3305'and r['unit']==1)['pins']['2'],'A_BUFFER')
    def test_wrong_feedback_rejected(self):
        families,instances=e.hosting.specification()
        from dataclasses import replace
        fs=[]
        for f in families:
            if f.name=='manual_ab':
                ps=[]
                for p in f.parts:
                    if p.pins=={'1':'A_BUFFER','2':'A_BUFFER','3':'A_SENSE'}:p=replace(p,pins={**p.pins,'2':'SELECTOR_REMOTE'})
                    ps.append(p)
                f=replace(f,parts=tuple(ps))
            fs.append(f)
        with patch.object(e.hosting,'specification',return_value=(fs,instances)):
            with self.assertRaises(ValueError):e.source_trace()
    def test_RC(self):
        r=e.passive_pole(998,1e-9);self.assertAlmostEqual(r['tau_s'],998e-9);self.assertAlmostEqual(r['pole_Hz'],159473.89087364264)
        with self.assertRaises(ValueError):e.passive_pole(998,0)
    def test_octile(self):
        self.assertAlmostEqual(e.segment([0,0],[3,4]),1.15*(1+3*math.sqrt(2))+7)
    def test_contact_budget(self):
        b=e.conditional_budgets()['return_contact_sensitivity'];self.assertAlmostEqual(b['contact_only_current_ceiling_A']['after_test'],.002)
        self.assertAlmostEqual(b['rows'][3]['after_test_drop_V'],.001)
        self.assertIsNone(b['joint_return_current_A'])
    def test_no_cap_or_power_qualification(self):
        b=e.conditional_budgets();self.assertIsNone(b['power']['actual_current_bound_A'])
        self.assertTrue(all(n['aggregate_pF']is None and n['acceptance_limit_pF']==1000 for n in b['capacitance']['nets'].values()))
        self.assertAlmostEqual(b['A_B']['selected_5V_nominal_loading_error_V'],5*2200/10002200)

    def test_physical_counts_and_paths(self):
        r=e.analyze(self.interface,self.baseline);self.assertEqual(r['counts']['physical_wires'],15);self.assertEqual(len(r['signal_paths']),3);self.assertEqual(len(r['bypass_associations']),10)
        self.assertTrue(all(p['mated_contacts']==4 for p in r['signal_paths']))
        self.assertEqual(r['OSC_unchanged']['path_count'],225)
    def test_wrong_wire_net_rejected(self):
        r=copy.deepcopy(self.interface);r['links'][0]['conductors'][0]['net']='/X2/A_BUFFER'
        with self.assertRaises(ValueError):e.analyze(r,self.baseline)
    def test_missing_wire_rejected(self):
        r=copy.deepcopy(self.interface);r['links'][0]['conductors'].pop()
        with self.assertRaises(ValueError):e.analyze(r,self.baseline)
    def test_wrong_middle_contact_rejected(self):
        r=copy.deepcopy(self.interface);r['middle_trace_edges'][0]['to']['pin']='2'
        with self.assertRaises(ValueError):e.analyze(r,self.baseline)
    def test_missing_return_edge_rejected(self):
        r=copy.deepcopy(self.interface);r['middle_trace_edges'].pop()
        with self.assertRaises(ValueError):e.analyze(r,self.baseline)
    def test_actual_wire_pad_rejected(self):
        r=copy.deepcopy(self.interface);r['links'][0]['conductors'][0]['front_pad_xyz_mm'][0]+=1
        with self.assertRaises(ValueError):e.analyze(r,self.baseline)
    def test_wrong_source_pin_rejected(self):
        r=copy.deepcopy(self.interface);r['packages']['U3305']['pins']['2']='/X1/SELECTOR_REMOTE'
        with self.assertRaises(ValueError):e.analyze(r,self.baseline)

if __name__=='__main__':unittest.main()
