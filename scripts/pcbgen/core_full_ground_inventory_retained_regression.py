"""Complete K model basis rejects missing GH, DNP and native connectivity."""
import copy
import json
import unittest
from pathlib import Path

from scripts.pcbgen.core_full_ground_inventory import project

ROOT=Path(__file__).resolve().parents[2]


class CoreFullGroundInventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=json.loads((ROOT/'.circuit-cache/issue38-recovery/core-feasibility-v7/ground-feasibility-geometry.json').read_bytes())
        cls.partition=json.loads((ROOT/'design/partition/partition.json').read_bytes())
        cls.io=json.loads((ROOT/'design/reports/io-partition.json').read_bytes())

    def test_exact_full_basis_and_source_native_failures(self):
        result=project(self.native,self.partition,self.io)
        self.assertEqual((result['fitted_own_count'],result['GH_return_count'],result['main_land_count']),(1903,376,9))
        self.assertEqual(result['balanced_function_count'],2287)
        source=copy.deepcopy(self.partition)
        connector=next(c for c in source['connectors'] if c['board']=='K' and any(n=='AGND' for n in c['pin_map'].values()))
        pin=next(p for p,n in connector['pin_map'].items() if n=='AGND')
        connector['pin_map'][pin]='+5V'
        with self.assertRaisesRegex(ValueError,'GH return inventory'):
            project(self.native,source,self.io)
        native=copy.deepcopy(self.native)
        gh=next(i for i in native['items'] if i.get('ref','').startswith('J900') and i['net']=='AGND')
        native['main_rail_members']['AGND'].remove(gh['uuid'])
        with self.assertRaisesRegex(ValueError,'GH source/native'):
            project(native,self.partition,self.io)
        io=copy.deepcopy(self.io)
        dnp=next(p for p in io['physical_packages'] if p['ref']=='C106')
        dnp['dnp']=False
        with self.assertRaises(ValueError):project(self.native,self.partition,io)


if __name__=='__main__':unittest.main()
