"""The sections of link-gate.md for part 2 of attempt a8 (ways out, consolidation, re-placement, report, hand-overs).
Headings carry the computed verdicts; every figure is read from the record."""
from links_gate_readme import _g, _xy, _rng


def render(w, doc):
    _ways(w, doc)
    _riders(w, doc)
    _consolidation(w, doc)
    _totals(w, doc)
    _replacement(w, doc)
    _ds97(w, doc)
    _leads(w, doc)
    _compliance(w, doc)
    _lengthened(w, doc)
    _owner(w, doc)
    _handover(w, doc)


def _live(doc):
    return [r for r in doc['links'] if not r.get('gone')]


def _ways(w, doc):
    wo = doc['ways_out']
    per = wo['per_link']
    by = {}
    for lid, x in per.items():
        by.setdefault(x['way'], []).append(lid)
    w1 = wo['way_1']
    if not per:
        return
    w('## Of the %d links without a place of part 1, %s' % (len(per), '; '.join(
        '%d %s way %s' % (len(v), 'takes' if len(v) == 1 else 'take', k) for k, v in sorted(by.items(), key=lambda kv: str(kv[0])))))
    w('')
    w('Ways out of DS-84 and DS-85 in order, the first that works per link (rules in `link-gate-options.json` '
      '`ways_out`). Way 1 is tried for every link before any link takes way 2. Order used: %s (%s; %d order%s tried). '
      'Class distances: %s.'
      % (', '.join(w1['order_used']), 'the order of the record' if w1['order_used'] == w1['record_order'] else
         'the first order in which the most links ride', w1['orders_tried'], '' if w1['orders_tried'] == 1 else 's',
         ', '.join('%s %s mm' % (k, _g(v)) for k, v in wo['limits_mm'].items())))
    w('')
    if w1.get('left_out_as_unable_to_ride_alone'):
        w('Left out of the orders because they cannot ride even alone: %s. At most %d orders are tried%s.'
          % (', '.join(w1['left_out_as_unable_to_ride_alone']), w1['max_orders'],
             '; the bound cut the search' if w1['bound_cut_the_search'] else '; the bound did not cut the search'))
        w('')
    if wo.get('way_3_trial'):
        w('Way 3: %s.' % wo['way_3_trial'])
        w('')
    w('| Link | Way | Riders | Hosts |')
    w('| --- | --- | --- | --- |')
    for lid, x in per.items():
        w('| %s | %s | %s | %s |' % (lid, x['way'], x.get('riders', '-'), ', '.join(x.get('hosts', [])) or '-'))
    w('')
    for lid, x in per.items():
        if x['way'] == 1:
            continue
        w('- %s: way 1 %s.' % (lid, x['way_1']))
        if 'way_2' in x:
            w('  Way 2 (radius %s mm, class distance): %s on grids %s mm.' % (
                _g(x['way_2']['radius_mm']), 'a place' if x['way_2']['found'] else 'no place',
                ', '.join(_g(g) for g in x['way_2']['grids_tried_mm'])))
        for f, v in (x.get('way_3') or {}).items():
            w('  Way 3, keep-out of %s left out: %s (%s mm from the link centre; candidates reach %s mm%s).' % (
                f, 'holds' if v['holds'] else 'does not hold', _g(v['distance_mm']), _g(v['reach_mm']),
                '; ' + v['test'] if 'test' in v else ', so the keep-out cannot be the blocker'))
        if 'way_4' in x:
            w('  Way 4: %s.' % _way4(x['way_4']))
        if x.get('why'):
            w('  Way 5: %s.' % x['why'])
    if any(x['way'] != 1 for x in per.values()):
        w('')
    if not any(by.get(k) for k in (2, 3, 4, 5)):
        w('No link reaches way 2, 3, 4 or 5: no search radius is widened, no sleeve trial is run (no file of trials is '
          'retained), no field growth is reduced, and no link is reported under way 5.')
        w('')


