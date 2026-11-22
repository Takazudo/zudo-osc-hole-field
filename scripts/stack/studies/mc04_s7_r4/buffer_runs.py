"""MC04-S7 Revision 7 item 1: on-board input-run estimates for the far input buffers.

For each non-inverting input of a high_impedance_input unit, the net's pins (floorplan poses, footprint pads; panel
parts from the placement lock) give a half-perimeter wire length (HPWL); the routed length is estimated as
1.5 x HPWL, and the capacitance with an ASSUMED 0.20 pF/mm (outer-layer trace over the continuous In1 AGND plane,
ground-flanked; a conservative upper value for a 0.2-0.25 mm trace on the 6-layer 1.6 mm stack-up). Paper only."""
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.checks.partition35_floorplan import pad_point, footprint_pads  # noqa: E402

PF_PER_MM = 0.20
ROUTE_FACTOR = 1.5
LIMIT_PF = 50.0


def poses(floor):
    lock = {p['uid']: p for p in json.loads((ROOT / 'design/grid/placements.lock.json').read_text())['placements']}
    return {p['ref']: p for p in floor['placements']}, lock


def pin_xy(ref, pin, P, pk, lock):
    p = pk[ref]
    if ref in P:
        q = P[ref]
        return pad_point(p['footprint'], pin, q['side'], q['rotation_deg'], q['x_mm'], q['y_mm'])
    if p['panel_uid'] in lock:
        L = lock[p['panel_uid']]
        x, y = footprint_pads(p['footprint'])[pin]
        a = math.radians(L['rot_deg'])
        return (L['x_mm'] + x * math.cos(a) - y * math.sin(a), L['y_mm'] + x * math.sin(a) + y * math.cos(a))
    return None


def run(ics=('U5112', 'U4646', 'U5113')):
    io = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    pk = {p['ref']: p for p in io['physical_packages']}
    net_pins = {}
    for u in io['package_units']:
        for pin, n in (u.get('pins') or {}).items():
            if n:
                net_pins.setdefault(n, []).append((u['ref'], pin))
    net_pins_by_ref = {}
    for u in io['package_units']:
        net_pins_by_ref.setdefault(u['ref'], {}).update(u.get('pins') or {})
    floor = json.loads((ROOT / 'design/partition/floorplan-candidate.json').read_text())
    base = json.loads(subprocess.run(['git', '-C', str(ROOT), 'show', '6093081c:design/partition/floorplan-candidate.json'],
                                     capture_output=True, text=True, check=True).stdout)
    P, lock = poses(floor)
    P0, _ = poses(base)
    out = []
    for ic in ics:
        units = [u for u in io['package_units'] if u['ref'] == ic]
        for u in units:
            role = u['role']
            if not role.startswith('high_impedance_input:'):
                continue
            plus = {'1': '3', '2': '5', '3': '10', '4': '12'}.get(str(u['unit']))
            if not plus or plus not in u['pins']:
                continue
            net = u['pins'][plus]
            row = {'ic': ic, 'unit': u['unit'], 'role': role, 'input_net': net,
                   'members': sorted({r for r, _ in net_pins[net]})}
            for label, PP in (('now', P), ('pre_move', P0)):
                pts = [pin_xy(r, pin, PP, pk, lock) for r, pin in net_pins[net]]
                pts = [q for q in pts if q]
                hp = (max(x for x, _ in pts) - min(x for x, _ in pts)) + (max(y for _, y in pts) - min(y for _, y in pts))
                row[label] = {'hpwl_mm': round(hp, 1), 'routed_estimate_mm': round(ROUTE_FACTOR * hp, 1),
                              'capacitance_estimate_pF': round(ROUTE_FACTOR * hp * PF_PER_MM, 1)}
            row['added_capacitance_estimate_pF'] = round(row['now']['capacitance_estimate_pF'] - row['pre_move']['capacitance_estimate_pF'], 1)
            row['within_50pF'] = row['now']['capacitance_estimate_pF'] <= LIMIT_PF
            # where the input passives sit: distance of each from the buffer input pin and from the jack pin of the
            # protected node on its other side
            bx, by = pin_xy(ic, plus, P, pk, lock)
            ends = {}
            for r, pin in net_pins[net]:
                if r == ic:
                    continue
                q = pin_xy(r, pin, P, pk, lock)
                ends[r] = {'to_buffer_mm': round(math.hypot(q[0] - bx, q[1] - by), 1)}
                other = [n for k, n in (net_pins_by_ref.get(r) or {}).items() if n not in (net, None, 'AGND', '+12V', '-12V')]
                jack = [(rr, pp) for n in other for rr, pp in net_pins.get(n, []) if pk[rr]['panel_uid']]
                if jack:
                    jx, jy = pin_xy(jack[0][0], jack[0][1], P, pk, lock)
                    ends[r]['to_jack_mm'] = round(math.hypot(q[0] - jx, q[1] - jy), 1)
                    ends[r]['jack'] = jack[0][0]
            row['input_passives'] = ends
            out.append(row)
    return {'assumed': {'pF_per_mm': PF_PER_MM, 'route_factor': ROUTE_FACTOR, 'limit_pF': LIMIT_PF}, 'runs': out}


if __name__ == '__main__':
    r = run()
    Path(__file__).with_name('buffer-runs.json').write_text(json.dumps(r, indent=1) + '\n')
    for x in r['runs']:
        print(x['ic'], x['unit'], x['input_net'], x['pre_move']['capacitance_estimate_pF'], x['now'], x['within_50pF'], x['input_passives'])
