"""Place complete envelope debounce triplets beside their exact Schmitt inputs.

Distances are project layout targets, not manufacturer or functional guarantees.
Panel hardware, ICs, bypasses, identities and net assignments remain unchanged.
"""
import math
from collections import Counter
from scripts.pcbgen.placement_geometry import Box, inside_outline

LIMITS = {'capacitor_to_input': 8, 'series_to_capacitor': 4, 'pull_to_series': 4}


def debounce_groups(io):
    parts = {p['ref']: p for p in io['physical_packages']}
    result = {}
    for instance in ('E1', 'E2', 'E3', 'E4', 'E5', 'E6'):
        units = [u for u in io['package_units']
                 if parts[u['ref']]['instance'] == instance and u['region'] == 'control']
        caps = [u for u in units if u['role'] == 'switch_button_input:C_DB']
        if len(caps) != 5:
            raise ValueError('Exactly five envelope debounce capacitors required: '+instance)
        for cap in caps:
            net = cap['pins'].get('1')
            if not net or cap['pins'].get('2') != 'AGND':
                raise ValueError('Debounce capacitor must join its input net to AGND')
            amps = [u for u in units if u['role'] == 'switch_button_input:U' and net in u['pins'].values()]
            series = [u for u in units if u['role'] == 'switch_button_input:R_SER' and u['pins'].get('2') == net]
            if len(amps) != 1 or len(series) != 1:
                raise ValueError('Unique Schmitt input and series resistor required')
            amp, resistor = amps[0], series[0]
            inputs = [p for p, n in amp['pins'].items() if n == net]
            if (len(inputs) != 1 or inputs[0] not in {'1','3','5','9','11','13'} or
                    parts[amp['ref']]['mpn'] != 'SN74HC14DR'):
                raise ValueError('Exact SN74HC14DR input pin required')
            contact = resistor['pins'].get('1')
            pulls = [u for u in units if u['role'] == 'switch_button_input:R_PULL'
                     and u['pins'].get('2') == contact and u['pins'].get('1') == '+5V']
            if len(pulls) != 1 or not contact or contact == net:
                raise ValueError('Unique contact pull-up and distinct RC input required')
            result[cap['ref']] = {'instance': instance, 'schmitt_ref': amp['ref'],
                'input_pin': inputs[0], 'debounce_net': net, 'contact_net': contact,
                'capacitor': cap['ref'], 'series': resistor['ref'], 'pull': pulls[0]['ref']}
    refs = [g[k] for g in result.values() for k in ('capacitor','series','pull')]
    if len(result) != 30 or len(set(refs)) != 90:
        raise ValueError('All thirty independent three-part debounce groups required')
    return result


