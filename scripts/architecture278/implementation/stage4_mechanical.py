"""Independent retained-coordinate, connector-land and two-grip screen."""
import argparse,collections,hashlib,itertools,json,math
from pathlib import Path
import stage3_reservations as reserve
from stage3_direct_mechanical import shift
ROOT=reserve.ROOT;OUT=ROOT/'design/architecture-278/implementation/stage4'
def tail_circle_overlap(x,y,b,radius=.145):
    return math.hypot(max(b[0]-x,0,x-b[2]),max(b[1]-y,0,y-b[3])) < radius
def build():
    names=['design/architecture-278/implementation/stage4/candidate-report.json','design/architecture-278/implementation/stage4/occupied-report.json','design/architecture-278/implementation/assembly-report.json','design/architecture-278/implementation/stage4/mechanical-input.json','scripts/architecture278/implementation/front_evidence.py','design/architecture-278/implementation/front-evidence.json']
    raw={n:(ROOT/n).read_bytes()for n in names};report,inventory,assembly,spec=[json.loads(raw[n])for n in names[:4]];c=report['candidate'];cards=c['geometry']['five_card_boxes_mm'];overlap=reserve.overlap
    retained=[p for p in inventory['rows']if p['historical_placement']['board']=='K'and p['population_group']!='OCTAVE_REF']
    projections=[{'ref':p['ref'],'function':p['function_or_service'],'side':p['historical_placement']['side'],'courtyard_mm':p['historical_placement']['courtyard_mm'],'cards':[k for k,b in cards.items()if overlap(p['historical_placement']['courtyard_mm'],b)]}for p in retained]
    hits=[p for p in projections if p['cards']]
    local=next(p['box_mm']for p in c['fixtures']if p['id']=='DIN');dins=[{'id':k,'box_mm':shift(local,*xy),'origin':xy}for k,xy in c['origins_mm'].items()]
    shared=[p['new_candidate_placement']|{'ref':p['ref']}for p in inventory['rows']if p['population_group']=='OCTAVE_REF']
    same=[{'DIN':d['id'],'shared':p['ref']}for d in dins for p in shared if overlap(d['box_mm'],p['box_mm'])]
    headers=[dict(p,id=f'O{i+1}:'+p['ref'],box_mm=shift(p['box_mm'],17*i),pads_mm={k:[[x+17*i,y]for x,y in v]for k,v in p['pads_mm'].items()})for i in range(5)for p in assembly['middle_header_placements']]
    lands=[]
    for h in headers:
        for pin,points in h['pads_mm'].items():
            # Exact source GH copper land dimensions; tails compared at nominal centers.
            w,t=(1,2.8)if pin.startswith('MP')else(.6,1.7)
            for x,y in points:lands.append({'header':h['id'],'pin':pin,'box_mm':[x-w/2,y-t/2,x+w/2,y+t/2]})
    contacts=[];landhits=[];courthits=[]
    for d in dins:
        ox,oy=d['origin'];cx,cy=c['connector_centre_mm']
        for row,xoff in zip('abc',(-2.54,0,2.54)):
            for n in range(1,33):
                x,y=xoff,-39.37+(n-1)*2.54
                for _ in range(c['connector_turn_deg']//90):x,y=-y,x
                x,y=ox+cx+x,oy+cy+y
                # Female minimum section .68 by .29; orientation unavailable.
                # Inscribed circle radius .145 is invariant to unknown axial rotation.
                key={'DIN':d['id'],'contact':row+str(n),'point_mm':[x,y]};contacts.append(key)
                for l in lands:
                    b=l['box_mm'];inside=b[0]<=x<=b[2]and b[1]<=y<=b[3]
                    if inside or tail_circle_overlap(x,y,b):landhits.append(key|{'GH':l['header'],'land':l['pin'],'land_box_mm':b,'center_inside':inside,'minimum_tail_inscribed_circle_overlap':tail_circle_overlap(x,y,b)})
                for h in headers:
                    b=h['box_mm']
                    if b[0]<x<b[2]and b[1]<y<b[3]:courthits.append(key|{'GH':h['id']})
    union=[min(p['box_mm'][i]for p in shared)if i<2 else max(p['box_mm'][i]for p in shared)for i in range(4)]
    grips=[{'id':h['id'],'center_mm':[(h['box_mm'][0]+h['box_mm'][2])/2,(h['box_mm'][1]+h['box_mm'][3])/2]}for h in c['fixtures']if h['id'].startswith('handle')]
    assert [g['center_mm']for g in grips]==[[11,234],[33,234]]
    hashes={n:hashlib.sha256(b).hexdigest()for n,b in raw.items()}
    hashes[str(Path(__file__).relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {'status':'SOURCE EXCLUSIONS AND CONDITIONAL SERVICE PROPOSAL; NOT PHYSICAL ACCEPTANCE','source_sha256':hashes,
      'retained_K_XY_interpretation':{'assumption':'Project exact historical other/POWER courtyards at candidate core plane. Conditional ownership exclusion only; historical XY is not an assigned new placement. No area-fit argument.','package_count':len(retained),'intersecting_unique_packages':len(hits),'by_function':dict(collections.Counter(p['function']for p in hits)),'by_card':{k:sum(k in p['cards']for p in hits)for k in cards},'multiple_card_packages':sum(len(p['cards'])>1 for p in hits),'all_K_bearing_other_functions':sorted({p['function_or_service']for p in retained if p['population_group']=='other28'}),'rows':projections},
      'shared_group':{'count':len(shared),'translation_mm':[6,0],'courtyard_union_mm':union,'same_face_DIN_conflicts':same,'nominal_bank_gap_clearance_mm':[union[0]-dins[1]['box_mm'][2],dins[2]['box_mm'][0]-union[2]],'qualification':'Package courtyards clear nominal DIN reservation. Carrier outline, flange holes, mounting, copper, tolerances, body heights and service remain UNKNOWN.'},
      'connector':{'DIN_contact_count':len(contacts),'middle_header_count':len(headers),'GH_land_count':len(lands),'nominal_contact_inside_GH_courtyard':courthits,'minimum_tail_or_center_GH_land_exclusions':landhits,'female_minimum_section_mm':[.68,.29],'female_maximum_section_mm':[.75,.31],'male_minimum_section_mm':[.575,.5],'male_maximum_section_mm':[.6,.55],'female_tail_mm':2.9,'male_tail_mm':3,'drill_mm':None,'pad_mm':None,'flange_hole_coordinates':None,'section_orientation':None,'land_tolerance_screen':'Nominal lands only; source width/pitch/hold-down tolerances not a clearance certification. Positive center or inscribed-circle overlap is an exclusion under nominal source datums, not a manufactured worst-case assertion. Absence of overlap is not acceptance.'},
      'service':{'grips':grips,'finger_diameter_mm':20,'same_card_finger_gap_mm':2,'card_edge_margin_mm':1,'adjacent_card_finger_gap_mm':4,'attachment_to_support_box_gap_mm':1.5,'finger_access_Z':'UNKNOWN; 18mm projection does not prove finger access or load-bearing strength','insertion_force_max_N':90,'withdrawal_force_max_N':60,'procedure':'Unpowered, cover removed, supported assembly; release power and retainers; simultaneous two-grip axial extraction through guides on retained rigid frame. Do not rock or pull one grip. Load split, frame strength, guide engagement and exact connector alignment require drawings/verification.','force_rating_scope':'Connector datasheet limits are not proof that handles, frame or guides can carry these forces.','withdrawal_mm':40,'external_workspace_mm':100},
      'blockers':['All 2572 other K packages plus13 POWER require explicit physical disposition; all4766 other package inventory retained, no new solids assigned. Interleaved functions cannot be silently moved or repartitioned within this bounded OSC task.','Physical old K retention conflicts with candidate extraction/cover. Canonical K files remain unchanged regardless of physical disposition.','Exact DIN flange/drill/pad/mating alignment drawing and supported frame/carrier/guide geometry missing. Other438 hardware full Z solids remain unresolved.'],
      'native':'NOT RUN','physical':'NOT RUN'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();r=build();s=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n';p=OUT/'mechanical-report.json'
    if a.check:assert p.read_text()==s,'stale stage4 mechanical report'
    else:p.write_text(s)
    print(json.dumps({'retained_XY_unique':r['retained_K_XY_interpretation']['intersecting_unique_packages'],'same_face_shared':len(r['shared_group']['same_face_DIN_conflicts']),'GH_land_exclusions':len(r['connector']['minimum_tail_or_center_GH_land_exclusions']),'GH_courtyard':len(r['connector']['nominal_contact_inside_GH_courtyard'])}))
if __name__=='__main__':main()
