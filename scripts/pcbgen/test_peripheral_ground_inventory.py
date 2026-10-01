import copy
import json
import unittest
from pathlib import Path
from scripts.pcbgen.peripheral_ground_inventory import audit

BASE=Path('design/partition/peripheral-ground-feasibility')


class PeripheralGroundInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.partition=json.loads(Path('design/partition/partition.json').read_bytes())
        cls.io=json.loads(Path('design/reports/io-partition.json').read_bytes())

    def fixture(self,bid):
        manifest=json.loads((BASE/(bid+'.receipt.json')).read_bytes())
        rows=manifest['own_ground_contacts']+manifest['GH_ground_contacts']
        pads=[{'ref':r['ref'],'pad':r['pad'],'uuid':r['ref']+':'+r['pad'],'net':'AGND',
               'copper':{r.get('side','F.Cu'):[]},'xy_mm':[100.,50.]} for r in rows]
        ref=manifest['source_reference'];reference={**ref,'layer':ref['side'],
            'uuid':ref['ref']+':'+ref['pad'],'xy_mm':[100.,50.]}
        native={'board_id':bid,'coordinate_frame':{'source_to_native_translation_mm':[100,50]},
            'items':pads,'ground_reference':reference,'ground_reference_members':[r['uuid'] for r in pads]}
        return native,manifest

    def test_complete_actual_source_sets_and_connectivity_negatives(self):
        for bid,count in [('osc-octave-1',7),('osc-stage-optical',72)]:
            native,manifest=self.fixture(bid);result=audit(native,manifest,self.partition,self.io)
            self.assertEqual(result['connected_count'],count)
            for mode in ('missing','duplicate','disconnect','reference','face','foreign'):
                changed=copy.deepcopy(native)
                if mode=='missing':changed['items'].pop(0)
                elif mode=='duplicate':changed['items'].append(changed['items'][0])
                elif mode=='disconnect':changed['ground_reference_members'].pop(0)
                elif mode=='reference':changed['ground_reference']['uuid']='wrong'
                elif mode=='face':
                    contact=next(r for r in changed['items'] if r['ref'].startswith('J900'))
                    contact['copper']={'F.Cu':[]}
                else:changed['items'].append({'ref':'UNDECLARED','pad':'1','uuid':'foreign','net':'AGND','copper':{'B.Cu':[]},'xy_mm':[0,0]})
                with self.subTest(bid=bid,mode=mode),self.assertRaises(ValueError):audit(changed,manifest,self.partition,self.io)
            changed=copy.deepcopy(native);changed['ground_reference_members']=[]
            planning=audit(changed,manifest,self.partition,self.io,require_connected=False)
            self.assertEqual(planning['connected_count'],0);self.assertEqual(len(planning['disconnected']),count)


if __name__=='__main__':unittest.main()