def apply_debounce_locality(placements, io, source, connectors, lock, shapes, proposal, optical):
    from scripts.checks.partition35_floorplan import Grid, oriented_box, footprint_pads, turn
    from scripts.checks.connector_packing35 import board_for, pads, rect_collision
    if type(proposal.get('schema_version')) is not int or proposal['schema_version'] != 1:
        raise ValueError('Unsupported debounce-locality schema')
    if proposal.get('limits_mm') != LIMITS:
        raise ValueError('Reviewed debounce distance targets changed')
    expected = debounce_groups(io)
    if set(proposal['groups']) != set(expected):
        raise ValueError('Complete envelope debounce group set required')
    parts = {p['ref']: p for p in io['physical_packages']}
    prior = {p['ref']: p for p in placements}
    moving = set()
    for key, group in expected.items():
        proposed = proposal['groups'][key]
        if {k: proposed.get(k) for k in ('instance','schmitt_ref','input_pin')} != {
                k: group[k] for k in ('instance','schmitt_ref','input_pin')}:
            raise ValueError('Debounce group targets a different source input')
        refs = {group[k] for k in ('capacitor','series','pull')}
        if set(proposed['placements']) != refs:
            raise ValueError('Complete exact resistor/capacitor closure required')
        for ref in refs:
            if (parts[ref]['panel_uid'] or parts[ref]['dnp'] or parts[ref]['decouples_ref'] or
                    board_for(parts[ref]) != 'P' or prior[ref]['fixed'] or prior[ref]['side'] != 'B.Cu'):
                raise ValueError('Debounce placement cannot move fixed, bypass or non-P hardware')
        moving |= refs
    grid = Grid('P', 'B.Cu', source['boards']['P']['outline'])
    for p in parts.values():
        if board_for(p) == 'P' and p['panel_uid']:
            for _, box in pads(p, lock): grid.fill(box)
    for header in connectors['headers']:
        if header['board'] == 'P' and header['side'] == 'B.Cu': grid.fill(header['land_courtyard_mm'])
    for x,y in source['boards']['P']['supports_mm']: grid.fill([x-1.6,y-1.6,x+1.6,y+1.6])
    for x in optical['support']['x_mm']:
        for y in optical['support']['y_mm']:
            if y >= 176: grid.fill([x-1.6,y-1.6,x+1.6,y+1.6])
    for reserve in source['boards']['P'].get('reserves', []):
        if 'B.Cu' in reserve['sides']: grid.fill(reserve['rect'])
    for row in placements:
        if row['board'] == 'P' and not row['fixed'] and row['ref'] not in moving:
            grid.fill(row['courtyard_mm'])
    # Existing locality stages also rasterize the new parts when replayed.
    # Check their query boxes in that direction to keep staged replay stable.
    retained_bounds = [(math.floor(r['courtyard_mm'][0]*grid.scale),
                        math.floor(r['courtyard_mm'][1]*grid.scale),
                        math.ceil(r['courtyard_mm'][2]*grid.scale),
                        math.ceil(r['courtyard_mm'][3]*grid.scale))
                       for r in placements if r['board']=='P' and not r['fixed'] and r['ref'] not in moving]
    new = {}
    for key in sorted(expected):
        for ref, pose in proposal['groups'][key]['placements'].items():
            if set(pose) != {'x_mm','y_mm','rotation_deg'} or any(
                    type(v) not in (int,float) or not math.isfinite(v) for v in pose.values()):
                raise ValueError('Finite complete debounce pose required')
            x,y,angle = pose['x_mm'],pose['y_mm'],pose['rotation_deg']
            if type(angle) is not int or angle not in (0,90,180,270):
                raise ValueError('Integer orthogonal debounce pose required')
            b = oriented_box(shapes[parts[ref]['footprint']], 'B.Cu', angle)
            box = [b[0]+x,b[1]+y,b[2]+x,b[3]+y]
            if not inside_outline(Box(*box), source['boards']['P']['outline'], .30):
                raise ValueError('Debounce courtyard outside P: '+ref)
            x0,x1 = math.floor(box[0]*grid.scale),math.ceil(box[2]*grid.scale)
            y0,y1 = math.floor(box[1]*grid.scale),math.ceil(box[3]*grid.scale)
            mask = ((1 << (x1-x0))-1) << x0
            if any(row & mask for row in grid.rows[y0:y1]):
                raise ValueError('Debounce courtyard collides with retained geometry: '+ref)
            ex0,ey0 = math.floor((box[0]-.35)*grid.scale),math.floor((box[1]-.35)*grid.scale)
            ex1,ey1 = math.ceil((box[2]+.35)*grid.scale),math.ceil((box[3]+.35)*grid.scale)
            if any(ex0<rx1 and ex1>rx0 and ey0<ry1 and ey1>ry0 for rx0,ry0,rx1,ry1 in retained_bounds):
                raise ValueError('Debounce courtyard fails reverse-stage grid clearance: '+ref)
            if any(rect_collision(box, row['courtyard_mm'], .35) for row in new.values()):
                raise ValueError('Debounce courtyards overlap: '+ref)
            new[ref] = {**prior[ref], **pose, 'side':'B.Cu', 'courtyard_mm':box, 'debounce_group':key}
    final = {**prior, **new}
    def point(ref, pin, positions):
        pose = positions[ref]
        x,y = footprint_pads(parts[ref]['footprint'])[pin]
        x,y = turn((-x,y), pose['rotation_deg'])
        return x+pose['x_mm'],y+pose['y_mm']
    distances = []
    for key,g in expected.items():
        cap,series,pull = (g[k] for k in ('capacitor','series','pull'))
        row = {**g,
            'capacitor_to_input_mm':math.dist(point(cap,'1',final),point(g['schmitt_ref'],g['input_pin'],final)),
            'series_to_capacitor_mm':math.dist(point(series,'2',final),point(cap,'1',final)),
            'pull_to_series_mm':math.dist(point(pull,'2',final),point(series,'1',final))}
        if any(row[k+'_mm'] > limit+1e-9 for k,limit in LIMITS.items()):
            raise ValueError('Debounce group exceeds source distance target: '+key)
        distances.append(row)
    result = [new.get(row['ref'],row) for row in placements]
    if Counter(p['ref'] for p in result) != Counter(p['ref'] for p in placements):
        raise ValueError('Debounce locality changed package roster')
    return result, {'status':'Source courtyard and pad-distance screen only; native routing and physical qualification required',
        'moved_references':sorted(moving), 'limits_mm':dict(LIMITS), 'groups':distances,
        'maximum_capacitor_to_input_mm':max(r['capacitor_to_input_mm'] for r in distances)}
