#!/usr/bin/env python3
"""Design-only deterministic courtyard population; no KiCad or route qualification."""
import argparse, copy, hashlib, html, json, math, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'design/architecture-278'
def read(p): return json.loads((ROOT/p).read_text())
def digest(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def sexpr(text):
    tokens=iter(re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',text))
    def node():
        out=[]
        for t in tokens:
            if t=='(': out.append(node())
            elif t==')': return out
            else: out.append(t.strip('"'))
        return out
    return node()[0]
def field(n,k): return next((a[1:] for a in n if isinstance(a,list) and a[0]==k),None)
def courtyard(path):
    root=sexpr((ROOT/path).read_text()); pts=[]
    for n in root:
        if isinstance(n,list) and n[0] in ('fp_line','fp_rect') and field(n,'layer')==['F.CrtYd']:
            pts.extend([list(map(float,field(n,k))) for k in ('start','end')])
    if not pts: raise ValueError(f'missing source courtyard {path}')
    return [min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]
def overlap(a,b,clearance=0):
    return a[0]<b[2]+clearance and b[0]<a[2]+clearance and a[1]<b[3]+clearance and b[1]<a[3]+clearance

def build(cfg=None):
    c=copy.deepcopy(cfg or read('design/architecture-278/revision-mechanical-input.json'))
    def finite(v,key):
        if isinstance(v,dict):
            for k,a in v.items(): finite(a,key+'.'+k)
        elif isinstance(v,list):
            for a in v:finite(a,key)
        elif isinstance(v,(int,float)) and (isinstance(v,bool) or not math.isfinite(v) or v<0):raise ValueError(key)
    finite(c,'config')
    if c['panel_mm']!=[318,298]:raise ValueError('fixed panel dimensions')
    def numbers(v,count,label):
        if not isinstance(v,list) or len(v)!=count or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in v):raise ValueError('numeric shape '+label)
    numbers(c['tile_mm'],2,'tile')
    if min(c['tile_mm'])<=0:raise ValueError('positive tile dimensions')
    for name,origin in c['origins_mm'].items():numbers(origin,2,'origin '+name)
    for label,box in [('connector',c['connector_box_mm']),('placement',c['placement_region_mm'])]+[('power',v) for v in c['power_boxes_mm']]:
        numbers(box,4,label)
        if box[2]<=box[0] or box[3]<=box[1]:raise ValueError('ordered positive rectangle '+label)
    for key,count in [('support_centres_mm',4),('guide_centres_mm',2),('probe_centres_mm',4),('pull_handle_centres_mm',2),('trim_centres_mm',6),('power_boxes_mm',4)]:
        if len(c[key])!=count:raise ValueError('incomplete '+key)
        if len({tuple(v) for v in c[key]})!=count:raise ValueError('duplicate '+key)
        if any(len(v)!=(4 if key=='power_boxes_mm' else 2) for v in c[key]):raise ValueError('shape '+key)
    if set(c['origins_mm'])!={'O1','O2','O3','O4','O5'}:raise ValueError('five oscillator cards required')
    if set(c['receiver_centres_mm'])!={'R1119','R1125','R1129','R1131','R1133'}:raise ValueError('five wiper receivers required')
    for key in ['tool_diameter_mm','probe_diameter_mm','support_radius_mm','guide_radius_mm','rear_component_height_bound_mm','withdrawal_mm','handle_projection_mm','handle_finger_diameter_mm','power_driver_diameter_mm','retention_driver_diameter_mm','package_clearance_mm']:
        if c[key]<=0:raise ValueError('positive '+key)
    if c['tool_diameter_mm']<1.7:raise ValueError('tool smaller than manufacturer cross tip')
    if c['trim_adjustment_degrees']!=[250,290]:raise ValueError('manufacturer trim sweep must be retained')
    if c['withdrawal_mm']<c['core_depth_mm']-c['middle_depth_mm']:raise ValueError('withdrawal does not clear stack')
    if c['guide_centres_mm'][0][1]==c['guide_centres_mm'][1][1]:raise ValueError('asymmetric guide key required')
    contract=read('design/architecture-278/interface-contract.json'); lock=read('design/grid/placements.lock.json'); old=read('design/architecture-278/mechanical-report.json')
    hashes={p:digest(p) for p in ['design/architecture-278/interface-contract.json','design/grid/placements.lock.json','design/architecture-278/revision-mechanical-input.json','scripts/architecture278/populated_mechanics.py','design/architecture-278/mechanical-report.json']}
    if len(lock['placements'])!=438:raise ValueError('locked panel count')
    packages={p['ref']:p for p in contract['parts'] if p['instance']=='O1' and p['footprint']}
    core={k:p for k,p in packages.items() if p['proposed_owner']=='rear-core'}
    cluster_expected={'U1110'}|{f'RB{i}' for i in range(1110,1118)}|{f'C{i}' for i in range(1115,1119)}
    cluster_expected|={p['ref'] for p in contract['parts'] if p['instance']=='O1' and p['attributes'].get('Decouples')=='PACK_OPA4197IPWR_1'}
    if set(c['reference_cluster_centres_mm'])!=cluster_expected:raise ValueError('complete reference package, four feedback loops and decouplers required')
    special={**c['receiver_centres_mm'],**c['reference_cluster_centres_mm']}
    for ref,coords in special.items():numbers(coords,2,'special component '+ref)
    trims={p['ref']:p for p in contract['trims']}
    placed=[]
    for ref,p in core.items():
        path='footprints/kicad/zudo-osc-hole-field.pretty/'+p['footprint'].split(':')[1]+'.kicad_mod'
        box=courtyard(path); hashes[path]=digest(path)
        placed.append({'ref':ref,'units':sorted({q['unit'] for q in contract['parts'] if q['ref']==ref}), 'footprint':p['footprint'],'mpn':p['attributes'].get('MPN',''),'role':p['attributes'].get('Role',''),'source_courtyard_mm':box,'source_path':path,'height_bound_mm':c['rear_component_height_bound_mm'],'height_evidence':c['height_status']})
    x0,y0,x1,y1=c['placement_region_mm']; x,y,rowh=x0,y0,0
    for p in sorted((p for p in placed if p['ref'] not in trims and p['ref'] not in special),key=lambda p:(-(p['source_courtyard_mm'][3]-p['source_courtyard_mm'][1]),p['ref'])):
        a,b,d,e=p['source_courtyard_mm'];w,h=d-a,e-b
        if x+w>x1: x=x0;y+=rowh+c['package_clearance_mm'];rowh=0
        if y+h>y1: raise ValueError('populated component capacity exceeded')
        p['box_mm']=[x,y,x+w,y+h];p['origin_mm']=[x-a,y-b];p['kind']='package';x+=w+c['package_clearance_mm'];rowh=max(rowh,h)
    for p in placed:
        if p['ref'] in special:
            cx,cy=special[p['ref']];a,b,d,e=p['source_courtyard_mm'];p['origin_mm']=[cx,cy];p['box_mm']=[cx+a,cy+b,cx+d,cy+e];p['kind']='package'
        if p['ref'] in trims:
            i=list(trims).index(p['ref']);cx,cy=c['trim_centres_mm'][i];a,b,d,e=p['source_courtyard_mm']
            p['height_bound_mm']=1.5;p['height_evidence']='Bourns TC33 p1 physical0:1.2±0.3mm; HF TC33X-2-203E candidate only';p['origin_mm']=[cx,cy];p['box_mm']=[cx+a,cy+b,cx+d,cy+e];p['kind']='trim';p['tool_axis_mm']=[cx,cy];p['tool_diameter_mm']=c['tool_diameter_mm'];p['adjustment_sweep_degrees']=c['trim_adjustment_degrees'];p['pins']=trims[p['ref']]['pins']
    fixed=[{'id':'DIN96','box_mm':c['connector_box_mm'],'kind':'connector'}, *[{'id':'power'+str(i+1),'box_mm':b,'kind':'power'} for i,b in enumerate(c['power_boxes_mm'])]]
    for kind,key,radius in [('support','support_centres_mm',c['support_radius_mm']),('guide','guide_centres_mm',c['guide_radius_mm']),('probe','probe_centres_mm',c['probe_diameter_mm']/2)]:
        for i,(x,y) in enumerate(c[key]): fixed.append({'id':f'{kind}{i+1}','kind':kind,'box_mm':[x-radius,y-radius,x+radius,y+radius]})
    # Probe pads attach only to existing rail/return and buffered output endpoints.
    for p,net in zip([v for v in fixed if v['kind']=='probe'],['AGND','+12V','-12V','/O1/TRI_SCALED']): p['net']=net
    conflicts=[];w,h=c['tile_mm'];t=c['tolerance_xy_mm']
    objects=[dict(p,id=p['ref']) for p in placed]+fixed
    for a in objects:
        b=a['box_mm']
        if b[0]<t or b[1]<t or b[2]>w-t or b[3]>h-t: conflicts.append('outside tile: '+a['id'])
    for i,a in enumerate(objects):
        for b in objects[i+1:]:
            if overlap(a['box_mm'],b['box_mm']): conflicts.append(a['id']+' overlaps '+b['id'])
    for support in [o for o in fixed if o['kind'] in ('support','probe','power')]:
        b=support['box_mm'];cx,cy=(b[0]+b[2])/2,(b[1]+b[3])/2
        diameter=c['power_driver_diameter_mm'] if support['kind']=='power' else c['retention_driver_diameter_mm'] if support['kind']=='support' else c['probe_diameter_mm']
        tool=[cx-diameter/2,cy-diameter/2,cx+diameter/2,cy+diameter/2];support['tool_corridor_mm']=tool
        for q in objects:
            if support['id']!=q['id'] and overlap(tool,q['box_mm']): conflicts.append('axial tool obstructed '+support['id']+' by '+q['id'])
    for p in (p for p in placed if p['kind']=='trim'):
        x,y=p['tool_axis_mm'];r=c['tool_diameter_mm']/2;tool=[x-r,y-r,x+r,y+r]
        for q in objects:
            if q['id']!=p['ref'] and overlap(tool,q['box_mm']): conflicts.append('trim tool '+p['ref']+' obstructed by '+q['id'])
    cards=[]
    for name,(x,y) in c['origins_mm'].items():
        box=[x,y,x+w,y+h];cards.append({'instance':name,'box_mm':box,'populated':name in ('O1','O2')})
        if x<t or y<t or x+w+t>c['panel_mm'][0] or y+h+t>c['panel_mm'][1]:conflicts.append(name+' outside panel')
    for i,a in enumerate(cards):
        for b in cards[i+1:]:
            if overlap(a['box_mm'],b['box_mm'],2*t): conflicts.append('neighbor tolerance collision '+a['instance']+'/'+b['instance'])
    if c['cover_depth_mm']-c['core_depth_mm']-c['handle_projection_mm']-c['relative_depth_tolerance_mm']<2:conflicts.append('cover/handle collision')
    if c['cover_depth_mm']-c['core_depth_mm']-c['rear_component_height_bound_mm']-c['relative_depth_tolerance_mm']<2:conflicts.append('cover/component collision')
    if c['external_workspace_mm']<c['withdrawal_mm']:conflicts.append('withdrawal workspace insufficient')
    stack=c['core_depth_mm']-c['middle_depth_mm']
    if stack-c['stack_tolerance_mm']<18.3 or stack+c['stack_tolerance_mm']>20:conflicts.append('DIN source stack outside18.3..20mm')
    # Rear handles need room above their own card, not fingers between adjacent cards.
    for x,y in c['pull_handle_centres_mm']:
        r=c['handle_finger_diameter_mm']/2
        if x-r<0 or x+r>w:conflicts.append('handle finger outside tile width')
        foot=[x-3,y-3,x+3,y+3]
        finger=[x-r,y-r,x+r,y+r]
        finger_bottom=c['handle_projection_mm']-r-c['relative_depth_tolerance_mm']
        for obj in objects:
            if overlap(foot,obj['box_mm']):conflicts.append('handle foot collision '+obj['id'])
            if overlap(finger,obj['box_mm']) and finger_bottom<=obj.get('height_bound_mm',c['rear_component_height_bound_mm']):conflicts.append('handle finger own collision '+obj['id'])
    sweep_checks=[]
    for card in cards:
        if not card['populated']:continue
        ox,oy=card['box_mm'][:2]
        for other in cards:
            if other['instance']==card['instance']:continue
            collision=overlap(card['box_mm'],other['box_mm'],2*t)
            if collision:conflicts.append('extraction sweep '+card['instance']+'/'+other['instance'])
            sweep_checks.append({'moving':card['instance'],'neighbor':other['instance'],'moving_depth_interval_mm':[c['core_depth_mm'],c['core_depth_mm']+c['withdrawal_mm']+c['rear_component_height_bound_mm']],'xy_overlap':collision})
            for x,y in c['pull_handle_centres_mm']:
                r=c['handle_finger_diameter_mm']/2;finger=[ox+x-r,oy+y-r,ox+x+r,oy+y+r]
                bottom=c['core_depth_mm']+c['handle_projection_mm']-r-c['relative_depth_tolerance_mm']
                if overlap(finger,other['box_mm'],t) and bottom<=c['core_depth_mm']+c['rear_component_height_bound_mm']:conflicts.append('handle finger neighbor collision '+card['instance']+'/'+other['instance'])
    axes=[]
    mappings={p['refs']['O1']:p['refs'] for p in contract['instance_mapping']}
    o2=[]
    for p in placed:
        q=copy.deepcopy(p);q['source_O1_ref']=p['ref'];q['ref']=mappings[p['ref']]['O2'];q['unit_mapping']=[{'O1_ref':p['ref'],'O2_ref':q['ref'],'unit':u} for u in p['units']];o2.append(q)
    for card in [x for x in cards if x['populated']]:
        ox,oy=card['box_mm'][:2]
        for p in placed:
            if p['kind']=='trim': axes.append({'instance':card['instance'],'ref':mappings[p['ref']][card['instance']],'axis_panel_mm':[ox+p['tool_axis_mm'][0],oy+p['tool_axis_mm'][1]],'approach':'from rear along negative depth direction; shaft rotates about axis','diameter_mm':c['tool_diameter_mm'],'pins_O1_basis':p['pins']})
    scope={'O1_physical_packages':len(packages),'rear_core':len(core),'front_jack':sum(p['proposed_owner']=='front-jack' for p in packages.values()),'front_control':sum(p['proposed_owner']=='front-control' for p in packages.values()),'octave_selector':sum(p['proposed_owner']=='octave-selector' for p in packages.values()),'nonphysical_declarations':[p['ref'] for p in contract['parts'] if p['instance']=='O1' and not p['footprint']], 'all_package_assignment':[{'ref':p['ref'],'owner':p['proposed_owner'],'footprint':p['footprint']} for p in packages.values()]}
    return {'schema_version':1,'status':'BOUNDED POPULATED COURTYARD CHECK ONLY; physical qualification NOT RUN','source_sha256':hashes,'config':c,'scope':scope,'O1_placements':sorted(placed,key=lambda p:p['ref']),'O2_placements':sorted(o2,key=lambda p:p['ref']),'extraction_sweep_checks':sweep_checks,'fixtures':fixed,'cards':cards,'trim_access':axes,'locked_panel_count':len(lock['placements']),'front_locked_O1_O2':[p for p in lock['placements'] if p.get('block') in ('O1','O2')],'front_source_envelopes':{'selector':old['selector_envelope'],'selector_planes':old['octave_instances'],'jack':read('design/mechanical/facts/jack.json')['grid_fit'],'pot':read('design/mechanical/facts/pot.json')['facts'],'scope':'Inherited body/courtyard envelopes and conditional datums; not revised front PCB packing'},'selector_to_middle_depth_clearance_mm':c['middle_depth_mm']-33-9-c['relative_depth_tolerance_mm'],'conflicts':conflicts,'minimum_cover_handle_gap_mm':c['cover_depth_mm']-c['core_depth_mm']-c['handle_projection_mm']-c['relative_depth_tolerance_mm'],'remaining_panel_projected_area_mm2':c['panel_mm'][0]*c['panel_mm'][1]-len(cards)*w*h,'limitations':['Shelf placement proves courtyard capacity and axial approach only; not routing, thermal, EMI or native solid fit.','All retained package heights use conservative5mm procurement bound except TC33 manufacturer1.5mm maximum; reconcile exact variants before PCB design.','Other28functions not populated; remaining projected area is fragmented and not an assertion of whole-instrument capacity.','Front-source package assignments conserved; redesigned front PCB copper/solids and seated datums still future one-zone work.','Support stiffness and connector alignment/proof load need prototype tests.']}

def drawing(r):
    c=r['config']; out=['<svg xmlns="http://www.w3.org/2000/svg" width="1260" height="900" viewBox="0 0 420 300">','<rect width="420" height="300" fill="white"/>','<g font-family="sans-serif" font-size="3" fill="#142c3a">','<text x="5" y="5">O1/O2 populated rear faces: proposed millimetres, not PCB routing or physical qualification</text>']
    def rect(box,fill,stroke='#718393',title=''):
        x,y,xx,yy=box;out.append(f'<rect x="{x}" y="{y+10}" width="{xx-x}" height="{yy-y}" fill="{fill}" stroke="{stroke}" stroke-width="0.3"><title>{html.escape(title)}</title></rect>')
    for card in r['cards']:
        rect(card['box_mm'],'#eaf2f5' if card['populated'] else '#f4f4f4');ox,oy=card['box_mm'][:2]
        if not card['populated']:
            out.append(f'<text x="{ox+10}" y="{oy+60}">{card["instance"]} reservation103x115</text>');continue
        for p in r['O1_placements']+r['fixtures']:
            b=p['box_mm'];box=[b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy];rect(box,'#b4d8b8' if p['kind'] in ('package','trim') else '#e4bf8b',title=p.get('ref',p.get('id','')))
            if p['kind']=='trim':
                x,y=p['tool_axis_mm'];out.append(f'<circle cx="{ox+x}" cy="{oy+y+10}" r="{c["tool_diameter_mm"]/2}" fill="none" stroke="#ba3424" stroke-width="0.4"/>')
        for x,y in c['pull_handle_centres_mm']:
            out.append(f'<circle cx="{ox+x}" cy="{oy+y+10}" r="{c["handle_finger_diameter_mm"]/2}" fill="none" stroke="#234cab" stroke-dasharray="1,1" stroke-width="0.4"/>')
        for fixture in r['fixtures']:
            if fixture['kind']=='power':
                b=fixture['tool_corridor_mm'];rect([b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy],'none','#782ca6','Power screw driver')
        out.append(f'<text x="{ox+10}" y="{oy+80.8}" font-size="2.5">{card["instance"]} 103x115</text>')
    out.append('<text x="329" y="16">Side section / depth mm</text>')
    for name,depth in [('Panel',0),('J / P conditional',11.8),('Octave rear',29),('Middle',c['middle_depth_mm']),('Core',c['core_depth_mm']),('Handle',c['core_depth_mm']+c['handle_projection_mm']),('Cover',c['cover_depth_mm'])]:
        yy=30+depth;out.append(f'<line x1="330" x2="410" y1="{yy}" y2="{yy}" stroke="#4c6476" stroke-width="0.4"/><text x="331" y="{yy-1}">{name} {depth:g}</text>')
    out.append(f'<rect x="350" y="{30+c["middle_depth_mm"]}" width="8" height="{c["core_depth_mm"]-c["middle_depth_mm"]}" fill="#e4bf8b"/>')
    out.extend(['<text x="5" y="253">Green: all154 source core packages per populated tile. Orange: DIN96, power, supports, guides, probes.</text>','<text x="5" y="259">Red: six rear axial calibration tool sweeps per oscillator. Grey O3–O5 are reservations, not placements.</text>',f'<text x="5" y="265">Side datums: panel0 / middle{c["middle_depth_mm"]} / core{c["core_depth_mm"]} / inner cover{c["cover_depth_mm"]}mm.</text>',f'<text x="5" y="271">DIN stack {c["core_depth_mm"]-c["middle_depth_mm"]:.1f}±{c["stack_tolerance_mm"]}mm; pull handles project{c["handle_projection_mm"]}mm; remove cover, withdraw{c["withdrawal_mm"]}mm.</text>','<text x="5" y="277">Front J/P and alternating octave boards retain locked panel centres; rear tile pitch is independent.</text>','<text x="5" y="283">Adjustment needs a1.7mm cross tip, not fingers between boards.100mm open rear work depth allocated.</text>','</g></svg>']);return '\n'.join(out)+'\n'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build()
    for path,data in [(D/'revision-mechanical-report.json',json.dumps(r,indent=2,sort_keys=True)+'\n'),(D/'revision-mechanical.svg',drawing(r))]:
        if args.check:
            if path.read_text()!=data:raise SystemExit('stale '+str(path))
        else:path.write_text(data)
    if r['conflicts']:raise SystemExit('\n'.join(r['conflicts']))
    print('PASS bounded154-package/O1+O2 courtyard and access arithmetic; physical qualification NOT RUN')
if __name__=='__main__':main()
