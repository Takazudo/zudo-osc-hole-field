"""Tests of the flat-link option study (ST-02 a4): staleness, counts, capacity, forbidden items, fault injection.

No network and no KiCad: the boards are parsed with plain Python.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import links  # noqa: E402


def setUpModule():
    global INP, OUT, SITES, MODEL, DOC, SMALL
    INP = links.load_inputs()
    OUT, _ = links.generate(with_p_small=False)
    SITES = links.link_sites(INP['cand'])
    MODEL = links.Model(INP, SITES)
    DOC = json.loads(links.LINK_CANDIDATE.read_text())
    SMALL = json.loads(links.LINK_P_SMALL.read_text())


def first_placed(doc, option='P100-N20 G-PER-2S'):
    return next(l for l in doc['options'][option]['links'] if l['placed'])


def move(rect, cx, cy):
    w, h = rect[2] - rect[0], rect[3] - rect[1]
    return [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]


class RetainedFiles(unittest.TestCase):
    def test_retained_files_equal_a_fresh_generation(self):
        self.assertEqual(links.render(OUT), links.LINK_CANDIDATE.read_text(),
                         'link-candidate.json is stale; regenerate with: ' + links.REGEN)
        self.assertEqual(links.readme(OUT, SMALL), links.LINK_README.read_text(),
                         'links/README.md is stale; regenerate with: ' + links.REGEN)

    def test_p_small_best_option_equals_a_fresh_generation(self):
        # the P-joint addition takes about 35 s in full; its best option is regenerated here, the rest by links.py
        self.assertEqual(SMALL['provenance'], DOC['provenance'])
        best = next(s for s in SMALL['summary'] if s['option'] == SMALL['best'])
        size = next(z for z in INP['opts']['p_small']['sizes'] if z['id'] == best['size'])
        s, d = links.p_small_option(MODEL, SITES, INP['opts'], INP['cand'], links.post_keepout_k(INP['root']),
                                    DOC['rigid_return_criterion']['total'], size, best['ground_rule'])
        self.assertEqual(json.dumps(s, sort_keys=True), json.dumps(best, sort_keys=True),
                         'link-candidate-p-small.json is stale; regenerate with: ' + links.REGEN)
        self.assertEqual(json.dumps(d, sort_keys=True), json.dumps(SMALL['options'][best['option']], sort_keys=True))

    def test_p_small_counts_and_checker(self):
        self.assertEqual(len(SMALL['summary']), 2 * len(INP['opts']['p_small']['sizes']))
        self.assertEqual(len(SMALL['combined']['summary']), len(INP['opts']['p_small']['combine_jl_jr_with']))
        doc = {'summary': SMALL['summary'] + SMALL['combined']['summary'],
               'options': dict(SMALL['options'], **SMALL['combined']['options'])}
        self.assertEqual(links.check(doc, MODEL, INP['opts'], SITES), [])

    def test_retained_candidate_passes_the_checker(self):
        self.assertEqual(links.check(DOC, MODEL, INP['opts'], SITES), [])


class Counts(unittest.TestCase):
    def test_item_1_counts(self):
        c = DOC['site_counts']
        self.assertEqual((c['pairs'], c['positions']), (191, 747))
        fam = {k: (v['pairs'], v['positions'], v['signals']) for k, v in c['by_family'].items()}
        self.assertEqual(fam, {'K/P': (123, 369, 246), 'JR/K': (27, 162, 106), 'JL/K': (25, 150, 100),
                               'JL/P pass-through': (8, 24, 16), 'P/K for EL': (6, 36, 18), 'SUB': (2, 6, 4)})

    def test_capacity_rules(self):
        self.assertEqual([links.capacity(n, 'G-PER-2S') for n in (20, 22, 30, 40)], [13, 14, 20, 26])
        self.assertEqual([links.capacity(n, 'G-BETWEEN') for n in (20, 22, 30, 40)], [10, 11, 15, 20])

    def test_every_option_and_rule_is_present(self):
        self.assertEqual(len(DOC['summary']), 12)

    def test_input_hashes_cover_the_report_and_the_renderer(self):
        h = DOC['provenance']['input_sha256']
        self.assertIn('design/stack/geometry/check-report.json', h)
        self.assertIn('scripts/stack/geometry/links_readme.py', h)


class FaultInjection(unittest.TestCase):
    def errors(self, doc, opts=None):
        return links.check(doc, MODEL, opts or INP['opts'], SITES)

    def test_overfull_link_fails(self):
        doc = copy.deepcopy(DOC)
        ls = doc['options']['P100-N20 G-PER-2S']['links']
        a, b = ls[0], ls[1]
        a['members'] += b['members']
        b['members'] = []
        a['signals'] += b['signals']
        errs = self.errors(doc)
        self.assertTrue(any('overfull' in e and a['id'] in e for e in errs), errs)

    def test_slot_in_a_fixing_keepout_fails(self):
        doc = copy.deepcopy(DOC)
        link = first_placed(doc)
        post = INP['cand']['posts'][0]
        x, y = post['proposed_K_land']
        link['geometry']['slot'] = move(link['geometry']['slot'], x + 3.0, y)
        errs = self.errors(doc)
        self.assertTrue(any(link['id'] in e and 'slot web on fixing keep-out ' + post['id'] in e for e in errs), errs)

    def test_field_on_panel_hardware_fails(self):
        doc = copy.deepcopy(DOC)
        link = next(l for l in doc['options']['P100-N20 G-PER-2S']['links'] if l['placed'] and l['front_board'] == 'JL')
        for jack in INP['ci']['boards']['JL']:
            if jack['ref'] in MODEL.panel['JL'] and jack['ref'].startswith('J'):
                pad = jack['pads'][0]['center']
                rect = move(link['geometry']['front_connector'], pad[0], pad[1])
                if links.sg.rect_inside_poly(rect, MODEL.outline['JL'], MODEL.margin):
                    break
        link['geometry']['front_connector'] = rect
        errs = self.errors(doc)
        self.assertTrue(any(link['id'] in e and 'front field on panel hardware' in e for e in errs), errs)

    def test_cable_too_short_fails(self):
        opts = copy.deepcopy(INP['opts'])
        opts['cable']['length_mm']['value'] = 35.0
        errs = self.errors(DOC, opts)
        self.assertTrue(errs and all('cable too short' in e for e in errs), errs[:3])

    def shifted(self, doc, link, dx, dy, keys=('slot', 'front_connector', 'front_tail', 'K_tail', 'K_connector')):
        for k in keys:
            r = link['geometry'][k]
            link['geometry'][k] = [r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy]

    def test_K_field_outside_K_fails(self):
        doc = copy.deepcopy(DOC)
        link = first_placed(doc)
        link['geometry']['K_connector'] = move(link['geometry']['K_connector'], -20.0, 100.0)
        errs = self.errors(doc)
        self.assertTrue(any(link['id'] in e and 'K field outside the K outline' in e for e in errs), errs)

    def test_overlap_between_links_fails(self):
        doc = copy.deepcopy(DOC)
        ls = [l for l in doc['options']['P100-N20 G-PER-2S']['links'] if l['placed']]
        a, b = ls[0], ls[1]
        b['geometry'] = copy.deepcopy(a['geometry'])
        errs = self.errors(doc)
        self.assertTrue(any(b['id'] in e and ('of ' + a['id']) in e for e in errs), errs)

    def test_slot_under_an_adapter_fails(self):
        doc = copy.deepcopy(DOC)
        link = first_placed(doc)
        sel = INP['cand']['selectors_kept'][0]['courtyard']
        link['geometry']['slot'] = move(link['geometry']['slot'], (sel[0] + sel[2]) / 2, (sel[1] + sel[3]) / 2)
        errs = self.errors(doc)
        self.assertTrue(any(link['id'] in e and ('under adapter' in e or 'under kept selector' in e or 'slot web on' in e)
                            for e in errs), errs)

    def test_tail_on_a_fixing_keepout_fails(self):
        doc = copy.deepcopy(DOC)
        link = next(l for l in doc['options']['P100-N20 G-PER-2S']['links'] if l['placed'] and l['front_board'] == 'JL')
        post = next(p for p in INP['cand']['posts'] if p['front_board'] == 'JL')
        x, y = post['proposed_front_land']
        link['geometry']['front_tail'] = move(link['geometry']['front_tail'], x, y)
        errs = self.errors(doc)
        self.assertTrue(any(link['id'] in e and 'front tail on fixing keep-out ' + post['id'] in e for e in errs), errs)

    def test_tail_over_panel_pins_is_listed_not_screened(self):
        jack = next(f for f in INP['ci']['boards']['JL'] if f['ref'] in MODEL.panel['JL'] and f['ref'].startswith('J'))
        pad = jack['pads'][0]['bbox']
        self.assertIsNotNone(MODEL.forbidden('JL', 'B', pad))
        hit = MODEL.forbidden('JL', 'B', pad, tail=True)
        self.assertTrue(hit is None or not hit[0].startswith('panel hardware'), hit)

    def test_staleness_detected(self):
        doc = copy.deepcopy(OUT)
        doc['summary'][0]['links'] += 1
        self.assertNotEqual(links.render(doc), links.LINK_CANDIDATE.read_text())


if __name__ == '__main__':
    unittest.main()
