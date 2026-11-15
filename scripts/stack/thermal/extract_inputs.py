"""Extract the ST-05 inputs from the repository into design/stack/thermal/thermal-screen.json.

Only the `inputs` and `provenance` blocks are written; the hand-authored `terms` block is kept.
Every source is pinned by the object or the row lines that a term reads (Amendment 2 of the brief).

  extract_inputs.py          rewrite the inputs and pins in place
  extract_inputs.py --check  exit 1 when the stored inputs or pins differ from the repository
"""
import glob
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCREEN = ROOT / 'design/stack/thermal/thermal-screen.json'
LEDGER = 'design/power/rail-ledger.json'
PARTITION = 'design/partition/partition.json'
FLOORPLAN = 'design/partition/floorplan-candidate.json'
STACK = 'design/stack/geometry/stack-candidate.json'
FIXINGS = 'design/stack/fixings/fixing-sites.json'
DECISIONS = 'circuit/orchestration/campaigns/osc-stack-20261114/decisions.md'
LINK_GATE = 'design/stack/geometry/links/link-gate.json'
IO_PARTITION = 'design/reports/io-partition.json'
PLAN = 'doc/src/content/docs/decisions/osc-direct-stack-plan.mdx'
EXACT_PARTS = ('CL10A105KB8NNNC', 'RC0603FR-072K2L')
CLASS_BUNDLES = {
    'AS3340D': 'component-alfa-rpar-as3340d', 'CD74HC221M96': 'component-ti-cd74hc221m96',
    'LF398M_NOPB': 'component-ti-lf398m-nopb', 'LM13700M_NOPB': 'component-ti-lm13700m-nopb',
    'LM393BIDR': 'component-ti-lm393bidr', 'NOISE2': 'component-electric-druid-noise2',
    'OPA4196IDR': 'component-ti-opa4196idr', 'OPA4197IDR': 'component-ti-opa4197idr',
    'OPA4197IPWR': 'component-ti-opa4197ipwr', 'REF5050AIDR': 'component-ti-ref5050aidr',
    'SN74HC00DR': 'component-ti-sn74hc00dr', 'SN74HC14DR': 'component-ti-sn74hc14dr',
    'SN74HC74DR': 'component-ti-sn74hc74dr', 'TMUX6112PWR': 'component-ti-tmux6112pwr',
    'TMUX7412FRRPR': 'component-ti-tmux7412frrpr', 'CL10A105KB8NNNC': 'component-samsung-cl10a105kb8nnnc',
    'RC0603FR-072K2L': 'component-yageo-rc0603fr-072k2l', 'BCM847BS': 'component-nexperia-bcm847bs-115',
}
RAILS = ('+12V', '-12V', '+5V')
DECISION_ROWS = ('DS-33', 'DS-42', 'DS-59', 'DS-60', 'DS-61', 'DS-62', 'DS-63', 'DS-64', 'DS-65', 'DS-66',
                 'DS-67', 'DS-72', 'DS-73', 'DS-74', 'DS-75', 'DS-76', 'DS-83', 'DS-88', 'DS-92', 'DS-94',
                 'DS-95', 'DS-96', 'DS-97', 'DS-98', 'DS-99')
