#!/usr/bin/env python3
"""OSC4: extract the named open residuals of the accepted K, JL and JR boards from their text.

Host-only, read-only analysis (no pcbnew, no refill, no DRC, no routing). Islands
come from scripts/checks/board_text_geometry.py and are compared with the native
open-edge counts recorded in the boards' receipts; a mismatch is reported, not
hidden. Each open edge is named by its nearest endpoints, and a straight-corridor
estimate lists the foreign copper that blocks it on each signal layer. The
corridor estimate is a planning input for one bounded native transaction per
board; it is not a route, and an empty corridor does not prove a route exists.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/checks'))
import board_text_geometry as g

BOARDS={
    # K3363 (2c1d67b7..., osc3-k-pilot.json) was replaced by K2518 on 2026-11-07 (manager adoption of wsl-20261107a).
    'osc-core':{'sha256':'7251dd933af810b7c659c9b90c6f6d9ba32d55ea432b0414c26c8b26b6b4be42','label':'K2518',
                'native':'circuit/reviews/osc3-k-signals/wsl-20261107a-adoption.json'},
    'osc-jack-left':{'sha256':'a7fe68606591186cc955178b949e1c5ce8df0d0ba5829d328bb6bebb119ca251','label':'JL184',
                     'native':'boards/osc-jack-left/reports/grid-routing/rrr-01.json'},
    'osc-jack-right':{'sha256':'f6106300bae4e253f4b869dd24d14cb2428715215917b33ebacaa0f9031bfaa8','label':'JR192',
                      'native':'boards/osc-jack-right/reports/grid-routing/rrr-01.json'},
}
RAILS=('+12V','-12V','+5V');PLANES={'+12V':'In4.Cu','-12V':'In3.Cu'}
SIGNAL_LAYERS=('F.Cu','In2.Cu','In3.Cu','B.Cu')
# Router defaults of the signal stages in scripts/pcbgen/route_jack_grid.py (clearance 0.2, width 0.2).
CLEARANCE=0.2;SIGNAL_WIDTH=0.2;HALF=CLEARANCE+SIGNAL_WIDTH/2
# Ground-corridor repair and rail stages: clearance 0.25, width 0.3 (route_jack_grid.py stage()).
RAIL_HALF=0.25+0.3/2
# scripts/pcbgen/route_jack_grid.py repair_selection()/repair_bounds() limits.
MAX_CUTS=12;MAX_VICTIMS=2;MAX_FRAME_MM=50.0


def native_counts(board_id):
    d=json.loads((ROOT/BOARDS[board_id]['native']).read_text())
    if d.get('schema')=='osc3-k-adoption-1':
        r=d['review_summary'];rails={n:r['rail_open_edges'][n] for n in RAILS}
        return {'source':BOARDS[board_id]['native'],'bound_sha256':d['candidate_board_sha256'],
                'open_edges':r['open_edges']['after'],'by_net':{**rails,'AGND':r['agnd']['open_edges']}}
    if board_id=='osc-core':
        a=d['after'];return {'source':BOARDS[board_id]['native'],'bound_sha256':d['final_gate']['candidate_board_sha256'],
                             'open_edges':a['open_edges'],'by_net':{**a['rail_open_edges'],'AGND':a['agnd_open_edges']}}
    return {'source':BOARDS[board_id]['native'],'bound_sha256':d['candidate_board_sha256'],'open_edges':d['open_edges_after'],
            'by_net':d['open_by_net_after']}


def label(item,pads,segs,vias):
    if item.startswith('pad:'):
        p=pads[item];return {'kind':'pad','ref':item[4:],'uuid':p['uuid'],'layers':[l for l in p['layers'] if l.endswith('.Cu')],
                             'xy':[round(p['x'],3),round(p['y'],3)]}
    if item.startswith('via:'):
        v=vias[item];return {'kind':'via','uuid':item[4:],'xy':list(v['xy'])}
    s=segs[item];return {'kind':'track','uuid':item[4:],'layer':s['layer']}


class Index:
    def __init__(self,board,pads):
        self.keepouts=collections.defaultdict(list)
        for z in board.zones:
            if z['keepout'] and z['keepout'].get('tracks')=='not_allowed':
                for l in z['layers']:self.keepouts[l].append((z['name'],z['outline']))
        self.segs=collections.defaultdict(lambda:g.Grid(2.0));self.vias=g.Grid(2.0);self.pads=collections.defaultdict(lambda:g.Grid(2.0))
        for s in board.segments:self.segs[s['layer']].add(g.seg_bbox(s),s)
        for v in board.vias:r=v['size']/2;self.vias.add((v['xy'][0]-r,v['xy'][1]-r,v['xy'][0]+r,v['xy'][1]+r),v)
        for lab,p in pads.items():
            for l in board.copper_layers:
                if g.pad_on_layer(p,l):self.pads[l].add(p['bbox'],(lab,p))
        # Pads without a net (mounting holes) block too.
        for f in board.footprints.values():
            for p in f.pad_shapes():
                if not p['net']:
                    for l in board.copper_layers:
                        if g.pad_on_layer(p,l):self.pads[l].add(p['bbox'],(f'pad:{f.ref}.{p["num"]}',p))


def corridor(index,a,b,net,layer):
    """Foreign copper within router clearance of the straight a-b path on one layer."""
    HALF=RAIL_HALF if net in (*RAILS,'AGND') else globals()['HALF']
    pad=HALF+0.5;bb=(min(a[0],b[0])-pad,min(a[1],b[1])-pad,max(a[0],b[0])+pad,max(a[1],b[1])+pad)
    cut=[];fixed=[]
    for s in index.segs[layer].query(bb):
        if s['net']==net:continue
        if g.seg_seg_dist(a,b,s['a'],s['b'])<=HALF+s['w']/2:
            (fixed if s['net'] in (*RAILS,'AGND') else cut).append({'kind':'track','uuid':s['uuid'],'net':s['net'],'layer':layer})
    for v in index.vias.query(bb):
        if v['net']==net:continue
        if g.seg_point_dist(v['xy'],a,b)<=HALF+v['size']/2:
            (fixed if v['net'] in (*RAILS,'AGND') else cut).append({'kind':'via','uuid':v['uuid'],'net':v['net'],'xy':list(v['xy'])})
    for lab,p in index.pads[layer].query(bb):
        if p['net']==net:continue
        if g.seg_rect_dist({'a':a,'b':b},p['bbox'])<=HALF:fixed.append({'kind':'pad','ref':lab[4:],'net':p['net']})
    for name,poly in index.keepouts[layer]:
        pts=[a,b,((a[0]+b[0])/2,(a[1]+b[1])/2)]
        crosses=any(g.point_in_poly(x,y,poly) for x,y in pts) or any(
            g.seg_seg_dist(a,b,poly[i],poly[(i+1)%len(poly)])<=HALF for i in range(len(poly)))
        if crosses:fixed.append({'kind':'keepout','name':name})
    return cut,fixed


def candidate(row):
    """An edge whose straight corridor is opened by a few explicit cuts on one layer, and by nothing else."""
    layers=row['corridor']
    clear=[l for l,v in layers.items() if v['fixed']==0 and v['cuttable']==0]
    usable=[(v['cuttable'],len(v['victim_nets']),l) for l,v in layers.items()
            if v['fixed']==0 and 1<=v['cuttable']<=MAX_CUTS and isinstance(v['victim_nets'],list)]
    if clear or not usable or row['previously_targeted']:return None
    cuts,victims,layer=min(usable)
    pts=[tuple(row['from_xy']),tuple(row['to_xy'])]
    box=frame(pts,margin=3.0)
    if box[2]-box[0]>MAX_FRAME_MM or box[3]-box[1]>MAX_FRAME_MM:return None
    return {'layer':layer,'cuts':cuts,'victim_nets':layers[layer]['victim_nets'],'cut_uuids':layers[layer]['cut_uuids'],
            'frame_mm':box,'score':[cuts,victims,row['gap_mm']]}


def frame(points,margin=3.0):
    xs=[p[0] for p in points];ys=[p[1] for p in points]
    return [round(min(xs)-margin,3),round(min(ys)-margin,3),round(max(xs)+margin,3),round(max(ys)+margin,3)]


def analyse(board_id,names,tried):
    path=ROOT/'boards'/board_id/f'{board_id}.kicad_pcb';board=g.Board(path)
    if board.sha256!=BOARDS[board_id]['sha256']:raise SystemExit(f'{board_id}: board bytes are not the accepted {BOARDS[board_id]["label"]}')
    isl,pads,segs,vias=g.connectivity(board)
    text_by={n:len(v)-1 for n,v in isl.items() if len(v)>1}
    native=native_counts(board_id)
    nat_by=native['by_net'];keys=set(nat_by)|({n for n in text_by} if board_id!='osc-core' else set(nat_by))
    mismatch={n:{'text':text_by.get(n,0),'native':nat_by.get(n,0)} for n in keys if text_by.get(n,0)!=nat_by.get(n,0)}
    index=Index(board,pads);rows=[]
    for net,groups in sorted(isl.items()):
        if len(groups)<2 or (board_id=='osc-core' and net not in (*RAILS,'AGND')):continue
        main=max(range(len(groups)),key=lambda i:len(groups[i]))
        order=[groups[main]]+[gr for i,gr in enumerate(groups) if i!=main]
        for e in g.open_edges(order,pads,segs,vias):
            a,b=tuple(e['from_xy']),tuple(e['to_xy'])
            row={'net':net,'name':names.get(net,net),'gap_mm':e['gap_mm'],
                 'from':label(e['from'],pads,segs,vias),'to':label(e['to'],pads,segs,vias),
                 'from_xy':e['from_xy'],'to_xy':e['to_xy'],
                 'stranded_island_pads':g.island_pads(order[e['to_island']]),
                 'stranded_island_items':len(order[e['to_island']])}
            if net in PLANES:
                fills=[pts for z in board.zones if z['net']==net and z['keepout'] is None for lay,pts in z['fills'] if lay==PLANES[net]]
                row['plane_layer']=PLANES[net]
                row['stranded_pads_over_plane_fill']=[r for r in row['stranded_island_pads'] if any(g.point_in_poly(pads['pad:'+r]['x'],pads['pad:'+r]['y'],f) for f in fills)]
            layers={}
            for layer in SIGNAL_LAYERS:
                cut,fixed=corridor(index,a,b,net,layer)
                victims=sorted({c['net'] for c in cut})
                layers[layer]={'cuttable':len(cut),'victim_nets':victims if len(victims)<=MAX_VICTIMS else len(victims),'fixed':len(fixed),
                               'fixed_items':fixed[:3],
                               # UUIDs only where an explicit bounded repair could use them.
                               **({'cut_uuids':[c['uuid'] for c in cut]} if len(cut)<=MAX_CUTS else {})}
            row['corridor']=layers
            best=[(v['cuttable'],l) for l,v in layers.items() if v['fixed']==0]
            row['best_layer']=min(best)[1] if best else None
            row['previously_targeted']=sorted(t for t in tried if t in (net,row['from'].get('uuid'),row['to'].get('uuid')))
            row['transaction_candidate']=candidate(row)
            rows.append(row)
    return board,{'board':str(path.relative_to(ROOT)),'board_sha256':board.sha256,'label':BOARDS[board_id]['label'],
                  'native':native,'text_open_edges':sum(text_by.values()),'text_by_net_mismatch':mismatch,
                  'text_matches_native':not mismatch and (board_id=='osc-core' or sum(text_by.values())==native['open_edges']),
                  'ranked_candidates':[{'net':r['net'],'name':r['name'],'from':r['from'],'to':r['to'],'gap_mm':r['gap_mm'],**r['transaction_candidate']}
                                       for r in sorted((r for r in rows if r['transaction_candidate']),key=lambda r:r['transaction_candidate']['score'])][:15],
                  'open_edges':rows,
                  'rows_cover':'rails and AGND only' if board_id=='osc-core' else 'every open edge'}


def tried_tokens():
    """Net tokens and pad UUIDs named as targets by earlier preserved local experiments."""
    import re
    key=re.compile(r'"(?:repair_targets|repair_ground_pad_uuids|targets|endpoints?)"\s*:\s*\[([^\]]*)\]')
    ident=re.compile(r'X[0-9A-F]{20}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
    out=set()
    for p in [*(ROOT/'circuit/routing/issue189').rglob('*plan*.json'),*(ROOT/'circuit/reviews').rglob('*.json')]:
        if 'osc4-local-transactions' in str(p) or p.stat().st_size>5_000_000:continue
        for body in key.findall(p.read_text()):out|=set(ident.findall(body))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0]);p.add_argument('-o','--output',type=Path,required=True)
    p.add_argument('--board',choices=sorted(BOARDS),action='append')
    a=p.parse_args();names=json.loads((ROOT/'design/reports/board-net-tokens.json').read_text());tried=tried_tokens()
    if a.board and a.output.exists():
        # Single-board refresh: keep the other boards' entries exactly as they are.
        out=json.loads(a.output.read_text())
        for bid in a.board:
            _,res=analyse(bid,names,tried);out['boards'][bid]=res
            print(bid,res['label'],'text',res['text_open_edges'],'native',res['native']['open_edges'],'match',res['text_matches_native'],'candidates',len(res['ranked_candidates']),flush=True)
        a.output.write_text(json.dumps(out,indent=1,sort_keys=True)+'\n');return
    out={'schema':'osc4-residuals-1','status':'HOST TEXT ANALYSIS; not a native result; corridor counts are straight-line estimates, not routes',
         'router_limits':{'clearance_mm':CLEARANCE,'signal_width_mm':SIGNAL_WIDTH,'max_cuts':MAX_CUTS,'max_victim_nets':MAX_VICTIMS,'max_frame_mm':MAX_FRAME_MM},
         'previously_targeted_identifiers':len(tried),'boards':{}}
    for bid in a.board or list(BOARDS):
        _,res=analyse(bid,names,tried);out['boards'][bid]=res
        print(bid,res['label'],'text',res['text_open_edges'],'native',res['native']['open_edges'],'match',res['text_matches_native'],'candidates',len(res['ranked_candidates']),flush=True)
    a.output.write_text(json.dumps(out,indent=1,sort_keys=True)+'\n')


if __name__=='__main__':sys.exit(main())
