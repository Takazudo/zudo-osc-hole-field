import unittest
from scripts.pcbgen.zone_cache import without_zone_cache


class ZoneCacheTests(unittest.TestCase):
    def test_only_zone_child_caches_are_removed(self):
        text='''(kicad_pcb
 (property "note" "(filled_polygon keep this quoted text)")
 (segment (start 1 2) (end 3 4) (net "AGND"))
 (zone (net "AGND") (layer "In1.Cu")
  (fill yes (thermal_gap 0.25))
  (polygon (pts (xy 0 0) (xy 10 0) (xy 10 10)))
  (filled_polygon (layer "In1.Cu") (pts (xy 1 1) (xy 9 1) (xy 9 9)))
  (fill_segments (pts (xy 2 2) (xy 3 3)))
 )
 (footprint "keep" (property "filled_polygon" "not a cache"))
)'''
        compact,count=without_zone_cache(text)
        expected=text.replace('(filled_polygon (layer "In1.Cu") (pts (xy 1 1) (xy 9 1) (xy 9 9)))','').replace('(fill_segments (pts (xy 2 2) (xy 3 3)))','')
        self.assertEqual(count,2);self.assertEqual(compact,expected)
        self.assertEqual(without_zone_cache(compact),(compact,0))

    def test_board_without_cache_is_byte_identical(self):
        text='(kicad_pcb (zone (net "AGND") (polygon (pts (xy 1 1)))))'
        self.assertEqual(without_zone_cache(text),(text,0))