DOC_LINES = {
    'plan-heat-row': (PLAN, '| Heat in a closed case |'),
    'plan-q6-row': ('doc/src/content/docs/decisions/osc-direct-stack-plan.mdx', '| Q6 |'),
    'plan-depth-34-supply': ('doc/src/content/docs/decisions/osc-direct-stack-plan.mdx', '- **Supply.** The external-source'),
    'ledger-bleeder-line': ('doc/src/content/docs/architecture/osc-rail-ledger.mdx', '`rail-allocation-input.json` assigns all 33'),
    'ledger-external-load-line': ('doc/src/content/docs/architecture/osc-rail-ledger.mdx', 'The 92 magnitude, ten clip'),
    'gates-e19-line': ('doc/src/content/docs/verification/osc-release-gates.mdx', 'E18 authorizes regional placement'),
    'gates-64-row': ('doc/src/content/docs/verification/osc-release-gates.mdx', '| [#64]'),
    'osc-vee-line': ('doc/src/content/docs/architecture/osc-block-osc.mdx', 'The document recommends externally supplied'),
    'posts-r30-row': ('design/stack/power-posts/README.md', '| JL and JR to K, 19.0 mm | Harwin R30-1011902'),
    'plan-joint-line': ('doc/src/content/docs/decisions/osc-direct-stack-plan.mdx', 'The ≤0.5 mΩ joint figure'),
    'plan-k-apertures-row': ('doc/src/content/docs/decisions/osc-direct-stack-plan.mdx', '| K latch-service apertures |'),
}
FACTS = {
    'fact-power-bleeder-identity': 'component-yageo-rc0603fr-072k2l',
    'fact-power-bleeder-power': 'component-yageo-rc0603fr-072k2l',
    'fact-power-bleeder-derating': 'component-yageo-rc0603fr-072k2l',
    'fact-power-bleeder-body': 'component-yageo-rc0603fr-072k2l',
    'fact-power-bleeder-application': 'component-yageo-rc0603fr-072k2l',
    'fact-r-general-power': 'component-passives-family',
    'fact-contact-pullup-r-derating': 'component-yageo-rc0603fr-0710kl',
    'fact-schmitt-temperature': 'component-ti-sn74hc14dr',
    'fact-flipflop-temperature': 'component-ti-sn74hc74dr',
    'fact-vco-supply-guidance': 'component-alfa-rpar-as3340d',
    'fact-vco-positive-supply-current': 'component-alfa-rpar-as3340d',
    'fact-vco-package-outline': 'component-alfa-rpar-as3340d',
    'fact-op-precision-d-quiescent-current': 'component-ti-opa4197idr',
    'fact-op-precision-quiescent-current': 'component-ti-opa4197ipwr',
    'fact-op-audio-quiescent-current': 'component-ti-opa4196idr',
    'fact-fault-switch-t-normal-supply-current': 'component-ti-tmux7412frrpr',
    'fact-fault-switch-t-thermal-pad': 'component-ti-tmux7412frrpr',
    'fact-clamp-diode-power-thermal': 'component-nexperia-bat54s-215',
    'fact-clamp-diode-ll-power-thermal': 'component-nexperia-bav199-215',
    'fact-trim-203-power': 'component-bourns-tc33x-2-203e',
    'fact-power-reservoir-temperature': 'component-samsung-cl10a105kb8nnnc',
    'fact-audio-feedback-c-temperature': 'component-kemet-c0603c100j5gactu',
    'fact-kingbright-white-identity': 'component-kingbright-aphhs1005qwf-d',
    'fact-kingbright-red-electrical': 'component-kingbright-apg1005sec-e-t',
}
THERMAL_WORDS = re.compile(r'thermal|theta|junction|rth_|derat|temperature|self-heating|power70|-power$', re.I)
SURVEY_BUNDLES = ('component-alfa-rpar-as3340d', 'component-ti-opa4197idr', 'component-ti-opa4197ipwr',
                  'component-ti-opa4196idr', 'component-ti-lm13700m-nopb', 'component-ti-ref5050aidr',
                  'component-electric-druid-noise2', 'component-ti-lf398m-nopb', 'component-ti-lm393bidr',
                  'component-ti-tmux7412frrpr', 'component-ti-tmux6112pwr', 'component-ti-cd74hc221m96',
                  'component-ti-sn74hc00dr', 'component-ti-sn74hc14dr', 'component-ti-sn74hc74dr',
                  'component-kingbright-aphhs1005qwf-d', 'component-kingbright-apg1005sec-e-t',
                  'component-yageo-rc0603fr-072k2l', 'component-passives-family', 'component-nexperia-bcm847bs-115')


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load(path):
    return json.loads((ROOT / path).read_text())


