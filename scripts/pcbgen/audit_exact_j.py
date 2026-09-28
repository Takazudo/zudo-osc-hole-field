#!/usr/bin/env python3
"""Read-only native identity and source-coordinate audit for the jack draft."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.uuid_tools import stable_uuid

def audit(board_id):
    definition=load_definition(ROOT/'design/boards'/f'{board_id}.json')
    components,_=read_netlist(ROOT/definition.netlist)
    board=pcbnew.LoadBoard(str(ROOT/'boards'/board_id/f'{board_id}.kicad_pcb'))
    footprints={fp.GetReference():fp for fp in board.GetFootprints()}
    fixed=selected_hardware(definition,load_lock(ROOT/'design/grid/placements.lock.json'))
    errors=[]
    expected={c.ref for c in components}|{f"MH_{h['id']}" for h in definition.mounting_holes}
    if set(footprints)!=expected:errors.append(f'reference set mismatch: missing {sorted(expected-set(footprints))[:8]}, extra {sorted(set(footprints)-expected)[:8]}')
    for ref,fp in footprints.items():
        if fp.m_Uuid.AsString()!=stable_uuid(board_id,'footprint:'+ref,'root'):errors.append(ref+': unstable root UUID')
    for component in components:
        fp=footprints.get(component.ref)
        if fp is None:continue
        fields=dict(component.fields);origin=fields.get('FootprintOriginMm','')
        if not origin:errors.append(component.ref+': missing source origin');continue
        x,y=map(float,origin.split(','));position=fp.GetPosition()
        if abs(pcbnew.ToMM(position.x)-100-x)>1e-5 or abs(pcbnew.ToMM(position.y)-50-y)>1e-5:errors.append(component.ref+': origin mismatch')
        if str(fp.GetLayerName())!=fields.get('BoardSide'):errors.append(component.ref+': face mismatch')
        angle=float(fields.get('KiCadOrientationDeg','nan'))
        if abs((fp.GetOrientationDegrees()-angle+180)%360-180)>1e-5:errors.append(component.ref+': angle mismatch')
    for hardware in fixed:
        fp=footprints.get(hardware['ref'])
        if fp is None:continue
        pos=fp.GetPosition()
        if not fp.IsLocked() or abs(pcbnew.ToMM(pos.x)-100-hardware['x_mm'])>1e-5 or abs(pcbnew.ToMM(pos.y)-50-hardware['y_mm'])>1e-5:
            errors.append(hardware['ref']+': fixed UID position/lock mismatch')
    for hole in definition.mounting_holes:
        ref=f"MH_{hole['id']}";fp=footprints.get(ref)
        if fp is None:continue
        pos=fp.GetPosition()
        if not fp.IsLocked() or abs(pcbnew.ToMM(pos.x)-100-hole['center'][0])>1e-5 or abs(pcbnew.ToMM(pos.y)-50-hole['center'][1])>1e-5:
            errors.append(ref+': support mismatch')
    refs=sorted(c.ref for c in components)
    return {'schema_version':1,'board_id':board_id,'status':'PASS' if not errors else 'FAIL',
        'netlisted_source_reference_count':len(refs),'source_reference_sha256':hashlib.sha256('\n'.join(refs).encode()).hexdigest(),
        'native_footprint_count':len(footprints),'fixed_lockfile_feature_count':len(fixed),
        'board_only_support_count':len(definition.mounting_holes),'errors':errors,
        'scope':'Native centre, face, angle, stable root UUID and fixed-lock checks only; physical fit and electrical routing not established.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('board_id');args=parser.parse_args()
    result=audit(args.board_id);path=ROOT/'boards'/args.board_id/'reports/exact-placement.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(result['status'],result['netlisted_source_reference_count'],result['native_footprint_count'],len(result['errors']))
    raise SystemExit(0 if not result['errors'] else 1)
