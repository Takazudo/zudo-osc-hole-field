"""Tests of the threading procedure (ST-08 part 2): a fresh run equals the retained files, every link of the record
has one row, the counts equal the record's summary, and the checker and the verdict fail on planted faults."""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import procedure as pr  # noqa: E402
import procedure_page  # noqa: E402


def setUpModule():
    global DOC, INP
    DOC, INP = pr.generate()


def rules(errs):
    return sorted({e[0] for e in errs})


def regenerate_with(mutate):
    inp = copy.deepcopy(INP)
    mutate(inp)
    rows = pr.link_rows(inp)
    return pr.lowering(rows, inp['sites'])


class Staleness(unittest.TestCase):
    def test_json_equals_the_retained_file(self):
        self.assertEqual(pr.render_json(DOC), pr.PROC_JSON.read_text(), 'stale; regenerate with: ' + pr.REGEN)

    def test_page_equals_the_retained_file(self):
        self.assertEqual(procedure_page.render(DOC), pr.PROC_MD.read_text(), 'stale; regenerate with: ' + pr.REGEN)

    def test_record_is_pinned_by_projection_not_by_file_hash(self):
        pins = DOC['provenance']['pins']
        self.assertNotIn(pr.GATE, pins['files_sha256'])
        self.assertEqual(pins['gate_record_projection']['digest'], pr.digest(INP['gate']))


class Record(unittest.TestCase):
    def test_clean_record_has_no_finding_and_is_done(self):
        self.assertEqual(pr.check(DOC, INP), [])
        self.assertEqual(DOC['verdict'], 'DONE')

    def test_one_row_per_link_in_use(self):
        ids = [r['id'] for r in DOC['links']]
        self.assertEqual(len(ids), 61)
        self.assertEqual(ids, [l['id'] for l in INP['gate']['links']])

    def test_counts_in_bench_units(self):
        c = DOC['counts']
        self.assertEqual(c['cables_per_code'], {'C26618 50 mm': 18, 'C29534 50 mm': 28, 'C32128 60 mm': 3,
                                                'C68390 50 mm': 9, 'C81339 40 mm': 3})
        self.assertEqual(c['parts_with_leads_to_cut_per_board'], {'JL': 19, 'JR': 14, 'P': 49, 'O3': 1})
        self.assertEqual((c['connectors'], c['locks_before_K'], c['locks_after_K']), (122, 61, 61))
        self.assertEqual((c['lengthened_tails'], c['holding_hand'], c['fastener_operations']), (30, 12, 44))

    def test_smallest_slack_and_stages(self):
        self.assertAlmostEqual(min(r['slack_mm'] for r in DOC['links']), 0.6602)
        low = DOC['lowering']
        self.assertEqual(sum(s['ends'] for s in low['stages']), 61)
        self.assertEqual(low['largest_ends'], max(s['ends'] for s in low['stages']))
        heights = [s['meets_K_at_mm'] for s in low['stages']]
        self.assertEqual(heights, sorted(heights, reverse=True))
        self.assertTrue(all(h > t['meets_K_at_mm'] for h in heights for t in low['screw_tips']))

    def test_meeting_height_follows_the_record_length_rule(self):
        # stand height less (gap + K thickness) = insertion + b + slack + R (pi/2 - 2)
        for r in DOC['links']:
            want = 4.0 + r['on_K_rear_mm'] + r['slack_mm'] + 2.4 * (3.141592653589793 / 2 - 2)
            self.assertAlmostEqual(r['through_K_when_seated_mm'], want, places=2, msg=r['id'])

    def test_holding_hand_names_the_twelve_of_the_record(self):
        self.assertEqual(sorted(h['link'] for h in DOC['holding_hand']),
                         sorted(INP['gate']['summary']['compliance']['links_above_list']))
        self.assertTrue(all(h['K_connector']['name'].startswith('the ') for h in DOC['holding_hand']))

    def test_latch_counts_and_the_31(self):
        self.assertEqual(DOC['latch']['counts'], {'NOT SHOWN': 31, 'open': 27, 'open after the displacement': 3})
        self.assertEqual(len(DOC['latch']['not_shown']), 31)
        self.assertTrue(all(n['neighbours'] for n in DOC['latch']['not_shown']))

    def test_service_counts(self):
        sv = DOC['service']
        self.assertEqual(sv['per_opening'], 2 * (61 + 61 + 18 + 4))
        self.assertLessEqual(sv['K_end_insertions_after_limit'], sv['insertions_sourced'])

    def test_verified_nut_height_does_not_resolve_washer_or_erase_history(self):
        s = DOC['screws']
        self.assertEqual(s['nut_height_mm'], {'nominal':2.4,'tolerance':.25,'interval':[2.15,2.65],
                                             'unit':'mm','status':'PRIMARY_DIMENSION_VERIFIED'})
        self.assertEqual(s['washer_thickness_mm'],'UNSOURCED')
        self.assertIn('nut height',s['sheet']['missing'])
        self.assertEqual(s['sheet'],pr.STORE_SHEET)
        self.assertLessEqual(len(s['sources_tried']), 2)

    def test_nut_source_identity_and_remaining_assembly_gaps(self):
        source=DOC['screws']['nut_height_source']
        self.assertEqual(source['verified_pdf_sha256'],'b31545f168c90a3bc2d44f06b0f0a3003a6aaeef002b4366e11a44230637af44')
        self.assertEqual(source['verified_pdf_bytes'],172371)
        self.assertEqual(source['drawing_date'],'2011-05-26')
        self.assertIsNone(source['revision'])
        self.assertEqual(source['finish_disposition'],'UNRESOLVED_VERSION_DISCREPANCY')
        self.assertIn('screw length tolerance',source['remaining_unknowns'])
        self.assertIn('grip tolerance',source['remaining_unknowns'])
        self.assertEqual(DOC['screws']['working_figure']['status'],'ASSUMED')
        self.assertEqual(DOC['counts']['latch']['NOT SHOWN'],31)
        page=procedure_page.render(DOC)
        self.assertIn('2.4 +/- 0.25 mm (interval 2.15 to 2.65 mm)',page)
        self.assertIn('washer thickness stays UNSOURCED',page)
        self.assertNotIn('Nut height and washer thickness: UNSOURCED',page)
        self.assertIn('Nut drawing height: PRIMARY_DIMENSION_VERIFIED; washer thickness: UNSOURCED',page)
        self.assertIn('no current-lot finish, hardware adoption or assembly acceptance',page)


