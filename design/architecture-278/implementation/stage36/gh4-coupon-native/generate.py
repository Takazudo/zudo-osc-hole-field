"""Generate only the isolated, unpowered GH4 review coupon with the pinned oracle."""
from pathlib import Path
import hashlib, json, uuid, sys
import pcbnew as p

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
sys.path.insert(0,str(ROOT))
from scripts.schgen.core import q
design_bytes=(OUT.parent/'gh4-coupon-plan/design.json').read_bytes()
# Geometry below intentionally implements this reviewed revision only.
assert hashlib.sha256(design_bytes).hexdigest()=='925a7b6ce211797d4736fe2c40fe71bb551b98bb3f720738f26e49a36e26dd7c', 'Design changed: review and update generator before regenerating'
D=json.loads(design_bytes)
NAME='JST_GH_BM04B-GHS-TBT_1x04-1MP_P1.25mm_Vertical'
assert hashlib.sha256((OUT/'gh4.pretty'/f'{NAME}.kicad_mod').read_bytes()).hexdigest()==D['footprint_source']['sha256']
assert p.GetBuildVersion().startswith('10.0.6'),p.GetBuildVersion()
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'gh4-coupon:'+s))
def v(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def layers(*ids):
    ls=p.LSET()
    for layer in ids: ls.AddLayer(layer)
    return ls
def prop(n,s,x,y,hide=False): return f'(property {q(n)} {q(s)} (at {x} {y} 0) (effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""}))'

# Small project-local passive symbols; numbers explicitly map to the pinned lands.
symbols=[]
for name,n in [('GH4',4),('TP',1)]:
    pins='\n'.join(f'(pin passive line (at -5.08 {-i*2.54} 0) (length 2.54) (name {q(str(i+1))} (effects (font (size 1.27 1.27)))) (number {q(str(i+1))} (effects (font (size 1.27 1.27)))))' for i in range(n))
    symbols.append(f'(symbol {q(name)} (pin_names (offset 1.016)) (in_bom yes) (on_board yes) {prop("Reference","J" if n==4 else "TP",0,5.08)} {prop("Value",name,0,2.54)} (symbol {q(name+"_0_1")} (rectangle (start -2.54 1.27) (end 2.54 {-2.54*(n-1)-1.27}) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol {q(name+"_1_1")} {pins}))')
(OUT/'coupon.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "gh4_coupon")\n'+'\n'.join(symbols)+'\n)\n')
(OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "coupon") (type "KiCad") (uri "${KIPRJMOD}/coupon.kicad_sym") (options "") (descr "Isolated passive coupon symbols")))\n')
(OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "gh4") (type "KiCad") (uri "${KIPRJMOD}/gh4.pretty") (options "") (descr "Pinned JST GH footprint and coupon lands")))\n')
sch=[f'(kicad_sch (version 20260306) (generator "gh4_coupon") (uuid "{uid("root")}") (paper "A4")', '(lib_symbols '+ '\n'.join(s.replace('(symbol "'+n+'"','(symbol "coupon:'+n+'"',1) for s,n in zip(symbols,['GH4','TP']))+')']
for ref,kind,x,y,count in [('J1','GH4',63.5,50.8,4)]+[(f'TP{i}','TP',114.3,38.1+i*12.7,1) for i in range(1,5)]:
    value=D['header']['mpn'] if ref=='J1' else ref
    fp='gh4:'+NAME if ref=='J1' else 'gh4:Coupon_TP_2mm'
    sch.append(f'(symbol (lib_id "coupon:{kind}") (at {x} {y} 0) (unit 1) (in_bom {"yes" if ref=="J1" else "no"}) (on_board yes) (dnp no) (uuid "{uid(ref)}") '+prop('Reference',ref,x,y-5)+prop('Value',value,x,y-2.5)+prop('Footprint',fp,x,y,True)+prop('Datasheet','https://www.jst-mfg.com/product/pdf/eng/eGH.pdf' if ref=='J1' else '',x,y,True)+f'(instances (project "gh4-coupon" (path "/{uid("root")}" (reference "{ref}") (unit 1)))))')
    for i in range(count):
        net=f'GH{i+1}' if ref=='J1' else 'GH'+ref[2:]
        py=y+i*2.54
        sch.append(f'(wire (pts (xy {x-5.08} {py}) (xy {x-15.24} {py})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(i)+"wire")}"))')
        sch.append(f'(global_label "{net}" (shape passive) (at {x-15.24} {py} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uid(ref+str(i)+"label")}"))')
sch.append(f'(text "UNPOWERED SAMPLE - REVIEW ONLY\\nJ1 pin n to TPn; GH1-GH4 independent; no supply" (at 60 110 0) (effects (font (size 1.5 1.5)) (justify left)) (uuid "{uid("note")}"))')
sch.append('(sheet_instances (path "/" (page "1"))) (embedded_fonts no))')
(OUT/'gh4-coupon.kicad_sch').write_text('\n'.join(sch)+'\n')

b=p.BOARD()
b.SetCopperLayerCount(2)
b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
b.SetLayerName(p.Dwgs_User,'V-CUT-REVIEW')
nets={}
for i in range(1,5):
    net=p.NETINFO_ITEM(b,f'GH{i}',i);b.Add(net);nets[i]=net
def text(s,x,y,layer=p.F_SilkS,size=1):
    t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.15));t.SetLayer(layer);b.Add(t)
