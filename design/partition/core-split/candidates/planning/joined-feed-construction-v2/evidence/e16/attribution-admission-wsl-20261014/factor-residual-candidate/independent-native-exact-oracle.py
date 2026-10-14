"""Independent raw-ctypes/Fraction oracle for bounded native exact helpers.

No original-data reader or certificate entrypoint. Temporary binary is deleted.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import sys
from pathlib import Path
import ctypes as C
import tempfile
import random
import struct
import math
import hashlib
import json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'fixture'))
import test_prototype as T
import native_exact as Build
P,F=T.P,T.F


class D(C.Structure):
    _fields_=[('words',C.c_uint64*34),('used',C.c_uint32),('sign',C.c_int32),('exponent',C.c_int32)]
class Stats(C.Structure):
    _fields_=[(n,C.c_uint64) for n in ('kernel_units','bit_work_envelope','limb_visits','initialized_words','copied_words_upper','floating_calls','peak_bits','scope_bits','proposed_contributions')]


def raw(pair):
    m,e=pair;v=abs(m);out=D();out.sign=(m>0)-(m<0);out.exponent=e
    for i in range(34):out.words[i]=(v>>(64*i))&((1<<64)-1)
    out.used=(v.bit_length()+63)//64
    return out


def pair(value):
    assert value.used<=34
    m=sum(int(value.words[i])<<(64*i) for i in range(value.used))*value.sign
    return m,int(value.exponent)


def rational(value):
    m,e=value
    return F(m)*F(2)**e


class Oracle:
    def __init__(self,path):
        self.lib=C.CDLL(str(path));d=C.POINTER(D);s=C.POINTER(Stats)
        signatures={'e16_decode':[C.c_double,d,s],'e16_half':[C.c_double,C.c_double,d,s],
                    'e16_add':[d,d,d,s],'e16_compare':[d,d,C.POINTER(C.c_int32),s],
                    'e16_floor':[d,C.POINTER(C.c_double),s],
                    'e16_row_margin':[C.c_double,C.c_uint32,C.POINTER(C.c_double),C.POINTER(C.c_double),d,s]}
        for name,args in signatures.items():
            fn=getattr(self.lib,name);fn.argtypes=args;fn.restype=C.c_int
        assert self.lib.e16_dyadic_size()==C.sizeof(D) and self.lib.e16_stats_size()==C.sizeof(Stats)
    def decode(self,x,stats):
        out=D();status=self.lib.e16_decode(x,C.byref(out),C.byref(stats))
        assert status==0;return pair(out)
    def half(self,x,y,stats):
        out=D();status=self.lib.e16_half(x,y,C.byref(out),C.byref(stats))
        assert status==0;return pair(out)
    def add(self,a,b,stats):
        aa,bb,out=raw(a),raw(b),D()
        status=self.lib.e16_add(C.byref(aa),C.byref(bb),C.byref(out),C.byref(stats))
        return status,pair(out)
    def compare(self,a,b,stats):
        aa,bb,out=raw(a),raw(b),C.c_int32()
        status=self.lib.e16_compare(C.byref(aa),C.byref(bb),C.byref(out),C.byref(stats))
        assert status==0;return out.value
    def floor(self,a,stats):
        aa,out=raw(a),C.c_double()
        code=self.lib.e16_floor(C.byref(aa),C.byref(out),C.byref(stats))
        return code,out.value
    def row(self,d,a,b,stats):
        aa=(C.c_double*len(a))(*a);bb=(C.c_double*len(b))(*b);out=D()
        code=self.lib.e16_row_margin(d,len(a),aa,bb,C.byref(out),C.byref(stats))
        assert code==0;return pair(out)


def ieee_cases(kernel):
    rng=random.Random(286)
    values=[0.,-0.,5e-324,-5e-324,2.**-1022,math.nextafter(2.**-1022,0.),
            math.nextafter(math.inf,0.),-math.nextafter(math.inf,0.),1.,-1.]
    while len(values)<1000:
        v=struct.unpack('>d',rng.getrandbits(64).to_bytes(8,'big'))[0]
        if math.isfinite(v):values.append(v)
    for i,x in enumerate(values):
        y=values[-1-i];stats=Stats()
        assert rational(kernel.decode(x,stats))==F(x)
        h=kernel.half(x,y,stats)
        assert rational(h)==(F(x)+F(y))/2
        assert h==P.compact_half_sum(x,y,P.Meter())
    maximum=math.nextafter(math.inf,0.)
    assert rational(kernel.half(maximum,maximum,Stats()))==F(maximum)
    assert kernel.half(maximum,-maximum,Stats())==(0,0)
    return {'seed':286,'IEEE_decodes':1000,'exact_half_sums':1002,'status':'PASS'}


def carry_compare_floor(kernel):
    cases=[]
    for bits in (1,63,64,65,127,128,129,2174,2175):
        exponent=0 if bits<=2048 else -127
        cases.append((((1<<bits)-1,exponent),(1,exponent)))
        cases.append(((1,exponent+bits),(-((1<<bits)-1),exponent)))
    added=refused=0
    for a,b in cases:
        code,c=kernel.add(a,b,Stats())
        try:expected=P.compact_add(a,b,P.Meter())
        except ValueError:assert code!=0;refused+=1
        else:
            assert code==0 and c==expected and rational(c)==rational(a)+rational(b);added+=1
    # Explicit preallocation refusal at full width, despite eventual normalization.
    code,_=kernel.add(((1<<2176)-1,-128),(1,-128),Stats());assert code!=0;refused+=1
    rng=random.Random(287);pairs=[]
    for _ in range(500):
        width=rng.choice((1,53,64,65,128,511,1024,2175,2176))
        m=rng.getrandbits(width)|(1<<(width-1))|1
        if rng.randrange(2):m=-m
        pairs.append((m,rng.randint(-1075,2048)))
    comparisons=floors=floor_refusals=0
    for i,a in enumerate(pairs):
        b=pairs[-1-i];av,bv=rational(a),rational(b)
        assert kernel.compare(a,b,Stats())==(av>bv)-(av<bv);comparisons+=1
        assert kernel.compare(a,a,Stats())==0;comparisons+=1
        positive=(abs(a[0]),a[1]);code,result=kernel.floor(positive,Stats())
        try:py=P.compact_positive_floor(positive,P.Meter())
        except ValueError:assert code!=0;floor_refusals+=1
        else:assert code==0 and result==py and 0<F(result)<=abs(av);floors+=1
    for a in [(1,-1075),(3,-1075),(5,-1075),((1<<53)-1,971),((1<<54)-1,970),(1,2048)]:
        code,result=kernel.floor(a,Stats())
        if code==0:assert F(result)<=rational(a)
    return {'carry_borrow_successes':added,'width_refusals':refused,'exact_comparisons':comparisons,
            'accepted_floor_checks':floors,'floor_refusals':floor_refusals,'status':'PASS'}


def rows(kernel):
    rng=random.Random(288)
    for case in range(200):
        count=case%129
        a=[math.ldexp(float(rng.choice((-3,-1,1,3))),rng.randint(-1000,900)) for _ in range(count)]
        b=[math.ldexp(float(rng.choice((-3,-1,1,3))),rng.randint(-1000,900)) for _ in range(count)]
        diagonal=math.ldexp(3.,rng.randint(-1000,900))
        expected=F(diagonal)-sum(abs((F(x)+F(y))/2) for x,y in zip(a,b))
        result=kernel.row(diagonal,a,b,Stats())
        assert rational(result)==expected
    return {'seed':288,'exact_rows':200,'maximum_offdiagonal_terms':128,'status':'PASS'}


def malformed_and_caps(kernel):
    refusals=0
    for change in [lambda d:setattr(d,'used',35),lambda d:setattr(d,'sign',2),
                   lambda d:setattr(d,'sign',0),lambda d:setattr(d,'exponent',2049),
                   lambda d:setattr(d,'exponent',-1076),lambda d:d.words.__setitem__(0,2),
                   lambda d:d.words.__setitem__(0,0),lambda d:d.words.__setitem__(33,1)]:
        a=raw((1,0));change(a);b=raw((1,0));out=D();stats=Stats()
        code=kernel.lib.e16_add(C.byref(a),C.byref(b),C.byref(out),C.byref(stats))
        assert code!=0;refusals+=1
    for v in (math.inf,-math.inf,math.nan):
        out=D();stats=Stats();assert kernel.lib.e16_decode(v,C.byref(out),C.byref(stats))!=0;refusals+=1
    out=D();stats=Stats();stats.kernel_units=199999
    code=kernel.lib.e16_decode(1.,C.byref(out),C.byref(stats));assert code==3
    used=stats.kernel_units;assert used>200000
    assert kernel.lib.e16_decode(1.,C.byref(out),C.byref(stats))==3 and stats.kernel_units==used
    aa=(C.c_double*129)(*([1.]*129));stats=Stats()
    assert kernel.lib.e16_row_margin(1.,129,aa,aa,C.byref(out),C.byref(stats))==12
    assert kernel.lib.e16_decode(1.,C.byref(out),None)==10
    overflow_refusals=0
    for field,_ in Stats._fields_:
        s=Stats();setattr(s,field,(1<<64)-1)
        assert kernel.lib.e16_decode(1.,C.byref(out),C.byref(s))!=0
        assert getattr(s,field)==(1<<64)-1
        overflow_refusals+=1
    stats=Stats();kernel.row(1.,[2.**-100,0.],[2.**-100,0.],stats)
    assert stats.proposed_contributions==4
    return {'raw_struct_nonfinite_refusals':refusals,'preloaded_counter_overflow_refusals':overflow_refusals,
            'wide_zero_shortcut_retains_four_word_contributions':True,'cap_persists_after_failure':True,
            'row129_and_null_stats_refuse':True,'status':'PASS'}


if __name__=='__main__':
    if '--ubsan' in sys.argv:
        Build.FLAGS=[*Build.FLAGS,'-fsanitize=undefined','-fno-sanitize-recover=all']
    with tempfile.TemporaryDirectory(prefix='e16-independent-native-') as directory:
        library,build=Build.build(directory);kernel=Oracle(library)
        result={'synthetic_only':True,'build':build,'IEEE':ieee_cases(kernel),
                'wide_arithmetic':carry_compare_floor(kernel),'rows':rows(kernel),
                'malformed':malformed_and_caps(kernel),
                'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [Path(__file__),HERE/'fixture/native_exact.cpp',HERE/'fixture/native_exact.py']}}
        print(json.dumps(result,indent=2))
