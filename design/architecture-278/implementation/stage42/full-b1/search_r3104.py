"""Bounded native-shape proposal search; never saves or accepts a board."""
from pathlib import Path
import argparse
import json
import math
import sys
import pcbnew
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'stage41/native-pilot'))
from native_guard import check_native
from identity_guard import digest


def search(path,output):
    raw=path.read_text();b=pcbnew.LoadBoard(str(path));check_native(b,raw)
    fps=list(b.GetFootprints());f=next(x for x in fps if x.GetReference()=='R3104')
    face=f.GetLayer();court=pcbnew.B_CrtYd if face==pcbnew.B_Cu else pcbnew.F_CrtYd
    f.BuildCourtyardCaches()
    if not f.GetCourtyard(court).OutlineCount():
        raise ValueError('missing target courtyard')
    foreign=[x for x in fps if x.GetReference()!='R3104']
    courts=[]
    for x in foreign:
        x.BuildCourtyardCaches();shape=x.GetCourtyard(court)
        if shape.OutlineCount():courts.append((x.GetReference(),shape))
    copper=[p for x in foreign for p in x.Pads() if p.IsOnLayer(face)]+[t for t in b.GetTracks() if t.IsOnLayer(face)]
    keepouts=[z for z in b.Zones() if z.GetIsRuleArea() and z.IsOnLayer(face) and z.GetDoNotAllowPads()]
    origin=(117.5,190.5);results=[];failures={};clear=pcbnew.FromMM(.25)
    # 10x10mm bounded neighborhood, unchanged native rotation and face.
    for ix in range(-20,21):
        for iy in range(-20,21):
            xy=(origin[0]+ix*.25,origin[1]+iy*.25)
            f.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in xy)))
            f.BuildCourtyardCaches();shape=f.GetCourtyard(court)
            reason=None
            for ref,other in courts:
                if shape.Collide(other,clear):reason='courtyard';break
            if reason is None:
                for p in f.Pads():
                    ps=p.GetEffectiveShape(face)
                    if any(x.GetNetname()!=p.GetNetname() and ps.Collide(x.GetEffectiveShape(face),clear) for x in copper):reason='copper';break
                    if any(ps.Collide(z.Outline(),0) for z in keepouts):reason='keepout';break
            if reason:failures[reason]=failures.get(reason,0)+1
            else:results.append({'native_xy_mm':xy,'native_angle':f.GetOrientationDegrees(),'distance_from_stage40_mm':math.dist(xy,origin)})
    check_native(b,raw)
    results.sort(key=lambda r:(r['distance_from_stage40_mm'],r['native_xy_mm']))
    result={'board_sha256':digest(raw),'version':pcbnew.GetBuildVersion(),'grid_mm':.25,'trials':1681,
            'origin_native_mm':origin,'half_width_mm':5,'clearance_mm':.25,'failures':failures,'feasible':results,
            'status':'Native-shape necessary screen only; full DRC/routing/physical acceptance NOT established'}
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'feasible':len(results),'best':results[:5],'failures':failures}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('board',type=Path);p.add_argument('output',type=Path);a=p.parse_args();search(a.board,a.output)
