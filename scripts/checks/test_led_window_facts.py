import copy
import json
import unittest
from pathlib import Path
from scripts.checks.check_led_window_facts import check


class LedWindowFactsTests(unittest.TestCase):
    def setUp(self):
        self.facts=json.loads(Path('design/mechanical/facts/led-window.json').read_bytes())
        self.lock=json.loads(Path('design/grid/placements.lock.json').read_bytes())

    def test_counts_and_parent_deltas_match(self):
        self.assertEqual(check(self.facts,self.lock),{'mag':92,'clip':10})

    def test_old_single_offset_and_wrong_clip_offset_are_rejected(self):
        old=copy.deepcopy(self.facts)
        old['placement']['offset_from_jack_centre_mm']=[6.15,0]
        with self.assertRaisesRegex(ValueError,'single offset'):check(old,self.lock)
        wrong=copy.deepcopy(self.facts)
        next(r for r in wrong['placement']['groups'] if r['led_type']=='clip')['offset_from_jack_centre_mm']=[6.15,0]
        with self.assertRaisesRegex(ValueError,'offset disagrees'):check(wrong,self.lock)

    def test_counts_and_actual_centres_are_checked_independently(self):
        wrong=copy.deepcopy(self.facts);wrong['count']+=1
        with self.assertRaisesRegex(ValueError,'total jack LED count'):check(wrong,self.lock)
        moved=copy.deepcopy(self.lock)
        next(r for r in moved['placements'] if r.get('led_type')=='clip')['y_mm']+=.01
        with self.assertRaisesRegex(ValueError,'actual parent centres'):check(self.facts,moved)
