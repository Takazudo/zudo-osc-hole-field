import copy
import json
from pathlib import Path
import unittest
from scripts.checks.control_bypass_locality import apply_bypass_locality
from scripts.checks.partition35_floorplan import footprint_geometry


class ControlBypassLocalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = lambda p: json.loads(Path(p).read_text())
        cls.io = read('design/reports/io-partition.json')
        cls.placements = read('design/partition/floorplan-candidate.json')['placements']
        cls.source = read('design/partition/partition-input.json')
        cls.connectors = read('design/partition/connector-packing-candidate.json')
        cls.lock = {p['uid']: p for p in read('design/grid/placements.lock.json')['placements']}
        cls.shapes = {p['footprint']: footprint_geometry(Path('footprints/kicad/zudo-osc-hole-field.pretty') /
            (p['footprint'].split(':')[1]+'.kicad_mod'))['courtyard_bbox_mm'] for p in cls.io['physical_packages']}
        cls.proposal = read('design/partition/control-bypass-locality.json')
        cls.optical = read('design/partition/stage-optical-input.json')
        cls.slew = read('design/partition/control-locality.json')

    def run_proposal(self, proposal):
        return apply_bypass_locality(self.placements, self.io, self.source,
            self.connectors, self.lock, self.shapes, proposal, self.optical, self.slew)

    def test_complete_bypass_closures_preserve_all_other_geometry(self):
        placed, report = self.run_proposal(self.proposal)
        refs = set(report['moved_references'])
        self.assertEqual(len(refs), 22)
        self.assertEqual(len(report['pairs']), 16)
        self.assertLessEqual(report['maximum_supply_pad_distance_mm'], 3)
        self.assertEqual([p for p in placed if p['ref'] not in refs],
                         [p for p in self.placements if p['ref'] not in refs])
        self.assertTrue(all(p['side']=='B.Cu' and not p['fixed'] for p in placed if p['ref'] in refs))

    def test_missing_capacitor_or_parent_group_rejected(self):
        p = copy.deepcopy(self.proposal)
        parent = next(iter(p['groups']))
        p['groups'].pop(parent)
        with self.assertRaises(ValueError): self.run_proposal(p)
        p = copy.deepcopy(self.proposal)
        parent = next(iter(p['groups']))
        cap = next(ref for ref in p['groups'][parent]['placements'] if ref != parent)
        p['groups'][parent]['placements'].pop(cap)
        with self.assertRaises(ValueError): self.run_proposal(p)

    def test_nonfinite_and_remote_capacitor_rejected(self):
        for bad in (float('nan'), float('inf'), True, 310):
            p = copy.deepcopy(self.proposal)
            parent = next(iter(p['groups']))
            cap = next(ref for ref in p['groups'][parent]['placements'] if ref != parent)
            p['groups'][parent]['placements'][cap]['x_mm'] = bad
            with self.subTest(value=bad), self.assertRaises(ValueError): self.run_proposal(p)

    def test_capacitor_parent_collision_and_fixed_hardware_rejected(self):
        p = copy.deepcopy(self.proposal)
        parent = next(iter(p['groups']))
        cap = next(ref for ref in p['groups'][parent]['placements'] if ref != parent)
        p['groups'][parent]['placements'][cap] = dict(p['groups'][parent]['placements'][parent])
        with self.assertRaises(ValueError): self.run_proposal(p)
        p = copy.deepcopy(self.proposal)
        p['groups'][parent]['placements'][cap] = {'x_mm':133.5, 'y_mm':269, 'rotation_deg':0}
        with self.assertRaises(ValueError): self.run_proposal(p)


if __name__ == '__main__': unittest.main()
