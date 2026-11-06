"""Adversarial sourcing and proposal boundaries; no network or native tools."""
import copy
import json
import unittest
import stage23_jlc as s

MPN='RT0603BRD0710KL'; CODE='C95204'


def page(row, visible=True, extra=''):
    payload='0:'+json.dumps({'componentInfo':row})+'\n'+extra
    table='<p>MFR.Part #</p><p>'+MPN+'</p><p>JLCPCB Part #</p><p>'+CODE+'</p>'
    if visible:
        table+='<p>Assembly Type</p><p>SMT Assembly</p><p>PCBA Type</p><p>Economic and Standard</p>'
    return table+'<p>Specifications</p><script>self.__next_f.push('+json.dumps([1,payload])+')</script>'


class Sourcing(unittest.TestCase):
    def setUp(self):
        self.e=s.read(s.OUT/'inventory-input.json')
        self.row=copy.deepcopy(self.e['candidates'][MPN]['observation'])
        self.row.pop('visible_service')

    def test_false_flag_is_not_smt_denial(self):
        parsed=s.parse_jlc(page(self.row),MPN,CODE)
        self.assertFalse(parsed['assemblyComponentFlag'])
        result=s.classify(parsed)
        self.assertEqual(result['catalog_assembly_declaration']['Assembly Type'],'SMT Assembly')
        self.assertFalse(result['allocation_confirmed'])
        self.assertIn('UNCONFIRMED',result['order_assembly_eligibility'])

    def test_missing_service_is_not_inferred_from_stock(self):
        with self.assertRaisesRegex(ValueError,'missing explicit service'):
            s.parse_jlc(page(self.row,False),MPN,CODE)

    def test_wrong_exact_mpn_and_code(self):
        for key,value in [('componentModelEn','RT0603FRD0710KL'),('componentCode','C1')]:
            row=self.row|{key:value}
            with self.assertRaisesRegex(ValueError,'identity mismatch'):s.parse_jlc(page(row),MPN,CODE)

    def test_wrong_manufacturer_and_package(self):
        for key,value in [('componentBrandEn','KEMET'),('componentSpecificationEn','0402')]:
            with self.assertRaisesRegex(ValueError,'manufacturer/package'):s.parse_jlc(page(self.row|{key:value}),MPN,CODE)

    def test_related_product_stock_is_ignored(self):
        row=self.row.copy();row.pop('overseasStockCount')
        parsed=s.parse_jlc(page(row,extra='1:'+json.dumps({'relatedProducts':[{'overseasStockCount':999999}]})),MPN,CODE)
        self.assertEqual(s.classify(parsed)['stock_status'],'UNKNOWN')

    def test_zero_stock_is_not_absence_or_allocation(self):
        row=self.row|{'overseasStockCount':0}
        result=s.classify(s.parse_jlc(page(row),MPN,CODE))
        self.assertEqual(result['stock_status'],'OBSERVED_ZERO')
        self.assertFalse(result['allocation_confirmed'])

    def test_invalid_counts(self):
        for value in (-1,True,1.5):
            with self.assertRaisesRegex(ValueError,'invalid count'):s.parse_jlc(page(self.row|{'overseasStockCount':value}),MPN,CODE)

    def test_conflicting_product_records(self):
        extra='1:'+json.dumps({'componentInfo':self.row|{'overseasStockCount':1}})
        with self.assertRaisesRegex(ValueError,'conflicting product'):s.parse_jlc(page(self.row,extra=extra),MPN,CODE)

    def test_unknown_service_and_visible_mismatch(self):
        for value in (3,True,2):
            with self.assertRaises(ValueError):s.parse_jlc(page(self.row|{'componentProductType':value}),MPN,CODE)

    def test_search_zero_is_inconclusive(self):
        with self.assertRaisesRegex(ValueError,'inconclusive'):s.parse_jlc('<p>0 results</p>',MPN,CODE)

    def test_referenced_product_and_missing_reference(self):
        extra='a:'+json.dumps(self.row)
        result=s.parse_jlc(page('$a',extra=extra),MPN,CODE)
        self.assertEqual(result['componentCode'],CODE)
        with self.assertRaisesRegex(ValueError,'missing or duplicate'):s.parse_jlc(page('$b',extra=extra),MPN,CODE)

    def test_other_product_cannot_supply_missing_service(self):
        other='<p>MFR.Part #</p><p>OTHER</p><p>JLCPCB Part #</p><p>C123</p><p>Assembly Type</p><p>SMT Assembly</p><p>PCBA Type</p><p>Economic and Standard</p>'
        html=page(self.row,False).replace('<p>Specifications</p>',other+'<p>Specifications</p>')
        with self.assertRaisesRegex(ValueError,'missing explicit service'):
            s.parse_jlc(html,MPN,CODE)

    def test_record_id_suffix_cannot_satisfy_reference(self):
        with self.assertRaisesRegex(ValueError,'missing or duplicate'):
            s.parse_jlc(page('$a',extra='1a:'+json.dumps(self.row)),MPN,CODE)

    def test_flight_text_length_and_fake_embedded_record(self):
        text='é\n1a:'+json.dumps(self.row)
        payload='a:T'+format(len(text.encode()),'x')+','+text+'b:'+json.dumps(self.row)
        frames=s.flight_frames(payload)
        self.assertEqual(frames['a'],'')
        self.assertEqual(json.loads(frames['b']),self.row)
        self.assertNotIn('1a',frames)
        with self.assertRaisesRegex(ValueError,'truncated'):s.flight_frames('a:Tffff,short')

    def test_duplicate_record_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            s.flight_frames('a:{}\na:{}\n')


