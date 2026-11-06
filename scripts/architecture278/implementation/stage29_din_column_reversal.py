"""Unadopted DIN column-reversal source correction candidate; source only, no native/physical claims."""
import argparse
import copy
import datetime
import hashlib
import html
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import stage28_din_harness as s28

ROOT=Path(__file__).resolve().parents[3]
REL='design/architecture-278/implementation/'
OUT=ROOT/REL/'stage29'
BASE='0c1871791a866ba3de64472cac360b81f9cb90ab'
MUTABLE={REL+'README.md',REL+'WORK.md','scripts/architecture278/implementation/check_source.py'}
SCRIPTS={'scripts/architecture278/implementation/'+n for n in ('stage29_din_column_reversal.py','test_stage29_din_column_reversal.py')}
# PDF user space is 72 pt per inch; both title blocks state scale 1:1 on an A3 sheet.
PT_PER_MM=72/25.4
SIDES={'female':('middle','J17909','A01-middle'),'male':('rear','J17910','A01-core')}
CORNERS=('a1','c1','a32','c32')
# Viewer screen (right, down) from the locked frame: rear viewers along -z see x reversed, front viewers along +z do not.
COMPONENT_VIEW={'female':[[-1,0],[0,1]],'male':[[1,0],[0,1]]}
CROPS={'female-view-A-board-drillings':('female',(95,215,560,440)),'female-elevation-arrow-A':('female',(170,455,600,575)),
    'male-view-B-board-drillings':('male',(120,40,520,280)),'male-elevation-arrow-B':('male',(140,555,480,790))}
REGIONS={'female':(95,215,560,440),'male':(120,40,520,280)}
UNCONFIRMED=['meaning of Ø1±0.1 (finished plated vs drill) for this part','fixing-hole plating','fabricator hole size and Ø0.05 position capability',
    'board thickness','mating, seating and retention','soldering and assembly process']
need,read,dump,sha=s28.need,s28.read,s28.dump,s28.sha


def rev(p):return p[0]+str(33-int(p[1:]))
def det(m):return m[0][0]*m[1][1]-m[0][1]*m[1][0]
def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(2))+0.0 for j in range(2)] for i in range(2)]


def validate_sources(sources,cache=False):
    need(set(sources)=={'harting-female','harting-male'},'exact Stage29 receipt set')
    stage5=read(ROOT/REL/'stage5/din-evidence.json')['sources'];stage28=read(ROOT/REL/'stage28/sources.json')
    for i,sid in enumerate(('harting-female','harting-male')):
        s=sources[sid]
        need(s['authority']=='MANUFACTURER_PRIMARY' and s['url']==stage28[sid]['url'] and s['bytes']==stage28[sid]['bytes'],'receipt identity '+sid)
        need(s['sha256']==stage5[i]['sha256']==stage28[sid]['sha256'],'drawing bytes differ from Stage5/Stage28 receipts '+sid)
        stamp=datetime.datetime.fromisoformat(s['retrieved_UTC'])
        need(stamp.utcoffset()==datetime.timedelta(0) and stamp.date()==datetime.date(2026,10,17),'dated UTC retrieval '+sid)
        if cache:
            p=ROOT/s['raw_cache'];need(p.read_bytes().startswith(b'%PDF-') and p.stat().st_size==s['bytes'] and sha(p)==s['sha256'],'raw receipt drift '+sid)


def vector_grid(v,reading):
    """Vector contact centres (pt, y down) labelled by the read view -> drawing mm (X right, Y up) about the pattern centre."""
    xs,ys=v['columns_x_pt_left_to_right'],v['rows_y_pt_top_to_bottom']
    need(len(xs)==32 and len(ys)==3 and v['contact_count']==96 and len(v['contact_centres_pt'])==96,'complete 96-circle vector pattern')
    need({tuple(c) for c in v['contact_centres_pt']}=={(x,y) for x in xs for y in ys},'vector contacts off the read grid')
    need(all(abs((b-a)/PT_PER_MM-2.54)<1e-3 for seq in (xs,ys) for a,b in zip(seq,seq[1:])),'vector pitch is not 2.54 mm')
    need(abs(v['contact_diameter_pt']/PT_PER_MM-1)<1e-3,'vector contact hole is not Ø1')
    cols=list(range(reading['left_to_right'][0],reading['left_to_right'][1]-1,-1));need(cols==list(range(32,0,-1)),'read column order')
    cx,cy=(xs[0]+xs[-1])/2,ys[1]
    return {r+str(c):[(x-cx)/PT_PER_MM,-(y-cy)/PT_PER_MM] for r,y in zip(reading['top_to_bottom'],ys) for c,x in zip(cols,xs)},(cx,cy)


