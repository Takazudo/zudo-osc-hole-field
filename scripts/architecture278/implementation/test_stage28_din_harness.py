import copy
import unittest
import stage28_din_harness as s

BASE=s.load()


def mutated(fn):
    data=copy.deepcopy(BASE);fn(data);return data


class Stage28(unittest.TestCase):
    def rejects(self,fn,text=None):
        with self.assertRaises(ValueError) as caught:s.build(mutated(fn),preserve=False)
        if text:self.assertIn(text,str(caught.exception))

    def test_baseline_counts_and_conflict(self):
        ledger,report=s.build(copy.deepcopy(BASE),preserve=False)
        self.assertEqual(len(ledger['conductors']),34);self.assertEqual(len(ledger['din_contacts']),96)
        self.assertTrue(report['din']['mirror_conflict']);self.assertEqual(report['din']['proper_handed_candidate'],['column_reversal'])
        self.assertEqual(report['din']['candidates']['row_reversal']['fixing_hole_shift_mm'],.6)
        self.assertTrue(all(r['results']=='NOT_RUN' for r in ledger['conductors']+ledger['din_contacts']))

    def test_generated_files_are_current(self):
        ledger,report=s.build(copy.deepcopy(BASE),preserve=False)
        report['preservation_baseline']=s.read(s.OUT/'report.json')['preservation_baseline']
        for name,body in s.outputs(ledger,report,BASE).items():self.assertEqual((s.OUT/name).read_text(),body,name)

    def test_missing_contact(self):
        self.rejects(lambda d:d['mech']['din_connectors']['middle']['pads_xyz_mm'].pop('b17'),'coincide')
        def both(d):
            for side in ('middle','rear'):d['mech']['din_connectors'][side]['pads_xyz_mm'].pop('b17')
        self.rejects(both,'complete 96')

    def test_one_side_mirrored(self):
        def f(d):
            pads=d['mech']['din_connectors']['middle']['pads_xyz_mm']
            for p in pads:pads[p]=[[598-pads[p][0][0],pads[p][0][1],pads[p][0][2]]]
        self.rejects(f,'coincide')

    def test_both_sides_relabeled_mirror_must_update_decision(self):
        def f(d):
            for side in ('middle','rear'):
                pads=d['mech']['din_connectors'][side]['pads_xyz_mm'];old=copy.deepcopy(pads)
                for p in pads:pads[p]=old[p[0]+str(33-int(p[1:]))]
        self.rejects(f,'D02')

    def test_resolved_status_without_resolution(self):
        self.rejects(lambda d:d['din']['rows'][1].update(status='CONFIRMED_FROM_DRAWING'),'D02')

    def test_contact_swap(self):
        def f(d):
            for side in ('middle','rear'):
                pads=d['mech']['din_connectors'][side]['pads_xyz_mm'];pads['c1'],pads['c2']=pads['c2'],pads['c1']
        self.rejects(f,'rigid')

    def test_net_swap_on_one_connector(self):
        def f(d):
            pins=d['inventory']['unbound']['J17910']['pins'];pins['c1'],pins['c2']=pins['c2'],pins['c1']
        self.rejects(f,'drift J17910')

    def test_nc_contact_connected(self):
        self.rejects(lambda d:d['inventory']['unbound']['J17909']['pins'].update(a5='AGND'))

    def test_unsupported_process_pass(self):
        self.rejects(lambda d:d['din']['rows'][10].update(status='PASS'))
        self.rejects(lambda d:d['measurements']['measurements'][0].update(result='PASS'))
        self.rejects(lambda d:d['policy']['route'][0].update(status='QUALIFIED'),'pass claim')
        self.rejects(lambda d:d['questions'].update(status='SENT'))
        self.rejects(lambda d:d['din']['rows'][10]['confirmed'].append('Assembler profile qualified for these parts'),'text')
        self.rejects(lambda d:d['questions']['questions'][0]['decision'][0].update(then=''),'decision')

    def test_unknown_values_not_zeroed(self):
        def ir(d):
            i=next(x for x in d['policy']['inspection'] if x['id']=='I-IR');i['limit']=0
        self.rejects(ir,'zeroed')
        self.rejects(lambda d:d['policy']['gh'].update(selected_wire_mpn='UL1571-26'))
        self.rejects(lambda d:d['interfaces']['wires'][0].update(wire_nominal_mm=0),'zeroed')
        self.rejects(lambda d:d['interfaces']['terminal_wires'][0].update(wire_tolerance_mm=0),'zeroed')
        self.rejects(lambda d:d['policy']['tail'].update(clearance_mm=0),'margin')

    def test_open_row_requires_question(self):
        self.rejects(lambda d:d['din']['rows'][2].update(confirmation_needed=[]),'question')
        self.rejects(lambda d:d['din']['rows'][3].update(pass_evidence=['M-99']),'pass evidence')

    def test_fixed_positions(self):
        self.rejects(lambda d:d['mech']['headers']['A01:J-SIG:local']['pads_xyz_mm']['1'][0].__setitem__(0,211),'Stage10')
        self.rejects(lambda d:d['mech']['DIN_flange_holes'][0].update(point_mm=[298.7,183.0]),'fixing holes')
        def shift(d):
            for side in ('middle','rear'):
                for v in d['mech']['din_connectors'][side]['pads_xyz_mm'].values():v[0][0]+=.1
        self.rejects(shift,'grid moved')
        self.rejects(lambda d:d['mech']['terminal_lands'][0].update(xyz_mm=[236,117,35]),'moved')

    def test_gh_conductor_identity(self):
        self.rejects(lambda d:d['interfaces']['wires'][3].update(net='/A01/REF5'))
        self.rejects(lambda d:d['interfaces']['wires'].pop(),'20 GH')

    def test_annotation_flags(self):
        self.rejects(lambda d:d['inventory']['unbound']['TP17901'].update(in_bom=True),'flags')

    def test_receipts(self):
        self.rejects(lambda d:d['sources']['jlc-pcb'].update(retrieved_UTC='2026-10-16T10:00:00+00:00'),'dated')
        self.rejects(lambda d:d['sources']['harting-male'].update(sha256='0'*63+'1'),'Stage5')

    def test_frame_and_trimmers(self):
        self.rejects(lambda d:d['lock']['frame'].update(positive_y='up'),'frame')
        self.rejects(lambda d:d['o1']['placements'].__setitem__(0,d['o1']['placements'][0]) or [p.update(trim_tool_diameter_mm=None) for p in d['o1']['placements'] if p['ref']=='RVO1109'],'trimmer')

    def test_segment_box(self):
        self.assertTrue(s.segment_box([0,0,0],[10,10,10],[4,4,4],[6,6,6]))
        self.assertFalse(s.segment_box([0,0,0],[10,0,0],[4,1,-1],[6,2,1]))


if __name__=='__main__':unittest.main()
