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
import links_gate_part2  # noqa: E402


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


PART2_KEYS = ('ways_out', 'consolidation', 'replacement', 'displaced_k_ic_packages')


def gate_doc():
    return copy.deepcopy(dict({'links': GDOC['links'], 'flags': GDOC['flags']}, **{k: GDOC[k] for k in PART2_KEYS}))


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
        # the four links without a place of part 1 keep their analysis; no live link is without a place after part 2,
        # so the recomputation against the final set is exercised by test_review_2 of GatePart2
        un = [dict(r, **r['part_1_analysis']) for r in GDOC['links'] if r.get('part_1_analysis')]
        self.assertEqual(len(un), 4)
        for r in un:
            self.assertTrue(r['nearest_misses'])
            self.assertFalse([b for b in r['most_frequent_blockers'] if 'own front board' in b['blocker']])
            self.assertFalse([m for m in r['nearest_misses'] if 'own front board' in m['screen']])

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


class GatePart2(unittest.TestCase):
    """ST-02 a8 part 2: the ways out, the consolidation, the re-placement search, and the ten review findings of the
    code of part 1. Fault tests call the part of the checker that owns the rule."""

    @classmethod
    def setUpClass(cls):
        setUpGate()

    def ctx(self):
        return gctx()[1]

    def site_by(self):
        return {s['id']: s for s in GSITES}

    # ---- point 1: ways out

    def test_every_link_without_a_place_of_part_1_has_a_way(self):
        per = GDOC['ways_out']['per_link']
        self.assertEqual(sorted(per), sorted(GDOC['ways_out']['links_without_a_place']))
        self.assertEqual(len(per), GDOC['part_1']['unplaced'])
        for lid, w in per.items():
            self.assertIn(w['way'], (1, 2, 3, 4, 5), lid)

    def test_rider_beyond_its_class_distance_fails(self):
        doc = gate_doc()
        r = next(l for l in doc['links'] if l.get('riders_out'))
        x = r['riders_out'][0]
        lim = links_gate_part2.limits_of(GINP['gopts'])
        g = dict(GINP['gopts'], ways_out=dict(GINP['gopts']['ways_out'], rider_distance_mm={
            'value': {k: min(v, x['distance_mm'] - 1.0) for k, v in lim.items()}}))
        ctx = self.ctx()
        ctx.gopts = g
        errs = links_gate_part2.check_riders(ctx, doc, self.site_by())
        self.assertTrue(any(r['id'] in e and 'beyond the' in e for e in errs), errs)

    def test_rider_on_another_joint_fails(self):
        doc = gate_doc()
        r = next(l for l in doc['links'] if l.get('riders_out'))
        other = next(l for l in doc['links'] if l['placed'] and not l.get('gone') and l['joint'] != r['joint'])
        r['riders_out'][0]['host'] = other['id']
        errs = links_gate_part2.check_riders(self.ctx(), doc, self.site_by())
        self.assertTrue(any('another joint' in e for e in errs), errs)

    def test_rider_not_recorded_on_its_host_fails(self):
        doc = gate_doc()
        h = next(l for l in doc['links'] if l.get('riders_in') and not l.get('gone'))
        h['riders_in'] = h['riders_in'][1:]
        errs = links_gate_part2.check_riders(self.ctx(), doc, self.site_by())
        self.assertTrue(any('is not recorded on its host' in e for e in errs), errs)

    def test_host_allocation_made_illegal_fails(self):
        doc = gate_doc()
        h = next(l for l in doc['links'] if not l.get('gone') and any(p.get('rider_from') for p in l['positions'])
                 and l['grounds'] >= 1 and l['unused'] == 0)
        p = h['positions']
        i = next(k for k, q in enumerate(p) if q['kind'] == 'ground')
        p[i] = dict(next(q for q in p if q['kind'] == 'signal' and q.get('rider_from')), pos=i + 1)
        errs = self.gerrs(doc)
        self.assertTrue(any(h['id'] in e for e in errs), errs)

    def gerrs(self, doc):
        return links_gate.check(doc, GINP, GSITES)

    def test_rider_signal_on_two_links_fails(self):
        doc = gate_doc()
        h = next(l for l in doc['links'] if not l.get('gone') and any(p.get('rider_from') for p in l['positions']))
        b = next(l for l in doc['links'] if not l.get('gone') and l is not h and any(p['kind'] == 'unused' for p in l['positions']))
        sig = next(q for q in h['positions'] if q.get('rider_from'))
        u = next(i for i, q in enumerate(b['positions']) if q['kind'] == 'unused')
        b['positions'][u] = dict(sig, pos=u + 1)
        errs = self.gerrs(doc)
        self.assertTrue(any(b['id'] in e and ('also on' in e or 'exactly the signals' in e) for e in errs), errs)

    def test_way_5_with_a_place_fails(self):
        doc = gate_doc()
        lid = next(iter(doc['ways_out']['per_link']))
        doc['ways_out']['per_link'][lid] = {'way': 5}
        r = next(l for l in doc['links'] if l['id'] == lid)
        r['gone'], r['placed'] = None, True
        errs = links_gate_part2.check_ways(self.ctx(), doc, self.site_by())
        self.assertTrue(any(lid in e and 'way 5' in e for e in errs), errs)

    def test_way_4_reduces_the_field_growth_against_panel_pads_only(self):
        idx = links.sg.RectIndex()
        pad = [10.0, 10.0, 11.0, 11.0]
        idx.add(pad, ('rect', pad, 'panel hardware RV1'))

        class M:
            forb = {('P', 'B'): idx}
        # a field (grown 0.25 mm) 0.1 mm into the pad: rejected at the growth of record, clear at 0.10 mm
        fc = [5.0, 10.2, 10.1, 10.8]
        self.assertEqual(links_gate.panel_hit(M, 'P', fc), ('panel hardware RV1', 0.1))
        self.assertIsNone(links_gate.panel_hit(M, 'P', sg_grow(fc, -0.15)))
        self.assertEqual(links_gate_part2.pad_distance(M, 'P', fc, 0.15), (0.05, 'RV1'))
        lid = next(l for l, w in GDOC['ways_out']['per_link'].items() if w['way'] == 4)
        r = next(l for l in GDOC['links'] if l['id'] == lid)
        self.assertEqual(r['field_growth_against_panel_pads_mm'], 0.1)
        doc = gate_doc()
        x = next(l for l in doc['links'] if l['id'] == lid)
        del x['field_growth_against_panel_pads_mm']
        errs = self.gerrs(doc)
        self.assertTrue(any(lid in e and 'way 4 gives 0.1 mm' in e for e in errs), errs)

    def test_way_3_is_only_tried_where_a_sleeve_keep_out_can_be_the_blocker(self):
        seen = 0
        for lid, w in GDOC['ways_out']['per_link'].items():
            for f, v in w.get('way_3', {}).items():
                seen += 1
                # either out of reach, or searched without the keep-out with no place found
                self.assertTrue(v['distance_mm'] > v['reach_mm'] or ('test' in v and v['place_without_the_keepout'] is None))
                self.assertFalse(v['holds'])
        self.assertTrue(seen)
        self.assertEqual(GDOC['ways_out']['way_3_trials'], [])

    # ---- point 2: consolidation

    def test_consolidation_runs_only_when_every_link_has_a_place(self):
        doc = gate_doc()
        c = doc['consolidation']
        self.assertEqual(c['run'], not any(not l['placed'] for l in doc['links'] if not l.get('gone')))
        doc['consolidation'] = dict(c, run=not c['run'], why='test', pass_=[])
        errs = links_gate_part2.check_consolidation(self.ctx(), doc)
        self.assertTrue(errs)

    def test_consolidation_out_of_order_fails(self):
        doc = gate_doc()
        c = doc['consolidation']
        self.assertTrue(c['run'])
        c['pass'] = list(reversed(c['pass']))
        errs = links_gate_part2.check_consolidation(self.ctx(), doc)
        self.assertTrue(any('order' in e for e in errs), errs)

    def test_consolidation_verdict_differs_fails(self):
        doc = gate_doc()
        c = doc['consolidation']
        x = next(p for p in c['pass'] if p['dissolved'])
        x['dissolved'] = False
        errs = links_gate_part2.check_consolidation(self.ctx(), doc)
        self.assertTrue(any(x['link'] in e for e in errs), errs)

    def test_dissolved_link_carries_nothing(self):
        for r in GDOC['links']:
            if r.get('gone'):
                self.assertEqual((r['positions'], r['placed'], r['signals']), ([], False, 0), r['id'])
                self.assertEqual(len(r['riders_out']), r['signals_before'])

    # ---- point 3: re-placement

    def rows(self, doc):
        return doc['replacement']['footprints']

    def test_replaced_footprint_on_an_obstacle_fails(self):
        doc = gate_doc()
        r = next(x for x in self.rows(doc) if x['step'] == 1 and 'under a field' in x['why'])
        r['shift_mm'], r['moved_mm'] = [0.0, 0.0], 0.0
        errs = links_gate_part2.check_replacement(self.ctx(), GINP, doc)
        self.assertTrue(any(r['ref'] in e and 'meets' in e for e in errs), errs)

    def test_replaced_footprint_on_an_earlier_replaced_one_fails(self):
        doc = gate_doc()
        rows = [x for x in self.rows(doc) if x['step'] != 'no position']
        a = rows[0]
        b = next(x for x in rows[1:] if x['board'] == a['board'] and x['new_face'] == a['new_face'] == x['face']
                 and not x['turned'] and not a['turned'])
        # put b's courtyard onto a's new courtyard
        dx = a['new_courtyard'][0] - b['courtyard'][0]
        dy = a['new_courtyard'][1] - b['courtyard'][1]
        b['shift_mm'], b['moved_mm'], b['step'] = [dx, dy], round((dx * dx + dy * dy) ** 0.5, 4), 3
        errs = links_gate_part2.check_replacement(self.ctx(), GINP, doc)
        self.assertTrue(any(b['ref'] in e and ('meets' in e or 'outside step' in e) for e in errs), errs)

    def test_shift_outside_its_step_fails(self):
        doc = gate_doc()
        r = next(x for x in self.rows(doc) if x['step'] == 3 and x['moved_mm'] > 12.0)
        r['step'] = 1
        errs = links_gate_part2.check_replacement(self.ctx(), GINP, doc)
        self.assertTrue(any(r['ref'] in e and 'outside step' in e for e in errs), errs)

    def test_replacement_out_of_the_ds97_order_fails(self):
        doc = gate_doc()
        rows = self.rows(doc)
        rows[0], rows[-1] = rows[-1], rows[0]
        errs = links_gate_part2.check_replacement(self.ctx(), GINP, doc)
        self.assertTrue(any('DS-97 order' in e for e in errs), errs)

    def test_sensitive_packages_come_first_and_step_3_starts_hold(self):
        rows = self.rows(GDOC)
        sym = {x['ref']: x['symbol'] for x in json.loads((links.sg.ROOT / links_gate_part2.RAIL_LEDGER).read_text())['physical_ic_packages']}
        tiers = [0 if (r['board'] == 'K' and sym.get(r['ref']) in links_gate_part2.SENSITIVE_FUNCTION) or
                 links_gate_part2.module_of_q(r['ref']) else 1 for r in rows]
        self.assertEqual(tiers, sorted(tiers))
        for r in rows:
            if r['ref'] in ('U4215', 'U4226', 'U208') and r['step'] != 'no position':
                self.assertEqual(r['step'], 3)

    def test_displaced_k_ic_packages_keys_are_fixed(self):
        lst = GDOC['displaced_k_ic_packages']
        self.assertIsInstance(lst, list)
        self.assertTrue(lst)
        for x in lst:
            self.assertEqual(sorted(x), sorted(['ref', 'symbol', 'old', 'new', 'moved_mm', 'step']))
            self.assertEqual(sorted(x['old']), ['side', 'xy'])
            self.assertIn(x['old']['side'], ('F.Cu', 'B.Cu'))
            self.assertEqual(len(x['old']['xy']), 2)
            if x['new'] is None:
                self.assertIsNone(x['moved_mm'])
            else:
                self.assertEqual(sorted(x['new']), ['side', 'xy'])
                self.assertIn(x['new']['side'], ('F.Cu', 'B.Cu'))
        doc = gate_doc()
        doc['displaced_k_ic_packages'][0]['moved_mm'] = -1
        self.assertIn('displaced_k_ic_packages differs from the re-placement rows',
                      links_gate_part2.check_replacement(self.ctx(), GINP, doc))

    # ---- point 7: the ten findings of the review of part 1

    def test_review_1_final_search_takes_a_freed_place(self):
        model, ctx = gctx()
        out = copy.deepcopy([l for l in GDOC['links'] if not l.get('gone')])
        r = next(l for l in out if l['placed'] and l['joint'] == 'P-K' and l['circuits'] == 8 and l['grid_mm'] == 2.0)
        ctx.freed = [links_gate.geo_bbox(r['geometry'])]
        r.update({'placed': False, 'refinement': {'found': False, 'grids_tried_mm': []}})
        links_gate.final_pass(ctx, out)
        self.assertTrue(r['placed'])
        self.assertEqual(r['refinement']['by'], 'final search against the final placed set')

    def test_review_2_a_link_recorded_without_a_place_that_has_one_is_reported(self):
        model, ctx = gctx()
        r = next(l for l in GDOC['links'] if l['placed'] and l['joint'] == 'P-K' and l['circuits'] == 8 and l['grid_mm'] == 2.0)
        rr = dict(r, placed=False)
        others = links_gate.placed_index([l for l in GDOC['links'] if l['id'] != r['id'] and not l.get('gone')])
        model.memo_for(None)
        with self.assertRaises(links_gate.LegalPlace):
            links_gate.misses_and_blockers(ctx, others, rr)
        doc = gate_doc()
        x = next(l for l in doc['links'] if l['id'] == r['id'])
        x['placed'] = False
        errs = self.gerrs(doc)
        self.assertTrue(any(r['id'] in e and 'recorded without a place' in e for e in errs), errs)

    def test_review_3_outside_figure_counts_against_the_active_fixings(self):
        model, ctx = gctx()
        keep = links_gate.fixing_keepout_k(model)
        self.assertIn('Q4305', keep)
        saved = links.post_keepout_k
        links.post_keepout_k = lambda root: (_ for _ in ()).throw(AssertionError('post screen read'))
        try:
            s, refs = links_gate.summarise(ctx, GDOC['links'])
        finally:
            links.post_keepout_k = saved
        k_all = set().union(*refs['K_displaced_refs'].values())
        self.assertEqual(s['K_displaced']['outside_fixing_keepouts'], len(k_all - keep))
        self.assertNotIn('outside_post_keepouts', s['K_displaced'])

    def test_review_4_adapters_are_searched_again_at_every_adapter_size(self):
        model, ctx = gctx()
        r = next(l for l in GDOC['links'] if l['joint'] == 'O-K')
        z = links_gate.sizes_to_try(ctx, r)
        self.assertEqual([x['cable_length_mm'] for x in z], [x['cable_length_mm'] for x in links_gate.adapter_sizes(ctx)])
        self.assertEqual(z[0]['cable_length_mm'], 40)

    def test_review_5_centre_grid_radius_cost_and_tail_lists_are_checked(self):
        model, ctx = gctx()
        doc = gate_doc()
        r = next(l for l in doc['links'] if l['placed'] and not l.get('gone'))
        r2 = copy.deepcopy(r)
        r['centre'] = [r['centre'][0] + 1.0, r['centre'][1]]
        r['cost'] += 1.0
        r['under_tails'] = {'front tail': ['X1'], 'K tail': []}
        r['placed_only_with_lengthened_tail'] = True
        r['geometry'] = dict(r['geometry'], front_extension_mm=0.0, K_extension_mm=0.0)
        r['lengthened_tail'] = False
        errs = links_gate.check_placement_terms(ctx, doc, self.site_by())
        for want in ('not the centroid', 'recorded cost', 'under the tails', 'lengthened-tail flags'):
            self.assertTrue(any(r['id'] in e and want in e for e in errs), (want, errs))
        r.update(copy.deepcopy(r2))
        r['slot_centre'] = [r['slot_centre'][0] + 0.1, r['slot_centre'][1]]
        errs = links_gate.check_placement_terms(ctx, doc, self.site_by())
        self.assertTrue(any(r['id'] in e and 'grid' in e for e in errs), errs)
        r['slot_centre'] = [r['centre'][0] + 30.0, r['centre'][1]]
        r['grid_mm'] = 2.0
        errs = links_gate.check_placement_terms(ctx, doc, self.site_by())
        self.assertTrue(any(r['id'] in e and 'beyond the radius' in e for e in errs), errs)

    def test_review_6_no_compliance_node_fails_closed(self):
        model, ctx = gctx()
        cm = ctx.cmap
        far = [-500.0, -500.0, -490.0, -495.0]
        self.assertIsNone(cm.value(far))
        geo = {'K_connector': far, 'K_tail': far}
        m = links_gate.GateModel.__new__(links_gate.GateModel)
        m.compliance = cm
        m.margin = 0.3
        m.inside = lambda key, rect, margin=0.0: True
        why = links_gate.check_k(m, links.Placed(), geo)
        self.assertEqual(why, ('K field has no node of the compliance map (DS-87 not shown)', None))

    def test_review_7_remaining_excludes_oversize_links(self):
        rf = GDOC['search']['refinement']
        un = [l for l in GDOC['links'] if (l.get('way_out') or l.get('refinement')) and not l.get('oversize')
              and not (l.get('refinement') or {}).get('found', True)]
        self.assertEqual(rf['remaining'], len(un))
        self.assertEqual(rf['oversize_not_searched_again'], sum(1 for l in GDOC['links'] if l.get('oversize')))

    def test_review_8_a_site_between_two_sizes_is_tried_alone_at_the_larger(self):
        model, ctx = gctx()
        calls = []
        saved = links_gate.place
        links_gate.place = lambda ctx_, placed, rec, size, centre, own, *a, **k: (calls.append(size['circuits']) or False, {})
        try:
            site = next(s for s in GSITES if s['joint'] == 'P-K')
            fake = dict(site, id='TEST-SITE', classes=['ANALOGUE'] * 10, signals=['/T/S%d' % i for i in range(10)])
            out = []
            c = {'id': 'T-L01', 'centre': fake['xy'], 'members': ['TEST-SITE'], 'oversize': links_gate.circuits_needed(fake['classes'])}
            links_gate._place_ladder(ctx, links.Placed(), out, 'P-K', 'P', c, [40, 26, 14, 8], 2, {'TEST-SITE': fake}, 35.0)
        finally:
            links_gate.place = saved
        self.assertEqual(calls, [26])
        self.assertIn('alone at 26 circuits', out[0]['no_place'])

    def test_review_9_allocation_refuses_a_class_it_does_not_know(self):
        with self.assertRaises(ValueError):
            links_gate.allocation([('/A', 'ANALOGUE', 'S'), ('/B', 'POWER', 'S')], 8)
        with self.assertRaises(ValueError):
            links_gate.allocation([('/A', 'ANALOGUE', 'S'), ('/B', 'STATIC', 'S')], 8)

    def test_review_10_dead_code_is_gone(self):
        import inspect
        self.assertEqual(list(inspect.signature(links_gate.grid_offsets).parameters), ['step', 'radius'])
        self.assertFalse(hasattr(links_gate, 'oriented_rect'))
        self.assertFalse(hasattr(links_gate_readme, '_beside'))
        self.assertNotIn('p_ = None', inspect.getsource(links_gate_readme))


