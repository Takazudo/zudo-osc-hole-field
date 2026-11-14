"""Unit tests for the printed spacer models: the retained STL files are read back and measured."""
import json
import math
import struct
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spacers as sp  # noqa: E402


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
            radii = {round(math.hypot(x, y), 3) for x, y, _ in points}
            self.assertEqual(radii, {round(ri, 3), round(ro, 3)})
            self.assertAlmostEqual(volume(tris), self.prism_volume(length), delta=0.05)

    def test_no_sleeve_is_longer_than_its_gap(self):
        self.assertLess(self.spec['length_allowance_mm'], 0)
        for m in self.spec['members']:
            self.assertAlmostEqual(sp.length_mm(self.spec, m), m['gap_mm'] - 0.2, places=6)

    def test_plate_holds_the_whole_set_without_touching(self):
        tris, _ = read_stl(self.files[self.spec['plate']['file']])
        places = sp.plate_positions(self.spec)
        self.assertEqual(len(places), sum(m['quantity'] + m['spares'] for m in self.spec['members']))
        self.assertEqual(shells(tris), len(places))
        centres = [(x, y) for _, x, y in places]
        nearest = min(math.dist(a, b) for i, a in enumerate(centres) for b in centres[i + 1:])
        self.assertGreaterEqual(nearest - self.sleeve['outer_diameter_mm'], 4.0)
        self.assertAlmostEqual(volume(tris), sum(self.prism_volume(sp.length_mm(self.spec, m)) for m, _, _ in places), delta=0.5)

    def test_sleeve_fits_the_screw_and_the_keep_out(self):
        self.assertGreater(self.sleeve['bore_diameter_mm'], 3.0)
        self.assertLessEqual(self.sleeve['outer_diameter_mm'] / 2, 3.75)


class AgreementWithTheStack(unittest.TestCase):
    def setUp(self):
        self.spec = sp.load()
        self.candidate = json.loads((sp.ROOT / 'design/stack/geometry/stack-candidate.json').read_text())['candidate']

    def test_gaps_are_the_candidates_gaps(self):
        gaps = self.candidate['stack']['stacker_height_by_gap']
        for m in self.spec['members']:
            for pair in m['between']:
                self.assertEqual(gaps[pair]['gap_mm'], m['gap_mm'], pair)

    def test_counts_are_the_kept_supports(self):
        kept = Counter(f['front_board'] for f in self.candidate['fixings'] if f['kind'] == 'kept support')
        listed = Counter()
        for m in self.spec['members']:
            listed.update(m['sites'])
            self.assertEqual(sum(m['sites'].values()), m['quantity'])
        self.assertEqual(dict(listed), dict(kept))

    def test_readme_states_the_same_figures(self):
        text = (sp.ROOT / 'design/stack/spacers/README.md').read_text()
        for m in self.spec['members']:
            for token in (m['file'], '%.1f mm' % m['gap_mm'], '%.1f mm' % sp.length_mm(self.spec, m)):
                self.assertIn(token, text)
        self.assertIn(self.spec['plate']['file'], text)


if __name__ == '__main__':
    unittest.main()
