"""Prepared native fixture checker. Run only in separately admitted pinned KiCad10.0.6."""
import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess

import generate as g


def nm(value):return int(Decimal(value)*1000000)


# Independent literal EDC sheet5 A/F/G table in integer nanometers. Do not
# derive this oracle from the generator's pads or fixture manifest geometry.
EXPECTED_AFG_NM={8:(3500000,5500000,9100000),14:(6500000,8500000,12100000),
                 26:(12500000,14500000,18100000),40:(19500000,21500000,25100000)}


def expected_rows(count,face,angle,origin=(100000000,100000000)):
    if count not in EXPECTED_AFG_NM or face not in ('F','B') or angle not in (0,90,180,270):
        raise ValueError('selected-count cardinal F/B transform required')
    A,F,G=EXPECTED_AFG_NM[count]
    local=[(str(i+1),-A//2+500000*i,0,300000,1300000) for i in range(count)]
    local.extend([('',-(F+G)//4,3250000,1800000,2200000),
                  ('',(F+G)//4,3250000,1800000,2200000)])
    rows=[]
    for number,x,y,w,h in local:
        if face=='B':y=-y  # canonical flipped local frame, then SetOrientationDegrees
        x,y={0:(x,y),90:(y,-x),180:(-x,-y),270:(-y,x)}[angle]
        rows.append((number,x+origin[0],y+origin[1],w,h,angle%180))
    return Counter(rows)


def check_footprint(pcbnew,fp,count,face,angle):
    pads=list(fp.Pads());wanted=pcbnew.F_Cu if face=='F' else pcbnew.B_Cu
    forbidden=pcbnew.B_Cu if face=='F' else pcbnew.F_Cu
    if fp.GetLayer()!=wanted or round(fp.GetOrientationDegrees()%360,6)!=angle:
        raise ValueError('native footprint face/orientation mismatch')
    rows=[]
    for pad in pads:
        at=pad.GetPosition();size=pad.GetSize()
        if pad.GetNetCode()!=0 or pad.GetNetname() or set(pad.GetLayerSet().Seq())!={wanted}:
            raise ValueError('unexpected pad net/copper layer')
        if pad.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD or pad.GetShape()!=pcbnew.PAD_SHAPE_RECT:
            raise ValueError('unexpected pad attribute/shape')
        rows.append((pad.GetNumber(),at.x,at.y,size.x,size.y,round(pad.GetOrientationDegrees()%180,6)))
    if Counter(rows)!=expected_rows(count,face,angle):raise ValueError('native pad numbering/position/size mismatch')
    if fp.GetDescription()!=g.DESCRIPTION:raise ValueError('incomplete/no-adoption description missing or changed')
    if list(fp.GraphicalItems()):raise ValueError('unexpected body/courtyard graphics')
    if len(fp.Models()):raise ValueError('unexpected 3D model')
    return {'contacts':count,'face':face,'angle':angle,'numbered_pads':count,'unnumbered_mounting_pads':2}


def run(target):
    target=Path(target);receipt=g.verify_fixture(target)
    work=target/'native-results';work.mkdir(exist_ok=False)  # fail before importing native API
    result_path=work/'result.json'
    with result_path.open('x') as stream:
        try:
            import pcbnew  # NEVER imported by generator or synthetic fixtures
            version=pcbnew.GetBuildVersion();cli=subprocess.check_output(['kicad-cli','version'],text=True).strip()
            if not re.match(r'^10\.0\.6(?:$|[^0-9])',version) or not re.match(r'^10\.0\.6(?:$|[^0-9])',cli):
                raise ValueError('both CLI and pcbnew must be10.0.6 in the pinned image')
            results=[]
            for record in receipt['footprints']:
                for face in ('F','B'):
                    for angle in (0,90,180,270):
                        board=pcbnew.BOARD();fp=pcbnew.FootprintLoad(str(target/receipt['library']),record['name'])
                        if fp is None:raise ValueError('FootprintLoad failed')
                        board.Add(fp);fp.SetReference('FIXTURE');fp.SetPosition(pcbnew.VECTOR2I(100000000,100000000))
                        if face=='B':fp.Flip(fp.GetPosition(),False)
                        fp.SetOrientationDegrees(angle)
                        pre=check_footprint(pcbnew,fp,record['contacts'],face,angle)
                        path=work/f'{record["contacts"]}-{face}-{angle}.kicad_pcb'
                        if path.exists():raise ValueError('native fixture output exists')
                        pcbnew.SaveBoard(str(path),board)
                        reloaded=pcbnew.LoadBoard(str(path));fps=list(reloaded.GetFootprints())
                        if len(fps)!=1:raise ValueError('roundtrip footprint count changed')
                        if check_footprint(pcbnew,fps[0],record['contacts'],face,angle)!=pre:raise ValueError('roundtrip changed fixture')
                        results.append(pre)
            g.verify_fixture(target)
            result={'status':'NATIVE_LAND_FIXTURE_ONLY','pcbnew_version':version,'cli_version':cli,'cases':results,
                    'scope':g.LABEL,'actual_project_registration':None,'endpoint_bindings':[],
                    'not_run':['DRC','zone fill','body/courtyard/3D validation','project placement binding','hardware acceptance']}
        except Exception as exc:
            json.dump({'status':'NATIVE_FIXTURE_FAILED','error':str(exc)},stream,indent=2);stream.write('\n');raise
        json.dump(result,stream,indent=2);stream.write('\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture-dir',type=Path,required=True);args=p.parse_args()
    print(json.dumps(run(args.fixture_dir),indent=2))