def _way4(y):
    if 'why' in y:
        return 'not searched, %s' % y['why']
    head = 'field growth %s mm against the pads of panel hardware: ' % _g(y.get('field_growth_against_panel_pads_mm'))
    if not y['found']:
        return head + 'no place'
    if y.get('distance_from_field_to_pad_mm') is None:
        return head + 'a place, no pad within 5 mm of its field'
    return head + 'a place, %s mm from its field to the pad obstacle of %s' % (_g(y['distance_from_field_to_pad_mm']),
                                                                           y['nearest_pad_of'])


def _riders(w, doc):
    rows = [(r['id'], x) for r in doc['links'] for x in r.get('riders_out', []) if r.get('gone') == 'riders (way 1)']
    if not rows:
        return
    lim = doc['ways_out']['limits_mm']
    worst = max(rows, key=lambda t: t[1]['distance_mm'] / lim[t[1]['class']])
    w('## Every one of the %d riders of way 1 lies within its class distance; the closest to its limit is %s at %s of %s mm'
      % (len(rows), worst[1]['net'], _g(worst[1]['distance_mm']), _g(lim[worst[1]['class']])))
    w('')
    w('Distance: the larger of the distances from the site to the host connector centre on the front board and on K. '
      'Each host keeps its size, place and cable and is allocated again (DS-62, DS-77, DS-78); its rider positions '
      'carry `rider_from`.')
    w('')
    w('| From link | Signal | Class | Site | Host | Distance mm |')
    w('| --- | --- | --- | --- | --- | --- |')
    for lid, x in rows:
        w('| %s | %s | %s | %s | %s | %s |' % (lid, x['net'], x['class'], x['site'], x['host'], _g(x['distance_mm'])))
    w('')


def _consolidation(w, doc):
    c = doc['consolidation']
    if not c['run']:
        w('## Consolidation %s' % c['why'])
        w('')
        return
    f = c['freed']
    w('## Consolidation dissolves %d of the %d eight-circuit links: %d links before, %d after'
      % (len(c['dissolved']), len(c['pass']), c['links_before'], c['links_after']))
    w('')
    w('One pass over the 8-circuit links, fewest signals first (riders count), ties by id; %s. A link dissolves where '
      'every one of its signals rides under way 1. The pass frees %d slots, %d connectors, %d latches and %d displaced '
      'footprints (%s).'
      % (c['order_rule'], f['slots'], f['connectors'], f['latches'], f['displaced_footprints'],
         ', '.join('%s %d' % kv for kv in f['displaced_footprints_per_board'].items()) or 'none'))
    w('')
    w('| Link | Signals at the start | Signals when tried | Dissolved |')
    w('| --- | --- | --- | --- |')
    for x in c['pass']:
        w('| %s | %d | %d | %s |' % (x['link'], x['signals'], x['signals_when_tried'], 'yes' if x['dissolved'] else 'no'))
    w('')
    rows = [(r['id'], x) for r in doc['links'] if r.get('gone') == 'dissolved (consolidation)' for x in r['riders_out']]
    w('Riders of the consolidation (%d): %s.' % (len(rows), '; '.join(
        '%s %s (%s, %s) to %s at %s mm' % (lid, x['net'], x['class'], x['site'], x['host'], _g(x['distance_mm']))
        for lid, x in rows)))
    w('')


def _disp_cells(s):
    k, f = s['K_displaced'], s['front_displaced']
    faces = k.get('faces', {})
    return {'K F.Cu': faces.get('F.Cu', k.get('F.Cu by slots')), 'K B.Cu': faces.get('B.Cu'),
            'fronts': ' / '.join('%s %s' % (b, _g(v)) for b, v in f.items())}


