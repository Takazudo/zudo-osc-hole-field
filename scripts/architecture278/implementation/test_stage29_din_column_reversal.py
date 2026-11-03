import copy
import unittest
import stage29_din_column_reversal as s

BASE=s.load()


def mutated(fn):
    data=copy.deepcopy(BASE);fn(data);return data


def candidate(data,female=True,male=True,label=s.rev):
    old=s.stage10_positions(data['mech'])
    data['candidate']={k:{p:copy.deepcopy(v[label(p)] if flip else v[p]) for p,v in [(p,pads) for p in pads]} for (k,pads),flip in zip(old.items(),(female,male))}
    return data['candidate']


def all_pins(data,fn):
    for pins in (data['interfaces']['DIN_pinmap'],data['inventory']['unbound']['J17909']['pins'],data['inventory']['unbound']['J17910']['pins'],
            data['mech']['din_connectors']['middle']['pins'],data['mech']['din_connectors']['rear']['pins']):fn(pins)


class Stage29(unittest.TestCase):
    def rejects(self,fn,text):
        with self.assertRaises(ValueError) as caught:s.build(mutated(fn),preserve=False)
        self.assertIn(text,str(caught.exception))

    def test_candidate_mapping_and_counts(self):
        cmap,report=s.build(copy.deepcopy(BASE),preserve=False)
        self.assertEqual(len(cmap['contacts']),192)
        for ref in ('J17909','J17910'):
            rows=[r for r in cmap['contacts'] if r['connector']==ref]
            self.assertEqual((sum(1 for r in rows if r['net']),sum(1 for r in rows if r['nc'])),(16,80))
        old=s.stage10_positions(BASE['mech'])
        for r in cmap['contacts']:
            pads=old[r['side']];self.assertEqual(r['candidate_xy_mm'],pads[s.rev(r['physical_contact'])][0][:2])
            self.assertEqual(r['net'],BASE['interfaces']['DIN_pinmap'][r['physical_contact']])
        self.assertEqual(report['counts']['moved_contacts_per_connector'],96)

    def test_determinants_views_corners_and_pin1(self):
        _,report=s.build(copy.deepcopy(BASE),preserve=False);m=report['matrices'];v=report['component_side_views']
        self.assertEqual((m['female']['candidate_det'],m['male']['candidate_det']),(1,-1))
        self.assertEqual((m['female']['stage10_det'],m['male']['stage10_det']),(-1,1))
        self.assertTrue(all(v[x]['candidate_view_det']==1 and v[x]['stage10_view_det']==-1 for x in v))
        self.assertTrue(all(v[x]['candidate_drawing_to_component_view']==[[0,-1],[1,0]] for x in v))
        old=s.stage10_positions(BASE['mech'])
        for side in ('female','male'):
            for p in s.CORNERS:self.assertEqual(report['corners'][side][p]['candidate_xy_mm'],old[side][s.rev(p)][0][:2])
            self.assertEqual(report['pin1_marker_xy_mm'][side],old[side]['a32'][0][:2])
        self.assertEqual(report['fixing_holes_xy_mm'],[[299.3,183.0],[299.3,273.0]])

    def test_drawing_offset_from_vector(self):
        _,report=s.build(copy.deepcopy(BASE),preserve=False);f=report['drawings']['female']
        self.assertEqual(f['fixing_hole_offset_side'],'row a');self.assertAlmostEqual(f['fixing_hole_offset_from_vector_mm'],.3,places=3)
        self.assertAlmostEqual(f['fixing_hole_spacing_from_vector_mm'],90,places=3)
        self.assertEqual(report['decision_status']['M-01'],'NOT_RUN');self.assertTrue(report['decision_status']['D02'].startswith('CONFLICT_REQUIRES_DECISION'))

    def test_generated_files_are_current(self):
        cmap,report=s.build(copy.deepcopy(BASE),preserve=False)
        report['preservation_baseline']=s.read(s.OUT/'report.json')['preservation_baseline']
        s.check_outputs(s.outputs(cmap,report))

    def test_stale_output_rejected(self):
        cmap,report=s.build(mutated(lambda d:d['reading']['male'].update(contact_attribute='pin type B')),preserve=False)
        report['preservation_baseline']=s.BASE
        with self.assertRaises(ValueError):s.check_outputs(s.outputs(cmap,report))

    def test_one_sided_reversal(self):
        self.rejects(lambda d:candidate(d,male=False),'handedness does not match drawing view male')
        self.rejects(lambda d:candidate(d,female=False),'handedness does not match drawing view female')

    def test_unreversed_stage10(self):
        self.rejects(lambda d:candidate(d,female=False,male=False),'handedness does not match drawing view female')

    def test_row_reversal_moves_fixing_holes(self):
        self.rejects(lambda d:candidate(d,label=lambda p:'cba'['abc'.index(p[0])]+p[1:]),'fixing holes moved')

    def test_missing_and_duplicate_contact(self):
        self.rejects(lambda d:candidate(d)['female'].pop('b17'),'complete 96')
        def dup(d):
            c=candidate(d)['male'];c['c2']=copy.deepcopy(c['c1'])
        self.rejects(dup,'bijection')

    def test_contact_swap(self):
        def f(d):
            for c in candidate(d).values():c['c1'],c['c2']=c['c2'],c['c1']
        self.rejects(f,'rigid')

    def test_moved_hole_and_plane(self):
        def f(d):
            for c in candidate(d).values():
                for p in c:c[p][0][0]=round(c[p][0][0]+.1,6)
        self.rejects(f,'bijection')
        def z(d):
            for p in candidate(d)['male'].values():p[0][2]=70.8
        self.rejects(z,'board plane male')
        self.rejects(lambda d:d['mech']['DIN_flange_holes'][0].update(point_mm=[299.9,183.0]),'fixing holes moved')

    def test_net_renumbering_and_nc_connection(self):
        def renumber(d):
            def f(pins):
                old=dict(pins)
                for p in pins:pins[p]=old[s.rev(p)]
            all_pins(d,f)
        self.rejects(renumber,'Stage28 ledger')
        self.rejects(lambda d:all_pins(d,lambda pins:pins.update(a5='AGND')),'Stage28 ledger')
        self.rejects(lambda d:d['inventory']['unbound']['J17910']['pins'].update(a5='AGND'),'drift J17910')

    def test_view_errors(self):
        self.rejects(lambda d:d['reading']['male'].update(top_to_bottom=['a','b','c']),'view reading differs')
        def both(d):
            for x in (d['reading']['male'],d['evidence']['DIN']['male']):x['top_to_bottom']=['a','b','c']
        self.rejects(both,'drawing view handedness')
        self.rejects(lambda d:d['lock']['frame'].update(positive_y='up'),'locked front-view frame')

    def test_vector_evidence_tamper(self):
        def side_c(d):
            for c in d['vector']['female']['other_circles']:c['centre_pt'][1]=round(322.309265+.850342,6)
        self.rejects(side_c,'offset not toward row a')
        self.rejects(lambda d:d['vector']['female']['other_circles'][0]['centre_pt'].__setitem__(0,229.0),'90 mm')
        def pitch(d):
            v=d['vector']['male'];v['columns_x_pt_left_to_right'][-1]+=1;v['contact_centres_pt']=[[x,y] for x in v['columns_x_pt_left_to_right'] for y in v['rows_y_pt_top_to_bottom']]
        self.rejects(pitch,'pitch')
        self.rejects(lambda d:d['vector']['male']['contact_centres_pt'].pop(),'96-circle')
        self.rejects(lambda d:d['vector']['male']['other_circles'].append({'diameter_pt':7.9,'centre_pt':[200,160]}),'only the 96')

    def test_receipts_and_claims(self):
        self.rejects(lambda d:d['sources']['harting-male'].update(sha256='0'*64),'differ')
        self.rejects(lambda d:d['sources']['harting-female'].update(retrieved_UTC='2026-10-16T11:49:51+00:00'),'dated')
        self.rejects(lambda d:d['reading'].update(status='PASS'),'pass claim')
        self.rejects(lambda d:d['reading']['female'].update(arrow_side='validated against the part'),'pass claim')

    def test_preservation_baseline(self):
        self.assertEqual(s.protected(),s.BASE)
        _,report=s.build(copy.deepcopy(BASE),preserve=False)
        for path in ('design/architecture-278/implementation/stage10/mechanical-report.json','design/architecture-278/implementation/stage28/harness-ledger.json','design/grid/placements.lock.json'):
            self.assertIn(path,report['source_sha256'])
        self.assertFalse(report['production_CAD_changed'] or report['architecture_adopted'])


if __name__=='__main__':unittest.main()
