"""Fault injection and staleness tests for the stack-geometry candidate and checker.

No network and no KiCad: the boards are parsed with plain Python.
"""
import copy
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check  # noqa: E402
import generate  # noqa: E402
import measure  # noqa: E402
import kicad_extract  # noqa: E402
import stackgeom as sg  # noqa: E402


def setUpModule():
    global RAW, CI, CTX, DOC
    RAW = sg.load_raw()
    CI = sg.canonical_inputs(RAW, sg.load_boards(RAW))
    CTX = check.Context(CI)
    DOC = json.loads(sg.CANDIDATE.read_text())


def pair(doc, pid):
    return next(p for p in doc['candidate']['pairs'] if p['id'] == pid)


def tab(doc, tid):
    return next(t for t in doc['candidate']['tabs'] if t['id'] == tid)


class CommittedCandidate(unittest.TestCase):
    def test_committed_candidate_fails_only_on_the_needs_design_items(self):
        res = check.run_checks(DOC, CTX)
        self.assertEqual(sorted({e.split(':')[0] for e in res.errors}), ['adapter_standoff_candidates', 'el_relief_holes'])
        holes = [e for e in res.errors if e.startswith('el_relief_holes')]
        self.assertEqual(len(holes), 2)
        for e, pin, rsv in zip(holes, (1, 2), ('UNSELECTED-BULK-2', 'UNSELECTED-BULK-3')):
            self.assertIn('pair EL-P-E1 relief hole pin %d' % pin, e)
            self.assertIn('overlaps EL F.Cu reserve %s (reserve) by 0.85 mm' % rsv, e)
        self.assertEqual(len([e for e in res.errors if e.startswith('adapter_standoff')]), 3)

    def test_candidate_is_not_stale(self):
        digest = sg.canonical_digest(CI)
        self.assertEqual(DOC['canonical_input_digest'], digest,
                         'stack-candidate.json is stale; regenerate with: ' + sg.REGEN_COMMAND)
        self.assertEqual(json.dumps(DOC['candidate'], sort_keys=True), json.dumps(CTX.reference, sort_keys=True),
                         'stack-candidate.json differs from a fresh generation; regenerate with: ' + sg.REGEN_COMMAND)

    def test_tracked_outputs_depend_on_inputs_only(self):
        out, _ = generate.generate()
        self.assertNotIn('git_head', out['provenance'])
        self.assertEqual(generate.render(out), sg.CANDIDATE.read_text(),
                         'stack-candidate.json differs from a fresh generation; regenerate with: ' + sg.REGEN_COMMAND)
        report = check.build_report(DOC, CTX, sg.sha256_file(sg.CANDIDATE))
        self.assertEqual(json.dumps(report, indent=1) + '\n', sg.REPORT.read_text(),
                         'check-report.json differs from a fresh check; regenerate with: ' + sg.REGEN_COMMAND)

    def test_plan_totals(self):
        res = check.run_checks(DOC, CTX)
        t = res.checks['pin_budget']['detail']['totals']
        self.assertEqual((t['pairs'], t['positions'], t['K_pairs'], t['K_positions']), (203, 825, 197, 777))
        self.assertEqual((t['signal_positions'], t['AGND'], t['rail'], t['unused']), (531, 276, 18, 2))


class Staleness(unittest.TestCase):
    """The digest binds footprint geometry, not routing."""

    def setUp(self):
        self.text = (sg.ROOT / sg.BOARD_FILES['O1']).read_text()
        self.base = self.digest(self.text)

    def digest(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'b.kicad_pcb')
            Path(path).write_text(text)
            t = RAW['lock']['frame']['kicad_translation_mm']
            return sg.canonical_digest(kicad_extract.parse_board(path, (t['x'], t['y'])))

    def test_routing_only_change_keeps_digest(self):
        end = self.text.rstrip().rfind(')')
        routed = (self.text[:end] + '\t(segment\n\t\t(start 110 230)\n\t\t(end 120 230)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n'
                  '\t\t(net "AGND")\n\t\t(uuid "00000000-0000-0000-0000-000000000001")\n\t)\n'
                  '\t(via\n\t\t(at 115 231)\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n'
                  '\t\t(net "AGND")\n\t\t(uuid "00000000-0000-0000-0000-000000000002")\n\t)\n' + self.text[end:])
        self.assertEqual(self.digest(routed), self.base)

    def test_footprint_move_changes_digest(self):
        moved = re.sub(r'(\n\t\(footprint "[^"]*"(?:\n\t\t[^\n]*)*?\n\t\t\(at )(-?[\d.]+)', lambda m: m.group(1) + str(float(m.group(2)) + 0.5),
                       self.text, count=1)
        self.assertNotEqual(moved, self.text)
        self.assertNotEqual(self.digest(moved), self.base)

    def test_stale_digest_names_regeneration_command(self):
        doc = copy.deepcopy(DOC)
        doc['canonical_input_digest'] = '0' * 64
        res = check.run_checks(doc, CTX)
        self.assertTrue(any('regenerate with: ' + sg.REGEN_COMMAND in e for e in res.errors), res.errors)

    def test_hand_edited_candidate_is_stale(self):
        doc = copy.deepcopy(DOC)
        pair(doc, 'K-P-1')['note'] = 'hand edit'
        res = check.run_checks(doc, CTX)
        self.assertTrue(any('differs from a fresh generation' in e for e in res.errors), res.errors)


