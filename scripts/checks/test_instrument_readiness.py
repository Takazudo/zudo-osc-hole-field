"""Negative controls for actual membership, identity and stale native evidence risks."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.checks import instrument_readiness as readiness
from scripts.checks.bom_readiness import build as historical_build


class ReadinessTests(unittest.TestCase):
    def test_dual_transistor_units_count_as_one_physical_package(self):
        packages, excluded = readiness.physical_source()
        self.assertEqual(len(packages), 6106)
        self.assertEqual(sum(not p['dnp'] and p['in_bom'] for p in packages.values()), 6098)
        self.assertEqual(historical_build()['placements_per_unit'], 6098)
        self.assertEqual(excluded['abstract_boundary'], ['CN301', 'XB301'])

    def test_membership_preserves_missing_and_unexpected_references(self):
        self.assertEqual(readiness.membership({'U1','R1'}, {'U1','R2'}),
                         {'missing':['R1'], 'unexpected':['R2']})

    def test_duplicate_native_reference_rejected(self):
        footprint = '(footprint "lib:part" (property "Reference" "U1"))'
        with self.assertRaisesRegex(ValueError, 'duplicate footprint reference'):
            readiness.footprints('(kicad_pcb ' + footprint + footprint + ')')

    def test_quoted_parentheses_do_not_hide_membership(self):
        board = '(kicad_pcb (footprint "lib:(part)" (property "Reference" "R1") (property "Value" "a(b)")))'
        self.assertEqual(set(readiness.footprints(board)), {'R1'})
        with self.assertRaisesRegex(ValueError, 'unbalanced'):
            readiness.footprints(board[:-1])

    def test_geometry_and_dnp_are_not_procurement_counts(self):
        self.assertEqual(readiness.classify({'Manufacturer':'Project CAD feature','MPN':'TEST_PAD_D1.5MM'}), 'non_procured_geometry')
        self.assertEqual(readiness.classify({'dnp':'','MPN':'x','Manufacturer':'y'}), 'dnp')
        self.assertEqual(readiness.classify({'exclude_from_bom':''}), 'non_procured_geometry')
        self.assertEqual(readiness.classify({'MPN':'x'}), 'fitted_identity_incomplete')

    def test_stale_board_cannot_inherit_zero_open_edges_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'board').write_text('original')
            report = {'native_board_sha256':readiness.digest(root/'board'), 'native_unconnected_edge_count':0}
            (root/'report').write_text(json.dumps(report))
            self.assertEqual(readiness.retained_connectivity(root,'board','report')['status'], 'MATCHED BOARD BYTES')
            (root/'board').write_text('changed copper')
            self.assertEqual(readiness.retained_connectivity(root,'board','report')['status'], 'STALE OR UNBOUND')

    def test_metadata_successor_binds_only_its_own_adopted_bytes(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'board').write_text('successor')
            (root/'report').write_text(json.dumps({'native_board_sha256': 'a'*64, 'native_unconnected_edge_count': 0}))
            successor = {'adopted': {'sha256': 'a'*64}, 'path': 'r.json', 'receipt_sha256': 'b'*64}
            with mock.patch.object(readiness, 'successor_for', return_value=successor):
                result = readiness.retained_connectivity(root, 'board', 'report')
            self.assertEqual(result['status'], 'MATCHED ADOPTED BYTES VIA METADATA-ONLY SUCCESSOR')
            self.assertEqual(result['metadata_successor'], {'path': 'r.json', 'sha256': 'b'*64})
            with mock.patch.object(readiness, 'successor_for', return_value={**successor, 'adopted': {'sha256': 'c'*64}}):
                self.assertEqual(readiness.retained_connectivity(root, 'board', 'report')['status'], 'STALE OR UNBOUND')
            with mock.patch.object(readiness, 'successor_for', return_value=None):
                self.assertEqual(readiness.retained_connectivity(root, 'board', 'report')['status'], 'STALE OR UNBOUND')

    def test_current_state_uses_complete_edges_not_capped_drc(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'board').write_text('board')
            report = {'schema':'osc-current-native-state-1', 'source':{'input_board_sha256':readiness.digest(root/'board')},
                      'native':{'open_edges':2518,'drc_unconnected_items_listed':499}}
            (root/'report').write_text(json.dumps(report))
            self.assertEqual(readiness.retained_connectivity(root,'board','report')['complete_native_open_edges'], 2518)

    def test_saved_report_hashes_detect_input_drift(self):
        report = json.loads((readiness.ROOT/readiness.OUTPUT).read_text())
        self.assertIn('design/standard/electrical-standard.json', report['source_sha256'])
        self.assertIn('design/standard/parts-shortlist.json', report['source_sha256'])
        self.assertIn('scripts/schgen/project_boards.py', report['source_sha256'])
        self.assertEqual(report['reconciliation']['discrepancy_count'], 0)
        for path, digest in report['source_sha256'].items():
            self.assertEqual(readiness.digest(readiness.ROOT/path), digest, path)
        self.assertEqual(set(u['key'] for u in report['units']), {'JL','JR','K','P','EL','O1','O2','O3','O4','O5'})
        self.assertIn('candidate', next(u for u in report['units'] if u['key']=='P')['adoption'])
        for unit in report['units']:
            self.assertEqual(unit['partition_netlist_membership'], {'missing':[], 'unexpected':[]})
            self.assertEqual(unit['netlist_pcb_membership'], {'missing':[], 'unexpected':[]})
            self.assertEqual(unit['field_discrepancies'], [])


if __name__ == '__main__':
    unittest.main()