def drawing_facts(evidence,vector,reading,sources):
    need(reading['status']=='CONFIRMED_FROM_PRIMARY_DRAWING_SOURCE_REVIEW_ONLY','drawing reading status')
    drawings,out={},{}
    for s in SIDES:
        ev,rd,v=evidence['DIN'][s],reading[s],vector[s]
        need(v['source']=='harting-'+s and v['sha256']==sources['harting-'+s]['sha256'],'vector evidence source '+s)
        need((ev['view'],ev['left_to_right'],ev['top_to_bottom'])==(rd['view'],rd['left_to_right'],rd['top_to_bottom']),'drawing view reading differs from Stage22 evidence '+s)
        drawings[s]=s28.requirements.drawing_coordinates(ev)
        grid,(cx,cy)=vector_grid(v,rd)
        need(all(math.isclose(a,b,abs_tol=1e-3) for p in drawings[s] for a,b in zip(grid[p],drawings[s][p])),'vector drawing grid differs from the Stage22 view '+s)
        out[s]={'view':rd['view'],'left_to_right':rd['left_to_right'],'top_to_bottom':rd['top_to_bottom'],'arrow_side':rd['arrow_side'],
            'pattern_centre_pt':[round(cx,6),round(cy,6)],'pitch_from_vector_mm':round((v['columns_x_pt_left_to_right'][1]-v['columns_x_pt_left_to_right'][0])/PT_PER_MM,6)}
    f=vector['female']['other_circles'];_,(cx,cy)=vector_grid(vector['female'],reading['female'])
    need(len(f)==2 and all(abs(c['diameter_pt']/PT_PER_MM-2.8)<1e-2 for c in f),'female board drillings carry exactly two Ø2.8 fixing holes')
    holes=sorted([(c['centre_pt'][0]-cx)/PT_PER_MM,-(c['centre_pt'][1]-cy)/PT_PER_MM] for c in f)
    spacing=holes[1][0]-holes[0][0];offset=holes[0][1]
    need(abs(spacing-90)<1e-3 and abs(holes[0][0]+holes[1][0])<1e-3 and holes[0][1]==holes[1][1],'vector fixing holes not 90 mm apart and symmetric to the pattern')
    toward='a' if offset>0 and reading['female']['top_to_bottom'][0]=='a' else 'c'
    need(toward=='a' and abs(offset-.3)<1e-3,'female fixing-hole offset not toward row a')
    need(evidence['DIN']['female']['fixing_board_holes']['offset_from_row_b_toward_a_mm']==.3,'Stage22 fixing-hole offset side')
    need(vector['male']['other_circles']==[] and evidence['DIN']['male']['fixing_board_holes'] is None,'male board drillings carry only the 96 contact holes')
    out['female']['fixing_holes_drawing_mm']=[[round(a,6)+0.0 for a in h] for h in holes]
    out['female']['fixing_hole_spacing_from_vector_mm']=round(spacing,6)
    out['female']['fixing_hole_offset_from_vector_mm']=round(offset,6)
    out['female']['fixing_hole_offset_side']='row a'
    out['female']['fixing_hole_offset_note']='Vector geometry of the drawing, not a manufacturing tolerance; the toleranced value is 0,3±0,1 on the drawing'
    return drawings,out


def stage10_positions(mech):
    return {s:copy.deepcopy(mech['din_connectors'][side]['pads_xyz_mm']) for s,(side,_,_) in SIDES.items()}


def propose(stage10):
    """candidate_position(row, n) = Stage10_position(row, 33-n); the physical contact ID keeps its net."""
    return {s:{p:copy.deepcopy(pads[rev(p)]) for p in pads} for s,pads in stage10.items()}


