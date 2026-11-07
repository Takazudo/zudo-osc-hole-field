#!/usr/bin/env python3
"""OSC4: choose at most one bounded local transaction per accepted board from residuals.json.

Host-only and deterministic. Eligible edges come from extract_residuals.py
(ranked_candidates: 1-12 explicit signal cuts on one layer, at most two victim
nets, a frame of at most 50 mm, no earlier native target). The driver's explicit
repair mode can target a signal net or AGND (ground corridor), never a rail, so
rail edges are reported but not selected. Among eligible edges an edge whose cut
layer is a copper layer of both endpoint pads (no via needed) is preferred; then
fewest cuts, fewest victims, shortest gap. The frame encloses both endpoints and
every cut object with a 3 mm margin. Nothing here routes or edits a board.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'scripts/checks'))
import board_text_geometry as g

RAILS=('+12V','-12V','+5V');MAX_FRAME_MM=50.0;MARGIN_MM=3.0
SIGNAL_LAYERS=['F.Cu','In2.Cu','In3.Cu','B.Cu']
# Same router arguments as the repair-NN stages in scripts/pcbgen/route_jack_grid.py STAGES.
REPAIR_ARGS={'repair':True,'agnd_guard':True,'clearance':.2,'signal_width':.2,'signal_via_diameter':.6,
             'grow':{n:.05 for n in [*RAILS,'AGND']},'res':.05,'window_mm':8,'repair_layers':SIGNAL_LAYERS}


def same_layer(c):
    lf=c['from'].get('layers') or ([c['from']['layer']] if 'layer' in c['from'] else None)
    lt=c['to'].get('layers') or ([c['to']['layer']] if 'layer' in c['to'] else None)
    return bool(lf and lt and c['layer'] in lf and c['layer'] in lt)


def objects(board):
    out={}
    for s in board.segments:out.setdefault(s['uuid'],[]).append(('track',s))
    for v in board.vias:out.setdefault(v['uuid'],[]).append(('via',v))
    return out


def extent(kind,o):
    if kind=='track':h=o['w']/2;xs=[o['a'][0],o['b'][0]];ys=[o['a'][1],o['b'][1]]
    else:h=o['size']/2;xs=[o['xy'][0]];ys=[o['xy'][1]]
    return min(xs)-h,min(ys)-h,max(xs)+h,max(ys)+h


def choose(board_id,res,board):
    rows=[c for c in res['ranked_candidates'] if c['net'] not in RAILS]
    rails=[c for c in res['ranked_candidates'] if c['net'] in RAILS]
    if not rows:return None,rails
    best=sorted(rows,key=lambda c:(not same_layer(c),c['score']))[0]
    objs=objects(board);cuts=[]
    for u in best['cut_uuids']:
        if len(objs.get(u,[]))!=1:raise SystemExit(f'{board_id}: cut {u} is not one unique copper object')
        kind,o=objs[u][0];cuts.append({'uuid':u,'kind':kind,'net':o['net'],**({'layer':o['layer'],'a':list(o['a']),'b':list(o['b']),'width':o['w']}
                                                                                if kind=='track' else {'xy':list(o['xy']),'diameter':o['size']})})
    boxes=[extent(c['kind'],{'a':c.get('a'),'b':c.get('b'),'w':c.get('width'),'xy':c.get('xy'),'size':c.get('diameter')}) for c in cuts]
    xs=[b[0] for b in boxes]+[b[2] for b in boxes];ys=[b[1] for b in boxes]+[b[3] for b in boxes]
    edge=next(r for r in res['open_edges'] if r['net']==best['net'] and r['from']==best['from'] and r['to']==best['to'])
    for p in (edge['from_xy'],edge['to_xy']):xs.append(p[0]);ys.append(p[1])
    frame=[round(min(xs)-MARGIN_MM,3),round(min(ys)-MARGIN_MM,3),round(max(xs)+MARGIN_MM,3),round(max(ys)+MARGIN_MM,3)]
    if frame[2]-frame[0]>MAX_FRAME_MM or frame[3]-frame[1]>MAX_FRAME_MM:raise SystemExit(f'{board_id}: frame exceeds {MAX_FRAME_MM} mm')
    short={'osc-core':'k','osc-jack-left':'jl','osc-jack-right':'jr'}[board_id]
    stranded=edge['to']
    if best['net']=='AGND':
        if stranded['kind']!='pad':raise SystemExit(f'{board_id}: stranded AGND endpoint is not a pad')
        spec={'name':f'osc4-{short}-agnd-{stranded["ref"].replace(".","-").lower()}',**REPAIR_ARGS,'repair_targets':['AGND'],
              'repair_ground_pad_uuids':[stranded['uuid']],'repair_source_uuids':[c['uuid'] for c in cuts],'repair_bounds_mm':frame}
        mode='AGND ground corridor (route_jack_grid.py repair_selection(), repair_ground_pad_uuids)'
    else:
        spec={'name':f'osc4-{short}-{best["net"][:9].lower()}',**REPAIR_ARGS,'repair_targets':[best['net']],
              'repair_source_uuids':[c['uuid'] for c in cuts],'repair_bounds_mm':frame}
        mode='explicit signal repair (route_jack_grid.py repair_selection(), repair_source_uuids + repair_bounds_mm)'
    return {'edge':{k:edge[k] for k in ('net','name','gap_mm','from','to','from_xy','to_xy','stranded_island_pads','stranded_island_items')},
            'mode':mode,'cut_layer':best['layer'],'cut_layer_is_shared_by_both_endpoints':same_layer(best),
            'cuts':cuts,'victim_nets':best['victim_nets'],'frame_mm':frame,
            'frame_size_mm':[round(frame[2]-frame[0],3),round(frame[3]-frame[1],3)],'spec':spec},rails


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0]);p.add_argument('--residuals',type=Path,default=HERE/'residuals.json')
    p.add_argument('-o','--output',type=Path,default=HERE/'transactions.json')
    p.add_argument('--board',action='append',choices=('osc-core','osc-jack-left','osc-jack-right'),
                   help='replan only this board and keep the other entries unchanged')
    a=p.parse_args()
    previous=json.loads(a.output.read_text()) if a.board and a.output.exists() else None
    res=json.loads(a.residuals.read_text());out={'schema':'osc4-transactions-1',
        'status':'PLAN ONLY; NOT RUN; every transaction needs one admitted native run and is never promoted by its driver',
        'residuals_sha256':hashlib.sha256(a.residuals.read_bytes()).hexdigest(),
        'limits':{'max_explicit_cuts':12,'max_victim_nets':2,'max_frame_mm':MAX_FRAME_MM,'search':'route() bounds_mm=frame, max_expansions=300000 (route_jack_grid.py stage())',
                  'wall_minutes':60,'refill':'route_jack_grid.check(): three equal island signatures, at most six refills',
                  'retries':'route_jack_grid.stage(): at most eight drop-and-retry passes','rip_up':'only the listed cuts; no rrr probe, no negotiation, no region pass'},
        'transactions':{}}
    for bid,r in res['boards'].items():
        if previous is not None and bid not in a.board:
            out['transactions'][bid]=previous['transactions'][bid];continue
        board=g.Board(ROOT/r['board'])
        if board.sha256!=r['board_sha256']:raise SystemExit(f'{bid}: board changed since residuals.json')
        t,rails=choose(bid,r,board)
        out['transactions'][bid]={'input_board':r['board'],'input_board_sha256':r['board_sha256'],'label':r['label'],
                                  'transaction':t,'rail_edges_not_selectable':[{k:c[k] for k in ('net','gap_mm','layer','cuts','victim_nets')} for c in rails]}
        print(bid,None if t is None else (t['edge']['net'],t['edge']['from'].get('ref'),t['edge']['to'].get('ref'),t['cut_layer'],len(t['cuts']),t['frame_size_mm']),flush=True)
    a.output.write_text(json.dumps(out,indent=1,sort_keys=True)+'\n')


if __name__=='__main__':sys.exit(main())
