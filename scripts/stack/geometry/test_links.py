"""Tests of the flat-link option study (ST-02 a4 to a6): staleness, counts, capacity, forbidden items, fault injection.

No network and no KiCad: the boards are parsed with plain Python.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import links  # noqa: E402
import links_gate  # noqa: E402


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
        self.assertEqual(links.check(doc, MODEL, INP['opts'], SITES, INP['cand']), [])

    def test_retained_candidate_passes_the_checker(self):
        self.assertEqual(links.check(DOC, MODEL, INP['opts'], SITES, INP['cand']), [])


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

    def test_field_scan_reports_signals_carried(self):
        fs = SMALL['field_scan']
        for r in fs['links']:
            n = r['largest_circuits_placed']
            self.assertEqual(r['signals_carried'], links.capacity(n, fs['ground_rule']) if n else 0)
            self.assertEqual(r['own_signals_fit'], r['signals_carried'] >= r['signals'])
        self.assertEqual(fs['links_whose_signals_fit'], sum(r['own_signals_fit'] for r in fs['links']))

    def test_input_hashes_cover_the_report_and_the_renderer(self):
        h = DOC['provenance']['input_sha256']
        self.assertIn('design/stack/geometry/check-report.json', h)
        self.assertIn('scripts/stack/geometry/links_readme.py', h)


FOCUS = 'P100-N20 G-PER-2S'


def one_option(doc, option=FOCUS):
    """A candidate restricted to one option, so a fault test checks only what it changed."""
    return {'summary': [s for s in doc['summary'] if s['option'] == option],
            'options': {option: doc['options'][option]}}


def size_of(sid):
    return next(z for z in INP['opts']['sizes'] + INP['opts']['p_small']['sizes'] if z['id'] == sid)


def relocate(doc, expected, option=FOCUS, radius=30.0, step=2.0, front=None, model=None, target=None):
    """Move one placed link (slot centre and direction; geometry rebuilt) to the nearest place, around its own slot
    centre or around `target`, where the search's own evaluate rejects it with a reason containing `expected`.
    Returns the moved link, or None if none was found."""
    model = model or MODEL
    ls = [l for l in doc['options'][option]['links'] if l['placed']]
    if target:
        # around a fixed target the other links are left out, so only the screen under test can reject
        keep = next(l for l in ls if not front or l['front_board'] == front)
        for o in ls:
            o['placed'] = o is keep
        ls = [keep]
    n = int(radius / step)
    offs = sorted(((i * step, j * step) for i in range(-n, n + 1) for j in range(-n, n + 1)), key=lambda o: abs(o[0]) + abs(o[1]))
    web = links.val(INP['opts']['slot']['web_mm'])
    for l in ls:
        if front and l['front_board'] != front:
            continue
        others = links.Placed()
        for o in ls:
            if o is not l:
                links.add_placed(others, o['front_board'], o['geometry'], o['id'])
        size = size_of(l['size'])
        for dx, dy in offs:
            cx, cy = target or l['slot_centre']
            sx, sy = cx + dx, cy + dy
            for d, name in links.DIR_NAMES.items():
                geo = links.link_geometry(sx, sy, d, size, INP['opts'])
                why, _ = links.evaluate(model, others, l['front_board'], geo, web)
                if why and expected in why[0]:
                    l.update({'slot_centre': [sx, sy], 'direction': name, 'geometry': geo})
                    return l
    return None


def model_without(drop=(), between_label=None):
    """A copy of the model without some forbidden items ((label prefix, board key) pairs, both faces) or between
    items, to reach a screen that an earlier screen shadows in the present geometry."""
    m = copy.copy(MODEL)
    m.forb = dict(MODEL.forb)
    for label, key in drop:
        for face in 'FB':
            idx = links.sg.RectIndex()
            for rect, payload in m.forb[(key, face)].items:
                if not payload[2].startswith(label):
                    idx.add(rect, payload)
            m.forb[(key, face)] = idx
    if between_label:
        m.between = [b for b in MODEL.between if between_label not in b[1]]
    return m


class FaultInjection(unittest.TestCase):
    def errors(self, doc, opts=None, model=None):
        return links.check(doc, model or MODEL, opts or INP['opts'], SITES, INP['cand'])

    def rejected(self, expected, front=None, model=None, target=None, radius=30.0, step=2.0):
        doc = one_option(copy.deepcopy(DOC))
        link = relocate(doc, expected, front=front, model=model, target=target, radius=radius, step=step)
        self.assertIsNotNone(link, 'no place found that triggers: ' + expected)
        errs = self.errors(doc, model=model)
        self.assertTrue(any(link['id'] in e and expected in e for e in errs), errs)
        return errs

    def test_overfull_link_fails(self):
        doc = one_option(copy.deepcopy(DOC))
        ls = doc['options'][FOCUS]['links']
        a, b = ls[0], ls[1]
        a['members'] += b['members']
        b['members'] = []
        a['signals'] += b['signals']
        errs = self.errors(doc)
        self.assertTrue(any('overfull' in e and a['id'] in e for e in errs), errs)

    def test_slot_web_on_a_fixing_keepout_fails(self):
        self.rejected('slot web on fixing keep-out')

    def test_front_field_on_panel_hardware_fails(self):
        self.rejected('front field on panel hardware', front='JL')

    def test_K_field_outside_K_fails(self):
        self.rejected('K field outside the K outline')

    def test_front_tail_on_a_fixing_keepout_fails(self):
        # shadowed in the present geometry: a front land shares its xy with the K land (slot web screen) and stands
        # 4 mm from the JL edge between jack rows (front field screen); both are taken out of a copy of the model
        post = next(p for p in INP['cand']['posts'] if p['front_board'] == 'JL')
        model = model_without(drop=(('fixing keep-out', 'K'), ('panel hardware', 'JL')))
        self.rejected('front tail on fixing keep-out', front='JL', target=post['proposed_front_land'], radius=8.0,
                      model=model)

    def test_every_kept_selector_lies_inside_an_adapter_screen(self):
        # so the adapter screen, checked first, always reports; the selector screen is reached in the test below
        for s in INP['cand']['selectors_kept']:
            c = s['courtyard']
            self.assertTrue(any(r[0] <= c[0] and r[1] <= c[1] and r[2] >= c[2] and r[3] >= c[3]
                                for r, lab in MODEL.between if lab.startswith('adapter')), s['ref'])

    def test_under_an_adapter_fails(self):
        self.rejected('under adapter')

    def test_under_a_kept_selector_fails(self):
        sel = INP['cand']['selectors_kept'][1]['courtyard']
        self.rejected('under kept selector', front='P', model=model_without(between_label='adapter'),
                      target=[(sel[0] + sel[2]) / 2, (sel[1] + sel[3]) / 2], radius=16.0, step=1.0)

    def test_front_field_on_another_links_slot_fails(self):
        errs = self.rejected('front field on slot of')
        self.assertTrue(any('(front board' in e for e in errs), errs)

    def test_slot_not_under_its_own_front_board_fails(self):
        self.rejected('not under its own front board')

    def test_overlap_between_links_fails(self):
        doc = one_option(copy.deepcopy(DOC))
        ls = [l for l in doc['options'][FOCUS]['links'] if l['placed']]
        a, b = ls[0], ls[1]
        for k in ('slot_centre', 'direction', 'geometry', 'front_board'):
            b[k] = copy.deepcopy(a[k])
        errs = self.errors(doc)
        self.assertTrue(any(b['id'] in e and ('of ' + a['id']) in e for e in errs), errs)

    def test_moved_K_connector_fails(self):
        doc = one_option(copy.deepcopy(DOC))
        link = first_placed(doc)
        r = link['geometry']['K_connector']
        link['geometry']['K_connector'] = [r[0] + 5.0, r[1], r[2] + 5.0, r[3]]
        errs = self.errors(doc)
        self.assertTrue(any(link['id'] in e and 'recorded K_connector' in e for e in errs), errs)

    def test_edited_cable_length_fails(self):
        doc = one_option(copy.deepcopy(DOC))
        link = first_placed(doc)
        link['cable_needed_mm'] -= 5.0
        errs = self.errors(doc)
        self.assertTrue(any(link['id'] in e and 'recorded cable length' in e for e in errs), errs)

    def test_emptied_displaced_list_fails(self):
        doc = one_option(copy.deepcopy(DOC))
        link = next(l for l in doc['options'][FOCUS]['links'] if l['placed'] and l['displaced']['K B (field)'])
        link['displaced']['K B (field)'] = []
        errs = self.errors(doc)
        self.assertTrue(any(link['id'] in e and 'displaced lists differ' in e for e in errs), errs)

    def test_cable_too_short_fails(self):
        opts = copy.deepcopy(INP['opts'])
        opts['cable']['length_mm']['value'] = 35.0
        errs = self.errors(one_option(DOC), opts)
        self.assertTrue(errs and all('cable too short' in e for e in errs), errs[:3])

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


def setUpGate():
    global GINP, GSITES, GDOC, GFRESH
    if 'GDOC' in globals():
        return
    GINP = links_gate.load_inputs()
    GSITES = links_gate.gate_sites(GINP)
    GDOC = json.loads(links_gate.LINK_GATE.read_text())
    # the comparison runs (field_change, causes, sensitivity) are regenerated by links_gate.py only
    GFRESH = links_gate.generate(causes=False)


def gate_doc():
    return copy.deepcopy({'links': GDOC['links']})


class Gate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setUpGate()

    def test_gate_file_equals_a_fresh_generation(self):
        kept = {k: v for k, v in GDOC.items() if k not in ('field_change', 'causes', 'sensitivity')}
        self.assertEqual(links_gate.render(GFRESH), links_gate.render(kept),
                         'link-gate.json is stale; regenerate with: ' + links_gate.REGEN)
        self.assertEqual(links_gate.readme(GDOC), links_gate.LINK_GATE_README.read_text())

    def test_refined_places_pass_the_checker(self):
        refined = [r for r in GDOC['links'] if (r.get('refinement') or {}).get('found')]
        self.assertTrue(refined)
        for r in refined:
            self.assertLess(r['grid_mm'], links.val(GINP['opts']['search']['step_mm']))
        errs = links_gate.check(GDOC, GINP, GSITES)
        self.assertEqual([e for e in errs if any(e.startswith(r['id'] + ':') for r in refined)], [])

    def test_improvement_moves_stay_within_the_allowance(self):
        allow = links.val(GINP['gopts']['refinement']['improvement']['allowance'])
        for r in GDOC['links']:
            m = r.get('moved_by_improvement')
            if m:
                self.assertLessEqual(m['new_cost'], m['cost'] + allow + 1e-9, r['id'])
                self.assertEqual(r['cost'], m['new_cost'])

    def test_gate_passes_the_checker(self):
        self.assertEqual(links_gate.check(GDOC, GINP, GSITES), [])

    def test_classes_equal_the_link_electrical_list(self):
        res = json.loads((links.sg.ROOT / 'design/stack/link-electrical/results.json').read_text())['signals']
        mine = {(s['id'], n): c for s in GSITES if s['joint'] != 'O-K' for n, c in zip(s['signals'], s['classes'])}
        self.assertEqual(len(res), 490)
        self.assertEqual(mine, {(r['pair'], r['net']): r['class'] for r in res})

    def test_511_signals_each_on_one_link(self):
        self.assertEqual(GDOC['signals']['total'], 511)
        seen = [(p['site'], p['net']) for r in GDOC['links'] for p in r['positions'] if p['kind'] == 'signal']
        self.assertEqual(len(seen), 511)
        self.assertEqual(len(set(seen)), 511)

    def test_circuits_needed_under_ds62(self):
        f = links_gate.circuits_needed
        self.assertEqual(f(['ANALOGUE'] * 7), 13)
        self.assertEqual(f(['WIPER'] * 7), 8)
        self.assertEqual(f(['LOGIC'] * 3 + ['ANALOGUE']), 5)
        self.assertIsNone(f(['LOGIC', 'WIPER']))
        self.assertEqual(f(['PRECISION']), 2)

    def test_fixings_come_from_one_function(self):
        self.assertEqual(GDOC['fixings']['count'], len(links_gate.fixing_sites(GINP)))
        self.assertEqual(GDOC['fixings']['count'], 30)

    def gerrs(self, doc):
        return links_gate.check(doc, GINP, GSITES)

    def test_two_analogue_signals_side_by_side_fail(self):
        doc = gate_doc()
        r = next(l for l in doc['links'] if l['joint'] == 'JL-K')
        pos = r['positions']
        i = next(k for k in range(len(pos) - 2) if pos[k]['kind'] == 'signal' and pos[k + 1]['kind'] == 'ground'
                 and pos[k + 2]['kind'] == 'signal')
        pos[i + 1], pos[i + 2] = dict(pos[i + 2], pos=i + 2), dict(pos[i + 1], pos=i + 3)
        errs = self.gerrs(doc)
        self.assertTrue(any(r['id'] in e and 'without a ground' in e for e in errs), errs)

    def test_logic_and_wiper_in_one_link_fail(self):
        doc = gate_doc()
        lg = next(l for l in doc['links'] if any(p.get('class') == 'LOGIC' for p in l['positions'])
                  and any(p['kind'] == 'unused' for p in l['positions']))
        wp = next(l for l in doc['links'] if any(p.get('class') == 'WIPER' for p in l['positions']))
        k = next(i for i, p in enumerate(wp['positions']) if p.get('class') == 'WIPER')
        u = next(i for i, p in enumerate(lg['positions']) if p['kind'] == 'unused')
        lg['positions'][u] = dict(wp['positions'][k], pos=u + 1)
        wp['positions'][k] = {'pos': k + 1, 'kind': 'unused'}
        errs = self.gerrs(doc)
        self.assertTrue(any(lg['id'] in e and 'LOGIC and WIPER share the link' in e for e in errs), errs)

    def test_signal_on_two_links_fails(self):
        doc = gate_doc()
        a = doc['links'][0]
        b = next(l for l in doc['links'][1:] if any(p['kind'] == 'unused' for p in l['positions']))
        sig = next(p for p in a['positions'] if p['kind'] == 'signal')
        u = next(i for i, p in enumerate(b['positions']) if p['kind'] == 'unused')
        b['positions'][u] = dict(sig, pos=u + 1)
        errs = self.gerrs(doc)
        self.assertTrue(any(b['id'] in e and 'also on' in e for e in errs), errs)

    def test_tails_longer_than_the_cable_fail(self):
        doc = gate_doc()
        r = next(l for l in doc['links'] if l['placed'])
        g = r['geometry']
        d = {v: k for k, v in links.DIR_NAMES.items()}[r['direction']]
        size = links_gate.fh12_size(r['circuits'], GINP['gopts'], {'cable': r['cable'], 'cable_length_mm': r['cable_length_mm']})
        r['geometry'] = links_gate.gate_geometry(r['slot_centre'][0], r['slot_centre'][1], d, size, GINP['opts'],
                                                 ef=g['front_extension_mm'], ek=g['K_extension_mm'] + 30.0,
                                                 hard=g['tail_rule_hard_mm'])
        errs = self.gerrs(doc)
        self.assertTrue(any(r['id'] in e and 'tails longer than the cable allows' in e for e in errs), errs)

    def test_panel_pad_under_the_first_4_mm_fails(self):
        doc = gate_doc()
        pl = [l for l in doc['links'] if l['placed']]
        model = links_gate.GateModel(GINP, GSITES)
        web = links.val(GINP['opts']['slot']['web_mm'])
        found = None
        for r in pl:
            if r['front_board'] != 'P':
                continue
            others = links.Placed()
            for o in pl:
                if o is not r:
                    links_gate.add_placed(others, o['front_board'], o['geometry'], o['id'])
            size = links_gate.fh12_size(r['circuits'], GINP['gopts'], {'cable': r['cable'], 'cable_length_mm': r['cable_length_mm']})
            for dx in range(-12, 13, 1):
                for dy in range(-12, 13, 1):
                    for d, name in links.DIR_NAMES.items():
                        sx, sy = r['slot_centre'][0] + dx, r['slot_centre'][1] + dy
                        geo = links_gate.gate_geometry(sx, sy, d, size, GINP['opts'], hard=4.0)
                        why = links_gate.evaluate(model, others, 'P', geo, web, None)
                        if why and why[0].startswith('first 4.0 mm of the front tail on panel hardware'):
                            found = (r, sx, sy, name, geo)
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break
        self.assertIsNotNone(found, 'no place found with a panel pad under the first 4.0 mm')
        r, sx, sy, name, geo = found
        r.update({'slot_centre': [sx, sy], 'direction': name, 'geometry': geo})
        errs = self.gerrs(doc)
        self.assertTrue(any(r['id'] in e and 'first 4.0 mm of the front tail on panel hardware' in e for e in errs), errs)

    def test_tail_rule_is_a_screen_not_a_listing(self):
        pl = [l for l in GDOC['links'] if l['placed']]
        model = links_gate.GateModel(GINP, GSITES)
        for r in pl:
            first = r['geometry']['front_tail_first']
            self.assertIsNone(model.forbidden(r['front_board'], 'B', first), r['id'])


if __name__ == '__main__':
    unittest.main()
