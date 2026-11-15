"""Threading procedure, screw operations and service steps on the record of the room study (ST-08 part 2;
DS-43, DS-63, DS-66, DS-67, DS-76, DS-87, DS-88, DS-110, DS-115).

Reads the gate record of ST-02 a8 part 2 (`design/stack/geometry/links/link-gate.json`, read only) and pins it by a
projection of the fields this script reads, not by the hash of the file. Writes
`design/stack/fixings/threading-procedure.json` and `design/stack/fixings/threading-procedure.md`.

A paper procedure on unvalidated drafts: no fit, no strength and no proven assembly. No KiCad.

  python3 scripts/stack/fixings/procedure.py           # write the JSON and the page
  python3 scripts/stack/fixings/procedure.py --check   # fail if a retained file differs or the checker finds anything
"""
import collections
import hashlib
import json
import math
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon, box

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

OUT_DIR = ROOT / 'design/stack/fixings'
PROC_JSON = OUT_DIR / 'threading-procedure.json'
PROC_MD = OUT_DIR / 'threading-procedure.md'
REGEN = 'python3 scripts/stack/fixings/procedure.py'

GATE = 'design/stack/geometry/links/link-gate.json'
CANDIDATE = 'design/stack/geometry/stack-candidate.json'
LINK_OPTIONS = 'design/stack/geometry/links/link-options.json'
FLEX_LINKS = 'design/stack/connectors/flex-links.json'
LOCK = 'design/grid/placements.lock.json'
SITES = 'design/stack/fixings/fixing-sites.json'
STORE_SHEET = {
    'store': 'circuit-dev-resources (private)',
    'path': 'keystone/4708/m60-section-8-washers-and-nuts-p132-frev1b1-11-2011-farnell-mirror.pdf',
    'sha256': '37571546d94c93793dae6cbbe894c1d28e34aee8e9ae76ab30f3897149c1a5a5',
    'authoritative_url': 'https://www.farnell.com/datasheets/1933945.pdf',
    'what': 'Keystone catalog M60 section 8 p.132 (FREV1B1_11-2011), washers and nuts, Farnell-hosted copy',
    'facts': {'M3 steel hex nut': 'cat. no. 4708, hex 5.50 mm, thread M3 (nylon: 4688)'},
    'missing': ['nut height', 'metric plain washer (the page lists fibre and nylon shoulder washers in inch sizes)'],
}
SOURCES_TRIED = [
    {'source': 'Keystone catalog page via farnell.com/datasheets/1933945.pdf', 'result':
     'HTTP 200, readable PDF of one page; retained. Gives the M3 hex of 5.50 mm, no nut height and no metric plain '
     'washer'},
    {'source': 'Bossard M6M M3 hex nut page on distrelec.nl', 'result':
     'HTTP 302 to a distributor home page; no sheet reached, nothing downloaded'},
]
WEB_SEARCHES = ['Keystone Electronics metric hex nut M3 datasheet pdf dimensions', 'keyelco.com 4708 hex nut M3 pdf',
                'M3 hex nut DIN 934 and M3 flat washer DIN 125 datasheet pdf manufacturer thickness 2.4 mm 0.5 mm']

FRONT_ORDER = ('JL', 'JR', 'P', 'O1', 'O3', 'O5')
CONTROL_KINDS = {'jack': 'jack', 'pot': 'pot', 'switch': 'switch', 'button': 'button', 'octave': 'selector'}
SERVICE_LIMIT = 10
GATE_OPTIONS = 'design/stack/geometry/links/link-gate-options.json'
# DS-63: stock cable width tolerance +/-0.08 mm (LX cable drawing); no retained field in the projected inputs
CABLE_WIDTH_TOL_MM = 0.08
# DS-63: 20 insertions SOURCED for the FH12 connector (catalogue in the private store); no retained field here
INSERTIONS_SOURCED = 20
EPS = 1e-9


def r3(v):
    return round(float(v) + 0.0, 3)


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def val(x):
    return x['value'] if isinstance(x, dict) and 'value' in x else x


# ---------------------------------------------------------------- inputs and their projection

LINK_FIELDS = ('id', 'front_board', 'size', 'circuits', 'cable', 'cable_length_mm', 'cable_needed_mm', 'loop_mm',
               'centre', 'slot_centre', 'direction', 'lengthened_tail', 'trim_leads', 'compliance_mm_per_N')
