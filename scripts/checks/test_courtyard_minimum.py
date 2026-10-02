"""A source minimum must survive normalization and two-decimal serialization."""
import json
import unittest
from pathlib import Path
from scripts.libgen.gen_courtyards import courtyard_box, desired_courtyard, envelope, parse, rewrite

ROOT = Path(__file__).resolve().parents[2]


def fixture(value=None):
    prop = '' if value is None else (' (property "ProjectCourtyardMinimumBox" '+json.dumps(value)+
        ' (at 0 0 0) (layer "F.Fab") (effects (font (size 1 1)) (hide yes)))\n')
    return ('(footprint "MinimumBoxFixture" (version 20260206) (generator "test")\n'
            ' (layer "F.Cu")\n'+prop+
            ' (pad "1" smd rect (at -0.8 0) (size 0.95 1) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
            ' (pad "2" smd rect (at 0.8 0) (size 0.95 1) (layers "F.Cu" "F.Paste" "F.Mask"))\n)\n')


class CourtyardMinimumTests(unittest.TestCase):
    def test_source_minimum_survives_rewrite(self):
        result = rewrite(fixture('-1.55 -0.75 1.55 0.75'))
        self.assertEqual(courtyard_box(result), (-1.55, -.75, 1.55, .75))
        self.assertEqual(rewrite(result), result)

    def test_near_matching_inward_edge_is_repaired(self):
        canonical = rewrite(fixture('-1.55 -0.75 1.55 0.75'))
        inward = canonical.replace('(start 1.55 ', '(start 1.5499995 ').replace(
            '(end 1.55 ', '(end 1.5499995 ')
        self.assertNotEqual(inward, canonical)
        self.assertEqual(rewrite(inward), canonical)

    def test_translated_asymmetric_local_box(self):
        self.assertEqual(courtyard_box(rewrite(fixture('-4 -2 0.1 3'))),
                         (-4, -2, 1.53, 3))

    def test_small_floor_cannot_shrink_unrounded_envelope(self):
        result = courtyard_box(rewrite(fixture('-.1 -.1 .1 .1')))
        self.assertEqual(result, (-1.53, -.75, 1.53, .75))
        self.assertLessEqual(result[0], -1.525)
        self.assertGreaterEqual(result[2], 1.525)

    def test_non_grid_minimum_rounds_outward(self):
        self.assertEqual(courtyard_box(rewrite(fixture('-2.001 -1.009 2.009 1.001'))),
                         (-2.01, -1.01, 2.01, 1.01))

    def test_invalid_minima_are_rejected(self):
        for value in ('', '0 0 1', '0 0 1 1 2', 'x 0 1 1',
                      'NaN 0 1 1', '-Infinity 0 1 1', '0 0 Infinity 1',
                      '1 0 0 1', '0 1 1 0', '0 0 0 1', '0 0 1 0',
                      '-1e100 0 1 1', '-1e24 -1 1e24 1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                rewrite(fixture(value))
        duplicate = fixture('-2 -1 2 1').replace(' (pad "1"',
            ' (property "ProjectCourtyardMinimumBox" "-3 -1 3 1")\n (pad "1"', 1)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            rewrite(duplicate)
        missing = fixture().replace(' (pad "1"',
            ' (property "ProjectCourtyardMinimumBox")\n (pad "1"', 1)
        with self.assertRaises(ValueError):
            rewrite(missing)

    def test_raw_envelope_does_not_consume_source_floor(self):
        self.assertEqual(envelope(parse(fixture('-4 -4 4 4')), clearance=0, rounded=False),
                         envelope(parse(fixture()), clearance=0, rounded=False))

    def test_floorless_library_bytes_are_unchanged(self):
        paths = list((ROOT/'footprints/kicad/zudo-osc-hole-field.pretty').glob('*.kicad_mod'))
        self.assertGreater(len(paths), 20)
        checked = 0
        for path in paths:
            text = path.read_text()
            if 'ProjectCourtyardMinimumBox' in text:
                continue
            checked += 1
            with self.subTest(path=path.name):
                self.assertEqual(desired_courtyard(parse(text)), envelope(parse(text)))
                self.assertEqual(rewrite(text), text)
        self.assertGreater(checked, 20)


if __name__ == '__main__':
    unittest.main()