class GatePart3(unittest.TestCase):
    """ST-02 a8 part 3: the ten findings of the review of the code of part 2. Each test fails on the code of part 2."""

    @classmethod
    def setUpClass(cls):
        setUpGate()

    def site_by(self):
        return {s['id']: s for s in GSITES}

    def live_copy(self):
        return copy.deepcopy([l for l in GDOC['links'] if not l.get('gone')])

    def test_finding_1_an_adapter_link_without_a_place_goes_to_way_5(self):
        model, ctx = gctx()
        out = self.live_copy()
        r = next(l for l in out if l['id'] == 'O-K-O1')
        r['placed'] = False
        rec = links_gate_part2.ways_out(ctx, out, self.site_by())
        w = rec['per_link']['O-K-O1']
        self.assertEqual(w['way'], 5)
        self.assertIn('rides on no other link (DS-79)', w['way_1'])
        self.assertIn('adapter link', w['why'])

    def test_finding_2_a_through_hole_pad_may_not_meet_a_link_on_its_other_face(self):
        model, ctx = gctx()
        doc = gate_doc()
        scope = links_gate_part2.replacement_scope(ctx, GINP, doc['links'])
        links_gate_part2.load_part2_inputs(GINP)
        field = links_gate_part2.Field(ctx, GINP, doc['links'], set(scope))
        model.memo_for(None)
        row = next(x for x in doc['replacement']['footprints'] if x['board'] == 'K' and x['new_face'] == 'F')
        cy = row['new_courtyard']
        self.assertIsNone(field.blocked('K', 'F', cy, []))
        hits = [field.blocked('K', 'F', cy, [sg_grow(l['geometry']['K_connector'], -0.5)])
                for l in doc['links'] if l['placed'] and not l.get('gone')]
        self.assertTrue(all(h is not None for h in hits))
        self.assertTrue(any(h.startswith('through-hole pad on K field of') for h in hits), hits)

    def test_finding_3_no_compliance_value_fails_closed_with_the_link_named(self):
        saved = links_gate.ComplianceMap.value
        links_gate.ComplianceMap.value = lambda self, rect: None
        try:
            errs = links_gate.check(gate_doc(), GINP, GSITES)
            model, ctx = gctx()
            out = self.live_copy()
            out[0]['compliance_mm_per_N'] = None if out[0]['placed'] else out[0]['compliance_mm_per_N']
            s, _ = links_gate.summarise(ctx, out)
        finally:
            links_gate.ComplianceMap.value = saved
        self.assertTrue(any('has no node of the compliance map' in e for e in errs), errs[:5])
        self.assertIn(out[0]['id'], s['compliance']['links_above_limit'])

    def test_finding_4_the_way_4_growth_comes_from_the_options(self):
        lid = next(l for l, w in GDOC['ways_out']['per_link'].items() if w['way'] == 4)
        doc = gate_doc()
        x = next(l for l in doc['links'] if l['id'] == lid)
        x['field_growth_against_panel_pads_mm'] = 0.0
        errs = links_gate.check(doc, GINP, GSITES)
        self.assertTrue(any(lid in e and 'way 4 gives 0.1 mm' in e for e in errs), errs)
        doc = gate_doc()
        y = next(l for l in doc['links'] if l['placed'] and not l.get('gone') and l['id'] != lid)
        y['field_growth_against_panel_pads_mm'] = 0.1
        errs = links_gate.check(doc, GINP, GSITES)
        self.assertTrue(any(y['id'] in e and 'does not take way 4' in e for e in errs), errs)

    def test_finding_5_a_qualifying_link_stops_the_run_with_a_named_error(self):
        model, ctx = gctx()
        out = self.live_copy()
        lid = next(l for l, w in GDOC['ways_out']['per_link'].items() if w['way'] == 4)
        r = next(l for l in out if l['id'] == lid)
        r['placed'] = False
        p2 = links_gate_part2
        saved = (p2.ride, p2.search_grids, p2.way3_holds)

        def no_ride(ctx_, link, signals, hosts, state, site_by, limits, why=None):
            if why is not None:
                why.append('test')
            return None
        p2.ride = no_ride
        p2.search_grids = lambda *a, **k: (False, [])
        p2.way3_holds = lambda ctx_, r_, radius: {'SLV-L1': {'distance_mm': 1.0, 'reach_mm': 2.0, 'holds': True}}
        try:
            with self.assertRaises(p2.SleeveTrialNotImplemented) as cm:
                p2.ways_out(ctx, out, self.site_by())
        finally:
            p2.ride, p2.search_grids, p2.way3_holds = saved
        self.assertIn(lid, str(cm.exception))
        self.assertIn('SLV-L1', str(cm.exception))
        self.assertEqual(GDOC['ways_out']['way_3_trial'], p2.WAY_3_STATEMENT)
        doc = gate_doc()
        doc['ways_out']['per_link'][lid]['way_3']['SLV-L1']['holds'] = True
        errs = p2.check_ways(ctx, doc, self.site_by())
        self.assertTrue(any(lid in e and 'not implemented' in e for e in errs), errs)

    def test_finding_6_way_1_leaves_out_links_that_cannot_ride_alone_and_bounds_the_orders(self):
        w1 = GDOC['ways_out']['way_1']
        self.assertEqual(w1['left_out_as_unable_to_ride_alone'], ['P-K-P-L12.01.01.02'])
        self.assertEqual((w1['orders_tried'], w1['bound_cut_the_search']), (1, False))
        self.assertEqual(w1['order_used'], w1['record_order'])
        model, ctx = gctx()
        out = [{'id': i, 'placed': False, 'positions': [], 'signals': 0, 'grounds': 0, 'unused': 0} for i in ('A', 'B')]
        p2 = links_gate_part2
        saved = p2.ride

        def one_only(ctx_, link, signals, hosts, state, site_by, limits, why=None):
            if state.get('taken'):
                if why is not None:
                    why.append('full')
                return None
            state['taken'] = True
            return [], {}
        p2.ride = one_only
        try:
            res = p2.way1(ctx, out, {}, {}, ['A', 'B'], 1)
        finally:
            p2.ride = saved
        self.assertEqual((res['orders_tried'], res['bound_cut_the_search']), (1, True))

    def test_findings_7_8_readme_prints_the_reason_and_one_not_run(self):
        doc = copy.deepcopy(GDOC)
        lid = next(l for l, w in doc['ways_out']['per_link'].items() if w['way'] == 4)
        doc['ways_out']['per_link'][lid]['way_4'] = {'found': False, 'why': 'the limit of 3 links is taken'}
        txt = links_gate.readme(doc)
        self.assertIn('not searched, the limit of 3 links is taken', txt)
        doc['ways_out']['per_link'][lid]['way_4'] = {'found': True, 'field_growth_against_panel_pads_mm': 0.1,
                                                     'distance_from_field_to_pad_mm': None, 'nearest_pad_of': None}
        doc['consolidation'] = {'run': False, 'why': 'NOT RUN: 1 link(s) without a place'}
        txt = links_gate.readme(doc)
        self.assertIn('no pad within 5 mm', txt)
        self.assertNotIn('of None', txt)
        self.assertIn('## Consolidation NOT RUN: 1 link(s)', txt)
        self.assertNotIn('NOT RUN: NOT RUN', txt)

    def test_finding_9_the_floorplan_reference_point_is_the_centre_of_every_turn(self):
        fp = {(p['board'], p['ref']): p for p in json.loads((links.sg.ROOT / links_gate_part2.FLOORPLAN).read_text())['placements']}
        org = {(b, f['ref']): f['origin'] for b in GINP['ci']['boards'] for f in GINP['ci']['boards'][b]}
        turned = [r for r in GDOC['replacement']['footprints'] if r['turned']]
        self.assertTrue(any(r['board'] == 'K' for r in turned))
        for r in turned:
            p = fp[(r['board'], r['ref'])]
            self.assertAlmostEqual(p['x_mm'], org[(r['board'], r['ref'])][0], places=6)
            self.assertAlmostEqual(p['y_mm'], org[(r['board'], r['ref'])][1], places=6)
        lst = {x['ref']: x for x in GDOC['displaced_k_ic_packages']}
        for r in turned:
            if r['ref'] in lst:
                x = lst[r['ref']]
                self.assertAlmostEqual(x['new']['xy'][0], x['old']['xy'][0] + r['shift_mm'][0], places=3)
                self.assertAlmostEqual(x['new']['xy'][1], x['old']['xy'][1] + r['shift_mm'][1], places=3)

    def test_finding_10_reason_from_ride_and_dead_code_gone(self):
        import inspect
        p2 = links_gate_part2
        self.assertFalse(hasattr(p2, 'why_no_ride'))
        self.assertFalse(hasattr(p2, 'cls_of'))
        self.assertFalse(hasattr(p2, 'FRONTS') or hasattr(p2, 'links'))
        self.assertEqual(list(inspect.signature(links_gate.gate_run).parameters), ['inp', 'flags'])
        self.assertEqual(list(inspect.signature(links_gate.summarise).parameters), ['ctx', 'out'])
        self.assertEqual(list(inspect.signature(links_gate.Ctx.grid).parameters), ['self', 'step', 'radius'])
        src = inspect.getsource(links_gate._place_ladder)
        self.assertNotIn("'alone'", src)
        self.assertNotIn("alone = {", src)
        w = GDOC['ways_out']['per_link']['P-K-P-L12.01.01.02']['way_1']
        self.assertEqual(w, 'no: /F2/FREQ_REMOTE (PRECISION, site K-P-48) has only full hosts within 40 mm: '
                            'P-K-P-L12.02.01.01 at 34.14 mm')


def sg_grow(r, m):
    return [r[0] - m, r[1] - m, r[2] + m, r[3] + m]


if __name__ == '__main__':
    unittest.main()