def find_line(path, prefix):
    lines = [ln for ln in (ROOT / path).read_text().splitlines() if ln.lstrip().startswith(prefix)]
    if len(lines) != 1:
        raise ValueError(f'Expected one line starting {prefix!r} in {path}, found {len(lines)}')
    return lines[0]


def object_pin(pin_id, path, key, obj, reads):
    return {'id': pin_id, 'path': path, 'object': key, 'sha256': sha(canonical(obj)), 'reads': reads}


def bundle_facts():
    rows, facts = [], {}
    for path in sorted(glob.glob(str(ROOT / '.claude/skills/component-*/facts.json'))):
        data = json.loads(Path(path).read_text())
        bundle = Path(path).parent.name
        for fact in data.get('facts', []):
            facts[fact['fact_id']] = (bundle, fact)
            if bundle in SURVEY_BUNDLES and THERMAL_WORDS.search(fact['fact_id']) and 'bias' not in fact['fact_id']:
                rows.append({'bundle': bundle, 'fact_id': fact['fact_id'], 'class': fact.get('class')})
    held = {r['bundle'] for r in rows}
    survey = {b: sorted(r['fact_id'] for r in rows if r['bundle'] == b) for b in SURVEY_BUNDLES if b in held}
    survey.update({b: [] for b in SURVEY_BUNDLES if b not in held})
    return dict(sorted(survey.items())), facts


def plan_heat_W(line):
    cells = [c.strip() for c in line.strip().strip('|').split('|')]
    return [float(v) for v in re.findall(r'(\d+(?:\.\d+)?) W\b', cells[1])]


def tail_width_mm(link):
    t = link['geometry']['front_tail']
    return t[2] - t[0] if link['direction'] in ('+y', '-y') else t[3] - t[1]


def link_figures(record):
    placed = [k for k in record['links'] if k['placed']]
    return {'links': record['summary']['links'], 'placed': record['summary']['placed'],
            'slots': record['summary']['slots'],
            'slot_area_mm2': round(sum((s[2] - s[0]) * (s[3] - s[1]) for s in
                                       (k['geometry']['slot'] for k in placed)), 6),
            'loop_plan_area_mm2': round(sum(k['loop_mm'] * tail_width_mm(k) for k in placed), 6),
            'cable_plan_area_mm2': round(sum(k['cable_length_mm'] * tail_width_mm(k) for k in placed), 6)}


def final_places(record, placements):
    places = {p['ref']: {'xy': [round(p['x_mm'], 3), round(p['y_mm'], 3)], 'side': p['side']} for p in placements}
    displaced = record.get('displaced_k_ic_packages')
    if displaced is None:
        return places, {'read': 'floorplan', 'moved': 0, 'listed': 0, 'kept': 0}
    moved = 0
    for row in displaced:
        if row['new'] is None:
            continue
        places[row['ref']] = {'xy': [round(row['new']['xy'][0], 3), round(row['new']['xy'][1], 3)],
                              'side': row['new']['side']}
        moved += 1
    return places, {'read': 'gate record displaced_k_ic_packages', 'moved': moved, 'listed': len(displaced),
                    'kept': len(displaced) - moved}


def exact_part_refs(io):
    return [{'ref': p['ref'], 'mpn': p['mpn'], 'instance': p['instance']}
            for p in io['physical_packages'] if p.get('mpn') in EXACT_PARTS]


def operating_ranges(facts):
    out = {}
    for symbol, bundle in sorted(CLASS_BUNDLES.items()):
        out[symbol] = []
        for fact_id, (b, fact) in sorted(facts.items()):
            v = fact.get('value')
            if b == bundle and 'temperature' in fact_id and isinstance(v, dict) and \
                    {'minimum', 'maximum'} <= set(v) and fact.get('unit') == 'degC':
                out[symbol].append({'fact_id': fact_id, 'minimum': v['minimum'], 'maximum': v['maximum']})
    return out


