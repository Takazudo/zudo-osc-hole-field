"""Stage55 controls: candidate board schematic, decoupling replay, retained native receipts
and acceptance-gate mutations. Source only; no KiCad execution."""
from pathlib import Path
from functools import lru_cache
import copy, hashlib, importlib.util, json, unittest
HERE = Path(__file__).resolve().parent


def load(name, file):
    s = importlib.util.spec_from_file_location(name, HERE/file); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


c = load('stage55_candidate', 'candidate.py'); d = load('stage55_decoupling', 'decoupling.py'); n = load('stage55_native', 'native.py')
EVIDENCE = HERE/'evidence'


@lru_cache(None)
def computed():
    return c.compute()


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Stage55Tests(unittest.TestCase):
    def test_candidate_schematic_receipt_replays(self):
        baseline, candidate, receipt = computed()
        self.assertEqual(receipt, json.loads((EVIDENCE/'schematic-receipt.json').read_text()))
        self.assertEqual(receipt['changed_board_schematic_files'], ['sheets/sample_hold_H1_K.kicad_sch', 'sheets/sample_hold_H2_K.kicad_sch'])
        self.assertEqual(len(receipt['removed_refs']), 36)
        self.assertEqual(len(receipt['removed_board_net_tokens']), 48)

    def test_unchanged_sheets_are_identical(self):
        baseline, candidate, receipt = computed()
        for name in baseline:
            if name not in receipt['changed_board_schematic_files']:
                self.assertEqual(baseline[name], candidate[name], name)

    def test_filtered_partition_rejects_unknown_ref(self):
        with self.assertRaisesRegex(ValueError, 'missing from canonical assignment'):
            c.filtered_partition({'U99999'})

    def test_decoupling_replays(self):
        result = d.run(check=True)
        self.assertEqual(result['rail_nominal_reduction_uF'], {'+12V': 1.2, '-12V': 1.2})
        self.assertEqual(result['surviving_ics_without_complete_owned_bypass']['before'],
                         result['surviving_ics_without_complete_owned_bypass']['after'])

    def test_pcb_receipt_binds_schematic_receipt_and_canonical_board(self):
        pcb = json.loads((EVIDENCE/'pcb-receipt.json').read_text())
        sch = json.loads((EVIDENCE/'schematic-receipt.json').read_text())
        self.assertEqual(sorted(r['ref'] for r in pcb['removed_footprints']), sch['removed_refs'])
        self.assertEqual(pcb['source_sha256'], sha(n.ROOT/'boards/osc-core/osc-core.kicad_pcb'))
        private = {r['net'] for r in pcb['deleted_copper'] if r['reason'] == 'private-net'}
        self.assertEqual(private, set(sch['removed_board_net_tokens']))
        shared = {r['net'] for r in pcb['deleted_copper'] if r['reason'] != 'private-net'}
        self.assertTrue(shared <= {'+12V', '-12V', 'AGND'})

    def test_native_audit_binds_receipts(self):
        audit = json.loads((HERE/'native-audit.json').read_text())
        pcb = json.loads((EVIDENCE/'pcb-receipt.json').read_text())
        self.assertEqual(audit['pcb_removal']['candidate_pcb_sha256'], pcb['output_sha256'])
        for side in n.SIDES:
            for kind in ('erc', 'drc'):
                r = json.loads((EVIDENCE/f'{side}-{kind}.execution.json').read_text())
                self.assertEqual(r['returncode'], 0); self.assertTrue(r['inputs_unchanged'])
                self.assertEqual(r['command'], n.commands(side)[kind])
        self.assertEqual(n.gate(audit), audit['gates'])
        self.assertEqual(audit['verdict'], 'PASS' if all(audit['gates'].values()) else 'FAIL')

    def mutated(self, fn):
        audit = copy.deepcopy(json.loads((HERE/'native-audit.json').read_text())); fn(audit); return n.gate(audit)

    def test_gate_rejects_new_drc_error(self):
        g = self.mutated(lambda a: a['drc'].__setitem__('candidate_errors', 1))
        self.assertFalse(g['no_drc_errors'])

    def test_gate_rejects_parity_and_ratsnest_regressions(self):
        g = self.mutated(lambda a: a['drc'].__setitem__('parity_items_not_preexisting_ambiguity', ['Field Value differs']))
        self.assertFalse(g['candidate_parity_only_preexisting_unit_field_ambiguity'])
        self.assertFalse(self.mutated(lambda a: a['drc'].__setitem__('schematic_parity', [1, 1]))['baseline_schematic_parity_zero'])
        self.assertFalse(self.mutated(lambda a: a['ratsnest'].__setitem__('nets_with_more_edges', {'+12V': [1, 2]}))['complete_ratsnest_no_net_gains_edges'])
        self.assertFalse(self.mutated(lambda a: a['ratsnest'].__setitem__('new_open_nets', ['X']))['complete_ratsnest_no_new_open_net'])
        self.assertFalse(self.mutated(lambda a: a['ratsnest'].__setitem__('candidate_private_net_edges', 1))['removed_private_nets_absent_from_ratsnest'])

    def test_parity_classifier(self):
        conflicts = {'baseline': {'Role': ['U111']}, 'candidate': {'Role': ['U111']}}
        item = lambda desc, ref: {'type': 'footprint_symbol_field_mismatch', 'description': desc, 'items': [{'description': 'Footprint '+ref}]}
        self.assertEqual(n.parity_unexplained([item("Field 'Role' differs (PCB: 'a', Schematic: 'b')", 'U111')], conflicts), [])
        self.assertEqual(len(n.parity_unexplained([item("Field 'Role' differs (PCB: 'a', Schematic: 'b')", 'U101')], conflicts)), 1)
        self.assertEqual(len(n.parity_unexplained([item("Field 'Value' differs (PCB: 'a', Schematic: 'b')", 'U111')], conflicts)), 1)
        self.assertEqual(len(n.parity_unexplained([{'type': 'missing_footprint', 'description': 'Missing footprint U9', 'items': []}], conflicts)), 1)

    def test_gate_rejects_uncapped_new_signature_and_removed_item_mention(self):
        g = self.mutated(lambda a: a['drc']['new_violation_signatures'].__setitem__('track_dangling :: Track [+12V] on B.Cu', 1))
        self.assertEqual(g['no_new_uncapped_drc_signatures'], 'track_dangling' in json.loads((HERE/'native-audit.json').read_text())['drc']['capped_types_at_199'])
        g = self.mutated(lambda a: a['drc']['violations_mentioning_removed_refs_or_nets'].__setitem__('candidate', ['U112']))
        self.assertFalse(g['no_candidate_violation_names_removed_item'])

    def test_gate_rejects_new_erc_signature_and_wrong_oracle(self):
        self.assertFalse(self.mutated(lambda a: a['erc'].__setitem__('new_violation_signatures', 1))['no_new_erc_signatures'])
        self.assertFalse(self.mutated(lambda a: a['oracle'].__setitem__('drc', ['10.0.6', '10.0.5']))['oracle_10_0_6'])


if __name__ == '__main__':
    unittest.main()
