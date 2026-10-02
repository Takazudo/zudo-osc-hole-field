#!/usr/bin/env python3
"""Fresh pinned native checks of display-envelope units, axes and body centres.

Run through scripts/kicad/run.sh. This checks display geometry, not installed
fit, leads, seating, clearance or physical qualification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import uuid
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/libgen'))
import gen_ic_package_envelopes as ic
from gen_component_envelopes import MODELS as COMPONENT_MODELS
from vrml_geometry import first_coordinate_geometry
import vrml_geometry

LIBRARY=ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'
MODELS=ROOT/'footprints/kicad/zudo-osc-hole-field.3dshapes'
FIXTURE=ROOT/'.circuit-cache/fixtures'
REPORT=ROOT/'design/mechanical/ic-envelope-native-report.json'
EXPECTED={
    'PTV09A-4020F':(10.0,10.0,6.8),
    'Jack_3.5mm_QingPu_WQP518MA':COMPONENT_MODELS['Jack_3.5mm_QingPu_WQP518MA.wrl'][:3],
    'Toggle_Dailywell_2MS_T1B1M2':COMPONENT_MODELS['Toggle_Dailywell_2MS_T1B1M2.wrl'][:3],
    'Button_Omron_B3F_6x6_P6.5x4.5':COMPONENT_MODELS['Button_Omron_B3F_6x6_P6.5x4.5.wrl'][:3],
    **{name:row['dims'] for name,row in ic.MODELS.items()},
    'TI_DCT0008A':(3.1,3.1,1.3),
    'KEMET_C0603_DensityB':(1.75,.95,.95),
}
TOLERANCE_MM=.005


class GeometryMismatch(AssertionError):
    pass


def fab_basis(footprint):
    """Independent native 2D body outline after the footprint's own transform."""
    layer=pcbnew.B_Fab if footprint.GetLayer()==pcbnew.B_Cu else pcbnew.F_Fab
    points=[]
    for item in footprint.GraphicalItems():
        if not isinstance(item,pcbnew.PCB_SHAPE) or item.GetLayer()!=layer:continue
        if item.GetShape()==pcbnew.SHAPE_T_POLY:
            poly=item.GetPolyShape()
            vertices=[]
            for index in range(poly.OutlineCount()):
                chain=poly.COutline(index)
                if chain.ArcCount():raise ValueError('curved Fab polygon is not supported')
                vertices.extend(chain.CPoint(i) for i in range(chain.PointCount()))
        elif item.GetShape() in (pcbnew.SHAPE_T_SEGMENT,pcbnew.SHAPE_T_RECT):
            vertices=(item.GetStart(),item.GetEnd())
        else:raise ValueError('unsupported Fab body primitive')
        for p in vertices:
            points.append((pcbnew.ToMM(p.x),-pcbnew.ToMM(p.y)))
    if len(points)<4:raise ValueError('missing native Fab body outline')
    bounds=[(min(p[i] for p in points),max(p[i] for p in points)) for i in range(2)]
    return {'bounds':bounds,'center':tuple((a+b)/2 for a,b in bounds),
            'size':tuple(b-a for a,b in bounds)}


def exported_geometry(name,position=(0,0),angle=0,bottom=False,offset=None,model_angle=None):
    board=pcbnew.BOARD()
    footprint=pcbnew.FootprintLoad(str(LIBRARY),name)
    if footprint is None:raise RuntimeError('native footprint load failed: '+name)
    board.Add(footprint)
    footprint.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in position)))
    if bottom:footprint.Flip(footprint.GetPosition(),False)
    footprint.SetOrientationDegrees(angle)
    models=footprint.Models()
    if len(models)!=1:raise RuntimeError('expected exactly one display model')
    if offset is not None:
        models[0].m_Offset.x,models[0].m_Offset.y,models[0].m_Offset.z=offset
    if model_angle is not None:models[0].m_Rotation.z=model_angle
    basis=fab_basis(footprint) if name in ic.MODELS or name in ('TI_DCT0008A','KEMET_C0603_DensityB') else None
    # Keep project depth fixed for existing KIPRJMOD/../../ model references;
    # unique filenames prevent stale or concurrent fixture reuse.
    base=FIXTURE/('wrl-placement-'+uuid.uuid4().hex)
    pcb=base.with_suffix('.kicad_pcb');vrml=base.with_suffix('.wrl')
    pcbnew.SaveBoard(str(pcb),board)
    result=subprocess.run(['kicad-cli','pcb','export','vrml','--units','mm',
                           '--user-origin','0x0mm','--force','-o',str(vrml),str(pcb)],
                          text=True,capture_output=True)
    if result.returncode:raise RuntimeError('native VRML export failed: '+result.stderr)
    geometry=first_coordinate_geometry(vrml.read_text())
    if geometry['transform_count']<2:
        raise RuntimeError('no attached model transform; refusing a board/pad mesh')
    return geometry,basis


