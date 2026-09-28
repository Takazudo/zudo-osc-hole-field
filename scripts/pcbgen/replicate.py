#!/usr/bin/env python3
"""Copy local routing from one placed instance to translated siblings on one board."""
from __future__ import annotations
import argparse,collections,json,sys
from pathlib import Path
import pcbnew
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.definition import load_definition
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.place import normalize_block,component_keys

def uid(item):return item.m_Uuid.AsString()
def xy(item):return (item.GetPosition().x,item.GetPosition().y)
def translations(definition,source):
    regions={r['instance']:r for r in definition.regions}
    if source not in regions:raise ValueError(f'source instance {source!r} has no placement region')
    base=regions[source]
    return {name:(pcbnew.FromMM(r['rect'][0]-base['rect'][0]),pcbnew.FromMM(r['rect'][1]-base['rect'][1]))
            for name,r in regions.items() if name!=source and r['family']==base['family'] and r['side']==base['side'] and
            abs((r['rect'][2]-r['rect'][0])-(base['rect'][2]-base['rect'][0]))<1e-6 and
            abs((r['rect'][3]-r['rect'][1])-(base['rect'][3]-base['rect'][1]))<1e-6}

def replicate(board_id,board_path,source,report_path,targets=None):
    definition=load_definition(ROOT/'design/boards'/f'{board_id}.json')
    board=pcbnew.LoadBoard(str(board_path));board.SetFileName(str(board_path))
    components,pin_nets=read_netlist(ROOT/definition.netlist)
    by_block=collections.defaultdict(list)
    for c in components:
        block=normalize_block(c)
        if block:by_block[block].append(c)
    if source not in by_block:raise ValueError(f'no components in source {source}')
    shifts=translations(definition,source)
    if targets is not None:shifts={k:v for k,v in shifts.items() if k in targets}
    if not shifts:raise ValueError('no translated targets')
    footprints={fp.GetReference():fp for fp in board.GetFootprints()}
    base=dict(component_keys(by_block[source]))
    source_refs={c.ref for c in by_block[source]}
    net_refs=collections.defaultdict(set)
    for (ref,_),net in pin_nets.items():net_refs[net].add(ref)
    tracks=list(board.GetTracks());original={uid(x) for x in tracks};zones={uid(z) for z in board.Zones()}
    existing_nets={x.GetNetname() for x in tracks}
    report={'schema_version':1,'board_id':board_id,'status':'REPLICATED DRAFT','source':source,'targets':{},'copied_track_count':0,'copied_via_count':0,'skipped_existing_nets':[]}
    for target,(dx,dy) in sorted(shifts.items()):
        match=dict(component_keys(by_block[target]))
        if set(match)!=set(base):raise ValueError(f'{target}: component Role/footprint signature differs')
        refs={base[k].ref:match[k].ref for k in base}
        for a,b in refs.items():
            left=footprints[a];right=footprints[b]
            if left.GetLayer()!=right.GetLayer() or xy(right)!=(xy(left)[0]+dx,xy(left)[1]+dy):raise ValueError(f'{target}: placement is not translation-identical at {a}/{b}')
            source_pads={p.GetNumber():p for p in left.Pads()};target_pads={p.GetNumber():p for p in right.Pads()}
            if source_pads.keys()!=target_pads.keys():raise ValueError(f'{target}: pad identity differs at {a}/{b}')
            for pad in source_pads:
                if xy(target_pads[pad])!=(xy(source_pads[pad])[0]+dx,xy(source_pads[pad])[1]+dy):raise ValueError(f'{target}: pad layout differs at {a}/{b}')
        mapping={}
        for (ref,pad),net in pin_nets.items():
            if ref not in source_refs or not net_refs[net].issubset(source_refs):continue
            other=pin_nets.get((refs[ref],pad))
            if other is None:continue
            if net in mapping and mapping[net]!=other:raise ValueError(f'{target}: net mapping for {net} is inconsistent')
            mapping[net]=other
        copied=0;vias=0
        for old,new in sorted(mapping.items()):
            if old==new:continue
            target_net=board.FindNet(new)
            if target_net is None:raise ValueError(f'{target}: mapped net {new!r} absent')
            if new in existing_nets:
                report['skipped_existing_nets'].append(new);continue
            source_items=[item for item in tracks if item.GetNetname()==old]
            if not source_items:continue
            for item in source_items:
                clone=item.Duplicate();clone.SetParent(board);clone.Move(pcbnew.VECTOR2I(dx,dy));clone.SetNet(target_net);clone.SetLocked(True);board.Add(clone)
                copied+=1;vias+=isinstance(clone,pcbnew.PCB_VIA)
            existing_nets.add(new)
        report['targets'][target]={'shift_mm':[round(pcbnew.ToMM(dx),4),round(pcbnew.ToMM(dy),4)],'copied_track_and_via_count':copied,'copied_via_count':vias}
        report['copied_track_count']+=copied-vias;report['copied_via_count']+=vias
    if original-{uid(x) for x in board.GetTracks()}:raise RuntimeError('replication removed an existing track')
    if zones!={uid(z) for z in board.Zones()}:raise RuntimeError('replication removed an existing zone')
    if report['copied_track_count'] or report['copied_via_count']:pcbnew.SaveBoard(str(board_path),board)
    else:report['status']='UNCHANGED DRAFT'
    report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(f'{board_id}: copied {report["copied_track_count"]} tracks and {report["copied_via_count"]} vias to {len(shifts)} targets; {report["status"]}')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('board_id');p.add_argument('--board',type=Path);p.add_argument('--source',default='S1');p.add_argument('--targets',nargs='*');p.add_argument('--report',type=Path)
    a=p.parse_args();board=a.board or ROOT/'boards'/a.board_id/f'{a.board_id}.kicad_pcb';report=a.report or board.parent/'reports/replication.json'
    replicate(a.board_id,board,a.source,report,a.targets)
if __name__=='__main__':main()