class Proposal(unittest.TestCase):
    def setUp(self):
        self.prior=s.read(s.ROOT/s.REL/'stage21/inventory-input.json')
        self.packages=s.read(s.ROOT/s.REL/'stage16/inputs-report.json')['packages']
        self.requirements=s.read(s.ROOT/s.REL/'stage22/requirements-report.json')
        self.e=s.read(s.OUT/'inventory-input.json')

    def run_proposal(self):
        return s.propose(self.prior,self.packages,self.requirements,self.e)

    def test_missing_guidance_receipt_and_source_substitution(self):
        receipts=s.read(s.OUT/'retrieval.json')
        for sid in ('frontend','sourcing','matching','global-sourcing'):
            changed=copy.deepcopy(receipts);del changed[sid]
            with self.assertRaisesRegex(ValueError,'guidance source binding'):
                s.validate_guidance(self.e,changed)
        self.e['service_guidance']['matching']['source_id']='sourcing'
        with self.assertRaisesRegex(ValueError,'guidance source binding'):
            s.validate_guidance(self.e,receipts)

    def test_guidance_url_and_frontend_hash_substitution(self):
        receipts=s.read(s.OUT/'retrieval.json');receipts['matching']['url']='https://jlcpcb.com/other'
        with self.assertRaisesRegex(ValueError,'official URL'):s.validate_guidance(self.e,receipts)
        receipts=s.read(s.OUT/'retrieval.json');receipts['frontend']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'frontend interpretation'):s.validate_guidance(self.e,receipts)

    def test_complete_unapplied_proposal(self):
        result=self.run_proposal()
        self.assertEqual(result['counts'],{'references':19,'exact_candidates':9,'substitutions':0})
        self.assertFalse(result['candidate_adoption'])
        self.assertTrue(all(not op['ready_to_apply'] for op in result['operations']))
        self.assertIn('AC center-null bandwidth',result['owner_choices_not_made'])

    def test_missing_candidate(self):
        del self.e['candidates'][MPN]
        with self.assertRaisesRegex(ValueError,'roster'):self.run_proposal()

    def test_missing_unit_rewiring_and_metadata_substitution(self):
        original=copy.deepcopy(self.packages['R7101'])
        for key,value in [('unit_records',[]),('pins',{'1':'AGND','2':'AGND'}),('selected_mpn','other')]:
            self.packages['R7101']=original|{key:value}
            with self.assertRaisesRegex(ValueError,'drift'):self.run_proposal()

    def test_omitted_reference(self):
        del self.prior['selections']['R7101']
        with self.assertRaisesRegex(ValueError,'roster'):self.run_proposal()

    def test_wrong_supplier_code(self):
        self.e['candidates'][MPN]['code']='C123'
        with self.assertRaisesRegex(ValueError,'mapping'):self.run_proposal()

    def test_primary_rating_substitution(self):
        self.e['candidates'][MPN]['ratings']['tolerance_fraction']=.01
        with self.assertRaisesRegex(ValueError,'rating substitution'):self.run_proposal()

    def test_primary_digest_substitution(self):
        self.e['candidates'][MPN]['manufacturer_source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'source substitution'):self.run_proposal()

    def test_assumption_promotion(self):
        self.requirements['assumptions']['owner_approved']=True
        with self.assertRaisesRegex(ValueError,'performance approval'):self.run_proposal()

    def test_manual_population_or_adoption(self):
        self.e['manual_population_required']=True
        with self.assertRaisesRegex(ValueError,'sourcing route'):self.run_proposal()
        self.e['manual_population_required']=False;self.e['adopted']=True
        with self.assertRaisesRegex(ValueError,'promotion'):self.run_proposal()

    def test_replacement_rating_rejections(self):
        old=self.prior['sources'][MPN]['ratings']
        for key,value in [('value_SI',22000),('tolerance_fraction',.01),('power_W_at_70C',.063),('TCR_ppm_per_C',100),('body_nominal_mm',[1,.5,.5]),('temperature_range_C',[-40,85])]:
            with self.assertRaises(ValueError):s.compare_candidate(old,old|{key:value})

    def test_capacitor_dielectric_voltage_and_tolerance(self):
        old=self.prior['sources']['C0603C100J5GACTU']['ratings']
        for key,value in [('dielectric','X7R'),('rated_voltage_V',25),('tolerance_fraction',.1)]:
            with self.assertRaises(ValueError):s.compare_candidate(old,old|{key:value})


if __name__=='__main__':unittest.main()