def check_geometry(name,geometry,basis):
    if any(not math.isclose(a,b,abs_tol=TOLERANCE_MM) for a,b in zip(geometry['mesh_axis_sizes'],EXPECTED[name])):
        raise GeometryMismatch('native model-axis dimensions differ from retained display bounds')
    if basis is not None:
        if any(not math.isclose(a,b,abs_tol=TOLERANCE_MM) for a,b in zip(geometry['center'][:2],basis['center'])):
            raise GeometryMismatch('native model centre differs from transformed Fab body centre')
        # Compare orientation, not containment: manufacturer maxima and generic
        # Fab outlines need not coincide (notably the SOD-123 family outline).
        actual=geometry['size'][0]-geometry['size'][1]
        expected=basis['size'][0]-basis['size'][1]
        if abs(expected)<TOLERANCE_MM:
            if name!='TI_DCT0008A' or any(not math.isclose(a,b,abs_tol=TOLERANCE_MM) for a,b in zip(geometry['size'],EXPECTED[name])):
                raise GeometryMismatch('native square-body bounds differ from retained envelope')
            return
        if actual*expected<=0:
            raise GeometryMismatch('native model long axis differs from transformed Fab body axis')
        short,long=sorted(EXPECTED[name][:2])
        aligned=(long,short,EXPECTED[name][2]) if expected>0 else (short,long,EXPECTED[name][2])
        if any(not math.isclose(a,b,abs_tol=TOLERANCE_MM) for a,b in zip(geometry['size'],aligned)):
            raise GeometryMismatch('native world body bounds differ from the Fab-aligned display envelope')
        if name=='DIP-8_W7.62mm' and any(not math.isclose(a,b,abs_tol=TOLERANCE_MM)
                for a,b in zip(geometry['size'][:2],basis['size'])):
            raise GeometryMismatch('DIP planform differs from its retained Fab source')



def check_capacitor_lands(footprint):
    """Independent KEMET C1002_X7R (2026-09-01), p12 Table3 DensityB."""
    raw_pads = list(footprint.Pads())
    if len(raw_pads) != 2:
        raise GeometryMismatch('KEMET must have exactly two physical pads')
    pads = {pad.GetNumber(): pad for pad in raw_pads}
    if set(pads) != {'1', '2'}:
        raise GeometryMismatch('KEMET terminal set differs')
    for number, x in (('1', -.8), ('2', .8)):
        pad = pads[number]
        angle = pad.GetOrientationDegrees() - footprint.GetOrientationDegrees()
        if not math.isclose(math.remainder(angle, 180), 0, abs_tol=1e-9):
            raise GeometryMismatch('KEMET pad axes differ from source orientation')
        actual = (pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y),
                  pcbnew.ToMM(pad.GetSize().x), pcbnew.ToMM(pad.GetSize().y))
        if actual != (x, 0, .95, 1.0):
            raise GeometryMismatch('KEMET source pad centres or X/Y dimensions differ')
    points = []
    for graphic in footprint.GraphicalItems():
        if graphic.GetLayer() == pcbnew.F_CrtYd:
            points.extend((graphic.GetStart(), graphic.GetEnd()))
    if len(points) != 8:
        raise GeometryMismatch('KEMET courtyard rectangle missing')
    box = (min(pcbnew.ToMM(p.x) for p in points), min(pcbnew.ToMM(p.y) for p in points),
           max(pcbnew.ToMM(p.x) for p in points), max(pcbnew.ToMM(p.y) for p in points))
    if box != (-1.55, -.75, 1.55, .75):
        raise GeometryMismatch('KEMET source courtyard differs')
    return {'pads_mm': {'1': [-.8, 0, .95, 1], '2': [.8, 0, .95, 1]},
            'courtyard_box_mm': box,
            'source': 'C1002_X7R (2026-09-01), physical index11/printed12 Table3 DensityB',
            'qualification_accepted': False}


def source_snapshot():
    paths={Path(__file__).resolve(),Path(ic.__file__).resolve(),Path(vrml_geometry.__file__).resolve(),
           ROOT/'scripts/libgen/gen_component_envelopes.py',ROOT/'scripts/libgen/build_monitor_candidate_assets.py',ROOT/'design/power/monitor-permit-parts.json',ROOT/'scripts/kicad/run.sh',ROOT/'scripts/kicad/pin.env'}
    for name in EXPECTED:paths.add(LIBRARY/(name+'.kicad_mod'))
    # Only attached models, not unrelated mutable cache/export artifacts.
    for name in EXPECTED:
        footprint=pcbnew.FootprintLoad(str(LIBRARY),name)
        for model in footprint.Models():paths.add(MODELS/Path(model.m_Filename).name)
    return {p:p.read_bytes() for p in sorted(paths)}


def rounded(value):
    if isinstance(value,float):return round(value,6)
    if isinstance(value,(tuple,list)):return [rounded(v) for v in value]
    if isinstance(value,dict):return {k:rounded(v) for k,v in value.items()}
    return value


