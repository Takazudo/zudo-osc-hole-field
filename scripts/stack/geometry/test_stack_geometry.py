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
    def test_checker_passes_on_committed_candidate(self):
        res = check.run_checks(DOC, CTX)
        self.assertEqual(res.errors, [])

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
        self.assertEqual((t['pairs'], t['positions'], t['K_pairs'], t['K_positions']), (203, 813, 197, 777))
        self.assertEqual((t['signal_positions'], t['AGND'], t['rail'], t['unused']), (531, 270, 12, 2))


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
        ci['land_pattern']['explicit_mm']['K']['3'] = [6.5, 7.0]
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
        self.assertFault(doc, r'tab TAB-EL .* overlaps the seam cross-member 2 carrier envelope')

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
        self.assertFault(doc, r'SUB pair at O2 centre \[31.5, 181.5\] is outside the placement window y=180.15..180.85')

    def test_control_tab_ending_at_178(self):
        doc = copy.deepcopy(DOC)
        tab(doc, 'TAB-CONTROL-O2')['rect'][1] = 178.0
        self.assertFault(doc, r'SUB pair O2 envelope .* is not inside control tab')

    def test_stale_k_plane(self):
        doc = copy.deepcopy(DOC)
        doc['candidate']['stack']['K_face_z_mm'] = -22.0
        self.assertFault(doc, r'stale K_face_z_mm -22.0, sources give -24.5')

    def test_stale_pair_height(self):
        doc = copy.deepcopy(DOC)
        pair(doc, 'K-O1-1')['mated_height_mm'] = 6.2
        self.assertFault(doc, r'pair K-O1-1 mated height 6.2 differs from gap O1/K 6.9')

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
        ci['land_pattern']['explicit_mm']['K']['3'] = [6.5, 7.0]
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


if __name__ == '__main__':
    unittest.main()
