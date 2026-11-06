import copy
import json
import math
import unittest
import stage9_electrical as e

class TerminalDeltaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline=json.loads((e.OUT.parent/'stage8/interfaces-report.json').read_text())
        # Synthetic topology fixture; never exported as mechanical evidence.
        rows=[]
        for ref in ('J809','J909','J1009','D809','D909','D1009','SW608'):
            p=cls.baseline['packages'][ref]
            for pin,net in p['pins'].items():
                if net is None:continue
                a=p['pads_xyz_mm'][pin][0];b=[a[0],a[1],35];wirefrom=[a[0],a[1],21.6]if ref.startswith('D')else a
                rows.append({'ref':ref,'pin':pin,'net':net,'source_terminal_xyz_mm':a,'from_xyz_mm':wirefrom,'local_terminal_copper_mm':1.6 if ref.startswith('D')else 0,'to_xyz_mm':b,'wire_nominal_mm':35,'wire_tolerance_mm':3,'minimum_geometric_slack_mm':32-math.dist(wirefrom,b)})
        for r in rows:
            r['proposed_wire_points_xyz_mm']=[r['from_xyz_mm'],r['to_xyz_mm']]
            r['proposed_developed_wire_mm']=math.dist(r['from_xyz_mm'],r['to_xyz_mm'])
            r['minimum_proposed_route_slack_mm']=32-r['proposed_developed_wire_mm']
        cls.support={'terminal_extensions':rows,'terminal_lands':[{'ref':r['ref'],'pin':r['pin'],'net':r['net'],'xyz_mm':r['to_xyz_mm']}for r in rows],'added_mating_interfaces':0,'retained_NC_terminals':[{'ref':r,'pin':'TN','net':None}for r in ('J809','J909','J1009')],'LED_wire_lands':[{'ref':r['ref'],'pin':r['pin'],'net':r['net'],'xyz_mm':r['from_xyz_mm']}for r in rows if r['ref'].startswith('D')]}
    def test_exact_physical_counts(self):
        r=e.analyze(self.support,self.baseline)
        self.assertEqual(r['counts']['total_candidate_physical_wires'],30)
        self.assertEqual(r['counts']['added_mating_interfaces'],0)
        self.assertEqual(r['counts']['retained_jack_TN_NC'],3)
        self.assertFalse(r['hardware_acceptance'])
    def test_wrong_net_rejected(self):
        s=copy.deepcopy(self.support);s['terminal_extensions'][0]['net']='+12V'
        with self.assertRaisesRegex(ValueError,'pin/net'):e.analyze(s,self.baseline)
    def test_omitted_or_duplicate_terminal_rejected(self):
        for replacement in (False,True):
            s=copy.deepcopy(self.support)
            if replacement:s['terminal_extensions'][-1]=copy.deepcopy(s['terminal_extensions'][0])
            else:s['terminal_extensions'].pop()
            with self.assertRaisesRegex(ValueError,'inventory'):e.analyze(s,self.baseline)
    def test_detached_source_rejected(self):
        s=copy.deepcopy(self.support);s['terminal_extensions'][0]['source_terminal_xyz_mm'][0]+=.1
        with self.assertRaisesRegex(ValueError,'datum'):e.analyze(s,self.baseline)
    def test_slack_and_plane_rejected(self):
        for field,value in [('minimum_geometric_slack_mm',99),('to_xyz_mm',[0,0,36])]:
            s=copy.deepcopy(self.support);s['terminal_extensions'][0][field]=value
            with self.assertRaises(ValueError):e.analyze(s,self.baseline)
    def test_nonfinite_and_negative_values_rejected(self):
        for value in (float('nan'),float('inf'),-1):
            s=copy.deepcopy(self.support);s['terminal_extensions'][0]['wire_tolerance_mm']=value
            with self.assertRaisesRegex(ValueError,'finite nonnegative'):e.analyze(s,self.baseline)
        s=copy.deepcopy(self.support);s['terminal_extensions'][0]['to_xyz_mm'][0]=float('nan')
        with self.assertRaisesRegex(ValueError,'finite terminal'):e.analyze(s,self.baseline)
    def test_land_and_added_mate_rejected(self):
        s=copy.deepcopy(self.support);s['terminal_lands'][0]['xyz_mm']=[0,0,35]
        with self.assertRaisesRegex(ValueError,'target detached'):e.analyze(s,self.baseline)
        s=copy.deepcopy(self.support);s['added_mating_interfaces']=1
        with self.assertRaisesRegex(ValueError,'mating'):e.analyze(s,self.baseline)
    def test_positive_but_insufficient_slack_rejected(self):
        s=copy.deepcopy(self.support);r=s['terminal_extensions'][0]
        r['to_xyz_mm']=[r['from_xyz_mm'][0]+20,r['from_xyz_mm'][1],35]
        s['terminal_lands'][0]['xyz_mm']=r['to_xyz_mm']
        r['minimum_geometric_slack_mm']=32-math.dist(r['from_xyz_mm'],r['to_xyz_mm'])
        r['proposed_wire_points_xyz_mm']=[r['from_xyz_mm'],r['to_xyz_mm']]
        r['proposed_developed_wire_mm']=32-r['minimum_geometric_slack_mm'];r['minimum_proposed_route_slack_mm']=r['minimum_geometric_slack_mm']
        self.assertGreater(r['minimum_geometric_slack_mm'],0)
        with self.assertRaisesRegex(ValueError,'slack'):e.analyze(s,self.baseline)
    def test_NC_and_LED_land_mutations_rejected(self):
        s=copy.deepcopy(self.support);s['retained_NC_terminals'][0]['net']='AGND'
        with self.assertRaisesRegex(ValueError,'NC inventory'):e.analyze(s,self.baseline)
        s=copy.deepcopy(self.support);s['LED_wire_lands'][0]['xyz_mm']=[0,0,21.6]
        with self.assertRaisesRegex(ValueError,'LED wire detached'):e.analyze(s,self.baseline)
    def test_proposed_wire_length_mutation_rejected(self):
        s=copy.deepcopy(self.support);s['terminal_extensions'][0]['proposed_developed_wire_mm']+=1
        with self.assertRaisesRegex(ValueError,'route length'):e.analyze(s,self.baseline)
    def test_shared_output_tip_is_one_wire(self):
        r=e.analyze(self.support,self.baseline)
        row=[x for x in r['terminal_extensions']if x['ref']=='J1009'and x['pin']=='T']
        self.assertEqual(len(row),1);self.assertIn('AND remote feedback',row[0]['electrical_role'])
if __name__=='__main__':unittest.main()
