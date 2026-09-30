#!/usr/bin/env python3
"""Audit draft compact LED land/courtyard geometry at every immutable R21 centre."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from scripts.libgen.gen_courtyards import parse, walk, node_name, child, numbers, pad_box, courtyard_box

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / 'footprints/kicad/zudo-osc-hole-field.pretty'
LOCK = ROOT / 'design/grid/placements.lock.json'
OUTPUT = ROOT / 'design/reports/compact-led-fit.json'
FILES = {'white':'LED0402-Kingbright-White', 'red':'LED0402-Kingbright-Red',
         'jack':'Jack_3.5mm_QingPu_WQP518MA', 'pot':'PTV09A-4020F'}

def footprint(name):
    path = LIB / f'{FILES[name]}.kicad_mod'
    raw = path.read_bytes(); tree = parse(raw.decode())
    pads=[]
    for node in walk(tree):
        if node_name(node)=='pad':
            box=pad_box(node)
            if box:pads.append({'number':str(node[1]),'box':box,'through_hole':node[2]=='thru_hole'})
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),
            'courtyard':courtyard_box(raw.decode()),'pads':pads}

def place(box, row):
    assert row['rot_deg']==0, row['uid']
    return [round(box[0]+row['x_mm'],5),round(box[1]+row['y_mm'],5),round(box[2]+row['x_mm'],5),round(box[3]+row['y_mm'],5)]

def gap(a,b):
    dx=max(b[0]-a[2],a[0]-b[2],0)
    dy=max(b[1]-a[3],a[1]-b[3],0)
    return round((dx*dx+dy*dy)**.5,5)

def overlaps(a,b):return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]

def main():
    spec={k:footprint(k) for k in FILES}
    placements=json.loads(LOCK.read_text())['placements']; uids={x['uid']:x for x in placements}
    leds=[x for x in placements if x['kind']=='led']; assert len(leds)==114
    assert sum(x['led_type']=='mag' for x in leds)==92
    assert sum(x['led_type']=='clip' for x in leds)==10
    assert sum(x['led_type']=='stage' for x in leds)==12
    hardware=[x for x in placements if x['kind'] in ('jack','pot')]
    rows=[]
    for led in leds:
        color='red' if led['led_type']=='clip' else 'white'; fp=spec[color]
        court=place(fp['courtyard'],led)
        pads=[{'number':p['number'],'box_mm':place(p['box'],led)} for p in fp['pads']]
        neighbors=[]
        for hw in hardware:
            hfp=spec[hw['kind']]; hc=place(hfp['courtyard'],hw)
            if gap(court,hc)>15:continue
            hpads=[place(p['box'],hw) for p in hfp['pads']]
            neighbors.append({'uid':hw['uid'],'kind':hw['kind'],'parent':led['parent']==hw['uid'],
                              'courtyard_gap_mm':gap(court,hc),'courtyard_overlap':overlaps(court,hc),
                              'pad_to_pad_gap_mm':min(gap(p['box_mm'],h) for p in pads for h in hpads),
                              'pad_overlap':any(overlaps(p['box_mm'],h) for p in pads for h in hpads)})
        other=[]
        for x in leds:
            if x['uid']==led['uid']:continue
            xc=place(spec['red' if x['led_type']=='clip' else 'white']['courtyard'],x)
            if gap(court,xc)>5:continue
            xpads=[place(p['box'],x) for p in spec['red' if x['led_type']=='clip' else 'white']['pads']]
            other.append({'uid':x['uid'],'courtyard_gap_mm':gap(court,xc),'courtyard_overlap':overlaps(court,xc),
                          'pad_to_pad_gap_mm':min(gap(p['box_mm'],q) for p in pads for q in xpads),
                          'pad_overlap':any(overlaps(p['box_mm'],q) for p in pads for q in xpads)})
        rows.append({'uid':led['uid'],'ref':led['ref'],'type':led['led_type'],'parent':led['parent'],
                     'centre_mm':[led['x_mm'],led['y_mm']],'rot_deg':led['rot_deg'],
                     'footprint':fp['path'],'package_height_mm':0.5 if color=='white' else 0.2,
                     'courtyard_box_mm':court,'pads':pads,'hardware_neighbors':neighbors,'led_neighbors':other})
    jack=[r for r in rows if r['type'] in ('mag','clip')]
    assert len(jack)==102 and all(uids[r['parent']]['kind']=='jack' for r in jack)
    assert all({p['number'] for p in r['pads']}=={'1','2'} for r in rows)
    assert not any(n['courtyard_overlap'] or n['pad_overlap'] for r in jack for n in r['hardware_neighbors'])
    assert not any(n['courtyard_overlap'] or n['pad_overlap'] for r in jack for n in r['led_neighbors'])
    pairs=[(r,n) for r in jack for n in r['led_neighbors'] if n['uid'].endswith('.clip') and r['uid'].endswith('.mag')]
    assert len(pairs)==10
    stage=[r for r in rows if r['type']=='stage']
    report={'schema_version':1,'status':'CONDITIONAL DRAFT; 2D source footprint envelopes only; no assembled fit or optical qualification',
            'lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'footprints':spec,
            'counts':{'indicators':114,'jack_indicators':102,'magnitude':92,'clip':10,'stage':12,'jack_led_pairs':10,'pads_checked':228},
            'jack_minimum_courtyard_gap_mm':min(n['courtyard_gap_mm'] for r in jack for n in r['hardware_neighbors']),
            'jack_minimum_pad_gap_mm':min(n['pad_to_pad_gap_mm'] for r in jack for n in r['hardware_neighbors']),
            'paired_minimum_courtyard_gap_mm':min(n['courtyard_gap_mm'] for _,n in pairs),
            'paired_minimum_pad_gap_mm':min(n['pad_to_pad_gap_mm'] for _,n in pairs),
            'stage_same_face_courtyard_conflicts':[r['uid'] for r in stage if any(n['courtyard_overlap'] for n in r['hardware_neighbors'])],
            'stage_same_face_pad_conflicts':[r['uid'] for r in stage if any(n['pad_overlap'] for n in r['hardware_neighbors'])],
            'rows':rows}
    OUTPUT.write_text(json.dumps(report,indent=2)+'\n')
    print(f"PASS: {len(jack)} jack LEDs, {len(pairs)} pairs, 228 pads; minimum jack courtyard gap {report['jack_minimum_courtyard_gap_mm']} mm; stage plane conflicts recorded")
if __name__=='__main__':main()