def line(a,c,layer,width=.1):
    z=p.PCB_SHAPE(b);z.SetShape(p.SHAPE_T_SEGMENT);z.SetStart(v(*a));z.SetEnd(v(*c));z.SetWidth(p.FromMM(width));z.SetLayer(layer);b.Add(z)
for a,c in [((0,0),(80,0)),((80,0),(80,100)),((80,100),(0,100)),((0,100),(0,0))]:line(a,c,p.Edge_Cuts)
for y in (10,90):
    line((0,y),(80,y),p.Dwgs_User)
    text('V-CUT FULL WIDTH - NOT A SLOT',40,y-2,p.Dwgs_User,1)
header=p.FootprintLoad(str(OUT/'gh4.pretty'),NAME)
header.SetReference('J1');header.SetValue(D['header']['mpn']);header.SetFPID(p.LIB_ID('gh4',NAME));header.SetPosition(v(40,50));header.SetPath(p.KIID_PATH('/'+uid('root')+'/'+uid('J1')))
header.GetField('Datasheet').SetText('https://www.jst-mfg.com/product/pdf/eng/eGH.pdf');header.Reference().SetPosition(v(40,44));header.Value().SetVisible(False)
for pad in header.Pads():
    if pad.GetNumber().isdigit():pad.SetNet(nets[int(pad.GetNumber())])
b.Add(header)
def land(ref,name,x,y,diam,net=None,mask=.05,npth=False):
    f=p.FOOTPRINT(b);f.SetReference(ref);f.SetValue(ref if net else name);f.SetBoardOnly(not bool(net));f.SetFPID(p.LIB_ID('gh4',name));f.SetAttributes(p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES | (p.FP_BOARD_ONLY if not net else 0) | (p.FP_THROUGH_HOLE if npth else p.FP_SMD))
    pad=p.PAD(f);pad.SetNumber('1' if net else '');pad.SetShape(p.PAD_SHAPE_CIRCLE);pad.SetSize(v(diam,diam));pad.SetAttribute(p.PAD_ATTRIB_NPTH if npth else p.PAD_ATTRIB_SMD)
    pad.SetLayerSet(layers(p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask) if npth else layers(p.F_Cu,p.F_Mask));pad.SetLocalSolderMaskMargin(p.FromMM(mask))
    if npth:pad.SetDrillSize(v(diam,diam))
    if net:pad.SetNet(nets[net]);f.SetPath(p.KIID_PATH('/'+uid('root')+'/'+uid(ref)))
    f.Add(pad);p.FootprintSave(str(OUT/'gh4.pretty'),f);f.SetPosition(v(x,y));f.Reference().SetPosition(v(x,y+3));f.Reference().SetTextSize(v(1,1));f.Reference().SetTextThickness(p.FromMM(.15));f.Value().SetVisible(False);b.Add(f)
    if not net:f.Reference().SetVisible(False)
for tp in D['testpads']:land('TP'+str(tp['number']),'Coupon_TP_2mm',*tp['at'],2,tp['number'])
for i,xy in enumerate(D['fiducials']['centres'],1):land('FID'+str(i),'Coupon_Fiducial_1mm',*xy,1,mask=.5)
for i,xy in enumerate(D['tooling']['centres'],1):land('H'+str(i),'Coupon_Tooling_2mm',*xy,2,npth=True)
for i,pad in enumerate(D['header']['pads'],1):
    x=40+pad['at'][0];xy=[(x,51.95),(x,57),(D['testpads'][i-1]['at'][0],66),tuple(D['testpads'][i-1]['at'])]
    for a,c in zip(xy,xy[1:]):
        t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(p.FromMM(.25));t.SetLayer(p.F_Cu);t.SetNet(nets[i]);b.Add(t)
def keepout(rect,layers,footprints=True):
    x1,y1,x2,y2=rect;z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayerSet(layers);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowPads(True);z.SetDoNotAllowFootprints(footprints)
    poly=z.Outline();poly.NewOutline()
    for xy in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]:poly.Append(*[p.FromMM(a) for a in xy])
    b.Add(z)
for rect in D['clamp_keepouts_both_faces']:keepout(rect,layers(p.F_Cu,p.B_Cu))
for y in (10,90):keepout((0,y-1,80,y+1),layers(p.F_Cu,p.B_Cu))
text('UNPOWERED SAMPLE',40,21,size=1.5);text('GH4 R1 - REVIEW ONLY',40,25,size=1.2)
text('PIN 1',34,54,size=.8);text('TOP VIEW   +X >   +Y DOWN',40,82,size=1)
text('80 x 80 FUNCTIONAL / 80 x 100 OVERALL',40,85,p.Dwgs_User,1)
p.SaveBoard(str(OUT/'gh4-coupon.kicad_pcb'),b)
project={'meta':{'filename':'gh4-coupon.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':.25,'min_track_width':.25,'min_copper_edge_clearance':1.0},'rule_severities':{'missing_courtyard':'ignore'}}},'net_settings':{'classes':[{'name':'Default','clearance':.25,'track_width':.25,'via_diameter':.6,'via_drill':.3}],'meta':{'version':4}},'sheets':[],'text_variables':{}}
(OUT/'gh4-coupon.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
(OUT/'gh4-coupon.kicad_dru').write_text('(version 1)\n(rule "Coupon 0.25 mm separation" (constraint clearance (min 0.25mm)))\n(rule "Coupon trace width" (constraint track_width (min 0.25mm)))\n(rule "Copper edge clearance" (constraint edge_clearance (min 1mm)))\n')
print('Generated isolated unpowered coupon with',p.GetBuildVersion())