def verify(candidate,stage10,drawings,facts,mech,nets,frozen):
    need(nets==frozen,'DIN net/NC assignment differs from the Stage28 ledger (mechanical renumbering or NC connection)')
    need(sum(1 for n in nets.values() if n)==16 and sum(1 for n in nets.values() if not n)==80,'16 assigned / 80 NC DIN contacts')
    fits={}
    for s,(side,ref,board) in SIDES.items():
        c,old=candidate[s],stage10[s]
        need(len(old)==96 and all(len(v)==1 for v in c.values()),'single pad per contact '+s)
        need(set(c)==set(old)==set(drawings[s]),'complete 96 physical contact IDs '+s)
        need({v[0][2] for v in c.values()}=={v[0][2] for v in old.values()}=={mech['din_connectors'][side]['mount_surface_z_mm']},'board plane '+s)
        xy={p:v[0][:2] for p,v in c.items()}
        need(len({tuple(v) for v in xy.values()})==96 and {tuple(v[0]) for v in c.values()}=={tuple(v[0]) for v in old.values()},'candidate is not a bijection onto the fixed Stage10 hole set '+s)
        m,t=s28.fit(drawings[s],xy)
        need(det(m)==facts[s]['expected_det'],'candidate handedness does not match drawing view '+s)
        if s=='female':
            holes=sorted((s28.apply(m,t,[x,.3]) for x in (-45,45)),key=lambda p:p[1])
            need(holes==sorted((h['point_mm'] for h in mech['DIN_flange_holes']),key=lambda p:p[1]),'female fixing holes moved')
        need(all(c[p]==old[rev(p)] for p in c),'candidate is not the column reversal of Stage10 '+s)
        fits[s]=(m,t)
    need(all(candidate['female'][p][0][:2]==candidate['male'][p][0][:2] for p in candidate['female']),'mated female/male physical contacts do not coincide')
    return fits


def component_view(s,m):
    """Drawing (X right, Y up) -> component-side viewer (right, up); a proper view is a pure rotation."""
    return mul([[1,0],[0,-1]],mul(COMPONENT_VIEW[s],m))


def build(data,cache=False,preserve=True):
    validate_sources(data['sources'],cache)
    for name in ('reading','sources'):s28.no_claims(data[name],name)
    facts=s28.frame_facts(data['lock'],data['mech'])
    drawings,dfacts=drawing_facts(data['evidence'],data['vector'],data['reading'],data['sources'])
    pinmap=data['interfaces']['DIN_pinmap']
    for s,(side,ref,_) in SIDES.items():
        need(data['inventory']['unbound'][ref]['pins']==pinmap==data['mech']['din_connectors'][side]['pins'],'DIN net/NC assignment drift '+ref)
    frozen={c['label']:c['net'] for c in data['ledger28']['din_contacts']}
    stage10=stage10_positions(data['mech'])
    old={s:s28.fit(drawings[s],{p:v[0][:2] for p,v in stage10[s].items()}) for s in SIDES}
    need(all(det(old[s][0])==-facts[s]['expected_det'] for s in SIDES),'Stage10 labels are no longer the recorded mirrored pair')
    candidate=data['candidate'] if 'candidate' in data else propose(stage10)
    fits=verify(candidate,stage10,drawings,facts,data['mech'],pinmap,frozen)
    rows=[]
    for s,(side,ref,board) in SIDES.items():
        attr=data['reading'][s]['contact_attribute']
        for p in sorted(candidate[s],key=lambda q:('abc'.index(q[0]),int(q[1:]))):
            rows.append({'connector':ref,'side':s,'board':board,'physical_contact':p,'net':pinmap[p],'nc':not pinmap[p],'contact_attribute':attr,
                'drawing_xy_mm':drawings[s][p],'stage10_xy_mm':stage10[s][p][0][:2],'candidate_xy_mm':candidate[s][p][0][:2],'z_mm':candidate[s][p][0][2],
                'stage10_label_at_candidate_xy':rev(p)})
    views={}
    for s in SIDES:
        a,b=component_view(s,old[s][0]),component_view(s,fits[s][0])
        views[s]={'stage10_drawing_to_component_view':a,'stage10_view_det':det(a),'candidate_drawing_to_component_view':b,'candidate_view_det':det(b)}
        need(det(b)==1 and det(a)==-1,'component-side view handedness '+s)
    corners={s:{p:{'stage10_xy_mm':stage10[s][p][0][:2],'candidate_xy_mm':candidate[s][p][0][:2]} for p in CORNERS} for s in SIDES}
    report={'status':'SOURCE_CORRECTION_CANDIDATE_NOT_ADOPTED','mapping':'candidate_position(row, n) = Stage10_position(row, 33-n)',
        'frame':facts,'drawings':dfacts,
        'matrices':{s:{'stage10':old[s][0],'stage10_det':det(old[s][0]),'candidate':fits[s][0],'candidate_det':det(fits[s][0]),'offset_mm':fits[s][1],
            'expected_det':facts[s]['expected_det']} for s in SIDES},
        'component_side_views':views,'corners':corners,'pin1_marker_xy_mm':{s:candidate[s]['a1'][0][:2] for s in SIDES},
        'fixing_holes_xy_mm':sorted((h['point_mm'] for h in data['mech']['DIN_flange_holes']),key=lambda p:p[1]),
        'counts':{'contacts_per_connector':96,'assigned':16,'NC':80,'moved_contacts_per_connector':sum(1 for p in candidate['female'] if candidate['female'][p]!=stage10['female'][p])},
        'rejected':{'row_reversal':'moves the female fixing holes 0.6 mm (Stage28 report din.candidates.row_reversal)','net_renumbering':'nets stay with physical contact IDs'},
        'decision_status':{'drawing_orientation_and_offset':'CONFIRMED_FROM_PRIMARY_DRAWING_SOURCE_REVIEW_ONLY','candidate':'PROPOSED_NOT_ADOPTED',
            'D02':'CONFLICT_REQUIRES_DECISION (Stage28 row unchanged)','M-01':'NOT_RUN','Q-O01':'OWNER_DECISION_OPEN','production_copper':'NOT_BOUND'},
        'unconfirmed':UNCONFIRMED,'native':'NOT_RUN','physical':'NOT_RUN','external_contact':'NONE','production_CAD_changed':False,'architecture_adopted':False,
        'preservation_baseline':protected() if preserve else None}
    files=[OUT/n for n in ('sources.json','drawing-reading.json','vector-evidence.json','README.md')]+[OUT/'evidence'/(n+'.png') for n in CROPS]
    files+=[ROOT/REL/p for p in ('stage22/evidence.json','stage10/mechanical-report.json','stage10/mechanical-input.json','stage15/interfaces-report.json',
        'stage21/inventory-input.json','stage5/din-evidence.json','stage28/harness-ledger.json','stage28/report.json','stage28/sources.json')]
    files+=[ROOT/'design/grid/placements.lock.json']+[Path(__file__).with_name(n) for n in ('test_stage29_din_column_reversal.py','stage28_din_harness.py','stage22_requirements.py','check_source.py')]+[Path(__file__)]
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    return {'status':'CONTACT_MAP_CANDIDATE_NOT_ADOPTED','mapping':report['mapping'],'contacts':rows},report


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<=MUTABLE,'historical/canonical protected bytes changed')
    new=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    new+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    need(all(p.startswith(REL+'stage29/') or p in SCRIPTS for p in new),'out-of-scope addition')
    return BASE


