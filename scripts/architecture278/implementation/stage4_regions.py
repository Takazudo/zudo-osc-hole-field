"""Necessary octile domains, not sufficient physical/routed feasibility. No native calls."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'design/architecture-278/implementation'
K=math.sqrt(2)-1
NORMALS=sorted(set((sx*a,sy*b) for a,b in ((1,K),(K,1)) for sx in (-1,1) for sy in (-1,1)))

def octile(a,b):
    x,y=abs(a[0]-b[0]),abs(a[1]-b[1])
    return max(x,y)+K*min(x,y)

def signature(r):
    return (r['instance'],r['net'],r['front_endpoint'],r['other_endpoint'],r.get('link'),r.get('link_pin'))

def budget(row):
    """Return fixed budget, copper segment count, and fixed anchor. OCT has no DIN."""
    s=row['segments'];octave=row['net'].startswith('OSC_OCT')
    if row['length_limit_mm']!=300 or row['capacitance_limit_pF']!=1000:raise ValueError('changed signal limits')
    if 'link' in row:
        if s['wire_max_mm']!=63 or s['GH_pair_mm']!=15:raise ValueError('changed wire/GH allowance')
        fixed=s['front_trace_mm']+63+15+(0 if octave else 25)
        anchor=row['middle_header_pad_mm']
    else:
        fixed=25;anchor=row['front_pad_mm']
    if s['DIN_mm']!=(0 if octave else 25):raise ValueError('changed DIN allowance')
    return fixed,1 if octave else 2,anchor

def endpoint_domain(row,connector=None):
    """Necessary domain of other_pad. With fixed connector, exact scalar path domain.

    Without connector, O(q-anchor)<=R follows O(a-d)+O(d-q)>=O(a-q).
    A surviving point is NOT a placed connector, common pin assignment or route.
    """
    fixed,n,anchor=budget(row);radius=(300-fixed-7*n)/1.15
    if connector is not None and n==2:
        radius-=octile(anchor,connector);anchor=connector
    return {'centre_mm':anchor,'octile_radius_mm':radius,'fixed_allowance_mm':fixed,'copper_segment_count':n,
            'halfplanes':[[x,y,radius+x*anchor[0]+y*anchor[1]] for x,y in NORMALS]}

def clip(poly,h):
    if not poly:return []
    x,y,c=h;result=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da=x*a[0]+y*a[1]-c;db=x*b[0]+y*b[1]-c
        if da<=1e-9:result.append(a)
        if (da<=0)!=(db<=0):
            t=da/(da-db);result.append([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])])
    return result

def polygon(halfplanes):
    if not halfplanes:return None
    # First eight halfplanes define one complete bounded octagon; no arbitrary box.
    first=halfplanes[:8];points=[]
    for a,b in itertools.combinations(first,2):
        det=a[0]*b[1]-a[1]*b[0]
        if abs(det)<1e-12:continue
        q=[(a[2]*b[1]-a[1]*b[2])/det,(a[0]*b[2]-a[2]*b[0])/det]
        if all(h[0]*q[0]+h[1]*q[1]<=h[2]+1e-8 for h in first):
            if not any(math.dist(p,q)<1e-8 for p in points):points.append(q)
    if not points:return []
    cx=sum(p[0] for p in points)/len(points);cy=sum(p[1] for p in points)/len(points)
    points.sort(key=lambda p:math.atan2(p[1]-cy,p[0]-cx))
    for h in halfplanes[8:]:points=clip(points,h)
    return points

def translation_domain(rows,moving='rear',connector_by_instance=None):
    """Intersect necessary domains for a rigid translation of supplied endpoint rows.

    moving='shared': OCT other pads and reference front source pads translate together;
    all other endpoints/connectors stay fixed. Rear mode translates all other pads.
    connector_by_instance, when given, maps instance -> net -> actual DIN XY.
    """
    if moving not in ('rear','shared'):raise ValueError('unknown moving group')
    constraints=[]
    for row in rows:
        octave=row['net'].startswith('OSC_OCT')
        connector=None if connector_by_instance is None else connector_by_instance[row['instance']].get(row['net'])
        domain=endpoint_domain(row,connector);centre=domain['centre_mm'];q=row['other_pad_mm'];radius=domain['octile_radius_mm']
        if moving=='shared' and not octave:
            if 'link' in row:raise ValueError('not a shared source row')
            # O(source+t - rear)<=R, or O(source+t - DIN)<=R-O(DIN-rear).
            source=row['front_pad_mm'];centre=row['other_pad_mm'];radius=(300-25-14)/1.15
            if connector is not None:centre=connector;radius-=octile(connector,row['other_pad_mm'])
            q=source
        h=[[x,y,radius+x*(centre[0]-q[0])+y*(centre[1]-q[1])] for x,y in NORMALS]
        constraints.append({'signature':list(signature(row)),'actual_identity':row['actual_identity'],'halfplanes_translation_mm':h})
    allh=[h for r in constraints for h in r['halfplanes_translation_mm']];poly=polygon(allh)
    witness=[]
    if poly==[]:
        # Inclusion-minimal ROW witness, not a claim of minimum cardinality.
        witness=list(range(len(constraints)))
        for i in list(witness):
            trial=[j for j in witness if j!=i]
            if trial and polygon([h for j in trial for h in constraints[j]['halfplanes_translation_mm']])==[]:witness=trial
    return {'moving':moving,'row_count':len(rows),'constraints':constraints,'translation_polygon_mm':poly,
            'necessary_domain_empty':poly==[],'conflict_row_indices':witness,
            'meaning':'empty rejects this fixed-orientation rigid group under stated fixed endpoints; nonempty is necessary only'}

def connector_translation_domain(rows,shared_translation=(6,0)):
    """Exact scalar-budget domain for one rigid DIN translation, fixed pads/pinmap.

    Each octile two-focus inequality is the intersection of64 linear halfplanes.
    Eight redundant single-focus halfplanes provide a bounded polygon seed.
    """
    constraints=[]
    for row in rows:
        fixed,n,anchor=budget(row)
        if n!=2:raise ValueError('DIN domain excludes offcard OCT')
        if 'link' not in row:anchor=[anchor[i]+shared_translation[i] for i in (0,1)]
        d=row['DIN_pad_mm'];q=row['other_pad_mm'];radius=(300-fixed-14)/1.15
        h=[[nx,ny,radius-nx*(d[0]-anchor[0])-ny*(d[1]-anchor[1])] for nx,ny in NORMALS]
        for nx,ny in NORMALS:
            for mx,my in NORMALS:
                h.append([nx+mx,ny+my,radius-nx*(d[0]-anchor[0])-ny*(d[1]-anchor[1])-mx*(d[0]-q[0])-my*(d[1]-q[1])])
        constraints.append({'signature':list(signature(row)),'actual_identity':row['actual_identity'],'halfplanes_translation_mm':h})
    poly=polygon([h for c in constraints for h in c['halfplanes_translation_mm']]);witness=[]
    if poly==[]:
        witness=list(range(len(constraints)))
        for i in list(witness):
            trial=[j for j in witness if j!=i]
            if trial and polygon([h for j in trial for h in constraints[j]['halfplanes_translation_mm']])==[]:witness=trial
    nearest=None
    if poly:
        allh=[h for c in constraints for h in c['halfplanes_translation_mm']]
        if all(h[2]>=-1e-9 for h in allh):nearest=[0,0]
        else:
            choices=list(poly)
            for a,b in zip(poly,poly[1:]+poly[:1]):
                dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
                t=max(0,min(1,-(a[0]*dx+a[1]*dy)/den)) if den else 0
                choices.append([a[0]+t*dx,a[1]+t*dy])
            nearest=min(choices,key=lambda q:q[0]**2+q[1]**2)
    return {'row_count':len(rows),'shared_translation_mm':list(shared_translation),'constraints':constraints,'translation_polygon_mm':poly,'domain_empty':poly==[],
            'conflict_row_indices':witness,'bounds_mm':None if not poly else [min(p[0] for p in poly),min(p[1] for p in poly),max(p[0] for p in poly),max(p[1] for p in poly)],
            'closest_translation_mm':nearest,'meaning':'exact continuous scalar allocation domain for fixed rear pads and common pin map; mechanical space, returns and capacitance unqualified'}

def validate_rows(rows):
    source=json.loads((OUT/'direct-study-report.json').read_text())['best']['paths']
    expected={signature(r):r for r in source}
    if len(rows)!=225 or {signature(r) for r in rows}!=set(expected):raise ValueError('exact225 crossing signatures required')
    for row in rows:
        old=expected[signature(row)]
        if row['actual_identity']!=old['actual_identity']:raise ValueError('changed actual identity or UID')
        for field in ('front_pad_mm','middle_header_pad_mm'):
            if row.get(field)!=old.get(field):raise ValueError('changed fixed front geometry')
        if row['segments'].get('front_trace_mm')!=old['segments'].get('front_trace_mm'):raise ValueError('changed front trace allowance')

def evaluate_paths(rows,other_pads,connector_pads,shared_translation=(0,0)):
    """Pure optimizer interface: mappings keyed by signature(row); exact budget unchanged.

    other_pads supplies ALL225 target pads; connector_pads supplies195 DIN contacts.
    shared_translation moves shared source pads; OCT other pads must already be moved.
    Returns lengths only: no contact injectivity, geometry, return or cap qualification.
    """
    if len(rows)!=225 or len({signature(r) for r in rows})!=225:raise ValueError('225 unique source rows required')
    validate_rows(rows)
    result=[]
    for row in rows:
        key=signature(row);fixed,n,anchor=budget(row);q=other_pads[key]
        if 'link' not in row:anchor=[anchor[i]+shared_translation[i] for i in (0,1)]
        length=fixed+7*n
        length+=1.15*octile(anchor,q) if n==1 else 1.15*(octile(anchor,connector_pads[key])+octile(connector_pads[key],q))
        result.append({'signature':list(key),'total_mm':length,'margin_mm':300-length})
    return result

def build():
    direct=json.loads((OUT/'direct-study-report.json').read_text());refined=json.loads((OUT/'cluster-refinement-report.json').read_text());results={}
    for variant,best in direct['best_by_variant'].items():
        rows=best['paths'];assert len(rows)==225 and len({signature(r) for r in rows})==225
        byref={p['ref']:p['cluster'] for p in best['packages']};groups={}
        for r in rows:
            if r['net'].startswith('OSC_OCT'):continue
            group=r['instance']+'/'+byref[r['other_endpoint'].split(':')[0]];groups.setdefault(group,[]).append(r)
        shared=[r for r in rows if r['net'].startswith('OSC_OCT') or 'link' not in r]
        assert len(shared)==65
        connectors={i:{} for i in best['origins_mm']}
        for r in rows:
            if r['DIN_pad_mm'] is not None:connectors[r['instance']][r['net']]=r['DIN_pad_mm']
        evaluated=evaluate_paths(rows,{signature(r):r['other_pad_mm'] for r in rows},{signature(r):r['DIN_pad_mm'] for r in rows if r['DIN_pad_mm'] is not None})
        assert all(math.isclose(x['total_mm'],r['total_mm'],abs_tol=1e-8) for x,r in zip(evaluated,rows))
        moved_other={signature(r):([r['other_pad_mm'][0]+6,r['other_pad_mm'][1]] if r['net'].startswith('OSC_OCT') else r['other_pad_mm']) for r in rows}
        moved=evaluate_paths(rows,moved_other,{signature(r):r['DIN_pad_mm'] for r in rows if r['DIN_pad_mm'] is not None},(6,0))
        shared_keys={signature(r) for r in shared}
        shifted_shared=[x for x in moved if tuple(x['signature']) in shared_keys]
        results[variant]={'whole_DIN_translation_domains_shared_plus6':{i:connector_translation_domain([r for r in rows if r['instance']==i and not r['net'].startswith('OSC_OCT')]) for i in best['origins_mm']},'shared_translation_plus6_x_comparison':{'translation_mm':[6,0],'all65_shared_rows':shifted_shared,'shared_maximum_mm':max(x['total_mm'] for x in shifted_shared),'shared_over300_count':sum(x['total_mm']>300 for x in shifted_shared),'all225_maximum_mm':max(x['total_mm'] for x in moved),'all225_over300_count':sum(x['total_mm']>300 for x in moved),'capacitance_pF':None,'mechanical_status':'NOT QUALIFIED'},'endpoint_domains':[{'signature':list(signature(r)),'actual_identity':r['actual_identity'],**endpoint_domain(r)} for r in rows],
            'rigid_cluster_free_connector_domains':{k:translation_domain(v) for k,v in groups.items()},
            'rigid_cluster_fixed_connector_domains':{k:translation_domain(v,connector_by_instance=connectors) for k,v in groups.items()},
            'shared_30_package_rigid_translation_free_connector_domain':translation_domain(shared,'shared'),
            'shared_30_package_rigid_translation_fixed_connector_domain':translation_domain(shared,'shared',connectors),
            'current_max_mm':max(x['total_mm'] for x in evaluated)}
    regressions=[r for r in refined['local_net_span_comparison'] if r['change_mm']>1e-8]
    paths=[Path(__file__),Path(__file__).with_name('test_stage4_regions.py'),OUT/'direct-study-report.json',OUT/'cluster-refinement-report.json',OUT/'stage3-crossing-audit.json']
    return {'status':'HISTORICAL STRICT300 SENSITIVITY DOMAINS ONLY; requirements rationale under review; NOT ADOPTED; native NOT RUN','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'derivation':'O(dx,dy)=max(|dx|,|dy|)+(sqrt(2)-1)*min(|dx|,|dy|). Linked rear: O(anchor-DIN)+O(DIN-rear)<=(300-front-63-15-25-14)/1.15. Shared reference: same sum<=(300-25-14)/1.15. OCT: O(header-shared)<=(300-front-63-15-7)/1.15; no DIN. Triangle inequality gives necessary endpoint octagons. Each eight inequalities n dot translation <= radius+n dot(centre-originalpad) is explicit. Euclidean ellipses are a looser necessary comparison, not used to weaken octile budgets.',
            'variants':results,'shared_aggregate_capacitance':direct['best']['shared_aggregate_capacitance'],
            'locality_comparison':{'engineering_comparison_only_not_new_acceptance_requirements':True,'no_regression_definition':'Every rear nonrail net maximum pair span <= its baseline, every bypass supply-pad leg <= baseline and dedicated two-leg sum <= baseline. Simultaneous componentwise comparison; no scalar benefit offsets a worsening timing/feedback/reference metric. Rigid translation/rotation preserves within-cluster spans; intercluster spans still require recomputation.',
                'refined_nonrail_regressions':regressions,'refined_bypass_rail_regressions':refined['rail_leg_regressions'],'refined_bypass_dedicated_two_leg_regressions':refined['dedicated_two_leg_regressions']},
            'limit_classification':'300mm and1000pF are retained project acceptance/allocation rules here, not measured failure thresholds. A334mm model does not prove unsafe hardware; a300mm model does not guarantee safe or stable hardware. This study does not establish their original empirical rationale or waive them.',
            'limitations':['Domains omit bodies, common-contact injectivity, collisions, occupied volumes, power/return topology and routed capacitance.','Shared island has30 whole packages; this necessary translation domain checks65 electrical rows only, not whole-island mechanical clearance.','OCT source movement is included: its30 paths are recomputed, never silently left unchanged.','Separate cluster domains assume every other group fixed; they are not a certificate of simultaneous joint feasibility.','All nine aggregate shared capacitances remain unextracted; 1000pF direct budget unchanged, receiver dynamics separate.']}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();r=build();p=OUT/'stage4-regions-report.json';data=json.dumps(r,sort_keys=True,separators=(',',':'))+'\n'
    if args.check:
        if p.read_text()!=data:raise ValueError('stale stage4 regions')
    else:p.write_text(data)
    for name,v in r['variants'].items():
        print(name,'empty free/fixed cluster domains',sum(x['necessary_domain_empty'] for x in v['rigid_cluster_free_connector_domains'].values()),sum(x['necessary_domain_empty'] for x in v['rigid_cluster_fixed_connector_domains'].values()),'shared free/fixed',v['shared_30_package_rigid_translation_free_connector_domain']['necessary_domain_empty'],v['shared_30_package_rigid_translation_fixed_connector_domain']['necessary_domain_empty'])
if __name__=='__main__':main()
