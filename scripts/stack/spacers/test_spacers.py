"""Unit tests for the printed spacer models: the retained STL files are read back and measured."""
import contextlib
import copy
import io
import json
import math
import struct
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spacers as sp  # noqa: E402

REVIEW = sp.ROOT / 'circuit/orchestration/campaigns/osc-stack-20261114/reviews/da-03.md'


def read_stl(data):
    """Triangles of a binary STL as tuples of three vertices; the stored normals are returned beside them."""
    (count,) = struct.unpack_from('<I', data, 80)
    assert len(data) == 84 + 50 * count, (len(data), count)
    tris, normals = [], []
    for k in range(count):
        v = struct.unpack_from('<12f', data, 84 + 50 * k)
        normals.append(v[0:3])
        tris.append((v[3:6], v[6:9], v[9:12]))
    return tris, normals


def shells(tris):
    """Number of connected pieces, joining triangles through shared vertices."""
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b, c in tris:
        parent[find(b)] = find(a)
        parent[find(c)] = find(a)
    return len({find(v) for v in parent})


def volume(tris):
    """Signed volume by the divergence theorem; positive when every triangle faces outward."""
    return sum((a[0] * (b[1] * c[2] - b[2] * c[1]) + a[1] * (b[2] * c[0] - b[0] * c[2])
                + a[2] * (b[0] * c[1] - b[1] * c[0])) for a, b, c in tris) / 6