def load():
    return {'sources':read(OUT/'sources.json'),'reading':read(OUT/'drawing-reading.json'),'vector':read(OUT/'vector-evidence.json'),
        'evidence':read(ROOT/REL/'stage22/evidence.json'),'mech':read(ROOT/REL/'stage10/mechanical-report.json'),
        'interfaces':read(ROOT/REL/'stage15/interfaces-report.json'),'inventory':read(ROOT/REL/'stage21/inventory-input.json'),
        'lock':read(ROOT/'design/grid/placements.lock.json'),'ledger28':read(ROOT/REL/'stage28/harness-ledger.json')}


def esc(s):return html.escape(str(s),quote=True)


def render_map(cmap):
    out=['# Stage29 DIN contact map candidate (not adopted)','',
        'Mapping: `'+cmap['mapping']+'`. Nets stay with the physical contact ID; only the ID-to-position binding changes.',
        'Female and male physical contact p coincide in XY. Stage10 XY is historical, candidate XY is a proposal; z is the unchanged board plane.','']
    for ref in ('J17909','J17910'):
        rows=[r for r in cmap['contacts'] if r['connector']==ref]
        out+=['## '+ref+' ('+rows[0]['side']+', '+rows[0]['board']+', z='+str(rows[0]['z_mm'])+' mm)','','Contact attribute: '+rows[0]['contact_attribute']+'.','',
            '| Physical contact | Net | Stage10 XY (mm) | Candidate XY (mm) | Stage10 label at candidate XY |','|---|---|---|---|---|']
        out+=[f"| {r['physical_contact']} | {r['net'] or 'NC'} | {r['stage10_xy_mm'][0]}, {r['stage10_xy_mm'][1]} | {r['candidate_xy_mm'][0]}, {r['candidate_xy_mm'][1]} | {r['stage10_label_at_candidate_xy']} |" for r in rows]
        out.append('')
    return '\n'.join(out)


