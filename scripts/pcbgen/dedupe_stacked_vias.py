"""Remove redundant same-net through vias stacked inside another via's pad.

Earlier grid stages left clusters of same-net vias at raster pitch (0.075 mm), which
are hole_to_hole warnings. KiCad 10.0.6 reports at most 199 warnings per type, so a
board above that cap shows a different sample after any change and the promotion
gate reads pre-existing pairs as new. A via is removed only when a kept via of the
same net, size and layers lies within `radius_mm` of it, so every track end and
zone contact at the removed centre stays inside the kept via's copper. Native refill,
DRC and ratsnest checks still decide whether the result is adopted.
"""
from __future__ import annotations
import argparse,collections,json,math,re
from pathlib import Path
from scripts.pcbgen.uuid_tools import top_level_spans


def vias(text):
    out=[]
    for a,b in top_level_spans(text):
        block=text[a:b]
        if not block.startswith('(via'):continue
        x,y=map(float,re.search(r'\(at ([-\d.]+) ([-\d.]+)\)',block).groups())
        out.append({'span':(a,b),'uuid':re.search(r'\(uuid "([0-9a-f-]+)"\)',block)[1],'net':re.search(r'\(net "([^"]*)"\)',block)[1],
                    'xy':(x,y),'size':float(re.search(r'\(size ([\d.]+)\)',block)[1]),'drill':float(re.search(r'\(drill ([\d.]+)\)',block)[1]),
                    'layers':re.search(r'\(layers ([^)]*)\)',block)[1],'locked':'(locked' in block})
    return out


def plan(items,radius_mm=0.25):
    """Greedy keep set: vias with the most stacked neighbours first; returns {removed uuid: kept uuid}."""
    by=collections.defaultdict(list)
    for v in items:by[(v['net'],v['size'],v['drill'],v['layers'])].append(v)
    removed={}
    for group in by.values():
        near=lambda v:sum(math.dist(v['xy'],w['xy'])<=radius_mm for w in group)
        kept=[]
        for v in sorted(group,key=lambda v:(-near(v),v['xy'],v['uuid'])):
            host=next((k for k in kept if math.dist(v['xy'],k['xy'])<=radius_mm),None)
            if host and not v['locked'] and radius_mm<v['size']/2:removed[v['uuid']]=host['uuid']
            else:kept.append(v)
    return removed


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('board',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--radius-mm',type=float,default=0.25)
    a=p.parse_args();text=a.board.read_text();items=vias(text);removed=plan(items,a.radius_mm)
    spans=sorted((v['span'] for v in items if v['uuid'] in removed),reverse=True)
    for s,e in spans:
        e2=e+1 if text[e:e+1]=='\n' else e
        s2=s-1 if text[s-1:s]=='\t' else s
        text=text[:s2]+text[e2:]
    a.output.write_text(text)
    nets=collections.Counter(v['net'] for v in items if v['uuid'] in removed)
    a.report.write_text(json.dumps({'radius_mm':a.radius_mm,'vias_before':len(items),'removed':len(removed),'by_net':dict(nets.most_common()),
                                    'removed_to_host':dict(sorted(removed.items()))},indent=1)+'\n')
    print(json.dumps({'vias_before':len(items),'removed':len(removed),'nets':len(nets)}))


if __name__=='__main__':main()
