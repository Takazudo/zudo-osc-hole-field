#!/usr/bin/env python3
"""Generate JST GH top-entry SMT assets from the retained eGH drawing."""
from __future__ import annotations
import hashlib
import json
import sys
from gen_courtyards import rewrite
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = 'zudo-osc-hole-field'
PDF = ROOT / 'design/connectors/sources/jst-gh.pdf'
PDF_SHA = 'b1dcb317b6b9a4fbbedd2dbf42c64c95306a252d23de8933b85fcf161240b722'
URL = 'https://www.jst-mfg.com/product/pdf/eng/eGH.pdf'
SIZES = (3, 7, 8)
CHECK = False

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if CHECK:
        if not path.exists() or path.read_text() != content:
            raise SystemExit(f'GH asset drift: {path.relative_to(ROOT)}')
    else:
        path.write_text(content)

def dump(path, value):
    write(path, json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rect(x1,y1,x2,y2,layer):
    return f'  (fp_rect (start {x1:g} {y1:g}) (end {x2:g} {y2:g}) (stroke (width 0.05) (type default)) (fill none) (layer "{layer}"))'

def symbol(n, mpn, fp):
    name=f'JST_GH{n}_{"BM"}'
    lines=['(kicad_symbol_lib','  (version 20231120)','  (generator "kicad_symbol_editor")','  (generator_version "8.0")',f'  (symbol "{name}"','    (in_bom yes) (on_board yes)']
    props=[('Reference','J'),('Value',name),('Footprint',f'{LIB}:{fp}'),('Datasheet',URL),('MPN',mpn),('Manufacturer','JST'),('LCSC','')]
    for idx,(k,v) in enumerate(props):
        lines.append(f'    (property "{k}" "{v}" (at 0 {-10.16-idx*2.54:g} 0) (effects (font (size 1.27 1.27))'+(' hide' if idx>1 else '')+'))')
    h=(n+1)*1.27
    lines.append(f'    (symbol "{name}_0_1"')
    lines.append(f'      (rectangle (start -5.08 {h:g}) (end 5.08 {-h:g}) (stroke (width 0.254) (type default)) (fill (type background)))')
    for i in range(1,n+1):
        y=(n+1-2*i)*1.27
        lines.append(f'      (pin passive line (at -7.62 {y:g} 0) (length 2.54) (name "{i}" (effects (font (size 1 1)))) (number "{i}" (effects (font (size 1 1)))))')
    for j in (1,2):
        lines.append(f'      (pin passive line (at 7.62 {2.54-j*2.54:g} 180) (length 2.54) (name "MOUNT" (effects (font (size 1 1)))) (number "MP{j}" (effects (font (size 1 1)))))')
    lines+=['    )','  )',')']
    return '\n'.join(lines)+'\n'

def footprint(n,mpn,b):
    fp=f'JST_GH{n}_BM_TopEntry'
    half=b/2
    lines=[f'(footprint "{fp}"','  (version 20240108)','  (generator "jst-gh-drawing")','  (layer "F.Cu")','  (attr smd)',f'  (descr "{mpn}; JST eGH p2 mounting-surface land drawing; top entry; pin 1 at +x")',f'  (property "Reference" "J" (at 0 -2 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',f'  (property "Value" "{fp}" (at 0 6 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',rect(-half,0.2,half,4.45,'F.Fab'),rect(-half-0.35,-1.1,half+0.35,5.0,'F.CrtYd')]
    for i in range(1,n+1):
        x=(n+1-2*i)*0.625
        lines.append(f'  (pad "{i}" smd rect (at {x:g} 0) (size 0.6 1.7) (layers "F.Cu" "F.Paste" "F.Mask"))')
    for side in (-1,1):
        x=side*(half-0.4)
        lines.append(f'  (pad "MP{1 if side<0 else 2}" smd rect (at {x:g} 3.35) (size 1 2.8) (layers "F.Cu" "F.Paste" "F.Mask"))')
    lines.append(f'  (model "${{KIPRJMOD}}/../../footprints/kicad/{LIB}.3dshapes/{fp}.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    lines.append(')')
    return fp,'\n'.join(lines)+'\n'

def model(b):
    # KiCad WRL coordinates are 2.54 mm per unit. This is a nominal bounding prism, not an exact solid.
    x=b/5.08; ya=-4.45/2.54; yb=-0.2/2.54; z=4.05/2.54
    pts=[(-x,ya,0),(x,ya,0),(x,yb,0),(-x,yb,0),(-x,ya,z),(x,ya,z),(x,yb,z),(-x,yb,z)]
    return '#VRML V2.0 utf8\nShape { appearance Appearance { material Material { diffuseColor 0.94 0.91 0.83 } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ '+', '.join(' '.join(f'{v:.6f}' for v in p) for p in pts)+' ] } coordIndex [ 0,1,2,3,-1,4,7,6,5,-1,0,4,5,1,-1,1,5,6,2,-1,2,6,7,3,-1,3,7,4,0,-1 ] } }\n'

def main():
    global CHECK
    CHECK = sys.argv[1:] == ["--check"]
    assert sha(PDF)==PDF_SHA
    sizes=[]
    for n in SIZES:
        a=(n-1)*1.25; b=a+4.5; housing=a+2.5
        mpn=f'BM{n:02d}B-GHS-TBT(LF)(SN)'; hm=f'GHR-{n:02d}V-S'
        fp,fp_text=footprint(n,mpn,b)
        sp=ROOT/f'symbols/src/JST_GH{n}_BM.kicad_sym'; fpp=ROOT/f'footprints/kicad/{LIB}.pretty/{fp}.kicad_mod'; mp=ROOT/f'footprints/kicad/{LIB}.3dshapes/{fp}.wrl'
        write(sp,symbol(n,mpn,fp));write(fpp,rewrite(fp_text));write(mp,model(b))
        sizes.append({'positions':n,'header_mpn':mpn,'housing_mpn':hm,'contact_mpn':'SSHL-002T-P0.2','orientation':'top entry (BM); mating axis normal to PCB','pitch_mm':1.25,'header_body_width_mm':b,'header_body_depth_mm':4.25,'header_body_height_mm':4.05,'header_courtyard_xy_mm':[-round(b/2+0.35,2),-1.1,round(b/2+0.35,2),5.0],'housing_width_mm':housing,'housing_depth_mm':4.15,'housing_height_mm':5.7,'mated_height_reference_mm':7.3,'signal_pad_size_mm':[0.6,1.7],'signal_pad_centers_mm':[[round((n+1-2*i)*0.625,3),0] for i in range(1,n+1)],'mount_pad_size_mm':[1,2.8],'mount_pad_centers_mm':[[-round(b/2-0.4,3),3.35],[round(b/2-0.4,3),3.35]],'drills_mm':[],'rated_current_A_per_contact':1,'rated_current_condition':'AWG26; -40..105 C operating temperature includes energized temperature rise','rated_voltage_V_ac_dc':50,'initial_contact_resistance_max_mohm':30,'after_test_contact_resistance_max_mohm':50,'insulation_resistance_min_Mohm':100,'withstand_voltage_V_ac_1min':500,'temperature_C':[-40,105],'wire_awg':[30,26],'insulation_outer_diameter_mm':[0.76,1.0],'crimp_tooling':{'machine':'AP-K2N','applicator':'MKS-L-10-3','dies':'APLMK SSHL002-02'},'pin1_view':'PCB mounting-surface; pin 1 at positive local x','mating_face':'top entry, housing approaches normal to PCB','cable_bend_access_mm':None,'assembled_derating_A_per_contact':None,'status':'drawing-derived nominal geometry; installation and derating OPEN'})
        receipt={'receipt_version':1,'identity':{'asset_id':f'gh{n}-drawing-derived','record_id':f'rec-gh{n}-header','manufacturer':'JST','mpn':mpn,'package':fp,'variant_notes':'BM top-entry, exact position count'},'acquisition':{'provider':'manufacturer primary PDF','source_url':URL,'acquired_on':'2026-09-28','sha256':{'design/connectors/sources/jst-gh.pdf':PDF_SHA}},'representation':{'files':[str(p.relative_to(ROOT)) for p in (sp,fpp,mp)],'formats':['kicad_sym','kicad_mod','wrl'],'units':'footprint mm; WRL 2.54 mm per unit','original_paths':['design/connectors/sources/jst-gh.pdf']},'fidelity':{'class':'derived','reason':'Pads from JST reference PC layout; nominal body prism only. No housing/cable solid or installed fit.'},'derivation':{'derived':True,'input_sha256':{'design/connectors/sources/jst-gh.pdf':PDF_SHA},'output_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (sp,fpp,mp)},'tool':'scripts/libgen/gen_gh_connectors.py','tool_version':'1','parameters':{'drawing_pages':[1,2,5],'mating_axis':'normal to PCB','model_scope':'nominal header body bounding prism'}}}
        dump(ROOT/f'circuit/cad-receipts/gh{n}-drawing-derived.receipt.json',receipt)
    # External mating components use explicit NOT_FOR_PCB mapping aids so the pin-asset
    # contract can verify cavity/contact numbering. These are not placement footprints.
    for n in (3, 7, 8, 1):
        key = f'gh{n}-housing' if n != 1 else 'gh-contact'
        mpn = f'GHR-{n:02d}V-S' if n != 1 else 'SSHL-002T-P0.2'
        name = f'JST_GH{n}_EXTERNAL_NOT_FOR_PCB'
        sp=ROOT/f'symbols/src/{name}.kicad_sym'
        fpp=ROOT/f'footprints/kicad/{LIB}.pretty/{name}.kicad_mod'
        lines=['(kicad_symbol_lib','  (version 20231120)','  (generator "kicad_symbol_editor")','  (generator_version "8.0")',f'  (symbol "{name}"','    (in_bom yes) (on_board no)']
        for idx,(k,v) in enumerate([('Reference','H'),('Value',name),('Footprint',f'{LIB}:{name}'),('Datasheet',URL),('MPN',mpn),('Manufacturer','JST'),('LCSC','')]):
            lines.append(f'    (property "{k}" "{v}" (at 0 {-10.16-idx*2.54:g} 0) (effects (font (size 1.27 1.27))'+(' hide' if idx>1 else '')+'))')
        lines.append(f'    (symbol "{name}_0_1"')
        lines.append(f'      (rectangle (start -5.08 {(n+1)*1.27:g}) (end 5.08 {-(n+1)*1.27:g}) (stroke (width 0.254) (type default)) (fill (type background)))')
        for i in range(1,n+1):
            y=(n+1-2*i)*1.27
            lines.append(f'      (pin passive line (at -7.62 {y:g} 0) (length 2.54) (name "{i}" (effects (font (size 1 1)))) (number "{i}" (effects (font (size 1 1)))))')
        lines += ['    )','  )',')']
        write(sp,'\n'.join(lines)+'\n')
        flines=[f'(footprint "{name}"','  (version 20240108)','  (generator "jst-gh-drawing")','  (layer "F.Cu")','  (attr smd board_only exclude_from_pos_files exclude_from_bom)',f'  (descr "EXTERNAL NOT FOR PCB: {mpn}; cavity/contact numbering aid only")',rect(-n*0.7,-1.0,n*0.7,1.0,'F.Fab')]
        for i in range(1,n+1):
            x=(n+1-2*i)*0.625
            flines.append(f'  (pad "{i}" smd rect (at {x:g} 0) (size 0.5 0.5) (layers "F.Cu" "F.Mask"))')
        flines.append(')')
        write(fpp,rewrite('\n'.join(flines)+'\n'))
        receipt={'receipt_version':1,'identity':{'asset_id':key+'-mapping','record_id':'rec-'+key,'manufacturer':'JST','mpn':mpn,'package':name,'variant_notes':'External mapping aid; not a board footprint'},'acquisition':{'provider':'manufacturer primary PDF','source_url':URL,'acquired_on':'2026-09-28','sha256':{'design/connectors/sources/jst-gh.pdf':PDF_SHA}},'representation':{'files':[str(p.relative_to(ROOT)) for p in (sp,fpp)],'formats':['kicad_sym','kicad_mod'],'units':'mm','original_paths':['design/connectors/sources/jst-gh.pdf']},'fidelity':{'class':'derived','reason':'Cavity mapping aid only, not physical PCB geometry; do not place on any board.'},'derivation':{'derived':True,'input_sha256':{'design/connectors/sources/jst-gh.pdf':PDF_SHA},'output_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (sp,fpp)},'tool':'scripts/libgen/gen_gh_connectors.py','tool_version':'1','parameters':{'scope':'EXTERNAL NOT FOR PCB'}}}
        dump(ROOT/f'circuit/cad-receipts/{key}-mapping.receipt.json',receipt)
    out={'schema_version':1,'source':{'path':'design/connectors/sources/jst-gh.pdf','sha256':PDF_SHA,'url':URL,'physical_pdf_page_indexes':[0,1,2,5],'printed_page_labels':['1','2','3','6'],'revision':'not printed'},'sizes':sizes,'selector_gh7_check':{'selector_source':'design/mechanical/selector-assembly.json','mount_pad_center_x_mm':8,'mount_pad_copper_radius_mm':1.3,'mount_pad_inner_copper_edge_x_mm':6.7,'gh7_courtyard_outer_x_mm':6.35,'gh7_nominal_gap_mm':0.35,'gh8_courtyard_outer_x_mm':6.97,'gh8_overlap_mm':0.27,'gh8_unrounded_overlap_mm':0.275,'conditions':'connector centered on adapter x=0; comparison applies only where y envelopes overlap; actual placement and board routing owned by #35','status':'nominal x-axis geometry PASS; physical/tolerance fit NOT RUN'},'open':{'assembled_contact_derating':'OPEN: no primary simultaneous-contact derating curve or built loom test','retention':'OPEN: no quantitative insertion/withdrawal force or cable strain result in eGH','cable_bend':'OPEN: no bend radius/clearance supplied; #35 owns cable route and support','mated_stack':'7.3 mm is reference, no tolerance or installed measurement'}}
    dump(ROOT/'design/connectors/jst-gh.json',out)
if __name__=='__main__':main()