def render_svg(cmap,report):
    k,top,pw=6.0,70,250
    rows=[r for r in cmap['contacts'] if r['side']=='female']
    ys=[r['candidate_xy_mm'][1] for r in rows];y0=min(ys)-12
    holes=report['fixing_holes_xy_mm']
    panels=[('Panel front view (locked frame)','+x right, +y down; J17909 and J17910 coincide',lambda x:x,'female'),
        ('J17909 female, component side','seen from the rear along -z (x reversed)',lambda x:-x,'female'),
        ('J17910 male, component side','seen from the front along +z',lambda x:x,'male')]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{pw*3+40}" height="{top+int((max(ys)-y0+12)*k)+150}" font-family="sans-serif" font-size="11">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        f'<text x="20" y="22" font-size="14" font-weight="bold">Stage29 DIN column-reversal candidate: NOT ADOPTED, physical M-01 NOT RUN</text>',
        f'<text x="20" y="40">{esc(report["mapping"])}; black = candidate physical contact, grey = historical Stage10 label; triangle = candidate pin 1 (a1)</text>']
    for i,(title,sub,fx,s) in enumerate(panels):
        ox=20+i*pw;cx=ox+pw/2
        xs=[fx(r['candidate_xy_mm'][0]) for r in rows];mx=(max(xs)+min(xs))/2
        X=lambda x:round(cx+(fx(x)-mx)*k,2);Y=lambda y:round(top+(y-y0)*k,2)
        out+=[f'<text x="{ox}" y="{top-12}" font-weight="bold">{esc(title)}</text>',f'<text x="{ox}" y="{top}">{esc(sub)}</text>']
        for r in rows:out.append(f'<circle cx="{X(r["candidate_xy_mm"][0])}" cy="{Y(r["candidate_xy_mm"][1])+12}" r="{0.5*k}" fill="none" stroke="#000" stroke-width="0.8"/>')
        if s=='female':
            for h in holes:out.append(f'<circle cx="{X(h[0])}" cy="{Y(h[1])+12}" r="{1.4*k}" fill="none" stroke="#06c" stroke-width="1"/>')
        else:out.append(f'<text x="{ox}" y="{Y(holes[0][1])+16}">no board fixing holes (Ø2.55 is a body flange)</text>')
        for p,c in report['corners'][s].items():
            x,y=c['candidate_xy_mm'];sx=X(x);sy=Y(y)+12;right=fx(x)>=mx
            tx=sx+(14 if right else -14);anchor='start' if right else 'end'
            out.append(f'<text x="{tx}" y="{sy+4}" text-anchor="{anchor}" font-weight="bold">{p}</text>')
            out.append(f'<text x="{tx+(26 if right else -26)}" y="{sy+4}" text-anchor="{anchor}" fill="#888" font-style="italic">S10 {rev(p)}</text>')
        x,y=report['pin1_marker_xy_mm'][s];sx,sy=X(x),Y(y)+12;d=-1 if fx(x)<mx else 1
        out.append(f'<polygon points="{sx+d*5},{sy} {sx+d*12},{sy-5} {sx+d*12},{sy+5}" fill="#c00"/>')
        v=report['component_side_views'].get(s) if i else None
        foot='drawing-to-view det: n/a (panel frame)' if not v else f'drawing-to-view det: candidate {v["candidate_view_det"]:+.0f}, Stage10 {v["stage10_view_det"]:+.0f}'
        out.append(f'<text x="{ox}" y="{Y(max(ys)+12)+40}">{esc(foot)}</text>')
        if v:
            r=v['candidate_drawing_to_component_view'];turn=round(math.degrees(math.atan2(r[1][0],r[0][0])))
            out.append(f'<text x="{ox}" y="{Y(max(ys)+12)+54}">= drawing view {report["drawings"][s]["view"]} turned {turn:+d}° (CCW +)</text>')
    out.append(f'<text x="20" y="{Y(max(ys)+12)+70}">Blue: female fixing holes (unchanged, offset 0.3 toward row a). Rows: a at x={report["corners"]["female"]["a1"]["candidate_xy_mm"][0]}, c at x={report["corners"]["female"]["c1"]["candidate_xy_mm"][0]} (panel frame).</text>')
    out.append(f'<text x="20" y="{Y(max(ys)+12)+88}">Source candidate only; not bound to board copper. D02 stays CONFLICT_REQUIRES_DECISION until M-01 and owner decision Q-O01.</text>')
    out.append('</svg>')
    return '\n'.join(out)+'\n'


def outputs(cmap,report):
    return {'contact-map.json':dump(cmap),'contact-map.md':render_map(cmap),'report.json':dump(report),'orientation.svg':render_svg(cmap,report)}