GEO_FIELDS = ('slot', 'front_connector', 'front_tail', 'K_tail', 'K_connector', 'a_mm', 'b_mm',
              'front_extension_mm', 'K_extension_mm')
SUMMARY_FIELDS = ('links', 'placed', 'slots', 'connectors', 'latches', 'lengthened_tails', 'trim_leads',
                  'loop_mm', 'links_over_cable_length', 'latch_verdicts', 'latch_not_shown', 'compliance')


def project_gate(gate):
    """The part of the gate record this procedure reads; its digest is the pin."""
    links = []
    for l in gate['links']:
        if 'gone' in l:
            continue
        row = {k: l[k] for k in LINK_FIELDS}
        row['geometry'] = {k: l['geometry'][k] for k in GEO_FIELDS}
        row['latch_reach'] = {'verdict': l['latch_reach']['verdict'], 'remaining': l['latch_reach']['remaining']}
        links.append(row)
    return {'links': links,
            'summary': {k: gate['summary'][k] for k in SUMMARY_FIELDS},
            'parameters': {k: gate['parameters'][k] for k in ('insertion_mm', 'bend_radius_mm', 'trim_to_mm',
                                                                'latch_margin_mm', 'compliance')},
            'fixings': gate['fixings']['keepouts'],
            'gone': sorted(l['id'] for l in gate['links'] if 'gone' in l)}


def project_candidate(cand):
    return {'stack': {k: cand['stack'][k] for k in ('K_face_z_mm', 'K_rear_z_mm', 'mated_heights_mm')},
            'planes': {k: {'outline': v['outline'], 'face_z_mm': v['face_z_mm'], 'rear_z_mm': v['rear_z_mm']}
                       for k, v in cand['planes'].items()},
            'tabs': [{'id': t['id'], 'rect': t['rect'], 'board': t['board']} for t in cand['tabs']],
            'selectors_kept': [{'ref': s['ref'], 'block': s['block'], 'courtyard': s['courtyard']}
                               for s in cand['selectors_kept']],
            'sub_toggles': [{'block': s['block'], 'toggle_courtyard': s['toggle_courtyard']}
                            for s in cand['sub_toggles']]}


def project_options(opts, lands):
    lx = lands['st01e']['cable_drawings']['lx_0_5mm']
    return {'slot_width_extra_mm': val(opts['slot']['width_extra_mm']), 'slot_length_mm': val(opts['slot']['length_mm']),
            'straight_stiffened_outside_mm': val(opts['cable']['straight_stiffened_outside_mm']),
            'cable_tail_thickness': lx['tail_thickness']}


def project_gate_options(gopts):
    return {'tail_step_mm': val(gopts['tail_lengthening']['step_mm'])}


def load_inputs(root=ROOT):
    root = Path(root)
    gate = json.loads((root / GATE).read_text())
    cand = json.loads((root / CANDIDATE).read_text())['candidate']
    opts = json.loads((root / LINK_OPTIONS).read_text())
    lands = json.loads((root / FLEX_LINKS).read_text())
    lock = json.loads((root / LOCK).read_text())
    sites = json.loads((root / SITES).read_text())
    gopts = json.loads((root / GATE_OPTIONS).read_text())
    o = project_options(opts, lands)
    o.update(project_gate_options(gopts))
    return {'gate': project_gate(gate), 'cand': project_candidate(cand), 'opts': o,
            'lock': lock, 'sites': sites, 'root': root}


def pins(inp):
    root = inp['root']
    return {
        'gate_record_projection': {'file': GATE, 'digest': digest(inp['gate']),
                                   'fields': {'links (without gone)': list(LINK_FIELDS) + ['geometry.' + g for g in GEO_FIELDS]
                                              + ['latch_reach.verdict', 'latch_reach.remaining'],
                                              'summary': list(SUMMARY_FIELDS),
                                              'parameters': ['insertion_mm', 'bend_radius_mm', 'trim_to_mm',
                                                             'latch_margin_mm', 'compliance'],
                                              'fixings': ['keepouts']}},
        'candidate_projection': {'file': CANDIDATE, 'digest': digest(inp['cand'])},
        'options_projection': {'files': [LINK_OPTIONS, FLEX_LINKS, GATE_OPTIONS], 'digest': digest(inp['opts'])},
        'files_sha256': {p: sha_file(root / p) for p in (LOCK, SITES, 'design/stack/fixings/ruled-list.json',
                                                          'scripts/stack/fixings/procedure.py',
                                                          'scripts/stack/fixings/procedure_page.py')},
    }


