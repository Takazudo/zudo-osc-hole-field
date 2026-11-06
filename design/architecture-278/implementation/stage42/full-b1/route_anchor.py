"""Propose a real B.Cu approach to the retained +5V layer-transition anchor.

Only one newly added segment is replaced. Shared baseline copper stays intact.
Native necessary geometry screen; full identity/DRC/partitions remain mandatory.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import pcbnew
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'stage41/native-pilot'))
from native_guard import check_native
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.route_source_local import box_hit


def propose(path, signal_path, output):
    generated=[output,output.with_name('signal-proposal.json'),output.with_name('anchor-screen.json')]
    cache=(ROOT/'.circuit-cache').resolve()
    if len({p.resolve() for p in generated})!=3 or output.resolve().parent.parent!=cache or any(p.exists() or p.resolve() in (path.resolve(),signal_path.resolve()) for p in generated):raise ValueError('fresh disposable proposal outputs required')
    raw=path.read_text();board=pcbnew.LoadBoard(str(path));check_native(board,raw)
    signal=json.loads(signal_path.read_text())
    uid='ee856bc4-0c03-5c3a-b7d7-8efb9dd013be'
    matches=[r for r in signal['copper'] if r['uuid']==uid]
    if len(matches)!=1:raise ValueError('exact new approach missing')
    old=matches[0]
    if (old['net'],old['layer'],old['start_nm'],old['end_nm'],old['width_nm'])!=('+5V','In2.Cu',[133800000,202500000],[134900000,201400000],400000):raise ValueError('approach binding')
    pads=[p for f in board.GetFootprints() for p in f.Pads()]
    tracks=list(board.GetTracks());layers=list(board.GetEnabledLayers().CuStack())
    keepouts=[z for z in board.Zones() if z.GetIsRuleArea()]
    face=pcbnew.B_Cu
    def segment_clear(a, b, net):
        segment = pcbnew.SEG(a, b)
        clearance = pcbnew.FromMM(.25 + .4/2)
        if any(p.IsOnLayer(face) and p.GetNetname() != net and p.GetEffectiveShape(face).Collide(segment, clearance) for p in pads): return False
        if any(t.IsOnLayer(face) and t.GetNetname() != net and t.GetEffectiveShape(face).Collide(segment, clearance) for t in tracks): return False
        if any(z.IsOnLayer(face) and z.GetDoNotAllowTracks() and box_hit(z.GetBoundingBox(), a, b, clearance) for z in keepouts): return False
        return True
    def via_clear(at, net):
        shape = pcbnew.SHAPE_CIRCLE(at, pcbnew.FromMM(.35))
        for item in [*pads, *tracks]:
            if item.GetNetname() == net: continue
            if any(item.IsOnLayer(l) and item.GetEffectiveShape(l).Collide(shape, pcbnew.FromMM(.25)) for l in layers): return False
        for p in pads:
            if p.HasHole() and math.dist((at.x, at.y), (p.GetPosition().x, p.GetPosition().y)) < (max(p.GetDrillSize().x, p.GetDrillSize().y) + pcbnew.FromMM(.3))/2 + pcbnew.FromMM(.25): return False
        for t in tracks:
            if t.Type() == pcbnew.PCB_VIA_T and math.dist((at.x, at.y), (t.GetPosition().x, t.GetPosition().y)) < (t.GetDrillValue() + pcbnew.FromMM(.3))/2 + pcbnew.FromMM(.25): return False
        if any(z.GetDoNotAllowVias() and box_hit(z.GetBoundingBox(), at, at, pcbnew.FromMM(.6)) for z in keepouts): return False
        return True
    start=pcbnew.VECTOR2I(*old['start_nm']);end=pcbnew.VECTOR2I(*old['end_nm'])
    candidates=[];chosen=None
    for step in range(12):
        at=pcbnew.VECTOR2I(start.x+step*50000,start.y-step*50000)
        clear=segment_clear(at,end,'+5V') and via_clear(at,'+5V')
        candidates.append({'at_nm':[at.x,at.y],'necessary_clear':clear})
        if clear and chosen is None:chosen=at
    if chosen is None:raise ValueError('no screened anchor approach')
    rows=[]
    if (chosen.x,chosen.y)!=(start.x,start.y):rows.append(dict(old,start_nm=[start.x,start.y],end_nm=[chosen.x,chosen.y]))
    rows.append(dict(old,start_nm=[chosen.x,chosen.y],layer='B.Cu'))
    rows.append({'kind':'via','net':'+5V','at_nm':[chosen.x,chosen.y],'diameter_nm':700000,'drill_nm':300000,'layers':['F.Cu','B.Cu'],'locked':False})
    for r in rows:r['uuid']=stable_uuid('osc-jack-left','stage42-anchor',json.dumps({k:v for k,v in r.items() if k!='uuid'},sort_keys=True))
    output.write_text(json.dumps({'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'removed_uuids':[uid],'copper':rows},indent=2)+'\n')
    signal['copper']=[r for r in signal['copper'] if r['uuid']!=uid]+rows
    output.with_name('signal-proposal.json').write_text(json.dumps(signal,indent=2)+'\n')
    output.with_name('anchor-screen.json').write_text(json.dumps({'candidates':candidates,'chosen_nm':[chosen.x,chosen.y],'limits':'Necessary geometry screen only; full native checks required.'},indent=2)+'\n')
    print(json.dumps({'chosen_nm':[chosen.x,chosen.y],'added':len(rows),'replaced_new_segment':uid}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('board','signal','output'):p.add_argument(n,type=Path)
    a=p.parse_args();propose(a.board,a.signal,a.output)
