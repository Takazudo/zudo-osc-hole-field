"""Independent synthetic characterization formulas, lifetime and receipts.

Never opens retained originals; every input pickle is created in a temporary dir.
"""
import sys
from pathlib import Path
import tempfile
import pickle
import hashlib
import json
import weakref
import gc
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
BASE=next(p for p in HERE.parents if (p/'attribution_characterization.py').is_file())
sys.path.insert(0,str(BASE))
import attribution_characterization as C
from attribution_transport import Budget
from test_attribution_preallocation import descriptors


def binding(path,value):
    data=pickle.dumps(value);path.write_bytes(data)
    return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'decoded_limit':len(data),'decoded_sha256':hashlib.sha256(data).hexdigest(),
            'format':'pickle','gzip':False}


def expected(n,face,inner,sizes,taps):
    intervals=sum(max(t-1,0) for t in taps)
    k=face+inner+4*intervals;outer=sum(s*s for s in sizes);largest=max(s*s for s in sizes)
    raw=k+outer;t=len(sizes)
    return {'K_stored_upper':k,'termination_raw_triples':outer,'raw_coordinate_upper':raw,
            'largest_outer_entries':largest,'named_array_bytes':{
              'coordinate_conversion_arrays_upper':80*raw+8*(n+1),
              'active_outer_float_buffers_upper':16*largest,
              'dense_B_D_upper':8*n*t+8*t*t}}


def refs_of(op):
    objects=[]
    for name in ('Kg_face','Kg_inner'):
        csr=op[name];objects.extend([csr,csr.data,csr.indices,csr.indptr])
    for nodes,weights in op['supports'].values():objects.extend([nodes,weights])
    return [weakref.ref(x) for x in objects]


def success_and_formula():
    cases=[(7,9,4,(0,5,7),(0,1,4,2)),(1,2,0,(4001,0),())]
    results=[]
    with tempfile.TemporaryDirectory(prefix='e16-independent-characterization-') as tmp:
        root=Path(tmp);bindings={}
        for board,args in zip(('KA','KB'),cases):
            n,f,i,s,t=args;bindings[board]=binding(root/board,descriptors(n,f,i,s,t))
        references=[];real=C.decode;seen=[];budget=Budget();clock=(budget.started,budget.deadline)
        def observe(b,used_budget):
            assert used_budget is budget
            gc.collect();assert all(ref() is None for ref in references)
            op=real(b,used_budget);references.extend(refs_of(op));seen.append(b['sha256']);return op
        with patch.object(C,'decode',side_effect=observe):report=C.characterize(bindings,root/'output',budget)
        assert all(ref() is None for ref in references) and (budget.started,budget.deadline)==clock
        raw=(root/'output/components.jsonl').read_bytes()
        assert report['components_sha256']==hashlib.sha256(raw).hexdigest()
        rows=[json.loads(line) for line in raw.splitlines()]
        for board,row,args in zip(('KA','KB'),rows,cases):
            ex=expected(*args)
            for key,value in ex.items():assert row[key]==value
            assert row['named_array_bytes_upper']==sum(ex['named_array_bytes'].values())
            assert row['operator_binding_sha256']==hashlib.sha256(C.canonical(bindings[board])).hexdigest()
            assert row['full_pipeline_qualification']=='NOT_QUALIFIED'
            results.append({'board':board,'R':row['raw_coordinate_upper'],'largest_s_squared':row['largest_outer_entries'],
                            'outcome':row['raw_bound_outcome'],'named_arrays':row['named_array_bytes_upper']})
        assert report['status']=='COMPLETE' and report['electrical_acceptance'] is False
        assert report['summary']['full_pipeline_qualification']=='NOT_QUALIFIED'
        assert rows[1]['raw_bound_outcome']=='EXCEEDS_RAW_BOUND'
        assert report['summary']['metadata_checkpoints']==sum(r['metadata']['metadata_visits'] for r in rows)+4
        assert len(seen)==2
    # Huge metadata-only support descriptors do not allocate their numerical arrays.
    op=descriptors(n=16_000_000,face=16_000_000,inner=16_000_000,sizes=(16_000_000,)*8,taps=())
    metadata=C.G.extract_metadata(op,lambda:None);result=C.bounds(metadata)
    assert result['raw_coordinate_upper']==32_000_000+8*16_000_000**2
    assert result['raw_bound_outcome']=='EXCEEDS_RAW_BOUND' and len(C.canonical(result))<C.MAX_ROW_BYTES
    return {'two_board_formula_controls':results,'huge_descriptor_R':result['raw_coordinate_upper'],
            'serial_all_descriptor_weakrefs_released':True,'same_budget_clock':True,'receipt_binding':'PASS'}


def failures():
    outcomes=[]
    for mode in ('KB_bad_digest','source_changed','timeout_after_metadata'):
        with tempfile.TemporaryDirectory(prefix='e16-characterization-failure-') as tmp:
            root=Path(tmp);bindings={b:binding(root/b,descriptors()) for b in ('KA','KB')}
            budget=Budget();patcher=None
            if mode=='KB_bad_digest':bindings['KB']['sha256']='0'*64
            elif mode=='source_changed':
                real=C.source_identity;calls=[0]
                def altered(used_budget):
                    values=real(used_budget);calls[0]+=1
                    if calls[0]>1:values['attribution_characterization.py']='0'*64
                    return values
                patcher=patch.object(C,'source_identity',side_effect=altered)
            else:
                now=[0.];budget=Budget(seconds=1.,clock=lambda:now[0]);real=C.G.extract_metadata
                def elapsed(op,checkpoint):
                    result=real(op,checkpoint);now[0]=2.;return result
                patcher=patch.object(C.G,'extract_metadata',side_effect=elapsed)
            if patcher:patcher.start()
            try:
                try:C.characterize(bindings,root/'output',budget)
                except ValueError:pass
                else:raise AssertionError('failed characterization completed')
            finally:
                if patcher:patcher.stop()
            receipt=json.loads((root/'output/terminal.json').read_text())
            assert receipt['status']=='INCOMPLETE' and receipt['electrical_acceptance'] is False
            assert not (root/'output/components.jsonl').exists()
            partial=(root/'output/components.partial').read_bytes()
            assert receipt['partial_sha256']==hashlib.sha256(partial).hexdigest()
            outcomes.append({'case':mode,'component_rows':receipt['component_rows'],'status':receipt['status']})
    return outcomes


if __name__=='__main__':
    print(json.dumps({'synthetic_only':True,'success':success_and_formula(),'failures':failures(),
        'sha256':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in [Path(__file__),BASE/'attribution_characterization.py',BASE/'attribution_preallocation.py',BASE/'attribution_transport.py']}},indent=2))
