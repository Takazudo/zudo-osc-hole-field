"""Source ownership must be proved before retiring a generated via."""
import hashlib
import unittest
from scripts.pcbgen.source_copper import retire_vias
from scripts.pcbgen.uuid_tools import stable_uuid


class SourceCopperTests(unittest.TestCase):
    def test_exact_owned_via_only_and_modified_or_unowned_rejected(self):
        uid=stable_uuid('fixture','plus12v-fanout-via','U1:8:pad-id')
        via=f'(via (at 1 2) (size .7) (drill .3) (uuid "{uid}"))'
        untouched='(segment (start 1 2) (end 2 2) (uuid "other"))'
        text='(kicad_pcb\n'+via+'\n'+untouched+'\n)'
        row={'uuid':uid,'generator_kind':'plus12v-fanout-via','generator_key':'U1:8:pad-id',
             'serialized_via_sha256':hashlib.sha256(via.encode()).hexdigest()}
        spec={'boards':{'fixture':[row]}}
        result,retired=retire_vias(text,'fixture',spec)
        self.assertNotIn(via,result);self.assertIn(untouched,result);self.assertEqual(retired,[row])
        with self.assertRaisesRegex(ValueError,'reviewed source bytes'):
            retire_vias(text.replace('(at 1 2)','(at 1 3)'),'fixture',spec)
        row['generator_key']='other-pad'
        with self.assertRaisesRegex(ValueError,'not owned'):
            retire_vias(text,'fixture',spec)


if __name__=='__main__':unittest.main()
