"""Local synthetic C ABI for bounded exact arithmetic; no original-data reader."""
import ctypes as C
import hashlib
from pathlib import Path
import subprocess

FLAGS=['-std=c++20','-O2','-fno-fast-math','-frounding-math','-fPIC','-shared','-Wall','-Wextra','-Werror']
SOURCE=Path(__file__).with_suffix('.cpp')


class Dyadic(C.Structure):
    _fields_=[('word',C.c_uint64*34),('used',C.c_uint32),('sign',C.c_int32),('exponent',C.c_int32)]


class Stats(C.Structure):
    _fields_=[(name,C.c_uint64) for name in ['kernel_units','bit_work_envelope','limb_visits',
        'initialized_words','copied_words_upper','floating_calls','peak_bits','scope_bits','proposed_contributions']]
    def snapshot(self):
        out={name:int(getattr(self,name)) for name,_ in self._fields_}
        out['counter_semantics']='native bounded limb-kernel units and limb-width squared envelope; not Python whole-significand units or machine instructions'
        out['copy_scope']='conservative fixed-buffer copy-word envelope; compiler may elide copies'
        return out


def pair(value):
    m=sum(int(value.word[i])<<(64*i) for i in range(value.used))*value.sign
    return m,int(value.exponent)


def from_pair(value):
    if type(value) is not tuple or len(value)!=2 or any(type(v) is not int for v in value):raise ValueError('native dyadic tuple')
    m,e=value
    if m.bit_length()>2176 or not -1075<=e<=2048 or (m==0 and e!=0) or (m and not abs(m)&1):raise ValueError('native dyadic canonical range')
    result=Dyadic();result.sign=(m>0)-(m<0);result.exponent=e;v=abs(m)
    while v:
        result.word[result.used]=v&((1<<64)-1);result.used+=1;v>>=64
    return result


def build(directory):
    """Caller owns a fresh temporary directory and its eventual cleanup."""
    directory=Path(directory);target=directory/'native_exact.so'
    compiler=subprocess.run(['c++','--version'],check=True,text=True,capture_output=True).stdout.splitlines()[0]
    subprocess.run(['c++',*FLAGS,str(SOURCE),'-o',str(target)],check=True,capture_output=True,text=True)
    return target,{'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'binary_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'compiler':compiler,'flags':FLAGS}


class Kernel:
    def __init__(self,path):
        self.lib=C.CDLL(str(path));self.lib.e16_dyadic_size.restype=C.c_uint32;self.lib.e16_stats_size.restype=C.c_uint32
        if self.lib.e16_dyadic_size()!=C.sizeof(Dyadic) or self.lib.e16_stats_size()!=C.sizeof(Stats):raise ValueError('native ABI layout')
        d=C.POINTER(Dyadic);s=C.POINTER(Stats)
        specs={'e16_decode':[C.c_double,d,s], 'e16_half':[C.c_double,C.c_double,d,s],
               'e16_add':[d,d,d,s],'e16_compare':[d,d,C.POINTER(C.c_int32),s],
               'e16_floor':[d,C.POINTER(C.c_double),s],
               'e16_row_margin':[C.c_double,C.c_uint32,C.POINTER(C.c_double),C.POINTER(C.c_double),d,s]}
        for name,args in specs.items():fn=getattr(self.lib,name);fn.argtypes=args;fn.restype=C.c_int
    def checked(self,name,*args):
        code=getattr(self.lib,name)(*args)
        if code:raise ValueError(f'native exact refusal code={code}')
    def decode(self,value,stats):
        out=Dyadic();self.checked('e16_decode',value,C.byref(out),C.byref(stats));return pair(out)
    def half(self,x,y,stats):
        out=Dyadic();self.checked('e16_half',x,y,C.byref(out),C.byref(stats));return pair(out)
    def add(self,a,b,stats):
        aa,bb,out=from_pair(a),from_pair(b),Dyadic()
        self.checked('e16_add',C.byref(aa),C.byref(bb),C.byref(out),C.byref(stats));return pair(out)
    def compare(self,a,b,stats):
        aa,bb,out=from_pair(a),from_pair(b),C.c_int32()
        self.checked('e16_compare',C.byref(aa),C.byref(bb),C.byref(out),C.byref(stats));return out.value
    def floor(self,a,stats):
        aa,out=from_pair(a),C.c_double()
        self.checked('e16_floor',C.byref(aa),C.byref(out),C.byref(stats));return out.value
    def row(self,diagonal,outward,reverse,stats):
        if len(outward)!=len(reverse) or len(outward)>128:raise ValueError('native row shape/order cap')
        aa=(C.c_double*len(outward))(*outward);bb=(C.c_double*len(reverse))(*reverse);out=Dyadic()
        self.checked('e16_row_margin',diagonal,len(outward),aa,bb,C.byref(out),C.byref(stats));return pair(out)