def run(check=False):
    if not re.match(r'^10\.0\.6(?:[-+ ]|$)',pcbnew.GetBuildVersion()):
        raise RuntimeError('pinned KiCad10.0.6 oracle required')
    FIXTURE.mkdir(parents=True,exist_ok=True)
    snapshot=source_snapshot();rows=[]
    capacitor = pcbnew.FootprintLoad(str(LIBRARY), "KEMET_C0603_DensityB")
    capacitor_lands = check_capacitor_lands(capacitor)
    cases=[(name,(0,0),0,False) for name in EXPECTED]
    cases += [('DIP-8_W7.62mm',(12,7),angle,bottom) for angle,bottom in ((0,False),(90,False),(90,True))]
    for name,position,angle,bottom in cases:
        geometry,basis=exported_geometry(name,position,angle,bottom)
        check_geometry(name,geometry,basis)
        rows.append(rounded({'footprint':name,'position_mm':position,'rotation_deg':angle,
                    'side':'B.Cu' if bottom else 'F.Cu','native_model':geometry,'native_Fab':basis,
                    'scope':'body axes/centre and units' if basis is not None else 'legacy model-axis units only'}))
    rejected=[]
    for label,name,kwargs in (
            ('DIP zero offset','DIP-8_W7.62mm',{'offset':(0,0,0)}),
            ('DIP wrong Y sign','DIP-8_W7.62mm',{'offset':(3.81,3.81,0)}),
            ('SOT wrong rotation','SOT-23-5',{'model_angle':90}),
            ('SOT oblique rotation','SOT-23-5',{'model_angle':20}),
            ('DCT oblique rotation','TI_DCT0008A',{'model_angle':20})):
        geometry,basis=exported_geometry(name,**kwargs)
        try:check_geometry(name,geometry,basis)
        except GeometryMismatch as error:rejected.append({'case':label,'rejected':True,'reason':str(error)})
        else:raise AssertionError('negative control was accepted: '+label)
    capacitor.Pads()[0].SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1), pcbnew.FromMM(.95)))
    try: check_capacitor_lands(capacitor)
    except GeometryMismatch as error:
        rejected.append({'case': 'KEMET swapped pad dimensions', 'rejected': True, 'reason': str(error)})
    else: raise AssertionError('negative KEMET pad control accepted')
    duplicate = pcbnew.FootprintLoad(str(LIBRARY), 'KEMET_C0603_DensityB')
    extra = pcbnew.PAD(duplicate)
    extra.SetNumber('1')
    extra.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(-.8), 0))
    extra.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(.95), pcbnew.FromMM(1)))
    duplicate.Add(extra)
    try: check_capacitor_lands(duplicate)
    except GeometryMismatch as error:
        rejected.append({'case': 'KEMET duplicate physical pad', 'rejected': True, 'reason': str(error)})
    else: raise AssertionError('negative KEMET duplicate-pad control accepted')
    rotated = pcbnew.FootprintLoad(str(LIBRARY), 'KEMET_C0603_DensityB')
    pad = list(rotated.Pads())[0]
    original = (pad.GetPosition().x, pad.GetPosition().y, pad.GetSize().x, pad.GetSize().y)
    pad.SetOrientationDegrees(90)
    if original != (pad.GetPosition().x, pad.GetPosition().y, pad.GetSize().x, pad.GetSize().y):
        raise AssertionError('rotation control changed pad centre or stored size')
    try: check_capacitor_lands(rotated)
    except GeometryMismatch as error:
        rejected.append({'case': 'KEMET rotated pad axes', 'rejected': True, 'reason': str(error)})
    else: raise AssertionError('negative KEMET rotated-pad control accepted')
    pad.SetOrientationDegrees(180)
    check_capacitor_lands(rotated)
    capacitor_lands['symmetric_pad_rotation_checked_deg'] = 180
    if any(p.read_bytes()!=data for p,data in snapshot.items()):
        raise RuntimeError('envelope inputs changed during native checks')
    report={'status':'PASS - native display-envelope placement; no physical qualification',
            'qualification_accepted':False,'oracle':pcbnew.GetBuildVersion(),
            'tolerance_mm':TOLERANCE_MM,'cases':rows,'negative_controls':rejected,
            'capacitor_land_check':capacitor_lands,
            'limits':['IC body centres and long axes are compared with independent native Fab outlines; DCT square-body bounds are checked without an orientation claim.',
                      'Other four component models retain their earlier model-axis unit checks only. KEMET capacitor body dimensions come from the exact sheet; lands are separately checked against family Table3.',
                      'No footprint-containment, lead, seating, height qualification, installed clearance or fabrication claim.',
                      'DIP0.1mm is a display plate, not a package-height bound.'],
            'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(data).hexdigest() for p,data in snapshot.items()}}
    text=json.dumps(report,indent=2)+'\n'
    if check:
        if not REPORT.exists() or REPORT.read_text()!=text:raise AssertionError('native envelope report drift')
    else:
        REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(text)
    print(f'PASS: {len(rows)} native display cases and {len(rejected)} rejected placement mutations; physical fit NOT RUN')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    run(parser.parse_args().check)