# ---------------------------------------------------------------- naming by the nearest panel control

class Namer:
    def __init__(self, lock):
        self.items = [p for p in lock['placements'] if p['kind'] in CONTROL_KINDS]

    def __call__(self, xy):
        best = min(self.items, key=lambda p: (math.hypot(p['x_mm'] - xy[0], p['y_mm'] - xy[1]), p['uid']))
        d = math.hypot(best['x_mm'] - xy[0], best['y_mm'] - xy[1])
        return {'name': 'the %s %s of %s' % (best['label'], CONTROL_KINDS[best['kind']], best['block']),
                'control_xy': [best['x_mm'], best['y_mm']], 'distance_mm': r3(d), 'xy': [r3(xy[0]), r3(xy[1])]}


def centre(rect):
    return [(rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2]


# ---------------------------------------------------------------- per link

def bend_term(R):
    """Height the quarter bend adds to an upright end: it rises R over a cable length of pi R / 2 and replaces R of
    straight run, so the end stands R (2 - pi / 2) higher than the length less the run."""
    return R * (2 - math.pi / 2)


def tail_thickness_max(opts):
    t = opts['cable_tail_thickness'].split()  # '0.3 +/- 0.03 mm'
    return float(t[0]) + float(t[2])


def stand_height(l, prm, opts):
    """Height of the free end above the front board's rear face when the cable is folded upward under its slot:
    cable length less the insertion, less the plan run a to the slot centre, with a quarter bend of radius R
    (a - R straight, pi R / 2 in the bend, then upright from height R). Same path as the record's length rule."""
    return l['cable_length_mm'] - prm['insertion_mm'] - l['geometry']['a_mm'] + bend_term(prm['bend_radius_mm'])


def tail_width(circuits):
    return 0.5 * (circuits + 1)


def slot_clearance(l, opts):
    g = l['geometry']['slot']
    dx, dy = g[2] - g[0], g[3] - g[1]
    across, along = (dx, dy) if l['direction'] in ('+y', '-y') else (dy, dx)
    width_tol = CABLE_WIDTH_TOL_MM
    thick = tail_thickness_max(opts)
    return {'slot_across_mm': r3(across), 'slot_along_mm': r3(along),
            'across_per_side_mm': r3((across - tail_width(l['circuits']) - width_tol) / 2),
            'along_per_side_mm': r3((along - thick) / 2)}


def column_obstacles(l, links, inp):
    """What stands in the plan of the slot between the link's front board and K: another link's front connector or
    front tail, a post or sleeve keep-out, an adapter board it is not on, a tab, a kept selector or a sub toggle,
    and the edge of its own front board under the fold."""
    s = box(*l['geometry']['slot'])
    why = []
    for o in links:
        if o['id'] == l['id']:
            continue
        for part in ('front_connector', 'front_tail'):
            if s.intersection(box(*o['geometry'][part])).area > EPS:
                why.append('%s of %s' % (part.replace('_', ' '), o['id']))
        if s.intersection(box(*o['geometry']['slot'])).area > EPS:
            why.append('slot of ' + o['id'])
    for f in inp['gate']['fixings']:
        r = f['r_front'] if f.get('front') else f['r_K']
        if Point(*(f.get('front') or f['K'])).buffer(r, 64).intersection(s).area > EPS:
            why.append('fixing ' + f['id'])
    cand = inp['cand']
    for a in ('O1', 'O3', 'O5'):
        if a != l['front_board'] and Polygon(cand['planes'][a]['outline']).intersection(s).area > EPS:
            why.append('adapter ' + a)
    if l['front_board'] not in ('O1', 'O3', 'O5'):
        for t in cand['tabs']:
            if box(*t['rect']).intersection(s).area > EPS:
                why.append('tab ' + t['id'])
        for k in cand['selectors_kept']:
            if box(*k['courtyard']).intersection(s).area > EPS:
                why.append('kept selector ' + k['ref'])
        for k in cand['sub_toggles']:
            if box(*k['toggle_courtyard']).intersection(s).area > EPS:
                why.append('sub toggle ' + k['block'])
    own = Polygon(cand['planes'][l['front_board']]['outline'])
    if not own.contains(s):
        why.append('fold off the edge of ' + l['front_board'])
    return why


def link_rows(inp):
    gate, cand, opts = inp['gate'], inp['cand'], inp['opts']
    prm = gate['parameters']
    name = Namer(inp['lock'])
    gaps = cand['stack']['mated_heights_mm']
    k_th = round(cand['stack']['K_face_z_mm'] - cand['stack']['K_rear_z_mm'], 4)
    above = set(gate['summary']['compliance']['links_above_list'])
    links = gate['links']
    rows = []
    for l in links:
        g = l['geometry']
        gap = gaps[l['front_board'] + '/K']
        h = stand_height(l, prm, opts)
        rows.append({
            'id': l['id'], 'front_board': l['front_board'], 'size': l['size'],
            'front_connector': name(centre(g['front_connector'])),
            'slot': name(l['slot_centre']),
            'K_connector': name(centre(g['K_connector'])),
            'direction': l['direction'],
            'cable': l['cable'], 'cable_length_mm': l['cable_length_mm'],
            'on_front_board_mm': r3(g['a_mm']), 'on_K_rear_mm': r3(g['b_mm']),
            'front_extension_mm': g['front_extension_mm'], 'lengthened_tail': l['lengthened_tail'],
            'cable_needed_mm': l['cable_needed_mm'], 'slack_mm': l['loop_mm'],
            'leads_to_cut': list(l['trim_leads']),
            'compliance_mm_per_N': l['compliance_mm_per_N'], 'holding_hand': l['id'] in above,
            'latch': l['latch_reach']['verdict'].split(' (')[0], 'latch_detail': l['latch_reach']['verdict'],
            'latch_neighbours_remaining': list(l['latch_reach']['remaining']),
            'gap_mm': gap, 'stand_height_mm': r3(h), 'meets_K_at_mm': r3(h - gap),
            'through_K_when_seated_mm': r3(h - gap - k_th),
            'slot_clearance': slot_clearance(l, opts),
            'column_obstacles': column_obstacles(l, links, inp),
        })
    return rows


# ---------------------------------------------------------------- lowering, screws, service, counts

def lowering(rows, sites):
    by_h = collections.defaultdict(list)
    for r in rows:
        by_h[r['meets_K_at_mm']].append(r)
    stages = [{'meets_K_at_mm': h, 'ends': len(rs), 'links': sorted(r['id'] for r in rs),
               'per_board': {b: n for b in FRONT_ORDER for n in [sum(1 for r in rs if r['front_board'] == b)] if n}}
              for h, rs in sorted(by_h.items(), reverse=True)]
    for i, s in enumerate(stages):
        s['stage'] = i + 1
        s['drop_to_next_mm'] = r3(s['meets_K_at_mm'] - stages[i + 1]['meets_K_at_mm']) if i + 1 < len(stages) else None
    screw = sites['screw']
    L = screw['working_figure']['length_mm']
    tips = []
    for c in screw['classes']:
        tips.append({'class': c['class'], 'meets_K_at_mm': r3(L - c['grip_mm'] + 1.6)})
    largest = max(stages, key=lambda s: (s['ends'], s['meets_K_at_mm']))
    cl = [r['slot_clearance'] for r in rows]
    return {'stages': stages, 'largest_stage': largest['stage'], 'largest_ends': largest['ends'],
            'smallest_gap_between_stages_mm': min(s['drop_to_next_mm'] for s in stages if s['drop_to_next_mm']),
            'first_stage': stages[0]['stage'], 'travel_mm': stages[0]['meets_K_at_mm'],
            'screw_tips': tips, 'posts_meet_K_at_mm': 0.0,
            'slot_clearance_min': {'across_per_side_mm': min(c['across_per_side_mm'] for c in cl),
                                   'along_per_side_mm': min(c['along_per_side_mm'] for c in cl)},
            'blocked': [{'link': r['id'], 'by': r['column_obstacles']} for r in rows if r['column_obstacles']],
            'short_cables': [{'link': r['id'], 'slack_mm': r['slack_mm']} for r in rows if r['slack_mm'] < -EPS]}


def screws(sites):
    s = sites['screw']
    return {'working_figure': s['working_figure'], 'classes': s['classes'],
            'sheet': STORE_SHEET, 'sources_tried': SOURCES_TRIED, 'web_searches': WEB_SEARCHES,
            'nut_height_mm': 'UNSOURCED', 'washer_thickness_mm': 'UNSOURCED',
            'washer_verdict': 'UNSOURCED at all four sites: the washer rule of point 9 of the spacer page stands as it is',
            'holding': {'way': 'a strip of tape over each head (point 7 of the spacer page; ASSUMED to hold)',
                        'not_retained': ['threaded insert', 'soldered nut on the front board'],
                        'verdict': 'tape confirmed as the way; no retained part class holds the screw'}}


def service(rows, sites):
    n = len(rows)
    posts = sites['counts']['posts']
    sleeves = sites['counts']['sleeves']
    off = {'K-end locks opened': n, 'K ends withdrawn': n, 'nuts off': sleeves, 'post screws out (K side)': posts}
    on = {'K ends inserted': n, 'K-end locks closed': n, 'post screws in (K side)': posts, 'nuts on': sleeves}
    return {'off': off, 'on': on, 'per_opening': sum(off.values()) + sum(on.values()),
            'limit_openings': SERVICE_LIMIT, 'insertions_sourced': INSERTIONS_SOURCED,
            'K_end_insertions_after_limit': 1 + SERVICE_LIMIT, 'front_end_insertions': 1,
            'replace_link': {'cables': 1, 'locks': 2, 'needs_K_off': True,
                             'front_connector_insertions_after': 2}}


def counts(rows, gate, sites):
    cables = collections.Counter('%s %g mm' % (r['cable'], r['cable_length_mm']) for r in rows)
    per_board = collections.defaultdict(set)
    for r in rows:
        per_board[r['front_board']].update(r['leads_to_cut'])
    fronts = collections.Counter(r['front_board'] for r in rows)
    return {
        'links': len(rows), 'cables': len(rows), 'cables_per_code': dict(sorted(cables.items())),
        'connectors': 2 * len(rows), 'front_ends_per_board': {b: fronts[b] for b in FRONT_ORDER if fronts[b]},
        'locks_before_K': len(rows), 'locks_after_K': len(rows), 'locks': 2 * len(rows),
        'fixings': sites['counts']['fixings'], 'fastener_operations': sites['counts']['fastener_operations']['total'],
        'parts_with_leads_to_cut': sum(len(v) for v in per_board.values()),
        'parts_with_leads_to_cut_per_board': {b: len(per_board[b]) for b in FRONT_ORDER if per_board[b]},
        'lead_entries_per_link': sum(len(r['leads_to_cut']) for r in rows),
        'lengthened_tails': sum(1 for r in rows if r['lengthened_tail']),
        'holding_hand': sum(1 for r in rows if r['holding_hand']),
        'latch': dict(sorted(collections.Counter(r['latch'] for r in rows).items())),
    }


COUNT_AGAINST_SUMMARY = (('links', 'links'), ('connectors', 'connectors'), ('locks', 'latches'),
                         ('lengthened_tails', 'lengthened_tails'), ('lead_entries_per_link', 'trim_leads'))


def steps(rows, cnt, low, scr, sites, prm):
    hole = sites['access_holes'][0]
    sl = [f for f in sites['fixings'] if f['active'] and f['kind'] != 'post']
    where = ', '.join('(%g, %g) on %s%s' % (f['xy'][0], f['xy'][1], f['front_board'],
                                           (' through the %g mm access hole of %s' % (hole['diameter_mm'], hole['board']))
                                           if f['xy'] == hole['xy'] else '') for f in sl)
    lead = cnt['parts_with_leads_to_cut_per_board']
    fe = cnt['front_ends_per_board']
    wf = scr['working_figure']
    return [
        {'n': 1, 'do': 'Solder the parts of JL, JR, P and the three adapters. Every lead on the rear faces of JL, JR, P '
                       'and the adapters is cut to %g mm or less when the part is soldered (DS-88).' % prm['trim_to_mm'],
         'parts': cnt['parts_with_leads_to_cut'], 'where': '%s, listed below' %
         (', '.join('%s %d' % (b, lead[b]) for b in ('P', 'JL', 'JR', 'O3') if b in lead))},
        {'n': 2, 'do': 'Solder the panel hardware with the panel as the fixture, and fit the P unit with EL on its six '
                       'rigid pairs (DS-43).', 'parts': None},
        {'n': 3, 'do': 'Fit the brass posts on the front boards from the panel side: JL 6, JR 6, P 6 (DS-43).',
         'parts': 18},
        {'n': 4, 'do': 'Before the panel goes on, push an %s screw (head at most %.1f mm, not countersunk) through each '
                       'sleeve hole from the front of its board and hold the head down with a strip of tape: %s '
                       '(DS-76).' % (wf['designation'].replace(' x ', ' × ') + ' mm', wf['head_max_mm'], where),
         'parts': 4},
        {'n': 5, 'do': 'Slip a printed sleeve over each screw: long (18.8 mm) on JL and JR, short (16.8 mm) on P.',
         'parts': 4},
        {'n': 6, 'do': 'Put JL, JR and the P unit in the panel, and the three adapters on their selectors.',
         'parts': None},
        {'n': 7, 'do': 'Plug the front end of every cable into its front connector and close the lock with one '
                       'fingertip or a plastic tool. Every front end is plugged and locked before K comes down.',
         'parts': cnt['locks_before_K'], 'where': ', '.join('%s %d' % (b, fe[b]) for b in fe)},
        {'n': 8, 'do': 'Fold each cable upward under its slot so that its free end stands up from the board.',
         'parts': cnt['links']},
        {'n': 9, 'do': 'Lower K over the 18 posts in %d stages, highest end first, guiding the cable ends through '
                       'their slots stage by stage (largest stage: %d ends at %.2f mm), then the four screw ends '
                       'through K at %.1f and %.1f mm.' % (len(low['stages']), low['largest_ends'],
                                                          next(s['meets_K_at_mm'] for s in low['stages']
                                                               if s['stage'] == low['largest_stage']),
                                                          low['screw_tips'][1]['meets_K_at_mm'],
                                                          low['screw_tips'][0]['meets_K_at_mm']),
         'parts': cnt['links'] + 4},
        {'n': 10, 'do': 'Fasten K\'s screw at every post first.', 'parts': 18},
        {'n': 11, 'do': 'Put a nut on each of the four sleeve screws and turn it with the fingers until it is snug. '
                        'No tool and no thread lock. A washer only where the screw end still comes through the nut '
                        'with it.', 'parts': 4},
        {'n': 12, 'do': 'Fold each cable end onto K\'s rear face, insert it into its K connector and close the lock '
                        'with one fingertip or a plastic tool; never press K with the palm (DS-66). At the %d '
                        'connectors named below, the other hand holds K\'s edge beside the connector while its lock '
                        'is closed (DS-87).' % cnt['holding_hand'], 'parts': cnt['locks_after_K']},
        {'n': 13, 'do': 'Before power: look at every one of the %d locks, closed and square, and check the continuity '
                        'of every link (DS-43).' % cnt['locks'], 'parts': cnt['locks']},
    ]


def page_parameters(inp, rows):
    prm, opts, sites = inp['gate']['parameters'], inp['opts'], inp['sites']
    hole = sites['access_holes'][0]
    return {'bend_radius_mm': prm['bend_radius_mm'], 'bend_term_mm': round(bend_term(prm['bend_radius_mm']), 4),
            'insertion_mm': prm['insertion_mm'], 'trim_to_mm': prm['trim_to_mm'],
            'latch_margin_mm': prm['latch_margin_mm'], 'tail_step_mm': opts['tail_step_mm'],
            'slot_width_extra_mm': opts['slot_width_extra_mm'], 'slot_length_mm': opts['slot_length_mm'],
            'cable_tail_thickness': opts['cable_tail_thickness'], 'tail_thickness_max_mm': r3(tail_thickness_max(opts)),
            'cable_width_tol_mm': CABLE_WIDTH_TOL_MM, 'insertions_sourced': INSERTIONS_SOURCED,
            'cable_length_range_mm': [min(r['cable_length_mm'] for r in rows), max(r['cable_length_mm'] for r in rows)],
            'access_hole': {'board': hole['board'], 'xy': hole['xy'], 'diameter_mm': hole['diameter_mm']}}


def generate(root=ROOT):
    inp = load_inputs(root)
    return build(inp), inp


def build(inp):
    rows = link_rows(inp)
    low = lowering(rows, inp['sites'])
    scr = screws(inp['sites'])
    cnt = counts(rows, inp['gate'], inp['sites'])
    doc = {
        'schema_version': 1,
        'status': 'paper procedure on unvalidated drafts; no fit, no strength and no proven assembly',
        'verdict': 'NEEDS_DESIGN' if (low['blocked'] or low['short_cables']) else 'DONE',
        'parameters': page_parameters(inp, rows),
        'links': rows,
        'steps': steps(rows, cnt, low, scr, inp['sites'], inp['gate']['parameters']),
        'lowering': low,
        'latch': {'counts': dict(inp['gate']['summary']['latch_verdicts']),
                  'not_shown': [{'link': r['id'], 'K_connector': r['K_connector']['name'],
                                 'neighbours': r['latch_neighbours_remaining']}
                                for r in rows if r['latch'] == 'NOT SHOWN'],
                  'reason': 'no footprint height is retained; the neighbours are exempt packages ASSUMED lower than '
                            'the 2.0 mm connector body (DS-88)'},
        'holding_hand': [{'link': r['id'], 'K_connector': r['K_connector'], 'compliance_mm_per_N': r['compliance_mm_per_N']}
                         for r in rows if r['holding_hand']],
        'screws': scr,
        'service': service(rows, inp['sites']),
        'counts': cnt,
        'provenance': {'generator': 'scripts/stack/fixings/procedure.py', 'regenerate': REGEN, 'pins': pins(inp)},
    }
    return doc


# ---------------------------------------------------------------- checker

def check(doc, inp):
    """(rule, message) findings: a link without a row, a count that differs from the record, a stale projection."""
    errs = []
    want = [l['id'] for l in inp['gate']['links']]
    have = [r['id'] for r in doc['links']]
    for i in sorted(set(want) - set(have)):
        errs.append(('row', 'link %s of the record has no row' % i))
    for i in sorted(set(have) - set(want)):
        errs.append(('row', 'row %s is no link in use in the record' % i))
    if len(have) != len(set(have)):
        errs.append(('row', 'a link has more than one row'))
    s = inp['gate']['summary']
    c = doc['counts']
    for mine, theirs in COUNT_AGAINST_SUMMARY:
        if c[mine] != s[theirs]:
            errs.append(('count', '%s %s differs from the record summary %s %s' % (mine, c[mine], theirs, s[theirs])))
    if c['latch'] != s['latch_verdicts']:
        errs.append(('count', 'latch verdicts %s differ from the record %s' % (c['latch'], s['latch_verdicts'])))
    if c['holding_hand'] != len(s['compliance']['links_above_list']):
        errs.append(('count', 'holding hand %d differs from the record %d' % (c['holding_hand'],
                                                                             len(s['compliance']['links_above_list']))))
    if c['locks_before_K'] + c['locks_after_K'] != s['latches']:
        errs.append(('count', 'locks before and after K do not add up to the record latches'))
    if sum(len(v['links']) for v in doc['lowering']['stages']) != len(want):
        errs.append(('count', 'the lowering stages do not hold every end'))
    pin = doc['provenance']['pins']['gate_record_projection']['digest']
    if pin != digest(inp['gate']):
        errs.append(('stale', 'projection of the gate record changed; regenerate with: ' + REGEN))
    return errs


def render_json(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False) + '\n'


def main(argv):
    import procedure_page
    doc, inp = generate()
    errs = check(doc, inp)
    if '--check' in argv:
        errs = list(errs)
        if PROC_JSON.read_text() != render_json(doc):
            errs.append(('stale', '%s differs; regenerate with: %s' % (PROC_JSON.relative_to(ROOT), REGEN)))
        if PROC_MD.read_text() != procedure_page.render(doc):
            errs.append(('stale', '%s differs; regenerate with: %s' % (PROC_MD.relative_to(ROOT), REGEN)))
        if PROC_JSON.exists():
            retained = json.loads(PROC_JSON.read_text())
            errs += [e for e in check(retained, inp) if e not in errs]
    else:
        PROC_JSON.write_text(render_json(doc))
        PROC_MD.write_text(procedure_page.render(doc))
    for r, m in errs:
        print('FAIL %s: %s' % (r, m))
    print('verdict %s; %d findings' % (doc['verdict'], len(errs)))
    return 1 if errs else 0


if __name__ == '__main__':
    sys.path.insert(0, str(HERE))
    sys.exit(main(sys.argv[1:]))
