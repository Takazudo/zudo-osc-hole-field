"""The P local epoch bridge rejects source changes affecting P contacts."""
import copy
import json
import unittest

from scripts.pcbgen.control_source_epoch_bridge import IO,OLD_IO,PARTITION,project_io,verify


class ControlSourceEpochBridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=json.loads(OLD_IO.read_bytes())
        cls.current=json.loads(IO.read_bytes())
        cls.partition=json.loads(PARTITION.read_bytes())
        cls.ref=next(row['ref'] for row in cls.partition['assignment']['components'] if row['board']=='P')

    def test_current_actual_local_bridge_and_projected_source_mutations(self):
        report=verify()
        self.assertEqual(report['own_source_contact_count'],214)
        self.assertEqual(report['family_counts'],{'convex_SMD':94,'PTH':120})
        self.assertEqual(len(project_io(self.old,self.current,self.partition)),285)
        for mutation in ('package','missing','duplicate','crossing'):
            changed=copy.deepcopy(self.current)
            if mutation=='package':
                next(row for row in changed['physical_packages'] if row['ref']==self.ref)['dnp']=not next(row for row in changed['physical_packages'] if row['ref']==self.ref)['dnp']
            elif mutation=='missing':
                changed['physical_packages']=[row for row in changed['physical_packages'] if row['ref']!=self.ref]
            elif mutation=='duplicate':
                changed['physical_packages'].append(copy.deepcopy(next(row for row in changed['physical_packages'] if row['ref']==self.ref)))
            else:
                changed['allowed_crossings'].append({'net':'AGND','members':[{'ref':self.ref,'pin':'2'}]})
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                project_io(self.old,changed,self.partition)


if __name__=='__main__':unittest.main()