def quiet(call, *args):
    """Run a command-line entry with its output captured, so a test run stays readable."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return call(*args)


class RetainedModels(unittest.TestCase):
    def setUp(self):
        self.spec = sp.load()
        self.sleeve = self.spec['sleeve']
        self.files = {p.name: p.read_bytes() for p in sp.OUT.glob('*')}

    def prism_volume(self, length):
        n, ro, ri = self.sleeve['facets'], self.sleeve['outer_diameter_mm'] / 2, self.sleeve['bore_diameter_mm'] / 2
        return n / 2 * math.sin(2 * math.pi / n) * (ro * ro - ri * ri) * length

    def test_retained_files_are_what_the_parameter_list_generates(self):
        self.assertEqual(self.files, sp.outputs(self.spec))

    def test_every_model_is_closed_and_faces_outward(self):
        for name, data in self.files.items():
            tris, normals = read_stl(data)
            edges = Counter(e for a, b, c in tris for e in ((a, b), (b, c), (c, a)))
            self.assertTrue(all(n == 1 and edges[(q, p)] == 1 for (p, q), n in edges.items()), name)
            self.assertGreater(volume(tris), 0, name)
            for (a, b, c), stored in zip(tris, normals):
                u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
                n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                k = math.sqrt(sum(x * x for x in n))
                self.assertGreater(k, 1e-6, name)
                self.assertLess(max(abs(n[i] / k - stored[i]) for i in range(3)), 1e-3, name)

    def test_single_sleeves_have_the_listed_dimensions(self):
        ro, ri = self.sleeve['outer_diameter_mm'] / 2, self.sleeve['bore_diameter_mm'] / 2
        for m in self.spec['members']:
            tris, _ = read_stl(self.files[m['file']])
            length = sp.length_mm(self.spec, m)
            points = {v for t in tris for v in t}
            self.assertEqual(len(tris), 8 * self.sleeve['facets'])
            self.assertEqual(shells(tris), 1)
            self.assertEqual({round(z, 4) for _, _, z in points}, {0.0, round(length, 4)})
            radii = [math.hypot(x, y) for x, y, _ in points]
            self.assertTrue(all(min(abs(r - ri), abs(r - ro)) < 1e-3 for r in radii), m['id'])
            self.assertTrue(any(abs(r - ri) < 1e-3 for r in radii) and any(abs(r - ro) < 1e-3 for r in radii), m['id'])
            self.assertAlmostEqual(volume(tris), self.prism_volume(length), delta=0.05)

    def test_no_sleeve_is_longer_than_its_gap(self):
        allowance = self.spec['length_allowance_mm']
        self.assertLess(allowance, 0)
        for m in self.spec['members']:
            tris, _ = read_stl(self.files[m['file']])
            top = max(v[2] for t in tris for v in t)
            self.assertLess(top, m['gap_mm'], m['id'])
            self.assertAlmostEqual(top, m['gap_mm'] + allowance, places=4, msg=m['id'])

    def test_plate_holds_the_whole_set_without_touching(self):
        tris, _ = read_stl(self.files[self.spec['plate']['file']])
        places = sp.plate_positions(self.spec)
        self.assertEqual(len(places), sum(m['quantity'] + m['spares'] for m in self.spec['members']))
        self.assertEqual(shells(tris), len(places))
        centres = [(x, y) for _, x, y in places]
        nearest = min(math.dist(a, b) for i, a in enumerate(centres) for b in centres[i + 1:])
        self.assertGreaterEqual(nearest - self.sleeve['outer_diameter_mm'], self.spec['plate']['min_gap_mm'])
        self.assertAlmostEqual(volume(tris), sum(self.prism_volume(sp.length_mm(self.spec, m)) for m, _, _ in places), delta=0.5)

    def test_sleeve_is_the_one_the_design_review_states(self):
        review = REVIEW.read_text()
        self.assertGreater(self.sleeve['bore_diameter_mm'], self.sleeve['screw_nominal_diameter_mm'])
        self.assertLessEqual(self.sleeve['outer_diameter_mm'] / 2, self.sleeve['keep_out_radius_mm'])
        for token in ('outer diameter %s mm' % sp.fmt_mm(self.sleeve['outer_diameter_mm']),
                      '%s mm keep-out radius' % sp.fmt_mm(self.sleeve['keep_out_radius_mm']),
                      'bore %s mm' % sp.fmt_mm(self.sleeve['bore_diameter_mm'])):
            self.assertIn(token, review)


class RejectedParameters(unittest.TestCase):
    """A parameter list that cannot give a printable set is refused with the defect named."""

    def setUp(self):
        self.spec = sp.load()

    def found(self, edit):
        spec = copy.deepcopy(self.spec)
        edit(spec)
        return ' / '.join(sp.problems(spec))

    def test_the_retained_list_has_no_problem(self):
        self.assertEqual(sp.problems(self.spec), [])

    def test_swapped_diameters_are_refused(self):
        def swap(spec):
            s = spec['sleeve']
            s['outer_diameter_mm'], s['bore_diameter_mm'] = s['bore_diameter_mm'], s['outer_diameter_mm']
        self.assertIn('must exceed the bore', self.found(swap))

    def test_a_bore_the_screw_cannot_pass_is_refused(self):
        self.assertIn('must exceed the screw diameter', self.found(lambda spec: spec['sleeve'].update(bore_diameter_mm=0)))

    def test_too_few_facets_are_refused(self):
        self.assertIn('facets', self.found(lambda spec: spec['sleeve'].update(facets=2)))

    def test_a_sleeve_outside_the_keep_out_is_refused(self):
        self.assertIn('keep-out radius', self.found(lambda spec: spec['sleeve'].update(outer_diameter_mm=7.6)))

    def test_a_sleeve_as_long_as_its_gap_is_refused(self):
        self.assertIn('never longer than its gap', self.found(lambda spec: spec.update(length_allowance_mm=0.0)))

    def test_sites_on_the_wrong_board_are_refused(self):
        def move(spec):
            spec['members'][0]['sites'] = {'P': 4, 'JR': 4}
            spec['members'][1]['sites'] = {'JL': 4}
        self.assertIn('are not the front boards of', self.found(move))

    def test_sites_that_do_not_add_up_are_refused(self):
        self.assertIn('do not add up', self.found(lambda spec: spec['members'][0].update(quantity=9)))

    def test_a_crowded_plate_is_refused(self):
        self.assertIn('between pieces', self.found(lambda spec: spec['plate'].update(pitch_mm=9.0)))

    def test_load_names_the_file_and_the_defect(self):
        spec = copy.deepcopy(self.spec)
        spec['sleeve']['facets'] = 2
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'broken-set.json'
            path.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'broken-set.json: sleeve.facets'):
                sp.load(path)

    def test_a_header_over_80_bytes_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'at most 80 bytes'):
            sp.stl_bytes('x' * 40, [])
        with self.assertRaisesRegex(ValueError, 'ASCII'):
            sp.stl_bytes('gap-µ', [])

    def test_a_label_never_rounds_the_modelled_length(self):
        self.assertEqual([sp.fmt_mm(x) for x in (19.0, 18.8, 18.75)], ['19.0', '18.8', '18.75'])


class CommandLine(unittest.TestCase):
    def test_check_passes_on_the_retained_models(self):
        self.assertEqual(quiet(sp.main, ['--check']), 0)

    def test_an_unknown_flag_stops_before_anything_is_written(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(sp, 'OUT', Path(folder) / 'generated'):
            with self.assertRaises(SystemExit) as stop:
                quiet(sp.main, ['--chek'])
            self.assertEqual(stop.exception.code, 2)
            self.assertFalse(sp.OUT.exists())

    def test_writing_removes_a_model_that_is_no_longer_listed(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(sp, 'OUT', Path(folder)):
            (sp.OUT / 'stack-spacer-for-21mm-gap.stl').write_bytes(b'superseded')
            self.assertEqual(quiet(sp.main, ['--check']), 1)
            self.assertEqual(quiet(sp.main, []), 0)
            self.assertEqual(sorted(p.name for p in sp.OUT.iterdir()), sorted(sp.outputs()))
            self.assertEqual(quiet(sp.main, ['--check']), 0)

    def test_writing_leaves_a_foreign_file_alone(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(sp, 'OUT', Path(folder)):
            (sp.OUT / 'notes.txt').write_text('kept')
            self.assertEqual(quiet(sp.main, []), 1)
            self.assertEqual([p.name for p in sp.OUT.iterdir()], ['notes.txt'])


class AgreementWithTheStack(unittest.TestCase):
    def setUp(self):
        self.spec = sp.load()
        self.candidate = json.loads((sp.ROOT / 'design/stack/geometry/stack-candidate.json').read_text())['candidate']
        self.fixing_list = json.loads((sp.ROOT / 'design/stack/fixings/fixing-sites.json').read_text())
        self.ruled = [f for f in self.fixing_list['fixings'] if f['active'] and f['kind'] == 'sleeve added']
        self.readme = (sp.ROOT / 'design/stack/spacers/README.md').read_text()

    def test_gaps_are_the_candidates_gaps(self):
        gaps = self.candidate['stack']['stacker_height_by_gap']
        for m in self.spec['members']:
            for pair in m['between']:
                self.assertEqual(gaps[pair]['gap_mm'], m['gap_mm'], pair)

    def test_each_length_serves_the_ruled_sleeves_of_its_own_boards(self):
        ruled = Counter((f['front_board'], f['gap_mm']) for f in self.ruled)
        listed = Counter({(board, m['gap_mm']): count for m in self.spec['members'] for board, count in m['sites'].items()})
        self.assertGreater(len(self.ruled), 0)
        self.assertEqual(listed, ruled)

    def test_readme_places_every_ruled_sleeve_and_names_its_screw(self):
        lengths = {m['gap_mm']: sp.fmt_mm(sp.length_mm(self.spec, m)) for m in self.spec['members']}
        rows = [line for line in self.readme.splitlines() if line.startswith(('| Long, ', '| Short, '))]
        self.assertEqual(len(rows), len(self.ruled))
        for f in self.ruled:
            (row,) = [line for line in rows if '| (%g, %g) |' % tuple(f['xy']) in line]
            self.assertIn(', %s mm |' % lengths[f['gap_mm']], row, f['id'])
            self.assertIn('(%s)' % f['front_board'], row, f['id'])
        screw = self.fixing_list['screw']['working_figure']
        self.assertEqual(screw['designation'], 'M3 x %g' % screw['length_mm'])
        self.assertIn('M3 × %g mm screw' % screw['length_mm'], self.readme)
        self.assertIn('%d post screws' % self.fixing_list['counts']['posts'], self.readme)
        self.assertIn('%d fixings' % self.fixing_list['counts']['fixings'], self.readme)

    def test_readme_states_the_same_figures(self):
        text = self.readme
        rows = [[cell.strip() for cell in line.split('|')] for line in text.splitlines() if line.startswith('| [')]
        for m in self.spec['members']:
            (row,) = [cells for cells in rows if m['file'] in cells[1]]
            self.assertEqual(row[3], '%s mm' % sp.fmt_mm(m['gap_mm']), m['id'])
            self.assertEqual(row[4], '%s mm' % sp.fmt_mm(sp.length_mm(self.spec, m)), m['id'])
            self.assertEqual(row[5].split()[0], str(m['quantity']), m['id'])
            self.assertEqual(row[6], str(m['spares']), m['id'])
            if len(m['sites']) > 1:
                for board, count in m['sites'].items():
                    self.assertIn('%s %d' % (board, count), row[5])
            self.assertIn('%d sleeves for the %s mm gap in rows of %d'
                          % (m['quantity'] + m['spares'], sp.fmt_mm(m['gap_mm']), m['plate_columns']), text)
        sleeve = self.spec['sleeve']
        for token in (self.spec['plate']['file'],
                      '%s mm outer diameter' % sp.fmt_mm(sleeve['outer_diameter_mm']),
                      '%s mm bore' % sp.fmt_mm(sleeve['bore_diameter_mm']),
                      '%s mm short' % sp.fmt_mm(-self.spec['length_allowance_mm'])):
            self.assertIn(token, text)


if __name__ == '__main__':
    unittest.main()
