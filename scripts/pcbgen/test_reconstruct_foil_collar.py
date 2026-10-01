"""Portable preservation/authority tests; native execution is a separate gate."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.pcbgen.foil_collar_geometry import PROPOSAL,compile_proposal
from scripts.pcbgen.reconstruct_foil_collar import require_cache,island_polygon,added_ids,restore_unchanged,check_named_connectivity,declared_edit_windows,result_policy


class ReconstructFoilCollarTests(unittest.TestCase):
    def test_destinations_are_confined_to_disposable_descendants(self):
        root=Path('/tmp/proposal-test')
        for path in (root/'boards/a.kicad_pcb',root/'.circuit-cache',root/'.circuit-cache/../boards/a'):
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'descendant'):require_cache(path,root)
        self.assertEqual(require_cache(root/'.circuit-cache/new',root),root/'.circuit-cache/new')

    def test_source_union_contains_full_pad_and_nominal_sections(self):
        spec=json.loads(PROPOSAL.read_bytes());compiled=compile_proposal(spec)
        for b,recipe in zip(spec['boards'],compiled['boards']):
            p=island_polygon(recipe['proposed_geometry'])
            self.assertEqual(len(p),10)
            self.assertEqual(len(set(map(tuple,p))),10)
            self.assertEqual(set(added_ids(b)),{'collar_zone','via','tracks'} if b['board_key']=='JL' else {'collar_zone'})
            # Both collar edges and both shoulder/pad endpoints are retained.
            self.assertTrue(set(map(tuple,recipe['proposed_geometry']['collar_polygon_mm']))<=set(map(tuple,p)))

    def test_preservation_transplants_only_named_copper(self):
        old='''(kicad_pcb (version 1)
(footprint "library:fixed" (uuid "f") (property "Reference" "J1") (pad "2" smd rect (net "AGND")))
(segment (uuid "old") (net "SIGNAL") (locked yes))
(via (uuid "retired") (net "AGND"))
(zone (uuid "zone") (net "AGND") (old geometry))
)'''
        saved=old.replace('(locked yes)','(locked no)').replace('(old geometry)','(new geometry)').replace('(via (uuid "retired") (net "AGND"))','')
        saved=saved[:-1]+'(zone (uuid "added-zone") (net "AGND"))\n(segment (uuid "added-track") (net "AGND"))\n)'
        # Native UUID parser expects real UUID strings; use deterministic aliases.
        mapping={name:f'00000000-0000-0000-0000-{i:012d}' for i,name in enumerate(('f','old','retired','zone','added-zone','added-track'),1)}
        old=old.replace('(via ', '(via\n').replace('(zone ', '(zone\n')
        saved=saved.replace('(via ', '(via\n').replace('(zone ', '(zone\n')
        for key,value in mapping.items():old=old.replace('"'+key+'"','"'+value+'"');saved=saved.replace('"'+key+'"','"'+value+'"')
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'old';candidate=Path(temp)/'new';source.write_text(old);candidate.write_text(saved)
            r=restore_unchanged(source,candidate,{mapping['retired']},{'collar_zone':mapping['added-zone'],'tracks':[mapping['added-track']]},{mapping['zone']})
            self.assertIn('(locked yes)',candidate.read_text());self.assertNotIn('(locked no)',candidate.read_text())
            self.assertNotIn(mapping['retired'],candidate.read_text());self.assertEqual(r['byte_preserved_footprints'],1)
            candidate.write_text(saved.replace(mapping['added-track'],'10000000-0000-0000-0000-000000000000'))
            with self.assertRaisesRegex(ValueError,'inventory delta'):
                restore_unchanged(source,candidate,{mapping['retired']},{'collar_zone':mapping['added-zone'],'tracks':[mapping['added-track']]},{mapping['zone']})

    def test_full_named_connectivity_not_total_alone(self):
        before={'native_open_edges_by_net':{'SIGNAL_A':2,'SIGNAL_B':1},'native_unconnected_edges':3,'native_open_net_count':2}
        self.assertEqual(check_named_connectivity(before,copy.deepcopy(before))['AGND_open_edges'],0)
        changed=copy.deepcopy(before);changed['native_open_edges_by_net']={'SIGNAL_A':1,'SIGNAL_B':2}
        with self.assertRaisesRegex(ValueError,'named'):check_named_connectivity(before,changed)
        changed=copy.deepcopy(before);changed['native_open_edges_by_net']['AGND']=1
        with self.assertRaisesRegex(ValueError,'AGND'):check_named_connectivity(changed,changed)

    def test_refill_allowance_is_local_and_derived_before_delta(self):
        spec=json.loads(PROPOSAL.read_bytes());compiled=compile_proposal(spec)
        for b,recipe in zip(spec['boards'],compiled['boards']):
            windows=declared_edit_windows(b,recipe,.35)
            scan=b['snapshot']['scan_window_mm']
            for w in windows:
                self.assertTrue(scan[0]<=w[0]<w[2]<=scan[2])
                self.assertTrue(scan[1]<=w[1]<w[3]<=scan[3])
            # Old via's removal changes its finite antipad outside the pad box.
            if b['board_key']=='JL':self.assertGreater(max(w[3] for w in windows),87.8)

    def test_historical_rejected_receipt_preserves_failed_admission(self):
        # This record is historical, not an assertion that current code was
        # rerun. It remains portable without any ignored native artifacts.
        receipt=json.loads((PROPOSAL.parent/'foil-collar-native-receipt.json').read_bytes())
        self.assertTrue(receipt['status'].startswith('REJECTED'))
        self.assertTrue(receipt['local_only_is_experimental_scope_not_original_project_target'])
        for board in receipt['boards']:
            self.assertFalse(board['native_admission_gate_pass'])
            self.assertFalse(board['local_only_delta_gate_pass'])
            self.assertGreater(sum(r['outside_declared_area_mm2'] for r in board['filled_copper_delta']),0)
            self.assertEqual(board['collar_overshoot']['intersection_with_full_dry_guard_mm2'],0)
        k=next(b for b in receipt['boards'] if b['board_key']=='K')
        self.assertEqual([e['type'] for e in k['native_rule_errors']],['zones_intersect'])
        jl=next(b for b in receipt['boards'] if b['board_key']=='JL')
        self.assertTrue(jl['constructor_execution']['source_hash_guard'].startswith('FAIL'))

    def test_full_refill_scope_does_not_admit_old_local_or_electrical_gate(self):
        full=result_policy('full_refill_draft_epoch',True,False)
        self.assertTrue(full['command_scope_gate_pass'])
        self.assertTrue(full['native_rule_connectivity_gate_pass'])
        self.assertFalse(full['local_only_experiment_gate_pass'])
        self.assertFalse(full['electrical_or_physical_admission'])
        self.assertFalse(result_policy('full_refill_draft_epoch',False,True)['command_scope_gate_pass'])
        self.assertFalse(result_policy('local_only_experiment',True,False)['command_scope_gate_pass'])
        with self.assertRaisesRegex(ValueError,'unknown'):result_policy('ignore_rules',True,True)

    def test_priority_receipt_retains_old_failure_and_separate_native_scope(self):
        receipt=json.loads((PROPOSAL.parent/'foil-collar-k-priority-receipt.json').read_bytes())
        historical=json.loads((PROPOSAL.parent/'foil-collar-native-receipt.json').read_bytes())
        self.assertEqual(receipt['source_priority']['new_collar'],1)
        self.assertEqual(receipt['source_priority']['retained_target'],0)
        self.assertEqual(receipt['K']['native_rule_errors'],0)
        self.assertEqual(receipt['K']['schematic_parity_issues'],0)
        self.assertTrue(receipt['native_result_policy']['native_rule_connectivity_gate_pass'])
        self.assertFalse(receipt['native_result_policy']['local_only_experiment_gate_pass'])
        self.assertFalse(receipt['native_result_policy']['electrical_or_physical_admission'])
        old_jl=next(b for b in historical['boards'] if b['board_key']=='JL')
        self.assertEqual(receipt['JL_not_rerun']['historical_candidate_sha256'],old_jl['candidate_sha256'])
        self.assertEqual(receipt['JL_not_rerun']['historical_proposal_sha256'],historical['proposal_sha256'])
        self.assertNotEqual(receipt['source_sha256']['proposal'],historical['proposal_sha256'])


if __name__=='__main__':unittest.main()
