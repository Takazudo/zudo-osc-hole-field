#!/usr/bin/env python3
"""Derive the exact white LED land revision from retained original owner bytes."""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SPEC=ROOT/'design/mechanical/kingbright-white-land.json'
FOOTPRINT='footprints/kicad/zudo-osc-hole-field.pretty/LED0402-Kingbright-White.kicad_mod'
RECEIPT='circuit/cad-receipts/cad-kingbright-white-0402.receipt.json'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def derive(original,spec):
    if sha(original)!=spec['original_footprint_sha256']:
        raise ValueError('original white footprint differs from retained source')
    p={k:F(str(v)) for k,v in spec['project_mm'].items()}
    n={k:F(str(v)) for k,v in spec['primary_nominal_mm'].items()}
    for key in ('width','height','gap'):
        if abs(p[key]-n[key])>n['drawing_tolerance']:
            raise ValueError('project land exceeds published drawing range')
    if p['gap']<p['required_design_clearance'] or 2*p['centre_x_magnitude']-p['width']!=p['gap'] or p['centre_x_magnitude']+p['width']/2!=p['unchanged_outer_x_magnitude']:
        raise ValueError('land clearance, symmetry or unchanged outer extent failed')
    if p['height']!=F('0.5') or p['unchanged_outer_x_magnitude']!=F('0.8') or p['required_design_clearance']!=F('0.25'):
        raise ValueError('unrelated white geometry or target changed')
    result=original.decode()
    for pin,sign in (('1','-'),('2','')):
        old=f'(pad "{pin}" smd rect (at {sign}0.45 0) (size 0.7 0.5)'
        new=f'(pad "{pin}" smd rect (at {sign}{float(p["centre_x_magnitude"]):g} 0) (size {float(p["width"]):g} 0.5)'
        if result.count(old)!=1:raise ValueError('exact original white pad missing')
        result=result.replace(old,new)
    return result.encode()


def outputs():
    raw=SPEC.read_bytes();spec=json.loads(raw)
    inputs={str(SPEC.relative_to(ROOT)):sha(raw)}
    for key in ('original_footprint','original_receipt','primary_pdf'):
        path=ROOT/spec[key];value=path.read_bytes()
        if sha(value)!=spec[key+'_sha256']:raise ValueError('retained land evidence changed: '+key)
        inputs[spec[key]]=sha(value)
    footprint=derive((ROOT/spec['original_footprint']).read_bytes(),spec)
    receipt=json.loads((ROOT/spec['original_receipt']).read_bytes())
    receipt['acquisition']['sha256']=inputs
    receipt['representation']['original_paths']=list(inputs)
    receipt['derivation']['input_sha256']=dict(inputs)
    receipt['derivation']['tool']='scripts/libgen/gen_kingbright_land.py'
    receipt['derivation']['tool_version']='2'
    receipt['derivation']['parameters']={'pads':'Project 0.65 x 0.5 mm at x +/-0.475; gap 0.30 mm; 1=K 2=A','primary_nominal':'0.7 x 0.5 mm, gap 0.2 mm; drawing tolerance +/-0.1 mm','source_owned_delta':spec['preservation'],'qualification':spec['qualification']}
    receipt['derivation']['output_sha256'][FOOTPRINT]=sha(footprint)
    receipt['fidelity']['reason']='Drawing-derived project land selection within the published recommended ranges. Exact original owner bytes retained; only two inner pad edges trimmed. Not assembly or manufacturing qualification.'
    receipt['checks']['remaining_physical_checks'].append(spec['qualification'])
    return {ROOT/FOOTPRINT:footprint,ROOT/RECEIPT:(json.dumps(receipt,indent=2)+'\n').encode()}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for path,value in outputs().items():
        if args.check:
            if path.read_bytes()!=value:raise ValueError('generated white land drift: '+str(path))
        else:path.write_bytes(value)
    print('PASS: exact source-derived white land; original owner style retained; no physical qualification')


if __name__=='__main__':main()
