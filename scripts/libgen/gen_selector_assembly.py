#!/usr/bin/env python3
"""Generate source-bounded selector assets; no exact solid or fit is claimed."""
import argparse
import hashlib
import json
from pathlib import Path
from gen_courtyards import rewrite

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / 'design/mechanical/selector-assembly.json'
FACES = '0,3,2,1,-1,4,5,6,7,-1,0,1,5,4,-1,1,2,6,5,-1,2,3,7,6,-1,3,0,4,7,-1'

def cuboid(bounds, color):
    x0,y0,z0,x1,y1,z1 = bounds
    # KiCad component VRML uses 0.1 inch units (2.54 mm); invert drawing Y.
    points = [(x,-y,z) for z in (z0,z1) for x,y in ((x0,y1),(x1,y1),(x1,y0),(x0,y0))]
    return ('Shape { appearance Appearance { material Material { diffuseColor '+color+' transparency 0.35 } } '
            'geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+
            ', '.join(' '.join(f'{v / 2.54:.9f}' for v in point) for point in points)+
            ' ] } coordIndex [ '+FACES+' ] } }\n')

def outputs():
    a=json.loads(SPEC.read_text()); d=a['drawing']
    lines=['(footprint "SRBV160803"', '  (version 20240108)', '  (generator "selector-assembly-draft")',
           '  (layer "F.Cu")','  (attr through_hole)',
           '  (descr "Drawing No.7; asymmetric body and conservative 18.2 mm support envelope; stepped assembly required")',
           '  (property "Reference" "REF**" (at 0 -12 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
           '  (property "Value" "SRBV160803" (at 0 12 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
    for key in ('main_body_xy_mm','conservative_body_support_xy_mm'):
        x0,y0,x1,y1=d[key]
        lines.append(f'  (fp_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))')
    lines.append('  (fp_circle (center 0 0) (end 4.5 0) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))')
    for row,y in zip(([6,7,8,9,10],[5,4,3,2,1]),d['terminal_rows_y_mm']):
        for i,pin in enumerate(row):
            size=d['terminal_pad_diameter_mm']; drill=d['terminal_hole_diameter_mm']
            lines.append(f'  (pad "{pin}" thru_hole circle (at {-5+2.5*i} {y}) (size {size} {size}) (drill {drill}) (layers "*.Cu" "*.Mask"))')
    for i,(x,y) in enumerate(d['mount_holes_xy_mm'],1):
        size=d['mount_pad_diameter_mm'];drill=d['mount_hole_diameter_mm']
        lines.append(f'  (pad "MP{i}" thru_hole circle (at {x} {y}) (size {size} {size}) (drill {drill}) (layers "*.Cu" "*.Mask"))')
    lines.extend(['  (model "${KIPRJMOD}/../../footprints/kicad/zudo-osc-hole-field.3dshapes/SRBV160803.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))',')'])
    fp=rewrite('\n'.join(lines)+'\n')
    x0,y0,x1,y1=d['conservative_body_support_xy_mm'];z0,z1=d['body_support_z_mm']
    wrl='#VRML V2.0 utf8\n# Conservative KEEP OUT volumes, not actual solids. Includes uncertain support contour and tails.\n'
    wrl+=cuboid((x0,y0,z0,x1,y1,z1),'0.4 0.25 0.15')
    tx0,ty0,tx1,ty1=d['terminal_tail_xy_mm']
    tz0,tz1=d['terminal_tail_z_mm']
    wrl+=cuboid((tx0,ty0,tz0,tx1,ty1,tz1),'0.65 0.45 0.15')
    # Square bounds on bushing and shaft intentionally enclose their true round profiles.
    wrl+=cuboid((-4.5,-4.5,7.5,4.5,4.5,14.5),'0.65 0.65 0.65')
    wrl+=cuboid((-3,-3,14.5,3,3,23),'0.8 0.8 0.8')
    result={'footprints/kicad/zudo-osc-hole-field.pretty/SRBV160803.kicad_mod':fp,
            'footprints/kicad/zudo-osc-hole-field.3dshapes/SRBV160803.wrl':wrl}
    receipt_path='circuit/cad-receipts/topic12-footprint-selector.receipt.json'
    receipt=json.loads((ROOT/receipt_path).read_text())
    for source in ('design/mechanical/sources/alps-srbv-shaft.gif','design/mechanical/sources/alps-srbv-hardware.gif'):
        receipt['acquisition']['sha256'][source]=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
        if source not in receipt['representation']['original_paths']:receipt['representation']['original_paths'].append(source)
    receipt['derivation']['input_sha256']=receipt['acquisition']['sha256'].copy()
    receipt['fidelity']['reason']='Drawing-derived holes and unchanged PTH annular rings. Asymmetric body plus conservative 18.2 mm support/tail keepout; no exact vendor solid. Coplanar candidates rejected; stepped 3+2 assembly is a conditional draft.'
    receipt['derivation']['tool']='scripts/libgen/gen_selector_assembly.py; design/mechanical/selector-assembly.json; gen_courtyards.py'
    receipt['derivation']['tool_version']='2'
    receipt['representation']['units']='Footprint mm; WRL coordinate unit 0.1 inch (2.54 mm)'
    for path,content in result.items():receipt['derivation']['output_sha256'][path]=hashlib.sha256(content.encode()).hexdigest()
    receipt['derivation']['parameters']={'specification_sha256':hashlib.sha256(SPEC.read_bytes()).hexdigest(),'drawing_view':'A; x right / y down; 3D Y inverted','support_envelope_fidelity':'conservative bound; not measured solid','installed_qualification':'NOT RUN','vrml_mm_per_unit':2.54,'vrml_units_reference':'https://dev-docs.kicad.org/en/file-formats/legacy-pcb/index.html'}
    result[receipt_path]=json.dumps(receipt,indent=2)+'\n'
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    for name,content in outputs().items():
        path=ROOT/name
        if args.check:
            if not path.exists() or path.read_text()!=content:raise SystemExit(f'STALE: {name}')
        else:path.write_text(content)
    print('PASS: selector drawing assets current' if args.check else 'Generated selector drawing assets and receipt')
if __name__=='__main__':main()
