"""README of the fixing list (ST-08 a1 part 1), rendered from fixing-sites.json only."""


def f1(v):
    return '-' if v is None else '%.1f' % v


def f2(v):
    return '-' if v is None else '%.2f' % v


def xy(p):
    return '(%g, %g)' % (p[0], p[1])


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join('---' for _ in head) + ' |']
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def render(doc):
    fx = doc['fixings']
    by = {f['id']: f for f in fx}
    sleeves = [f for f in fx if f['kind'] != 'post']
    kept = [f for f in fx if f['kind'] == 'sleeve kept']
    added = [f for f in fx if f['kind'] == 'sleeve added']
    dropped = [f for f in fx if f['kind'] == 'sleeve dropped']
    cov = doc['coverage']
    cnt = doc['counts']
    sel = doc['selection']
    t1, t2 = sel['tier1_stated_set'], sel['tier2_grid_screen']
    prm = doc['parameters']
    hw_dropped = [f for f in dropped if f['status'].startswith('dropped: site conflicts')]
    beyond = cov['beyond_rule']['clusters']
    L = []
    a = L.append
    a('# Fixing list of the flat-link stack (ST-08 attempt a1, part 1)')
    a('')
    a('Task `%s`, ruling DS-66 (`reviews/da-03.md`, Continuation c1, G8). **Status: generated paper list on '
      'unvalidated drafts.** Every figure is a courtyard-level screen of the board files; nothing is a copper '
      'clearance, a DRC, a fit, a strength or a strain result, and nothing is adopted. Coordinates are in the panel '
      'frame (`placements.lock.json`: origin at the panel\'s top-left, y down); K and the front boards share it, and '
      'the KiCad file coordinates add (100, 50).' % doc['task'])
    a('')
    a('- [`fixing-sites.json`](fixing-sites.json): every fixing of K with kind, coordinates, boards, keep-out radii, '
      'part moves and status, the screened candidates, the selection and its alternatives, and the SHA256 of every input.')
    a('- `scripts/stack/fixings/fixings.py` writes both files; `fixings_check.py` is the checker; '
      '`test_fixings.py` holds the tests (`python3 scripts/checks/frozen_studies.py discover scripts/stack/fixings`).')
    a('')
    a('Regenerate with `%s`; `--check` fails when a retained file differs from a fresh run.' % doc['provenance']['regenerate'])
    a('')

    if doc['verdict'] == 'NEEDS_DESIGN':
        c0 = max(beyond, key=lambda c: c['farthest_mm'])
        a('## NEEDS_DESIGN: no site list meets both rules without moving locked panel hardware; the best reaches %.1f mm, not 90 mm'
          % cov['after'][0])
        a('')
        a('The 70 mm rule is met everywhere. The 90 mm rule fails at %d grid nodes in %d clusters; the worst is %s, '
          '%.2f mm from a fixing. No node of the 1 mm site screen within 90 mm of it is clear of locked panel hardware '
          'on P. %d of the four P-side sleeve sites of DS-45 stand on locked pots themselves. '
          'No selection from the clear nodes of the screen can do better than %.2f mm.'
          % (cov['beyond_rule']['nodes'], len(beyond), xy(c0['at']), c0['farthest_mm'], len(hw_dropped),
             cov['lower_bound_any_selection'][0]))
    else:
        a('## DONE: both rules hold; no point of K is farther than %.1f mm from a fixing' % cov['after'][0])
    a('')
    a(table(['Result', 'Value'], [
        ['Sleeve sites that go', '%d of 12: %s' % (len(dropped), ', '.join(f['id'] for f in dropped))],
        ['Sleeve sites kept', ', '.join('%s %s' % (f['id'], xy(f['xy'])) for f in kept)],
        ['Sleeve sites added', ', '.join('%s %s on %s' % (f['id'], xy(f['xy']), f['front_board']) for f in added)],
        ['Farthest point of K from a fixing, 18 posts only', '%.1f mm at %s' % (cov['posts_only'][0], xy(cov['posts_only'][1]))],
        ['Farthest point, the 30 present fixings', '%.1f mm at %s' % (cov['present_30'][0], xy(cov['present_30'][1]))],
        ['Farthest point, this list', '%.1f mm at %s' % (cov['after'][0], xy(cov['after'][1]))],
        ['Sleeves per length', '%d long (19.0 mm gap), %d short (17.0 mm gap)' % (cnt['long_19'], cnt['short_17'])],
        ['Delivered plate (%d long, %d short)' % (cnt['plate']['long'], cnt['plate']['short']),
         'covers the list' if cnt['plate_covers'] else 'does not cover the list'],
        ['Checker findings on the retained list', '; '.join('[%s] %s' % tuple(e) for e in doc['checker_findings']) or 'none'],
    ]))
    a('')

    # item 1
    close = [i for i in doc['inventory'] if i['kind'] == 'sleeve' and i['nearest_other_fixing']['distance_mm'] < 70]
    a('## Inventory: 18 posts and 12 sleeve sites; %d sleeve sites stand within 70 mm of another present fixing' % len(close))
    a('')
    a('Posts from `design/stack/power-posts/joint-design.json` (the DS-44 lands govern; `stack-candidate.json` still '
      'holds the four JR lands 0.5 mm off). Sleeve sites from `stack-candidate.json` `fixings` (kind "kept support"). '
      'The front-board coordinates equal the K coordinates for every fixing. Nearest other fixing among the 30.')
    a('')
    a(table(['Fixing', 'Kind', 'On K and on the front board', 'Front board', 'Gap, mm', 'Nearest other fixing', 'mm'],
            [[i['id'], i['kind'], xy(i['xy']), i['front_board'], f1(i['gap_mm']), i['nearest_other_fixing']['id'],
              f2(i['nearest_other_fixing']['distance_mm'])] for i in doc['inventory']]))
    a('')

    # item 2
    a('## 70 mm rule: %d of the 12 sleeve sites go; %s stay' % (len(dropped), ' and '.join(f['id'] for f in kept)))
    a('')
    a('The four named sites go by DS-66. A given site that stands on locked panel hardware or on a fixed hole cannot '
      'be kept, because no jack, pot, switch or LED moves; this removes %s. The panel-side test is ST-04\'s: the '
      'locked courtyard against the %.1f mm radius of an M3 head without washer, and the locked part\'s rear-face pads '
      'against the %.2f mm keep-out (DS-44 accepted the same screen at the JR lands).'
      % (', '.join(f['id'] for f in hw_dropped) or 'none', prm['panel_head_radius_mm']['value'],
         prm['keepout_radius_front_mm']['value']))
    a('')
    a(table(['Site', 'Kind', 'Status', 'Nearest other fixing of this list', 'mm'],
            [[f['id'], f['kind'], f['status'], f['nearest_other_fixing']['id'], f2(f['nearest_other_fixing']['distance_mm'])]
             for f in sleeves if f['kind'] != 'sleeve added']))
    a('')
    alt = sel['pair_alternatives']
    a('The pair choice comes from the coverage of item 3: with each member forced, the smallest list needs')
    a('')
    a(table(['Pair', 'Member kept', 'Added sites needed', 'Farthest point, mm'],
            [[' / '.join(r['pair']), r['kept'], '-' if r['added_sites'] is None else r['added_sites'], f2(r['farthest_mm'])]
             for r in alt]))
    a('')
    pk = {tuple(r['pair']) for r in alt}
    if ('K-SUP-5', 'K-SUP-7') not in pk:
        a('K-SUP-5 and K-SUP-7 both stand on locked pots, so neither member of that pair can stay.')
        a('')
    for pr in sorted(pk):
        rs = [r for r in alt if tuple(r['pair']) == pr]
        best = min(rs, key=lambda r: (r['added_sites'] is None, r['added_sites'] or 0))
        other = [r for r in rs if r is not best]
        if other:
            a('- %s stays: %s added sites against %s with %s.' % (best['kept'], best['added_sites'],
                                                             other[0]['added_sites'], other[0]['kept']))
    a('')

    # item 3
    a('## Coverage: %d added sites bring the farthest point from %.1f to %.1f mm; %s' % (
        len(added), cov['present_30'][0], cov['after'][0],
        '90 mm is met' if cov['rule_met'] else '90 mm is missed at %d clusters' % len(beyond)))
    a('')
    a(table(['Added site', 'On K and on the front board', 'Front board', 'Boards pierced', 'Sleeve', 'Nearest other fixing',
             'mm', 'Clearance to the nearest board edge, mm', 'Candidate'],
            [[f['id'], xy(f['xy']), f['front_board'], ', '.join(f['boards']), '%s mm gap' % f['length_class'],
              f['nearest_other_fixing']['id'], f2(f['nearest_other_fixing']['distance_mm']), f2(f['edge_distance_mm']),
              f['candidate']] for f in added]))
    a('')
    a('- **Candidates.** First the stated set: the five provisional sites of the rigid design and the %d clear sites '
      'of `stack-candidate.json`, %d candidates in all, of which %d pass the screen; %s. ' % (
          t1['candidates'] - 5, t1['candidates'], t1['usable'],
          'they meet both rules' if t1['feasible'] else 'they cannot meet the 90 mm rule') +
      ('Then a screen of K on a %.1f mm grid with the same rules: %d clear nodes, thinned to %d candidates at %.1f mm.'
       % (t2['grid_mm'], t2['clear_nodes'], t2['candidates'], t2['thin_mm']) if t2 else ''))
    a('- **Screen.** A site needs a facing front board; the sleeve (r %.1f mm) plus %.1f mm inside K, the front board '
      'and EL where it lies under EL; clear of the tabs, the adapters O1, O3 and O5, the kept selectors and the sub '
      'toggles by %.2f mm; no locked panel hardware or fixed hole in its keep-out; at least %.0f mm from every post.'
      % (prm['sleeve_outer_diameter_mm']['value'] / 2, prm['board_edge_margin_mm']['value'],
         prm['keepout_radius_front_mm']['value'], prm['sleeve_min_spacing_mm']['value']))
    a('- **Method.** ' + sel['method'] + '. Where 90 mm cannot be met, nodes that no candidate reaches within 90 mm '
      'must be reached within the smallest radius that is feasible (%s mm, in 0.5 mm steps); every other node keeps '
      '90 mm.' % (f1(cov['best_reachable_mm']) if cov['best_reachable_mm'] else '-'))
    a('- **Minimality.** The count is the minimum for the screened candidate set on the 1 mm coverage grid. A site '
      'off the candidate grid could do better by an unknown amount; no continuous search was run (NOT RUN). A point '
      'between grid nodes lies at most 0.71 mm farther than its nearest node.')
    a('')
    a(table(['Fixings', 'Farthest point of K, mm', 'At'],
            [['18 posts only', f2(cov['posts_only'][0]), xy(cov['posts_only'][1])],
             ['18 posts and the 12 present sleeves', f2(cov['present_30'][0]), xy(cov['present_30'][1])],
             ['this list', f2(cov['after'][0]), xy(cov['after'][1])],
             ['lower bound, any selection from all clear nodes of the screen', f2(cov['lower_bound_any_selection'][0]),
              xy(cov['lower_bound_any_selection'][1])]]))
    a('')
    if beyond:
        a('Grid nodes beyond 90 mm, grouped:')
        a('')
        a(table(['Region of K (x0, y0, x1, y1)', 'Nodes', 'Farthest node', 'mm'],
                [['(%g, %g, %g, %g)' % tuple(c['box']), c['nodes'], xy(c['at']), f2(c['farthest_mm'])] for c in beyond]))
        a('')
        a('Both clusters lie at K\'s left edge, in front of the pot field of P: the grid screen finds no clear site '
          'within 90 mm of them. The corner cluster misses by under 1 mm and may close on a finer '
          'candidate grid than 1 mm (NOT RUN). Ways out are design decisions, not taken here: a site in the pot field '
          'with a smaller head or a front-side nut, a fixing through the adapter region, a K fixing to the enclosure, '
          'or a relaxed 90 mm figure at the left edge.')
        a('')
    a(table(['Sleeve length', 'Needed', 'On the delivered plate', 'Covered'],
            [['18.8 mm (19.0 mm gap: JL, JR)', cnt['long_19'], cnt['plate']['long'], 'yes' if cnt['long_19'] <= cnt['plate']['long'] else 'no'],
             ['16.8 mm (17.0 mm gap: P)', cnt['short_17'], cnt['plate']['short'], 'yes' if cnt['short_17'] <= cnt['plate']['short'] else 'no']]))
    a('')

    # item 4
    nofree = [(f['id'], m) for f in added for m in f['part_moves'] if m['class'] == 'movable' and m['nearest_free_origin'] is None]
    a('## Part moves: the %d added sites put %d footprints in their keep-outs; %d have no free position within 12 mm'
      % (len(added), sum(len(f['part_moves']) for f in added), len(nofree)))
    a('')
    a('Method of ST-04 (`design/stack/power-posts/envelopes.json`): courtyard box (pad box when none) against the '
      'keep-out circle, r %.2f mm on K and r %.2f mm on a front board or EL, both faces; the nearest free position is '
      'the smallest shift (0.25 mm steps, 24 directions, up to 12 mm) that clears every fixing of this list, every '
      'other footprint on its faces and the outline by 0.3 mm. No locked part is in any added keep-out. A footprint '
      'with no free position needs a hand placement. GH harness headers that a flat link replaces are not listed; '
      'the room study places the links around these keep-outs.' % (
          prm['keepout_radius_K_mm']['value'], prm['keepout_radius_front_mm']['value']))
    a('')
    rows = []
    for f in added + kept:
        for m in f['part_moves']:
            rows.append([f['id'], m['board'], m['ref'], m['lib'], m['class'], f2(m['distance_mm']), xy(m['origin']),
                         '-' if m['nearest_free_origin'] is None else xy(m['nearest_free_origin']),
                         'none within 12 mm' if m['nearest_free_shift_mm'] is None and m['class'] == 'movable'
                         else ('locked, outside the panel-side and pad test' if m['class'] != 'movable' else f2(m['nearest_free_shift_mm']))])
    a(table(['Site', 'Board', 'Reference', 'Footprint', 'Class', 'Courtyard from centre, mm', 'Origin',
             'Nearest free origin', 'Shift, mm'], rows))
    a('')
    a('Kept sites are listed too. They are given positions of DS-45 and keep their %.1f mm distance to the board '
      'edge: the 7.0 mm sleeve overhangs K and the front board there by %.1f mm, an open item for the design authority.'
      % (min(f['edge_distance_mm'] for f in kept) if kept else 0,
         (prm['sleeve_outer_diameter_mm']['value'] / 2 - min(f['edge_distance_mm'] for f in kept)) if kept else 0))
    a('')

    # item 5
    cer = [(f, m) for f in fx if f['kind'] != 'sleeve dropped' for m in f.get('part_moves', [])
           if m['ceramic_0805_or_larger_within_5mm']]
    a('## Ceramics: %d ceramic part of 0805 or larger within 5 mm of a fixing%s' % (
        len(cer), ' (%s)' % ', '.join('%s at %s' % (m['ref'], f['id']) for f, m in cer) if cer else ''))
    a('')
    a('Screened at every post and every kept or added sleeve, on every board the fixing pierces, from the fixing '
      'centre to the courtyard. Ceramic identity is ASSUMED from a C reference on a chip footprint; the dielectric '
      'comes from the value text where it names one, otherwise it is unknown.')
    a('')
    if cer:
        a(table(['Fixing', 'Board', 'Reference', 'Case', 'Value', 'mm', 'Nearest free origin beyond 5 mm', 'Shift, mm'],
                [[f['id'], m['board'], m['ref'], m['lib'], m['value'], f2(m['distance_mm']),
                  '-' if m['nearest_free_origin'] is None else xy(m['nearest_free_origin']), f2(m['nearest_free_shift_mm'])]
                 for f, m in cer]))
        a('')

    # item 6
    a('## Screw lengths stay UNSOURCED: the grip is %s mm, but no washer, nut or protrusion figure is retained'
      % ' / '.join('%.1f' % s['grip_mm'] for s in doc['screws'][:2]))
    a('')
    a(table(['Site class', 'Front board, mm', 'Gap (posts set it), mm', 'K, mm', 'Grip, mm', 'Washer', 'Nut',
             'Protrusion', 'Length', 'Grip source'],
            [[s['class'], f1(s['front_board_mm']), f1(s['gap_mm']), f1(s['K_mm']), f1(s['grip_mm']), s['washer_mm'],
              s['nut_mm'], s['protrusion_mm'], s['length'], s['grip_source']] for s in doc['screws']]))
    a('')
    a('Post screws are outside this list: the Harwin posts are M3 through-tapped (ST-04), and their engagement length '
      'is UNSOURCED as well.')
    a('')

    # item 7
    a('## Interface: `fixing-sites.json` lists all %d fixings of K with their keep-outs, %d of them active' % (
        len(fx), len(fx) - len(dropped)))
    a('')
    a('Per fixing: `id`, `kind` (post, sleeve kept, sleeve added, sleeve dropped), `xy` on K and `front_xy` on the '
      'front board (panel frame), `K_kicad_xy` and `front_kicad_xy`, `front_board`, `boards` pierced, `gap_mm`, '
      '`keepout_radius_mm` per board, `part_moves` and `status`. The room study reads the active ones as link '
      'keep-outs, the mechanics study for its short pass on K, the manager for the spacer README.')
    a('')
    a(table(['Fixing', 'Kind', 'xy', 'Front board', 'Keep-out radius per board, mm'],
            [[f['id'], f['kind'], xy(f['xy']), f['front_board'],
              ', '.join('%s %.2f' % (b, r) for b, r in sorted(f['keepout_radius_mm'].items()))]
             for f in fx if f['kind'] != 'sleeve dropped']))
    a('')

    # item 8
    a('## Checker: five rules with one fault-injection test each; the retained list fails only the 90 mm rule'
      if [e[0] for e in doc['checker_findings']] == ['coverage'] else
      '## Checker: five rules with one fault-injection test each; the retained list has %d findings' % len(doc['checker_findings']))
    a('')
    a(table(['Rule', 'What the checker recomputes from the boards'], [
        ['spacing', 'no kept or added sleeve within 70 mm of another active fixing'],
        ['coverage', 'no node of the 1 mm grid over K\'s outline beyond 90 mm'],
        ['site', 'no sleeve on locked panel hardware, a fixed hole, a tab, an adapter, a kept selector or a sub toggle, or outside a board'],
        ['moves', 'every footprint in a sleeve keep-out and every ceramic of 0805 or larger within 5 mm of any fixing has a listed move, and each listed free position clears every keep-out'],
        ['stale', 'the SHA256 of every input and program file equals the provenance'],
    ]))
    a('')
    a('## NOT RUN: any fit, strength, strain or creep figure, any native KiCad check, a continuous site search')
    a('')
    a('- The strain and deflection of K on this list: the short pass of ST-03 (DS-67).')
    a('- Copper clearance, DRC and routing around the new holes: no KiCad was run; the screen is courtyard level.')
    a('- The flat links themselves are not on the boards yet; the room study places them around these keep-outs.')
    a('- UNSOURCED: washer thickness, nut height, thread protrusion, creep of the printed sleeve.')
    a('- ASSUMED: the sleeve keep-out radii equal to the post radii (`link-options.json`), ceramic identity from the footprint class.')
    a('')
    return '\n'.join(L)
