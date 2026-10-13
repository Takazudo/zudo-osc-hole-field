import unittest
import check_pose as check


class PoseTests(unittest.TestCase):
    def setUp(self):
        self.old=dict(x_mm=10,y_mm=20,kicad_orientation_deg=270,side='B.Cu')
        self.new=dict(x_mm=30,y_mm=40,kicad_orientation_deg=90,side='B.Cu')

    def test_integer_half_turn_and_inverse(self):
        source=[11234567,22345678]
        after=check.transform_xy(source,self.old,self.new,1_000_000)
        self.assertEqual(after,[28765433,37654322])
        self.assertEqual(check.transform_xy(after,self.new,self.old,1_000_000),source)

    def test_no_face_flip_or_arbitrary_rotation(self):
        with self.assertRaises(ValueError):
            check.transform_xy([10,20],self.old,self.new|{'side':'F.Cu'})
        with self.assertRaises(ValueError):
            check.transform_xy([10,20],self.old,self.new|{'kicad_orientation_deg':45})

    def test_pad_identity_preserved_and_input_immutable(self):
        pad={'uuid':'test','ref':'U1','pad':'12','net':'BP','xy':[11000000,22000000],
             'poly':[[10000000,21000000],[12000000,21000000],[12000000,23000000]],'layers':['B.Cu']}
        original=check.canonical(pad)
        out=check.transform_pad(pad,self.old,self.new)
        self.assertEqual(check.canonical(pad),original)
        self.assertEqual(out['xy'],[29000000,38000000])
        for name in ['uuid','ref','pad','net','layers']:
            self.assertEqual(out[name],pad[name])

    def test_sensitive_bypass_fixed_point(self):
        b={'sensitive_nets':[{'refs':['U2','R2']},{'refs':['U1','U2']}],
           'source_parts':[{'ref':'C2','decouples_ref':'U2'},{'ref':'C1','decouples_ref':'U1'}]}
        self.assertEqual(check.closure(b,{'U1'}),['C1','C2','R2','U1','U2'])

    def test_pose_epoch_seal(self):
        self.assertEqual(check.digest((check.HERE/'pose-epoch.json').read_bytes()),check.EPOCH_SHA)


if __name__=='__main__':
    unittest.main()