class PageReadsData(unittest.TestCase):
    @staticmethod
    def bend_figure(page):
        m = re.search(r'plus ([0-9.]+) mm from the bend', page)
        return float(m.group(1))

    def test_bend_term_of_the_page_is_the_term_of_stand_height(self):
        R = INP['gate']['parameters']['bend_radius_mm']
        self.assertAlmostEqual(self.bend_figure(pr.PROC_MD.read_text()), pr.bend_term(R), places=4)
        l = INP['gate']['links'][0]
        p = INP['gate']['parameters']
        self.assertAlmostEqual(pr.stand_height(l, p, INP['opts']) - (l['cable_length_mm'] - p['insertion_mm']
                                                                      - l['geometry']['a_mm']), pr.bend_term(R))

    def test_changed_bend_radius_changes_sentence_and_stages_together(self):
        inp = copy.deepcopy(INP)
        inp['gate']['parameters']['bend_radius_mm'] = 3.0
        doc = pr.build(inp)
        page = procedure_page.render(doc)
        self.assertIn('bend radius 3 mm', page)
        self.assertAlmostEqual(self.bend_figure(page), pr.bend_term(3.0), places=4)
        shift = pr.bend_term(3.0) - pr.bend_term(2.4)
        old = [s['meets_K_at_mm'] for s in DOC['lowering']['stages']]
        new = [s['meets_K_at_mm'] for s in doc['lowering']['stages']]
        self.assertEqual(len(old), len(new))
        for o, n in zip(old, new):
            self.assertAlmostEqual(n - o, shift, places=2)

    def test_slot_and_insertion_figures_follow_the_inputs(self):
        inp = copy.deepcopy(INP)
        inp['opts']['slot_length_mm'] = 1.7
        inp['opts']['tail_step_mm'] = 3.0
        inp['gate']['parameters']['insertion_mm'] = 3.5
        inp['gate']['parameters']['latch_margin_mm'] = 1.2
        page = procedure_page.render(pr.build(inp))
        for text in ('the 1.7 mm slot', 'steps of 3 mm', 'less the 3.5 mm insertion', 'by the 3.5 mm insertion',
                     'Neighbours within 1.2 mm', 'a 1.7 mm slot'):
            self.assertIn(text, page)


