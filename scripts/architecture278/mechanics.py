#!/usr/bin/env python3
"""Bounded source-only geometry; no CAD/native execution. Outputs never qualify fit."""
import argparse
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'design/architecture-278'
SOURCES = ['design/grid/placements.lock.json', 'design/mechanical/selector-assembly.json',
 'design/partition/partition.json', 'design/partition/loom-candidate.json',
 'design/partition/mechanical-candidate.json', 'design/mechanical/facts/jack.json',
 'design/mechanical/facts/pot.json', 'design/connectors/jst-gh.json',
 'design/partition/harness-wire-evidence.json', 'design/architecture-278/source-ledger.json',
 'design/architecture-278/interface-contract.json', 'design/architecture-278/mechanical-input.json']

def read(path):
    return json.loads((ROOT / path).read_text())

def model(p=None):
    p = p or read(SOURCES[-1])
    lock, selector, partition, loom = [read(s) for s in SOURCES[:4]]
    contract = read(SOURCES[-2])
    assert len(lock['placements']) == 438
    assert len(contract['trims']) == 6
    assert len(contract['harnesses']) == 11
    assert sum(h['conductors'] for h in contract['harnesses']) == 51
    assert len(contract['shared_services']) == 13
    assert p['rear_face_z_mm'] < p['middle_face_z_mm'] < -33
    assert len(p['trim_y_mm']) == 6 and len(set(p['trim_y_mm'])) == 6
    positions = [a for a in lock['placements'] if a['block'] in ['O1', 'O2']]
    x = {a['block']:a['x_mm'] for a in positions if a['kind']=='octave'}
    assert x['O2'] - x['O1'] == 17
    assert [s['pcb_z_mm'] for s in selector['instances']] == [-16,-29,-16,-29,-16]
    gap = x['O2']-x['O1']-p['card_width_mm']
    assert gap >= p['free_clearance_mm'], 'adjacent rear card edge allocation lost'
    assert p['front_link_max_mm'] + p['rear_link_max_mm'] + p['middle_trace_max_mm'] <= 300
    # Depth is positive rearward in arithmetic below; display retains panel z convention.
    middle_gap = -33 - p['middle_face_z_mm'] - p['connector_height_allowance_mm'] - p['relative_plane_tolerance_mm']
    rear_gap = p['rear_face_z_mm']-p['pcb_thickness_mm']-p['component_rear_height_mm']-p['cover_inner_z_mm']-p['pcb_thickness_tolerance_mm']-p['relative_plane_tolerance_mm']
    interboard = p['middle_face_z_mm']-p['rear_face_z_mm']-p['pcb_thickness_mm']-2*p['connector_height_allowance_mm']-2*p['cable_bend_radius_allocation_mm']-p['relative_plane_tolerance_mm']-p['pcb_thickness_tolerance_mm']
    checks = [dict(name='rear selector to middle front connector allowance', margin_mm=round(middle_gap,3)),dict(name='rear component to closed cover',margin_mm=round(rear_gap,3)),dict(name='middle/rear opposed connectors plus two bend allocations',margin_mm=round(interboard,3)),dict(name='adjacent card edge',margin_mm=gap),dict(name='simultaneous adjacent finger cylinders',margin_mm=17-p['finger_diameter_mm'])]
    for c in checks:c['status']='CONDITIONAL ALLOCATION' if c['margin_mm']>=p['free_clearance_mm'] else 'CONFLICT; REVISE'
    assert p['cable_bend_radius_allocation_mm'] >= 9.398, 'retained Alpha 6821 bend minimum'
    assert len(p['card_y_mm']) == 2 and p['card_y_mm'][0] < p['card_y_mm'][1]
    checks.append(dict(name='external workspace minus extraction stroke',
        margin_mm=p['rear_external_work_depth_mm']-p['rear_extraction_stroke_mm'],
        status='CONDITIONAL ALLOCATION' if p['rear_external_work_depth_mm'] >= p['rear_extraction_stroke_mm'] else 'CONFLICT; REVISE'))
    reservations=[]
    for kind,ys,width,height in [
        ('trim',p['trim_y_mm'],p['tool_diameter_mm'],p['tool_diameter_mm']),
        ('probe',p['probe_y_mm'],p['probe_diameter_mm'],p['probe_diameter_mm']),
        ('support',p['support_y_mm'],p['support_collar_diameter_mm'],p['support_collar_diameter_mm']),
        ('connector',p['connector_y_mm'],p['connector_reservation_width_mm'],p['connector_reservation_length_mm'])]:
        assert width > 0 and height > 0
        for idx,y in enumerate(ys):
            reservations.append(dict(id=f'{kind}-{idx}',kind=kind,y=y,width=width,height=height))
            margin=min((p['card_width_mm']-width)/2, y-height/2-p['card_y_mm'][0], p['card_y_mm'][1]-y-height/2)
            checks.append(dict(name=f'{kind}-{idx} card containment',margin_mm=round(margin,3),status='CONDITIONAL ALLOCATION' if margin>=0 else 'CONFLICT; REVISE'))
        margin=17-width
        checks.append(dict(name=f'adjacent {kind} reservations',margin_mm=margin,status='CONDITIONAL ALLOCATION' if margin>=p['free_clearance_mm'] else 'CONFLICT; REVISE'))
    for i,a in enumerate(reservations):
        for b in reservations[i+1:]:
            gap=abs(a['y']-b['y'])-(a['height']+b['height'])/2
            checks.append(dict(name=f"same card {a['id']} / {b['id']} bounding-box separation",margin_mm=round(gap,3),status='CONDITIONAL ALLOCATION' if gap>=p['free_clearance_mm'] else 'CONFLICT; REVISE'))
    checks.append(dict(name='Exact latch/mating sweep, rail solids, neighbor components, cable solid curvature and deflection',status='NOT CHECKED; exact solids/forces unavailable'))
    routes = {r['id']:r for r in loom['routes']}
    harnesses=[]
    for h in contract['harnesses']:
        r=routes[h['id']]
        assert r['conductor_count']==h['conductors']
        harnesses.append(dict(id=h['id'],conductors=h['conductors'],returns=h['return_contacts'],baseline_cut_length_max_mm=r['cut_length_max_mm'],baseline_conductor_length_max_mm=h['conductors']*r['cut_length_max_mm'],baseline_mating_interfaces=2*h['conductors'],baseline_crimps=h['crimps'],candidate_segments=2*h['conductors'],candidate_mating_interfaces=4*h['conductors'],candidate_crimps=4*h['conductors'],candidate_front_link_max_mm=p['front_link_max_mm'],candidate_rear_link_max_mm=p['rear_link_max_mm'],candidate_conductor_length_max_mm=h['conductors']*(p['front_link_max_mm']+p['rear_link_max_mm']),final_status='Not a BOM: same-path two-link comparison; final services/returns and connector grouping OPEN'))
    trims=[dict(**t,proposed_xy_mm=[x['O1'],y],proposed_z_mm=p['rear_face_z_mm']-p['pcb_thickness_mm'],tool_diameter_mm=p['tool_diameter_mm'],status='Proposed rear-facing adjustment axis, exact body/actuator geometry OPEN') for t,y in zip(contract['trims'],p['trim_y_mm'])]
    return dict(status='REVISE; source-derived and proposed bounds only; physical qualification NOT RUN',source_sha256={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in SOURCES},parameters=p,locked_positions=positions,octave_instances=selector['instances'],selector_envelope=selector['drawing'],interference_table=checks,trims=trims,harnesses=harnesses,baseline_o1=dict(harnesses=11,conductors=51,crimps=102,mating_interfaces=102,cut_conductor_length_max_mm=sum(h['baseline_conductor_length_max_mm'] for h in harnesses)),candidate_o1_same_paths=dict(harnesses=22,conductor_segments=102,crimps=204,mating_interfaces=204,cut_conductor_length_max_mm=sum(h['candidate_conductor_length_max_mm'] for h in harnesses),additional_services='OPEN; 13 net classes, no inferred 13-pin connector',test_adapters='OPEN; excluded from final connection totals'),existing_rear_terminals=contract['rear_terminals'],blockers=['Exact J/P seating and enclosure/support force qualification absent', '15 mm rear-card width not placed or routed; rear terminal conversion and package fit unresolved', '20 mm finger envelopes overlap adjacent 17 mm pitch: sequential narrow-tool release required, exact latch force/tool unselected', 'Middle two-face connection multiplicity and service pinout unresolved; cannot certify assembly count', 'Alpha 6821 bend minimum 9.398 mm retained; 9 mm connector envelope remains allocation; installed cable solid NOT CHECKED', 'No stiffness/deflection or cover/support solids; side-frame rail and load path require owner enclosure constraints', 'All-six trim bodies and complete test-point positions need source/schematic/PCB implementation; HF trim exact identity absent'])