def _totals(w, doc):
    s, s1, a = doc['summary'], doc['part_1'], doc.get('part_2_of_a7') or {}
    w('## Against part 1 and a7 part 2: %d links (%d, %s), %d slots (%d, %s), %d signals on links (%d, %s)'
      % (s['links'], s1['links'], _g(a.get('links')), s['slots'], s1['slots'], _g(a.get('slots', a.get('placed'))),
         s['signals_on_placed_links'], s1['signals_on_placed_links'], _g(a.get('signals_on_placed_links'))))
    w('')
    w('Courtyard-level counts on unvalidated drafts; no count is a minimum.')
    w('')
    w('| Total | Part 2 (this record) | Part 1 | a7 part 2 |')
    w('| --- | --- | --- | --- |')

    def sp(x):
        return '%s / %s / %s / %s' % tuple(_g(x.get(k)) for k in ('ICs', 'resistors', 'capacitors', 'other')) if x else '-'
    d, d1 = _disp_cells(s), _disp_cells(s1)
    rows = [
        ('Links', s['links'], s1['links'], a.get('links')),
        ('Without a place', s['unplaced'], s1['unplaced'], a.get('unplaced')),
        ('Slots', s['slots'], s1['slots'], a.get('placed')),
        ('Connectors', s['connectors'], s1['connectors'], 2 * a['placed'] if a.get('placed') is not None else None),
        ('Latches', s['latches'], s1['latches'], 2 * a['placed'] if a.get('placed') is not None else None),
        ('Signals on placed links (of %d)' % doc['signals']['total'], s['signals_on_placed_links'],
         s1['signals_on_placed_links'], a.get('signals_on_placed_links')),
        ('of which on riders', s['signals_on_riders'], s1.get('signals_on_riders', 0), None),
        ('Grounds', s['grounds'], s1['grounds'], a.get('grounds')),
        ('Unused positions', s['unused_positions'], s1['unused_positions'], a.get('unused_positions')),
        ('K footprints displaced', s['K_displaced']['total'], s1['K_displaced']['total'], (a.get('K_displaced') or {}).get('total')),
        ('K F.Cu / K B.Cu', '%s / %s' % (_g(d['K F.Cu']), _g(d['K B.Cu'])), '%s / %s' % (_g(d1['K F.Cu']), _g(d1['K B.Cu'])), None),
        ('K ICs / resistors / capacitors / other', sp(s['K_displaced']['split']), sp(s1['K_displaced']['split']),
         sp((a.get('K_displaced') or {}).get('split'))),
        ('Front boards (rear face)', d['fronts'], d1['fronts'], None),
        ('Front ICs / resistors / capacitors / other', sp(s['front_displaced_split']), sp(s1['front_displaced_split']), None),
        ('Front tails over panel hardware', s['front_tails_over_panel_hardware'], s1['front_tails_over_panel_hardware'],
         a.get('front_tails_over_panel_hardware')),
        ('Leads to cut', s['trim_leads'], s1['trim_leads'], a.get('trim_leads')),
        ('Lengthened tails', s['lengthened_tails'], s1['lengthened_tails'], a.get('lengthened_tails')),
        ('Cable needed mm (range)', _rng(s['cable_needed_mm']), _rng(s1['cable_needed_mm']), None),
        ('Loop mm (range; cable length less cable needed)', _rng(s['loop_mm']), _rng(s1['loop_mm']), None),
        ('Links needing more than their cable', s['links_over_cable_length'], s1['links_over_cable_length'], None),
    ]
    for name, v, v1, o in rows:
        w('| %s | %s | %s | %s |' % (name, _g(v), _g(v1), _g(o) if o is not None else '-'))
    w('')


