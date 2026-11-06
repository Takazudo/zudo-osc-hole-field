"""Native-bound locality and copper integration plan. No mutation of any board."""
from pathlib import Path
import collections,copy,hashlib,importlib.util,json,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=load('native_mult_plan',HERE/'native.py');s39=load('retained39',ROOT/'design/architecture-278/implementation/stage39/mult-substrate-comparison/generate.py');g=s39.g
BOARD='boards/osc-jack-left/osc-jack-left.kicad_pcb'
def read(p):return json.loads((ROOT/p).read_text())
def identity(row):return {k:row[k] for k in ('index','kind','uuid','occurrence','sha256')}
def manifest_hash(rows):return hashlib.sha256(json.dumps(sorted((r['kind'],r['uuid'] or '',r['sha256']) for r in rows),separators=(',',':')).encode()).hexdigest()
def copper_layers(row):
    layers=row['layers'];return set(('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')) if row.get('kind')=='via' or '*.Cu' in layers else set(layers)
def pad_layer(q,p):return copper_layers({'layers':p.get('layers',['B.Cu' if q['side']=='rear' else 'F.Cu'])})
def point(pk,r,p):return next(x['xy'] for x in pk[r]['pads'] if x['pin']==p)
def dist(pk,a,pa,b,pb):return round(math.dist(point(pk,a,pa),point(pk,b,pb)),6)
def metrics(pk,logical):
    bypass=[];feedback=[]
    for r,q in logical.items():
        if not q['decouples']:continue
        owner=next(v for v in logical.values() if any(u['key'].rsplit('.',1)[0]==q['decouples'] for u in v['units']))
        rail=next(v for v in q['pins'].values() if v!='AGND');pa=next(p for p,v in q['pins'].items() if v==rail);pb=next(p for p,v in owner['pins'].items() if v==rail)
        bypass.append({'capacitor':r,'owner':owner['ref'],'rail':rail,'endpoints':[[r,pa],[owner['ref'],pb]],'rail_pad_distance_mm':dist(pk,r,pa,owner['ref'],pb),'return_path_length_mm':None})
    for net in sorted({v for q in logical.values() for v in q['pins'].values() if v and v.endswith('_FB')}):
        ends=[[r,p] for r,q in logical.items() for p,v in q['pins'].items() if v==net]
        pairs=[{'a':a,'b':b,'distance_mm':dist(pk,*a,*b)} for i,a in enumerate(ends) for b in ends[i+1:]]
        lengths=sorted(v['distance_mm'] for v in pairs)
        feedback.append({'net':net,'endpoints':ends,'pairs':pairs,'three_pad_mst_proxy_mm':round(sum(lengths[:2]),6),'max_pair_distance_mm':max(lengths),'actual_route_length_mm':None})
    return {'bypass':bypass,'feedback':feedback,'sum_bypass_distances_mm':round(sum(x['rail_pad_distance_mm'] for x in bypass),6),'sum_feedback_mst_proxy_mm':round(sum(x['three_pad_mst_proxy_mm'] for x in feedback),6),'scope':'Pair distances are path lower bounds; feedback terminal-only MST is a proxy, not a routing lower bound; no ground-return loop, via, routed length, stability or inductance qualification'}
def validate_aliases(alias):
    inverse={}
    rails={'AGND','+12V','-12V','+5V'}
    for key,actual in alias.items():
        semantic=key.split(':',1)[1]
        if actual is None:raise ValueError('functional net missing '+key)
        if semantic in rails and actual!=semantic:raise ValueError('global rail identity changed '+key)
        canonical=semantic if semantic in rails else key
        if actual in inverse and inverse[actual]!=canonical:raise ValueError('distinct semantic nets merged '+actual)
        inverse[actual]=canonical

