import itertools
import random
import unittest
from scripts.pcbgen.audit_hole_pairs import possible_pairs, pack_pairs
from scripts.pcbgen.compare_hole_audits import compare


class HoleCoverageTests(unittest.TestCase):
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

    def test_hidden_new_warning_is_not_lost_when_full_report_is_capped(self):
        old=('hole_to_hole','warning',('old-a','old-b'))
        new=('hole_to_hole','warning',('new-a','new-b'))
        context=dict(version='10.0.6',project_sha256='p',rules_sha256='r',
                     clearance_nm=250000,source_sha256='b')
        capped={'violations':[dict(type=old[0],severity=old[1],items=[{'uuid':u} for u in old[2]])]}
        result=compare(dict(context,identities=[old]),dict(context,identities=[old,new]),capped,capped)
        self.assertEqual(result['new_identities'],[new])

    def test_missing_original_native_identity_fails_closed(self):
        context=dict(version='10.0.6',project_sha256='p',rules_sha256='r',
                     clearance_nm=250000,source_sha256='b',identities=[])
        report={'violations':[dict(type='hole_to_hole',severity='warning',items=[{'uuid':'a'},{'uuid':'b'}])]}
        with self.assertRaises(ValueError):compare(context,context,report,report)


if __name__=='__main__':unittest.main()
