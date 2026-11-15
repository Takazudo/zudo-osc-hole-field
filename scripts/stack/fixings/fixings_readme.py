"""README of the ruled fixing list (ST-08 a2 part 1), rendered from fixing-sites.json only: every figure and every
verdict below is read from the file."""


def f2(v):
    return '-' if v is None else '%.2f' % v


def xy(p):
    return '(%g, %g)' % (p[0], p[1])


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join('---' for _ in head) + ' |']
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def same(a, b):
    return 'same' if a == b else 'differs'


def render(doc):
    fx = doc['fixings']
    sleeves = [f for f in fx if f['active'] and f['kind'] != 'post']
    dropped = [f for f in fx if not f['active']]
    cnt, parts, cov, scans = doc['counts'], doc['parts'], doc['coverage'], doc['region_scans']
    auth = doc['authority']
    prm = doc['parameters']
    L = []
    a = L.append
    a('# Fixing list of the flat-link stack as ruled (ST-08 attempt a2, part 1)')
    a('')
    a('Task `%s`. The list is the ruled input [`ruled-list.json`](ruled-list.json) (decision rows DS-72 to DS-76); this '
      'study checks it and does not choose it. **Status: generated paper check on unvalidated drafts.** Every figure is '
      'a courtyard-level count of the board files; nothing is a copper clearance, a DRC, a fit, a strength or a strain '
      'result, and nothing is adopted. Coordinates are in the panel frame of the placement lock, the same on K and on '
      'the front board; KiCad file coordinates add the lock\'s translation.' % doc['task'])
    a('')
    a('- [`fixing-sites.json`](fixing-sites.json): `fixings` (every fixing of K with `active`), `reserve`, '
      '`alternatives`, `access_holes`, `screw`, `region_scans`, `coverage` and the pins of every input.')
    a('- `scripts/stack/fixings/fixings.py` writes both files (`--check` fails on a stale file or on any checker '
      'finding); `fixings_check.py` is the checker; `test_fixings.py` holds the tests.')
    a('')
    if doc['verdict'] == 'DONE':
        a('## DONE: all %d ruled sleeves pass the hard screens' % len(sleeves))
    else:
        a('## NEEDS_DESIGN: %d findings on the ruled sleeves' % len(doc['ruled_findings']))
        a('')
        a(table(['Sleeve', 'Finding'], doc['ruled_findings']))
    a('')
    a(table(['Result', 'Value'], [
        ['Fixings of K', '%d: %d posts and %d sleeves (%d long, %d short)' % (cnt['fixings'], cnt['posts'], cnt['sleeves'], cnt['long_19'], cnt['short_17'])],
        ['Fastener operations', '%d (%d post screws, %d sleeve screws, %d nuts; %s)' % (
            cnt['fastener_operations']['total'], cnt['fastener_operations']['post_screws'],
            cnt['fastener_operations']['sleeve_screws'], cnt['fastener_operations']['sleeve_nuts'], cnt['fastener_operations']['basis'])],
        ['Delivered plate (%d long, %d short)' % (cnt['plate']['long'], cnt['plate']['short']), 'covers the list' if cnt['plate_covers'] else 'does not cover the list'],
        ['Dropped sites of DS-45', '%d, none active' % cnt['dropped']],
        ['Farthest point of K from a fixing', '%s mm at %s (posts only: %s mm at %s)' % (
            f2(cov['overall'][0]), xy(cov['overall'][1]), f2(cov['posts_only'][0]), xy(cov['posts_only'][1]))],
        ['Movement limit of DS-72', doc['movement_limit']['status']],
    ]))
    a('')

    a('## The ruled sleeves: %d pass, %d fail the panel-side, pad, hole, keep-out and 70 mm screens' % (
        sum(1 for s in sleeves if not s['findings']), sum(1 for s in sleeves if s['findings'])))
    a('')
    a(table(['Sleeve', 'xy', 'Front board', 'Boards pierced', 'Gap, mm', 'Nearest other fixing', 'mm',
             'Edge clearance, mm', 'Decision', 'Findings'],
            [[s['id'], xy(s['xy']), s['front_board'], ', '.join(s['boards']), s['gap_mm'], s['nearest_other_fixing']['id'],
              f2(s['nearest_other_fixing']['distance_mm']), f2(s['edge_distance_mm']), s['decision'],
              '; '.join(s['findings']) or 'none'] for s in sleeves]))
    a('')
    a('Reserve and alternatives, screened the same way against the list (an alternative in place of the sleeve it replaces):')
    a('')
    a(table(['Site', 'Role', 'xy', 'Decision', 'Nearest other fixing', 'mm', 'Displaced parts', 'Without a free position', 'Findings'],
            [[r['id'], r['kind'] + ('' if 'replaces' not in r else ' for ' + r['replaces']), xy(r['xy']), r['decision'],
              r['nearest_other_fixing']['id'], f2(r['nearest_other_fixing']['distance_mm']), len(r['part_moves']),
              ', '.join(m['ref'] for m in r['part_moves'] if m['nearest_free_origin'] is None) or 'none',
              '; '.join(r['findings']) or 'none'] for r in doc['reserve'] + doc['alternatives']]))
    a('')
    a('Dropped: ' + ', '.join('%s (%s)' % (f['id'], '; '.join(f['site_conflicts']) or 'no site conflict') for f in dropped) + '.')
    a('')

    a('## Parts in the sleeve keep-outs: %d movable footprints, %d without a free position within 12 mm, %d of them not assigned by a decision (authority: %d and %d)' % (
        parts['movable_in_sleeve_keepouts'], parts['without_free_position'], parts['without_free_position_not_decided'],
        auth['parts']['movable_in_sleeve_keepouts'], auth['parts']['without_free_position']))
    a('')
    a('Method of ST-04: courtyard box against the keep-out circle (r %.2f mm on K, r %.2f mm on a front board and on EL, '
      'both faces); the nearest free position is the smallest shift (0.25 mm steps, 24 directions, up to 12 mm) that '
      'clears every active fixing, every other footprint on its faces and the outline by 0.3 mm, tested at the rounded '
      'position that is retained.' % (prm['keepout_radius_K_mm']['value'], prm['keepout_radius_front_mm']['value']))
    a('')
    rows = []
    for f in [x for x in fx if x['active']]:
        for m in f.get('part_moves', []):
            rows.append([f['id'], m['board'], m['ref'], m['lib'], f2(m['distance_mm']), xy(m['origin']),
                         '-' if m['nearest_free_origin'] is None else xy(m['nearest_free_origin']),
                         f2(m['nearest_free_shift_mm']) if m['nearest_free_origin'] else m.get('decided_by', 'none within 12 mm'),
                         'yes' if m['ceramic_0805_or_larger_within_5mm'] else 'no'])
    a(table(['Fixing', 'Board', 'Reference', 'Footprint', 'Courtyard from centre, mm', 'Origin', 'Nearest free origin',
             'Shift, mm', 'Ceramic 0805+ within 5 mm'], rows))
    a('')
    for h in doc['access_holes']:
        a('**Access hole in %s at %s, %.1f mm (%s):** %s the %.2f mm keep-out already applied to %s at %s (centre offset %s mm), so it displaces nothing further.' % (
            h['board'], xy(h['xy']), h['diameter_mm'], h['decision'],
            'inside' if h['inside_applied_keepout'] else 'NOT inside', h['keepout_radius_mm'], h['board'], h['for'], f2(h['centre_offset_mm'])))
        a('')

    def cmp_row(name, mine, theirs):
        return [name, mine, theirs, 'not stated by the authority' if theirs == '-' else same(mine, theirs)]

    j, r, m, lr = scans['JL'], scans['JR'], scans['upper_middle'], scans['lower_right']
    aj, ar, am, alr = auth['scans']['JL'], auth['scans']['JR'], auth['scans']['upper_middle'], auth['scans']['lower_right']
    rows = [
        cmp_row('JL clear nodes (y 22 to 70)', j['clear'], aj['clear']),
        cmp_row('JL clear nodes, y 22 to 69', j['clear_without_last_row'], aj['clear']),
        cmp_row('JL nodes with a free position for every part', j['all_parts_free'], aj['all_parts_free']),
        cmp_row('JL columns of those nodes', j['columns_x_of_all_parts_free'], [float(v) for v in aj['columns_x']]),
        cmp_row('JR clear nodes', r['clear'], ar['clear']),
        cmp_row('JR nodes with a free position for every part', r['all_parts_free'], ar['all_parts_free']),
        cmp_row('JR those nodes', r['all_parts_free_nodes'], [[float(v) for v in p] for p in ar['all_parts_free_nodes']]),
        cmp_row('Upper middle clear nodes (x 120 to 200)', m['clear'], am['clear']),
        cmp_row('Upper middle nodes with no integrated circuit lacking a free position', m['without_an_ic_lacking_a_free_position'], am['without_an_ic_lacking_a_free_position']),
        cmp_row('Upper middle nodes with a free position for every part', m['all_parts_free'], 0),
        cmp_row('Lower right clear nodes', lr['clear'], alr['clear']),
        cmp_row('Lower right clear nodes, y 176 to 291', lr['clear_without_last_row'], alr['clear']),
        cmp_row('Lower right y range', lr['y_range'], [float(v) for v in alr['y_range']]),
        cmp_row('Lower right SOIC-14 without a free position per node', lr['soic14_without_free_position'], alr['soic14_without_free_position']),
        cmp_row('Lower right clear nodes 70 mm or more from every post', lr['clear_outside_70_mm_of_every_post'], '-'),
    ]
    for c in scans['corners']:
        rows.append(cmp_row('Corner %s: panel-side courtyard, mm' % xy(c['xy']),
                            [f['panel_face_courtyard_mm'] for f in c['fails']], [auth['scans']['corners']['jack_courtyard_mm']]))
    ndiff = sum(1 for x in rows if x[3] == 'differs' and x[2] != '-')
    a('## Region scans: %d of %d compared figures equal the authority\'s scratch runs; the differences are listed' % (
        sum(1 for x in rows if x[3] == 'same'), sum(1 for x in rows if x[2] != '-')) if ndiff else
      '## Region scans: every compared figure equals the authority\'s scratch runs')
    a('')
    a('Integer nodes of a 1 mm grid; a node is clear when it faces the named board, passes the edge, tab, adapter, '
      'selector and sub-toggle screens and has no locked hardware or fixed hole in its keep-out. Free positions are '
      'searched with the posts and the node as the only fixings. The node lists are in `region_scans`. A row named '
      '"y 22 to 69" or "y 176 to 291" counts the region without its last row, for comparison only.')
    a('')
    a(table(['Figure', 'This study', 'Authority (scratch run)', 'Comparison'], rows))
    a('')

    ab, be = cov['above_post_rows'], cov['below_post_rows']
    ma, mb = auth['coverage']['above_post_rows'], auth['coverage']['below_post_rows']
    a('## Distance screen (DS-72, no rule): farthest point %s mm above the post rows and %s mm below; %d and %d nodes beyond %g mm' % (
        f2(ab['farthest_mm']), f2(be['farthest_mm']), ab['nodes_beyond_screen'], be['nodes_beyond_screen'], cov['screen_mm']))
    a('')
    a(table(['Region', 'Farthest node', 'mm', 'Nodes beyond the screen', 'Manager\'s count'],
            [['above the post rows (y <= 160)', xy(ab['at']), f2(ab['farthest_mm']), ab['nodes_beyond_screen'],
              '%s mm at %s, %d nodes' % (f2(ma['farthest_mm']), xy(ma['at']), ma['nodes_beyond_90'])],
             ['below the post rows (y >= 175)', xy(be['at']), f2(be['farthest_mm']), be['nodes_beyond_screen'],
              '%s mm at %s, %d nodes' % (f2(mb['farthest_mm']), xy(mb['at']), mb['nodes_beyond_90'])]]))
    a('')
    a(table(['Region of K (x0, y0, x1, y1)', 'Side', 'Nodes', 'Farthest node', 'mm'],
            [['(%g, %g, %g, %g)' % tuple(c['box']), side, c['nodes'], xy(c['at']), f2(c['farthest_mm'])]
             for side, k in (('above', 'above_post_rows'), ('below', 'below_post_rows')) for c in cov[k]['clusters']]))
    a('')
    a(table(['Sleeve', 'Nearest post, mm', 'Manager'],
            [[k, f2(v), f2(auth['coverage']['nearest_post_mm'].get(k))] for k, v in cov['nearest_post_mm'].items()]))
    a('')
    a('The movement limit of DS-72 is ST-03\'s figure: %s.' % doc['movement_limit']['status'])
    a('')

    sc = doc['screw']
    a('## Screw: %s (%s) %s the head test and leaves the thread %s mm behind K\'s rear face, against a %s mm envelope' % (
        sc['working_figure']['designation'], sc['working_figure']['status'], 'passes' if sc['head_fits_panel_test'] else 'fails',
        ' and '.join(f2(c['thread_behind_K_rear_mm']) for c in sc['classes']), f2(sc['classes'][0]['rear_envelope_mm'])))
    a('')
    a(table(['Class', 'Grip, mm', 'Thread behind K, mm', 'Inside the envelope', 'Grip source'],
            [[c['class'], f2(c['grip_mm']), f2(c['thread_behind_K_rear_mm']), 'yes' if c['inside_envelope'] else 'no', c['grip_source']]
             for c in sc['classes']]))
    a('')
    a('Head at most %.1f mm, not countersunk, against the %.1f mm head radius of the panel-side test. Nut height and '
      'washer thickness: %s, %s.' % (sc['working_figure']['head_max_mm'], sc['head_against_panel_test_mm'],
                                     sc['nut_height_mm'], sc['washer_thickness_mm']))
    a('')

    a('## Interface: `fixings` keeps its keys; %d entries, %d active' % (len(fx), sum(1 for f in fx if f['active'])))
    a('')
    a('Keys with unchanged meaning: `id`, `kind`, `xy`, `front_xy`, `front_board`, `boards`, `gap_mm`, '
      '`keepout_radius_mm`, `length_class`; added: `active`. The ruled sleeves keep the kind `sleeve added`. The '
      'reserve, the alternatives, the access hole and the scans are top-level objects and never in `fixings`.')
    a('')
    a(table(['Fixing', 'Kind', 'Active', 'xy', 'Front board', 'Keep-out radius per board, mm'],
            [[f['id'], f['kind'], 'yes' if f['active'] else 'no', xy(f['xy']), f['front_board'],
              ', '.join('%s %.2f' % (b, v) for b, v in sorted(f['keepout_radius_mm'].items()))] for f in fx]))
    a('')
    pins = doc['provenance']['pins']
    a('## Pins: %d whole files, %d objects, %d decision rows and %d review section' % (
        len(pins['files_sha256']), len(pins['objects_sha256']), len(pins['decision_rows_sha256']), len(pins['review_sections_sha256'])))
    a('')
    a(table(['Pin', 'SHA256'], [[k, v] for g in ('decision_rows_sha256', 'review_sections_sha256', 'objects_sha256', 'files_sha256')
                                 for k, v in pins[g].items()]))
    a('')
    a('## NOT RUN: K\'s movement and strain on this list, native KiCad checks, any fit, strength or creep figure')
    a('')
    a('- The movement limit of DS-72 on this list: ST-03 attempt a6.')
    a('- Copper clearance, DRC and routing around the holes: no KiCad was run; the screen is courtyard level.')
    a('- The flat links are not on the boards; ST-02 attempt a8 reads `fixings` as its keep-out list.')
    a('- UNSOURCED: nut height, washer thickness, creep of the printed sleeve. ASSUMED: the screw figure, the sleeve '
      'keep-out radii equal to the post radii, ceramic identity from the footprint class.')
    a('')
    return '\n'.join(L)