def build():
    old=read('design/architecture-278/implementation/stage39/mult-substrate-comparison/comparison.json');logical=old['A']['packages_B1'];positions=json.loads((HERE/'positions.json').read_text())['positions']
    if set(positions)!=set(logical):raise ValueError('candidate reference set changed')
    native=n.parse((ROOT/BOARD).read_text());fps=native['footprints'];owned=set(logical)|{q['B2_ref'] for q in logical.values()};fixed={r for r,q in logical.items() if q['panel']}|{q['B2_ref'] for q in logical.values() if q['panel']}
    pk={};allnew={};alias={};nc=[];moves=[]
    for r,q in logical.items():
        c=copy.deepcopy(q);c.update(positions[r]);c['box'],c['pads']=g.shape(c['footprint'],c['origin'],c['side']=='rear',c['rotation'])
        if not c['panel'] and not g.inside(c['box'],[7.5,118.5,38.5,163.5]):raise ValueError('candidate outside screened cell region')
        if c['panel'] and positions[r]!={k:q[k] for k in ('origin','rotation','side')}:raise ValueError('fixed front placement changed')
        for pad in c['pads']:pad['net']=c['pins'][pad['pin']]
        pk[r]=c
        for ref,dx in [(r,0),(q['B2_ref'],34)]:
            f=fps[ref];native_pads={p['pin']:p for p in f['pads']}
            if set(native_pads)!=set(c['pins']):raise ValueError('native/source pin mismatch '+ref)
            proposed=copy.deepcopy(c);proposed['ref']=ref;proposed['origin']=[c['origin'][0]+dx,c['origin'][1]];proposed['box']=g.shift(c['box'],dx)
            for pad in proposed['pads']:
                pad['xy']=[pad['xy'][0]+dx,pad['xy'][1]];pad['box']=g.shift(pad['box'],dx);semantic=pad['net'];actual=native_pads[pad['pin']]['net']
                if semantic is None:
                    if actual is not None and not actual.startswith('unconnected-'):raise ValueError('NC pin has native functional net')
                    nc.append({'ref':ref,'pin':pad['pin'],'native_net':actual})
                else:
                    key=('B1' if dx==0 else 'B2')+':'+semantic
                    if key in alias and alias[key]!=actual:raise ValueError('logical net split in native '+key)
                    alias[key]=actual
                pad['native_net']=actual
            allnew[ref]=proposed
            if ref not in fixed:moves.append({'ref':ref,**identity(f),'old':{'origin':f['origin'],'native_angle':f['native_angle'],'layer':f['layer'],'pads':f['pads']},'proposed':{'origin':proposed['origin'],'study_clockwise_angle':c['rotation'],'layer':'B.Cu' if c['side']=='rear' else 'F.Cu','pads':proposed['pads']},'action':'Replace pose/pad geometry from library with explicit face transform; native UUID/pin identity must persist; no board edited'})
    validate_aliases(alias)
    owners=collections.defaultdict(set)
    for ref,f in fps.items():
        for p in f['pads']:
            if p['net']:owners[p['net']].add(ref)
    private={v for v in alias.values() if owners[v]<=owned and v not in ('AGND','+12V','-12V','+5V')}
    nets=[{'logical':k,'native':v,'owners':sorted(owners[v]),'class':'module-private reroute' if v in private else 'shared supply/return preserve-and-reconnect'} for k,v in sorted(alias.items())]
    obstacle={l:n.obstacles(native,old,l) for l in ('F.Cu','B.Cu')};hits=[];old_hits=[]
    for ref,c in allnew.items():
        if ref in fixed:continue
        layer='B.Cu' if c['side']=='rear' else 'F.Cu'
        for b in obstacle[layer]:
            if g.ov(g.grow(c['box'],.25),b['box']):hits.append([ref,b['id']])
    for dx in(0,34):
        for r,c in logical.items():
            if c['panel']:continue
            for b in obstacle['B.Cu']:
                if g.ov(g.grow(g.shift(c['box'],dx),.25),b['box']):old_hits.append([r if dx==0 else c['B2_ref'],b['id']])
    pairs=[[a,b] for i,(a,q) in enumerate(allnew.items()) if a not in fixed for b,z in list(allnew.items())[i+1:] if b not in fixed and q['side']==z['side'] and g.ov(g.grow(q['box'],.25),z['box'])]
    if hits or pairs:raise ValueError('candidate footprint conflict '+str(hits+pairs))
    for c in allnew.values():
        for p in c['pads']:
            if not g.inside(g.grow(p['box'],.5),[4,20,176.5,164]):raise ValueError('edge clearance')
    retire=[];shared=[];foreign_new=[];remaining=[]
    movedpads=[(r,p,copper_layers(p)) for r,f in fps.items() if r in owned-fixed for p in f['pads']]
    newpads=[(r,p,set(['B.Cu' if c['side']=='rear' else 'F.Cu'])) for r,c in allnew.items() if r not in fixed for p in c['pads']]
    for copper in native['copper']:
        cp={**identity(copper),'net':copper['net'],'points':copper['points'],'width':copper['width'],'layers':copper['layers']};layers=copper_layers(copper)
        if copper['net'] in private:retire.append({**cp,'action':'proposed whole-private-net retirement and reroute; no external pad owners'});continue
        oldcontacts=[r+':'+p['pin'] for r,p,ls in movedpads if p['net']==copper['net'] and layers&ls and g.ov(g.grow(copper['box'],.000001),p['box'])]
        newconflicts=[r+':'+p['pin'] for r,p,ls in newpads if p['native_net']!=copper['net'] and layers&ls and g.ov(g.grow(copper['box'],.25),p['box'])]
        if oldcontacts:shared.append({**cp,'old_pad_AABB_contacts':oldcontacts,'action':'preserve until branch connectivity review; split/reconnect only demonstrably owned stubs, no whole-shared-net deletion'})
        if newconflicts:foreign_new.append({**cp,'candidate_pad_clearance_AABB_hits':newconflicts,'action':'preserve foreign/shared copper; reroute candidate pad access or explicit bounded connectivity-reviewed cut, never automatic deletion'})
        remaining.append(copper)
    nc_nets={x['native_net'] for x in nc};nc_copper=[identity(c) for c in native['copper'] if c['net'] in nc_nets]
    if nc_copper:raise ValueError('native NC has routed copper')
    zoneplans=[{**z,'action':'PRESERVE rule-area bytes' if z['is_keepout'] else 'PRESERVE definition; refill all five filled copper zones after candidate routing, then compare connectivity/warnings'} for z in native['zones']]
    current_metrics={}
    for inst in ('B1','B2'):
        current_metrics[inst]=metrics({r:{'pads':fps[r if inst=='B1' else q['B2_ref']]['pads']} for r,q in logical.items()},logical)
    sources=set(old['source_sha256'])|{BOARD,'boards/osc-jack-left/osc-jack-left.kicad_dru','scripts/pcbgen/uuid_tools.py','scripts/pcbgen/copper_identity.py','design/architecture-278/implementation/stage39/mult-substrate-comparison/comparison.json','design/architecture-278/implementation/stage39/mult-substrate-comparison/generate.py',str((HERE/'positions.json').relative_to(ROOT)),str((HERE/'native.py').relative_to(ROOT))}
    return {'baseline':'ab4193cf6b769bda0b86ff45656cbe71db2c1d39','adopted':False,'status':'SOURCE INTEGRATION PLAN ONLY; native routing/DRC/connectivity and hardware NOT RUN','native_board':{'path':BOARD,'sha256':native['board_sha256'],'coordinate_transform':'panel XY = native XY - (100,50); native positive angle rotates clockwise in mathematical Y-up; embedded backside coordinates already reflected','counts':native['counts'],'duplicate_copper_uuids':native['duplicate_copper_uuids']},'candidate_B1':pk,'B2_translation_mm':[34,0],'moves':moves,'net_mapping':nets,'NC_equivalence':nc,'metrics':{'stage39':metrics(logical,logical),'candidate':metrics(pk,logical),'current_native':current_metrics},'obstacles':obstacle,'stage39_native_conflicts':old_hits,'candidate_conflicts':hits+pairs,'private_net_retire_copper':retire,'shared_old_pad_contact_review':shared,'preserved_new_pad_clearance_review':foreign_new,'zones':zoneplans,'preservation':{'all_native_items_multiset_sha256':manifest_hash(native['items']),'foreign_and_fixed_footprints_count':len(fps)-(len(owned)-len(fixed)),'foreign_and_fixed_footprints_multiset_sha256':manifest_hash([f for r,f in fps.items() if r not in owned-fixed]),'private_retirement_count':len(retire),'remaining_copper_count':len(remaining),'remaining_copper_multiset_sha256':manifest_hash(remaining),'no_native_file_written':True,'all_rule_areas_preserve_count':sum(z['is_keepout'] for z in native['zones']),'filled_copper_zone_count':sum(not z['is_keepout'] for z in native['zones'])},'source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sorted(sources)},'limits':['AABB contacts/intersections are conservative candidates, not exact copper connectivity or DRC','No automatic shared-rail, foreign-copper or zone deletion','Pad-centre distances do not establish complete bypass return or feedback routing','Relocated pads invalidate prior local copper/zone-fill assumptions','All private-net retirement is a conservative proposed strategy, not minimum required edits','Existing native open edges and warning identities must be measured before any future native edit','Stage38/39 negative findings remain retained; this mixed-face revision is unadopted']}

def svg(d):
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 800">','<rect width="1160" height="800" fill="#fafafa"/>','<g font-family="sans-serif" fill="#222">','<text x="20" y="30" font-size="22">Stage40 — repeated cells and native copper integration plan</text>','<text x="20" y="54" font-size="14">Candidate only; fixed jacks/foreign parts. Orange=front electronics, green=rear; diagram is not routing.</text>']
    for dx,left in [(0,30),(34,430)]:
        s=7;ox=7+dx;oy=118
        def rect(b,color,fill,dash=''):
            return f'<rect x="{left+(b[0]-ox)*s}" y="{100+(b[1]-oy)*s}" width="{(b[2]-b[0])*s}" height="{(b[3]-b[1])*s}" stroke="{color}" fill="{fill}" stroke-dasharray="{dash}"/>'
        out.append(f'<text x="{left}" y="82" font-size="18">{"B1" if dx==0 else "B2"}: exact34mm translation</text>')
        out.append(rect([7+dx,118,39+dx,164],'#777','none'))
        for row in d['obstacles']['B.Cu']:
            if ':courtyard' in row['id'] and g.ov(row['box'],[7+dx,118,39+dx,164]):out.append(rect(row['box'],'#b44','#eedddd','3 2'))
        for r,q in d['candidate_B1'].items():
            b=g.shift(q['box'],dx);color='#a65c1d' if q['side']=='front' else '#28705c';out.append(rect(b,color,'none' if q['panel'] else '#f1cfac' if q['side']=='front' else '#b7ddc8','3 2' if q['panel'] else ''))
            out.append(f'<text x="{left+(b[0]-ox)*s}" y="{98+(b[1]-oy)*s}" font-size="9">{r if dx==0 else q["B2_ref"]}</text>')
    b=d['metrics']['stage39'];c=d['metrics']['candidate'];p=d['preservation']
    lines=[f"Bypass rail-pad sum: {b['sum_bypass_distances_mm']:.2f} → {c['sum_bypass_distances_mm']:.2f} mm",f"Feedback MST proxy sum: {b['sum_feedback_mst_proxy_mm']:.2f} → {c['sum_feedback_mst_proxy_mm']:.2f} mm",'Distance proxies; native comparisons in JSON.',f"{len(d['moves'])} package moves/face decisions; fixed hardware preserved.",f"{p['private_retirement_count']} private-net copper objects proposed for reroute.",f"{len(d['shared_old_pad_contact_review'])} shared old-pad contact candidates: REVIEW.",f"{len(d['preserved_new_pad_clearance_review'])} preserved copper/new-pad candidates: REVIEW.",f"{p['filled_copper_zone_count']} copper-zone definitions preserved; refill required.",f"{p['all_rule_areas_preserve_count']} rule areas preserved; duplicate UUIDs retained."]
    for i,t in enumerate(lines):out.append(f'<text x="760" y="{112+i*28}" font-size="13">{t}</text>')
    bottom=['Native board contains fixed connectors/test points missing from Stage39 report-only placement screen.', 'All-rear bounded repacks failed; this explicit mixed-face candidate keeps amplifier and feedback parts together front.', 'Private nets are classified from every native footprint pad owner, not opaque native net names.', 'Shared rails/AGND and foreign copper are never bulk-deleted. Exact object occurrence+hash lists drive later review.', 'Next: native disposable candidate, one complete cell/loop pilot; baseline ratsnest, pad parity, DRC, zones and foreign connectivity.', 'No canonical PCB or copper changed. Native feasibility, return loops, optics, physical fit and protection remain unresolved.']
    for i,t in enumerate(bottom):out.append(f'<text x="20" y="{490+i*32}" font-size="15">{t}</text>')
    return '\n'.join(out+['</g></svg>'])+'\n'
if __name__=='__main__':
    d=build();(HERE/'plan.json').write_text(json.dumps(d,indent=2)+'\n');(HERE/'plan.svg').write_text(svg(d));print(json.dumps({'native':d['native_board']['counts'],'preservation':d['preservation'],'metrics':{k:{x:v[x] for x in ('sum_bypass_distances_mm','sum_feedback_mst_proxy_mm')} for k,v in d['metrics'].items() if k!='current_native'},'shared':len(d['shared_old_pad_contact_review']),'newpad':len(d['preserved_new_pad_clearance_review'])},indent=2))
