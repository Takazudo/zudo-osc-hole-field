"""Current J source bridge rejects changed native copper support and drills."""
import copy
import unittest

from scripts.pcbgen.verify_jack_source_geometry_epoch import compare_epoch,verify


class JackGroundSourceEpochTest(unittest.TestCase):

    def test_changed_drill_or_pad_rejects(self):
        old={'board_id':'osc-jack-left','holes':[{'uuid':'h','size_mm':[.3,.3]}],
             'outline_mm':[[0,0],[1,0],[1,1],[0,1]],'stackup':[{'layer':'F.Cu'}],
             'items':[{'ref':'J1','pad':'2','uuid':'u','net':'AGND','copper':{'F.Cu':[]}},
                      {'uuid':'via','net':'AGND','analytic_primitives':{'F.Cu':{'radius_nm':200000}}}]}
        self.assertEqual(len(compare_epoch(old,copy.deepcopy(old))),1)
        for key,change in (('holes',lambda x:x['holes'][0].update(size_mm=[.4,.4])),
                           ('pad',lambda x:x['items'][0]['copper'].update({'F.Cu':[[1,2]]})),
                           ('stack',lambda x:x.update(stackup=[{'layer':'B.Cu'}])),
                           ('via_net',lambda x:x['items'][1].update(net='GND')),
                           ('via_land',lambda x:x['items'][1]['analytic_primitives']['F.Cu'].update(radius_nm=160000))):
            with self.subTest(key=key):
                modified=copy.deepcopy(old);change(modified)
                with self.assertRaises(ValueError):compare_epoch(old,modified)


if __name__=='__main__':unittest.main()
