"""Mutation checks for complete rear package geometry and bypass association."""
import copy
import json
import unittest
import cluster_refinement as r

class RefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((r.OUT/'cluster-refinement-report.json').read_text())
        cls.spec=r.c.read('implementation/compact-rear.json')
        cls.contract=r.c.read('interface-contract.json')
        cls.physical={k:v for k,v in r.c.packages(cls.contract).items() if v['owner']=='rear-core' and v['footprint']}
        cls.base=r.c.place(cls.spec,cls.physical)
    def validate(self,p):r.validate(p,self.base,self.spec,self.physical)
    def test_complete_packages_units_and_clusters(self):
        self.validate(self.report['placements'])
        self.assertEqual((154,193,8,6),tuple(self.report[k] for k in ('package_count','unit_count','cluster_count','trim_count')))
    def test_missing_package_rejected(self):
        with self.assertRaises(ValueError):self.validate(self.report['placements'][1:])
    def test_supply_pad_warp_rejected(self):
        p=copy.deepcopy(self.report['placements']);q=next(x for x in p if x['ref']=='U1112');q['pads_mm']['4'][0][0]+=.1
        with self.assertRaises(ValueError):self.validate(p)
    def test_trim_axis_move_rejected(self):
        p=copy.deepcopy(self.report['placements']);i=next(i for i,q in enumerate(p) if q['ref']=='RVO1106');q=p[i]
        original=next(q for q in self.base if q['ref']=='RVO1106');p[i]=r.pose(original,[q['origin_mm'][0]+.1,q['origin_mm'][1]])
        with self.assertRaises(ValueError):self.validate(p)
    def test_overlap_rejected(self):
        p=copy.deepcopy(self.report['placements']);a=next(q for q in p if q['ref']=='C1142');b=next(q for q in self.base if q['ref']=='C1143')
        p[next(i for i,q in enumerate(p) if q['ref']=='C1143')]=r.pose(b,a['origin_mm'])
        with self.assertRaises(ValueError):self.validate(p)
    def test_cluster_transfer_rejected(self):
        p=copy.deepcopy(self.report['placements']);p[0]['cluster']='invalid'
        with self.assertRaises(ValueError):self.validate(p)
    def test_bypass_source_and_ground_semantics(self):
        expected=r.associations(self.contract,self.physical)
        self.assertEqual(19,len(expected))
        for a in self.report['bypass_associations']:
            self.assertIn({k:a[k] for k in expected[0]},expected)
            if a['IC'] not in r.SUPPLY_RETURN:self.assertIsNone(a['after']['IC_dedicated_return_pad_mm'])
            self.assertAlmostEqual(r.math.dist(a['after']['capacitor_rail_pad_mm'],a['after']['IC_rail_pad_mm']),a['after']['rail_pad_distance_mm'])
    def test_nonrail_net_span_inventory_and_arithmetic(self):
        report=self.report;old={p['ref']:p for p in self.base};new={p['ref']:p for p in report['placements']}
        expected={n for p in self.physical.values() for n in p['pins'].values() if n not in (None,'AGND','+12V','-12V','+5V')}
        self.assertEqual(expected,{row['net'] for row in report['local_net_span_comparison']})
        for row in report['local_net_span_comparison']:
            nodes=[(ref,pin) for ref,p in self.physical.items() for pin,n in p['pins'].items() if n==row['net']]
            self.assertEqual([ref+':'+pin for ref,pin in nodes],row['endpoints'])
            for by,key in ((old,'before_max_pair_separation_mm'),(new,'after_max_pair_separation_mm')):
                points=[xy for ref,pin in nodes for xy in by[ref]['pads_mm'][pin]]
                self.assertAlmostEqual(max((r.math.dist(a,b) for a,b in r.itertools.combinations(points,2)),default=0),row[key])
    def test_rotation_is_rigid(self):
        p=self.base[0];q=r.pose(p,p['origin_mm'],1)
        for pin,coords in p['pads_mm'].items():
            self.assertAlmostEqual(r.math.dist(coords[0],p['origin_mm']),r.math.dist(q['pads_mm'][pin][0],q['origin_mm']))

if __name__=='__main__':unittest.main()
