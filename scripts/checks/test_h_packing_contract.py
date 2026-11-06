"""Regression and mutation tests for the pinned H1/H2 source distinction."""
import copy
import json
import unittest
from scripts.checks import h_packing_contract as contract


class HPackingContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(contract.FIXTURE.read_text())

    def test_live_repository_matches_reviewed_source(self):
        contract.validate(contract.repository_snapshot(), self.fixture['repository'], 'repository')

    def test_lineage_explains_the_repin_exactly(self):
        contract.validate_lineage(self.fixture)

    def test_unlisted_package_change_breaks_lineage(self):
        changed = copy.deepcopy(self.fixture)
        next(r for r in changed['repository']['channels'] if r['ref'] == 'U102')['device'] = 'OPA4197IDR'
        with self.assertRaisesRegex(ValueError, 'lineage'):
            contract.validate_lineage(changed)

    def test_lineage_cannot_absorb_a_net_change(self):
        changed = copy.deepcopy(self.fixture)
        row = next(r for r in changed['repository']['channels'] if r['ref'] == 'U103' and not r['spare'])
        row['nets'][2] = 'AGND'
        with self.assertRaisesRegex(ValueError, 'lineage'):
            contract.validate_lineage(changed)

    def test_only_documented_device_difference_in_active_channels(self):
        def active(snapshot):
            return {(r['instance'], r['ref'], r['unit'], tuple(r['nets'])): r['device']
                    for r in snapshot['channels'] if not r['spare']}
        source = active(self.fixture['repository'])
        self.assertEqual(len(source), 22)
        # The variants are retained pre-S2b candidate evidence, so the source now also differs by
        # the S2b OPA4197IPWR->OPA4197IDR package change recorded in fixture['lineage'].
        lineage = self.fixture['lineage']['package_change']
        s2b_refs = {tuple(r) for r in lineage['refs']}
        s2b = {(i, ref, lineage['to'], lineage['from'])
               for (i, ref, _, _), device in source.items() if (i, ref) in s2b_refs}
        self.assertEqual({(i, ref) for i, ref, _, _ in s2b},
                         {('H1', 'U103'), ('H1', 'U104'), ('H2', 'U203'), ('H2', 'U204')})
        for name, candidate in self.fixture['variants'].items():
            with self.subTest(variant=name):
                other = active(candidate)
                self.assertEqual(source.keys(), other.keys())
                changes = {(k[0], k[1], source[k], other[k]) for k in source if source[k] != other[k]}
                self.assertEqual(changes, {('H1', 'U110', 'OPA4196IDR', 'TL074HIDR'),
                                           ('H2', 'U210', 'OPA4196IDR', 'TL074HIDR')} | s2b)
                self.assertEqual(candidate['ic_packages'], 26)
        self.assertEqual(self.fixture['repository']['ic_packages'], 38)

    def test_signal_pin_swap_is_rejected(self):
        changed = copy.deepcopy(self.fixture['repository'])
        row = next(r for r in changed['channels'] if not r['spare'] and r['nets'][1] != r['nets'][2])
        row['nets'][1], row['nets'][2] = row['nets'][2], row['nets'][1]
        with self.assertRaisesRegex(ValueError, 'channels drift'):
            contract.validate(changed, self.fixture['repository'], 'mutant')

    def test_spare_removal_cannot_silently_redefine_repository(self):
        changed = copy.deepcopy(self.fixture['repository'])
        changed['channels'].remove(next(r for r in changed['channels'] if r['ref'] == 'U112'))
        with self.assertRaisesRegex(ValueError, 'channels drift'):
            contract.validate(changed, self.fixture['repository'], 'mutant')

    def test_candidate_device_change_is_rejected(self):
        expected = self.fixture['variants']['UNI_ROYAL/BA1']
        changed = copy.deepcopy(expected)
        next(r for r in changed['channels'] if r['ref'] == 'U110')['device'] = 'OPA4196IDR'
        with self.assertRaisesRegex(ValueError, 'channels drift'):
            contract.validate(changed, expected, 'mutant')

    def test_removed_packages_are_exactly_grounded_spares(self):
        source = self.fixture['repository']['channels']
        for candidate in self.fixture['variants'].values():
            refs = {r['ref'] for r in candidate['channels']}
            removed = [r for r in source if r['ref'] not in refs]
            self.assertEqual(len(removed), 48)
            self.assertEqual(len({r['ref'] for r in removed}), 12)
            self.assertTrue(all(r['spare'] for r in removed))

    def test_candidate_net_scope_change_is_rejected(self):
        expected = self.fixture['variants']['UNI_ROYAL/BA1']
        changed = copy.deepcopy(expected)
        changed['channels'][0]['pin_scopes']['1'][1] = 'WRONG_HIERARCHY'
        with self.assertRaisesRegex(ValueError, 'channels drift'):
            contract.validate(changed, expected, 'mutant')

    def test_supply_change_is_rejected(self):
        changed = copy.deepcopy(self.fixture['repository'])
        changed['supplies'][0]['pins']['11'] = 'AGND'
        with self.assertRaisesRegex(ValueError, 'supplies drift'):
            contract.validate(changed, self.fixture['repository'], 'mutant')


if __name__ == '__main__':
    unittest.main()
