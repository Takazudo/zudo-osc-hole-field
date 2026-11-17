import copy
import json
import unittest
import audit as a


def mm(lo,hi): return {'unit':'mm','lower':lo,'upper':hi}


class CableContractTests(unittest.TestCase):
    def setUp(self):
        self.evidence=json.loads(a.EVIDENCE.read_text())

    def test_closed_interval_boundaries(self):
        self.assertEqual(a.compare_interval(mm('.25','.35'),mm('.25','.35'))['verdict'],'WITHIN_DECLARED_INTERVAL')
        self.assertEqual(a.compare_interval(mm('3.5','5'),mm('3.5',None))['verdict'],'WITHIN_DECLARED_INTERVAL')

    def test_partial_overlap_is_not_containment(self):
        r=a.compare_interval(mm('.253','.353'),mm('.250','.350'))
        self.assertEqual(r['verdict'],'DECLARED_INTERVAL_NOT_CONTAINED')
        self.assertEqual(r['upper_excess_mm'],'0.003')
        r=a.compare_interval(mm('4.42','4.58'),mm('4.43','4.57'))
        self.assertEqual(r['lower_shortfall_mm'],'0.01')
        self.assertEqual(r['upper_excess_mm'],'0.01')

    def test_only_matching_endpoint_still_not_contained(self):
        self.assertEqual(a.compare_interval(mm('2.5','3.5'),mm('3.5',None))['lower_shortfall_mm'],'1.0')

    def test_wrong_units_and_nondecimal_or_invalid_interval(self):
        for value in ({'unit':'um','lower':'250','upper':'350'},mm('NaN','1'),mm('2','1'),mm('0',.3)):
            with self.assertRaises(ValueError):a.compare_interval(value,mm('0','1'))

    def test_missing_bound_not_nominal_pass(self):
        self.assertEqual(a.compare_interval(mm('.225',None),mm('.188',None))['verdict'],'UNSOURCED')

    def test_family_and_wrong_exact_code_never_transfer(self):
        for scope,code in (('generic','C81339'),('exact','C68390')):
            cable=copy.deepcopy(self.evidence['cables']['C81339'])
            cable['source'].update(scope=scope,order_code=code)
            rows=a.compare('C81339',cable,self.evidence['connector'])
            self.assertTrue(all(r['verdict']=='UNSOURCED' for r in rows))

    def test_missing_exact_datum(self):
        cable=self.evidence['cables']['C81339']; cable['dimensions']={}
        self.assertTrue(all(r['verdict']=='UNSOURCED' for r in a.compare('C81339',cable,self.evidence['connector'])))

    def test_source_pin_cannot_be_silently_changed(self):
        self.evidence['cables']['C29534']['source']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'source pin changed'):a.audit(self.evidence)

    def test_finish_disagreement_independent_of_thickness(self):
        rows={r['field']:r for r in a.compare('C29534',self.evidence['cables']['C29534'],self.evidence['connector'])}
        self.assertEqual(rows['finish']['verdict'],'DIFFERENT_STATED_FINISH')
        self.assertEqual(rows['tail_thickness']['verdict'],'WITHIN_DECLARED_INTERVAL')
        self.assertEqual(rows['total_width']['comparator_class'],'recommended drawing dimensions')
        self.assertEqual(rows['finish']['comparator_class'],'requirement')

    def test_generic_scope_cannot_be_promoted_at_unchanged_hash(self):
        for code in ('C26618','C32128'):
            evidence=copy.deepcopy(self.evidence)
            cable=evidence['cables'][code]
            cable['source'].update(scope='exact',order_code=code)
            cable['dimensions']=copy.deepcopy(evidence['cables']['C81339']['dimensions'])
            with self.assertRaisesRegex(ValueError,'source applicability changed'):
                a.audit(evidence)

    def test_nominal_stiffener_is_not_guaranteed_minimum(self):
        result=a.audit(self.evidence)
        for cable in result['cables']:
            row=next(r for r in cable['comparisons'] if r['field']=='stiffener_thickness')
            self.assertEqual(row['verdict'],'UNSOURCED')
            self.assertEqual(row['comparator']['lower'],'0.188')
            if cable['code'] in ('C29534','C68390','C81339'):
                self.assertEqual(row['declared']['nominal'],'0.225')
                self.assertIsNone(row['declared']['lower'])

    def test_selected_five_codes_61_links_and_two_unresolved_sources(self):
        result=a.audit(self.evidence)
        self.assertEqual(result['links'],61)
        self.assertEqual({r['code']:r['link_count'] for r in result['cables']},a.SELECTED)
        for r in result['cables']:
            if r['code'] in ('C26618','C32128'):
                self.assertEqual(r['source_scope'],'generic')
                self.assertEqual(self.evidence['cables'][r['code']]['source']['sha256'],a.SOURCE_PINS['C26618'])
                self.assertTrue(all(c['verdict']=='UNSOURCED' for c in r['comparisons']))


if __name__=='__main__':unittest.main()