def check_outputs(bodies):
    for name,body in bodies.items():need((OUT/name).read_text()==body,'deterministic drift '+name)


def extract_vector(check):
    import fitz
    sources=read(OUT/'sources.json');ev={'tool':'PyMuPDF '+fitz.VersionBind+' Page.get_drawings(); circle = path with >=4 Bezier segments and a square bbox; centre = bbox centre',
        'units':'PDF points, origin top-left, y down; 72 pt = 25.4 mm at drawing scale 1:1','status':'VECTOR_EXTRACTION_NOT_A_TOLERANCE'}
    images={}
    for s in SIDES:
        p=ROOT/sources['harting-'+s]['raw_cache'];page=fitz.open(p)[0];reg=REGIONS[s];found=[]
        for d in page.get_drawings():
            r=d['rect']
            if sum(1 for it in d['items'] if it[0]=='c')>=4 and abs(r.width-r.height)<.05 and r.width>1:
                x,y=round((r.x0+r.x1)/2,6),round((r.y0+r.y1)/2,6)
                if reg[0]<=x<=reg[2] and reg[1]<=y<=reg[3]:found.append((round(r.width,3),x,y))
        small=sorted((x,y) for w,x,y in found if w<3)
        ev[s]={'source':'harting-'+s,'sha256':sha(p),'region_pt':list(reg),'contact_count':len(small),'contact_diameter_pt':sorted({w for w,_,_ in found if w<3})[0],
            'columns_x_pt_left_to_right':sorted({x for x,_ in small}),'rows_y_pt_top_to_bottom':sorted({y for _,y in small}),'contact_centres_pt':[list(c) for c in small],
            'other_circles':[{'diameter_pt':w,'centre_pt':[x,y]} for w,x,y in sorted(found) if w>=3]}
    for name,(s,reg) in CROPS.items():
        page=fitz.open(ROOT/sources['harting-'+s]['raw_cache'])[0]
        images[name]=page.get_pixmap(dpi=220,clip=fitz.Rect(*reg),colorspace=fitz.csGRAY).tobytes('png')
    if check:
        need((OUT/'vector-evidence.json').read_text()==dump(ev),'vector evidence drift')
        for n,b in images.items():need((OUT/'evidence'/(n+'.png')).read_bytes()==b,'evidence crop drift '+n)
    else:
        (OUT/'vector-evidence.json').write_text(dump(ev))
        for n,b in images.items():(OUT/'evidence'/(n+'.png')).write_bytes(b)


def history():
    protected()
    with tempfile.TemporaryDirectory(prefix='osc-stage29-history-') as tmp:
        checkout=Path(tmp)/'repo'
        subprocess.run(['git','worktree','add','--detach',str(checkout),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            subprocess.run([sys.executable,'scripts/architecture278/implementation/check_source.py'],cwd=checkout,check=True)
            for flags in ([],['-O']):
                subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage28_din_harness.py'],cwd=checkout,check=True)
        finally:subprocess.run(['git','worktree','remove','--force',str(checkout)],cwd=ROOT,check=True)
    print('PASS immutable Stage28 source checkpoint including historical checks')


def review():
    r=read(OUT/'independent-review.json');need(r['status']=='PASS_SOURCE_REVIEW_ONLY','independent source review')
    required=set(read(OUT/'report.json')['source_sha256'])|{REL+'stage29/'+n for n in ('report.json','contact-map.json','contact-map.md','orientation.svg')}
    need(required<=set(r['reviewed_sha256']),'complete review bindings')
    for path,value in r['reviewed_sha256'].items():need(sha(ROOT/path)==value,'review drift '+path)


def main():
    p=argparse.ArgumentParser()
    for flag in ('check','check-cache','check-history','check-review','extract-vector','check-vector'):p.add_argument('--'+flag,action='store_true')
    a=p.parse_args()
    if a.extract_vector or a.check_vector:extract_vector(a.check_vector)
    if a.check_history:history()
    cmap,report=build(load(),a.check_cache);bodies=outputs(cmap,report)
    if a.check:check_outputs(bodies)
    else:
        for name,body in bodies.items():(OUT/name).write_text(body)
    if a.check_review:review()
    print(f"PASS Stage29 source checks: 2x96 DIN contacts column-reversal candidate, dets female {report['matrices']['female']['candidate_det']:+.0f} / male {report['matrices']['male']['candidate_det']:+.0f}; NOT ADOPTED; M-01/native NOT RUN")


if __name__=='__main__':main()
