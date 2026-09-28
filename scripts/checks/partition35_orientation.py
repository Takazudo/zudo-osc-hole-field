#!/usr/bin/env python3
"""Pinned KiCad in-memory courtyard/pin oracle; never saves a PCB."""
import argparse
import json
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
    b=pcbnew.BOARD();rows=[];errors=[]
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
        rows.append({'footprint':name,'side':side,'source_clockwise_rotation_deg':theta,'kicad_orientation_deg':p['kicad_orientation_deg'],'representative_ref':p['ref'],'max_drawn_courtyard_delta_mm':delta,'native_cached_courtyard_inflation_mm':halo,'reserved_cache_inflation_mm':.05})
    return {'schema_version':1,'oracle':'KiCad10.0.6 in-memory footprint loading via scripts/kicad/run.sh; no PCB saved','status':'FAIL' if errors else 'PASS - all used footprint/face/rotation classes match native drawn coordinates; cached courtyard inflation <=0.05mm','errors':errors,'cases':rows,'physical_fit':'NOT RUN; transform equality is not a solid-body/tolerance/installed fit test'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();r=build();text=dumps(r)+'\n'
    if args.check:
        if not OUT.exists() or OUT.read_text()!=text:raise SystemExit('orientation oracle drift')
    else:OUT.write_text(text)
    print(r['status'],len(r['cases']),'classes')
    if r['errors']:raise SystemExit('\n'.join(r['errors']))
