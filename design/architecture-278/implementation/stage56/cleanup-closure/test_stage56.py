"""Stage56 controls: candidate board schematic, field-sync and cleanup receipts, decoupling
replay, retained native receipts and acceptance-gate mutations. Source only; no KiCad execution."""
from pathlib import Path
from functools import lru_cache
import copy, hashlib, importlib.util, json, unittest
HERE = Path(__file__).resolve().parent


def load(name, file):
    s = importlib.util.spec_from_file_location(name, HERE/file); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


c = load('stage56_candidate', 'candidate.py'); d = load('stage56_decoupling', 'decoupling.py'); n = load('stage56_native', 'native.py')
EVIDENCE = HERE/'evidence'


@lru_cache(None)
def computed():
    return c.compute()


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Stage56Tests(unittest.TestCase):
    def test_candidate_schematic_receipt_replays(self):
        baseline, candidate, receipt = computed()
        self.assertEqual(receipt, json.loads((EVIDENCE/'schematic-receipt.json').read_text()))
        self.assertEqual(len(receipt['removed_refs']), 30)
        self.assertEqual(len(receipt['removed_board_net_tokens']), 48)
        self.assertEqual(sorted(r['ref'] for r in receipt['retained_bypasses']), ['C128', 'C140', 'C144', 'C228', 'C240', 'C244'])
        self.assertEqual(receipt['multi_unit_field_conflicts']['candidate'], {})
        self.assertNotEqual(receipt['multi_unit_field_conflicts']['baseline'], {})

    def test_retained_caps_are_not_removed_and_keep_identity(self):
        baseline, candidate, receipt = computed()
        self.assertFalse({r['ref'] for r in receipt['retained_bypasses']} & set(receipt['removed_refs']))
        for ref in c.RETAIN:
            self.assertTrue(any(f'"Reference" "{ref}"' in body for body in candidate.values()), ref)

    def test_field_receipt_matches_schematic_drop_set(self):
        sch = json.loads((EVIDENCE/'schematic-receipt.json').read_text())
        fields = json.loads((EVIDENCE/'fields-receipt.json').read_text())
        pairs = {tuple(x) for x in sch['dropped_unit_fields']['pairs']}
        changed = {(x['ref'], x['field']) for x in fields['changes'] if x['field'] != 'Decouples'}
        self.assertEqual(changed, pairs)
        for x in fields['changes']:
            if x['field'] == 'LogicalCellKey':
                self.assertIsNone(x['new'])
            elif x['field'] in ('Role', 'Island'):
                self.assertEqual(x['new'], '')
        self.assertEqual(fields['requested_fields_absent_on_pcb'], 0)
        self.assertEqual(fields['decouples_updates'], 6)

    def test_pcb_receipt_binds_canonical_board_and_removed_set(self):
        pcb = json.loads((EVIDENCE/'pcb-receipt.json').read_text())
        sch = json.loads((EVIDENCE/'schematic-receipt.json').read_text())
        self.assertEqual(pcb['source_sha256'], sha(n.ROOT/'boards/osc-core/osc-core.kicad_pcb'))
        self.assertEqual(sorted(r['ref'] for r in pcb['removed_footprints']), sch['removed_refs'])
        private = {r['net'] for r in pcb['deleted_copper'] if r['reason'] == 'private-net'}
        self.assertEqual(private, set(sch['removed_board_net_tokens']))
        shared = {r['net'] for r in pcb['deleted_copper'] if r['reason'] != 'private-net'}
        self.assertTrue(shared <= {'+12V', '-12V', 'AGND'})

    def test_decoupling_replays(self):
        result = d.run(check=True)
        self.assertEqual(result['survivors_whose_nearest_rail_cap_is_removed'], [])
        self.assertEqual(result['rail_nominal_reduction_uF'], {'+12V': 0.6, '-12V': 1.2})
        self.assertEqual(result['surviving_ics_without_complete_owned_bypass']['before'],
                         result['surviving_ics_without_complete_owned_bypass']['after'])

    def test_native_audit_binds_receipts(self):
        audit = json.loads((HERE/'native-audit.json').read_text())
        self.assertEqual(n.evaluate(write=False), audit)
        self.assertEqual(n.gate(audit), audit['gates'])
        self.assertEqual(audit['verdict'], 'PASS' if all(audit['gates'].values()) else 'FAIL')

    def mutated(self, fn):
        audit = copy.deepcopy(json.loads((HERE/'native-audit.json').read_text())); fn(audit); return n.gate(audit)

    def test_gate_rejects_parity_drc_and_erc_regressions(self):
        self.assertFalse(self.mutated(lambda a: a['drc'].__setitem__('schematic_parity', 1))['schematic_parity_zero'])
        self.assertFalse(self.mutated(lambda a: a['drc'].__setitem__('baseline_schematic_parity', 1))['baseline_schematic_parity_zero'])
        self.assertFalse(self.mutated(lambda a: a['drc'].__setitem__('candidate_errors', 1))['no_drc_errors'])
        self.assertFalse(self.mutated(lambda a: a['erc'].__setitem__('new_violation_signatures', 1))['erc_errors_zero_and_signatures_unchanged'])
        self.assertFalse(self.mutated(lambda a: a['oracle'].__setitem__(3, '10.0.5'))['oracle_10_0_6'])
        self.assertFalse(self.mutated(lambda a: a['drc'].__setitem__('violations_mentioning_removed_refs_or_nets', ['U112']))['no_candidate_violation_names_removed_item'])

    def test_gate_rejects_ratsnest_and_cluster_regressions(self):
        self.assertFalse(self.mutated(lambda a: a['ratsnest'].__setitem__('nets_with_more_edges', {'+12V': [1, 2]}))['complete_ratsnest_no_net_gains_edges'])
        self.assertFalse(self.mutated(lambda a: a['ratsnest'].__setitem__('new_open_nets', ['X']))['complete_ratsnest_no_new_open_net'])
        self.assertFalse(self.mutated(lambda a: a['ratsnest'].__setitem__('candidate_private_net_edges', 1))['removed_private_nets_absent_from_ratsnest'])
        self.assertFalse(self.mutated(lambda a: a['rail_clusters']['+12V'].__setitem__('split_clusters', 1))['rail_clusters_equal_baseline_minus_removed_pads'])
        self.assertFalse(self.mutated(lambda a: a['rail_clusters']['AGND'].__setitem__('identical_after_projection', False))['rail_clusters_equal_baseline_minus_removed_pads'])

    def test_gate_rejects_uncapped_new_signature(self):
        audit = json.loads((HERE/'native-audit.json').read_text())
        g = self.mutated(lambda a: a['drc']['new_violation_signatures'].__setitem__('track_dangling :: Track [+12V] on B.Cu', 1))
        self.assertEqual(g['no_new_uncapped_drc_signatures'], 'track_dangling' in audit['drc']['capped_types_at_199'])


if __name__ == '__main__':
    unittest.main()
