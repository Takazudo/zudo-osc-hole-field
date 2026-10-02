import copy
import json
from pathlib import Path
import unittest
from scripts.checks.control_locality import apply_locality
from scripts.checks.partition35_floorplan import footprint_geometry

class ControlLocalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=lambda p:json.loads(Path(p).read_text())
        cls.io=read('design/reports/io-partition.json')
        cls.placements=read('design/partition/floorplan-candidate.json')['placements']
        cls.source=read('design/partition/partition-input.json')
        cls.connectors=read('design/partition/connector-packing-candidate.json')
        cls.lock={p['uid']:p for p in read('design/grid/placements.lock.json')['placements']}
        cls.shapes={p['footprint']:footprint_geometry(Path('footprints/kicad/zudo-osc-hole-field.pretty')/(p['footprint'].split(':')[1]+'.kicad_mod'))['courtyard_bbox_mm'] for p in cls.io['physical_packages']}
        cls.proposal=read('design/partition/control-locality.json')
        cls.optical=read('design/partition/stage-optical-input.json')

    def run_proposal(self,proposal):
        return apply_locality(self.placements,self.io,self.source,self.connectors,self.lock,self.shapes,proposal,self.optical)

    def test_full_source_closures_preserve_every_other_package(self):
        placed,report=self.run_proposal(self.proposal)
        refs={r for g in self.proposal['groups'].values() for r in g['placements']}
        self.assertEqual(len(refs),18)
        self.assertEqual(len(placed),len(self.placements))
        self.assertEqual([p for p in placed if p['ref'] not in refs],[p for p in self.placements if p['ref'] not in refs])
        self.assertEqual(len(report),2)
        for row in report:
            self.assertLess(row['maximum_component_centre_distance_mm'],25)
            self.assertEqual(len(row['bypass_supply_pad_distances']),2)
            self.assertTrue(all(p['distance_mm']<3 for p in row['bypass_supply_pad_distances']))

    def test_missing_capacitor_and_wrong_anchor_reject(self):
        p=copy.deepcopy(self.proposal);p['groups']['H1']['placements'].pop('C107')
        with self.assertRaisesRegex(ValueError,'nine'):self.run_proposal(p)
        p=copy.deepcopy(self.proposal);p['groups']['H1']['anchor_uid']='C:H2.SLEW'
        with self.assertRaisesRegex(ValueError,'anchor'):self.run_proposal(p)

    def test_nonfinite_and_distant_pose_reject(self):
        for x in (float('nan'),float('inf'),True,300):
            p=copy.deepcopy(self.proposal);p['groups']['H1']['placements']['C107']['x_mm']=x
            with self.subTest(x=x),self.assertRaises(ValueError):self.run_proposal(p)

    def test_intercomponent_and_fixed_hardware_collisions_reject(self):
        p=copy.deepcopy(self.proposal);p['groups']['H1']['placements']['C107']=dict(p['groups']['H1']['placements']['U102'])
        with self.assertRaisesRegex(ValueError,'collid'):self.run_proposal(p)
        p=copy.deepcopy(self.proposal);p['groups']['H1']['placements']['C107']={'x_mm':133.5,'y_mm':269,'rotation_deg':0}
        # The fixed control's through-hole footprint is an obstacle.
        with self.assertRaises(ValueError):self.run_proposal(p)

if __name__=='__main__':unittest.main()
