"""Populated source-only MULT reuse candidate; no canonical writes/native tools."""
from pathlib import Path
import hashlib, json, math, sys, csv, io
from functools import lru_cache
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts/architecture278'))
from populated_mechanics import sexpr,field,courtyard
from design.spec.modules import mult
from design.spec.instrument import specification
from scripts.schgen.core import designator
HERE=Path(__file__).resolve().parent

def ov(a,b):return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]
def grow(b,d):return [b[0]-d,b[1]-d,b[2]+d,b[3]+d]
def shift(b,dx,dy=0):return [round(b[0]+dx,6),round(b[1]+dy,6),round(b[2]+dx,6),round(b[3]+dy,6)]
def inside(a,b):return a[0]>=b[0] and a[1]>=b[1] and a[2]<=b[2] and a[3]<=b[3]
def box(x,y,w,h):return [x-w/2,y-h/2,x+w/2,y+h/2]
def fp_path(p):return 'footprints/kicad/zudo-osc-hole-field.pretty/'+p.footprint.split(':')[1]+'.kicad_mod'
def transformed(x,y,origin,back=False,angle=0):
    if back:x=-x
    a=math.radians(angle)
    return [round(origin[0]+x*math.cos(a)-y*math.sin(a),6),round(origin[1]+x*math.sin(a)+y*math.cos(a),6)]
@lru_cache(None)
def geometry(path):return courtyard(path),sexpr((ROOT/path).read_text())

def shape(path,origin,back=False,angle=0):
    q,tree=geometry(path);pts=[transformed(x,y,origin,back,angle) for x in (q[0],q[2]) for y in (q[1],q[3])]
    bounds=[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]
    pads=[]
    for p in tree:
        if not isinstance(p,list) or not p or p[0]!='pad':continue
        xy=list(map(float,field(p,'at')[:2]));w,h=map(float,field(p,'size')[:2]);rotation=float(field(p,'at')[2]) if len(field(p,'at'))>2 else 0
        corners=[transformed(x,y,xy,False,rotation) for x in (-w/2,w/2) for y in (-h/2,h/2)]
        coords=[transformed(x,y,origin,back,angle) for x,y in corners]
        pads.append({'pin':p[1],'type':p[2],'shape':p[3],'xy':transformed(*xy,origin,back,angle),
                     'box':[min(x for x,y in coords),min(y for x,y in coords),max(x for x,y in coords),max(y for x,y in coords)],'size':[w,h],'drill':field(p,'drill')})
    return bounds,pads