class FaultInjection(unittest.TestCase):
    def assertFault(self, doc, pattern, ctx=None):
        res = check.run_checks(doc, ctx or CTX)
        self.assertTrue(any(re.search(pattern, e) for e in res.errors), 'expected %r in %s' % (pattern, res.errors[:8]))

    def test_non_coaxial_site(self):
        doc = copy.deepcopy(DOC)
        pair(doc, 'K-P-1')['sites']['back']['center'][0] += 0.5
        self.assertFault(doc, r'coaxial_sites: pair K-P-1 is not coaxial')

    def test_site_off_replaced_header(self):
        doc = copy.deepcopy(DOC)
        p = pair(doc, 'JL-K-1')
        for s in p['sites'].values():
            s['center'][1] += 1.0
        self.assertFault(doc, r'not at the replaced J900001 courtyard centre')

    def test_land_pattern_wider_than_gh_courtyard(self):
        ci = copy.deepcopy(CI)
        ci['land_pattern']['halves']['K']['explicit']['1x3'] = {'width_mm': 6.5, 'length_mm': 7.0, 'status': 'TEST', 'source': 'test'}
        ctx = check.Context(ci)
        self.assertFault(DOC, r'replacement_inside_gh_courtyard: pair K-P-1 back envelope .* outside the GH courtyard', ctx)

    def test_undeclared_blocker(self):
        doc = copy.deepcopy(DOC)
        pair(doc, 'JL-K-X3')['sites']['back']['blockers'] = []
        self.assertFault(doc, r'pair JL-K-X3 back site on K F.Cu has undeclared blocker R1286')

    def test_declared_blocker_absent_from_sources(self):
        doc = copy.deepcopy(DOC)
        pair(doc, 'JL-K-X1')['sites']['back']['blockers'] = [['R9999', 'courtyard']]
        self.assertFault(doc, r'declares blocker R9999 that the sources do not give')

    def test_missing_net(self):
        doc = copy.deepcopy(DOC)
        p = pair(doc, 'K-P-1')
        p['pin_map'][0] = 'NC'
        self.assertFault(doc, r'pin_budget: pair K-P-1 does not carry /A01/C38cac0_W')

    def test_signal_without_return(self):
        doc = copy.deepcopy(DOC)
        p = pair(doc, 'JL-K-1')
        p['pin_map'][1], p['pin_map'][2] = p['pin_map'][2], p['pin_map'][1]
        self.assertFault(doc, r'pair JL-K-1 puts .* on an AGND position|has no adjacent AGND')

    def test_pin_count_over_positions(self):
        doc = copy.deepcopy(DOC)
        pair(doc, 'K-P-2')['pin_map'].append('AGND')
        self.assertFault(doc, r'pair K-P-2 has 4 pin entries for 3 positions')

    def test_unreplaced_harness(self):
        doc = copy.deepcopy(DOC)
        doc['candidate']['pairs'] = [p for p in doc['candidate']['pairs'] if p['id'] != 'K-P-7']
        self.assertFault(doc, r'harness K-P-7 is not replaced by any pair')

    def test_missing_pass_through_site(self):
        doc = copy.deepcopy(DOC)
        doc['candidate']['pairs'] = [p for p in doc['candidate']['pairs'] if p['id'] != 'P-K-X2']
        self.assertFault(doc, r'expected 8 JL-to-P pass-through pairs, found 7')

    def test_offset_post_unresolved(self):
        doc = copy.deepcopy(DOC)
        post = next(p for p in doc['candidate']['posts'] if p['id'] == 'POWER-P-+12V')
        post['proposed_front_land'] = list(post['front_land'])
        self.assertFault(doc, r'post POWER-P-\+12V is not coaxial: front land \[142, 179\], K land \[142, 175\]')

    def test_power_tab_too_short(self):
        doc = copy.deepcopy(DOC)
        tab(doc, 'TAB-POWER')['rect'][2] = 150.0
        self.assertFault(doc, r'post POWER-P-AGND1 moved land courtyard .* is outside TAB-POWER')

    def test_tab_over_jack_board(self):
        doc = copy.deepcopy(DOC)
        tab(doc, 'TAB-EL')['rect'][1] = 160.0
        self.assertFault(doc, r'tab TAB-EL .* overlaps board outline JR')

    def test_tab_over_carrier(self):
        doc = copy.deepcopy(DOC)
        tab(doc, 'TAB-EL')['rect'][1] = 166.5
        res = check.Result()
        check.check_tabs(doc['candidate'], CTX, res)
        self.assertEqual(res.errors, [], 'the cross-member is removed (DA-01 D3)')
        ctx = copy.copy(CTX)
        ctx.params = dict(CTX.params, removed_carriers=[])
        self.assertFault(doc, r'tab TAB-EL .* overlaps the seam cross-member 2 carrier envelope', ctx)

    def test_tab_over_support(self):
        doc = copy.deepcopy(DOC)
        tab(doc, 'TAB-EL')['pass_through_supports'] = []
        self.assertFault(doc, r'tab TAB-EL .* overlaps support EL-OPT-1 collar')

    def test_tab_over_selector(self):
        doc = copy.deepcopy(DOC)
        tab(doc, 'TAB-CONTROL-O2')['rect'][0] = 23.5
        self.assertFault(doc, r'tab TAB-CONTROL-O2 .* overlaps selector SW101 courtyard')

    def test_tab_holding_foreign_post(self):
        doc = copy.deepcopy(DOC)
        tab(doc, 'TAB-POWER')['carried_posts'] = []
        self.assertFault(doc, r'tab TAB-POWER .* holds post land POWER-P-\+12V')

    def test_sub_pair_outside_window(self):
        doc = copy.deepcopy(DOC)
        s = next(x for x in doc['candidate']['sub_toggles'] if x['block'] == 'O2')
        s['site_centre'][1] = 181.5
        self.assertFault(doc, r'SUB pair at O2 centre \[31.5, 181.5\] is outside the placement window y=180.25..180.75')

    def test_control_tab_ending_at_178(self):
        doc = copy.deepcopy(DOC)
        tab(doc, 'TAB-CONTROL-O2')['rect'][1] = 178.0
        self.assertFault(doc, r'SUB pair O2 envelope .* is not inside control tab')

    def test_stale_k_plane(self):
        doc = copy.deepcopy(DOC)
        doc['candidate']['stack']['K_face_z_mm'] = -22.0
        self.assertFault(doc, r'stale K_face_z_mm -22.0, sources give -30.4')

    def test_stale_pair_height(self):
        doc = copy.deepcopy(DOC)
        pair(doc, 'K-O1-1')['mated_height_mm'] = 6.2
        self.assertFault(doc, r'pair K-O1-1 mated height 6.2 differs from gap O1/K 12.8')

    def test_selector_tail_reaches_k(self):
        ci = copy.deepcopy(CI)
        ci['parameters']['k_plane']['adapter_mated_height_mm'] = 2.0
        ctx = check.Context(ci)
        doc = {'candidate': ctx.reference, 'canonical_input_digest': sg.canonical_digest(ci)}
        self.assertFault(doc, r'selector tail at z=-20 reaches K F.Cu at z=-19.6', ctx)

    def test_facing_height_collision(self):
        doc = copy.deepcopy(DOC)
        doc['candidate']['stack']['mated_heights_mm']['P/K'] = 3.0
        self.assertFault(doc, r'facing-height collision in gap P/K \(3.0 mm\)')

    def test_retired_board_reused(self):
        doc = copy.deepcopy(DOC)
        pair(doc, 'K-O1-1')['boards'] = ['K', 'O2']
        self.assertFault(doc, r'pair K-O1-1 uses retired board O2')

    def test_retired_aperture_count(self):
        doc = copy.deepcopy(DOC)
        doc['candidate']['retired']['K_service_apertures'] = 187
        self.assertFault(doc, r'retired K service aperture count 187')


