import copy
import unittest
import stage32_service_envelope as s

BASE=s.load()
BUILT,BODIES=s.run(copy.deepcopy(BASE),preserve=False)
RES=BUILT['res']


def mutated(fn):
    data=copy.deepcopy(BASE);fn(data);return data


class Stage32(unittest.TestCase):
    def rejects(self,fn,text):
        with self.assertRaises(ValueError) as caught:s.run(mutated(fn),preserve=False)
        self.assertIn(text,str(caught.exception))

    def test_deterministic_outputs_match_committed_files(self):
        _,again=s.run(copy.deepcopy(BASE),preserve=False)
        self.assertEqual(again,BODIES);self.assertEqual(set(again),set(s.GENERATED))
        for name,body in again.items():
            if name!='report.json':self.assertEqual((s.OUT/name).read_text(),body,name)

    def test_b32_meets_s1_s8_and_b31_does_not(self):
        self.assertEqual(RES['B32']['status'],'CONDITIONAL_PENDING_WIRE_SELECTION');self.assertEqual(RES['B32']['failed'],['S9_bend_maker_rule'])
        self.assertEqual(BUILT['report']['recommendation']['status'],'CONDITIONAL_PENDING_WIRE_SELECTION')
        self.assertEqual(RES['B31']['failed'],['S2_robust_K4','S3_retention_modelled','S4_sweeps_clear','S9_bend_maker_rule'])
        self.assertLess(RES['B31']['tightest_robust']['robust_spare_mm'],0.0)
        self.assertGreaterEqual(RES['B32']['tightest_robust']['robust_spare_mm'],0.15)

    def test_k4_is_applied_after_the_tolerance_stack_without_rounding(self):
        for r in RES['B32']['robust']:
            self.assertAlmostEqual(r['robust_spare_mm'],r['sampled_clearance_mm']-0.5-r['tolerance']['worst_case_mm'],places=5)
            self.assertEqual(r['meets_K4'],r['robust_spare_mm']>=0.15-1e-12)
        self.rejects(lambda d:d['input']['tolerances']['pcb_bow_fraction'].__setitem__('value',0.005),'PCB bow allowance is not reduced')
        self.rejects(lambda d:d['input']['parameters']['strength_safety_factor'].__setitem__('value',1.2),'strength safety factor is not reduced')
        self.rejects(lambda d:d['input']['parameters']['planning_load_N'].__setitem__('value',3),'planning load equals the Stage10')
        self.rejects(lambda d:d['input']['parameters']['panel_rear_z_mm'].__setitem__('value',2.0),'panel datum follows Stage10')

    def test_robust_spare_is_the_minimum_over_samples_and_strap_footprint(self):
        built=BUILT['built']['B32'];P=BUILT['P'];T=BASE['input']['tolerances'];rules=BASE['input']['tolerance_rules']
        for r in RES['B32']['robust']:
            if 'from' in r:continue
            smp=BUILT['samples']['B32'][r['link']];o=next(x for x in built['obs'] if x['id']==r['obstacle'])
            worst=min(s.s31.box_distance(p,o['lo'],o['hi'])-rr-0.1-0.5-s.tol_stack(o['id'],p,P,T,rules)['worst_case_mm'] for p,rr in smp)
            self.assertAlmostEqual(r['robust_spare_mm'],worst,places=5)
        strap=[r for r in RES['B32']['robust'] if r.get('from','').endswith(':strap')]
        for r in strap:
            g=next(x for x in RES['B32']['guides'] if x['link']==r['link']);self.assertGreater(r['tolerance']['contributors']['pcb_bow'],s.bow(P,T,g['centre_mm'][1])-1e-9)
            self.assertIn('strap_bore_mm',r['tolerance']['contributors']);self.assertIn('saddle_seating_mm',r['tolerance']['contributors'])
        cases={c['case']:c for c in RES['B32']['bow_sensitivity']}
        self.assertTrue(cases['length-142-292']['meets_K4']);self.assertFalse(cases['uniform-diagonal']['meets_K4'])
        self.rejects(lambda d:d['input']['parameters']['robust_spare_mm'].__setitem__('value',0.1),'K4 threshold is not relaxed')
        self.rejects(lambda d:d['input']['parameters']['placement_margin_mm'].__setitem__('value',0.4),'placement margin is not relaxed')

    def test_bow_drives_b31_failure_and_b32_lowers_the_runs(self):
        top=RES['B31']['robust'][0];self.assertTrue(top['obstacle'].startswith('board:A01-middle'));self.assertGreater(top['tolerance']['contributors']['pcb_bow'],0.5)
        data=mutated(lambda d:d['input']['tolerances']['pcb_bow_fraction'].__setitem__('value',0.03))
        with self.assertRaises(ValueError) as caught:s.run(data,preserve=False)
        self.assertIn('S2_robust_K4',str(caught.exception))

    def test_unconfirmed_values_stay_null_and_classes_are_enforced(self):
        self.rejects(lambda d:d['input']['parameters']['gh_unmating_stroke_mm'].__setitem__('value',3.0),'UNCONFIRMED value must stay null')
        self.rejects(lambda d:d['input']['parameters']['wire_od_max_mm'].__setitem__('class','MEASURED'),'value class must be one of')
        self.rejects(lambda d:d['input']['parameters']['wire_od_max_mm'].__setitem__('sources',['R-STAGE31']),'MAKER_DOC value without an obtained maker document')
        self.rejects(lambda d:d['input']['parameters']['release_travel_mm'].__setitem__('sources',['S-JST-EGH']),'EXISTING_DESIGN value without a repository source')
        self.rejects(lambda d:d['input']['parameters']['strength_safety_factor'].pop('note'),'DESIGN_ASSUMPTION needs a stated basis')
        self.rejects(lambda d:d['input']['parameters']['wire_od_max_mm'].__setitem__('sources',['S-NOPE']),'unknown source')
        self.rejects(lambda d:d['input']['parameters']['gh_mated_height_mm'].__setitem__('sources',['S-JST-GATED']),'without an obtained maker document')

    def test_release_travel_cannot_be_shortened_without_a_maker_stroke(self):
        self.rejects(lambda d:d['input']['parameters']['release_travel_mm'].__setitem__('value',5),'release travel stays the Stage10 15 mm')
        self.rejects(lambda d:d['input']['parameters']['geometric_separation_mm'].__setitem__('value',1.0),'geometric separation is derived')

    def test_release_keeps_the_design_length_and_slides_through_the_guide(self):
        built=BUILT['built']['B32'];P=BUILT['P']
        for l in s.LINKS:
            Ld=built['lengths'][l]['design_length_mm'];self.assertGreater(Ld,built['lengths'][l]['minimum_installed_mm']+15)
            self.assertAlmostEqual(built['routes'][l]['length_mm']+14.6,Ld,places=5)
            for x in RES['B32']['states'][l]['release']:
                self.assertFalse(x['slack_short'])
                c=s.constant_length(built['geo'],l,built['spec']['routes'][l],P,Ld,x['travel_mm'],{'middle':(0,1),'local':(1,0),'both':(1,1)}[x['withdrawn']])
                self.assertAlmostEqual(c['route']['length_mm']+14.6,Ld,places=5)
                self.assertAlmostEqual(x['slide_through_guide_mm'],0.0 if x['withdrawn']=='local' else x['travel_mm'],places=3)
        with self.assertRaises(ValueError):s.constant_length(built['geo'],'J-SIG',built['spec']['routes']['J-SIG'],P,90,15,(0,1))['route'] or (_ for _ in ()).throw(ValueError('slack short'))

    def test_release_dip_and_reservations(self):
        for l in s.LINKS:
            rel=[x for x in RES['B32']['states'][l]['release'] if x['travel_mm']==15 and x['withdrawn']=='middle'][0]
            self.assertTrue(rel['neighbour_conflicts']['NB-278'])
            self.assertLess(rel['envelope_bottom_z_mm'],21.6)
        rv={r['id']:r for r in BUILT['neighbour']['reservations']}
        for l in s.LINKS:
            box=rv['RV-DIP-'+l];env=s.middle_envelopes(BUILT['built']['B32'],BUILT['P'],l);self.assertTrue(env)
            for p,r in env:
                self.assertTrue(box['box_mm'][0]<=p[0]-r and p[0]+r<=box['box_mm'][2] and box['box_mm'][1]<=p[1]-r and p[1]+r<=box['box_mm'][3] and box['z_mm'][0]<=p[2]-r,(l,p))
        for l in s.LINKS:
            self.assertEqual(rv['RV-DIP-'+l]['status'],'PROPOSAL_REQUIRES_OWNER_DECISION')
            self.assertLess(rv['RV-DIP-'+l]['z_mm'][0],21.6)
        self.assertEqual(BUILT['report']['decision_status']['reservations'],'PROPOSAL_REQUIRES_OWNER_DECISION')
        self.assertEqual(BUILT['neighbour']['unknown_regions'][0]['status'],'UNKNOWN_NOT_FREE')

    def test_bend_rule_is_not_met_and_is_reported(self):
        bend=RES['B32']['bend']
        self.assertFalse(bend['any_identified_wire_met'])
        self.assertTrue(all(not w['route_meets_maker_rule'] for w in bend['wire_candidates']))
        self.assertEqual(RES['B32']['open_conditions']['bend_radius'],'maker rule not met by the 5 mm route for any identified wire')
        for h in bend['hook_lower_bound']:
            if h['radius_mm']>5:self.assertFalse(h['route_admits'])
        self.rejects(lambda d:d['input']['parameters']['design_bend_radius_mm'].__setitem__('value',10.0),'design bend radius carried from Stage31')

    def test_guides_contain_a_straight_bundle_and_notches_follow(self):
        for g in RES['B32']['guides']:
            self.assertAlmostEqual(g['radial_clearance_mm'],0.25,places=6)
            self.assertGreaterEqual(g['saddle_mm']['seat_thickness'],0.8-1e-9)
            self.assertLessEqual(g['notch']['relieved_top_z_mm'],g['centre_mm'][2]-g['seat_radius_mm']-0.8+1e-9)
        def bend_in_guide(d):d['input']['candidates']['B32']['routes']['J-SIG']['waypoints_mm'][4]=[239.5,171.5,44.3]
        self.rejects(bend_in_guide,'route must be straight through guide R1')

    def test_strength_is_conditional_and_sensitive(self):
        st=RES['B32']['strength']
        self.assertEqual(st['status'],'CALCULATED_CONDITIONALLY; not a physical strength result (M32-06)')
        self.assertTrue(st['meets_at_planning_load'])
        self.assertTrue(any(not r['meets'] for n in st['notches'] for r in n['grid']))
        self.assertGreater(st['tip_deflection_mm']['with_notches'],st['tip_deflection_mm']['without_notches'])
        data=mutated(lambda d:d['input']['parameters']['strength_safety_factor'].__setitem__('value',4.0))
        with self.assertRaises(ValueError) as caught:s.run(data,preserve=False)
        self.assertIn('S6_strength_planning_load',str(caught.exception))

    def test_scope_and_identity_are_protected(self):
        def move_local(d):d['input']['candidates']['B32']['header_moves']['A01:J-SIG:local']={'origin_mm':[211,173],'rotation_deg':0}
        self.rejects(move_local,'header move outside the approval')
        def guide_elsewhere(d):d['input']['candidates']['B32']['guides'][0]['obstacle']='crossmember:middle:0'
        self.rejects(guide_elsewhere,'guide outside the approved carrier shape')
        self.rejects(lambda d:d['approval']['changeable'].__setitem__('header_refs',['A01:J-SIG:local']),'only the middle J-SIG/J-PWR headers may move')
        for ref,g in BUILT['built']['B32']['geo'].items():
            h=BUILT['mech']['headers'][ref];self.assertEqual((g['pins'],g['header_mpn'],g['face_z_mm']),(h['pins'],h['header_mpn'],h['pad_depth_mm']))

    def test_no_status_claims_and_nothing_measured(self):
        self.rejects(lambda d:d['input']['parameters']['wire_od_max_mm'].__setitem__('status','VALIDATED'),'unsupported pass claim')
        rep=BUILT['report']
        self.assertTrue(all(m['status']=='NOT_RUN' and m['value'] is None for m in rep['measurements']))
        self.assertEqual((rep['native'],rep['physical'],rep['external_contact'],rep['production_CAD_changed']),('NOT_RUN','NOT_RUN','NONE',False))
        self.assertTrue(all('not' in v.lower() or 'NOT' in v or 'CONFLICT' in v or 'CONDITIONAL' in v or 'PROPOSAL' in v for v in rep['decision_status'].values()))

    def test_access_is_not_called_finger_operable(self):
        faces=RES['B32']['access']['J-SIG']['latch_faces']
        self.assertEqual((faces['-x']['nearest_cable'],round(faces['-x']['free_to_cable_mm'],1)),('J-SIG',3.5))
        self.assertEqual(faces['+x']['nearest_cable'],'J-PWR');self.assertLess(faces['+x']['free_to_cable_mm'],faces['+x']['free_to_rigid_mm'])
        for g in ('R1','R2'):
            a=RES['B32']['access']['strap:'+g];self.assertEqual(a['front_access'],'BLOCKED');self.assertIn('A01-middle removed',a['reopen'])
        for l in s.LINKS:
            a=RES['B32']['access'][l]
            self.assertIn('NOT_DETERMINED',a['finger_operation']);self.assertIsNone(a['grip_length_needed_mm'])
            self.assertIn('UNKNOWN',a['panel_side_corridor']['crosses'])


if __name__=='__main__':unittest.main()
