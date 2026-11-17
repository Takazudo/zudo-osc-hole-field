"""One original-F-face U4517 annulus, fixed U4527 probe and retained 45 R4577 offsets."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[4]
SPEC=Path(__file__).with_name('spec.json')
loader=importlib.util.spec_from_file_location('reviewed_e5_exchange',ROOT/'scripts/stack/studies/mc04_e5_exchange/study.py')
ex=importlib.util.module_from_spec(loader);loader.loader.exec_module(ex)
r1,sg,rp,lg=ex.r1,ex.sg,ex.rp,ex.lg
FACES={'U4527':'B','U4517':'F','R4577':'B'}
ANGLES={'U4527':180,'U4517':0,'R4577':90}
PAIR_CAP=56160


def fixed_hits(scene,body,dx=0,dy=0,excluded=None):
    keys=ex.KEYS if excluded is None else set(excluded)
    if keys!=ex.KEYS:raise ValueError('only the same exact three models may be excluded')
    if body['ref'] not in FACES or body['side']!=FACES[body['ref']] or body['angle']!=ANGLES[body['ref']]:
        raise ValueError('wrong original-face pilot identity/face')
    return scene._violations('K',body,dx,dy,keys)


def original_domain():
    return [(index,offset) for index,offset in enumerate(rp.ring_offsets(.25,24,25)) if 12<offset[0]<=25]


def original_candidates(scene,original,accepted_origin,probe,domain):
    if original['ref']!='U4517' or original['side']!='F' or original['angle']!=0:
        raise ValueError('actual original F/angle0 source geometry required')
    if len(domain)>1248:raise ValueError('original annulus enumeration cap exceeded')
    candidates,tests=[],[]
    previous=-1
    for index,(radius,dx,dy) in domain:
        if not 12<radius<=25 or index<=previous:raise ValueError('annulus radius/order changed')
        previous=index
        moved=ex.translate(original,dx,dy)
        from_current=[round(moved['origin'][i]-accepted_origin[i],4) for i in (0,1)]
        row={'original_ring_index':index,'radius_mm':radius,'shift_from_original_mm':[dx,dy],
             'shift_from_accepted_mm':from_current}
        if not ex.within25((dx,dy)) or not ex.within25(from_current):
            row['disposition']='FILTERED_DISPLACEMENT_BOUND'
        else:
            hits=fixed_hits(scene,original,dx,dy)
            if ex.mutual(moved,probe,scene.field.gap):hits=sorted(set(hits+['fixed U4527 probe']))
            row.update(blockers=hits,disposition='BLOCKED' if hits else 'INDIVIDUAL_ROOM_ONLY')
            if not hits:candidates.append({'offset_index':index,'geometry':moved})
        tests.append(row)
    return candidates,tests


def retained_resistor_candidates(scene,body,original_origin,probe,receipt,expected_rows):
    if receipt['status']!='NO_INDIVIDUAL_ROOM_FOR_EXCHANGE' or receipt['pair_checks']!=0:
        raise ValueError('wrong prior terminal receipt')
    rows=[row for row in receipt['individual_tests']['R4577'] if row['disposition']=='INDIVIDUAL_ROOM_ONLY']
    if rows!=expected_rows or len(rows)!=45 or len({row['offset_index'] for row in rows})!=45:
        raise ValueError('exact prior 45 resistor offsets changed')
    rings=rp.ring_offsets(.25,24,25)
    candidates=[]
    for row in rows:
        index=row['offset_index'];radius,dx,dy=rings[index]
        if radius!=row['radius_mm'] or [dx,dy]!=row['shift_from_accepted_mm'] or row['blockers']:
            raise ValueError('retained resistor ring correspondence changed')
        moved=ex.translate(body,dx,dy)
        cumulative=[round(moved['origin'][i]-original_origin[i],4) for i in (0,1)]
        if cumulative!=row['shift_from_original_mm'] or not ex.within25((dx,dy)) or not ex.within25(cumulative):
            raise ValueError('retained resistor displacement changed')
        if fixed_hits(scene,moved) or ex.mutual(moved,probe,scene.field.gap):
            raise ValueError('prior resistor room does not revalidate against frozen scene')
        candidates.append({'offset_index':index,'geometry':moved})
    if [row['offset_index'] for row in candidates]!=sorted(row['offset_index'] for row in candidates):
        raise ValueError('retained resistor order changed')
    return candidates


def validate_final(scene,bodies):
    if len(bodies)!=3 or {b['ref'] for b in bodies}!=set(FACES):raise ValueError('exact three final models required')
    for body in bodies:
        if fixed_hits(scene,body):raise ValueError('final body overlaps frozen scene')
    for i,a in enumerate(bodies):
        for b in bodies[i+1:]:
            if ex.mutual(a,b,scene.field.gap):raise ValueError('final model mutual collision')


def pair_search(scene,probe,left,right,cap=PAIR_CAP):
    if not 1<=cap<=PAIR_CAP or len(left)>1248 or len(right)>45:raise ValueError('pair domain/cap exceeded')
    count=0
    for a in left:
        for b in right:
            if count==cap:return {'status':'ORIGINAL_FACE_SEARCH_CAP_REACHED','pair_checks':count}
            count+=1
            if not ex.mutual(a['geometry'],b['geometry'],scene.field.gap):
                bodies=[probe,a['geometry'],b['geometry']]
                validate_final(scene,bodies)
                return {'status':'ORIGINAL_FACE_ROOM_WITNESS_ONLY','pair_checks':count,
                        'witness_ring_indices':[a['offset_index'],b['offset_index']], 'candidate_geometry':bodies}
    return {'status':'NO_ORIGINAL_FACE_PAIR_FIT','pair_checks':count}


def run(root=ROOT):
    spec=json.loads(SPEC.read_text());r1.verify_pins(root,spec)
    prior_spec=json.loads((root/'scripts/stack/studies/mc04_e5_exchange/spec.json').read_text())
    prior=json.loads((root/spec['prior_exchange_receipt']).read_text())
    if prior['inputs_sha256']!=prior_spec['sha256']:raise ValueError('prior exchange input closure mismatch')
    diagnostic=json.loads((root/prior_spec['diagnostic_receipt']).read_text());point=ex.validate_diagnostic(diagnostic)
    frozen=json.loads((root/'scripts/stack/studies/mc04_r1/spec.json').read_text())
    gate=json.loads((root/'design/stack/geometry/links/link-gate.json').read_text());rows=gate['replacement']['footprints']
    inp=lg.load_inputs(root)
    original=copy.deepcopy(next(f for f in inp['ci']['boards']['K'] if f['ref']=='U4517'))
    if original!=spec['original_U4517']:raise ValueError('actual original footprint geometry mismatch')
    by_ref={r['ref']:r for r in rows if r['board']=='K'}
    if by_ref['U4517']['face']!='F' or by_ref['U4517']['new_face']!='B' or by_ref['U4517']['step']!=2 or by_ref['U4517']['turned']:
        raise ValueError('original-face novelty premise changed')
    inp['ci']['boards'],accepted=r1.reconstruct(inp['ci']['boards'],rows,frozen['replacement'])
    unresolved={(r['board'],r['ref']) for r in rows if r['new'] is None}
    if len(accepted)!=412 or len(unresolved)!=26:raise ValueError('retained scene counts changed')
    model=lg.GateModel(inp,lg.gate_sites(inp));scene=r1.Scene(SimpleNamespace(model=model,opts=inp['opts']),inp,gate['links'])
    for ref,expected in prior_spec['geometry'].items():
        fp=scene.bodies['K',ref]
        if (fp['origin'],fp['side'],fp['angle'])!=(expected['current_origin'],expected['face'],expected['angle']):
            raise ValueError('accepted moving baseline geometry changed')
    companions={ref:scene.bodies['K',ref] for ref in prior_spec['frozen_geometry']}
    for ref,fp in companions.items():
        e=prior_spec['frozen_geometry'][ref]
        if (fp['origin'],fp['side'],fp['angle'])!=(e['origin'],e['face'],e['angle']):raise ValueError('frozen companion changed: '+ref)
    if any(p['type']!='smd' for fp in [original,scene.bodies['K','U4527'],scene.bodies['K','R4577']] for p in fp['pads']):
        raise ValueError('moving source SMD geometry assumption changed')
    fixed={(board,ref) for board,refs in model.panel.items() for ref in refs}
    fixed.update(key for key in scene.bodies if key[1] in {p['ref'] for p in inp['raw']['lock']['placements']})
    diag=ex.diag.DiagnosticScene(scene,accepted,unresolved,fixed)
    reproduced=diag.blockers('K',scene.bodies['K','U4527'],ex.POINT[2],ex.POINT[3])
    if reproduced!=point['blocker_ids'] or any(diag.registry[k]!=diagnostic['blockers'][k] for k in reproduced):
        raise ValueError('frozen U4527 diagnostic predicate mismatch')
    probe=ex.translate(scene.bodies['K','U4527'],ex.POINT[2],ex.POINT[3])
    if fixed_hits(scene,probe):raise ValueError('fixed probe fails against unchanged scene')
    logic=json.loads((root/prior_spec['logic_receipt']).read_text())
    interfaces=ex.ledger(json.loads((root/'design/reports/io-partition.json').read_text()),logic['external_contacts'],prior_spec['identities'])
    right=retained_resistor_candidates(scene,scene.bodies['K','R4577'],prior_spec['geometry']['R4577']['original_origin'],probe,prior,spec['retained_R4577_rows'])
    domain=original_domain()
    if len(domain)!=1248 or domain[0][0]!=1153 or domain[-1][0]!=2400:raise ValueError('annulus domain changed')
    left,tests=original_candidates(scene,original,prior_spec['geometry']['U4517']['current_origin'],probe,domain)
    result={'status':'NO_ORIGINAL_FACE_INDIVIDUAL_ROOM','pair_checks':0} if not left else pair_search(scene,probe,left,right)
    result.update({'source_commit':spec['source_commit'],'engineering_commit':spec['engineering_commit'],
        'inputs_sha256':spec['sha256'],'prior_exchange_receipt':spec['prior_exchange_receipt'],
        'original_U4517_geometry':original,'individual_tests':tests,'individual_room_count':len(left),
        'revalidated_R4577_count':len(right),'retained_R4577_ring_indices':[r['offset_index'] for r in right],
        'frozen_companion_geometry':companions,'interface_ledger':interfaces,
        'canonical_unresolved':26,'canonical_changes':[],'adopted_placements':[],
        'scope':'One original F/angle0 annulus hypothesis only; no rotation or B-to-F label flip. Same fixed U4527 point214 and prior45 R4577 offsets. Room-only necessary condition, not timing/analog/decoupling/routing/access acceptance, native, DRC/fill, adoption or manufacturing.'})
    r1.verify_pins(root,spec)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():parser.error('output already exists; no attempt consumed')
    if not args.output.resolve().is_relative_to((ROOT/'.circuit-cache').resolve()):parser.error('output must be inside ignored cache')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:
        try:result=run()
        except Exception as exc:
            json.dump({'status':'ADMISSION_OR_EXECUTION_FAILED','error':str(exc)},stream);stream.write('\n');raise
        json.dump(result,stream,indent=2);stream.write('\n')
    print(result['status'])
    return 0 if result['status'] in {'NO_ORIGINAL_FACE_INDIVIDUAL_ROOM','NO_ORIGINAL_FACE_PAIR_FIT','ORIGINAL_FACE_SEARCH_CAP_REACHED','ORIGINAL_FACE_ROOM_WITNESS_ONLY'} else 1


if __name__=='__main__':sys.exit(main())