def drawing(r):
    p=r['parameters']; lines=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 400 300">','<rect width="400" height="300" fill="white"/>','<style>text{font:3px sans-serif} .proposal{fill:none;stroke:#c06020;stroke-dasharray:2 1} .fixed{fill:#164f70}</style>','<text x="4" y="5">#278 O1/O2 bounded reservations — mm — NOT qualified fit</text>']
    for a in r['locked_positions']:
        xx,yy=a['x_mm'],a['y_mm'];lines.append(f'<circle class="fixed" cx="{xx}" cy="{yy}" r="1"/><text x="{xx+2}" y="{yy-2 if "O1." in a["uid"] else yy+3}">{html.escape(a["uid"])}</text>')
    for x in [14.5,31.5]:
        lines.append(f'<rect class="proposal" x="{x-p["card_width_mm"]/2}" y="{p["card_y_mm"][0]}" width="{p["card_width_mm"]}" height="{p["card_y_mm"][1]-p["card_y_mm"][0]}"/>')
        for y in p['trim_y_mm']:lines.append(f'<circle class="proposal" cx="{x}" cy="{y}" r="{p["tool_diameter_mm"]/2}"/>')
        for y in p['connector_y_mm']:lines.append(f'<rect class="proposal" x="{x-p["connector_reservation_width_mm"]/2}" y="{y-p["connector_reservation_length_mm"]/2}" width="{p["connector_reservation_width_mm"]}" height="{p["connector_reservation_length_mm"]}"/>')
        for y in p['support_y_mm']:lines.append(f'<circle class="proposal" cx="{x}" cy="{y}" r="{p["support_collar_diameter_mm"]/2}"/>')
        for y in p['probe_y_mm']:lines.append(f'<circle fill="none" stroke="green" stroke-width="0.3" cx="{x}" cy="{y}" r="{p["probe_diameter_mm"]/2}"/>')
    for a in r['octave_instances'][:2]:
        xx=14.5 if a['uid']=='C:O1.OCT' else 31.5
        yy=174.5 if a['rotation_deg']==0 else 177
        lines.append(f'<rect fill="none" stroke="purple" stroke-width="0.3" x="{xx-9.1}" y="{yy}" width="18.2" height="18.5"/><text x="55" y="{181 if xx==14.5 else 186}">{a["uid"]}: z={a["pcb_z_mm"]}, rotation {a["rotation_deg"]} degrees</text>')
    for index,(label,z) in enumerate([('Panel',0),('Jack proposal',-10),('Control proposal',-11.8),('Octave front',-16),('Octave rear',-29),('Middle proposal',p['middle_face_z_mm']),('Rear card proposal',p['rear_face_z_mm']),('Cover proposal',p['cover_inner_z_mm'])]):
        xx=130-z;lines.append(f'<path d="M{xx} 25V175" stroke="#777" stroke-width="0.4"/><text x="{xx}" y="{18-index%3*4}">{index+1}</text><text x="275" y="{30+index*8}">{index+1}. {label}: z={z} mm</text>')
    notes=[f'Rearward extraction: {p["rear_extraction_stroke_mm"]} mm after unplugging; cover removed.', f'Reserve {p["rear_external_work_depth_mm"]} mm external work depth. No blind hot swap.', 'Orange: proposed card / tool / connector / support envelopes.', 'Green: GND, rail and measurement probe reservations.', 'Blue: exact locked panel centres, x=14.5 / 31.5; pitch=17.', 'Rear adjacent zones: O3+ reserved from x=40; no borrowing.', f'Finger diameter {p["finger_diameter_mm"]} mm at 17 pitch; see interference table.', 'Octave 3+2: O1/O3/O5 -16; O2/O4 -29.', 'GH 7.3 reference is NOT PCB spacing.', 'Rail paths, stiffness, cable solids and terminal conversion OPEN.']
    for i,t in enumerate(notes):lines.append(f'<text x="100" y="{200+i*6}">{html.escape(t)}</text>')
    lines.append('</svg>');return '\n'.join(lines)+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=model()
    for name,data in [('mechanical-report.json',json.dumps(r,indent=2,sort_keys=True)+'\n'),('mechanical-envelope.svg',drawing(r))]:
        path=OUT/name
        if args.check:
            if not path.exists() or path.read_text()!=data:raise SystemExit('STALE '+str(path))
        else:path.write_text(data)
    print('PASS source calculations/current outputs; mechanical fit NOT RUN; recommendation REVISE')
if __name__=='__main__':main()
