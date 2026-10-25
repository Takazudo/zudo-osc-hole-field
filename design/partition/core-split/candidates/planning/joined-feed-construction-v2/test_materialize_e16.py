#!/usr/bin/env python3
"""Small source-only regression tests; no routing, solver or native process."""
import copy
import unittest
import uuid
import materialize_e16 as m


def uid(value):
    return str(uuid.uuid5(m.NS, value))


class MaterializationTests(unittest.TestCase):
    def setUp(self):
        self.pad = {'id': uid('test-pad'), 'kind': 'pad', 'net': '+5V', 'layers': ['F.Cu'],
                    'polygon_mm': [[0, 0], [1, 0], [1, 1], [0, 1]], 'center_mm': [.5, .5]}
        self.base = {'schema': 'e16-normalized-board-v1', 'board': 'KB', 'coordinate_offset_mm': m.OFFSET,
                     'objects': [self.pad], 'loads': [], 'input_sha256': {'run-local': 'seal'}}
        self.ref = {'objects': 1, 'loads': 0,
                    'content_sha256': m.digest({k: v for k, v in self.base.items() if k not in m.SEALS})}
        self.via = {'id': uid('test-via'), 'kind': 'via', 'net': '+5V', 'layers': m.LAYERS,
                    'center_mm': [1., 2.], 'diameter_mm': .6, 'drill_mm': .3,
                    'epoch': 'E16', 'access_for_pad': self.pad['id'], 'process': 'standard through via'}
        self.seg = {'id': uid('test-segment'), 'kind': 'segment', 'net': '+5V', 'layers': ['F.Cu'],
                    'path_mm': [[.5, .5], [1., 2.]], 'width_mm': .25,
                    'epoch': 'E16', 'access_for_pad': self.pad['id']}
        layers = ' '.join(f'({i} "{layer}" signal)' for i, layer in enumerate(m.LAYERS))
        nets = ' '.join(f'(net "{net}")' for net in m.NET_LAYER)
        self.pcb = f'(kicad_pcb (version 20260206) (layers {layers}) {nets}\n'
        self.pcb += f'(footprint "test" (uuid "{uid("test-fp")}") (pad "1" (uuid "{self.pad["id"]}")))\n'
        self.pcb += f'(zone (uuid "{uid("rule")}") (keepout (tracks not_allowed)))\n)\n'
        self.outline = [[0., 0.], [10., 0.], [10., 10.], [0., 10.]]

    def compose(self, spans=None, pilot=None):
        return m.compose('KB', self.base, spans or [[self.via], [self.seg]], self.ref, pilot)

    def test_retained_spans_once_and_base_is_immutable(self):
        original = copy.deepcopy(self.base)
        out = self.compose()
        self.assertEqual(out['objects'], [self.pad, self.via, self.seg])
        self.assertEqual(self.base, original)
        self.assertNotIn('input_sha256', out)

    def test_run_local_seal_changes_do_not_change_base_lock(self):
        self.base['input_sha256'] = {'another-absolute-path': 'different'}
        self.compose()

    def test_base_geometry_drift_fails_closed(self):
        self.base['objects'][0]['center_mm'][0] += .001
        with self.assertRaisesRegex(ValueError, 'base differs'):
            self.compose()

    def test_duplicate_span_and_source_identity_reuse_rejected(self):
        for spans in ([[self.via], [self.via]], [[dict(self.via, id=self.pad['id'])], [self.seg]]):
            with self.subTest(spans=spans), self.assertRaisesRegex(ValueError, 'identity'):
                self.compose(spans)

    def test_wrong_net_typed_vias_and_per_layer_stacks_rejected(self):
        changes = [{'net': '-12V'}, {'via_type': 'microvia'}, {'layers': ['F.Cu', 'In1.Cu']},
                   {'padstack': {'In3.Cu': 0}}, {'diameter_mm': float('nan')}, {'drill_mm': .6}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.compose([[dict(self.via, **change)], [self.seg]])

    def test_segments_require_straight_positive_outer_face_geometry(self):
        for change in ({'layers': ['In3.Cu']}, {'path_mm': [[0, 0]]}, {'path_mm': [[0, 0], [0, 0]]}, {'width_mm': 0}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.compose([[self.via], [dict(self.seg, **change)]])

    def test_byte_preservation_inverse_coordinates_and_zone_policy(self):
        src = self.compose()
        out, receipt = m.materialize('KB', self.pcb, self.base, src, self.outline)
        close = self.pcb.rfind(')')
        self.assertEqual(out[:close], self.pcb[:close])
        self.assertTrue(out.endswith(self.pcb[close:]))
        self.assertIn('(at 101.000000000 52.000000000)', out)
        self.assertIn('(layers "F.Cu" "B.Cu")', out)
        self.assertIn('(min_thickness .25)', out)
        self.assertIn('(connect_pads yes (clearance .25))', out)
        self.assertNotIn('filled_polygon', out)
        self.assertEqual(len(receipt['unfilled_zone_ids']), 4)
        self.assertEqual(receipt['added_objects'], 2)
        self.assertEqual(receipt['native_calls'], 0)
        self.assertEqual((out, receipt), m.materialize('KB', self.pcb, self.base, src, self.outline))

    def test_native_uuid_collision_rejected(self):
        pcb = self.pcb.replace(uid('test-fp'), self.via['id'])
        with self.assertRaisesRegex(ValueError, 'collision'):
            m.materialize('KB', pcb, self.base, self.compose(), self.outline)

    def test_p1_is_separate_and_may_only_add_three_face_segments(self):
        p1 = [dict(self.seg, id=uid('p1-' + str(n)), epoch='E16-P1') for n in range(3)]
        t2 = self.compose()
        combined = self.compose(pilot=p1)
        self.assertEqual(combined['objects'][:len(t2['objects'])], t2['objects'])
        self.assertEqual(len(t2['objects']), 3)
        with self.assertRaises(ValueError):
            self.compose(pilot=[dict(self.via, epoch='E16-P1')] * 3)
        with self.assertRaises(ValueError):
            m.compose('KA', dict(self.base, board='KA'), [[self.via], [self.seg]], self.ref, p1)


if __name__ == '__main__':
    unittest.main()
