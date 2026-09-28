"""Adversarial package, net, geometry and power-budget gates for the draft."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts.checks import partition35
from scripts.checks.connector_packing35 import rect_collision
from scripts.checks.partition35_floorplan import Grid
ROOT=Path(__file__).resolve().parents[2]


class PartitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.io=json.loads((ROOT/'design/reports/io-partition.json').read_text())
        cls.parts=cls.io['physical_packages']
        cls.rows=json.loads((ROOT/'design/partition/partition.json').read_text())['assignment']['components']

    def test_manifest_numeric_family_keys_remain_valid_json(self):
        from scripts.checks.partition35_json import dumps
        self.assertEqual(json.loads(dumps({'families':{3:{'pins':3}}})),{'families':{'3':{'pins':3}}})

    def test_missing_duplicate_unknown_package_rejected(self):
        for rows in (self.rows[:-1],self.rows+[self.rows[0]],self.rows+[{'ref':'FICTION','board':'J'}]):
            self.assertTrue(partition35.validate_assignment(self.parts,rows,self.io))

    def test_sensitive_component_move_rejected(self):
        net=next(r for r in self.io['local_raw_sensitive_nets'] if r['net']=='/H1/SLEW_STORAGE')
        ref=next(r for r in net['refs'] if r.startswith('C'))
        rows=[{**r,'board':'K'} if r['ref']==ref else r for r in self.rows]
        self.assertTrue(any('sensitive' in e for e in partition35.validate_assignment(self.parts,rows,self.io)))

    def test_package_bypass_move_rejected(self):
        cap=next(p for p in self.parts if p['decouples_ref'] and p['regions']==['stage_optical'])
        rows=[{**r,'board':'K'} if r['ref']==cap['ref'] else r for r in self.rows]
        self.assertTrue(any('bypass' in e for e in partition35.validate_assignment(self.parts,rows,self.io)))

    def test_wire_loss_overrun_cannot_pass(self):
        original=partition35.read
        def altered(path):
            row=original(path)
            if path=='design/partition/partition-input.json':row['load_distribution']['max_wire_length_mm']=1000
            return row
        with patch.object(partition35,'read',altered):report,_=partition35.build()
        self.assertIn('load distribution exceeds 20 mV',report['checks']['errors'])

    def test_shared_ground_neck_requires_extra_dedicated_returns(self):
        original=partition35.read
        def altered(path):
            row=original(path)
            if path=='design/partition/partition-input.json':
                row['load_distribution']['net_order']=['+12V','-12V','+5V','AGND']
            return row
        with patch.object(partition35,'read',altered):report,_=partition35.build()
        self.assertIn('GH return derating exceeded P',report['checks']['errors'])
        self.assertIn('GH return derating exceeded J',report['checks']['errors'])

    def test_capacitance_is_consumed_from_current_report(self):
        original=partition35.read
        def altered(path):
            row=original(path)
            if path=='design/power/supply-architecture.json':row['implementation']['actual_fitted_capacitor_inventory']['+12V']['captured_fitted_nominal_uF']=140
            return row
        with patch.object(partition35,'read',altered):report,_=partition35.build()
        self.assertIn('bulk capacitance exceeds rail ceiling',report['checks']['errors'])

    def test_j_bulk_reserve_duplicate_source_geometry_must_match(self):
        board=partition35.read('design/partition/partition-input.json')['boards']['J']
        self.assertEqual(partition35.bulk_reserve_source_errors(board),[])
        board['board_bulk_reserve'][0]['rect'][0]+=.5
        self.assertIn('UNSELECTED-BULK-1 geometry differs between reserves and board_bulk_reserve',partition35.bulk_reserve_source_errors(board))

    def test_exact_selector_contact_choice(self):
        gh=json.loads((ROOT/'design/connectors/jst-gh.json').read_text())
        bounds={p['positions']:p['header_courtyard_xy_mm'][2] for p in gh['sizes']}
        self.assertAlmostEqual(6.7-bounds[7],.35)
        self.assertAlmostEqual(bounds[8]-6.7,.27)

    def test_asymmetric_back_face_origin_is_mirrored(self):
        grid=Grid('K','B.Cu',[])
        row=grid.place([1,2,3,5])
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row['x_mm']-3,row['courtyard_mm'][0])
        self.assertAlmostEqual(row['x_mm']-1,row['courtyard_mm'][2])

    def test_fixed_coordinate_drift_rejected(self):
        original=partition35.read
        def altered(path):
            row=original(path)
            if path=='design/grid/placements.lock.json':row['placements'][0]['x_mm']+=.01
            return row
        with patch.object(partition35,'read',altered):report,_=partition35.build()
        self.assertIn('fixed UID/XY source digest drift',report['checks']['errors'])


if __name__=='__main__':unittest.main()