class Faults(unittest.TestCase):
    def test_link_without_a_row(self):
        doc = copy.deepcopy(DOC)
        doc['links'].pop(5)
        self.assertIn('row', rules(pr.check(doc, INP)))

    def test_count_that_differs_from_the_record(self):
        doc = copy.deepcopy(DOC)
        doc['counts']['locks'] = 120
        self.assertIn('count', rules(pr.check(doc, INP)))
        doc = copy.deepcopy(DOC)
        doc['counts']['latch']['open'] = 28
        self.assertIn('count', rules(pr.check(doc, INP)))

    def test_stale_projection(self):
        inp = copy.deepcopy(INP)
        inp['gate']['links'][0]['loop_mm'] = 1.0
        self.assertIn('stale', rules(pr.check(DOC, inp)))

    def test_slot_covered_by_another_front_connector_returns_needs_design(self):
        def plant(inp):
            a, b = inp['gate']['links'][0], inp['gate']['links'][1]
            b['geometry']['front_connector'] = list(a['geometry']['slot'])
        low = regenerate_with(plant)
        self.assertTrue(low['blocked'])
        self.assertIn('front connector of', ' '.join(low['blocked'][0]['by']))

    def test_end_blocked_by_a_post(self):
        def plant(inp):
            l = inp['gate']['links'][0]
            inp['gate']['fixings'][0]['front'] = pr.centre(l['geometry']['slot'])
        low = regenerate_with(plant)
        self.assertIn('fixing', ' '.join(b for x in low['blocked'] for b in x['by']))

    def test_short_cable_returns_needs_design_on_the_page(self):
        def plant(inp):
            inp['gate']['links'][0]['loop_mm'] = -0.5
        low = regenerate_with(plant)
        self.assertEqual(low['short_cables'], [{'link': INP['gate']['links'][0]['id'], 'slack_mm': -0.5}])
        doc = copy.deepcopy(DOC)
        doc['lowering'] = low
        doc['verdict'] = 'NEEDS_DESIGN' if (low['blocked'] or low['short_cables']) else 'DONE'
        self.assertIn('## NEEDS_DESIGN', procedure_page.render(doc))


class PrimaryActuationMethod(unittest.TestCase):
    def test_both_phases_require_central_hand_only_operation(self):
        steps = {step['n']: step for step in DOC['steps']}
        for number in (7, 12):
            text = steps[number]['do']
            self.assertIn('by hand only at the center of the actuator', text)
            self.assertIn('Do not insert tools or fingernails into the connector', text)
            self.assertNotIn('or a plastic tool', text)
            self.assertEqual(steps[number]['parts'], 61)
        self.assertIn('before K comes down', steps[7]['do'])
        self.assertIn('never press K with the palm (DS-66)', steps[12]['do'])
        self.assertIn('At the 12 connectors', steps[12]['do'])
        self.assertIn('other hand holds K', steps[12]['do'])
        page = procedure_page.render(DOC)
        self.assertNotIn('or a plastic tool', page)
        # Two assembly table rows and the separate K-side instruction paragraph.
        self.assertEqual(page.count('by hand only at the center of the actuator'), 3)

    def test_method_correction_is_not_access_acceptance(self):
        self.assertEqual(DOC['counts']['latch']['NOT SHOWN'], 31)
        self.assertEqual(DOC['counts']['holding_hand'], 12)
        self.assertEqual(DOC['lowering']['largest_ends'], 17)
        self.assertEqual(len(DOC['lowering']['stages']), 9)
        self.assertEqual(DOC['counts']['links'], 61)
        self.assertEqual(DOC['counts']['connectors'], 122)


if __name__ == '__main__':
    unittest.main()
