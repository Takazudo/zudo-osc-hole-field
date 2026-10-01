"""Actual K inventory regressions, independent of its failed geometry verdict."""
import json
import unittest
from pathlib import Path
from scripts.pcbgen.core_ground_inventory import audit


class CoreGroundInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def read(p):return json.loads(Path(p).read_text())
        cls.native=read('.circuit-cache/issue38-recovery/core-feasibility-v2/ground-feasibility-geometry.json')
        cls.manifest=read('design/partition/core-ground-feasibility/osc-core.receipt.json')
        cls.partition=read('design/partition/partition.json');cls.io=read('design/reports/io-partition.json')

    def test_all_selected_contacts_and_independent_source_inventory(self):
        report=audit(self.native,self.manifest,self.partition,self.io)
        self.assertEqual(report['source_fitted_AGND_count'],1903)
        self.assertEqual(len(report['selected_contacts']),215)
        self.assertFalse(report['selected_disconnected'])
        # This gate cannot turn the separate 802-error native trial into PASS.
        for kind in ('GH','main'):
            uid=next(r['uuid'] for r in report['selected_contacts'] if r['kind']==kind)
            changed={**self.native,'main_rail_members':{**self.native['main_rail_members'],
                'AGND':[x for x in self.native['main_rail_members']['AGND'] if x!=uid]}}
            with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'disconnected'):
                audit(changed,self.manifest,self.partition,self.io)

    def test_missing_source_pad_and_wrong_selected_net_or_face_fail(self):
        fitted={r['ref'] for r in self.partition['assignment']['components'] if r['board']=='K' and r['fitted']}
        uid=next(i['uuid'] for i in self.native['items'] if i.get('ref') in fitted and i['net']=='AGND')
        changed={**self.native,'items':[i for i in self.native['items'] if i['uuid']!=uid]}
        with self.assertRaisesRegex(ValueError,'fitted contact mismatch'):audit(changed,self.manifest,self.partition,self.io)
        row=self.manifest['selected_K_ground_ports'][0]
        for key,value in [('net','FOREIGN'),('copper',{'B.Cu':[]})]:
            changed={**self.native,'items':[({**i,key:value} if (i.get('ref'),i.get('pad'))==(row['ref'],row['pad']) else i) for i in self.native['items']]}
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'net or physical face'):
                audit(changed,self.manifest,self.partition,self.io)


if __name__=='__main__':unittest.main()
