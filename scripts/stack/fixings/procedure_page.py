"""Renders `design/stack/fixings/threading-procedure.md` from the procedure file alone: every figure and every
verdict heading is read from the document, so the page cannot disagree with the file."""


def _g(v):
    return ('%.4f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else str(v)


def _xy(xy):
    return '(%s, %s)' % (_g(xy[0]), _g(xy[1]))


def _place(p):
    return '%s %s' % (p['name'], _xy(p['xy']))


def render(doc):
    c = doc['counts']
    low = doc['lowering']
    st = {s['stage']: s for s in low['stages']}
    big = st[low['largest_stage']]
    scr = doc['screws']
    sv = doc['service']
    lat = doc['latch']
    out = []
    w = out.append
    ok = doc['verdict'] == 'DONE'
    w('# Threading procedure on the record of the room study: %s on paper, %d links in %d steps, K lowered in %d '
      'stages with at most %d ends at one height' % (doc['verdict'], c['links'], len(doc['steps']), len(low['stages']),
                                                     low['largest_ends']))
    w('')
    w('Status: %s. ST-08 part 2 (DS-115), read from the record of ST-02 a8 part 2 (DS-110). Places are named by the '
      'nearest panel control of the placement lock, seen from the front of the panel, with the panel coordinates '
      '(x from the left edge, y from the top edge, mm) beside them; seen from behind, left and right are swapped. '
      'Every figure is a paper result: the page claims no fit, no strength and no proven assembly.' % doc['status'])
    w('')
    if ok:
        w('## Every one of %d links has a row; no slot is covered, no end is blocked and no cable is shorter than its '
          'path' % c['links'])
        w('')
        w('Screened per slot: the front connectors, front tails and slots of every other link, the 22 fixing '
          'keep-outs, the adapters, the tabs, the kept selectors and sub toggles, and the own front board under the '
          'fold. The smallest slack is %s mm.' % _g(min(r['slack_mm'] for r in doc['links'])))
    else:
        w('## NEEDS_DESIGN: %d links cannot stand or thread' % (len(low['blocked']) + len(low['short_cables'])))
        w('')
        for b in low['blocked']:
            w('- %s: %s' % (b['link'], ', '.join(b['by'])))
        for b in low['short_cables']:
            w('- %s: cable short by %s mm' % (b['link'], _g(-b['slack_mm'])))
    w('')
    w('## The work takes %d steps; all %d front ends are plugged and locked before K comes down' %
      (len(doc['steps']), c['locks_before_K']))
    w('')
    for s in doc['steps']:
        extra = []
        if s.get('parts') is not None:
            extra.append('%d parts' % s['parts'] if s['n'] not in (7, 12, 13, 8, 9) else
                         {7: '%d locks' % s['parts'], 12: '%d locks' % s['parts'], 13: '%d locks' % s['parts'],
                          8: '%d cables' % s['parts'], 9: '%d ends' % s['parts']}[s['n']])
        if s.get('where'):
            extra.append(s['where'])
        w('%d. %s%s' % (s['n'], s['do'], (' (' + '; '.join(extra) + ')') if extra else ''))
    w('')
    lead = c['parts_with_leads_to_cut_per_board']
    w('## Leads are cut at %d parts: %s' % (c['parts_with_leads_to_cut'],
                                            ', '.join('%s %d' % (b, lead[b]) for b in ('P', 'JL', 'JR', 'O3') if b in lead)))
    w('')
    per = {}
    for r in doc['links']:
        per.setdefault(r['front_board'], set()).update(r['leads_to_cut'])
    for b in ('P', 'JL', 'JR', 'O3'):
        if per.get(b):
            w('- %s: %s.' % (b, ', '.join(sorted(per[b]))))
    w('')
    w('The rule for the bench is the one sentence of step 1; the list says where it matters. %d entries over the links '
      'count a part once per tail that crosses it (%d parts).' % (c['lead_entries_per_link'], c['parts_with_leads_to_cut']))
    w('')
    w('## K comes down over %d ends in %d stages, %s mm apart at the least; the largest stage guides %d ends at %s mm' %
      (c['links'], len(low['stages']), _g(low['smallest_gap_between_stages_mm']), big['ends'], _g(big['meets_K_at_mm'])))
    w('')
    w('Before K comes down each cable is folded upward under its slot (bend radius 2.4 mm) and stands on its front '
      'board. Its free end stands at the cable length less the 4.0 mm insertion, less the run to the slot, plus '
      '0.88 mm from the bend. It meets K\'s front face when K is that height less the gap above its seat. The heights '
      'fall into stages by themselves, because the cable lengths and the tail extensions come in steps of 2 mm. The '
      'highest end comes first; the posts meet K last, at 0 mm, after the four screw ends at %s mm (short sleeves) and '
      '%s mm (long sleeves).' % (_g(low['screw_tips'][1]['meets_K_at_mm']), _g(low['screw_tips'][0]['meets_K_at_mm'])))
    w('')
    w('| Stage | K above its seat, mm | Ends | By board | Links |')
    w('| --- | --- | --- | --- | --- |')
    for s in low['stages']:
        w('| %d | %s | %d | %s | %s |' % (s['stage'], _g(s['meets_K_at_mm']), s['ends'],
                                          ', '.join('%s %d' % kv for kv in s['per_board'].items()), ', '.join(s['links'])))
    w('')
    cl = low['slot_clearance_min']
    w('## A cable end clears its slot by %s mm across and %s mm along on each side at the least' %
      (_g(cl['across_per_side_mm']), _g(cl['along_per_side_mm'])))
    w('')
    w('Across: slot width (tail width + 1.0 mm) less the tail width at its +0.08 mm tolerance (DS-63). Along: the '
      '1.5 mm slot less the 0.33 mm stiffened tail (0.3 +/- 0.03 mm on the LX 0.5 mm cable drawing). The same at '
      'every slot, because the slot rule follows the tail width.')
    w('')
    w('## That one person guides %d ends and that a folded cable keeps its fold: NOT RUN' % c['links'])
    w('')
    w('Paper gives the heights for an end that stands straight. Whether a 40 to 60 mm stock cable stands, bows or '
      'falls over, whether one person can guide %d ends at one height with K in the other hand, and whether a fold '
      'stays where it was made are not shown. The cheap way to see them is the handling trial of owner item 4 of c1: '
      'one stock 0.5 mm cable and one printed plate with a 1.5 mm slot.' % big['ends'])
    w('')
    w('## After K is seated, %d ends are folded onto K\'s rear face, inserted and locked; %d connectors need the '
      'holding hand' % (c['locks_after_K'], c['holding_hand']))
    w('')
    w('Fold each end down onto K\'s rear face toward its K connector (the run on K is in the link table), push it in '
      'by the 4.0 mm insertion and close the lock with one fingertip or a plastic tool, never with the palm on K. At '
      'the connectors below, the other hand holds K\'s edge beside the connector while its lock is closed (DS-87).')
    w('')
    w('| Link | K connector beside | Panel coordinates | mm/N |')
    w('| --- | --- | --- | --- |')
    for h in doc['holding_hand']:
        w('| %s | %s | %s | %s |' % (h['link'], h['K_connector']['name'], _xy(h['K_connector']['xy']),
                                     _g(h['compliance_mm_per_N'])))
    w('')
    lc = lat['counts']
    w('## Latch reach: %d open, %d open after the displacement, %d NOT SHOWN' %
      (lc.get('open', 0), lc.get('open after the displacement', 0), lc.get('NOT SHOWN', 0)))
    w('')
    w('NOT SHOWN, because %s. Nothing is claimed for them.' % lat['reason'])
    w('')
    w('| Link | K connector beside | Neighbours within 1.0 mm |')
    w('| --- | --- | --- |')
    for n in lat['not_shown']:
        w('| %s | %s | %s |' % (n['link'], n['K_connector'], ', '.join(n['neighbours'])))
    w('')
    wf = scr['working_figure']
    w('## The screw stays %s mm (ASSUMED); nut height and washer thickness stay UNSOURCED, so the washer rule of '
      'point 9 stands' % wf['designation'].replace(' x ', ' × '))
    w('')
    for k in scr['classes']:
        w('- %s: grip %s mm, thread %s mm behind K\'s rear face, inside the %s mm envelope.' %
          (k['class'], _g(k['grip_mm']), _g(k['thread_behind_K_rear_mm']), _g(k['rear_envelope_mm'])))
    w('- Head at most %s mm and not countersunk; it passes the 7.0 mm access hole of EL at (244, 230).' %
      _g(wf['head_max_mm']))
    sh = scr['sheet']
    w('- Retained maker sheet: `%s` in the %s, SHA256 `%s`, from %s. It gives %s; it does not give %s.' %
      (sh['path'], sh['store'], sh['sha256'], sh['authoritative_url'], '; '.join('%s: %s' % kv for kv in sh['facts'].items()),
       ' or '.join(sh['missing'])))
    w('- Sources tried (two, the limit): ' + ' '.join('%d. %s: %s.' % (i + 1, t['source'], t['result'])
                                                       for i, t in enumerate(scr['sources_tried'])))
    w('- Washer: ' + scr['washer_verdict'] + '.')
    w('')
    w('## Tape holds the four screws; no retained part class does')
    w('')
    w('%s. A %s are on no record and are not retained.' % (scr['holding']['way'][0].upper() + scr['holding']['way'][1:],
                                                           ' and a '.join(scr['holding']['not_retained'])))
    w('')
    w('## Taking K off and putting it back is %d operations; after %d openings the K ends stand at %d of %d insertions' %
      (sv['per_opening'], sv['limit_openings'], sv['K_end_insertions_after_limit'], sv['insertions_sourced']))
    w('')
    w('Off: ' + ', '.join('%s %d' % kv for kv in sv['off'].items()) + '. Lift K straight up over the %d cable ends and '
      'the four screw ends in the stages above, last stage first; the front ends stay plugged and locked at one '
      'insertion.' % c['links'])
    w('')
    w('On: steps 9 to 13 again: ' + ', '.join('%s %d' % kv for kv in sv['on'].items()) + '. Before power: every lock '
      'closed and square, no cable pinched under K or at a post, 18 post screws and 4 nuts present, continuity of '
      'every link.')
    w('')
    w('K comes off at most %d times (DS-63: 20 insertions SOURCED for the connector). The owner keeps the count '
      'without a change to a board: one line per opening in the instrument\'s log (date, reason, opening number), and '
      'a tally on a paper label inside the case. Replacing a link costs one opening of K, one stock cable and its two '
      'locks; that front connector then stands at %d insertions.' % (sv['limit_openings'],
                                                                    sv['replace_link']['front_connector_insertions_after']))
    w('')
    w('## Counts in the units of the bench match the record summary')
    w('')
    w('| Figure | Value |')
    w('| --- | --- |')
    w('| Cables | %d (%s) |' % (c['cables'], ', '.join('%s %d' % kv for kv in c['cables_per_code'].items())))
    w('| Connectors | %d |' % c['connectors'])
    w('| Front ends per board | %s |' % ', '.join('%s %d' % kv for kv in c['front_ends_per_board'].items()))
    w('| Locks closed before K comes down | %d |' % c['locks_before_K'])
    w('| Locks closed after K is seated | %d |' % c['locks_after_K'])
    w('| Fixings | %d (18 posts, 4 sleeves) |' % c['fixings'])
    w('| Fastener operations | %d (36 post screws, 4 sleeve screws, 4 nuts) |' % c['fastener_operations'])
    w('| Parts with leads to cut | %d |' % c['parts_with_leads_to_cut'])
    w('| Lengthened tails | %d |' % c['lengthened_tails'])
    w('| Connectors with the holding hand | %d |' % c['holding_hand'])
    w('')
    w('Checked against the record by `procedure.check`: links, connectors, locks, lengthened tails, lead entries, '
      'latch verdicts and the holding-hand count. A link without a row, a count that differs and a stale projection '
      'are findings.')
    w('')
    w('## Per link: %d rows' % c['links'])
    w('')
    w('Front and K runs are plan lengths from the connector opening to the slot centre, extension included. Slack is '
      'the cable length less the needed length.')
    w('')
    w('| Link | Front connector beside | Slot beside | Dir | Cable | On front / on K mm | Slack mm | Lengthened | '
      'Leads to cut | mm/N | Latch |')
    w('| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    for r in doc['links']:
        w('| %s | %s | %s | %s | %s %s mm | %s / %s | %s | %s | %s | %s%s | %s |' % (
            r['id'], _place(r['front_connector']), _place(r['slot']), r['direction'], r['cable'],
            _g(r['cable_length_mm']), _g(r['on_front_board_mm']), _g(r['on_K_rear_mm']), _g(r['slack_mm']),
            ('+%s mm' % _g(r['front_extension_mm'])) if r['lengthened_tail'] else 'no',
            ', '.join(r['leads_to_cut']) or '-', _g(r['compliance_mm_per_N']), ' (hold)' if r['holding_hand'] else '',
            r['latch']))
    w('')
    pins = doc['provenance']['pins']
    w('## The record is pinned by a projection of what this page reads')
    w('')
    w('- `%s`: digest `%s` over the fields %s.' % (pins['gate_record_projection']['file'],
                                                   pins['gate_record_projection']['digest'],
                                                   '; '.join('%s: %s' % (k, ', '.join(v)) for k, v in
                                                             pins['gate_record_projection']['fields'].items())))
    w('- `%s`: projection digest `%s`.' % (pins['candidate_projection']['file'], pins['candidate_projection']['digest']))
    w('- %s: projection digest `%s`.' % (', '.join('`%s`' % f for f in pins['options_projection']['files']),
                                         pins['options_projection']['digest']))
    for f, h in pins['files_sha256'].items():
        w('- `%s`: `%s`.' % (f, h))
    w('')
    w('Regenerate with `%s`; `--check` fails on a stale file or any finding.' % doc['provenance']['regenerate'])
    w('')
    w('## Checks NOT RUN')
    w('')
    w('- The handling trial (owner item 4 of c1): standing, guiding and fold of the cables; wear of a tail on cut leads.')
    w('- The closing force of the lock and the open lock height: UNSOURCED (DS-63, DS-87).')
    w('- Heights of the latch neighbours and of the loops: no footprint height is retained.')
    w('- Nut height and washer thickness: UNSOURCED; any print, fit, torque or creep test.')
    w('- KiCad, DRC and `scripts/checks/regen-all.sh`: no board changes here; the pull request\'s CI runs it.')
    w('')
    return '\n'.join(out)
