"""Source-owned stack metadata is idempotent and preserves other setup text."""
import unittest
from scripts.pcbgen.native_stack import apply


class NativeStackTests(unittest.TestCase):
    def test_only_stack_changes_and_replay_is_idempotent(self):
        rows=[]
        for i,(name,t) in enumerate(zip(('F.Cu','In1.Cu','In2.Cu','B.Cu'),(.07,.14,.07,.07))):
            rows.append({'layer':name,'copper_thickness_mm':t})
            if i<3:rows.append({'layer':'dielectric-'+str(i+1),'thickness_mm':(1.13,.06,.06)[i]})
        spec={'stackup':rows,'thickness_mm':1.6}
        original='(kicad_pcb (general (thickness 1.6)) (layers (0 "F.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal) (2 "B.Cu" signal)) (setup (pad_to_mask_clearance 0.025) (grid_origin 100 50)) (segment (width 0.3)))'
        updated,_=apply(original,spec);again,_=apply(updated,spec)
        self.assertEqual(updated,again)
        self.assertIn('(pad_to_mask_clearance 0.025) (grid_origin 100 50)',updated)
        self.assertTrue(updated.endswith('(segment (width 0.3)))'))
        self.assertNotIn('epsilon_r',updated)
        with self.assertRaisesRegex(ValueError,'nominal native board thickness'):
            apply(original,{**spec,'thickness_mm':2.})


if __name__=='__main__':unittest.main()
