"""Independent packed native forest structural/Fraction/raw-ABI/lifetime oracle.

Synthetic only; no original-data access. Native binaries live in deleted temp dirs.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import sys
from pathlib import Path
import ctypes as C
import tempfile
import importlib.util
import itertools
import hashlib
import json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'fixture'))
import test_prototype as T
import native_forest as N
P,F,np=T.P,T.F,T.np
spec=importlib.util.spec_from_file_location('independent_forest_reference',HERE/'independent-forest-oracle.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)


class Stats(C.Structure):
    _fields_=[(k,C.c_uint64) for k in ('kernel_units','bit_work_envelope','limb_visits','initialized_words',
                 'copied_words_upper','floating_calls','peak_bits','scope_bits','proposed_contributions')]
IP=C.POINTER(C.c_int32);DP=C.POINTER(C.c_double);UP=C.POINTER(C.c_uint32)
class Board(C.Structure):
    _fields_=[('n',C.c_uint32),('nnz',C.c_uint32),('terminals',C.c_uint32),
              ('indptr',IP),('indices',IP),('columns',IP),('data',DP),('coupling',DP)]
class Result(C.Structure):
    _fields_=[(k,C.c_double) for k in ('bound','ground','radius','deficit','q','midpoint_bound','interval_radius','interval_q')]+[
        ('root',C.c_uint32),('edges',C.c_uint32),('index_visits',C.c_uint64*6),
        ('coefficient_reads',C.c_uint64*6),('row_visits',C.c_uint64),('phases',Stats*6)]+[(k,C.c_uint64) for k in ('scratch_live_bytes','scratch_peak_bytes','allocation_attempts','scratch_allocations','scratch_releases','selection_scratch_bytes','path_scratch_bytes')]


class Raw:
    def __init__(self,path):
        self.lib=C.CDLL(str(path));self.lib.e16_forest_result_size.restype=C.c_uint32
        assert self.lib.e16_forest_result_size()==C.sizeof(Result)
        self.fn=self.lib.e16_forest
        self.fn.argtypes=[C.c_uint32,C.POINTER(Board),C.c_uint32,DP,DP,DP,UP,DP,C.POINTER(Result)]
        self.fn.restype=C.c_int
    def call(self,blocks,intervals,mutate=None,count=None):
        m=len(intervals);n=sum(a.shape[0] for a,_,_ in blocks)+m
        boards=(Board*len(blocks))();owned=[]
        for k,(a,b,columns) in enumerate(blocks):
            columns=np.array(columns,dtype=np.int32);owned.append(columns)
            boards[k]=Board(a.shape[0],a.nnz,len(columns),a.indptr.ctypes.data_as(IP),a.indices.ctypes.data_as(IP),
                            columns.ctypes.data_as(IP),a.data.ctypes.data_as(DP),b.ctypes.data_as(DP))
        mid=np.array([[lo*.5+hi*.5 for lo,hi in row] for row in intervals],dtype=np.float64).reshape(m,m)
        lo=np.array([[x[0] for x in row] for row in intervals],dtype=np.float64).reshape(m,m)
        hi=np.array([[x[1] for x in row] for row in intervals],dtype=np.float64).reshape(m,m)
        if mutate:mutate(boards,mid,lo,hi)
        parent=(C.c_uint32*128)();edge=(C.c_double*128)();out=Result()
        code=self.fn(len(blocks) if count is None else count,boards,m,mid.ctypes.data_as(DP),lo.ctypes.data_as(DP),
                     hi.ctypes.data_as(DP),parent,edge,C.byref(out))
        assert out.scratch_live_bytes==0, 'scratch leaked on return'
        assert out.scratch_allocations==out.scratch_releases, 'allocation/release mismatch'
        if code==0:
            assert out.scratch_allocations==5 and out.allocation_attempts==5
            assert out.selection_scratch_bytes==8*n and out.path_scratch_bytes==13*n
            assert out.scratch_peak_bytes==13*n, 'selection and path arrays overlap'
        return code,out,list(parent)[:n],list(edge)[:n]


def structural(kernel,raw):
    def check(a):
        ref=R.reference(a);report=kernel.certify(a,{'independent':'native-forest'})
        assert report['status']=='CERTIFIED'
        bound=F(report['inverse_infinity_upper'])
        assert ref['bound']<=bound<=ref['bound']*F(1000000000001,1000000000000)
        assert bound>=ref['inverse_norm'] and report['root']==ref['root']
        code,out,parent,edge=raw.call([(a,np.empty((a.shape[0],0)),())],[])
        assert code==0 and out.row_visits==a.shape[0]
        selected={tuple(sorted((i,j))):c for i,j,c in ref['edges']}
        actual={tuple(sorted((i,parent[i]))):F(edge[i]) for i in range(len(parent)) if i!=out.root}
        assert actual==selected and parent[out.root]==out.root and edge[out.root]==0.
        for start in range(a.shape[0]):
            current=start;visited=set()
            while current!=out.root:
                assert current not in visited;visited.add(current);current=parent[current]
        return {'order':a.shape[0],'root':out.root,'exact_rmax':str(ref['rmax']),
                'bound':report['inverse_infinity_upper'],'exact_inverse_norm':float(ref['inverse_norm'])}
    R.check=check
    result=R.run()
    single=T.csr([[2.]])
    check(single)
    result['single_vertex_control']='PASS'
    return result


def coupled(kernel,raw):
    results=[]
    for name,kwargs in [('strong',{}),('weak',{'ground':2.**-30}),('nonsymmetric',{'nonsymmetric':True})]:
        blocks,d,exact=T.separated_fixture(**kwargs);mapped=[(a,b,(0,1)) for a,b in blocks]
        view=P.JoinedRows(mapped,d,P.Meter());report=kernel.certify(view,{'independent':name})
        assert report['status']=='CERTIFIED'
        bound=F(report['inverse_infinity_upper']);norm=max(sum(map(abs,r)) for r in T.exact_inverse_values(exact))
        assert bound>=norm
        for choices in itertools.product((0,1),repeat=4):
            corner=[row[:] for row in exact]
            for (i,j),side in zip(itertools.product(range(2),repeat=2),choices):corner[4+i][4+j]=F(d[i][j][side])
            assert bound>=max(sum(map(abs,r)) for r in T.exact_inverse_values(corner))
        code,out,_,_=raw.call(mapped,d);assert code==0 and F(out.bound)>=norm and out.row_visits==6
        results.append({'case':name,'bound':report['inverse_infinity_upper'],'exact_original_norm':float(norm)})
    return {'exact_full_operator_and_corner_checks':51,'cases':results,'status':'PASS'}


def shared_mapping(kernel,raw):
    a=T.csr([[3.,-1.],[-1.,3.]])
    blocks=[(a,np.array([[-.25],[0.]]),(1,)),(a.copy(),np.array([[-.5],[0.]]),(1,))]
    d=[[(1.,1.),(-.1,-.1)],[(-.1,-.1),(2.,2.)]]
    view=P.JoinedRows(blocks,d,P.Meter());report=kernel.certify(view,{})
    assert report['status']=='CERTIFIED'
    exact=[[F(0) for _ in range(6)] for _ in range(6)]
    for board,(aa,b,cols) in enumerate(blocks):
        for i in range(2):
            for j in range(2):exact[2*board+i][2*board+j]=F(float(aa[i,j]))
            exact[2*board+i][5]=exact[5][2*board+i]=F(float(b[i,0]))
    for i in range(2):
        for j in range(2):exact[4+i][4+j]=F(d[i][j][0])
    norm=max(sum(map(abs,row)) for row in T.exact_inverse_values(exact))
    assert F(report['inverse_infinity_upper'])>=norm
    code,out,_,_=raw.call(blocks,d);assert code==0 and F(out.bound)>=norm
    return {'shared_terminal':1,'unmapped_terminal':0,'exact_inverse_norm':float(norm),
            'bound':report['inverse_infinity_upper'],'status':'PASS'}


def malformed(raw):
    a=T.grid(4);blocks=[(a,np.empty((16,0)),())];refusals=[]
    mutations=[('order129',lambda b,m,l,h:setattr(b[0],'n',129)),
               ('nnz_overcap',lambda b,m,l,h:setattr(b[0],'nnz',16385)),
               ('terminals_mismatch',lambda b,m,l,h:setattr(b[0],'terminals',1)),
               ('null_indptr',lambda b,m,l,h:setattr(b[0],'indptr',None))]
    for name,change in mutations:
        code,_,_,_=raw.call(blocks,[],mutate=change);assert code!=0;refusals.append(name)
    code,_,_,_=raw.call(blocks,[],count=0);assert code!=0;refusals.append('zero_boards')
    for name,values in [('one_sided',[[2.,-1.],[0.,2.]]),('singular',[[1.,-1.],[-1.,1.]]),
                        ('disconnected',[[1.,0.],[0.,1.]]),('indefinite',[[3.,-1.],[-1.,.25]])]:
        matrix=T.csr(values);code,_,_,_=raw.call([(matrix,np.empty((2,0)),())],[])
        assert code!=0;refusals.append(name)
    b,d,_=T.separated_fixture();mapped=[(aa,bb,(0,1)) for aa,bb in b]
    for name,change in [('reversed_interval',lambda bs,m,l,h:l.__setitem__((0,0),h[0,0]+1.)),
                        ('nonfinite_interval',lambda bs,m,l,h:h.__setitem__((0,0),float('nan'))),
                        ('nonfinite_midpoint',lambda bs,m,l,h:m.__setitem__((0,0),float('inf')))]:
        code,_,_,_=raw.call(mapped,d,change);assert code!=0;refusals.append(name)
    return {'raw_refusals':refusals,'status':'PASS'}


def metadata_boundary(kernel):
    refusals=[]
    for mode in ('short_indptr','short_indices','short_data','int64_indices','noncontiguous_data'):
        a=T.grid(4)
        if mode=='short_indptr':a.indptr=a.indptr[:-1]
        elif mode=='short_indices':a.indices=a.indices[:-1]
        elif mode=='short_data':a.data=a.data[:-1]
        elif mode=='int64_indices':a.indices=a.indices.astype(np.int64)
        else:
            doubled=np.repeat(a.data,2);a.data=doubled[::2]
        original=kernel.lib.e16_forest
        def should_not_call(*args):raise AssertionError('malformed capacity reached native ABI')
        kernel.lib.e16_forest=should_not_call
        try:
            try:kernel.certify(a,{})
            except ValueError as exc:assert 'metadata' in str(exc);refusals.append(mode)
            else:raise AssertionError('bad metadata accepted')
        finally:kernel.lib.e16_forest=original
    blocks,d,_=T.separated_fixture();view=P.JoinedRows([(a,b,(0,1)) for a,b in blocks],d,P.Meter())
    view.intervals[0][0]=(np.longdouble(d[0][0][0]),np.longdouble(d[0][0][1]))
    try:kernel.certify(view,{})
    except ValueError as exc:assert 'metadata' in str(exc);refusals.append('extended_interval_no_silent_conversion')
    else:raise AssertionError('extended interval accepted')
    a=T.grid(4);a.data[0]=float('nan')
    report=kernel.certify(a,{})
    assert report['status']=='REFUSED' and report['native_code']==21
    return {'before_native_refusals':refusals,'native_owns_nonfinite_coefficient_refusal':True,'status':'PASS'}


def binding(kernel):
    outcomes=[]
    for mode in ('matrix','context','live_interval_replacement'):
        blocks,d,_=T.separated_fixture();view=P.JoinedRows([(a,b,(0,1)) for a,b in blocks],d,P.Meter())
        context={'binding':'original'};original=kernel.lib.e16_forest
        def altered(*args):
            result=original(*args)
            if mode=='matrix':blocks[0][0].data[0]+=.125
            elif mode=='context':context['binding']='changed'
            else:
                new=[row[:] for row in d];lo,hi=new[0][0];new[0][0]=(lo-.01,hi+.01);view.intervals=new
            return result
        kernel.lib.e16_forest=altered
        try:report=kernel.certify(view,context)
        finally:kernel.lib.e16_forest=original
        assert report['status']=='REFUSED' and 'changed during proof' in report['reason'];outcomes.append(mode)
    return {'persistent_mutation_refusals':outcomes,'status':'PASS'}


def allocation_failures(directory):
    rows=[]
    for failure in range(1,6):
        path,build=N.build(directory,fail_allocation=failure)
        raw=Raw(path);a=T.grid(4)
        code,out,_,_=raw.call([(a,np.empty((16,0)),())],[])
        assert code==11 and out.allocation_attempts==failure
        assert out.scratch_allocations==failure-1 and out.scratch_releases==failure-1
        if failure==2:assert out.index_visits[2]==16
        if failure==4:assert out.index_visits[3]>=16
        rows.append({'failure_position':failure,'code':code,'completed':out.scratch_allocations,
                     'released':out.scratch_releases,'live':out.scratch_live_bytes,'peak':out.scratch_peak_bytes})
    return rows


if __name__=='__main__':
    if '--ubsan' in sys.argv:N.FLAGS=[*N.FLAGS,'-fsanitize=undefined','-fno-sanitize-recover=all']
    with tempfile.TemporaryDirectory(prefix='e16-independent-native-forest-') as directory:
        path,build=N.build(directory);kernel=N.Kernel(path);raw=Raw(path)
        result={'synthetic_only':True,'lifetime_checks':'all raw returns: zero live payload and matched releases; successful calls: 5 allocations, selection 8N, path/peak 13N','build':build,'structural':structural(kernel,raw),
                'coupled':coupled(kernel,raw),'shared_mapping':shared_mapping(kernel,raw),'malformed':malformed(raw),'metadata_boundary':metadata_boundary(kernel),'binding':binding(kernel),
                'allocation_failures':allocation_failures(directory),'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [Path(__file__),HERE/'fixture/native_forest.cpp',HERE/'fixture/native_forest.py',HERE/'independent-forest-oracle.py']}}
        print(json.dumps(result,indent=2))