class ContinuationC1(unittest.TestCase):
    def test_toggle_courtyard_off_tab(self):
        doc = copy.deepcopy(DOC)
        s = next(x for x in doc['candidate']['sub_toggles'] if x['block'] == 'O2')
        s['toggle_courtyard'][1] -= 12.0
        s['toggle_courtyard'][3] -= 12.0
        self.assertFault(doc, r'SUB toggle O2 courtyard .* is not inside control tab .* or P outline')

    def test_toggle_tail_reported_not_checkable(self):
        res = check.run_checks(DOC, CTX)
        tails = res.checks['sub_toggle_windows']['detail']['toggle_tail_against_K']
        self.assertEqual({v['status'] for v in tails.values()}, {'NOT CHECKABLE'})
        self.assertIn('missing_source', tails['O2'])

    def test_k_half_wider_than_front_half(self):
        ci = copy.deepcopy(CI)
        ci['land_pattern']['halves']['K']['explicit']['1x3'] = {'width_mm': 6.5, 'length_mm': 7.0, 'status': 'TEST', 'source': 'test'}
        ctx = check.Context(ci)
        obs = dict(ctx.obstacles, **sg.stack_obstacles(ci, ('O2', 'O4')))
        fits = measure.envelope_fits(ci, obs, ci['land_pattern'], ci['parameters']['positions'])['GH3']
        self.assertEqual(fits['envelope_mm'], {'front': [5.8, 7.0], 'K': [6.5, 7.0]})
        expect = 0
        for p in ctx.reference['pairs']:
            if p['family'] != 'K/P':
                continue
            k = p['sites']['back']
            rect = sg.env_rect(k['center'][0], k['center'][1], 6.5, 7.0, k['long_axis_x'])
            expect += bool(ctx.obstacles['K'].hits('F', rect, {k['replaces']}))
        self.assertGreater(expect, 0)
        self.assertEqual(fits['sites'] - fits['fit_in_place_both_boards'], expect)
        sub = next(s for s in ctx.reference['sub_toggles'] if s['block'] == 'O2')
        tab_top = next(t for t in ctx.reference['tabs'] if t['id'] == 'TAB-CONTROL-O2')['rect'][1]
        m = ci['parameters']['tab_edge_margin_mm']
        self.assertAlmostEqual(tab_top, sub['site_centre'][1] - 6.5 / 2 - m, places=4)
        probe = 178.0
        ci['parameters']['probe_tab_top_mm'] = probe
        short = next(e for e in measure.measure(ci, ctx.reference, ctx)['sub_tab_probe'] if e['block'] == 'O2')
        self.assertAlmostEqual(short['shortfall_mm'], probe + m + 6.5 / 2 - sub['window_centre_y'][1], places=4)

    def test_support_inside_k_does_not_raise(self):
        ci = copy.deepcopy(CI)
        sup = next(s for s in ci['partition']['supports'] if s['id'] == 'P-SUP-2')
        sup['position_mm'] = [150.0, 238.0]
        res = measure.supports(ci)
        e = next(x for x in res['P_collars'] if x['support'] == 'P-SUP-2')
        self.assertTrue(e['centre_inside_K'])
        self.assertEqual(e['overlap_mm'], sup['collar_diameter_mm'])

    def test_measurement_failure_becomes_report_error(self):
        saved = measure.measure
        measure.measure = lambda *a: (_ for _ in ()).throw(ValueError('injected'))
        try:
            report = check.build_report(DOC, CTX, 'x')
        finally:
            measure.measure = saved
        self.assertEqual(report['verdict'], 'FAIL')
        self.assertIn('measurements: ValueError: injected', report['errors'])

    def test_sub_threshold_post_offset_agrees(self):
        ci = copy.deepcopy(CI)
        t = next(x for x in ci['partition']['load_side_terminals'] if x['reference'] == 'TP990001')
        t['center_mm'] = [t['center_mm'][0] + sg.OFFSET_TOL_MM / 2, t['center_mm'][1]]
        ctx = check.Context(ci)
        cand = ctx.reference
        post = next(p for p in cand['posts'] if p['id'] == 'POWER-JL-+12V')
        self.assertGreater(post['present_offset_mm'], 0)
        self.assertIsNone(post['resolved_by'])
        res = check.Result()
        check.check_posts(cand, ctx, res)
        self.assertEqual(res.errors, [])
        self.assertEqual(res.checks['post_coaxiality']['detail']['coaxial_today'], 14)
        lands = measure.power_lands(ci, cand, ci['parameters']['power_land_neighbour_radius_mm'])
        self.assertEqual(lands['coaxial_pairs'], 14)
        self.assertEqual(len(lands['offset_pairs']), 4)

    assertFault = FaultInjection.assertFault