def _replacement(w, doc):
    rp = doc['replacement']
    t, rows, par = rp['totals'], rp['footprints'], rp['parameters']
    found = [r for r in rows if r['step'] != 'no position']
    w('## %d of %d displaced footprints find a position in the cumulative search; %d have none'
      % (len(found), len(rows), len(t['without_a_position'])))
    w('')
    pat = par['search_pattern']['value']
    w('Scope: every displaced footprint of the final record on K, JL, JR, P and the adapters (under a field or a slot, '
      'the latch neighbours of DS-88) and the part moves of the active fixings (EL parts are outside the scope). '
      'Order of DS-97: the sensitive packages, the other ICs, everything else, larger courtyard first, ties by '
      'reference. Steps: %s; U4215, U4226 and U208 start at step 3; the smallest shift wins within a step; a 90 degree '
      'turn only where no position exists without it. Pattern: rings of %s mm in %d directions (%s). Courtyard gap %s mm '
      '(%s). Edge margin %s mm (%s). Face change: %s (%s). Obstacles: the fields, slots, tails and latch margins of every '
      'link, the keep-outs of the active fixings, panel hardware, holes, tabs and the board outline, the footprints that '
      'stay and the footprints already re-placed.'
      % ('; '.join('%d within %s mm on %s' % (x['step'], _g(x['max_mm']), x['faces']) for x in par['steps']['value']),
         _g(pat['step_mm']), pat['directions'], par['search_pattern']['status'], _g(par['courtyard_gap_mm']['value']),
         par['courtyard_gap_mm']['status'], _g(par['edge_margin_mm']['value']), par['edge_margin_mm']['status'],
         par['face_change']['value'], par['face_change']['status']))
    w('')
    w('| Board and face | Displaced | Step 1 | Step 2 | Step 3 | No position | Turned |')
    w('| --- | --- | --- | --- | --- | --- | --- |')
    for k, e in t['per_board_face'].items():
        w('| %s | %d | %d | %d | %d | %d | %d |' % (k, e['displaced'], e['step 1'], e['step 2'], e['step 3'],
                                                   e['no position'], e['turned']))
    w('')
    w('| Class | Displaced | Step 1 | Step 2 | Step 3 | No position |')
    w('| --- | --- | --- | --- | --- | --- |')
    for k, e in t['per_class'].items():
        w('| %s | %d | %d | %d | %d | %d |' % (k, e['displaced'], e['step 1'], e['step 2'], e['step 3'], e['no position']))
    w('')
    if t['without_a_position']:
        w('Without a position (listed, not forced): %s.' % ', '.join(
            '%s %s (%s)' % (x['board'], x['ref'], x['package']) for x in t['without_a_position']))
        w('')
    w('Every footprint with board, face, package, old and new place, shift, step and turn: `replacement.footprints` of '
      '`link-gate.json`; the displaced IC packages of K at the floorplan reference point: `displaced_k_ic_packages`.')
    w('')


def _mv(m):
    if m['new'] is None:
        return '%s: no position' % m['ref']
    return '%s %s %s -> %s %s (%s mm, step %s%s)' % (m['ref'], _xy(m['old']), m['face'], _xy(m['new']), m['new_face'],
                                                    _g(m['moved_mm']), m['step'], ', turned' if m['turned'] else '')


def _ds97(w, doc):
    d = doc['ds97']
    n = sum(len(v) for v in d['sensitive_by_function'].values())
    w('## DS-97 for the gate: %d sensitive packages displaced, %s without a position; %d trimmers displaced'
      % (n, len(d['sensitive_without_a_position']) or 'none', len(d['trimmers'])))
    w('')
    w('| Function | Moves (old -> new, shift, step) |')
    w('| --- | --- |')
    for fn, ms in d['sensitive_by_function'].items():
        w('| %s | %s |' % (fn, '; '.join(_mv(m) for m in ms)))
    w('')
    w('Displaced packages: %s.' % ', '.join('%s %d' % kv for kv in d['displaced_counts'].items()))
    w('')
    w('Trimmers: %s.' % ('; '.join(_mv(m) for m in d['trimmers']) or 'none'))
    w('')
    if d['sensitive_without_a_position']:
        w('Sensitive packages without a position: %s.' % ', '.join(d['sensitive_without_a_position']))
        w('')


def _leads(w, doc):
    pl = [r for r in _live(doc) if r['placed']]
    per = {}
    for r in pl:
        for x in r['trim_leads']:
            per.setdefault(r['front_board'], set()).add(x)
    w('## %d parts and pads under a front tail have their leads cut to %s mm: %s'
      % (sum(len(v) for v in per.values()), _g(doc['parameters']['trim_to_mm']),
         ', '.join('%s %d' % (b, len(v)) for b, v in sorted(per.items())) or 'none'))
    w('')
    for b, v in sorted(per.items()):
        w('- %s: %s.' % (b, ', '.join(sorted(v))))
    w('')


