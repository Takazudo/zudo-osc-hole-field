"""Additive source comparison; no PCB regeneration, routing or hardware qualification."""
from pathlib import Path
import copy, hashlib, importlib.util, json, sys
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
OLD=ROOT/'design/architecture-278/implementation/stage38/mult-common-board'
spec=importlib.util.spec_from_file_location('stage38_geometry',OLD/'generate.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)

def read(p):return json.loads((ROOT/p).read_text())
def bounds(points):return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
def pack(packages,blockers,region):
    placed={}
    for q0 in sorted(packages,key=lambda q:-(lambda b:(b[2]-b[0])*(b[3]-b[1]))(g.courtyard(q['footprint']))):
        q=copy.deepcopy(q0);found=False
        for yi in range(int(region[1]*2),int(region[3]*2)+1):
            for xi in range(int(region[0]*2),int(region[2]*2)+1):
                o=[xi/2,yi/2];b,pads=g.shape(q['footprint'],o,True)
                if not g.inside(b,region) or any(g.ov(g.grow(b,.25),v) for v in blockers):continue
                q.update(origin=o,box=b,pads=pads,side='rear',rotation=0)
                for p in pads:p['net']=q['pins'][p['pin']]
                placed[q['ref']]=q;blockers.append(b);found=True;break
            if found:break
        if not found:raise ValueError('capacity failure '+q['ref'])
    return placed

def header(template,nets,center,side):
    # Retained maker drawing dimensions; no assumed mated height or cable length.
    n=len(nets);tb=template['header_max_xy_mm'];width=tb[2]-tb[0];height=tb[3]-tb[1]
    b=g.box(*center,width,height);pins=[]
    for old,net in zip(template['coordinates']['pins'],nets):
        x,y=old['header_face_xy'];sx,sy=old['socket_face_xy'];sign=-1 if side=='rear' else 1
        xy=[center[0]+sign*x,center[1]+y]
        pins.append({'pin':old['pin'],'net':net,'header_face_xy':[x,y],'socket_face_xy':[sx,sy],'global_xy':xy,'socket_global_xy':[center[0]+sign*sx,center[1]-sy],'pad_box':g.box(*xy,1.6,1.6)})
    return {'center':center,'side':side,'header_mpn':f'D25{n:02d}-6002-AR','socket_mpn':f'891{n:02d}-0101','body_max_xy':b,'body_allowance_xy':g.grow(b,1),'grip_trial_xy':g.grow(b,3),'pins':pins,'pad_diameter_trial_mm':1.6,'finished_hole_interval_mm':[.8128,.9652],'mated_max_height_mm':None,'cable_cut_length_mm':None,'bend_radius_mm':None,'status':'PROJECT proposal, body drawing envelope only; actual grip, mated height and cable unknown'}

def crossings(packages,front):
    owners={}
    for r,q in packages.items():
        for pin,net in q['pins'].items():
            if net is not None:owners.setdefault(net,{'front':[],'rear':[]})['front' if r in front else 'rear'].append(r+':'+pin)
    return {n:v for n,v in owners.items() if v['front'] and v['rear']}

def build():
    old=read(str((OLD/'layout.json').relative_to(ROOT)));pk=old['packages_B1']
    lock=read('design/grid/placements.lock.json')['placements'];partition=read('design/partition/partition.json')
    jl=read('design/partition/jack-white-current/osc-jack-left.json')
    placements=read('boards/osc-jack-left/reports/placement.json')['placements']
    edge=read('boards/osc-jack-left/osc-jack-left.kicad_pro')['board']['design_settings']['rules']['min_copper_edge_clearance']
    # Compute all row seams in the four fixed columns, not only Stage38's final row.
    seams=[];columns=[];jack=pk['J109']['footprint']
    for x in sorted({p['x_mm'] for p in lock if p['block'] in ('B1','B2') and p['kind']=='jack'}):
        col=sorted((p for p in lock if p['kind']=='jack' and p['x_mm']==x),key=lambda p:p['y_mm']);columns.append({'x':x,'refs':[p['ref'] for p in col]})
        for a,b in zip(col,col[1:]):
            pa=next(p for p in g.shape(jack,[x,a['y_mm']],False,a['rot_deg'])[1] if p['pin']=='T')
            pb=next(p for p in g.shape(jack,[x,b['y_mm']],False,b['rot_deg'])[1] if p['pin']=='S')
            gap=round(pb['box'][1]-pa['box'][3],6)
            seams.append({'upper':a['ref'],'lower':b['ref'],'x':x,'gap_mm':gap,'required_edges_mm':2*edge,'overlap_mm':round(2*edge-gap,6)})
    # Source placement report is a retained placement screen, not a fresh native placement check.
    region=[7.5,132.5,38.5,161.5];study=[7,132,73,174.5]
    foreign=[p for p in placements if p['block'] not in ('B1','B2') and p['side']=='B.Cu' and g.ov(p['courtyard_mm'],study)]
    # All fixed panel PTH in the footprint projection neighborhood, across all families.
    fs,ins=g.specification();fm={f.name:f for f in fs};fixed={p['ref']:p for p in lock};pth=[]
    for i in ins:
        for p in fm[i.family].parts:
            if not p.panel_refs or not p.footprint or p.unit not in (0,1):continue
            ref=g.designator(p,i)
            if ref not in fixed:continue
            k=fixed[ref];_,pads=g.shape(g.fp_path(p),[k['x_mm'],k['y_mm']],False,k['rot_deg'])
            for pad in pads:
                if pad['type']=='thru_hole' and g.ov(g.grow(pad['box'],.5),study):pth.append({'ref':ref,'pin':pad['pin'],'box':g.grow(pad['box'],.5),'depth':'UNKNOWN installed tail'})
    supports=[{'id':h['id'],'center':h['center'],'drill_mm':h['diameter_mm'],'tool_trial_xy':g.box(*h['center'],8,8),'status':'Retained hole;8mm tool/fastener reservation PROJECT trial, strength/actual fastener unknown'} for h in jl['mounting_holes']]
    keepouts=[{'id':k['id'],'box':bounds(k['polygon'])} for k in jl['keepouts'] if 'B.Cu' in k['layers'] and g.ov(bounds(k['polygon']),study)]
    global_blockers=[p['courtyard_mm'] for p in foreign]+[p['box'] for p in pth]+[s['tool_trial_xy'] for s in supports]+[k['box'] for k in keepouts]
    # Both instances must fit simultaneously with exactly identical coordinates modulo34mm.
    local_blockers=[g.shift(b,-dx) for dx in (0,34) for b in global_blockers]
    active=[q for q in pk.values() if not q['panel']]
    a=pack(active,local_blockers.copy(),region)
    a.update({r:copy.deepcopy(q) for r,q in pk.items() if q['panel']})
    indicator={r for r,q in pk.items() if all(u['key'].startswith('LED_') for u in q['units'])}
    front=indicator|{r for r,q in pk.items() if q['panel']};rear=set(pk)-front
    src=read('design/architecture-278/implementation/stage36/idc-service-placement/candidate.json')['connectors']
    templates={len(c['coordinates']['pins']):c for c in src}
    signals=['IN_TIP','AGND','OUT_1_TIP','AGND','OUT_2_TIP','AGND','OUT_3_TIP','AGND','IN_BUFFER','AGND']
    signal_front=header(templates[10],signals,[23,169],'rear')
    signal_rear=header(templates[10],signals,[23,169],'front')
    power_rear=header(templates[8],['+12V','AGND','-12V','AGND','+5V','AGND',None,None],[23,125],'front')
    b_supports=[{'center':[11,y],'drill_mm':3.4,'body_xy':g.box(11,y,6.4,6.4),'tool_trial_xy':g.box(11,y,8,8),'anchor_depth_interval_mm':[11.6,40],'status':'Two new supports per rear board; anchor, material, stiffness, fastener and full column volume unresolved'} for y in (137,157)]
    b_blockers=[s['tool_trial_xy'] for s in b_supports]+[g.grow(p['pad_box'],.5) for c in (signal_rear,power_rear) for p in c['pins']]
    b=pack([pk[r] for r in sorted(rear)],b_blockers.copy(),region)
    # Detailed necessary XY screens, deliberately separate from occupied/unknown depth.
    a_hits=[[r,p['ref'],dx] for dx in (0,34) for r,q in a.items() if not q['panel'] for p in foreign if g.ov(g.grow(g.shift(q['box'],dx),.25),p['courtyard_mm'])]
    front_hits=[[p['ref'],p['pin']] for p in pth if g.ov(signal_front['grip_trial_xy'],p['box']) or g.ov(g.shift(signal_front['grip_trial_xy'],34),p['box'])]
    rear_outline=[7,118,39,174.5]
    foreign_boards=[]
    for board in partition['boards']:
        if board['id']=='osc-jack-left':continue
        bb=bounds(board['outline'])
        for dx in (0,34):
            if g.ov(g.shift(rear_outline,dx),bb):foreign_boards.append({'instance':'B1' if dx==0 else 'B2','board':board['id'],'outline':board['outline'],'face_depth_mm':abs(board['face_z_mm']),'status':'Projected occupancy; populated depth, support and service sweep UNKNOWN; not a collision claim'})
    front_selector=[]
    for board in partition['boards']:
        if not board['id'].startswith('osc-octave'):continue
        pts=board['outline'];bb=bounds(pts);mid=sorted(set(p[1] for p in pts))[1]
        rects=[[bb[0],mid,bb[2],bb[3]],[pts[1][0],bb[1],pts[3][0],mid]]
        for dx in (0,34):
            for kind,key in [('body','body_max_xy'),('grip','grip_trial_xy')]:
                if any(g.ov(g.shift(signal_front[key],dx),r) for r in rects):
                    ceiling=round(abs(board['face_z_mm'])-11.6-1,6)
                    front_selector.append({'instance':'B1' if dx==0 else 'B2','selector':board['id'],'reservation':kind,'ceiling_with_1mm_trial_clearance':ceiling,'bare_header_nominal_mm':.390*25.4,'status':'FAIL reserved envelope' if ceiling<.390*25.4 else 'UNKNOWN mated height/withdrawal'})
    anchor_hits=[{'instance':'B1' if dx==0 else 'B2','support':s['center'],'terminal':p['ref']+':'+p['pin']} for dx in (0,34) for s in b_supports for p in pth if g.ov(g.shift(s['body_xy'],dx),p['box'])]
    b_cross=crossings(pk,front);passive_front={r for r,q in pk.items() if q['panel']}
    sources=set(old['source_sha256'])|{str((OLD/f).relative_to(ROOT)) for f in ['generate.py','layout.json','README.md']}|{'boards/osc-jack-left/reports/placement.json','design/partition/jack-white-current/osc-jack-left.json','.claude/skills/circuit-spec-integration/references/rules.json','.claude/skills/component-precision-feedback-passives/facts.json'}
    return {'baseline':'df3ae42a981a1459297f0994a38e4255780c164f','adopted':False,'recommendation':'A: shared incumbent JL substrate with repeated cells; source-screen candidate only','columns':columns,'seams':seams,'stage38_failures':old['boundary_failures'],'A':{'outline':jl['outline'],'depth_trial_mm':[10,11.6],'packages_B1':a,'B2_translation_mm':[34,0],'removed_stage38_headers':2,'removed_stage38_supports':2,'new_mult_analog_cables':0,'new_mult_power_cables':0,'new_mount_holes':0,'shared_board_count':1,'shared_design_count':1,'interchangeable_mult_boards':0,'identical_cells':2,'foreign_package_hits':a_hits,'source_keepouts':keepouts,'retained_mounts':supports,'scope':'Re-place only B1/B2 on JL; foreign circuits unchanged. Layout/copper rerouting required; source report screen not current native clearance proof.'},'B':{'verdict':'Passive front rejected for local LED feedback; active-front placement also blocked by selector/support reservations; not selected','passive_front_refs':sorted(passive_front),'passive_crossings':crossings(pk,passive_front),'front_refs':sorted(front),'rear_refs':sorted(rear),'front_packages_B1':{r:a[r] for r in sorted(front)},'rear_packages_B1':b,'crossings':b_cross,'rear_outline_B1':rear_outline,'rear_depth_trial_mm':[40,41.6],'additional_board_separation_mm':30,'required_enclosure_depth_increase_mm':None,'front_tabs':[[7,164,39,174.5],[41,164,73,174.5]],'front_signal':signal_front,'rear_signal':signal_rear,'rear_power':power_rear,'rear_supports_B1':b_supports,'front_grip_terminal_hits':front_hits,'front_selector_reservations':front_selector,'anchor_terminal_projections':anchor_hits,'foreign_board_projections':foreign_boards,'assembly_board_count':3,'unique_designs':2,'identical_rear_boards':2,'analog_cables':2,'power_cables':2,'new_board_headers_total_including_distribution':8,'cable_sockets':8,'mating_actions':8,'new_rear_support_sites':4,'front_circuit_packages_each':len(front),'rear_circuit_packages_each':len(rear),'status':'Front rails retained from shared JL, +5V needed rear only. Eight cross-boundary nets include three rails/return via existing supply topology, not all through signal10.'},'foreign_rear_placements':foreign,'fixed_pth_reservations':pth,'fixed_markers':old['fixed_markers'],'current_report':old['current_report'],'source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sorted(sources)},'unknowns':old['unknowns']+['B raw input cable exposure and uncompensated output cable/contact error','B front shared-substrate tabs, anchors and selector service volumes','A new copper/decoupling routing and preserved foreign-copper integration']}

def svg(d):
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 820">','<rect width="1100" height="820" fill="#fafafa"/>','<g font-family="sans-serif" fill="#222">','<text x="24" y="30" font-size="22">Stage39: fixed front / shared cells versus separate rear boards</text>','<text x="24" y="55" font-size="14">Proposal only. A preferred for source development; no routed, installed or physical qualification.</text>']
    def rect(b,ox,oy,scale,color,fill,dash=''):
        return f'<rect x="{ox+b[0]*scale}" y="{oy+b[1]*scale}" width="{(b[2]-b[0])*scale}" height="{(b[3]-b[1])*scale}" stroke="{color}" fill="{fill}" stroke-dasharray="{dash}"/>'
    out+=['<text x="24" y="90" font-size="18">A — continuous existing JL substrate</text>']
    ox,oy,s=20,72,1.4
    out.append(rect(bounds(d['A']['outline']),ox,oy,s,'#555','#eff4ef'))
    for col in d['columns']:
        for n,ref in enumerate(col['refs']):
            out.append(rect(g.box(col['x'],29+14*n,9.5,13.9),ox,oy,s,'#7d8c90','none'))
    for dx in (0,34):
        for q in d['A']['packages_B1'].values():
            if not q['panel']:out.append(rect(g.shift(q['box'],dx),ox,oy,s,'#28705c','#9bcbb8'))
    for i,t in enumerate(['40 jacks in four affected columns; all row seams fail.', 'No seam here: retain JL, including foreign ownership.', '2 identical circuit cells; 0 removable mult modules.', 'No added mult signal/power cables or mount holes.', 'No extra board depth; shared-board service remains.']):out.append(f'<text x="24" y="{342+22*i}" font-size="14">{t}</text>')
    out.append('<text x="550" y="90" font-size="18">B — active front + identical rear23 boards</text>')
    for dx,left in [(0,550),(34,800)]:
        ox,oy,s=left-7*4.5,-435,4.5
        out.append(rect(g.shift(d['B']['rear_outline_B1'],dx),ox-dx*s,oy,s,'#555','#f4efe9'))
        for q in d['B']['rear_packages_B1'].values():out.append(rect(q['box'],ox,oy,s,'#28705c','#9bcbb8'))
        for c in (d['B']['rear_signal'],d['B']['rear_power']):out.append(rect(c['body_max_xy'],ox,oy,s,'#a65c1d','#edc9a6'));out.append(rect(c['grip_trial_xy'],ox,oy,s,'#b33','none','3 2'))
        for h in d['B']['rear_supports_B1']:out.append(rect(h['tool_trial_xy'],ox,oy,s,'#758','none','3 2'))
    for i,t in enumerate(['B1 and B2:32 ×56.5 mm rear boards;34 mm translation.', '13 packages/cell remain front;23 move rear.', '2 signal +2 power ribbons /8 mating actions.', 'Shared front tabs and4 new support sites proposed.', 'Front header fails selector envelope; anchors unresolved.']):out.append(f'<text x="550" y="{395+22*i}" font-size="14">{t}</text>')
    out+=['<path d="M35 550 H1060" stroke="#aaa"/>','<text x="24" y="580" font-size="18">Electrical boundary and depth consequences</text>']
    lines=['A keeps raw input, protected/sense nodes, precision feedback and complete LED driver on one board.', 'B passive adapter rejected: a front LED exports the indicator loop. Active front keeps that nine-package loop local.', 'B signal10: input +3 outputs +buffered monitor, each with AGND. Local rear feedback senses before cable losses.', 'B front substrate z10–11.6 → cable/support unknown volume → rear z40–41.6 → component/cover unknown volume.', 'Extra30 mm separation is explicit, unadopted. Enclosure-depth increase cannot be computed from unknown maximum Z.', 'Neither proposal changes locked positions,0.5 mm copper-edge rules, other-family circuits or canonical manufacturing outputs.', 'Selection: A is simpler and resolves the seam without new analog interfaces. Interchangeable modules remain a tradeoff.']
    for i,t in enumerate(lines):out.append(f'<text x="24" y="{612+i*26}" font-size="14">{t}</text>')
    return '\n'.join(out+['</g></svg>'])+'\n'

if __name__=='__main__':
    d=build();(HERE/'comparison.json').write_text(json.dumps(d,indent=2)+'\n');(HERE/'comparison.svg').write_text(svg(d));print(json.dumps({'recommendation':d['recommendation'],'seams':len(d['seams']),'A_foreign_hits':d['A']['foreign_package_hits'],'B_front_grip_hits':d['B']['front_grip_terminal_hits'],'B_selector_failures':[r for r in d['B']['front_selector_reservations'] if r['status'].startswith('FAIL')],'B_crossings':list(d['B']['crossings'])},indent=2))
