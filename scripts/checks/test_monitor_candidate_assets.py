"""Independent pin-function and package-drawing checks for candidate logic."""
import copy
import json
import unittest
from scripts.libgen import build_monitor_candidate_assets as assets
from scripts.schgen.core import parse, tokens, children


class MonitorCandidateAssetTests(unittest.TestCase):
    def setUp(self):
        self.parts={p['mpn']:p for p in json.loads(assets.CATALOG.read_text())['parts']}

    def test_lvc_push_pull_outputs_and_power_pins(self):
        expected={
            'SN74LVC1G17DBVR':{'1':'no_connect','2':'input','3':'power_in','4':'output','5':'power_in'},
            'SN74LVC1G74DCTR':{'1':'input','2':'input','3':'output','4':'power_in','5':'output','6':'input','7':'input','8':'power_in'},
        }
        for mpn,pins in expected.items():
            tree,_=parse(tokens(assets.ic_symbol(self.parts[mpn])))
            symbol=children(tree,'symbol')[0]
            units=children(symbol,'symbol')
            actual={children(pin,'number')[0][1]:pin[1] for unit in units for pin in children(unit,'pin')}
            self.assertEqual(actual,pins)

    def test_incomplete_or_unknown_electrical_types_are_rejected(self):
        part=copy.deepcopy(self.parts['SN74LVC1G17DBVR'])
        del part['pin_types']['4']
        with self.assertRaisesRegex(ValueError,'complete pin map'):assets.ic_symbol(part)
        part=copy.deepcopy(self.parts['SN74LVC1G17DBVR'])
        part['pin_types']['4']='output_or_something'
        with self.assertRaisesRegex(ValueError,'unsupported'):assets.ic_symbol(part)

    def test_dct_example_pad_centres_and_pin_order(self):
        text=assets.dct_footprint(self.parts['SN74LVC1G74DCTR']['package_envelope'])
        tree,_=parse(tokens(text))
        pads=children(tree,'pad')
        self.assertEqual(len(pads),8)
        expected={'1':(-1.9,-.975),'2':(-1.9,-.325),'3':(-1.9,.325),'4':(-1.9,.975),
                  '5':(1.9,.975),'6':(1.9,.325),'7':(1.9,-.325),'8':(1.9,-.975)}
        for pad in pads:
            self.assertEqual(pad[3],'roundrect')
            self.assertAlmostEqual(float(children(pad,'roundrect_rratio')[0][1])*.4,.05)
            self.assertEqual(tuple(float(v) for v in children(pad,'at')[0][1:]),expected[pad[1]])
            self.assertEqual(tuple(float(v) for v in children(pad,'size')[0][1:]),(1.1,.4))
