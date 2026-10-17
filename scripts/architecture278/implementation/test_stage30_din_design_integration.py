import copy
import math
import re
import unittest
import stage29_din_column_reversal as s29
import stage30_din_design_integration as s

BASE=s.load()
BUILT=s.build(copy.deepcopy(BASE),preserve=False)
DESIGN=s.design_positions(s.read(s.ROOT/s.REL/'stage29/contact-map.json'))
STAGE10=s29.stage10_positions(s29.load()['mech'])


def mutated(fn):
    data=copy.deepcopy(BASE);fn(data);return data


def with_design(fn):
    def apply(data):
        data['design']=copy.deepcopy(DESIGN);fn(data['design'])
    return apply


class Stage30(unittest.TestCase):
    def rejects(self,fn,text):
        with self.assertRaises(ValueError) as caught:s.build(mutated(fn),preserve=False)
        self.assertIn(text,str(caught.exception))

    def test_design_map_keeps_identity_nets_and_nc(self):
        rows=BUILT['cmap']['contacts'];self.assertEqual(len(rows),192)
        pinmap=BASE['graph']['DIN_pinmap']
        for ref in ('J17909','J17910'):
            r=[x for x in rows if x['connector']==ref]
            self.assertEqual((sum(1 for x in r if x['net']),sum(1 for x in r if x['nc'])),(16,80))
            self.assertEqual({x['physical_contact'] for x in r},set(pinmap))
        for x in rows:
            self.assertEqual(x['net'],pinmap[x['physical_contact']])
            self.assertEqual(x['design_xy_mm'],STAGE10[x['side']][s.rev(x['physical_contact'])][0][:2])
        female={x['physical_contact']:x['design_xy_mm'] for x in rows if x['side']=='female'}
        male={x['physical_contact']:x['design_xy_mm'] for x in rows if x['side']=='male'}
        self.assertEqual(female,male)

    def test_determinants_pin1_corners_and_fixed_geometry(self):
        r=BUILT['report']
        self.assertEqual(r['determinants'],{'female':1,'male':-1})
        self.assertEqual(r['pin1_xy_mm'],{'female':[301.54,188.63],'male':[301.54,188.63]})
        self.assertEqual(r['corners']['female'],{'a1':[301.54,188.63],'c1':[296.46,188.63],'a32':[301.54,267.37],'c32':[296.46,267.37]})
        self.assertEqual(r['fixing_holes_xy_mm'],[[299.3,183.0],[299.3,273.0]])
        self.assertEqual(r['status'],'DESIGN_ONLY_PROVISIONAL')
        self.assertTrue(r['decision_status']['D02'].startswith('CONFLICT_REQUIRES_DECISION'))
        self.assertEqual(r['decision_status']['M-01'],'NOT_RUN')

    def test_one_sided_update_rejected(self):
        self.rejects(with_design(lambda d:d.__setitem__('male',copy.deepcopy(STAGE10['male']))),'Stage10 coordinate left in the design map male')
        self.rejects(with_design(lambda d:d.__setitem__('female',copy.deepcopy(STAGE10['female']))),'Stage10 coordinate left in the design map female')

    def test_old_coordinate_mixture_rejected(self):
        self.rejects(with_design(lambda d:d['female'].__setitem__('c4',copy.deepcopy(STAGE10['female']['c4']))),'Stage10 coordinate left in the design map female c4')
        def swap(d):d['male']['a1'],d['male']['a2']=d['male']['a2'],d['male']['a1']
        self.rejects(with_design(swap),'rigid')

    def test_net_change_and_nc_connection_rejected(self):
        def renumber(data):data['graph']['DIN_pinmap']['c1'],data['graph']['DIN_pinmap']['c2']=data['graph']['DIN_pinmap']['c2'],data['graph']['DIN_pinmap']['c1']
        self.rejects(renumber,'Stage15 DIN pin map')
        def nc_edge(data):
            for g in (data['graph'],data['stage16']['transport_contract']):
                g['edges'].append({'net':None,'from':'DIN:middle:a7','to':'DIN:middle:a8','kind':'middle_copper','allocated_developed_mm':9.921,'wire_cut_max_mm':0,'mated_GH_contacts':0,'routed_mm':None})
        self.rejects(nc_edge,'NC DIN contact connected')
        def drift(data):data['stage16']['transport_contract']['edges'][0]['net']='AGND'
        self.rejects(drift,'Stage16 transport contract differs')

    def test_allocations_recomputed_and_paths_resummed(self):
        imp=BUILT['impact'];edges=imp['edges']
        self.assertEqual(sum(1 for e in edges if e['kind']=='DIN_mated_pair'),16)
        self.assertTrue(all(e['design_allocation_mm']==25 and e['delta_allocation_mm']==0 for e in edges if e['kind']=='DIN_mated_pair'))
        copper=[e for e in edges if e['kind']!='DIN_mated_pair'];self.assertEqual(len(copper),34)
        self.assertTrue(all(e['routed_copper_mm'] is None for e in edges))
        nodes=BASE['graph']['nodes'];pos={'DIN:'+s.NODE_SIDE[k]+':'+p:v[0] for k,pads in DESIGN.items() for p,v in pads.items()}
        for e in copper:
            a=pos.get(e['from'],nodes[e['from']]['pad_xyz_mm']);b=pos.get(e['to'],nodes[e['to']]['pad_xyz_mm'])
            self.assertAlmostEqual(e['design_allocation_mm'],s.interfaces.trace_length(a,b),places=5)
            self.assertAlmostEqual(e['design_straight_mm'],math.dist(a,b),places=5)
        changed={e['edge_index']:e['design_allocation_mm'] for e in copper}
        paths=imp['paths']['signal_net_paths'];self.assertEqual(len(paths),11)
        stage15={(r['net'],r['from'],r['to']):r for r in BASE['paths']['signal_net_paths']}
        for r in paths:
            old=stage15[(r['net'],r['from'],r['to'])]
            new=sum(changed.get(j,BASE['graph']['edges'][j]['allocated_developed_mm']) for j in old['edge_indices'])
            self.assertAlmostEqual(r['design_allocation_mm'],new,places=4)
        self.assertEqual(imp['paths']['power_and_return_endpoint_paths'],[]);self.assertEqual(imp['paths']['local_endpoint_paths'],[])
        def moved(data):
            for g in (data['graph'],data['stage16']['transport_contract']):
                g['nodes']['DIN:middle:c1']['pad_xyz_mm']=[296.46,188.63,50];g['nodes']['DIN:rear:c1']['pad_xyz_mm']=[296.46,188.63,69.2]
        self.rejects(moved,'not reproducible from Stage10 DIN XY')
        def unmated(data):
            for g in (data['graph'],data['stage16']['transport_contract']):g['nodes']['DIN:middle:c1']['pad_xyz_mm']=[296.46,188.63,50]
        self.rejects(unmated,'mated DIN pair must coincide')

    def test_connections_traced_for_16_contacts(self):
        c={x['physical_contact']:x for x in BUILT['impact']['contacts']};self.assertEqual(len(c),16)
        self.assertEqual([(l['ref'],l['pin'],l['board']) for l in c['c1']['middle']['connections']],[('A01:J-SIG:middle','1','A01-middle'),('A01:C-SIG:middle','1','A01-middle')])
        self.assertEqual([(l['ref'],l['pin'],l['board']) for l in c['c1']['rear']['connections']],[('U7104','1','A01-core')])
        self.assertEqual([(l['ref'],l['pin']) for l in c['b5']['rear']['connections']],[('A01:K-PWR:local','3')])
        self.assertIsNone(c['c3']['beyond_A01']);self.assertIn('position null',c['b1']['beyond_A01'])

    def test_harness_preserved_and_measurements_stay_null(self):
        h=BUILT['report']['harness']
        self.assertEqual((h['conductors'],h['GH_harnesses'],h['GH_conductors'],h['permanent_tails'],h['land_annotations'],h['DIN_contacts_as_harness']),(34,4,20,14,22,0))
        self.rejects(lambda d:d['ledger28']['conductors'][0]['geometry'].__setitem__('measured_path_mm',91.0),'recorded as a measurement H-J-SIG-1')
        self.rejects(lambda d:d['ledger28']['conductors'][5]['geometry'].__setitem__('chosen_cut_mm',90),'recorded as a measurement')
        self.rejects(lambda d:d['ledger28']['conductors'].pop(),'harness counts changed')
        def din_as_wire(d):d['ledger28']['conductors'][0]['kind']='DIN_HARNESS'
        self.rejects(din_as_wire,'DIN contacts must not become harness conductors')
        inv=copy.deepcopy(s29.load()['inventory']);next(v for k,v in inv['unbound'].items() if k.startswith('TP'))['in_bom']=True
        with self.assertRaises(ValueError) as caught:s.harness_preserved(BASE['ledger28'],BASE['report28'],inv,BASE['policy28'])
        self.assertIn('exclusion flags',str(caught.exception))

    def test_approval_scope_cannot_widen(self):
        self.rejects(lambda d:d['approval'].__setitem__('status','ADOPTED'),'design-only provisional owner record')
        self.rejects(lambda d:d['approval']['scope_excludes'].remove('canonical schematic, board or library changes'),'approval scope widened')
        self.rejects(lambda d:d['approval']['scope_includes'].append('Adopted for manufacturing release'),'manufacturing/qualification scope')
        self.rejects(lambda d:d['approval'].__setitem__('mapping','candidate_position(row, n) = Stage10_position(row, n)'),'approved mapping differs')
        self.rejects(lambda d:d['approval'].__setitem__('result','PASS'),'unsupported pass claim')

    def test_route_keep_out_hits_are_reported(self):
        st={c['id']:c for c in BUILT['study']['candidates']}
        self.assertEqual(BUILT['report']['route_study']['feasible_under_existing_conditions'],[])
        self.assertIn('rail:middle:0',st['W1']['keep_out_hits']);self.assertEqual(st['W1']['status'],'BLOCKED_BY_KEEP_OUT')
        self.assertEqual(st['W3']['status'],'UNKNOWN_FOREIGN_DEPTH');self.assertEqual(st['W4']['status'],'CENTRELINE_CLEAR_UNDER_ASSUMPTIONS')
        self.assertTrue(st['W4']['centreline_clearance_known_keep_outs_mm']>=st['W4']['required_clearance_mm'])
        self.assertFalse(st['W4']['bend_ok_under_assumption'])
        def through_sweep(d):d['route']['candidates'][3]['waypoints_mm'][2]=[260,152,40]
        data=mutated(through_sweep);b=s.build(data,preserve=False)
        w4=next(c for c in b['study']['candidates'] if c['id']=='W4')
        self.assertEqual(w4['status'],'BLOCKED_BY_KEEP_OUT');self.assertIn('release:A01:J-SIG:middle',w4['keep_out_hits'])
        def unrelieved(d):d['route']['candidates'][3].pop('modification')
        self.rejects(unrelieved,'candidate geometry flag W4')
        def missed(d):d['route']['candidates'][3]['modification']['relieved_top_z_mm']=45.5
        self.rejects(missed,'proposed relief smaller than the W4 centreline needs')
        corr=BUILT['study']['corridors'];self.assertEqual(corr['slot_over_ring_mm'],2.4);self.assertTrue(corr['local_end_axial_lead_ceiling_mm']<3)
        self.assertIn('H-J-SIG-1',BUILT['report']['route_study']['J_SIG_proxies_cross_middle_rail'])
        self.assertTrue(34<st['W4']['foreign_depth_cap_that_adds_unknown_hits_z_mm']<35)
        self.assertTrue(st['W3']['foreign_depth_cap_that_adds_unknown_hits_z_mm']<34)
        def deeper(d):d['route']['assumptions']['foreign_unknown_depth_top_z_mm']['value']=36
        self.rejects(deeper,'capped at the middle carrier front')
        a=copy.deepcopy(BASE['route']['assumptions'])
        o=s.obstacles(s29.load()['mech'],BASE['lock'],a,cap=36)
        w4=next(c for c in BASE['route']['candidates'] if c['id']=='W4');o=s.relieve(o,w4['modification'])
        line=[BUILT['study']['exits']['local_exit_mm']]+w4['waypoints_mm']+[BUILT['study']['exits']['middle_exit_mm']]
        self.assertIn('foreign-depth:J1710',s.hits(line,o,BUILT['study']['envelope']['required_centreline_clearance_mm']))

    def test_assumption_recorded_as_measurement_rejected(self):
        self.rejects(lambda d:d['route']['assumptions']['wire_od_mm'].__setitem__('status','MEASURED'),'must not be recorded as measured')
        self.rejects(lambda d:d['route'].__setitem__('status','ROUTE_MEASURED'),'route input status')
        self.rejects(lambda d:d['route']['assumptions']['wire_od_mm'].__setitem__('value',0.8),'assumed OD is the JST GH maximum')

    def test_segment_distance_and_bend_limit(self):
        self.assertAlmostEqual(s.segment_distance([0,0,0],[10,0,0],[5,3,4],[5,3,9]),5.0)
        self.assertAlmostEqual(s.segment_distance([0,0,0],[1,0,0],[3,0,0],[4,0,0]),2.0)
        b=s.bend_limit([[0,0,0],[0,0,1],[0,0,3],[4,0,3],[4,0,1],[4,0,0]])
        self.assertEqual([x['max_radius_mm'] for x in b],[2.0,2.0])
        with self.assertRaises(ValueError):s.bend_limit([[0,0,0],[0,0,1],[1,0,1],[2,0,1]])

    def test_m01_print_geometry_and_labels(self):
        checks=BUILT['report']['m01']['layout_checks']
        for k,v in checks.items():self.assertEqual((v['contacts'],v['pitch_mm'],v['span_a1_a32_mm']),(96,2.54,78.74))
        self.assertEqual((checks['female-design']['fixing_spacing_mm'],checks['female-design']['fixing_offset_toward_row_a_mm']),(90.0,0.3))
        bad=copy.deepcopy(BUILT['layout']);h=bad['female-design']['holes_mm'];h['a1'],h['a32']=h['a32'],h['a1']
        with self.assertRaises(ValueError):s.layout_checks(bad)
        bad=copy.deepcopy(BUILT['layout']);bad['male-design']['holes_mm']=copy.deepcopy(bad['male-stage10']['holes_mm'])
        with self.assertRaises(ValueError) as caught:s.layout_checks(bad)
        self.assertIn('column reversal',str(caught.exception))
        bad=copy.deepcopy(BUILT['layout']);bad['female-stage10']['fixing_mm'][0][0]+=0.6
        with self.assertRaises(ValueError):s.layout_checks(bad)

    def test_pdf_structure_is_valid_and_states_scale(self):
        pdf=BUILT['pdf'];self.assertTrue(pdf.startswith(b'%PDF-1.4'));self.assertIn(b'/Count 5',pdf)
        start=int(re.search(rb'startxref\n(\d+)',pdf).group(1));table=pdf[start:].split(b'\n')
        count=int(table[1].split()[1])
        for i in range(1,count):
            off=int(table[2+i][:10]);self.assertTrue(pdf[off:].startswith(b'%d 0 obj'%i))
        self.assertEqual(pdf.count(b'PRINT AT 100% / ACTUAL SIZE'),4)
        for mark in (b'09032966824',b'09031966922',b'COMPONENT SIDE',b'STAGE10 HISTORICAL',b'STAGE30 DESIGN-ONLY PROVISIONAL',b'RECORD SHEET',b'SCALE CHECK: 100.00 mm'):
            self.assertIn(mark,pdf)
        t=s.record_template();self.assertEqual(t['status'],'M-01_NOT_RUN_EMPTY_TEMPLATE')
        self.assertTrue(all(v is None or v==[] for sheet in t['sheets'].values() for v in sheet.values()))

    def test_generated_files_are_current_and_deterministic(self):
        b=s.build(copy.deepcopy(BASE),preserve=False);b['report']['preservation_baseline']=s.read(s.OUT/'report.json')['preservation_baseline']
        s.check_outputs(s.outputs(b),b['pdf'])
        self.assertEqual(b['pdf'],BUILT['pdf'])

    def test_stale_output_rejected(self):
        b=copy.deepcopy(BUILT);b['report']['preservation_baseline']=s.BASE;bodies=s.outputs(b)
        bodies['route-study.md']+='stale\n'
        with self.assertRaises(ValueError) as caught:s.check_outputs(bodies,b['pdf'])
        self.assertIn('deterministic drift route-study.md',str(caught.exception))
        bodies=s.outputs(b)
        with self.assertRaises(ValueError) as caught:s.check_outputs(bodies,b['pdf']+b' ')
        self.assertIn('m01-print.pdf',str(caught.exception))

    def test_preservation_baseline(self):
        self.assertEqual(s.protected(),'00266037a7e2134c9c6c70d1ae95695932e7f1f6')
        self.assertEqual(BUILT['report']['native'],'NOT_RUN');self.assertFalse(BUILT['report']['production_CAD_changed'])


if __name__=='__main__':unittest.main()
