import copy
import unittest
import stage31_cable_entry_redesign as s

BASE=s.load()
BUILT=s.build(copy.deepcopy(BASE),preserve=False)
MECH=BUILT['mech']
PARAMS=BASE['input']['parameters']
CAND={c['id']:c for c in BASE['input']['candidates']}
RES={r['id']:r for r in BUILT['candidates']}


def evaluate(c):return s.evaluate(c,MECH,BASE['lock'],PARAMS,BASE['approval'])[0]


def variant(cid,fn):
    c=copy.deepcopy(CAND[cid]);fn(c);return c


class Stage31(unittest.TestCase):
    def rejects(self,c,text):
        with self.assertRaises(ValueError) as caught:evaluate(c)
        self.assertIn(text,str(caught.exception))

    def test_deterministic_outputs_match_committed_files(self):
        again=s.outputs(s.build(copy.deepcopy(BASE),preserve=False),BASE['input'])
        self.assertEqual(again,s.outputs(BUILT,BASE['input']))
        self.assertEqual(set(again),set(s.GENERATED))
        for name,body in again.items():
            if name!='report.json':self.assertEqual((s.OUT/name).read_text(),body,name)

    def test_recommendation_is_the_unique_candidate_meeting_all_criteria(self):
        self.assertEqual({k:all(r['criteria'].values()) for k,r in RES.items()},{'A':False,'B':True,'C':False})
        self.assertEqual(RES['A']['criteria'],{'K1':True,'K2':False,'K3':False,'K4':True})
        self.assertEqual(RES['C']['criteria'],{'K1':True,'K2':True,'K3':True,'K4':False})
        self.assertEqual(BUILT['report']['recommendation']['id'],'B')
        self.assertEqual({k:r['status'] for k,r in RES.items()},{'A':'REJECTED_BY_CRITERIA','B':'RECOMMENDABLE_UNDER_MODEL_CONDITIONS','C':'REJECTED_BY_CRITERIA'})
        self.assertEqual((RES['A']['failed_criteria'],RES['C']['failed_criteria']),(['K2','K3'],['K4']))
        data=copy.deepcopy(BASE);data['input']['recommendation']['id']='C'
        with self.assertRaises(ValueError):s.build(data,preserve=False)

    def test_identity_and_fixed_conditions_preserved(self):
        ident=BUILT['report']['identity']
        self.assertEqual(len(ident['J_SIG_J_PWR_conductors']),11)
        self.assertEqual(ident['harness']['status'],'UNCHANGED_FROM_STAGE28')
        self.assertEqual(ident['panel_lock_sha256'],BASE['report30']['source_sha256']['design/grid/placements.lock.json'])
        for cid,geo in BUILT['geo'].items():
            for ref,g in geo.items():
                h=MECH['headers'][ref]
                self.assertEqual((g['pins'],g['header_mpn'],g['board'],g['face_z_mm']),(h['pins'],h['header_mpn'],h['board'],h['pad_depth_mm']))
                self.assertEqual(g['moved'],ref in CAND[cid]['header_moves'])
        self.assertFalse(any(g['moved'] for g in BUILT['geo']['A'].values()))
        self.assertEqual({r:m['rotation_deg'] for r,m in CAND['B']['header_moves'].items()},{'A01:J-SIG:middle':90,'A01:J-PWR:middle':90})
        self.assertEqual({g['pin_row_axis'] for r,g in BUILT['geo']['B'].items() if g['moved']},{'y'})

    def test_both_cables_and_crossing_detection(self):
        for r in RES.values():
            self.assertTrue(r['cable_to_cable']['clear'])
            self.assertGreaterEqual(r['cable_to_cable']['min_surface_gap_mm'],0.5)
        bund={k:s.bundle(PARAMS,k,'ROUND_BUNDLE') for k in s.LINKS}
        line=lambda a,b:s.samples(s.fillet_route([a,[(a[i]+b[i])/2 for i in range(3)],b],5.0,(0.0,0.0)),bund['J-SIG'])
        crossing,_=s.cable_gap(line([250,160,44],[260,170,44]),line([250,170,44.5],[260,160,44.5]))
        apart,_=s.cable_gap(line([250,160,44],[260,160,44]),line([250,166,44],[260,166,44]))
        self.assertLess(crossing,0.0);self.assertAlmostEqual(apart,6-3.0-0.2,places=6)
        self.assertTrue(all(BUILT['common']['straight_proxies_cross_rail_middle_0'].values()))
        self.assertEqual(len(BUILT['common']['straight_proxies_cross_rail_middle_0']),11)

    def test_rail_without_notch_rejects_round_bundles(self):
        r=evaluate(variant('B',lambda c:c.__setitem__('rail_reliefs',[])))
        self.assertEqual(r['status'],'REJECTED')
        for k in s.LINKS:self.assertLess(r['routes'][k]['min_surface_clearance_mm'],0.5)

    def test_known_infeasible_stage30_candidates_rejected(self):
        screen={w['id']:w for w in BUILT['screen']}
        self.assertEqual(set(screen),{'W1','W2','W3','W4'})
        for w in screen.values():
            self.assertEqual(w['stage31_status'],'REJECTED')
            self.assertTrue(any(x.startswith('bend: bend radius 5.0 mm does not fit leg 0') for x in w['reasons']))
            self.assertTrue(any('no J-SIG route' in x for x in w['reasons']))
        self.assertTrue(any('rail:middle:0' in x for x in screen['W1']['reasons']))
        self.assertTrue(any('board:A01-middle' in x for x in screen['W2']['reasons']))
        self.assertTrue(any('J1710' in x for x in screen['W3']['reasons']))

    def test_header_move_guards(self):
        self.rejects(variant('B',lambda c:c['header_moves']['A01:J-PWR:middle'].__setitem__('origin_mm',[266.0,170.0])),'release sweep overlaps')
        self.rejects(variant('B',lambda c:c['header_moves']['A01:J-SIG:middle'].__setitem__('rotation_deg',45)),'quarter turn')
        self.rejects(variant('B',lambda c:c['header_moves'].__setitem__('A01:C-SIG:middle',{'origin_mm':[244,278],'rotation_deg':0})),'outside the approval')
        self.rejects(variant('B',lambda c:c['header_moves']['A01:J-PWR:middle'].__setitem__('origin_mm',[320.0,174.6])),'on its board')

    def test_notch_guards(self):
        self.rejects(variant('B',lambda c:c['rail_reliefs'][0].__setitem__('relieved_top_z_mm',44.5)),'smaller than the route needs N1')
        self.rejects(variant('B',lambda c:c['rail_reliefs'][1].__setitem__('relieved_top_z_mm',43.0)),'not the minimum plus allowance')
        self.rejects(variant('B',lambda c:c['rail_reliefs'][0].__setitem__('obstacle','rail:middle:2')),'outside the approval')

    def test_route_guards(self):
        self.rejects(variant('B',lambda c:c['routes']['J-SIG']['waypoints_mm'][0].__setitem__(0,212)),'leave the housing along its axis')
        def tight(c):c['routes']['J-SIG']['waypoints_mm'][1][1]=168.0
        self.rejects(variant('B',tight),'does not fit leg')

    def test_release_sweeps_and_foreign_bounds(self):
        a=RES['A']['release_sweeps'];b=RES['B']['release_sweeps']
        self.assertIn('J1710',[x['ref'] for x in a['A01:J-PWR:middle']['foreign_xy_overlaps']])
        self.assertIn('J1510',[x['ref'] for x in a['A01:J-SIG:middle']['foreign_xy_overlaps']])
        self.assertTrue(all(not v['foreign_xy_overlaps'] and not v['known_overlaps'] for v in b.values()))
        self.assertEqual(RES['B']['routes']['J-SIG']['foreign_depth_bounds'],{})
        self.assertEqual(set(RES['B']['routes']['J-PWR']['foreign_depth_bounds']),{'SW1401','SW1501','SW1601'})
        self.assertGreaterEqual(RES['B']['tightest_sweep_gap_mm'],0.5)
        self.assertLess(RES['A']['tightest_sweep_gap_mm'],0.5)
        self.assertLess(RES['A']['smallest_foreign_rear_side_allowance_mm'],12.4)
        rect=[201.65,179.75,208.25,180.0]
        self.assertTrue(s.shielded(rect,36.6,BUILT['obs']['B']))
        self.assertFalse(s.shielded(rect,36.6,[o for o in BUILT['obs']['B'] if o['id']!='board:A01-jack']))

    def test_lengths_are_design_values_and_unknowns_stay_null(self):
        for r in RES.values():
            for k in s.LINKS:
                R=r['routes'][k]
                self.assertTrue(R['length_status'].startswith('DESIGN_LENGTH_PROPOSAL'))
                self.assertGreaterEqual(R['design_length_proposal_mm'],R['installed_pad_to_pad_design_length_mm']+10)
                self.assertTrue(all(x>=0 for x in R['release_extra_length_mm']))
                self.assertEqual([c['case'] for c in R['release_cases']],['installed','middle withdrawn 15 mm','local withdrawn 15 mm','both withdrawn 15 mm'])
                self.assertEqual(R['straight_from_exit_mm']['middle'],2.0)
                self.assertGreaterEqual(R['straight_from_exit_mm']['local'],2.0)
                self.assertTrue(all(b['radius_mm']==5.0 for b in R['bends']))
            for t in r['retention']:self.assertIsNone(t['dimensions_mm'])
            for n in r['rail_reliefs']:self.assertTrue(n['strength'].startswith('NOT_CALCULATED'))
        rep=BUILT['report']
        self.assertEqual((rep['physical'],rep['native'],rep['external_contact']),('NOT_RUN','NOT_RUN','NONE'))
        self.assertTrue(all(m['status']=='NOT_RUN' and m['value'] is None for m in rep['measurements']))
        for k in ('M-01','M-09','M-12'):self.assertEqual(rep['decision_status'][k],'NOT_RUN')

    def test_inputs_reject_claims_and_measured_unknowns(self):
        for fn,text in ((lambda d:d['input']['candidates'][1].__setitem__('status','PASS'),'unsupported pass claim'),
                        (lambda d:d['input']['parameters']['foreign_depth'].__setitem__('value',34),'unknowns stay null'),
                        (lambda d:d['input']['parameters']['wire_od_mm'].__setitem__('value',0.8),'maximum JST insulation OD'),
                        (lambda d:d['input']['parameters']['placement_margin_mm'].__setitem__('class','MEASURED'),'parameter class')):
            data=copy.deepcopy(BASE);fn(data)
            with self.assertRaises(ValueError) as caught:s.build(data,preserve=False)
            self.assertIn(text,str(caught.exception))

    def test_core_service_and_flat_slot(self):
        for r in RES.values():self.assertGreater(r['service']['min_core_motion_clearance_mm'],0.5)
        c=RES['C']['routes']
        self.assertEqual(c['J-SIG']['dressing']['flat_width_mm'],7.0)
        self.assertAlmostEqual(RES['C']['tightest_spare_beyond_margin_mm'],0.1,places=6)
        self.assertTrue(any(k['id'].startswith('rail:middle:0') for k in c['J-SIG']['nearest_keep_outs_mm']))


if __name__=='__main__':unittest.main()
