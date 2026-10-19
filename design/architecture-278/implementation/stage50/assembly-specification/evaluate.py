"""Conditional envelope analysis; no claim of populated identity or shop acceptance."""
import hashlib
import json
import math
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PREV = HERE.parent.parent / 'stage49/led-tail-cleanup'

def gap(center, bounds, radius):
    if len(bounds) != 4 or not all(math.isfinite(x) for x in (*center, *bounds, radius)):
        raise ValueError('finite geometry required')
    x0,y0,x1,y1 = bounds
    if x0>x1 or y0>y1 or radius<0:
        raise ValueError('invalid envelope')
    return math.hypot(max(x0-center[0],0,center[0]-x1),
                      max(y0-center[1],0,center[1]-y1))-radius

def evaluate():
    source=json.loads((HERE/'sources.json').read_text())['candidate']
    old=json.loads((PREV/'assembly.json').read_text())
    if source['status']!='PROPOSED_NOT_ASSIGNED' or source['supplier_code'] is not None:
        raise ValueError('unreviewed identity adoption')
    if old['via_center_mm'] != [271.32,132.8] or old['via_diameter_mm'] != .6:
        raise ValueError('Stage49 geometry changed')
    # Actual placement is 90 degrees: width is along board X; length along Y.
    cx,cy=270.31,133.94
    length=max(source['length_mm']);width=max(source['width_mm'])
    bounds=[cx-width/2,cy-length/2,cx+width/2,cy+length/2]
    via=old['via_center_mm']; radius=old['via_diameter_mm']/2
    body=gap(via,bounds,radius)
    arbitrary_angle=math.dist(via,[cx,cy])-math.hypot(length/2,width/2)-radius
    pad=old['nearest_five_pads'][0]['copper_gap_mm']
    # These are geometric budgets, not sourced process tolerances.
    return {'status':'CONDITIONAL_SOURCE_SCREEN_ONLY','populated_identity':'UNRESOLVED',
        'assembly_acceptance':'UNRESOLVED','candidate_mpn':source['mpn'],
        'max_body_bounds_mm':[round(x,9) for x in bounds],
        'body_annulus_gap_mm':round(body,9),
        'body_drill_gap_mm':round(gap(via,bounds,old['drill_mm']/2),9),
        'all_rotation_combined_radial_error_budget_mm':round(arbitrary_angle,9),
        'pad_copper_and_nominal_mask_gap_mm':pad,
        'mask_screen_margin_above_0_09_mm':round(pad-.09,9),
        'ink_plug_screen_margin_above_0_35_mm':round(pad-.35,9),
        'tent_hole_nominal_mm':old['drill_mm'],
        'limitations':['No actual part or order code assigned','No placement/fillet/copper size tolerance asserted',
            'Nominal source apertures only; no generated manufacturing output',
            'Tenting is not ink plugging; no shop acceptance inferred',
            'Hole diameter tolerance not supplied for vias; PTH tolerance not borrowed']}

def verify_bindings():
    data=json.loads((HERE/'review-bindings.json').read_text())
    for name,expected in data.items():
        p=ROOT/name
        if not p.is_file() or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            raise ValueError('binding changed: '+name)

if __name__=='__main__':
    result=evaluate()
    if '--write' in sys.argv:
        (HERE/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    else:
        verify_bindings()
        if result!=json.loads((HERE/'result.json').read_text()):
            raise ValueError('result drift')
    print(json.dumps(result,sort_keys=True))
