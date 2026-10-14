"""Tiny source-only fixtures, never native acceptance or production materialization."""
import copy
import json
import math
import unittest

import clip_sheets
import connectivity
import fragments
import materialize_e16
import selective_annulus as a
from test_connectivity import base, pad


def fixture():
    source, planes = base()
    x, y = 110.245, 184.97
    source['objects'] += [
        pad(a.PAD_ID, 'AGND', x, y, r=.32, layer='B.Cu'),
        {'id': a.VIA_ID, 'kind': 'via', 'net': 'AGND', 'layers': list(a.LAYERS),
         'center_mm': [x, y], 'diameter_mm': .6, 'drill_mm': .3,
         'access_for_pad': a.PAD_ID, 'epoch': 'E16', 'via_in_pad': True},
        {'id': 'original-artwork', 'kind': 'rule_area', 'layers': ['F.Cu'],
         'polygon_mm': [[100, 170], [101, 170], [101, 171]], 'rules': {}}]
    # A short same-net functional B-face path to an explicit feed terminal.
    source['objects'][3] = pad('CS247-KA-W4', 'AGND', x+.5, y, r=.3, layer='B.Cu')
    source['loads'].append({'net': 'AGND', 'pad_id': a.PAD_ID})
    return source, planes


class SelectiveAnnulus(unittest.TestCase):
    def test_default_unchanged(self):
        s, p = fixture()
        v = s['objects'][-2]
        self.assertEqual(a.diameter(v, None), .6)
        self.assertEqual(clip_sheets.copper(v).area, clip_sheets.copper(v, 'In3.Cu').area)
        self.assertNotIn(a.FIELD, json.loads(json.dumps(s))['objects'][-2])
        self.assertIn('(size 0.600000000)', materialize_e16.serialize_object(v))

    def test_one_policy_only_and_originals_exact(self):
        s, _ = fixture()
        original = copy.deepcopy(s)
        out = a.apply(s)
        changed = [(x, y) for x, y in zip(s['objects'], out['objects']) if x != y]
        self.assertEqual(len(changed), 1)
        self.assertEqual(changed[0][1]['id'], a.VIA_ID)
        self.assertEqual(a.original(changed[0][1]), changed[0][0])
        self.assertEqual(s, original)

    def test_json_reload_and_idempotence(self):
        out = a.apply(fixture()[0])
        reloaded = json.loads(json.dumps(out))
        a.validate_source(reloaded)
        self.assertEqual(a.apply(reloaded), out)

    def test_barrel_and_all_other_annuli_preserved(self):
        out = a.apply(fixture()[0])
        v = next(o for o in out['objects'] if o['id'] == a.VIA_ID)
        self.assertEqual(v['layers'], a.LAYERS)
        self.assertEqual(v['drill_mm'], .3)
        for layer in a.LAYERS:
            self.assertAlmostEqual(a.diameter(v, layer), .35 if layer == a.LAYER else .6)
        with self.assertRaisesRegex(ValueError, 'explicit known foil'):
            clip_sheets.copper(v)

    def test_unknown_identity_layer_and_policy_fail(self):
        s, _ = fixture()
        out = a.apply(s)
        for changes in ({'via_id': 'unknown'}, {'omit_layer': 'In7.Cu'},
                        {'omit_layer': 'B.Cu'}, {'remove_unused_layers': True}):
            changed = copy.deepcopy(out)
            v = next(o for o in changed['objects'] if o['id'] == a.VIA_ID)
            v[a.FIELD].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                a.validate_source(changed)
        s['objects'] = [o for o in s['objects'] if o['id'] != a.VIA_ID]
        with self.assertRaisesRegex(ValueError, 'absent'):
            a.apply(s)

    def test_functional_and_tangent_contacts_refused(self):
        for offset in (0, .35):
            s, _ = fixture()
            s['objects'].append(pad('functional', 'AGND', 110.245+offset, 184.97,
                                    r=.05, layer='In3.Cu'))
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, 'contact'):
                a.apply(s)

    def test_source_edit_after_audit_refused(self):
        out = a.apply(fixture()[0])
        out['objects'][0]['polygon_mm'][0][0] += .01
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            a.validate_source(out)

    def test_original_via_geometry_or_net_edit_refused(self):
        for changes in ({'net': '-12V'}, {'drill_mm': .31}, {'diameter_mm': .59},
                        {'center_mm': [110.246, 184.97]}, {'layers': ['F.Cu', 'B.Cu']}):
            s, _ = fixture()
            v = next(o for o in s['objects'] if o['id'] == a.VIA_ID)
            v.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                a.apply(s)

    def test_graph_and_finite_fragments_preserve_functional_contacts(self):
        s, p = fixture()
        before = connectivity.build(s, p)
        out = a.apply(s)
        after = connectivity.build(out, p)
        self.assertEqual(before['physical_ports'], after['physical_ports'])
        self.assertEqual(before['object_connections'], after['object_connections'])
        self.assertTrue(after['object_connections'][a.PAD_ID]['all_fragments_connected_to_feed'])
        fs = fragments.NetFragments(out, p, 'AGND')
        fs.verify(after)
        target = [i for i in fs.portnodes[a.VIA_ID] if fs.layer[i] == a.LAYER]
        self.assertEqual(len(target), 1)
        self.assertGreater(fs.nodes[target[0]].area, 0)  # barrel remains, no bore copper
        self.assertLess(fs.nodes[target[0]].area, math.pi * (.175**2 - .15**2))
        self.assertEqual(len(fs.barrels[a.VIA_ID]), 6)

    def test_clipping_uses_barrel_and_preserves_other_layers(self):
        s, _ = fixture()
        out = a.apply(s)
        outline = [[109,184], [111.5,184], [111.5,186], [109,186]]
        before, _ = clip_sheets.clip(s, outline)
        after, _ = clip_sheets.clip(out, outline)
        self.assertNotEqual(before['-12V'], after['-12V'])
        for net in ('AGND', '+12V', '+5V'):
            self.assertEqual(before[net], after[net])

    def test_native_explicitly_unsupported(self):
        s = a.apply(fixture()[0])
        v = next(o for o in s['objects'] if o['id'] == a.VIA_ID)
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_NATIVE_SELECTIVE_ANNULUS'):
            materialize_e16.serialize_object(v)
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_NATIVE_SELECTIVE_ANNULUS'):
            materialize_e16.materialize('KA', '(kicad_pcb)', fixture()[0], s, [])

    def test_oblique_tangent_circular_contact_refused(self):
        s, _ = fixture()
        other = copy.deepcopy(s['objects'][-2])
        other['id'] = 'oblique-via'
        angle = math.pi / 128
        other['center_mm'] = [110.245 + .6 * math.cos(angle),
                              184.97 + .6 * math.sin(angle)]
        s['objects'].append(other)
        with self.assertRaisesRegex(ValueError, 'contact'):
            a.apply(s)

    def test_staged_caps_and_supplemental_inventory_fail_closed(self):
        s, p = fixture()
        s['staged_cap_solids'] = {'caps': [{'net': 'AGND', 'layer': 'In3.Cu'}]}
        with self.assertRaisesRegex(ValueError, 'staged cap'):
            a.apply(s)
        out = a.apply(fixture()[0])
        p['new_objects'] = [pad('extra', 'AGND', 110.245, 184.97, layer='In3.Cu')]
        with self.assertRaisesRegex(ValueError, 'supplemental'):
            connectivity.build(out, p)
        p['new_objects'] = []
        p['clipped_sheets']['AGND'] = [{'layer': 'In3.Cu'}]
        with self.assertRaisesRegex(ValueError, 'sheet layer'):
            fragments.NetFragments(out, p, 'AGND')

    def test_contradictory_global_policy_refused(self):
        s, _ = fixture()
        s['objects'][-2]['remove_unused_layers'] = True
        with self.assertRaisesRegex(ValueError, 'global'):
            a.apply(s)


if __name__ == '__main__':
    unittest.main()
