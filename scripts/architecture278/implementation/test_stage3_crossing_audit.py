import copy
import json
import unittest
import stage3_crossing_audit as a

class CrossingAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx=a.context()
        cls.report=json.loads((a.OUT/'stage3-crossing-audit.json').read_text())
        cls.rows=cls.report['audited_paths']
        cls.links={h['id']:h for h in json.loads((a.OUT/'candidate-report.json').read_text())['front_links']}
    def row(self,net='/O1/FM_BUFFER'):
        return copy.deepcopy(next(r for r in self.rows if r['instance']=='O1' and r['template_net']==net))
    def reject(self,row):
        with self.assertRaises(ValueError):a.validate_row(row,self.ctx)
    def test_full_live_source_correspondence(self):
        a.validate_collection(self.rows,self.links,self.ctx)
        self.assertEqual(80,len(self.report['locked_panel_checks']))
        self.assertEqual(287,len(self.report['source_mapping_all_five']))
    def test_wrong_instance(self):
        row=self.row();row['instance']='O2';self.reject(row)
    def test_wrong_net(self):
        row=self.row();row['actual_net']='/O1/PWM_BUFFER';self.reject(row)
    def test_wrong_pin(self):
        row=self.row();row['front']['pin']='3';self.reject(row)
    def test_wrong_uid(self):
        row=self.row();row['actual_panel_uid']='J:O2.FM';self.reject(row)
    def test_wrong_uid_even_if_template_changed(self):
        row=self.row();row['template_panel_uid']='J:O1.PWM';row['actual_panel_uid']='J:O1.PWM';self.reject(row)
    def test_feedback_pin_cannot_replace_source(self):
        row=self.row();row['template_front_endpoint']='U1116:2';row['front']=a.map_endpoint('U1116:2','O1',self.ctx);self.reject(row)
    def test_wrong_shared_driver(self):
        row=self.row('OSC_REF5');row['template_front_endpoint']='U1602:2';row['front']=a.map_endpoint('U1602:2','O1',self.ctx);self.reject(row)
    def test_weakened_length(self):
        row=self.row();row['length_limit_mm']=301;self.reject(row)
    def test_weakened_capacitance(self):
        row=self.row();row['capacitance_limit_pF']=1001;self.reject(row)
    def test_omitted_wire_decomposition(self):
        row=self.row();del row['segments_mm']['wire_max_mm'];self.reject(row)
    def test_missing_pwm_wiper_branch(self):
        rows=copy.deepcopy(self.rows)
        target=next(r for r in rows if r['alternative']=='five_card_two_rows' and r['instance']=='O5' and r['template_net']=='/O1/C42d8cd_W')
        rows.remove(target)
        with self.assertRaises(ValueError):a.validate_collection(rows,self.links,self.ctx)
    def test_missing_shared_instance(self):
        rows=[r for r in self.rows if not(r['alternative']=='five_card_two_rows' and r['instance']=='O4' and r['actual_net']=='OSC_REF5')]
        with self.assertRaises(ValueError):a.validate_collection(rows,self.links,self.ctx)
    def test_one_receiver_omitted_but_link_remains(self):
        rows=copy.deepcopy(self.rows)
        target=next(r for r in rows if r['alternative']=='five_card_two_rows' and r['instance']=='O3' and r['template_net']=='/O1/FM_BUFFER' and r['other']['ref']=='R1321')
        rows.remove(target)
        with self.assertRaises(ValueError):a.validate_collection(rows,self.links,self.ctx)
    def test_duplicate_endpoint(self):
        with self.assertRaises(ValueError):a.validate_collection(self.rows+[self.rows[0]],self.links,self.ctx)
    def test_missing_return_endpoint(self):
        alt=json.loads((a.OUT/'assembly-report.json').read_text())['alternatives']['five_card_two_rows']
        row=copy.deepcopy(next(r for r in alt['returns'] if r['endpoint_ids']))
        row['endpoint_ids'].pop()
        with self.assertRaises(ValueError):a.validate_return(row,self.ctx,self.links,alt['DIN_signal_labels'])
    def test_wrong_return_contact(self):
        alt=json.loads((a.OUT/'assembly-report.json').read_text())['alternatives']['five_card_two_rows']
        row=copy.deepcopy(next(r for r in alt['returns'] if r.get('link')=='FRONT-C:O1.FM±'))
        row['contact']='2'
        with self.assertRaises(ValueError):a.validate_return(row,self.ctx,self.links,alt['DIN_signal_labels'])

if __name__=='__main__':unittest.main()
