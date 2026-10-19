import copy
import math
import unittest
from unittest.mock import patch
import stage35_cover_service as s


class Stage35(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.P,cls.T,cls.rules,cls.c=s.context()

    def test_exact_length_identity(self):
        for L in (129,130,133,149):
            for travel in (0,2.45,7.5,15):
                z=s.exact_top(L,45.1774279923,43.9,57.3+travel,12,14.6)
                reconstructed=(z-43.9-12)+(45.1774279923-24)+(z-57.3-travel-12)+math.pi*12+14.6
                self.assertAlmostEqual(reconstructed,L,places=10)

    def test_shortened_242_is_not_cover_pass(self):
        c=s.candidate_at(self.c,self.P,130.58)
        g=s.s34.rg34(c,self.P,self.T)
        self.assertFalse(s.s34.cover(g,self.P)['J-SIG']['meets_K4'])

    def test_screen_intervals_are_not_hardware_claims(self):
        for l in s.s34.LINKS:
            for mode in ('inherited_height_screen','endpoint_box_downward_bow','endpoint_box_signed_bow'):
                x=s.interval(self.c,self.P,self.T,l,mode)
                self.assertFalse(x['full_service_solution'])
                self.assertIsNone(x['physical_or_cut_length_mm'])
                self.assertEqual(x['interval_nonempty'],x['lower_design_length_mm']<=x['upper_design_length_mm'])
        x=s.interval(self.c,self.P,self.T,'J-SIG','endpoint_box_signed_bow')
        self.assertFalse(x['interval_nonempty'])

    def test_interval_bounds_have_independent_witnesses(self):
        x=s.interval(self.c,self.P,self.T,'J-SIG','endpoint_box_signed_bow')
        D=x['D_mm'];R=12;f=x['fan_in_mm'];b=x['bow_mm'];cut=.5
        L=x['lower_design_length_mm']-cut
        z=s.exact_top(L,D+2,43.9-1,57.3+1+b+15,R,14.6)
        self.assertAlmostEqual(z-R-(57.3+1+b+15),f,places=9)
        L=x['upper_design_length_mm']+cut
        z=s.exact_top(L,D-2,43.9+1,57.3+1+b+15,R,14.6)
        self.assertAlmostEqual(z+1.75+.3+1.2+.5+.1+.1+1+.15,105,places=9)

    def test_continuous_straight_extrema_bound_interior(self):
        c=s.candidate_at(self.c,self.P,130)
        rows=s.continuous_states(c,self.P,self.T)
        row=next(x for x in rows if x['link']=='J-SIG' and x['state']=='middle')
        D=math.hypot(40,21)
        for t in (1,3.2,6,11.7,14.99):
            z=s.exact_top(130,D,43.9,57.3+t,12,14.6)
            self.assertGreaterEqual(z-12-57.3-t,row['minimum_straight_mm'])
            self.assertLessEqual(z,row['top_z_interval_mm'][1])
        self.assertTrue(row['straight_pass'])

    def test_longer_length_raises_cap_half_as_far(self):
        tops=[]
        for L in (129,130.5):
            g=s.s34.rg34(s.candidate_at(self.c,self.P,L),self.P,self.T)
            tops.append(g['J-SIG']['Ztop'])
        self.assertAlmostEqual(tops[1]-tops[0],.75,places=6)

    def test_retained_thresholds_and_wire_unknown(self):
        self.assertEqual(s.val(self.P,'release_travel_mm'),15)
        self.assertEqual(s.val(self.P,'robust_spare_mm'),.15)
        self.assertEqual(s.val(self.P,'placement_margin_mm'),.5)
        self.assertIsNone(s.val(self.P,'selected_wire_mpn'))

    def test_shortening_does_not_remove_service_slack(self):
        for L in (129,130.5):
            c=s.candidate_at(self.c,self.P,L)
            z0=s.s33.constant_length(c['geo'],'J-SIG',L,0,0,self.P)['top_centreline_z_mm']
            z1=s.s33.constant_length(c['geo'],'J-SIG',L,0,15,self.P)['top_centreline_z_mm']
            self.assertAlmostEqual(2*(z1-z0),15,places=6)

    def test_bad_mode_rejected_under_optimized_python(self):
        with self.assertRaises(ValueError):s.interval(self.c,self.P,self.T,'J-SIG','qualified')

    def test_unknown_height_extends_through_envelope(self):
        c=copy.deepcopy(self.c)
        c['obs'].append({'id':'test-unknown','kind':'unknown_depth','lo':[210,170,20],'hi':[211,171,34]})
        o=next(x for x in s.occupied_obstacles(c,150) if x['id']=='test-unknown')
        self.assertGreater(o['z'][1],150)
        self.assertEqual(s.gap_status(o,-1,.15),'UNKNOWN_OCCUPANCY')
        self.assertEqual(s.gap_status(o,1,.15),'CLEAR_OF_THIS_BOUND')

    def test_board_in_access_column_is_not_skipped(self):
        c=s.candidate_at(self.c,self.P,130);g=s.s34.rg34(c,self.P,self.T)
        post=s.s34.post_prism(c,g,self.data['input'])
        c['obs'].append({'id':'board:test-obstruction','kind':'known','lo':[208,171,60],'hi':[212,175,70]})
        rows=s.access_screen(c,g,post,self.P,self.T,self.rules)
        self.assertTrue(any(b['obstacle']=='board:test-obstruction' for x in rows for b in x['blockers']))

    def test_vertical_removal_captures_overhead_obstacle(self):
        c=s.candidate_at(self.c,self.P,130);g=s.s34.rg34(c,self.P,self.T)
        post=s.s34.post_prism(c,g,self.data['input'])
        c['obs'].append({'id':'test-overhead','kind':'known','lo':[208,171,110],'hi':[212,175,115]})
        a=s.all_obstacle_rows(c,g,post,self.P,self.T,self.rules,False)
        b=s.all_obstacle_rows(c,g,post,self.P,self.T,self.rules,True)
        self.assertFalse(any(x['obstacle']=='test-overhead' for x in a['unexcluded_below_K4']))
        self.assertTrue(any(x['obstacle']=='test-overhead' for x in b['unexcluded_below_K4']))
        self.assertEqual(a['examined_pair_count'],b['examined_pair_count'])

    def test_free_span_audits_unknown_above_historical_top(self):
        c=s.candidate_at(self.c,self.P,130);g=s.s34.rg34(c,self.P,self.T)
        post=s.s34.post_prism(c,g,self.data['input'])
        c['obs'].append({'id':'test-span-unknown','kind':'unknown_depth',
                         'lo':[209,172,20],'hi':[211,174,34]})
        sp={'xy':[210,173],'zc':100,'A':2,'B':1,'inflate_mm':1}
        inherited=[{'link':'J-SIG','side':'local','spheroids':[sp],
                    'tightest':[], 'meets_K4':True}]
        with patch.object(s.s34,'free_spans',return_value=inherited):
            rows=s.conservative_free_spans(c,g,post,self.P,self.T,self.rules)
        hit=next(x for x in rows[0]['blockers'] if x['obstacle']=='test-span-unknown')
        self.assertEqual(hit['status'],'UNKNOWN_OCCUPANCY')
        self.assertEqual(rows[0]['status'],'NOT_CERTIFIED')

    def test_summary_never_calls_hardware_feasible(self):
        a={'intervals':[],'evaluations':[]}
        text=s.summary(a)
        self.assertIn('not complete feasible hardware intervals',text)
        self.assertIn('unestablished',text)


if __name__=='__main__':unittest.main()