def build():
    lock=json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements'];locked={p['ref']:p for p in lock}
    fs,ins=mult.specification();f=fs[0];packages={}
    for p in f.parts:
        if not p.on_board or not p.footprint:continue
        r=designator(p,ins[0]);q=packages.setdefault(r,{'ref':r,'B2_ref':designator(p,ins[1]),'footprint':fp_path(p),'value':p.value,'mpn':p.attributes.get('MPN',''),'manufacturer':p.attributes.get('Manufacturer',''),'dnp':p.dnp,'in_bom':p.in_bom,'units':[],'pins':{},'panel':bool(p.panel_refs),'decouples':p.attributes.get('Decouples')})
        if set(q['pins'])&set(p.pins):raise ValueError('duplicate physical pins '+r)
        q['pins'].update(p.pins);q['units'].append({'unit':p.unit,'key':p.key,'pins':p.pins,'role':p.attributes.get('Role','')})
    outline=[7,132,39,174.5];objects=[];tails=[]
    for r,q in packages.items():
        if not q['panel']:continue
        k=locked[r];q.update(origin=[k['x_mm'],k['y_mm']],side='front',rotation=k['rot_deg'])
        q['box'],q['pads']=shape(q['footprint'],q['origin'],False,q['rotation'])
        for pad in q['pads']:
            pad['net']=q['pins'][pad['pin']]
            if pad['type']=='thru_hole':tails.append({'id':r+':'+pad['pin'],'box':grow(pad['box'],.5),'status':'THROUGH terminal/copper +0.5mm XY; tail length UNKNOWN'})
    # Source capacity packing on reverse face. It is not a routed signal-quality layout.
    blocked=[x['box'] for x in tails]
    parts=sorted((q for q in packages.values() if not q['panel']),key=lambda q:-(lambda b:(b[2]-b[0])*(b[3]-b[1]))(courtyard(q['footprint'])))
    for q in parts:
        found=None
        for yi in range(267,324):
            for xi in range(16,76):
                o=[xi/2,yi/2];b,pads=shape(q['footprint'],o,True)
                if inside(b,[7.5,132.5,38.5,161.5]) and not any(ov(grow(b,.25),v) for v in blocked):found=(o,b,pads);break
            if found:break
        if not found:raise ValueError('capacity failure '+q['ref'])
        o,b,pads=found;q.update(origin=o,box=b,pads=pads,side='rear',rotation=0)
        for pad in pads:pad['net']=q['pins'][pad['pin']]
        blocked.append(b)
    for q in packages.values():
        if set(q['pins'])!={p['pin'] for p in q['pads']}:raise ValueError('footprint pin mismatch '+q['ref'])
    source=json.loads((ROOT/'design/architecture-278/implementation/stage36/idc-service-placement/candidate.json').read_text())
    template=next(c for c in source['connectors'] if c['ref']=='J17903')
    power=['+12V','AGND','-12V','AGND','+5V','AGND',None,None]
    center=[28,169];header=box(*center,.693*25.4,.343*25.4)
    connector={'ref':'P8','center':center,'header_mpn':'D2508-6002-AR','socket_mpn':'89108-0101','side':'rear','header_face_to_panel_xy':[[-1,0],[0,1]],'socket_mating_face_to_panel_xy':[[-1,0],[0,-1]],'body_max_xy':header,'body_allowance_xy':grow(header,1),'grip_trial_xy':grow(header,3),'mated_max_height':None,'cut_length':None,'bend_radius':None,'finished_hole_interval_mm':[.8128,.9652],'pad_diameter_trial_mm':1.6,'pad_status':'PROJECT CHOICE, fabrication annular/drill tolerance unresolved','pins':[]}
    for old,net in zip(template['coordinates']['pins'],power):
        xy=[center[0]-old['header_face_xy'][0],center[1]+old['header_face_xy'][1]]
        connector['pins'].append({'pin':old['pin'],'net':net,'global_xy':xy,'header_face_xy':old['header_face_xy'],'socket_face_xy':old['socket_face_xy'],'pad_box':box(*xy,1.6,1.6)})
    support={'center':[10.5,166],'drill_mm':3.4,'body_reservation':box(10.5,166,6.4,6.4),'tool_reservation':box(10.5,166,8,8),'z_trial':[11.6,20],'status':'One proposed insulating support; carrier anchorage/material/MPN/stiffness UNKNOWN; four panel jack bushings also unqualified'}
    # Exact equality target: no instance-specific values, channels, nets or rotations.
    b2={r:{'ref':q['B2_ref'],'origin':[q['origin'][0]+34,q['origin'][1]],'box':shift(q['box'],34),'pads':[{**p,'xy':[p['xy'][0]+34,p['xy'][1]],'box':shift(p['box'],34)} for p in q['pads']]} for r,q in packages.items()}
    # Boundary theorem: separate coplanar PCB edges each need retained0.5 copper clearance.
    rules=json.loads((ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pro').read_text())['board']['design_settings']['rules'];edge=rules['min_copper_edge_clearance']
    boundary=[]
    jack='footprints/kicad/zudo-osc-hole-field.pretty/Jack_3.5mm_QingPu_WQP518MA.kicad_mod'
    for inst in ('B1','B2'):
        for p in lock:
            if p['block']!=inst or p['kind']!='jack' or p['y_mm']!=141:continue
            above=next(v for v in lock if v['kind']=='jack' and v['x_mm']==p['x_mm'] and v['y_mm']==127)
            own=next(v for v in shape(jack,[p['x_mm'],p['y_mm']])[1] if v['pin']=='S')
            other=next(v for v in shape(jack,[above['x_mm'],above['y_mm']])[1] if v['pin']=='T')
            upper=own['box'][1]-edge;lower=other['box'][3]+edge
            boundary.append({'instance':inst,'own_sleeve':p['ref'],'foreign_tip':above['ref'],'copper_gap_mm':round(own['box'][1]-other['box'][3],6),'each_edge_requirement_mm':edge,'foreign_board_min_end_y':round(lower,6),'candidate_max_start_y':round(upper,6),'minimum_board_overlap_mm':round(lower-upper,6),'status':'FAIL: no disjoint coplanar board outlines containing retained pads with0.5mm edges, even at zero inter-board gap'})
    # All locked foreign hardware remains occupied/unknown in depth; use real footprints, not marker radii.
    allfs,allins=specification();fmap={f.name:f for f in allfs};foreign=[]
    for i in allins:
        for p in fmap[i.family].parts:
            if not p.panel_refs or not p.footprint or p.unit not in (0,1):continue
            ref=designator(p,i)
            if ref not in locked or locked[ref]['block'] in ('B1','B2'):continue
            k=locked[ref];path=fp_path(p);b,pads=shape(path,[k['x_mm'],k['y_mm']],False,k['rot_deg'])
            if not any(ov(b,shift(outline,d)) for d in (0,34)):continue
            foreign.append({'ref':ref,'uid':k['uid'],'footprint':path,'box':b,'pads':pads,'z':'UNKNOWN installed body/tail/support; projection is not physical collision'})
    # Retained selector board polygons, compared to connector/grip as polygons decomposed into rectangles.
    partition=json.loads((ROOT/'design/partition/partition.json').read_text());sel=[]
    for b in partition['boards']:
        if not b['id'].startswith('osc-octave'):continue
        pts=b['outline'];xs=[p[0] for p in pts];ys=[p[1] for p in pts]
        main=[min(xs),sorted(set(ys))[1],max(xs),max(ys)];tab=[pts[1][0],min(ys),pts[3][0],main[1]]
        for inst,dx in [('B1',0),('B2',34)]:
            for label,xy in [('body',connector['body_allowance_xy']),('grip',connector['grip_trial_xy']),('support',support['tool_reservation'])]:
                if any(ov(shift(xy,dx),r) for r in [main,tab]):sel.append({'instance':inst,'object':label,'selector_board':b['id'],'z':abs(b['face_z_mm']),'status':'KNOWN retained board projection; actual assembly maximum/sweep UNKNOWN'})
    screens={
        'rear_package_pair_hits':[[a['ref'],b['ref']] for n,a in enumerate(parts) for b in parts[n+1:] if ov(grow(a['box'],.25),b['box'])],
        'rear_terminal_hits':[[q['ref'],t['id']] for q in parts for t in tails if ov(q['box'],t['box'])],
        'header_body_package_hits':[q['ref'] for q in parts if ov(connector['body_allowance_xy'],q['box'])],
        'grip_package_hits':[q['ref'] for q in parts if ov(connector['grip_trial_xy'],q['box'])],
        'grip_terminal_hits':[t['id'] for t in tails if ov(connector['grip_trial_xy'],t['box'])],
        'support_tool_package_hits':[q['ref'] for q in parts if ov(support['tool_reservation'],q['box'])],
        'support_header_hit':ov(support['tool_reservation'],connector['body_allowance_xy']),
        'copper_edge_failures':[q['ref']+':'+p['pin'] for q in packages.values() for p in q['pads'] if not inside(grow(p['box'],edge),outline)]}
    bypass=[]
    for q in packages.values():
        if not q['decouples']:continue
        owner=next(v for v in packages.values() if any(u['key'].rsplit('.',1)[0]==q['decouples'] for u in v['units']))
        rail=next(n for n in q['pins'].values() if n!='AGND')
        a=next(p['xy'] for p in q['pads'] if p['net']==rail)
        endpoints=[p['xy'] for p in owner['pads'] if p['net']==rail]
        bypass.append({'capacitor':q['ref'],'owner':owner['ref'],'rail':rail,'straight_pad_distance_mm':round(min(math.dist(a,b) for b in endpoints),6),'routed_loop_length_mm':None,'status':'Placement diagnostic only; no decoupling-quality pass'})
    current=json.loads((ROOT/'design/reports/current/mult.json').read_text())
    pins={n:[] for n in f.sensitive_nets}
    for q in packages.values():
        for pin,net in q['pins'].items():
            if net in pins:pins[net].append(q['ref']+':'+pin)
    sources=['design/grid/placements.lock.json','design/partition/partition.json','boards/osc-jack-left/osc-jack-left.kicad_pro','design/reports/current/mult.json','design/mechanical/facts/jack.json','design/mechanical/kingbright-white-land.json','design/mechanical/facts/led-window.json','design/mechanical/selector-assembly.json','design/standard/ic-library-capture.json','design/architecture-278/implementation/stage36/idc-service-placement/candidate.json','design/architecture-278/implementation/stage36/standard-idc-assembly/sources.json','design/architecture-278/implementation/stage37/family-reuse/proposal.json','scripts/architecture278/populated_mechanics.py','scripts/schgen/core.py']
    sources+= [str(p.relative_to(ROOT)) for p in sorted((ROOT/'design/spec').rglob('*.py'))]
    sources+=sorted({q['footprint'] for q in packages.values()}|{q['footprint'] for q in foreign})
    return {'baseline':'8dbbc9d835832b0b55d7745692963fe2da0d29e8','adopted':False,'verdict':'REJECT coplanar standalone extraction under retained edge rules; translation/electrical target only PASS','outline_B1':outline,'outline_B2':shift(outline,34),'pcb_depth_trial':[10,11.6],'outline_status':'32x42.5mm populated source trial; not approved for manufacture','packages_B1':packages,'translation_B2':b2,'connector':connector,'support':support,'fixed_markers':[p for p in lock if p['block'] in ('B1','B2')],'tail_keepouts':tails,'source_screens':screens,'boundary_failures':boundary,'foreign_fixed_projections':foreign,'selector_projection_hits':sel,'sensitive_local_endpoints':pins,'bypass_diagnostics':bypass,'current_report':current,'return_planning_sum_mA':round(sum(current['instances'][0]['planning_maximum_mA_per_rail'].values()),6),'return_guaranteed_mA':None,'source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sorted(set(sources))},'first_rejected_grip':{'center':[28,168],'hit':'J210:T terminal +0.5mm reservation','reason':'symmetric grip trial overlaps tail reservation; final center moved+1mm Y, no terminal moved'},'header_y_necessary_interval_mm':[168.8411,169.1439],'counts':{'canonical_family_packages_each':36,'populated_candidate_packages_each_including_header':37,'two_mult_main_boards':2,'main_unique_designs':1,'power_cables':2,'header_ends_including_distribution':4,'socket_terminations':4,'mating_actions':4,'support_sites':2,'optional_optical_substrates':2,'optional_total_boards':4,'optional_unique_designs':2,'optional_LED_wires':4,'optional_LED_solder_joints':8},'unknowns':['actual jack seating, terminal length and tolerances','optical path and emitter plane','all foreign installed heights/tails and incumbent board coexistence','actual component heights and routing/decoupling quality','connector seating/maximum, exits, ribbon construction and bend limits','support carrier anchorage and retention strength','guaranteed rail/return/fault/transient currents','three blank resistor MPNs','complete remove/park/unplug sequence']}

def bom_csv(d):
    out=io.StringIO();w=csv.writer(out,lineterminator='\n')
    w.writerow(['B1_reference','B2_reference','quantity_per_board','value','MPN','footprint','status'])
    for r,q in sorted(d['packages_B1'].items()):
        w.writerow([r,q['B2_ref'],1,q['value'],q['mpn'],q['footprint'],'SOURCE TARGET; not released' if q['mpn'] else 'MPN UNRESOLVED'])
    w.writerow(['P8','P8',1,'8-way header','D2508-6002-AR','NEW land proposal in layout.json','PROPOSED; not canonical'])
    return out.getvalue()

def svg(d):
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 590">','<rect width="980" height="590" fill="#fafafa"/>','<g font-family="sans-serif" fill="#222">','<text x="20" y="30" font-size="21">B1 → B2 common MULT board: populated source trial, NOT adopted</text>','<text x="20" y="54" font-size="14">Exact34mm translation. Rear SMT shown in green; fixed front jacks dashed. Copper-edge separation FAILS.</text>']
    for label,dx,left in [('B1',0,30),('B2',34,380)]:
        scale=7;ox=7+dx;oy=127
        def rect(b,color,fill,dash=''):
            return f'<rect x="{left+(b[0]-ox)*scale}" y="{92+(b[1]-oy)*scale}" width="{(b[2]-b[0])*scale}" height="{(b[3]-b[1])*scale}" stroke="{color}" fill="{fill}" stroke-dasharray="{dash}"/>'
        out.append(f'<text x="{left}" y="82" font-size="18">{label} /32×42.5mm /37packages</text>');out.append(rect(shift(d['outline_B1'],dx),'#333','#f4f4ef'))
        for q in d['packages_B1'].values():
            b=shift(q['box'],dx);out.append(rect(b,'#28705c','none' if q['panel'] else '#c6ded5','3 2' if q['panel'] else ''))
            out.append(f'<text x="{left+(b[0]-ox)*scale}" y="{90+(b[1]-oy)*scale}" font-size="8">{q["ref"] if dx==0 else q["B2_ref"]}</text>')
            for p in q['pads']:out.append(rect(shift(p['box'],dx),'#b88b30','#e7c771'))
        out.append(rect(shift(d['connector']['body_max_xy'],dx),'#a65c1d','#edc9a6'))
        out.append(rect(shift(d['connector']['grip_trial_xy'],dx),'#c44','none','3 2'))
        out.append(rect(shift(d['support']['tool_reservation'],dx),'#758','none','3 2'))
        out.append(f'<text x="{left+120}" y="378" font-size="12">P8 (new pin map)</text>')
        for b in d['boundary_failures']:
            if b['instance']!=label:continue
            k=next(p for p in d['fixed_markers'] if p['ref']==b['own_sleeve']);x=left+(k['x_mm']-ox)*scale
            out.append(f'<path d="M{x-9},130 L{x+9},148 M{x-9},148 L{x+9},130" stroke="#c22" stroke-width="2"/>')
    lines=['Retained edge rule:0.5mm on each PCB; adjacent pad gap only0.62mm.', 'Required two-edge total1.00mm → unavoidable0.38mm overlap, even with zero board gap.', 'Four boundary failures: two top-row terminals for B1 and two for B2. No threshold relaxed.', 'Footprint/translation proof is not physical fit. Optical, tails, support, cable and foreign Z remain open.', 'Next source decision: shared front substrate or separately supported deeper electronics + front adapters.', 'Neither alternative is adopted or populated here; the Stage37 95conceptual projections are separate.']
    for i,line in enumerate(lines):out.append(f'<text x="20" y="{450+i*23}" font-size="14">{line}</text>')
    return '\n'.join(out+['</g></svg>'])+'\n'

if __name__=='__main__':
    d=build();(HERE/'layout.json').write_text(json.dumps(d,indent=2)+'\n');(HERE/'layout.svg').write_text(svg(d));(HERE/'assembly-target.csv').write_text(bom_csv(d))
    print(json.dumps({'screens':d['source_screens'],'boundaries':d['boundary_failures'],'selector':d['selector_projection_hits']},indent=2))
