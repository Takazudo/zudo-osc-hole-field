"""Selecting a rail never merges the original ground or changes geometry."""
import copy
import unittest
from scripts.pcbgen.selected_conductor_export import select


class SelectedConductorTests(unittest.TestCase):
    def test_bijective_roles_and_unchanged_native_shapes(self):
        original={'board_sha256':'physical-board','main_rail_members':{'AGND':['g'],'+12V':['p'],'-12V':['m']},
            'items':[{'net':n,'uuid':u,'primitive':{'xy':[1.234567,8.],'radius':.15}} for n,u in [('AGND','g'),('+12V','p'),('-12V','m')]],
            'holes':[{'net':'+12V','uuid':'p','size':[.3,.3]}],
            'zones':[{'net':'AGND','contours':[[[0,0],[2,0],[1,1]]]},
                     {'uuid':'native-keepout','layer':'F.Cu','keepout':True,'tracks_forbidden':True,'vias_forbidden':True,
                      'contours':[{'shell':[[188,207],[188.5,207],[188.5,213],[188,213]],'holes':[]}]}]}
        retained=copy.deepcopy(original);selected=select(original,'+12V','source-sha')
        self.assertEqual(original,retained)
        self.assertEqual(selected['main_rail_members']['AGND'],['p'])
        self.assertEqual(selected['main_rail_members']['__original_native_AGND__'],['g'])
        for before,after in zip(original['items'],selected['items']):
            self.assertEqual(before['primitive'],after['primitive']);self.assertEqual(before['uuid'],after['uuid'])
        self.assertEqual(selected['board_sha256'],'physical-board')
        self.assertEqual(selected['conductor_role_mapping']['actual_native_net'],'+12V')
        self.assertEqual(selected['zones'][1],original['zones'][1])
        self.assertNotIn('net',selected['zones'][1])
        malformed=copy.deepcopy(original);malformed['zones'][1]['keepout']=False
        with self.assertRaisesRegex(ValueError,'no explicit net'):select(malformed,'+12V','source-sha')

    def test_alias_cannot_merge_an_unconnected_native_net(self):
        native={'main_rail_members':{'+12V':['p']},
            'items':[{'net':'+12V','uuid':'p'},
                     {'net':'__original_native_AGND__','uuid':'unconnected'}],
            'holes':[],'zones':[]}
        with self.assertRaisesRegex(ValueError,'alias would collide'):
            select(native,'+12V','source-sha')


if __name__=='__main__':unittest.main()
