#!/usr/bin/env python3
"""Generate board interface audit tables from the selected partition."""
from collections import defaultdict
import json
from pathlib import Path
from scripts.schgen.project_boards import load_partition

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = load_partition()
    assignment = p['assignment']['components']
    floorplan = {x['ref']: x for x in json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text())['placements']}
    face = {x['ref']: {'board': x['board'], 'BoardSide': x['side'], 'fitted': x['fitted'],
                       'kicad_orientation_deg': floorplan[x['ref']]['kicad_orientation_deg'],
                       'footprint_origin_mm': [floorplan[x['ref']]['x_mm'], floorplan[x['ref']]['y_mm']]} for x in assignment}
    for c in p['connectors']:
        face[c['pcb_reference']] = {'board': c['board'], 'BoardSide': c['side'], 'kicad_orientation_deg': c['kicad_orientation_deg'],
                                    'footprint_origin_mm': c['footprint_origin_mm'], 'fitted': True}
    for t in p['load_side_terminals']:
        face[t['reference']] = {'board': t['board'], 'BoardSide': t['side'], 'center_mm': t['center_mm'], 'fitted': True}
    (ROOT/'design/reports/board-side-map.json').write_text(json.dumps(face, indent=2, sort_keys=True)+'\n')
    items = []
    by_pair = defaultdict(lambda: defaultdict(lambda: {'contacts': 0, 'max_bound_mA': 0, 'harnesses': set()}))
    headers = {c['id']: c for c in p['connectors']}
    for h in p['harnesses']:
        a, b = (headers[x] for x in h['header_ids'])
        pair = '/'.join(sorted(h['boards']))
        for pin in range(1, a['contacts']+1):
            key = str(pin); net = a['pin_map'].get(key)
            if net != b['pin_map'].get(key): raise ValueError(f'{h["id"]}: mate mismatch pin {pin}')
            if net in (None, 'NC'): continue
            record = by_pair[pair][net]
            record['contacts'] += 1
            record['harnesses'].add(h['id'])
            current = next((x.get('current_bound_mA') for x in a['pins'] if x['manufacturer_pin']==key), None)
            if isinstance(current, (int, float)): record['max_bound_mA'] = max(record['max_bound_mA'], current)
    for c in p['connectors']:
        used = []
        for pin in range(1, c['contacts']+1):
            n = str(pin); net = c['pin_map'].get(n)
            value = next((x.get('current_bound_mA') for x in c['pins'] if x['manufacturer_pin']==n), None)
            if isinstance(value, (int,float)) and value > 500:
                raise ValueError(f'{c["id"]}.{n}: declared {value} mA exceeds 500 mA planning derating')
            used.append({'manufacturer_pin': n, 'net': net, 'current_bound_mA': value,
                         'planning_contact_limit_mA': 500, 'wired': net not in (None,'NC')})
        items.append({'id': c['id'], 'board': c['board'], 'pcb_reference': c['pcb_reference'],
                      'header_mpn': c['header_mpn'], 'housing_mpn': c['housing_mpn'],
                      'contact_mpn': c['contact_mpn'], 'side': c['side'],
                      'kicad_orientation_deg': c['kicad_orientation_deg'],
                      'pins_used': sum(x['wired'] for x in used), 'pins_free': sum(not x['wired'] for x in used),
                      'mechanical_pads': c['mechanical_pads'], 'pins': used})
    report = {'status': 'CONDITIONAL UNVALIDATED DRAFT; currents are planning bounds, assembly qualification NOT RUN',
              'planning_contact_limit_mA': 500, 'headers': items,
              'external_assembly': {'housings': len(p['connectors']), 'fitted_crimps': sum(x['pins_used'] for x in items)//2,
                                    'pcb_footprints': 0},
              'load_side_factory_wires': p['load_side_wires']}
    # Each board end has a housing and a crimp per wired position.
    report['external_assembly']['fitted_crimps'] = sum(x['pins_used'] for x in items)
    (ROOT/'design/reports/connectors.json').write_text(json.dumps(report, indent=2)+'\n')
    lines = ['---', 'title: Board connector projection', 'description: Declared board-to-board interfaces in the conditional ten-board draft.', '---', '',
             '# Board connector projection', '',
             'This is an unvalidated draft. The 195 harnesses and eighteen factory load-side wires are declared interfaces; their installed fit, crimp, hot resistance and service behavior are NOT RUN. CN301/XB301 remain abstract source boundaries.', '',
             f'{len(p["connectors"])} PCB headers expose {sum(x["pins_used"] for x in items)} wired contact positions and {sum(x["pins_free"] for x in items)} unwired positions across both ends. The 390 external housings and {report["external_assembly"]["fitted_crimps"]} fitted crimps are non-PCB assembly items. The planning limit is 500 mA per contact; this is not a measured capacity.', '']
    for pair, nets in sorted(by_pair.items()):
        lines += [f'## {pair}', '', '| Net | Contacts per end | Highest declared contact bound (mA) | Harnesses |', '| --- | ---: | ---: | --- |']
        for net, v in sorted(nets.items()):
            lines.append(f'| `{net}` | {v["contacts"]} | {v["max_bound_mA"]} | {", ".join(sorted(v["harnesses"]))} |')
        lines.append('')
    lines += ['## Factory load-side wires', '', '| Wire | Net | PCB terminals | Max cut (mm) |', '| --- | --- | --- | ---: |']
    for w in p['load_side_wires']:
        lines.append(f'| {w["id"]} | `{w["net"]}` | {" / ".join(w["terminal_refs"])} | {w["maximum_length_mm"]} |')
    lines += ['', 'The source inlet and exact future protection/bulk parts remain unselected. Every PCB and schematic is an unvalidated draft.', '']
    path = ROOT/'doc/src/content/docs/architecture/osc-connectors.mdx'
    path.write_text('\n'.join(lines))
    print(f'Generated connector report: {len(items)} headers, {report["external_assembly"]["fitted_crimps"]} fitted crimps')


if __name__ == '__main__': main()
