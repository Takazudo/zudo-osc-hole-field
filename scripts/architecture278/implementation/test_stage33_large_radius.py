import copy
import math
import unittest
import stage33_large_radius as s

BASE=s.load()
BUILT,BODIES=s.run(copy.deepcopy(BASE),preserve=False)
RES=BUILT['res'];P=BUILT['P']


def mutated(fn):
    data=copy.deepcopy(BASE);fn(data);return data


def r33(d):return d['input']['candidates']['R33']


class Stage33(unittest.TestCase):
    def rejects(self,fn,text):
        with self.assertRaises(ValueError) as caught:s.run(mutated(fn),preserve=False)
        self.assertIn(text,str(caught.exception))

    def test_deterministic_outputs_match_committed_files(self):
        self.assertEqual(set(BODIES),set(s.GENERATED))
        for name,body in BODIES.items():
            if name!='report.json':self.assertEqual((s.OUT/name).read_text(),body,name)

    def test_candidates_are_classified_and_r33_meets_every_criterion(self):
        self.assertEqual(BUILT['report']['classification'],{'B32':'INFEASIBLE','F33':'INFEASIBLE','R33':'CONDITIONAL'})
        self.assertEqual(RES['failed'],[]);self.assertTrue(all(RES['criteria'].values()));self.assertEqual(len(RES['criteria']),12)
        self.assertFalse(BUILT['report']['recommendation']['adopted'])
        self.assertTrue(all(r['class'] in s.CLASSES for r in BUILT['report']['results']))

    def test_stage32_failures_are_preserved_not_recomputed_away(self):
        b=BUILT['b32']
        self.assertEqual(b['failed_stage32'],['S9_bend_maker_rule']);self.assertFalse(b['any_identified_wire_met'])
        self.assertFalse(b['bow_sensitivity']['uniform-diagonal']['meets_K4']);self.assertAlmostEqual(b['bow_sensitivity']['uniform-diagonal']['robust_spare_mm'],-0.382,places=3)
        self.assertGreater(b['notched_rail_20N_failures'],0);self.assertEqual(b['route_radius_mm'],5.0)
        self.assertIn('design/architecture-278/implementation/stage32/analysis.json',BUILT['report']['source_sha256'])
        def hide(d):d['s32_analysis']['candidates']['B32']['bend']['any_identified_wire_met']=True
        self.rejects(hide,'Stage32 failures are preserved')

    def test_required_radius_is_derived_from_the_innermost_conductor(self):
        w=RES['wires'];od=1.0;dress=0.25
        expect={'J-SIG':10*od+3.0*od/2+dress-od/2,'J-PWR':10*od+(1+math.sqrt(2))*od/2+dress-od/2}
        for l,v in expect.items():self.assertAlmostEqual(w['required_at_jst_max_od_10x_mm'][l],v,places=5)
        self.assertTrue(w['route_meets_10x_for_any_window_wire'])
        for l in s.LINKS:
            for r in RES['states'][l]['rows']:self.assertEqual(r['bend_radii_mm'],[12.0])
        self.assertFalse(any(f['route_R_meets'] for f in w['flex_sensitivity']))
        self.rejects(lambda d:d['input']['parameters']['route_radius_mm'].__setitem__('value',11.0),'S9_bend_maker_rule')
        self.rejects(lambda d:d['input']['parameters']['bundle_dressing_allowance_mm'].__setitem__('value',-0.1),'dressing allowance is not negative')

    def test_every_state_keeps_the_design_length_and_the_arch_rises_by_half(self):
        cand=BUILT['cand'];mh=2*7.3
        for l in s.LINKS:
            Ld=cand['lengths'][l]['design_length_mm'];rows={(r['withdrawn'],r['travel_mm']):r for r in RES['states'][l]['rows']};z0=rows[('installed',0.0)]['top_centreline_z_mm']
            for (n,t),r in rows.items():
                c=s.constant_length(cand['geo'],l,Ld,t*(n in ('local','both')),t*(n in ('middle','both')),P)
                d=c['route']['dense'];self.assertAlmostEqual(sum(math.dist(a,b) for a,b in zip(d,d[1:]))+mh,Ld,places=6)
                self.assertAlmostEqual(r['top_centreline_z_mm']-z0,t*(n in ('local','both'))/2+t*(n in ('middle','both'))/2,places=5)
                self.assertFalse(r['slack_short']);self.assertGreaterEqual(min(r['straight_from_exit_mm']),2.0-1e-9)
        self.assertEqual({l:BUILT['report']['design_lengths'][l]['design_length_proposal_mm'] for l in s.LINKS},{'J-SIG':116,'J-PWR':139})
        self.assertTrue(all(v['measured_or_cut_mm'] is None for v in BUILT['report']['design_lengths'].values()))

    def test_no_state_enters_the_undesigned_front_volume(self):
        cand=BUILT['cand']
        for l in s.LINKS:
            for r in RES['states'][l]['rows']:
                c=s.constant_length(cand['geo'],l,cand['lengths'][l]['design_length_mm'],r['travel_mm']*(r['withdrawn'] in ('local','both')),r['travel_mm']*(r['withdrawn'] in ('middle','both')),P)
                self.assertGreater(min(p[2] for p in c['route']['dense'])-s.bundle(P,l)['round_radius_mm'],34.0)
        self.assertFalse(BUILT['reservations']['front_unknown_volume']['entered_by_R33'])
        self.assertEqual(BUILT['reservations']['front_unknown_volume']['status'],'UNKNOWN_NOT_FREE (unchanged from Stage32)')

    def test_k4_after_the_stack_for_every_bow_case_and_thresholds_are_not_relaxed(self):
        cases={r['bow_case'] for r in RES['robust']};self.assertIn('uniform-diagonal',cases);self.assertEqual(len(cases),4)
        for c in RES['robust']:
            for r in c['rows']:
                self.assertAlmostEqual(r['robust_spare_mm'],r['sampled_clearance_mm']-0.5-r['tolerance']['worst_case_mm'],places=5)
                self.assertEqual(r['meets_K4'],r['robust_spare_mm']>=0.15-1e-12)
        self.rejects(lambda d:d['s32']['input']['parameters']['placement_margin_mm'].__setitem__('value',0.4),'placement margin is not relaxed')
        self.rejects(lambda d:d['s32']['input']['parameters']['robust_spare_mm'].__setitem__('value',0.1),'K4 threshold is not relaxed')
        self.rejects(lambda d:d['s32']['input']['parameters']['release_travel_mm'].__setitem__('value',10),'release travel stays')
        self.rejects(lambda d:d['input']['parameters'].__setitem__('placement_margin_mm',{'value':0.3,'class':'DESIGN_ASSUMPTION','note':'x'}),'may not override the inherited Stage32 parameter')

    def test_wire_selection_stays_null_and_current_is_not_transferred(self):
        w=RES['wires'];rows={x['mpn']:x for x in w['wires']}
        self.assertIsNone(w['selection']);self.assertEqual(w['qualified_wires'],[])
        self.assertEqual(rows['Alpha Wire 1852']['failed'],['current']);self.assertFalse(rows['Alpha Wire 1852']['checks']['current'])
        self.assertIn('od_window',rows['Alpha Wire 1853']['failed']);self.assertIn('tin_plated',rows['Alpha Wire 2843/7']['failed'])
        self.assertIn('temperature',rows['Alpha Wire 422607']['failed']);self.assertIn('od_window',rows['Alpha Wire 782607']['failed'])
        self.rejects(lambda d:d['input']['parameters']['jst_current_rating_awg28_A'].update(value=1.0,**{'class':'DESIGN_ASSUMPTION'},note='x'),'not transferred to AWG28')
        self.rejects(lambda d:d['input']['wire_candidates_not_obtained'][0].__setitem__('values',{'od_mm':0.98}),'carries no values')
        self.rejects(lambda d:d['input']['wire_candidates'][0].__setitem__('sources',['S-DABURN-2612']),'from an obtained maker document')
        self.rejects(lambda d:d['s32']['input']['parameters']['selected_wire_mpn'].update(value='Alpha Wire 1852',**{'class':'DESIGN_ASSUMPTION'},note='x'),'no wire is selected')

    def test_header_changes_stay_inside_the_approval(self):
        def drop(d):d['approval']['broader_change_proposals'].pop('header_mounting_face')
        self.rejects(drop,'a header face change must be listed as a broader change proposal')
        def local(d):r33(d)['header_moves']['A01:J-SIG:local']={'origin_mm':[211,173],'rotation_deg':0,'face':'front'}
        self.rejects(local,'header move outside the approval')
        def overlap(d):r33(d)['header_moves']['A01:J-PWR:middle']['origin_mm']=[262.0,150.0]
        self.rejects(overlap,'release sweep overlaps')
        def over_corridor(d):r33(d)['header_moves']['A01:J-SIG:middle']['origin_mm']=[262.0,156.0]
        self.rejects(over_corridor,'S4_sweeps_and_access_clear')
        for h in RES['header_moves']:
            g=BUILT['cand']['geo'][h['ref']];m=BUILT['mech']['headers'][h['ref']]
            self.assertEqual((g['pins'],g['header_mpn'],g['board'],g['face_z_mm'],g['axis']),(m['pins'],m['header_mpn'],m['board'],50,1))
            self.assertEqual(h['status'],'BROADER_CHANGE_PROPOSAL (mounting face)')

    def test_keeper_and_strength_are_conditional_and_sensitive(self):
        st=RES['strength'];k=st['keeper_K1']
        self.assertTrue(st['meets_at_planning_load']);self.assertEqual(st['status'],'CALCULATED_CONDITIONALLY; not a physical strength result (M33-06)')
        self.assertTrue(any(not g['meets'] for g in k['grid'] if g['load_N']==20 and g['Kt']==3.0))
        b,t,h=17.0,2.0,34.0;self.assertAlmostEqual(k['allowable_top_load_N'],240/1.5*(b*t**3/12)/(3.0*h*t/2),places=4)
        self.assertGreater(st['rail_middle_0']['allowable_tip_load_N']['lateral'],50)
        self.rejects(lambda d:r33(d)['keeper'].__setitem__('z_mm',[62.0,85.0]),'S12_keeper_above_installed_arch')
        self.rejects(lambda d:r33(d)['keeper'].__setitem__('obstacle','crossmember:rear:1'),'keeper outside the approval')
        self.rejects(lambda d:d['input']['parameters']['keeper_root_Kt'].__setitem__('value',40.0),'S6_strength_planning_load')

    def test_front_face_large_radius_is_infeasible(self):
        f=BUILT['f33']
        self.assertEqual(f['status'],'INFEASIBLE')
        self.assertAlmostEqual(f['links']['J-SIG']['slot_robust_spare_per_side_mm'],(4.0-2*1.75)/2-0.5-0.1,places=6)
        for l in s.LINKS:
            x=f['links'][l];self.assertFalse(x['slot_meets_K4']);self.assertTrue(x['release_15mm_conflicts_code_default_plane']);self.assertTrue(x['enters_front_unknown_volume_installed'])
            self.assertAlmostEqual(x['hook_low_centreline_z_max_mm'],41.1-2-12,places=6)
        self.assertEqual(f['descent']['gap_between_jack_board_edge_and_rail_mm'],2)

    def test_reservations_contain_every_state_and_stay_proposals(self):
        cand=BUILT['cand'];rv={r['id']:r for r in RES['reservations']}
        for l in s.LINKS:
            box=rv['RV-ARCH-'+l];rb=s.bundle(P,l)['round_radius_mm']
            for r in RES['states'][l]['rows']:
                c=s.constant_length(cand['geo'],l,cand['lengths'][l]['design_length_mm'],r['travel_mm']*(r['withdrawn'] in ('local','both')),r['travel_mm']*(r['withdrawn'] in ('middle','both')),P)
                for p in c['route']['dense']:
                    self.assertTrue(box['box_mm'][0]<=p[0]-rb and p[0]+rb<=box['box_mm'][2] and box['box_mm'][1]<=p[1]-rb and p[1]+rb<=box['box_mm'][3] and box['z_mm'][0]<=p[2]-rb and p[2]+rb<=box['z_mm'][1])
        self.assertTrue(all(r['status']=='PROPOSAL_REQUIRES_OWNER_DECISION' for r in rv.values()));self.assertEqual(len(rv),6)

    def test_cable_gap_plan_bound_holds_in_every_sampled_state(self):
        cc=RES['cable_to_cable']
        self.assertGreaterEqual(cc['robust_spare_mm'],0.15);self.assertEqual(len(cc['pairs']),16)
        for p in cc['pairs']:self.assertGreaterEqual(p['gap_mm']+0.2+1e-9,cc['plan_bound_mm'])

    def test_access_core_and_procedure_numbers(self):
        for ref,a in RES['access'].items():
            self.assertTrue(a['rear_corridor']['clear'],ref);self.assertIn('NOT_DETERMINED',a['finger_operation']);self.assertIsNone(a['grip_length_needed_mm'])
        self.assertTrue(RES['core_40mm']['clear']);self.assertGreaterEqual(RES['core_40mm']['keeper_clearance_mm'],0.5)
        pr=BUILT['model']['procedure'];tops={l:max(r['envelope_top_z_mm'] for r in RES['states'][l]['rows'] if r['withdrawn']=='installed') for l in s.LINKS}
        self.assertIn(f"z {tops['J-SIG']:.1f} / {tops['J-PWR']:.1f}",pr['R33 assembly'][4])
        mid=[r for r in RES['states']['J-SIG']['rows'] if r['withdrawn']=='middle' and r['travel_mm']==15][0]
        self.assertIn(f"{RES['static']['J-SIG']['straight_from_exit_mm'][1]:.1f} mm straight installed, {mid['straight_from_exit_mm'][1]:.1f} mm at 15 mm",pr['Middle connector service'][2])
        both=max(r['envelope_top_z_mm'] for l in s.LINKS for r in RES['states'][l]['rows'])
        self.assertIn(f'up to z {both:.1f}',pr['Core service (unchanged order)'][2])

    def test_radius_headroom_covers_the_flex_sensitivity(self):
        h=RES['radius_headroom'];self.assertEqual(h['largest_fitting_radius_mm'],22.5)
        self.assertIn('does not fit leg',h['scan'][-1]['reason'])
        for f in RES['wires']['flex_sensitivity']:
            self.assertTrue(any(x['fits'] and x['radius_mm']>=max(f['required_centreline_radius_mm'].values()) for x in h['scan']))

    def test_no_status_claims_and_nothing_measured(self):
        self.rejects(lambda d:d['input']['parameters']['route_radius_mm'].__setitem__('status','VALIDATED'),'unsupported pass claim')
        rep=BUILT['report']
        self.assertTrue(all(m['status']=='NOT_RUN' and m['value'] is None for m in rep['measurements']))
        self.assertEqual((rep['native'],rep['physical'],rep['external_contact'],rep['production_CAD_changed'],rep['architecture_adopted']),('NOT_RUN','NOT_RUN','NONE',False,False))
        self.assertTrue(all(('not' in v.lower()) or ('PROPOSAL' in v) or ('CONDITIONAL' in v) or v=='NOT_RUN' for v in rep['decision_status'].values()))


if __name__=='__main__':unittest.main()
