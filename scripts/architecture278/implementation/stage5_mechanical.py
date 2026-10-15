"""Independent official drill-envelope and whole-header source screen. No native execution."""
import argparse,hashlib,json,math,itertools
from pathlib import Path
from stage3_direct_mechanical import shift
from stage4_mechanical import tail_circle_overlap
from stage3_reservations import overlap
import stage5_rebudget
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'design/architecture-278/implementation/stage5'
def contact_envelopes(candidate,evidence):
    assert candidate['connector_turn_deg']==180,'unsupported DIN viewing/rotation datum'
    def bounds(key):
        lo,hi=evidence[key]
        assert all(math.isfinite(v) for v in (lo,hi)) and 0<=lo<=hi,'invalid dimension '+key
        return lo,hi
    contact_diameter=bounds('contact_drill_diameter_mm')[1]
    position=evidence['contact_true_position_diameter_mm']
    assert math.isfinite(position) and position>=0,'invalid contact positional tolerance'
    contact_radius=(contact_diameter+position)/2
    spacing=bounds('female_flange_spacing_mm');span=sum(spacing)/2
    offset=bounds('female_row_b_flange_axis_offset_mm')[1]
    flange_radius=bounds('female_flange_hole_diameter_mm')[1]/2+math.hypot(offset,(spacing[1]-spacing[0])/4)
    contacts=[]
    for inst,(ox,oy) in candidate['origins_mm'].items():
        cx,cy=candidate['connector_centre_mm']
        for row,xoff in zip('abc',(-2.54,0,2.54)):
            for n in range(1,33):
                x,y=-xoff,39.37-(n-1)*2.54
                contacts.append((ox+cx+x,oy+cy+y,contact_radius,inst+':'+row+str(n)))
        # Symmetric offset uncertainty avoids inventing a signed flange datum.
        for sign in [-1,1]:
            contacts.append((ox+cx,oy+cy+sign*span/2,flange_radius,inst+':flange'+str(sign)))
    return contacts

def build():
    names=['design/architecture-278/implementation/assembly-report.json','design/architecture-278/implementation/stage4/candidate-report.json','design/architecture-278/implementation/stage5/header-repair-input.json','design/architecture-278/implementation/stage5/din-evidence.json','scripts/architecture278/implementation/front_evidence.py','design/architecture-278/implementation/stage5/candidate-report.json']
    raw={n:(ROOT/n).read_bytes()for n in names};a,prior,spec,evidence=[json.loads(raw[n])for n in names[:4]]
    c,rebudget=stage5_rebudget.apply_moves(prior['candidate'],a,spec)
    assert c==json.loads(raw[names[5]])['candidate'],'rebudget report source mismatch'
    headers=[dict(p,id=p['instance']+':'+p['ref'])for p in c['middle_header_placements_all_instances']]
    contacts=contact_envelopes(c,evidence)
    def hits(h,dx=0,dy=0):
     out=[]
     for pin,points in h['pads_mm'].items():
      w,t=(1.1,2.9)if pin.startswith('MP')else(.65,1.7)
      for x,y in points:
       # conservative0.05 coordinate margin for GH nominal pitch dimension.
       b=[x+dx-w/2-.05,y+dy-t/2-.05,x+dx+w/2+.05,y+dy+t/2+.05]
       for px,py,r,ref in contacts:
        if tail_circle_overlap(px,py,b,r):out.append([ref,pin])
     return out
    findings=[{'header':h['id'],'hits':hits(h)}for h in headers if hits(h)]
    body_pairs=[{'a':p['id'],'b':q['id']}for p,q in itertools.combinations(headers,2)if overlap(p['box_mm'],q['box_mm'])]
    courtyard=[{'header':h['id'],'DIN':ref}for h in headers for x,y,r,ref in contacts if tail_circle_overlap(x,y,h['box_mm'],r)]
    shared=json.loads((ROOT/'design/architecture-278/implementation/stage4/occupied-report.json').read_text())
    shared=[p['new_candidate_placement']|{'ref':p['ref']}for p in shared['rows']if p['population_group']=='OCTAVE_REF']
    shared_holes=[{'ref':p['ref'],'DIN':ref}for p in shared for x,y,r,ref in contacts if tail_circle_overlap(x,y,p['box_mm'],r)]
    hashes={n:hashlib.sha256(b).hexdigest()for n,b in raw.items()}
    for p in [Path(__file__),*[Path(__file__).with_name(n) for n in ['stage5_rebudget.py','stage4_mechanical.py','stage3_reservations.py','stage3_direct_mechanical.py']],ROOT/'design/architecture-278/implementation/stage4/occupied-report.json']:hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return {'status':'CANDIDATE SOURCE REPAIR; NO PHYSICAL ACCEPTANCE','source_sha256':hashes,'moves':spec['moves'],'header_count':len(headers),'contact_hole_count':480,'flange_hole_count':10,'drill_envelope_land_exclusions':findings,'same_face_header_courtyard_conflicts':body_pairs,'shared_rear_courtyard_hole_conflicts':shared_holes,'opposite_face_GH_courtyard_hole_projections_UNKNOWN':courtyard,'rebudget':rebudget,'maximum_path_mm':c['maximum_mm'],'overlength_count':c['overlength_count'],'derived_envelope_radii_mm':{'contact':contacts[0][2],'flange':contacts[96][2]},'envelope_interpretation':'Contact radius derives from half maximum drill diameter plus half positional-tolerance diameter. Female flange radius derives from half maximum hole diameter plus symmetric offset/spacing uncertainty. GH maximum land dimensions plus0.05 source-coordinate allowance. Conditional drawing-to-board datum; no annular pads specified. Positive overlap rejects screen; absence is not full solid clearance.','service':'Two grips/frame/withdrawal and all438 hardware Z remain Stage4 conditional; hole/copper repair cannot close force, finger Z, fastener, body-tail or other-function reservation blockers.','native':'NOT RUN','physical':'NOT RUN'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();data=json.dumps(r,indent=2,sort_keys=True)+'\n';p=OUT/'mechanical-report.json'
    if args.check:assert p.read_text()==data,'stale stage5 mechanical screen'
    else:p.write_text(data)
    print({k:len(r[k])for k in ['drill_envelope_land_exclusions','same_face_header_courtyard_conflicts','shared_rear_courtyard_hole_conflicts','opposite_face_GH_courtyard_hole_projections_UNKNOWN']})
if __name__=='__main__':main()
