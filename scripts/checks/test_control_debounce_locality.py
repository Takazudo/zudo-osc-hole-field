import copy
import json
from pathlib import Path
import unittest
from scripts.checks.control_debounce_locality import apply_debounce_locality, debounce_groups
from scripts.checks.partition35_floorplan import footprint_geometry


class ControlDebounceLocalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = lambda p: json.loads(Path(p).read_text())
        cls.io = read('design/reports/io-partition.json')
        cls.placements = read('design/partition/floorplan-candidate.json')['placements']
        cls.source = read('design/partition/partition-input.json')
        cls.connectors = read('design/partition/connector-packing-candidate.json')
        cls.lock = {p['uid']:p for p in read('design/grid/placements.lock.json')['placements']}
        cls.shapes = {p['footprint']:footprint_geometry(Path('footprints/kicad/zudo-osc-hole-field.pretty') /
            (p['footprint'].split(':')[1]+'.kicad_mod'))['courtyard_bbox_mm'] for p in cls.io['physical_packages']}
        cls.proposal = read('design/partition/control-debounce-locality.json')
        cls.optical = read('design/partition/stage-optical-input.json')

    def run_proposal(self, proposal):
        return apply_debounce_locality(self.placements,self.io,self.source,self.connectors,
            self.lock,self.shapes,proposal,self.optical)

    def test_complete_groups_preserve_fixed_and_unrelated_parts(self):
        io = copy.deepcopy(self.io)
        placed,report = self.run_proposal(self.proposal)
        refs = set(report['moved_references'])
        self.assertEqual(len(refs),90)
        self.assertEqual(len(report['groups']),30)
        self.assertLessEqual(report['maximum_capacitor_to_input_mm'],8)
        self.assertEqual([p for p in placed if p['ref'] not in refs],
                         [p for p in self.placements if p['ref'] not in refs])
        self.assertTrue(all(p['side']=='B.Cu' and not p['fixed'] for p in placed if p['ref'] in refs))
        self.assertEqual(self.io,io)

    def test_missing_group_or_member_rejected(self):
        p = copy.deepcopy(self.proposal);key = next(iter(p['groups']))
        del p['groups'][key]
        with self.assertRaises(ValueError):self.run_proposal(p)
        p = copy.deepcopy(self.proposal)
        p['groups'][key]['placements'].pop(key)
        with self.assertRaises(ValueError):self.run_proposal(p)

    def test_wrong_input_and_nonfinite_pose_rejected(self):
        for mode in ('input','nan','rotation','limit'):
            p = copy.deepcopy(self.proposal);key = next(iter(p['groups']));g = p['groups'][key]
            if mode=='input':g['input_pin']='2'
            if mode=='nan':g['placements'][key]['x_mm']=float('nan')
            if mode=='rotation':g['placements'][key]['rotation_deg']=45
            if mode=='limit':p['limits_mm']['capacitor_to_input']=100
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.run_proposal(p)

    def test_ic_collision_and_remote_capacitor_rejected(self):
        p = copy.deepcopy(self.proposal);key = next(iter(p['groups']));g = p['groups'][key]
        parent = next(r for r in self.placements if r['ref']==g['schmitt_ref'])
        g['placements'][key] = {k:parent[k] for k in ('x_mm','y_mm','rotation_deg')}
        with self.assertRaises(ValueError):self.run_proposal(p)
        p = copy.deepcopy(self.proposal);p['groups'][key]['placements'][key]['x_mm']=10
        with self.assertRaises(ValueError):self.run_proposal(p)

    def test_reverse_stage_grid_clearance_rejected(self):
        p = copy.deepcopy(self.proposal)
        p['groups']['C4103']['placements']['C4103']['y_mm'] = 179.5
        with self.assertRaisesRegex(ValueError, 'reverse-stage grid clearance'):
            self.run_proposal(p)

    def test_source_net_and_device_identity_change_rejected(self):
        io = copy.deepcopy(self.io)
        cap = next(u for u in io['package_units'] if u['role']=='switch_button_input:C_DB'
                   and u['ref'] in self.proposal['groups'])
        cap['pins']['2']='+5V'
        with self.assertRaises(ValueError):debounce_groups(io)
        io = copy.deepcopy(self.io)
        ref = next(iter(self.proposal['groups'].values()))['schmitt_ref']
        next(p for p in io['physical_packages'] if p['ref']==ref)['mpn']='different device'
        with self.assertRaises(ValueError):debounce_groups(io)


if __name__=='__main__':unittest.main()
