"""Reject unbuildable wire cuts and stale depth/geometry budget receipts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.checks import connector_packing35,partition35,partition35_loom
from scripts.checks.connector_packing35 import core_service_depths,partition_source_digest
from scripts.checks.partition35_loom import ROOT,power_cut_requirement,power_route_errors


class ArchitectureMarginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads((ROOT/'design/partition/partition-input.json').read_text())
        cls.loom=json.loads((ROOT/'design/partition/loom-candidate.json').read_text())

    def test_cut_allows_complete_path_and_ten_mm_preparation(self):
        source=copy.deepcopy(self.source)
        self.assertEqual(power_route_errors(self.loom['load_power_routes'],source),[])
        longest=max(r['minimum_cut_length_mm'] for r in self.loom['load_power_routes'])
        self.assertAlmostEqual(longest,100.9070593291981,places=6)
        source['load_distribution']['max_wire_length_mm']=100
        self.assertTrue(any('power wire length exceeds loss budget POWER-JL-' in e for e in power_route_errors(self.loom['load_power_routes'],source)))
        self.assertEqual(power_cut_requirement([[0,0,0],[0,0,25]],40)['minimum_cut_length_mm'],35)

    def test_actual_points_cannot_borrow_a_shorter_reported_length(self):
        routes=copy.deepcopy(self.loom['load_power_routes'])
        routes[0]['points_mm_positive_rear'][50][0]+=100
        errors=power_route_errors(routes,self.source)
        self.assertTrue(any('receipt differs from source/geometry' in e for e in errors))
        self.assertTrue(any('length exceeds loss budget' in e for e in errors))

    def test_missing_duplicate_or_nonfinite_route_rejected(self):
        routes=self.loom['load_power_routes']
        for changed in (routes[:-1],routes+[routes[0]]):
            self.assertIn('power route inventory differs from source',power_route_errors(changed,self.source))
        for maximum in (0,-1,float('nan'),float('inf')):
            with self.assertRaisesRegex(ValueError,'invalid power wire'):
                power_cut_requirement([[0,0,0],[0,0,25]],maximum)

    def test_source_ceiling_reaches_every_generated_wire(self):
        report,_=partition35.build()
        self.assertEqual(report['checks']['errors'],[])
        self.assertEqual({w['maximum_length_mm'] for w in report['load_side_wires']},{110})
        self.assertEqual({w['max_cut_length_mm'] for w in self.loom['load_power_routes']},{110})
        self.assertAlmostEqual(report['power']['worst_load_distribution_drop_mV']['+12V'],15.321)
        self.assertLess(report['power']['GH_normal_return_bounds']['JL']['worst_single_contact_A'],.482)

    def test_changed_source_cannot_consume_old_loom_or_connector_receipt(self):
        original=partition35.read
        def altered(path):
            result=original(path)
            if path=='design/partition/partition-input.json':result['boards']['K']['face_z_mm']=-99
            return result
        with patch.object(partition35,'read',altered):report,_=partition35.build()
        for name in ('loom','connectors'):
            self.assertIn(name+': partition source digest drift',report['checks']['errors'])

    def test_service_depths_move_with_core_and_enclosure(self):
        self.assertEqual(core_service_depths(self.source),{'support_mm':[98,120],'hook_mm':[90.5,94]})
        changed=copy.deepcopy(self.source)
        changed['boards']['K']['face_z_mm']=-80
        changed['enclosure']['inside_depth_mm']=100
        self.assertEqual(core_service_depths(changed),{'support_mm':[78,100],'hook_mm':[70.5,74]})
        self.assertNotEqual(partition_source_digest(changed),partition_source_digest(self.source))
        changed['enclosure']['inside_depth_mm']=80
        with self.assertRaisesRegex(ValueError,'invalid K support/tool'):
            core_service_depths(changed)

    def test_generated_depth_receipts_follow_a_changed_plane(self):
        changed=copy.deepcopy(self.source)
        changed['boards']['K']['face_z_mm']=-96
        changed['enclosure']['inside_depth_mm']=116
        with patch.object(connector_packing35,'source',return_value=changed):
            connectors=connector_packing35.candidate()
        self.assertEqual({tuple(a['hook_sweep_positive_depth_mm']) for a in connectors['K_service_apertures']},{(86.5,90)})
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for relative in ('design/connectors/jst-gh.json','design/partition/stage-optical-candidate.json'):
                target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/relative).read_bytes())
            (root/'design/partition/partition-input.json').write_text(json.dumps(changed))
            (root/'design/partition/connector-packing-candidate.json').write_text(json.dumps(connectors))
            with patch.object(partition35_loom,'ROOT',root):result=partition35_loom.build()
        self.assertEqual(result['errors'],[])
        self.assertEqual(result['K_service_depths_positive_rear_mm'],{'support_mm':[94,116],'hook_mm':[86.5,90]})
        # This is route geometry only; the shorter GH paths need a new
        # electrical screen and cannot inherit the selected K100 current bound.

    def test_invalid_service_offsets_are_not_a_fit_pass(self):
        for offsets in ([9.5,6],[-1,9.5],[6,float('nan')],[6,101]):
            changed=copy.deepcopy(self.source)
            changed['boards']['K']['service_access']['hook_forward_offsets_mm']=offsets
            with self.assertRaisesRegex(ValueError,'invalid K support/tool'):
                core_service_depths(changed)


if __name__=='__main__':unittest.main()