def _compliance(w, doc):
    c = doc['summary']['compliance']
    pl = {r['id']: r for r in _live(doc) if r['placed']}
    w('## %d connectors above %s mm/N, none above %s mm/N' % (len(c['links_above_list']), _g(c['list_above_mm_per_N']),
                                                              _g(c['limit_mm_per_N']))
      if not c['links_above_limit'] else '## %d connectors above the limit' % len(c['links_above_limit']))
    w('')
    w('Value of the K connector of each link on the compliance map of ST-03: %s.' % (', '.join(
        '%s %s' % (x, _g(pl[x]['compliance_mm_per_N'])) for x in c['links_above_list']) or 'none'))
    w('')


def _lengthened(w, doc):
    pl = [r for r in _live(doc) if r['placed'] and r['lengthened_tail']]
    w('## %d links have a lengthened tail' % len(pl))
    w('')
    w('Front / K extension mm per link: %s.' % (', '.join('%s %s / %s' % (r['id'], _g(r['geometry']['front_extension_mm']),
                                                                         _g(r['geometry']['K_extension_mm'])) for r in pl) or 'none'))
    w('')


def _owner(w, doc):
    s = doc['summary']
    rp = doc['replacement']['totals']
    t = rp['per_class']
    w('## Figures for the owner: %d links, %d cables, %d connectors, %d latches to close'
      % (s['links'], s['slots'], s['connectors'], s['latches']))
    w('')
    w('| Figure | Value |')
    w('| --- | --- |')
    w('| Links | %d |' % s['links'])
    w('| Cables | %d (%s) |' % (s['slots'], ', '.join('%s %d' % kv for kv in _cables(doc).items())))
    w('| Connectors | %d |' % s['connectors'])
    w('| Latches to close | %d |' % s['latches'])
    for k, e in t.items():
        w('| Displaced %s | %d: step 1 %d, step 2 %d, step 3 %d, no position %d |'
          % (k, e['displaced'], e['step 1'], e['step 2'], e['step 3'], e['no position']))
    w('| Parts with leads to cut | %d |' % len({x for r in _live(doc) if r['placed'] for x in r['trim_leads']}))
    w('')


def _cables(doc):
    out = {}
    for r in _live(doc):
        if r['placed']:
            k = '%s %s mm' % (r['cable'], _g(r['cable_length_mm']))
            out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def _handover(w, doc):
    w('## Hand-overs: where ST-04, ST-08, ST-07 and ST-05 read')
    w('')
    w('- ST-04 part 2: per link of `links` without `gone`: `positions` (each signal with `class`, a rider marked '
      '`rider_from`), `riders_in` (signal, class, site, from, distance), `cable`, `cable_length_mm`, '
      '`cable_needed_mm`, `loop_mm` and the field positions `geometry.front_connector` and `geometry.K_connector`.')
    w('- ST-08 part 2: per link `front_board`, `slot_centre`, `direction`, `geometry.slot`, `geometry.front_tail`, '
      '`geometry.K_tail` and the tail extensions, `trim_leads` (leads to cut), `compliance_mm_per_N` and '
      '`summary.compliance.links_above_list` (connectors above 0.25 mm/N).')
    w('- ST-07: the keep-outs on K\'s rear face are `geometry.K_connector` (with the latch margin '
      '`parameters.latch_margin_mm`), `geometry.K_tail` and `geometry.slot` of every link, and `fixings.keepouts`; the '
      'displaced trimmers with their new places are `ds97.trimmers`, every footprint in `replacement.footprints`.')
    w('- ST-05: `displaced_k_ic_packages` (ref, symbol, old and new place and side, moved_mm, step) and the link '
      'figures of `summary` (links, slots, connectors, latches, signals, grounds, unused positions). The list holds '
      'no rotation: a 90 degree turn is held in `turned` of `replacement.footprints`. The new reference point is the '
      'old one plus the shift, because the turn is made about the footprint origin, which is the reference point of '
      'the floorplan for every turned package of the record.')
    w('- A link that left the record carries `gone` and `riders_out`; a dissolved link keeps its old geometry for '
      'reference only.')
    w('')
