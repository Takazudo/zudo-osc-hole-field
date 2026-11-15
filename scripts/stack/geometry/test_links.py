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
import links_gate_readme  # noqa: E402


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
    # the whole record of a8 part 1 is regenerated and compared; the retained comparison files are not (scope item 8)
    GFRESH = links_gate.generate()


def gate_doc():
    return copy.deepcopy({'links': GDOC['links'], 'flags': GDOC['flags']})


def gctx(flags=None):
    model = links_gate.cached_model(GINP, GSITES, links_gate.RECORD)
    return model, links_gate.Ctx(GINP, model, dict(links_gate.RECORD, **(flags or {})))


def pos(seq):
    """Positions from a compact list: 'G' ground, 'U' unused, else (net, class)."""
    out = []
    for i, x in enumerate(seq):
        if x in ('G', 'U'):
            out.append({'pos': i + 1, 'kind': 'ground' if x == 'G' else 'unused'})
        else:
            out.append({'pos': i + 1, 'kind': 'signal', 'net': x[0], 'class': x[1], 'site': 'S'})
    return out


class Gate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setUpGate()

    def gerrs(self, doc):
        return links_gate.check(doc, GINP, GSITES)

    # ---- the record and its staleness (finding 4, item 8)

    def test_gate_file_equals_a_fresh_generation(self):
        self.assertEqual(links_gate.render(GFRESH), links_gate.LINK_GATE.read_text(),
                         'link-gate.json is stale; regenerate with: ' + links_gate.REGEN)
        self.assertEqual(links_gate.readme(GDOC), links_gate.LINK_GATE_README.read_text())

    def test_the_record_holds_no_section_the_tests_do_not_regenerate(self):
        for k in ('field_change', 'causes', 'sensitivity', 'adapters_at_8', 'nearest_legal_unbounded'):
            self.assertNotIn(k, GDOC)
        a7 = json.loads(links_gate.A7_FILE.read_text())
        self.assertEqual(a7['commit_of_run'], '5c1a06f')
        self.assertIn('not regenerated', a7['note'])
        self.assertEqual((len(a7['causes']), len(a7['sensitivity'])), (6, 7))
        chain = json.loads(links_gate.CHAIN_FILE.read_text())
        self.assertIn('the tests do not regenerate them', chain['note'])
        self.assertEqual([r['run'] for r in chain['runs']], [c[0] for c in links_gate.CHAIN[:-1]])

    def test_gate_passes_the_checker(self):
        self.assertEqual(self.gerrs(GDOC), [])

    def test_refined_places_pass_the_checker(self):
        refined = [r for r in GDOC['links'] if (r.get('refinement') or {}).get('found')]
        self.assertTrue(refined)
        for r in refined:
            self.assertLess(r['grid_mm'], links.val(GINP['opts']['search']['step_mm']))
        errs = self.gerrs(GDOC)
        self.assertEqual([e for e in errs if any(e.startswith(r['id'] + ':') for r in refined)], [])

    def test_improvement_moves_stay_within_the_allowance_of_the_cost_before_the_pass(self):
        # finding 14: the bound is taken from the cost before the pass, and every move is recorded
        allow = links.val(GINP['gopts']['refinement']['improvement']['allowance'])
        for r in GDOC['links']:
            moves = r.get('moves_by_improvement', [])
            for m in moves:
                self.assertLessEqual(m['new_cost'], m['cost_before_the_pass'] + allow + 1e-9, r['id'])
                self.assertEqual(m['cost_before_the_pass'], moves[0]['cost'])
            if moves:
                self.assertEqual(r['cost'], moves[-1]['new_cost'])

    def test_classes_equal_the_link_electrical_list(self):
        res = json.loads((links.sg.ROOT / 'design/stack/link-electrical/results.json').read_text())['signals']
        mine = {(s['id'], n): c for s in GSITES if s['joint'] != 'O-K' for n, c in zip(s['signals'], s['classes'])}
        self.assertEqual(len(res), 490)
        self.assertEqual(mine, {(r['pair'], r['net']): r['class'] for r in res})

    def test_511_signals_each_on_one_link(self):
        self.assertEqual(GDOC['signals']['total'], 511)
        seen = [(p['site'], p['net']) for r in GDOC['links'] for p in r['positions'] if p['kind'] == 'signal']
        seen += [(x['site'], n) for r in GDOC['links'] if r.get('oversize') for x in r['sites'] for n in x['signals']]
        self.assertEqual(len(seen), 511)
        self.assertEqual(len(set(seen)), 511)

    # ---- item 1: fixings from the fixing list

    def test_fixings_come_from_the_fixing_list(self):
        fx = links_gate.fixing_sites(GINP)
        self.assertEqual(GDOC['fixings']['count'], len(fx))
        self.assertEqual(GDOC['fixings']['by_kind'], {'post': 18, 'sleeve added': 4})
        ids = {f['id'] for f in fx}
        self.assertEqual({i for i in ids if i.startswith('SLV')}, {'SLV-U1', 'SLV-U2', 'SLV-L1', 'SLV-L2'})
        self.assertFalse(ids & {x['id'] for x in GINP['fixing_list']['reserve'] + GINP['fixing_list']['alternatives']})
        self.assertFalse(ids & {'JL-SUP-1', 'K-SUP-5', 'K-SUP-8'})
        jr = sorted(f['K'][0] for f in fx if f['front_board'] == 'JR' and f['kind'] == 'post' and 'AGND' in f['id'] or
                    f['id'] == 'POWER-JR-+5V')
        self.assertEqual(jr, [227.5, 244.5, 261.5, 278.5])
        self.assertEqual(len(links_gate.fixing_sites(GINP, 'a7')), 30)
        h = GDOC['fixings']['access_holes']
        self.assertEqual([(x['for'], x['diameter_mm'], x['inside_P_keepout_of_its_sleeve']) for x in h], [('SLV-L2', 7.0, True)])

    def test_every_placed_link_clears_every_active_fixing(self):
        web = links.val(GINP['opts']['slot']['web_mm'])
        fx = links_gate.fixing_sites(GINP)
        for r in GDOC['links']:
            if not r['placed']:
                continue
            g = r['geometry']
            for f in fx:
                for rect in (links.sg.grow(g['slot'], web), g['K_connector'], g['K_tail']):
                    self.assertLessEqual(links.sg.circle_rect_depth(f['K'][0], f['K'][1], f['r_K'], rect), 1e-9,
                                         (r['id'], f['id']))
                if f['front_board'] == r['front_board']:
                    for rect in (g['front_connector'], g['front_tail']):
                        self.assertLessEqual(links.sg.circle_rect_depth(f['front'][0], f['front'][1], f['r_front'], rect),
                                             1e-9, (r['id'], f['id']))

    def test_K_field_on_SLV_L2_is_rejected(self):
        model, ctx = gctx()
        size = links_gate.fh12_size(8, GINP['gopts'])
        gm = links_gate.GeoMaker(size, GINP['opts'], ctx.hard)
        d = (1, 0)
        sx = 244.0 - (gm.a0 + gm.D / 2)
        why = links_gate.check_k(model, links.Placed(), gm.k(sx, 230.0, d, 0.0))
        self.assertIsNotNone(why)
        self.assertIn('fixing keep-out SLV-L2', why[0])

    def test_front_tail_across_SLV_L1_is_rejected(self):
        model, ctx = gctx()
        size = links_gate.fh12_size(8, GINP['gopts'])
        gm = links_gate.GeoMaker(size, GINP['opts'], ctx.hard)
        d = (0, 1)
        sy = 276.0 + (gm.a0 + gm.hs) / 2
        ft = gm.front(93.0, sy, d, 0.0)['front_tail']
        h = model.forbidden('P', 'B', ft, tail=True)
        self.assertIsNotNone(h)
        self.assertIn('fixing keep-out SLV-L1', h[0])

    # ---- item 2: allocation of DS-77 to DS-79

    def test_circuits_needed(self):
        f = links_gate.circuits_needed
        self.assertEqual(f(['ANALOGUE'] * 7), 13)
        self.assertEqual(f(['WIPER'] * 7), 8)
        self.assertEqual(f(['LOGIC'] * 3 + ['ANALOGUE'], 'a7'), 5)
        self.assertEqual(f(['LOGIC'] * 3 + ['ANALOGUE']), 6)
        self.assertEqual(f(['LOGIC'] * 3), 5)
        self.assertEqual(f(['LOGIC'] * 2 + ['ANALOGUE'] * 2), 6)
        self.assertEqual(f(['LOGIC'] + ['ANALOGUE']), 3)
        self.assertEqual(f(['STATIC'] * 7), 8)
        self.assertIsNone(f(['LOGIC', 'WIPER']))
        self.assertEqual(f(['PRECISION']), 2)

    def test_allocation_meets_its_own_rule(self):
        cases = [['LOGIC'] * 3, ['LOGIC'] * 3 + ['ANALOGUE'], ['LOGIC'] * 2 + ['ANALOGUE', 'PRECISION'],
                 ['WIPER'] * 2 + ['PRECISION', 'ANALOGUE'], ['LOGIC', 'PRECISION', 'ANALOGUE']]
        for cl in cases:
            sig = [('N%d' % i, c, 'S') for i, c in enumerate(cl)]
            n = links_gate.circuits_needed(cl)
            p = links_gate.allocation(sig, n + 2)
            self.assertEqual(links_gate.allocation_errors(p), [], cl)
            self.assertEqual(len(links_gate.allocation(sig, n)), n)

    def test_logic_run_at_position_1_fails(self):
        p = pos([('A', 'LOGIC'), ('B', 'LOGIC'), 'G', ('C', 'ANALOGUE')])
        self.assertTrue(any('outer position (DS-77)' in e for e in links_gate.allocation_errors(p)))

    def test_logic_run_without_a_ground_on_one_side_fails(self):
        p = pos(['G', ('A', 'LOGIC'), ('B', 'LOGIC'), ('C', 'ANALOGUE'), 'G'])
        self.assertTrue(any('without a ground' in e for e in links_gate.allocation_errors(p)))

    def test_unused_counts_as_a_ground(self):
        p = pos([('C', 'ANALOGUE'), 'G', ('A', 'LOGIC'), ('B', 'LOGIC'), 'U'])
        self.assertEqual(links_gate.allocation_errors(p), [])
        self.assertTrue(links_gate.allocation_errors(p, 'a7') == [])
        self.assertTrue(any('no ground' in e for e in links_gate.allocation_errors(pos([('C', 'ANALOGUE'), 'U']), 'a7')))

    def test_outer_preference_of_ds78(self):
        p = pos([('P', 'PRECISION'), 'G', ('A', 'ANALOGUE'), 'G', ('W', 'WIPER')])
        self.assertTrue(any('DS-78' in e for e in links_gate.allocation_errors(p)))

    def test_adapter_links_take_8_circuits_in_the_ruled_order(self):
        order = GINP['gopts']['adapters']['order']
        for r in GDOC['links']:
            if r['joint'] == 'O-K':
                self.assertEqual(r['circuits'], 8)
                got = [p['net'].split('/')[-1] if p['kind'] == 'signal' else 'AGND' for p in r['positions']]
                self.assertEqual(got, order)

    def test_adapter_link_in_another_order_fails(self):
        doc = gate_doc()
        r = next(l for l in doc['links'] if l['joint'] == 'O-K' and l['placed'])
        p = r['positions']
        p[0], p[1] = dict(p[1], pos=1), dict(p[0], pos=2)
        errs = self.gerrs(doc)
        self.assertTrue(any(r['id'] in e and 'ruled order' in e for e in errs), errs)

    # ---- item 3: compliance

    def test_compliance_value_is_the_largest_node_in_the_grown_field(self):
        cm = links_gate.ComplianceMap(GINP['compliance'], GINP['gopts']['compliance'])
        nodes = GINP['compliance']['nodes']
        for r in [l for l in GDOC['links'] if l['placed']][:12]:
            g = links.sg.grow(r['geometry']['K_connector'], 4.0)
            want = max(v for x, y, v in nodes if g[0] - 1e-9 <= x <= g[2] + 1e-9 and g[1] - 1e-9 <= y <= g[3] + 1e-9)
            self.assertAlmostEqual(cm.value(r['geometry']['K_connector']), want)
            self.assertAlmostEqual(r['compliance_mm_per_N'], links.r4(want))
        self.assertEqual(GDOC['summary']['compliance']['links_above_limit'], [])

    def test_K_field_in_the_lower_left_corner_is_rejected(self):
        model, ctx = gctx()
        geo = {'K_connector': [10.0, 272.0, 22.0, 278.1], 'K_tail': [14.0, 268.0, 18.0, 272.0]}
        why = links_gate.check_k(model, links.Placed(), geo)
        self.assertIsNotNone(why)
        self.assertIn('mm/N on the compliance map', why[0])

    # ---- item 4: latch rule

    def test_latch_exempt_packages(self):
        f = links_gate.latch_exempt
        self.assertTrue(all(f(x) for x in ('R0603', 'C0603', 'R0402', 'SOD-123', 'SOT-23')))
        self.assertFalse(any(f(x) for x in ('C0805', 'C1206', 'SOT-363_SC-70-6', 'SOIC-8_3.9x4.9mm_P1.27mm', '')))

    def test_latch_rule_displaces_no_exempt_part_and_nothing_under_the_field(self):
        model, ctx = gctx()
        for r in GDOC['links']:
            if r['placed']:
                d = r['displaced']
                self.assertFalse(set(d['K B (latch)']) & set(d['K B (field)']), r['id'])
                self.assertFalse([x for x in d['K B (latch)'] if links_gate.latch_exempt(model.lib[x])], r['id'])
        s = GDOC['summary']['K_displaced']
        self.assertEqual(len(GDOC['refs']['K_displaced_by_the_latch_rule_alone']), s['B.Cu by the latch rule alone'])

    # ---- findings of the two code reviews

    def test_finding_1_negative_or_off_step_extension_fails(self):
        for e in (-2.0, 1.0):
            doc = gate_doc()
            r = next(l for l in doc['links'] if l['placed'])
            d = {v: k for k, v in links.DIR_NAMES.items()}[r['direction']]
            size = links_gate.fh12_size(r['circuits'], GINP['gopts'], {'cable': r['cable'], 'cable_length_mm': r['cable_length_mm']})
            r['geometry'] = links_gate.gate_geometry(r['slot_centre'][0], r['slot_centre'][1], d, size, GINP['opts'],
                                                     ef=e, ek=r['geometry']['K_extension_mm'], hard=4.0)
            errs = self.gerrs(doc)
            self.assertTrue(any(r['id'] in x and 'not a non-negative multiple' in x for x in errs), errs)

    def test_finding_2_joint_front_board_size_and_adapter_cable_are_checked(self):
        doc = gate_doc()
        r = next(l for l in doc['links'] if l['joint'] == 'P-K' and l['circuits'] == 8 and l['placed'])
        r['cable'], r['cable_length_mm'] = GINP['gopts']['adapter_short_cable']['cable'], 40.0
        errs = self.gerrs(doc)
        self.assertTrue(any(r['id'] in x and 'not the stock cable' in x for x in errs), errs)
        doc = gate_doc()
        r = next(l for l in doc['links'] if l['joint'] == 'JL-K')
        r['front_board'] = 'JR'
        self.assertTrue(any(r['id'] in x and 'joint or front board' in x for x in self.gerrs(doc)))
        doc = gate_doc()
        r = next(l for l in doc['links'] if l['joint'] == 'JL-K')
        r['circuits'] = 26
        self.assertTrue(any(r['id'] in x and 'not a size of joint' in x for x in self.gerrs(doc)))

    def test_finding_3_empty_extension_list_gives_a_reason(self):
        model, ctx = gctx()
        size = links_gate.fh12_size(8, GINP['gopts'])
        r = next(l for l in GDOC['links'] if l['placed'] and l['circuits'] == 8 and l['joint'] == 'P-K')
        d = {v: k for k, v in links.DIR_NAMES.items()}[r['direction']]
        why, c = links_gate.candidate(ctx, links.Placed(), r['front_board'], size, None, r['slot_centre'][0],
                                      r['slot_centre'][1], d, 0.0, -5.0)
        self.assertIsNone(c)
        self.assertEqual(why, ('cable too short for the minimum tails', None))

    def test_finding_5_oversize_site_is_recorded_not_raised(self):
        sites = [{'id': 'X', 'xy': [0.0, 0.0], 'classes': ['ANALOGUE'] * 5}, {'id': 'Y', 'xy': [1.0, 0.0], 'classes': ['WIPER']}]
        out = links_gate.gate_cluster(sites, 8, 35.0, 'T')
        self.assertEqual([(c['members'], c.get('oversize')) for c in out], [(['X'], 9), (['Y'], None)])

    def test_findings_6_7_8_15_17_readme_reads_the_record(self):
        g = links_gate_readme._g
        self.assertEqual((g(5.62), g(0.25), g(117.875), g(0.0425)), ('5.62', '0.25', '117.875', '0.0425'))
        self.assertNotIn('at 8 circuits', ''.join(l for l in links_gate.LINK_GATE_README.read_text().splitlines()
                                                  if l.startswith('#')))
        doc = copy.deepcopy(GDOC)
        doc['parameters']['latch_margin_mm'] = 1.75
        doc['parameters']['trim_to_mm'] = 0.75
        txt = links_gate.readme(doc)
        self.assertIn('within 1.75 mm', txt)
        self.assertIn('to 0.75 mm or less', txt)

    def test_findings_9_16_misses_and_blockers_are_recomputed_against_the_final_set(self):
        un = [r for r in GDOC['links'] if not r['placed'] and not r.get('oversize')]
        for r in un:
            self.assertFalse([b for b in r['most_frequent_blockers'] if 'own front board' in b['blocker']])
            self.assertFalse([m for m in r['nearest_misses'] if 'own front board' in m['screen']])
        if un:
            doc = gate_doc()
            r = next(l for l in doc['links'] if l['id'] == un[0]['id'])
            r['nearest_misses'] = r['nearest_misses'][1:]
            self.assertTrue(any(r['id'] in x and 'nearest misses' in x for x in self.gerrs(doc)))

    def test_finding_11_a_K_side_failure_is_a_stage(self):
        model, ctx = gctx()
        r = next(l for l in GDOC['links'] if l['placed'] and l['joint'] == 'P-K' and l['geometry']['K_extension_mm'] == 0)
        size = links_gate.rec_size(ctx, r)
        gm = links_gate.GeoMaker(size, GINP['opts'], ctx.hard)
        d = {v: k for k, v in links.DIR_NAMES.items()}[r['direction']]
        placed = links.Placed()
        sx, sy = r['slot_centre']
        placed.add('K', 'B', links.oriented_rect(sx, sy, d, gm.hs + 0.01, gm.a0 + gm.D + 40.0, gm.L / 2 + 1.0), 'test block')
        model.memo_for(None)
        res = links_gate.staged(ctx, placed, r['front_board'], gm, r['slot_centre'][0], r['slot_centre'][1], d,
                                r['geometry']['front_extension_mm'], ctx.spare(r['front_board'], size), None)
        self.assertEqual(res[0], 4)
        self.assertIn('test block', res[1])

    def test_findings_13_18_stage_labels_and_one_sided_corridors(self):
        names = [s.format(hard='4') for s in links_gate.STAGES]
        self.assertEqual(len(set(names)), 5)
        for r in GDOC['links']:
            y = r.get('why_no_place')
            if y and 'stage' in y:
                self.assertEqual(y['lacks'], names[y['stage']])
                for c in list(y['field_corridor_mm'].values()) + [(y.get('tail_corridor_mm') or {}).get('across')]:
                    if c:
                        self.assertEqual(c['free'] is None, c['gap_low_mm'] is None or c['gap_high_mm'] is None)

    # ---- fault injection of a7, kept

    def test_two_analogue_signals_side_by_side_fail(self):
        doc = gate_doc()
        r = next(l for l in doc['links'] if l['joint'] == 'JL-K')
        p = r['positions']
        i = next(k for k in range(len(p) - 2) if p[k]['kind'] == 'signal' and p[k]['class'] == 'ANALOGUE'
                 and p[k + 1]['kind'] == 'ground' and p[k + 2]['kind'] == 'signal' and p[k + 2]['class'] == 'ANALOGUE')
        p[i + 1], p[i + 2] = dict(p[i + 2], pos=i + 2), dict(p[i + 1], pos=i + 3)
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
        a = next(l for l in doc['links'] if l['positions'])
        b = next(l for l in doc['links'] if l is not a and any(p['kind'] == 'unused' for p in l['positions']))
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
        model, _ = gctx()
        model.memo_for(None)
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
        model, _ = gctx()
        for r in GDOC['links']:
            if r['placed']:
                self.assertIsNone(model.forbidden(r['front_board'], 'B', r['geometry']['front_tail_first']), r['id'])


if __name__ == '__main__':
    unittest.main()
