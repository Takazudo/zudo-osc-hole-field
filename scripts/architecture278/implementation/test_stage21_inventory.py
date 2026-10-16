"""Adversarial source, sourcing and physical-boundary regressions."""
import copy
import json
import unittest
import stage21_inventory as s


class Inventory(unittest.TestCase):
    def setUp(self):
        self.spec = s.read(s.OUT/'inventory-input.json')
        self.land = s.read(s.OUT/'footprint-input.json')
        self.previous = s.read(s.ROOT/s.REL/'stage11/identity-input.json')
        self.packages = s.read(s.ROOT/s.REL/'stage16/inputs-report.json')['packages']
        self.transport = s.read(s.ROOT/s.REL/'stage17/generated/transport-component-rows.json')
        self.footprints = {n:(s.ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/f'{n}.kicad_mod').read_text() for n in ('R0603','C0603')}

    def run_audit(self):
        return s.analyze(self.spec,self.land,self.previous,self.packages,self.transport,self.footprints)

    def test_complete_candidates(self):
        report=self.run_audit()
        self.assertEqual(len(report['candidates']),19)
        self.assertAlmostEqual(report['candidates']['R7113']['conditional_70C_working_voltage_bound_V'],3.1606961258558215)
        self.assertFalse(report['electrical_acceptance'])
        self.assertEqual(report['footprint_comparison']['C0603']['delta_captured_minus_recommended_mm']['B'],{'pad_center_abs_x':-.1,'pad_length_x':-.15,'pad_width_y':-.1})

    def test_omitted_reference(self):
        del self.spec['selections']['R7101']
        with self.assertRaisesRegex(ValueError,'complete19'):self.run_audit()

    def test_every_source_identity_dimension_is_bound(self):
        original=copy.deepcopy(self.spec)
        for key in ('pins','unit_records','symbol','footprint','canonical','placement'):
            with self.subTest(key=key):
                self.spec=copy.deepcopy(original);self.spec['selections']['C7104']['captured_source'][key]={}
                with self.assertRaisesRegex(ValueError,'source identity'):self.run_audit()

    def test_wrong_value_candidate_or_grade(self):
        for mpn in ('RT0603BRD07100KL','RC0603FR-0710KL','RT0603BRD0710K0L'):
            self.spec['selections']['R7101']['candidate_mpn']=mpn
            with self.assertRaisesRegex(ValueError,'candidate identity'):self.run_audit()

    def test_rating_and_dielectric_substitution(self):
        original=copy.deepcopy(self.spec)
        for mpn,key,value in [('RT0603BRD0710KL','tolerance_fraction',.01),('RT0603BRD0710KL','power_W_at_70C',1),('C0603C103J5RACTU','dielectric','C0G'),('C0603C100J5GACTU','value_SI',1e-10),('RT0603BRD0710KL','body_nominal_mm',[1,2,3])]:
            with self.subTest(key=key):
                self.spec=copy.deepcopy(original);self.spec['sources'][mpn]['ratings'][key]=value
                with self.assertRaisesRegex(ValueError,'rating substitution'):self.run_audit()

    def test_supplier_cannot_supply_primary_ratings(self):
        self.spec['sources']['RT0603BRD0710KL']['authority']='SUPPLIER'
        with self.assertRaisesRegex(ValueError,'primary source'):self.run_audit()

    def test_all_unbound_annotations_preserved(self):
        del self.spec['unbound']['TP17901']
        with self.assertRaisesRegex(ValueError,'all24'):self.run_audit()

    def test_annotation_not_fitted(self):
        for key in ('in_bom','on_board'):
            self.spec['unbound']['TP17901'][key]=True
            with self.assertRaisesRegex(ValueError,'all24'):self.run_audit()

    def test_no_guessed_drill(self):
        self.land['DIN']['recommended_finished_hole_mm']=1
        with self.assertRaisesRegex(ValueError,'guessed DIN'):self.run_audit()

    def test_no_physical_qualification(self):
        self.land['capacitor']['qualified']=True
        with self.assertRaisesRegex(ValueError,'qualification boundary'):self.run_audit()

    def test_wrong_metric_size_row(self):
        self.land['capacitor']['density_patterns_mm']['B']['pad_center_abs_x']=.33
        with self.assertRaisesRegex(ValueError,'Table3'):self.run_audit()

    def test_no_application_acceptance(self):
        self.spec['application_qualified']=True
        with self.assertRaisesRegex(ValueError,'candidate-only'):self.run_audit()

    def test_no_selected_candidate(self):
        self.spec['selections']['R7101']['adopted']=True
        with self.assertRaisesRegex(ValueError,'selection decision'):self.run_audit()

    def test_missing_supplier_research(self):
        del self.spec['supplier_observations']['RT0603BRD0710KL']
        with self.assertRaisesRegex(ValueError,'sourcing outcomes'):self.run_audit()

    def test_stock_is_not_allocation(self):
        self.spec['supplier_observations']['RT0603BRD0710KL'][0]['allocation_confirmed']=True
        with self.assertRaisesRegex(ValueError,'not allocation'):self.run_audit()

    def test_unknown_is_not_out_of_stock(self):
        self.spec['supplier_observations']['C0603C100J5GACTU'][0]['status']='OUT_OF_STOCK'
        with self.assertRaisesRegex(ValueError,'lookup failure'):self.run_audit()

    def test_missing_decision_rejected(self):
        self.spec['selections']['C7105']['missing_decision']=''
        with self.assertRaisesRegex(ValueError,'selection decision'):self.run_audit()

    def test_source_receipt_required(self):
        self.spec['sources']['C0603C100J5GACTU']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'dated source receipt'):self.run_audit()

    def test_duplicate_and_rotated_pads_rejected(self):
        for text in (self.footprints['R0603'].replace('(pad 2','(pad 1'),self.footprints['R0603'].replace('0.00 0.00)','0.00 90.00)'),self.footprints['R0603']+'(pad 3 smd circle (at 0 0) (size 1 1))'):
            with self.assertRaises(ValueError):s.geometry(text)

    def test_supplier_code_cannot_move_between_sources(self):
        self.spec['supplier_observations']['RT0603BRD0710KL'][1]['observed']['componentCode']='C110776'
        with self.assertRaisesRegex(ValueError,'source/code'):self.run_audit()

    def test_no_missing_land_source(self):
        del self.spec['sources']['kemet-x7r']
        with self.assertRaisesRegex(ValueError,'mechanical source'):self.run_audit()


