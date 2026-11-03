import copy
import json
import math
import unittest
import stage34_arch_retention as s

BASE=s.load()
BUILT,BODIES=s.run(copy.deepcopy(BASE),preserve=False)
RG=BUILT['rg'];P=BUILT['P'];GEO=RG['geometry']


def mutated(fn):
    data=copy.deepcopy(BASE);fn(data);return data


def par(d,k,v):d['input']['parameters'][k]['value']=v


class Stage34(unittest.TestCase):
    def rejects(self,fn,text):
        with self.assertRaises(ValueError) as caught:s.run(mutated(fn),preserve=False)
        self.assertIn(text,str(caught.exception))

    def test_deterministic_outputs_match_committed_files(self):
        self.assertEqual(set(BODIES),set(s.GENERATED))
        for name,body in BODIES.items():
            if name!='report.json':self.assertEqual((s.OUT/name).read_text(),body,name)
        committed=json.loads((s.OUT/'report.json').read_text());self.assertEqual(committed['preservation_baseline'],s.BASE)
        committed['preservation_baseline']=None;self.assertEqual(committed,json.loads(BODIES['report.json']))

    def test_status_classes_and_preserved_stage33_results(self):
        rep=BUILT['report'];self.assertEqual(rep['recommendation']['status'],'CONDITIONAL_PENDING_COVER_REGISTRATION_AND_MEASUREMENT');self.assertFalse(rep['recommendation']['adopted'])
        self.assertEqual(RG['status'],'BOUNDED_EXCEPT_REAR_COVER');self.assertEqual(RG['failed'],['T6_rear_cover_K4']);self.assertEqual(rep['classification']['RG34'],'CONDITIONAL')
        self.assertTrue(all(r['class'] in s.CLASSES for r in rep['results']))
        cls={r['result']:r['class'] for r in rep['results']}
        self.assertEqual(cls['Inter-carrier registration within the 1.0 mm requirement'],'UNKNOWN');self.assertEqual(cls['Wire selection'],'UNKNOWN')
        self.assertEqual(cls['20x OD radius (Stage33 rear-cover failure, preserved)'],'INFEASIBLE');self.assertEqual(cls['B32 uniform 1.282 mm bow (Stage32, preserved)'],'INFEASIBLE')
        self.assertEqual(cls['RG34 J-SIG cap under the rear cover (margin, RG34 tolerances, registration, K4)'],'INFEASIBLE')
        self.assertEqual(cls['Front jack board removal with RG34 in place (J-PWR channel within K4 of the A01-jack M4 screwdriver column)'],'INFEASIBLE')
        self.assertIn('front_jack_board_procedure',BASE['approval']['broader_change_proposals']);self.assertIn('j_sig_cover_conflict',BASE['approval']['broader_change_proposals'])
        self.assertEqual(BUILT['res33']['failed'],['S3_lateral_retention'])
        def hide(d):d['s33_analysis']['R33']['failed']=[]
        self.rejects(hide,'Stage33 committed results are preserved')

    def test_escape_needs_closed_parts_and_a_small_closure_gap(self):
        self.assertLess(RG['closure']['gap_max_mm'],RG['closure']['smallest_wire_od_mm']/2)
        self.rejects(lambda d:par(d,'guide_closure_gap_max_mm',0.4),'T1_declared_closed_parts_and_closure_gap')
        self.rejects(lambda d:d['input']['rg34']['parts_closed'].__setitem__('channel_lid',False),'T1_declared_closed_parts_and_closure_gap')

    def test_every_single_end_state_is_inside_rg34_at_constant_length_and_both_ends_is_blocked(self):
        cand=BUILT['cand'];mh=2*7.3
        self.assertEqual({r['corner'] for r in RG['states']},{'low','nominal','high'})
        for g in GEO.values():self.assertAlmostEqual(g['corners_dz_mm']['low'],-(0.25+g['bow_mm']/2+1.0),places=5);self.assertAlmostEqual(g['corners_dz_mm']['high'],0.25+1.0,places=6)
        for r in RG['states']:
            l=r['link'];tl=r['travel_mm'] if r['state'] in ('local','both') else 0.0;tm=r['travel_mm'] if r['state'] in ('middle','both') else 0.0
            c=s.s33.constant_length(cand['geo'],l,cand['lengths'][l]['design_length_mm'],tl,tm,P);d=c['route']['dense']
            self.assertAlmostEqual(sum(math.dist(a,b) for a,b in zip(d,d[1:]))+mh,cand['lengths'][l]['design_length_mm'],places=6)
            if r['state']=='both':self.assertIn('cap',r['blocked_by'])
            else:self.assertTrue(r['admissible'] and r['fan_in_below_block'],(l,r['state'],r['travel_mm']))
        self.rejects(lambda d:par(d,'grip_length_design_mm',30.0),'T7_fan_in_grip_and_s_bend_with_registration')
        self.rejects(lambda d:d['input']['rg34'].__setitem__('service_withdrawal_ends_at_once',2),'one end at a time')

    def test_route_stays_outside_the_former_independently(self):
        cand=BUILT['cand']
        for l,g in GEO.items():
            f=s.frame(cand,l);D=f['D'];R=12.0;r=g['r'];Zl=g['Zlow']
            for (n,tl,tm),dz in [(x,y) for x in s.state_list(P) for y in g['corners_dz_mm'].values()]:
                for p in s.s33.constant_length(cand['geo'],l,cand['lengths'][l]['design_length_mm'],tl,tm,P)['route']['dense'][::5]:
                    sv,nn,z=s.local(f,p);z+=dz;self.assertAlmostEqual(nn,0.0,places=6)
                    # distance from the centreline to the former body (rectangle with two quarter-round corners of radius R - r, ending at its lowest corner point) must be at least r
                    if 1e-6<sv<D-1e-6 and Zl-R<=z<Zl-r:
                        cx=R if sv<R else D-R if sv>D-R else sv
                        if (sv<R or sv>D-R) and z>Zl-R:self.assertGreaterEqual(math.hypot(sv-cx,z-(Zl-R))-(R-r),r-1e-5)
                        else:self.fail(('inside former',l,sv,z))
                    self.assertLessEqual(z+r,g['Zcap_inner']+1e-9)

    def test_part_clearances_core_without_registration_and_k4_not_relaxed(self):
        rows=[r for r in RG['parts']['rows'] if r['obstacle']=='core-envelope-40mm']
        self.assertTrue(rows);self.assertTrue(all(not r['cross_carrier'] for r in rows))
        for r in rows:
            self.assertNotIn('registration_allowance_mm',r['stack']['contributors']);self.assertAlmostEqual(r['robust_spare_mm'],r['distance_mm']-0.5-r['stack']['worst_case_mm'],places=5)
        cross=[r for r in RG['parts']['rows'] if r['obstacle'] and r['cross_carrier']];self.assertTrue(all(r['stack']['contributors']['registration_allowance_mm']==1.0 for r in cross))
        svc=RG['parts']['service_only'];self.assertTrue(svc and not any(r['overlaps'] for r in svc));self.assertFalse(min(svc,key=lambda r:r['robust_spare_mm'])['meets_K4'])
        self.rejects(lambda d:par(d,'guide_wall_mm',1.8),'T3_parts_clear_K4')
        self.rejects(lambda d:d['s33']['s32']['input']['parameters']['robust_spare_mm'].__setitem__('value',0.1),'K4 threshold is not relaxed')

    def test_prism_distance_matches_brute_force(self):
        A={'poly':[[0,0],[4,1],[3,5],[-1,4]],'z':[0,2]};B={'poly':[[7,2],[9,2],[9,6],[7,6]],'z':[3,5]}
        best=min(math.hypot(math.hypot(ax-bx,ay-by),max(0,3-2)) for ax,ay in [(a[0]+(b[0]-a[0])*k/200,a[1]+(b[1]-a[1])*k/200) for a,b in zip(A['poly'],A['poly'][1:]+A['poly'][:1]) for k in range(201)] for bx,by in [(7,y/100) for y in range(200,601)])
        self.assertAlmostEqual(s.prism_dist(A,B),best,places=2);self.assertEqual(s.prism_dist(A,{'poly':[[1,1],[2,1],[2,2],[1,2]],'z':[1,3]}),0.0)

    def test_spheroid_distance_matches_brute_force(self):
        sp=s.spheroid([0,0],0,10,11,0.0);box={'poly':[[3,-1],[5,-1],[5,1],[3,1]],'z':[2,8]}
        best=min(math.hypot(max(0.0,3-sp['B']*math.sin(t)),max(0.0,2-(5+sp['A']*math.cos(t)),(5+sp['A']*math.cos(t))-8)) for t in [math.pi*k/50000 for k in range(50001)])
        self.assertAlmostEqual(s.spheroid_prism_dist(sp,box),best,places=4);self.assertAlmostEqual(sp['B'],0.5*math.sqrt(121-100),places=6)

    def test_free_spans_use_all_the_slack_and_lose_the_bound_without_the_set_former(self):
        for x in RG['free_spans']:
            g=GEO[x['link']];sp=x['spheroids'][0];ch=g['sleeve_bottom_z_mm'][x['side']]-g['exit_z_mm'][x['side']]
            self.assertAlmostEqual(sp['B'],0.5*math.sqrt((ch+g['slack_mm'])**2-ch*ch),places=5)
            self.assertAlmostEqual(sp['inflate_mm'],0.3+1.0+0.1+0.1+g['r'],places=5);self.assertTrue(x['meets_K4'])
        for g in GEO.values():
            self.assertAlmostEqual(g['slack_mm'],0.5,places=9);self.assertAlmostEqual(g['slack_fixed_former_mm'],2*0.5+g['bow_mm']+2*1.0,places=3)
        self.rejects(lambda d:par(d,'former_setting_resolution_mm',1.2),'T5_free_spans_bounded_and_clear')
        self.rejects(lambda d:par(d,'former_clearance_mm',0.2),'the former is a contact guide')

    def test_negative_controls_one_leg_guide_and_no_former_do_not_bound(self):
        for l,v in RG['negative_controls'].items():
            if l not in s.LINKS:continue
            self.assertFalse(v['local_leg_guide_only']['bounded_within_allowance']);self.assertGreater(v['local_leg_guide_only']['bucket_handle_radius_mm'],v['local_leg_guide_only']['stage33_allowance_mm'])
            self.assertFalse(v['without_former']['bounded_within_spare'])
        self.assertTrue(all(not v['fits_under_cover'] for v in RG['r17'].values()))
        self.assertFalse(RG['negative_controls']['fixed_former']['meets_K4'])

    def test_registration_stays_a_requirement(self):
        self.assertTrue(all(g['s_bend_length_mm']>0 for g in GEO.values()))
        for g in GEO.values():
            e=1.0-0.3;self.assertAlmostEqual(g['s_bend_length_mm'],math.sqrt(4*g['required_radius_mm']*e-e*e),places=5)
        self.rejects(lambda d:d['input']['parameters']['inter_carrier_registration_mm'].update(value=0.3,**{'class':'DESIGN_ASSUMPTION'},note='x'),'stays UNCONFIRMED')
        self.rejects(lambda d:par(d,'registration_allowance_mm',0.2),'larger than the guide play')

    def test_current_ledger_is_a01_and_never_promotes_conditional_values(self):
        cur=BUILT['ledger']['current'];self.assertFalse(cur['established_any'])
        hdr=BUILT['mech']['headers']
        for l,rows in cur['links'].items():
            for r in rows:
                self.assertEqual(hdr['A01:'+l+':local']['pins'][r['pin']],r['net']);self.assertIsNone(r['established_max_A']);self.assertTrue(r['established_status'].startswith('UNKNOWN'))
                self.assertLessEqual(r['typical_A'],r['conditional_max_A']);self.assertTrue(r['within_project_limit_conditional'])
        self.assertAlmostEqual(cur['stage33_superseded']['stage33_values']['j_pwr_agnd_return_bound_A'],0.024635858983630604)
        # independent sum of the +12V conditional terms (A01 spec values and evidence maxima)
        p12=4*1.5e-3+4*0.25e-3+2*1.3e-3+3*12.48/5600+(12.48+12.37)/22100+3*12.48/92500+12.48/199800+12.48/10988
        self.assertAlmostEqual(cur['links']['J-PWR'][0]['conditional_max_A'],p12,places=9);self.assertAlmostEqual(cur['links']['J-PWR'][0]['conditional_fault_A'],p12+0.025,places=9)
        self.assertIn('LM393BIDR supply current, U7107/U7108',cur['links']['J-PWR'][0]['unknown_terms'])
        self.assertGreater(cur['links']['J-PWR'][0]['conditional_max_A'],cur['stage33_superseded']['stage33_values']['j_pwr_conductor_current_max_A']['+12V'])
        def promote(d):d['input']['current_budget']['links']['J-SIG'][3]['established_max_A']=0.03
        self.rejects(promote,'an established maximum needs maker evidence')
        def swap(d):d['input']['current_budget']['links']['J-PWR'][0]['terms'][0]['A']=[0.01,0.0015]
        self.rejects(swap,'typical never exceeds the conditional maximum')
        def net(d):d['input']['current_budget']['links']['J-PWR'][0]['net']='-12V'
        self.rejects(net,'net matches the header pin map')

    def test_wire_ledger_separates_checks_and_selection_stays_null(self):
        w=BUILT['ledger']['wires'];rows={x['mpn']:x for x in w['wires']};self.assertIsNone(w['selection'])
        th=rows['Thermax M22759/18-26 (26-AMCFZ-1938)']['per_cable']['J-PWR'];self.assertEqual(th['failed'],[]);self.assertEqual(set(th['unknown']),{'bend_installed_R12','service_flex'})
        self.assertEqual(set(th['conditional']),{'contact_rating','temperature_rise','derating_to_project_limit'});self.assertNotIn('PASS',[th['checks'][k] for k in th['conditional']])
        a28=rows['Alpha Wire 6710']['per_cable']['J-PWR'];self.assertEqual(a28['failed'],[]);self.assertIn('contact_rating',a28['unknown']);self.assertEqual(a28['checks']['bend_installed_R12'],'PASS')
        self.assertIn('od_window_full_tolerance',rows['Alpha Wire 6711']['per_cable']['J-SIG']['failed']);self.assertIn('od_window_full_tolerance',rows['Alpha Wire 1853']['per_cable']['J-SIG']['failed'])
        self.assertEqual(rows['Alpha Wire 1852']['per_cable']['J-SIG']['checks']['contact_rating'],'UNKNOWN')
        self.assertTrue(all(x['per_cable'][l]['status']!='MEETS_ALL' for x in w['wires'] for l in s.LINKS))
        self.rejects(lambda d:d['input']['wire_candidates_added'][0].__setitem__('sources',['S-TE-55A-NOT-OBTAINED']),'from an obtained maker document')
        self.rejects(lambda d:d['s33']['input']['parameters']['jst_current_rating_awg28_A'].update(value=1.0,**{'class':'DESIGN_ASSUMPTION'},note='x'),'not transferred to AWG28')

    def test_strength_friction_cover_and_no_claims(self):
        st=RG['strength'];self.assertTrue(st['meets_at_planning_load']);self.assertEqual(st['status'],'CALCULATED_CONDITIONALLY; not a physical strength result (M34-05)')
        b,h=st['post_section_mm'];I=min(b*h**3,h*b**3)/12;c=min(b,h)/2;lo,hi=min(b,h),max(b,h);al=1/(3+1.8*lo/hi)
        vm=lambda F:math.sqrt((F*st['lever_mm']*c/I)**2+3*(F*st['torsion_arm_mm']/(al*hi*lo*lo))**2)
        for g in st['grid']:self.assertAlmostEqual(g['von_mises_MPa'],vm(g['load_N']),places=4);self.assertEqual(g['meets'],vm(g['load_N'])<=160)
        self.assertTrue([g['meets'] for g in st['grid'] if g['load_N']==20][0]);self.assertFalse([g['meets'] for g in st['grid'] if g['load_N']==50][0])
        for v in RG['friction']['links'].values():self.assertTrue(all(x['ratio_to_drag']>=10 for x in v['free_spans'].values()))
        for l,v in RG['cover'].items():
            need=GEO[l]['Ztop']+0.5+0.1+0.1+1.0+0.15;self.assertAlmostEqual(v['cover_needed_z_mm'],need,places=5);self.assertEqual(v['meets_K4'],need<=105.0+1e-9)
        self.assertFalse(RG['cover']['J-SIG']['meets_K4']);self.assertTrue(RG['cover']['J-PWR']['meets_K4'])
        self.rejects(lambda d:d['input']['rg34'].__setitem__('status','VALIDATED'),'unsupported pass claim')
        rep=BUILT['report'];self.assertTrue(all(m['status']=='NOT_RUN' and m['value'] is None for m in rep['measurements']))
        self.assertEqual((rep['native'],rep['physical'],rep['external_contact'],rep['production_CAD_changed'],rep['architecture_adopted']),('NOT_RUN','NOT_RUN','NONE',False,False))


if __name__=='__main__':unittest.main()
