"""Source/geometry/fixture tests only; none invoke native KiCad or claim acceptance."""
import copy
import gzip
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from scripts.partition import core_split_candidates as c


class CoreSplitCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = c.Inputs()
        cls.candidates = {opt: json.loads((c.OUT/f'{opt}.json').read_text()) for opt in c.OPTIONS}

    def test_complete_ownership_and_expected_counts(self):
        expected = {'two': [(1795, 64, 106), (1590, 36, 85)],
                    'three': [(919, 31, 58), (1134, 33, 70), (1332, 36, 63)]}
        for option, data in self.candidates.items():
            owners = c.assignments(self.inputs, option)
            self.assertEqual(set(owners), set(self.inputs.components))
            self.assertEqual(owners, data['ownership'])
            rows = [(b['counts']['source_parts'], b['counts']['trimmers'], b['counts']['headers']) for b in data['boards'].values()]
            self.assertEqual(rows, expected[option])
            self.assertEqual(sum(b['counts']['dnp'] for b in data['boards'].values()), 8)
            self.assertEqual(sum(b['counts']['load_lands'] for b in data['boards'].values()), 18)
            self.assertEqual(sum(b['counts']['trimmers'] for b in data['boards'].values()), 100)

    def test_wrong_module_or_mixed_harness_rejected(self):
        options = copy.deepcopy(c.OPTIONS)
        options['two']['A'].remove('N1')
        options['two']['B'].append('N1')
        with patch.object(c, 'OPTIONS', options), self.assertRaisesRegex(ValueError, 'mixed or unassigned harness'):
            c.assignments(self.inputs, 'two')
        options['two']['B'].append('NO_SUCH_MODULE')
        with patch.object(c, 'OPTIONS', options), self.assertRaisesRegex(ValueError, 'missing/unknown module'):
            c.assignments(self.inputs, 'two')

    def test_sensitive_bypass_split_rejected(self):
        source = copy.copy(self.inputs)
        source.io = copy.deepcopy(source.io)
        source.io['islands'].append({'refs': ['U1105', 'U4106'], 'island_id': 'deliberate_cross_core'})
        with self.assertRaisesRegex(ValueError, 'sensitive island split'):
            c.assignments(source, 'two')

    def test_legacy_interface_and_fixed_panel_exact(self):
        contract = json.loads((c.OUT/'interface-contract.json').read_text())
        self.assertEqual(contract['harnesses'], self.inputs.partition['harnesses'])
        self.assertEqual(contract['endpoints'], self.inputs.partition['connectors'])
        self.assertEqual(len(contract['harnesses']), 195)
        self.assertEqual(len(contract['endpoints']), 390)
        self.assertEqual(len(contract['fixed_panel']['placements']), 438)
        self.assertEqual(len(contract['non_core_placements']), 2519)
        nc = next(h for h in contract['endpoints'] if h['id'] == 'JR-K-27-K')
        self.assertEqual([nc['pin_map'][str(i)] for i in range(5, 9)], ['NC']*4)

    def test_actual_courtyards_match_preserved_source_transforms(self):
        for ref in self.inputs.core:
            actual = self.inputs.geometry[ref].bounds
            expected = self.inputs.floor[ref]['courtyard_mm']
            for a, b in zip(actual, expected):
                self.assertAlmostEqual(a, b, places=5, msg=ref)
        self.assertAlmostEqual(sum(self.inputs.geometry[r].area for r in self.inputs.core), 48224.7924, places=4)

    def test_polygon_area_not_bbox_and_open_linework_rejected(self):
        node = c.parsed('(footprint "concave" (fp_poly (pts (xy 0 0) (xy 3 0) (xy 3 1) (xy 1 1) (xy 1 3) (xy 0 3)) (layer "F.CrtYd")))')
        shape = c.courtyard(node)
        self.assertEqual(shape.area, 5)
        self.assertEqual(shape.bounds, (0, 0, 3, 3))
        with self.assertRaisesRegex(ValueError, 'courtyard'):
            c.courtyard(c.parsed('(footprint "open" (fp_line (start 0 0) (end 3 0) (layer "F.CrtYd")))'))

    def test_same_face_gap_uses_distance_and_polygon_overlap(self):
        from shapely.geometry import box
        shapes = {'a': box(0, 0, 1, 1), 'b': box(1.34, 0, 2, 1), 'c': box(2.35, 0, 3, 1)}
        pairs = c.collision_pairs(list(shapes), shapes, .35)
        self.assertEqual([p['refs'] for p in pairs], [['a', 'b']])
        self.assertEqual(pairs[0]['overlap_mm2'], 0)

    def test_all_mechanical_holes_measured_and_ar_area_heavier(self):
        for data in self.candidates.values():
            for board in data['boards'].values():
                self.assertEqual(board['counts']['mechanical_footprints'], 199)
                for face in board['measurement']['faces'].values():
                    ids = [r['id'] for r in face['reservation_polygons_mm']]
                    self.assertEqual(sum(i.endswith('-hole') for i in ids), 191)
                    self.assertEqual(sum(i.endswith('-hook') for i in ids), 191)
                    self.assertGreater(face['usable_after_reservations_mm2'], 0)
        boards = self.candidates['two']['boards']
        self.assertGreater(boards['two-B']['source_part_courtyard_sum_mm2'], boards['two-A']['source_part_courtyard_sum_mm2'])

    def test_copper_index_preserves_duplicate_uuid_multiplicity(self):
        rows = [json.loads(line) for line in gzip.decompress((c.OUT/'copper-index.jsonl.gz').read_bytes()).splitlines()]
        self.assertEqual(rows, self.inputs.copper)
        counts = c.Counter(r['kind'] for r in rows)
        self.assertEqual(counts, {'segment': 123905, 'via': 9646, 'zone': 5, 'rule_area': 346})
        report = json.loads((c.OUT/'copper-contract.json').read_text())
        for option in report['options'].values():
            self.assertEqual(option['counts']['RETAIN_RULE_AREA'], 346)
            self.assertEqual(sum(option['counts'].values()), len(rows))
            for n in option['nets']:
                if n['net_token'] in c.RAILS:
                    self.assertEqual(n['disposition'], 'INVALIDATE_AND_REPLAY_COUPLED_COPPER')

    def test_source_lock_and_tool_binding(self):
        c.verify_lock()
        # Reusing an old label after a changed input must fail, not silently rehash.
        with patch.object(c, 'digest', return_value='0'*64), self.assertRaisesRegex(ValueError, 'stale candidate input'):
            c.verify_lock()

    def test_pilot_context_distinguishes_candidates(self):
        a = json.loads((c.OUT/'pilots/two-A.json').read_text())
        b = json.loads((c.OUT/'pilots/three-A.json').read_text())
        self.assertNotEqual(a['refs'], b['refs'])
        for key in c.SAMPLES:
            pilot = json.loads((c.OUT/f'pilots/{key}.json').read_text())
            opt = key.split('-')[0]
            self.assertEqual(pilot['refs'], self.candidates[opt]['boards'][key]['refs'])
            for t in pilot['targets'].values():
                for p in t['pads']:
                    self.assertEqual(self.inputs.pins[p['ref'], p['pad']], t['net_token'])

    def test_filter_retains_multunit_and_power_symbols(self):
        source = '(kicad_sch (symbol (property "Reference" "U1") (unit 1)) (symbol (property "Reference" "U1") (unit 2)) (symbol (property "Reference" "U2")) (symbol (property "Reference" "#PWR1")))'
        filtered = c.filtered_schematic(source, {'U1'})
        self.assertEqual(filtered.count('"U1"'), 2)
        self.assertNotIn('"U2"', filtered)
        self.assertIn('"#PWR1"', filtered)

    def test_materialized_context_is_portable_complete_and_no_native(self):
        with tempfile.TemporaryDirectory(prefix='osc-245-fixture-test-') as temp:
            output = Path(temp)/'fixture'
            # Avoid reparsing unchanged 48 MB PCB per test; all writes remain real.
            with patch.object(c, 'Inputs', return_value=self.inputs), patch.object(c.subprocess, 'run', side_effect=AssertionError('native process forbidden')):
                result = c.materialize('three-C', output)
            self.assertEqual(result['native'], 'NOT RUN')
            expected = set(self.candidates['three']['boards']['three-C']['refs'])
            seen = set()
            for file in (output/'before').rglob('*.kicad_sch'):
                text = file.read_text()
                for a, b in c.top_level_spans(text):
                    block = text[a:b]
                    if block.startswith('(symbol '):
                        ref = c.REF_RE.search(block)[1]
                        if not ref.startswith('#'):
                            seen.add(ref)
            self.assertEqual(seen, expected)
            for phase in ('before', 'after', 'fresh'):
                for name in ('osc-core.kicad_sch', 'osc-core.kicad_pro', 'osc-core.kicad_dru', 'fp-lib-table', 'sym-lib-table'):
                    self.assertTrue((output/phase/name).is_file())
                for table in ('fp-lib-table', 'sym-lib-table'):
                    for uri in re.findall(r'\(uri "([^"]+)"\)', (output/phase/table).read_text()):
                        self.assertTrue(Path(uri.replace('${KIPRJMOD}', str(output/phase))).exists(), uri)
            board = (output/'before/osc-core.kicad_pcb').read_text()
            native_refs = {c.REF_RE.search(board[a:b])[1] for a, b in c.top_level_spans(board) if board[a:b].startswith('(footprint ')}
            self.assertEqual(native_refs, expected | set(self.inputs.mechanical_refs))
            self.assertNotIn('(filled_polygon', board)
            self.assertEqual(board.count('(keepout'), 346)
            self.assertEqual(board.count('\n\t(zone'), 351)
            commands = json.loads((output/'commands.json').read_text())['commands']
            self.assertTrue(any('audit-pilot' in command for command in commands))
            self.assertTrue(any('fresh-copy' in command for command in commands))
            self.assertTrue(any('focus' in command for command in commands))
            with self.assertRaisesRegex(ValueError, 'must not exist'):
                c.materialize('three-C', output)

    def test_closed_native_sample_is_not_exercised_and_obstacles_retained(self):
        # Synthetic routing-selector unit data, explicitly not native acceptance.
        dump = {'pads': [{'uuid': 'a', 'net': '+12V', 'xy': [0, 0]}, {'uuid': 'b', 'net': '+12V', 'xy': [1, 0]},
                         {'uuid': 's1', 'net': 'SIGNAL', 'xy': [2, 0]}, {'uuid': 's2', 'net': 'SIGNAL', 'xy': [3, 0]}],
                'islands': {'+12V': [['a'], ['b']]}, 'tracks': [{'obstacle': True}], 'open_edges': 1}
        targets = {'supply': {'net_token': '+12V', 'pads': [{'uuid': 'a'}]},
                   'signal': {'net_token': 'SIGNAL', 'pads': [{'uuid': 's1'}, {'uuid': 's2'}]}}
        selected, report = c.focused_dump(dump, targets)
        self.assertEqual(selected['tracks'], dump['tracks'])
        self.assertEqual(selected['pads'], dump['pads'])
        self.assertEqual(len(selected['islands']['+12V']), 2)
        self.assertIn('NOT EXERCISED', report['signal']['status'])
        self.assertNotIn('SIGNAL', selected['islands'])

    def test_missing_native_drc_categories_fail_closed(self):
        with self.assertRaises(ValueError):
            c.validate_native_report({}, Path('osc-core.kicad_pcb'))
        report = {'violations': [], 'unconnected_items': [], 'schematic_parity': [],
                  'kicad_version': '10.0.6', 'source': 'osc-core.kicad_pcb', 'included_severities': ['error']}
        with self.assertRaisesRegex(ValueError, 'severity'):
            c.validate_native_report(report, Path('osc-core.kicad_pcb'))


if __name__ == '__main__':
    unittest.main()