class SupplierParser(unittest.TestCase):
    def page(self,rows):
        text='\n'.join(json.dumps({'componentInfo':r},separators=(',',':')) for r in rows)
        return '<script>self.__next_f.push('+json.dumps([1,text])+')</script>'

    def row(self):
        return {'componentModelEn':'RT0603BRD071KL','componentCode':'C110776','componentBrandEn':'YAGEO','overseasStockCount':42,'assemblyComponentFlag':False}

    def test_exact_snapshot(self):
        self.assertEqual(s.parse_jlc(self.page([self.row()]),'RT0603BRD071KL','C110776'),self.row())

    def test_url_title_and_related_stock_not_evidence(self):
        with self.assertRaisesRegex(ValueError,'no server'):s.parse_jlc('<title>RT0603BRD071KL C110776</title> stock42','RT0603BRD071KL','C110776')

    def test_wrong_part_or_code(self):
        for key in ('componentModelEn','componentCode'):
            row=self.row();row[key]='wrong'
            with self.assertRaisesRegex(ValueError,'identity mismatch'):s.parse_jlc(self.page([row]),'RT0603BRD071KL','C110776')

    def test_conflicting_or_invalid_stock(self):
        row=self.row();other=dict(row,overseasStockCount=43)
        with self.assertRaisesRegex(ValueError,'conflicting'):s.parse_jlc(self.page([row,other]),'RT0603BRD071KL','C110776')
        for value in (-1,True,float('nan')):
            row['overseasStockCount']=value
            with self.assertRaisesRegex(ValueError,'invalid supplier stock'):s.parse_jlc(self.page([row]),'RT0603BRD071KL','C110776')

    def test_product_reference_and_split_stream(self):
        stream='1:{"componentInfo":"$59"}\n59:'+json.dumps(self.row(),separators=(',',':'))+'\n'
        html=''.join('<script>self.__next_f.push('+json.dumps([1,chunk])+')</script>' for chunk in (stream[:53],stream[53:]))
        self.assertEqual(s.parse_jlc(html,'RT0603BRD071KL','C110776'),self.row())
        for bad in ('1:{"componentInfo":"$59"}',stream+stream,stream.replace('"$59"','"$unsupported"')):
            page='<script>self.__next_f.push('+json.dumps([1,bad])+')</script>'
            with self.assertRaises(ValueError):s.parse_jlc(page,'RT0603BRD071KL','C110776')


if __name__=='__main__':unittest.main()
