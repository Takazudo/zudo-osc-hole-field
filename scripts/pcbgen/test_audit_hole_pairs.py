import itertools
import random
import unittest
import tempfile
from pathlib import Path
from scripts.pcbgen.audit_hole_pairs import possible_pairs, pack_pairs
from scripts.pcbgen.audit_hole_pairs import restore_fixture_context, verify_fixture_context
from scripts.pcbgen.compare_hole_audits import compare
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting, new_silk_identities


class HoleCoverageTests(unittest.TestCase):
    def test_native_new_board_project_reset_must_be_restored_and_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.kicad_pcb';fixture=root/'fixture.kicad_pcb'
            for suffix in ('.kicad_pro','.kicad_dru'):
                source.with_suffix(suffix).write_text('reviewed constraints and netclasses')
                fixture.with_suffix(suffix).write_text('native new BOARD defaults')
            with self.assertRaisesRegex(ValueError,'context changed'):
                verify_fixture_context(source,fixture)
            restore_fixture_context(source,fixture)
            verify_fixture_context(source,fixture)
            fixture.with_suffix('.kicad_pro').write_text('changed again during native processing')
            with self.assertRaisesRegex(ValueError,'context changed'):
                verify_fixture_context(source,fixture)

    def test_copper_layer_silk_warning_is_not_missed(self):
        row=dict(type='silk_overlap',severity='warning',items=[{'uuid':'via'},{'uuid':'text'}])
        self.assertEqual(new_silk_identities({'violations':[row]},'via'),[row])

    def test_old_silk_cap_cannot_hide_new_via_warning(self):
        row=dict(type='silk_overlap',severity='warning',items=[{'uuid':'old-a'},{'uuid':'old-b'}])
        with self.assertRaises(ValueError):new_silk_identities({'violations':[row]*199},'new-via')

    def test_added_mask_scope_rejects_changed_artwork_or_removed_copper(self):
        before='(kicad_pcb (footprint "U1" (fp_text "unchanged")) (via (at 1 2)))'
        after=before[:-1]+' (via (at 3 4)))'
        self.assertEqual(unchanged_nonrouting(before,after),1)
        with self.assertRaises(ValueError):unchanged_nonrouting(before,after.replace('unchanged','moved'))
        with self.assertRaises(ValueError):unchanged_nonrouting(before,after.replace('(via (at 1 2))',''))

    def test_spatial_cover_matches_all_pairs_with_negative_coordinates_and_large_drills(self):
        rng = random.Random(189)
        holes = [dict(xy=[rng.randrange(-5000000,5000000) for _ in range(2)],
                      radius=rng.choice([150000,400000,1100000])) for _ in range(300)]
        clearance = 250000
        expected = {(a,b) for a,b in itertools.combinations(range(len(holes)),2)
                    if sum((x-y)**2 for x,y in zip(holes[a]['xy'],holes[b]['xy']))
                    <= (clearance+holes[a]['radius']+holes[b]['radius'])**2}
        self.assertEqual(set(possible_pairs(holes,clearance)),expected)

    def test_dense_fixture_cover_cannot_reach_199_pair_cap(self):
        pairs = list(itertools.combinations(range(50),2))
        groups = pack_pairs(pairs)
        self.assertGreater(len(pairs),199)
        self.assertTrue(all(len(g)*(len(g)-1) < 199 for g in groups))
        self.assertTrue(all(any(set(p)<=set(g) for g in groups) for p in pairs))

    def test_boundary_and_colocated_pairs_are_covered(self):
        holes=[dict(xy=p,radius=150000) for p in [[0,0],[550000,0],[550001,0],[0,0]]]
        pairs=set(possible_pairs(holes,250000))
        self.assertIn((0,1),pairs); self.assertNotIn((0,2),pairs); self.assertIn((0,3),pairs)

    def test_oversized_fixture_refused(self):
        with self.assertRaises(ValueError):pack_pairs([(0,1)],15)

    def test_duplicate_uuid_objects_are_kept_in_separate_fixtures(self):
        pairs=[(0,1),(2,3)]
        self.assertEqual(pack_pairs(pairs,uuids=['duplicate','b','duplicate','d']),[[0,1],[2,3]])
        with self.assertRaises(ValueError):pack_pairs([(0,2)],uuids=['duplicate','b','duplicate'])

    def test_hidden_new_warning_is_not_lost_when_full_report_is_capped(self):
        old=('hole_to_hole','warning',('old-a','old-b'))
        new=('hole_to_hole','warning',('new-a','new-b'))
        context=dict(version='10.0.6',project_sha256='p',rules_sha256='r',
                     clearance_nm=250000,source_sha256='b')
        capped={'violations':[dict(type=old[0],severity=old[1],items=[{'uuid':u} for u in old[2]])]}
        result=compare(dict(context,identities=[old],object_identities=[old]),dict(context,identities=[old,new],object_identities=[old,new]),capped,capped)
        self.assertEqual(result['new_identities'],[new])

    def test_missing_original_native_identity_fails_closed(self):
        context=dict(version='10.0.6',project_sha256='p',rules_sha256='r',
                     clearance_nm=250000,source_sha256='b',identities=[],object_identities=[])
        report={'violations':[dict(type='hole_to_hole',severity='warning',items=[{'uuid':'a'},{'uuid':'b'}])]}
        with self.assertRaises(ValueError):compare(context,context,report,report)

    def test_same_uuid_identity_cannot_hide_a_different_hole_pair(self):
        uuid_identity=('hole_to_hole','warning',('duplicate','other'))
        old_object=('hole_to_hole','warning',('geometry-a','geometry-b'))
        new_object=('hole_to_hole','warning',('geometry-c','geometry-b'))
        context=dict(version='10.0.6',project_sha256='p',rules_sha256='r',
                     clearance_nm=250000,source_sha256='b',identities=[uuid_identity])
        report={'violations':[]}
        result=compare(dict(context,object_identities=[old_object]),
                       dict(context,object_identities=[old_object,new_object]),report,report)
        self.assertEqual(result['new_identities'],[])
        self.assertEqual(result['new_object_identities'],[new_object])


if __name__=='__main__':unittest.main()