def extract(gate=None):
    ledger = load(LEDGER)
    part = load(PARTITION)
    floor = load(FLOORPLAN)
    stack = load(STACK)['candidate']
    fixings = load(FIXINGS)
    gate = load(LINK_GATE) if gate is None else gate
    io = load(IO_PARTITION)
    assign = {c['ref']: c for c in part['assignment']['components']}
    place = {p['ref']: p for p in floor['placements']}
    final, place_source = final_places(gate, floor['placements'])
    pins = []

    rows = []
    for w in ledger['worksheet_loads']:
        rows.append({'id': w['id'], 'instance': w['instance'], 'label': w['label'], 'count': w['count'],
                     'unit': w['unit'], 'mA': [w['planning_allowance_mA'][r] for r in RAILS]})
    for key, a in ledger['draft_allowances'].items():
        inst = key.split(':')[0]
        rows.append({'id': 'allowance:' + key, 'instance': inst, 'label': 'draft allowance ' + key, 'count': 1,
                     'unit': 'draft allowance', 'mA': [a['planning_mA'] if r == a['rail'] else 0 for r in RAILS]})
    pins += [object_pin('ledger-worksheet-loads', LEDGER, 'worksheet_loads', ledger['worksheet_loads'],
                        'planning_allowance_mA, count, label and instance of every row'),
             object_pin('ledger-draft-allowances', LEDGER, 'draft_allowances', ledger['draft_allowances'],
                        'planning_mA and rail of every draft allowance')]
    ledger_cases = {}
    for key in ('two_feed_total_mA', 'conditional_SH_short_resistor_case_mA', 'sensitivity_case_mA',
                'conditional_startup_1ms_mA'):
        value = ledger[key]
        if 'A' in value:
            value = {r: round(value['A'][r] + value['B'][r], 9) for r in RAILS}
        ledger_cases[key] = [value[r] for r in RAILS]
        pins.append(object_pin('ledger-' + key, LEDGER, key, ledger[key], 'rail currents of the case'))
    rails_v = ledger['case_envelope']['continuous_normal']['rails_V']
    pins.append(object_pin('ledger-case-envelope', LEDGER, 'case_envelope', ledger['case_envelope'],
                           'nominal rail voltages and the 5 V into 10 kohm output state'))

    ic = []
    for pkg in ledger['physical_ic_packages']:
        a, p = assign[pkg['ref']], place[pkg['ref']]
        c = p['courtyard_mm']
        ic.append({'ref': pkg['ref'], 'instance': pkg['instance'], 'symbol': pkg['symbol'], 'board': a['board'],
                   'side': final[pkg['ref']]['side'], 'xy': final[pkg['ref']]['xy'],
                   'courtyard_mm2': round((c[2] - c[0]) * (c[3] - c[1]), 3)})
    pins.append(object_pin('ledger-ic-packages', LEDGER, 'physical_ic_packages', ledger['physical_ic_packages'],
                           'ref, instance and symbol of every IC package'))
    pins.append(object_pin('partition-assignment', PARTITION, 'assignment', part['assignment'],
                           'board of every reference'))
    pins.append(object_pin('floorplan-placements', FLOORPLAN, 'placements', floor['placements'],
                           'x, y, side and courtyard of every reference'))

    figures = link_figures(gate)
    pins.append(object_pin('link-gate-figures', LINK_GATE, 'derived: link_figures(record)', figures,
                           'links, placed and slots of the summary; slot, loop and cable areas of the placed links'))
    pins.append(object_pin('link-gate-displaced-k-ic-packages', LINK_GATE, 'displaced_k_ic_packages',
                           gate.get('displaced_k_ic_packages'), 'the rows of DS-97, or null while the key is absent'))
    refs = exact_part_refs(io)
    pins.append(object_pin('io-partition-exact-refs', IO_PARTITION, 'physical_packages[mpn in EXACT_PARTS]', refs,
                           'ref, mpn and instance of every CL10A105KB8NNNC and RC0603FR-072K2L package'))
    exact_places = {}
    for r in refs:
        exact_places.setdefault(r['mpn'], []).append({'ref': r['ref'], 'board': assign[r['ref']]['board'],
                                                      'side': final[r['ref']]['side'], 'xy': final[r['ref']]['xy']})

    prefix_instance = {}
    for pkg in ledger['physical_ic_packages']:
        prefix_instance[int(re.sub(r'\D', '', pkg['ref'])) // 100] = pkg['instance']
    sums = {}
    for p in floor['placements']:
        if p['board'] != 'K':
            continue
        digits = re.sub(r'\D', '', p['ref'])
        inst = prefix_instance.get(int(digits) // 100) if digits else None
        if inst is None:
            continue
        s = sums.setdefault(inst, [0, 0.0, 0.0])
        s[0] += 1
        s[1] += p['x_mm']
        s[2] += p['y_mm']
    module_k = {k: {'refs': v[0], 'centroid': [round(v[1] / v[0], 3), round(v[2] / v[0], 3)]}
                for k, v in sorted(sums.items())}

    leds = {}
    for path in sorted(glob.glob(str(ROOT / 'design/boards/osc-*.json'))):
        b = json.loads(Path(path).read_text())
        key = next(x['board_key'] for x in part['boards'] if x['id'] == b['board_id'])
        uids = [u for u in b.get('placement_uids', []) if u.startswith('L:')]
        for u in uids:
            inst, kind = u[2:].split('.')[0], u.split('.')[-1]
            leds.setdefault(inst + '.' + kind, {}).setdefault(key, 0)
            leds[inst + '.' + kind][key] += 1
        rel = str(Path(path).relative_to(ROOT))
        pins.append(object_pin('board-uids-' + key, rel, 'placement_uids', b.get('placement_uids', []),
                               'indicator uids (L:) on the board'))

    boards_120 = {b['board_key']: {'face_z_mm': b['face_z_mm'], 'thickness_mm': b['thickness_mm'],
                                   'outline': b['outline'], 'layers': b['layers'], 'copper_oz': b['copper_oz']}
                  for b in part['boards']}
    pins.append(object_pin('partition-boards', PARTITION, 'boards', part['boards'],
                           'outline, face_z_mm and thickness of every board in the cable design'))
    for key in ('jack_split', 'enclosure', 'panel'):
        pins.append(object_pin('partition-' + key, PARTITION, key, part[key], {
            'jack_split': 'left and right instances', 'enclosure': 'internal XY and the 120 mm depth',
            'panel': 'panel thickness'}[key]))
    pins.append(object_pin('partition-power-continuous', PARTITION, 'power.required_continuous_mA',
                           part['power']['required_continuous_mA'], 'continuous contract currents'))
    pins.append(object_pin('stack-stack', STACK, 'candidate.stack', stack['stack'],
                           'K planes, rear parts, enclosure depth cases and mated heights'))
    pins.append(object_pin('stack-planes', STACK, 'candidate.planes', stack['planes'],
                           'outline and planes of every board in the stack'))
    led = load('design/reports/current/compact-led-61.json')
    pins.append(object_pin('led-report-branches', 'design/reports/current/compact-led-61.json', 'branches',
                           led['branches'], 'LED branch counts and resistor values'))
    active = [f for f in fixings['fixings'] if f['active']]
    pins.append(object_pin('fixings-active', FIXINGS, 'fixings[active]', active, 'kind, xy and gap of the 22 fixings'))

    dec_lines = (ROOT / DECISIONS).read_text().splitlines()
    for row in DECISION_ROWS:
        line = [ln for ln in dec_lines if ln.startswith(f'| {row} |')]
        if len(line) != 1:
            raise ValueError('Decision row not found once: ' + row)
        pins.append({'id': 'decision-' + row, 'path': DECISIONS, 'row': row, 'sha256': sha(line[0])})
    for pin_id, (path, prefix) in DOC_LINES.items():
        pins.append({'id': pin_id, 'path': path, 'line_prefix': prefix, 'sha256': sha(find_line(path, prefix))})
    heat = plan_heat_W(find_line(*DOC_LINES['plan-heat-row']))

    survey, facts = bundle_facts()
    ranges = operating_ranges(facts)
    fact_values = {}
    for fact_id, bundle in FACTS.items():
        b, fact = facts[fact_id]
        if b != bundle:
            raise ValueError(f'{fact_id} is in {b}, not {bundle}')
        fact_values[fact_id] = {'bundle': bundle, 'value': fact.get('value'), 'unit': fact.get('unit'),
                                'class': fact.get('class')}
        pins.append({'id': fact_id, 'path': f'.claude/skills/{bundle}/facts.json',
                     'fact_id': fact_id, 'sha256': sha(canonical(fact))})
    for symbol, rows_r in ranges.items():
        for r in rows_r:
            if r['fact_id'] not in FACTS:
                b, fact = facts[r['fact_id']]
                pins.append({'id': r['fact_id'], 'path': f'.claude/skills/{b}/facts.json',
                             'fact_id': r['fact_id'], 'sha256': sha(canonical(fact))})

    inputs = {
        'rails_V': [abs(rails_v[r]) for r in RAILS],
        'rails': list(RAILS),
        'rows': rows,
        'ledger_cases_mA': ledger_cases,
        'contract_mA': [part['power']['required_continuous_mA'][r] for r in RAILS],
        'ic_packages': ic,
        'place_source': place_source,
        'exact_part_places': exact_places,
        'link_figures': figures,
        'plan_heat_row_W': heat,
        'operating_ranges': ranges,
        'class_bundles': dict(sorted(CLASS_BUNDLES.items())),
        'module_K_centroids': module_k,
        'led_uid_boards': dict(sorted(leds.items())),
        'jack_split': {'left': part['jack_split']['left_instances'], 'right': part['jack_split']['right_instances']},
        'enclosure_internal_xy_mm': part['enclosure']['internal_xy_mm'],
        'enclosure_120_inside_depth_mm': part['enclosure']['inside_depth_mm'],
        'enclosure_120_rear_clearance_from_K_B_face_mm': part['enclosure']['rear_clearance_from_K_B_face_mm'],
        'panel_thickness_mm': part['panel']['thickness_mm'],
        'boards_120': boards_120,
        'stack': stack['stack'],
        'planes_40': {k: {'face_z_mm': v['face_z_mm'], 'thickness_mm': v['thickness_mm'], 'outline': v['outline']}
                      for k, v in stack['planes'].items()},
        'led_branches': led['branches'],
        'fixings_active': [{'id': f['id'], 'kind': f['kind'], 'xy': f['xy'], 'gap_mm': f['gap_mm']} for f in active],
        'bundle_facts': fact_values,
        'bundle_thermal_survey': survey,
    }
    return inputs, pins


def check(screen=None):
    screen = screen or json.loads(SCREEN.read_text())
    inputs, pins = extract()
    problems = []
    if canonical(inputs) != canonical(screen['inputs']):
        problems.append('stored inputs differ from the repository')
    stored = {p['id']: p for p in screen['provenance']['pins']}
    produced = {p['id'] for p in pins}
    for p in pins:
        if p['id'] not in stored:
            problems.append('missing pin ' + p['id'])
        elif stored[p['id']]['sha256'] != p['sha256']:
            problems.append('stale pin ' + p['id'])
    for pin_id in stored:
        if pin_id not in produced:
            problems.append('stored pin no longer produced ' + pin_id)
    return problems


def main(argv):
    screen = json.loads(SCREEN.read_text())
    if argv == ['--check']:
        problems = check(screen)
        print('\n'.join(problems) or 'inputs and pins match the repository')
        return 1 if problems else 0
    inputs, pins = extract()
    screen['inputs'] = inputs
    screen['provenance']['pins'] = pins
    SCREEN.write_text(json.dumps(screen, indent=1, ensure_ascii=False) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