def check_one(fn, doc, ctx=None):
    res = check.Result()
    fn(doc['candidate'], ctx or CTX, res)
    return res


class AttemptA2(unittest.TestCase):
    assertFault = FaultInjection.assertFault

    def test_planes_at_the_decided_adapter_height(self):
        st = DOC['candidate']['stack']
        self.assertEqual((st['K_face_z_mm'], st['K_rear_z_mm'], st['K_rear_parts_z_mm']), (-30.4, -32.0, -37.0))
        g = st['mated_heights_mm']
        self.assertEqual([g[k] for k in ('O1/K', 'O3/K', 'O5/K', 'P/K', 'JL/K', 'JR/K', 'EL/P')],
                         [12.8, 12.8, 12.8, 17.0, 18.8, 18.8, 7.2])

    def test_stacker_height_rule(self):
        a = {g: r['stacker_A_mm'] for g, r in DOC['candidate']['stack']['stacker_height_by_gap'].items()}
        self.assertEqual((a['O1/K'], a['P/K'], a['JL/K']), (7.493, 11.684, 13.462))
        self.assertEqual(check_one(check.check_stacker_heights, DOC).errors, [])
        doc = copy.deepcopy(DOC)
        doc['candidate']['stack']['stacker_height_by_gap']['P/K']['stacker_A_mm'] = 11.811
        self.assertTrue(any('stacker A 11.811 + socket 4.5 + clearance 0.8 mm exceeds it' in e
                            for e in check_one(check.check_stacker_heights, doc).errors))

    def test_rear_envelope_rows(self):
        res = check_one(check.check_rear_envelope, DOC)
        self.assertEqual(res.errors, [])
        rows = {r['inside_depth_mm']: r['clearance_mm'] for r in res.checks['rear_envelope']['detail']['cases']}
        self.assertEqual(rows, {40: 3.0, 34: -3.0})
        doc = copy.deepcopy(DOC)
        for c in doc['candidate']['stack']['enclosure_depth_cases']:
            c['decided'] = c['inside_depth_mm'] == 34
        self.assertTrue(any('pass the enclosure inner rear at z=-34 by 3.0 mm' in e for e in check_one(check.check_rear_envelope, doc).errors))

    def test_land_pattern_entries_carry_provenance(self):
        used = DOC['candidate']['land_pattern']['envelopes_used']
        self.assertEqual((used['K']['1x3']['width_mm'], used['K']['1x3']['length_mm']), (6.04, 5.52))
        self.assertEqual((used['K']['2x4']['width_mm'], used['K']['2x4']['length_mm']), (8.07, 7.52))
        self.assertEqual({e['status'] for e in used['front'].values()}, {'PROVISIONAL'})
        for half in used.values():
            for e in half.values():
                self.assertTrue(e['source'])
        for p in DOC['candidate']['pairs']:
            self.assertIn(p['sites']['front']['envelope_entry'].split()[-1], ('PROVISIONAL', 'DERIVED'))

    def test_el_pairs_are_2x4_with_three_rails(self):
        el = [p for p in DOC['candidate']['pairs'] if p['family'] == 'EL/P']
        self.assertEqual(len(el), 6)
        for p in el:
            self.assertEqual((p['positions'], p['rows']), (8, 2))
            self.assertEqual(sorted(n for n in p['pin_map'] if n in check.RAILS), sorted(check.RAILS))
            self.assertEqual(p['pin_map'].count('AGND'), 2)
            self.assertEqual(check.adjacency_violations(p['pin_map'], 2), [])
            self.assertEqual(len(p['relief_holes']), 8)
        self.assertEqual(tab(DOC, 'TAB-EL')['rect'][1], 167.465)

    def test_two_row_adjacency(self):
        self.assertEqual(sorted(check.neighbours(0, 8, 2)), [1, 2])
        self.assertEqual(sorted(check.neighbours(4, 8, 2)), [2, 5, 6])
        self.assertEqual(check.adjacency_violations(['A', '+12V', '+5V', 'AGND', 'B', 'AGND', '-12V', 'NC'], 2), ['A'])
        self.assertEqual(check.adjacency_violations(['A', '+12V', '+5V', 'AGND', 'B', 'AGND', '-12V', 'NC'], 1), ['A'])
        self.assertEqual(check.adjacency_violations(['A', 'AGND', '+5V', 'B'], 2), [])
        self.assertEqual(check.adjacency_violations(['A', '+5V', 'B', 'AGND'], 2), ['A'])

    def test_el_pair_must_be_clear(self):
        ctx = copy.copy(CTX)
        ctx.obstacles = dict(CTX.obstacles)
        ctx.obstacles['EL'] = copy.deepcopy(CTX.obstacles['EL'])
        ctx.obstacles['EL']._add('B', [221.0, 170.0, 223.0, 171.0], 'TEST1', 'courtyard')
        self.assertFault(DOC, r'pair EL-P-E1 front 2x4 envelope .* on EL B.Cu overlaps TEST1 \(courtyard\) by 1.26 mm \(must be clear\)', ctx)

    def test_pot_passage_growth_is_screened(self):
        res = check_one(check.check_el_pot_passages, DOC)
        self.assertEqual(res.errors, [])
        rows = res.checks['el_pot_passages']['detail']['passages']
        self.assertEqual(len(rows), 18)
        self.assertEqual({r['diameter_mm'] for r in rows}, {6.8})
        doc = copy.deepcopy(DOC)
        doc['candidate']['el_pot_passages'][0]['diameter_mm'] = 8.0
        self.assertTrue(any(re.search(r'pot passage C:E1.RISE at \[218.5, 241.0\] \(d 8.0 mm\) overlaps EL', e)
                            for e in check_one(check.check_el_pot_passages, doc).errors))

    def test_fixing_reach_runs(self):
        res = check_one(check.check_fixing_reach, DOC)
        self.assertEqual(res.errors, [])
        runs = res.checks['fixing_reach']['detail']['runs']
        self.assertEqual(runs['without_tie_sites']['misses'], 27)
        self.assertEqual(runs['without_tie_sites']['by_front_board'], {'JL': 3, 'JR': 7, 'P': 17})
        self.assertEqual(runs['with_tie_sites']['misses'], 0)
        self.assertEqual(runs['posts_and_kept_supports_only']['fixings'], 30)
        kinds = {}
        for f in DOC['candidate']['fixings']:
            kinds[f['kind']] = kinds.get(f['kind'], 0) + 1
        self.assertEqual(kinds, {'post': 18, 'kept support': 12, 'interior candidate': 66, 'tie site': 5})
        ties = [f['xy'] for f in DOC['candidate']['fixings'] if f['kind'] == 'tie site']
        self.assertEqual(ties, [[202, 255], [252, 241], [227, 80], [227, 38], [108, 80]])
        doc = copy.deepcopy(DOC)
        doc['candidate']['fixings'] = [f for f in doc['candidate']['fixings'] if f['id'] != 'TIE-D4-2']
        self.assertTrue(any(re.search(r'pair \S+ at .* is [\d.]+ mm from the nearest fixing', e)
                            for e in check_one(check.check_fixing_reach, doc).errors))

    def test_adapter_standoff_search_finds_sites_when_room_exists(self):
        res = check_one(check.check_adapter_standoffs, DOC)
        self.assertEqual(len(res.errors), 3)
        ctx = copy.copy(CTX)
        ctx.obstacles = dict(CTX.obstacles)
        empty = sg.Obstacles([], CTX.params['obstacle_model'])
        for key in ('K', 'O1', 'O3', 'O5'):
            ctx.obstacles[key] = empty
        ctx.params = dict(CTX.params, adapter_standoffs=dict(CTX.params['adapter_standoffs'], diagnostic_keepouts_mm=[],
                                                              search_step_mm=0.5))
        res = check_one(check.check_adapter_standoffs, DOC, ctx)
        self.assertEqual(res.errors, [])
        self.assertTrue(all(a['regions'] for a in res.checks['adapter_standoff_candidates']['detail']['adapters'].values()))

    def test_sub_windows_at_the_stacker_courtyard(self):
        w = {s['block']: s['window_mm'] for s in DOC['candidate']['sub_toggles']}
        self.assertEqual(w, {'O2': 0.5, 'O4': 1.6})


if __name__ == '__main__':
    unittest.main()
