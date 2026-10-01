import json
from pathlib import Path
import unittest
from contact_support_frame import admit_rectangle, push_current


class ContactSupportFrameTest(unittest.TestCase):
    def test_actual_o1_and_normal_sign(self):
        root=Path(__file__).resolve().parents[2]
        data=json.loads((root/'.circuit-cache/issue38-recovery/octave-1-prerequisite-v3/native-geometry.json').read_text())
        item=next(x for x in data['items'] if x.get('ref')=='J900114' and x.get('pad')=='2')
        row=admit_rectangle(item,face='B.Cu',width_mm=.18,length_mm=.25,registration_mm=.05)
        self.assertEqual(row['quarter_turns'],2)
        self.assertEqual(row['uuid'],'85081f74-465c-591a-92fd-89ec273f1ced')
        # q enters from the high local-z face; local current points toward PCB.
        for face,sign in (('F.Cu',-1),('B.Cu',1)):
            for turn in range(4):
                j=push_current((.4,.7,-2.),quarter_turns=turn,face=face)
                self.assertEqual(j[2]*sign,-2.)
                self.assertAlmostEqual(j[0]**2+j[1]**2,.4**2+.7**2)
        for kw in ({'registration_mm':.22},{'local_offset_mm':(.3,0.)},{'width_mm':.7}):
            args=dict(face='B.Cu',width_mm=.18,length_mm=.25,registration_mm=.05);args.update(kw)
            with self.assertRaises(ValueError):admit_rectangle(item,**args)
        with self.assertRaises(ValueError):admit_rectangle(item,face='F.Cu',width_mm=.18,length_mm=.25,registration_mm=0.)


if __name__=='__main__':unittest.main()
