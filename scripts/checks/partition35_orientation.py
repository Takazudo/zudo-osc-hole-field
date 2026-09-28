#!/usr/bin/env python3
"""Pinned KiCad in-memory courtyard/pin oracle; never saves a PCB."""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(ROOT))
from scripts.checks.partition35_json import dumps
OUT=ROOT/'design/partition/orientation-oracle.json'


def build():
    io=json.loads((ROOT/'design/reports/io-partition.json').read_text());floor=json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text());partition=json.loads((ROOT/'design/partition/partition.json').read_text());parts={p['ref']:p for p in io['physical_packages']}
    cases={}
    for p in floor['placements']:cases.setdefault((parts[p['ref']]['footprint'],p['side'],p['rotation_deg']),p)
    for h in partition['connectors']:
        cases.setdefault(('zudo-osc-hole-field:JST_GH%d_BM_TopEntry'%h['contacts'],h['side'],h['rotation_deg']),{'ref':h['pcb_reference'],'x_mm':h['footprint_origin_mm'][0],'y_mm':h['footprint_origin_mm'][1],'courtyard_mm':h['land_courtyard_mm'],'side':h['side'],'rotation_deg':h['rotation_deg'],'kicad_orientation_deg':h['kicad_orientation_deg']})
    b=pcbnew.BOARD();rows=[];errors=[];cache={};padcache={}
    for (name,side,theta),p in sorted(cases.items()):
        fp=pcbnew.FootprintLoad(str(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'),name.split(':')[1]);b.Add(fp);fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(p['x_mm']),pcbnew.FromMM(p['y_mm'])))
        if side=='B.Cu':fp.Flip(fp.GetPosition(),False)
        fp.SetOrientationDegrees(p['kicad_orientation_deg'])
        layer=pcbnew.B_CrtYd if side=='B.Cu' else pcbnew.F_CrtYd
        box=fp.GetCourtyard(layer).BBox();actual=[pcbnew.ToMM(box.GetLeft()),pcbnew.ToMM(box.GetTop()),pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom())]
        points=[]
        for item in fp.GraphicalItems():
            if item.GetLayer()!=layer:continue
            for pt in (item.GetStart(),item.GetEnd()):points.append((pcbnew.ToMM(pt.x),pcbnew.ToMM(pt.y)))
        lines=[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)]
        delta=max(abs(a-v) for a,v in zip(lines,p['courtyard_mm']))
        halo=max(abs(a-v) for a,v in zip(actual,lines))
        if halo>.050001:errors.append(name+' cached courtyard inflation exceeds reserved0.05mm')
        if delta>1e-5:errors.append(name+' '+side+' '+str(theta)+' courtyard transform differs '+str(actual)+' '+str(p['courtyard_mm']))
        cache[name,side,theta]=[v-a for v,a in zip(actual,lines)]
        padboxes=[]
        for pad in fp.Pads():
            if pad.GetAttribute() not in (pcbnew.PAD_ATTRIB_PTH,pcbnew.PAD_ATTRIB_NPTH):continue
            pb=pad.GetBoundingBox();padboxes.append([pcbnew.ToMM(pb.GetLeft())-p['x_mm'],pcbnew.ToMM(pb.GetTop())-p['y_mm'],pcbnew.ToMM(pb.GetRight())-p['x_mm'],pcbnew.ToMM(pb.GetBottom())-p['y_mm']])
        padcache[name,side,theta]=padboxes
        rows.append({'footprint':name,'side':side,'source_clockwise_rotation_deg':theta,'kicad_orientation_deg':p['kicad_orientation_deg'],'representative_ref':p['ref'],'max_drawn_courtyard_delta_mm':delta,'native_cached_courtyard_inflation_mm':halo,'reserved_cache_inflation_mm':.05})
    # Apply actual cached native envelopes to EVERY new J placement, not just
    # the representative classes. Fixed jack pairs are owner-locked exceptions;
    # free parts and interfaces retain the project 0.25 mm native clearance.
    placements=[];holes=defaultdict(list)
    for p in floor['placements']:
        if p['board'] not in ('JL','JR'):continue
        key=(parts[p['ref']]['footprint'],p['side'],p['rotation_deg']);delta=cache[key]
        placements.append({**p,'native_box':[v+d for v,d in zip(p['courtyard_mm'],delta)]})
        for q in padcache[key]:holes[p['board']].append((p['ref'],[q[0]+p['x_mm'],q[1]+p['y_mm'],q[2]+p['x_mm'],q[3]+p['y_mm']]))
    for h in partition['connectors']:
        if h['board'] not in ('JL','JR'):continue
        key=('zudo-osc-hole-field:JST_GH%d_BM_TopEntry'%h['contacts'],h['side'],h['rotation_deg'])
        placements.append({'ref':h['pcb_reference'],'board':h['board'],'side':h['side'],'fixed':False,'native_box':[v+d for v,d in zip(h['land_courtyard_mm'],cache[key])]})
    buckets=defaultdict(list);minimum=100;worst=[];checked=0
    board_shapes={b['board_key']:b['outline'] for b in partition['boards']}
    edge_minimum=100
    for p in placements:
        a=p['native_box'];poly=board_shapes[p['board']];edge_gap=min(a[0]-min(v[0] for v in poly),a[1]-min(v[1] for v in poly),max(v[0] for v in poly)-a[2],max(v[1] for v in poly)-a[3]);edge_minimum=min(edge_minimum,edge_gap)
        if edge_gap<.24999:errors.append('native J courtyard/edge '+p['ref'])
        a=p['native_box'];cells=[(p['board'],p['side'],x,y) for x in range(math.floor((a[0]-.25)/20),math.floor((a[2]+.25)/20)+1) for y in range(math.floor((a[1]-.25)/20),math.floor((a[3]+.25)/20)+1)];seen=set()
        for cell in cells:
            for q in buckets[cell]:
                if q['ref'] in seen or p['fixed'] and q['fixed']:continue
                seen.add(q['ref']);bb=q['native_box'];distance=max(bb[0]-a[2],a[0]-bb[2],bb[1]-a[3],a[1]-bb[3]);checked+=1
                if distance<minimum:minimum=distance;worst=[p['ref'],q['ref']]
                if distance<.24999:errors.append('native J courtyard clearance '+p['ref']+' '+q['ref']+' '+str(distance))
        for cell in cells:buckets[cell].append(p)
        if not p['fixed']:
            for ref,q in holes[p['board']]:
                if max(q[0]-a[2],a[0]-q[2],q[1]-a[3],a[1]-q[3])<.24999:errors.append('native J courtyard/THT pad '+p['ref']+' '+ref)
    jcheck={'checked_package_and_header_count':len(placements),'nearby_pairs_checked':checked,'minimum_native_courtyard_clearance_mm':minimum,'limiting_pair':worst,'required_mm':.25,'minimum_native_edge_gap_mm':edge_minimum,'clearance_basis':'0.350 mm drawn gap minus two native cached0.045 mm edge expansions =0.260 mm; unchanged0.250 mm native requirement','scope':'Every JL/JR footprint and header; free-vs-fixed/free pairs plus native THT pads on both faces. Fixed hardware pair positions unchanged. Actual PCB routing/DRC NOT RUN #38.'}
    return {'schema_version':1,'oracle':'KiCad10.0.6 in-memory footprint loading via scripts/kicad/run.sh; no PCB saved','status':'FAIL' if errors else 'PASS - all used footprint/face/rotation classes match native drawn coordinates; cached courtyard inflation <=0.05mm','errors':errors,'J_all_placements':jcheck,'cases':rows,'physical_fit':'NOT RUN; transform equality is not a solid-body/tolerance/installed fit test'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();r=build();text=dumps(r)+'\n'
    if args.check:
        if not OUT.exists() or OUT.read_text()!=text:raise SystemExit('orientation oracle drift')
    else:OUT.write_text(text)
    print(r['status'],len(r['cases']),'classes')
    if r['errors']:raise SystemExit('\n'.join(r['errors']))
