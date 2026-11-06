#!/usr/bin/env python3
"""Report the placed geometry of every TMUX6112 SEL hold network on the core PCB.

Read only. For each driven SEL pin it lists the other parts on that net (the
100 kOhm pull-up, the BAT54S clamp and pull-down) with their centre distance to
the switch, the logic driver on the pull-down's other net, and the copper
currently on both nets. Centre distance is not trace length; an unrouted net has
no trace length. Source geometry only: no electrical or timing claim.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,math,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SEL_PINS=('1','16','9','8')
RADIUS_MM=24.0


def footprints(text):
    out={}
    for block in text.split('\n\t(footprint "')[1:]:
        ref=re.search(r'\(property "Reference" "([^"]+)"',block).group(1)
        value=re.search(r'\(property "Value" "([^"]+)"',block)
        at=re.search(r'\n\t\t\(at ([\d.\-]+) ([\d.\-]+)',block)
        layer=re.search(r'\n\t\t\(layer "([^"]+)"\)',block)
        pads=dict(re.findall(r'\(pad "(\w+)"[^\n]*?(?:\n[^\n]*?){0,12}?\(net (?:\d+ )?"([^"]*)"',block))
        out[ref]={'xy':(float(at.group(1)),float(at.group(2))),'side':layer.group(1) if layer else None,
                  'value':value.group(1) if value else '','pads':pads}
    return out


def copper(text,net):
    segments=re.findall(r'\(segment\s+\(start ([\d.\-]+) ([\d.\-]+)\)\s+\(end ([\d.\-]+) ([\d.\-]+)\)\s+\(width [\d.]+\)\s+\(layer "[^"]+"\)\s+(?:\(locked [^)]*\)\s+)?\(net "'+re.escape(net)+r'"\)',text)
    vias=len(re.findall(r'\(via\b(?:(?!\(via\b).){0,600}?\(net "'+re.escape(net)+r'"\)',text,flags=re.S))
    return {'segments':len(segments),'segment_length_mm':round(sum(math.dist((float(a),float(b)),(float(c),float(d))) for a,b,c,d in segments),3),'vias':vias}


def report(board):
    text=board.read_text();fps=footprints(text);names=json.loads((ROOT/'design/reports/board-net-tokens.json').read_text())
    by_net=collections.defaultdict(list)
    for ref,f in fps.items():
        for pad,net in f['pads'].items():by_net[net].append((ref,pad))
    rows=[]
    for ref,f in sorted(fps.items()):
        if not f['value'].startswith('TMUX6112'):continue
        for pin in SEL_PINS:
            net=f['pads'].get(pin)
            if not net or net=='AGND':continue
            members={}
            logic=set()
            for other,pad in by_net[net]:
                if other==ref:continue
                members[other]=round(math.dist(fps[other]['xy'],f['xy']),3)
                if fps[other]['value'].startswith('BAT54S'):
                    pin2=fps[other]['pads'].get('2')
                    if pin2 and pin2!='+12V':logic.add(pin2)
            drivers={}
            for n in sorted(logic):
                for other,pad in by_net[n]:
                    if other!=ref and not fps[other]['value'].startswith('BAT54S'):drivers[f'{other}.{pad}']=round(math.dist(fps[other]['xy'],f['xy']),3)
            rows.append({'switch':ref,'sel_pin':pin,'net':names.get(net,net),'net_token':net,'members_centre_distance_mm':members,
                         'logic_net':[names.get(n,n) for n in sorted(logic)],'logic_driver_centre_distance_mm':drivers,
                         'sel_copper':copper(text,net),'logic_copper':{names.get(n,n):copper(text,n) for n in sorted(logic)}})
    beyond=[r for r in rows if any(d>RADIUS_MM for d in r['members_centre_distance_mm'].values())]
    return {'schema':'osc-sel-hold-geometry-1','status':'SOURCE GEOMETRY ONLY; centre distances, not trace lengths; NOT a timing or noise result',
            'board':str(board.relative_to(ROOT)),'board_sha256':hashlib.sha256(board.read_bytes()).hexdigest(),
            'comparison_radius_mm':RADIUS_MM,'sel_nets':len(rows),'sel_nets_with_a_member_beyond_radius':len(beyond),
            'routed_sel_nets':sum(r['sel_copper']['segments']>0 for r in rows),
            'maximum_member_centre_distance_mm':max((d for r in rows for d in r['members_centre_distance_mm'].values()),default=0),
            'rows':rows}


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--board',type=Path,default=ROOT/'boards/osc-core/osc-core.kicad_pcb');p.add_argument('-o','--output',type=Path,required=True)
    a=p.parse_args();result=report(a.board.resolve())
    a.output.write_text(json.dumps(result,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('board_sha256','sel_nets','sel_nets_with_a_member_beyond_radius','routed_sel_nets','maximum_member_centre_distance_mm')}))


if __name__=='__main__':sys.exit(main())
