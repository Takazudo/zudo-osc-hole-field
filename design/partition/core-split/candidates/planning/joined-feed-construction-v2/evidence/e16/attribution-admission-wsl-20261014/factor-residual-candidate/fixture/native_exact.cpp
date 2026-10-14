// Synthetic-only bounded exact dyadics. No matrix solve or original-data entry.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {
constexpr unsigned LIMBS=34, BITS=2176;
constexpr uint64_t UNIT_CAP=200000;
struct Refusal { int code; };
void require(bool ok,int code=1) { if(!ok) throw Refusal{code}; }
}
extern "C" {
struct E16Dyadic { uint64_t word[34]; uint32_t used; int32_t sign; int32_t exponent; };
struct E16Stats {
    uint64_t kernel_units, bit_work_envelope, limb_visits, initialized_words;
    uint64_t copied_words_upper, floating_calls;
    uint64_t peak_bits, scope_bits, proposed_contributions;
};
}
namespace {
using D=E16Dyadic;using Stats=E16Stats;
static_assert(sizeof(double)==8 && std::numeric_limits<double>::is_iec559
    && std::numeric_limits<double>::radix==2 && std::numeric_limits<double>::digits==53
    && std::numeric_limits<double>::min_exponent==-1021 && std::numeric_limits<double>::max_exponent==1024);
void charge(Stats& s,uint64_t count,unsigned bits=64) {
    require(bits>0 && bits<=BITS,2);
    s.kernel_units+=count;s.bit_work_envelope+=count*uint64_t(bits)*bits;
    s.peak_bits=std::max(s.peak_bits,uint64_t(bits));s.scope_bits=std::max(s.scope_bits,uint64_t(bits));
    require(s.kernel_units<=UNIT_CAP,3);
}
D blank(Stats& s) { s.initialized_words+=LIMBS;s.copied_words_upper+=2*LIMBS;return D{}; }
unsigned width(const D& a) {
    return a.used ? (a.used-1)*64+64-unsigned(__builtin_clzll(a.word[a.used-1])) : 0;
}
void validate(const D& a,Stats& s) {
    charge(s,5,64);
    require(a.used<=LIMBS && a.exponent>=-1075 && a.exponent<=2048,4);
    if(!a.used) require(a.sign==0 && a.exponent==0,4);
    else require((a.sign==1 || a.sign==-1) && a.word[a.used-1]!=0 && (a.word[0]&1),4);
    // Full operand width remains visible even when zero shortcuts avoid limb work.
    s.scope_bits=std::max(s.scope_bits,uint64_t(width(a)));
    s.peak_bits=std::max(s.peak_bits,uint64_t(width(a)));
    for(unsigned i=a.used;i<LIMBS;++i) { ++s.limb_visits;require(a.word[i]==0,4); }
}
void normalize(D& a,Stats& s) {
    while(a.used && !a.word[a.used-1]) { ++s.limb_visits;--a.used; }
    if(!a.used) {a.sign=0;a.exponent=0;return;}
    unsigned low=0;
    while(!a.word[low]) {++s.limb_visits;++low;}
    const unsigned bits=unsigned(__builtin_ctzll(a.word[low]));
    charge(s,3,64);const unsigned shift=low*64+bits;
    require(int64_t(a.exponent)+shift<=2048,4);
    if(shift) {
        const unsigned old=a.used,new_used=old-low;
        for(unsigned i=0;i<new_used;++i) {
            uint64_t v=a.word[i+low]>>bits;
            if(bits && i+low+1<old) v|=a.word[i+low+1]<<(64-bits);
            a.word[i]=v;s.limb_visits+=3;charge(s,bits?3:1,64);
        }
        for(unsigned i=new_used;i<old;++i) {a.word[i]=0;++s.limb_visits;}
        a.used=new_used;a.exponent+=int32_t(shift);
        while(a.used && !a.word[a.used-1]) {--a.used;++s.limb_visits;}
    }
    require(a.exponent>=-1075 && a.exponent<=2048,4);
}
D decode(double x,Stats& s) {
    uint64_t raw;std::memcpy(&raw,&x,8);charge(s,6,64);
    const unsigned e=unsigned((raw>>52)&2047);require(e!=2047,5);
    uint64_t m=raw&((uint64_t(1)<<52)-1);
    D a=blank(s);
    if(e) {m|=uint64_t(1)<<52;a.exponent=int32_t(e)-1075;charge(s,2,64);}
    else a.exponent=-1074;
    if(m) {a.word[0]=m;a.used=1;a.sign=(raw>>63)?-1:1;}
    normalize(a,s);return a;
}
D aligned(const D& a,unsigned shift,Stats& s) {
    const unsigned w=width(a);require(uint64_t(w)+shift<=BITS,6);
    charge(s,2,64);D r=blank(s);r.sign=a.sign;r.exponent=a.exponent-int32_t(shift);
    if(!a.used) return r;
    const unsigned whole=shift/64,part=shift%64;
    r.used=(w+shift+63)/64;
    for(unsigned i=0;i<a.used;++i) {
        r.word[i+whole]|=a.word[i]<<part;charge(s,2,64);s.limb_visits+=2;
        if(part && i+whole+1<LIMBS) {r.word[i+whole+1]|=a.word[i]>>(64-part);charge(s,2,64);s.limb_visits+=2;}
    }
    s.scope_bits=std::max(s.scope_bits,uint64_t(w+shift));s.peak_bits=std::max(s.peak_bits,uint64_t(w+shift));
    return r;
}
int magnitude_compare(const D& a,const D& b,Stats& s) {
    charge(s,2,64);
    if(a.used!=b.used) return a.used>b.used?1:-1;
    for(unsigned i=a.used;i>0;--i) {s.limb_visits+=2;charge(s,2,64);if(a.word[i-1]!=b.word[i-1])return a.word[i-1]>b.word[i-1]?1:-1;}
    return 0;
}
D add(const D& a,const D& b,Stats& s) {
    validate(a,s);validate(b,s);charge(s,2,64);
    if(!a.sign){s.copied_words_upper+=2*LIMBS;return b;}
    if(!b.sign){s.copied_words_upper+=2*LIMBS;return a;}
    const int e=std::min(a.exponent,b.exponent);charge(s,3,64);
    const unsigned wa=width(a)+unsigned(a.exponent-e),wb=width(b)+unsigned(b.exponent-e);
    require(std::max(wa,wb)+1<=BITS,6);
    const unsigned operation_width=std::max(wa,wb)+1;
    s.scope_bits=std::max(s.scope_bits,uint64_t(operation_width));s.peak_bits=std::max(s.peak_bits,uint64_t(operation_width));
    D aa=aligned(a,unsigned(a.exponent-e),s),bb=aligned(b,unsigned(b.exponent-e),s),r=blank(s);r.exponent=e;
    const unsigned n=std::max(aa.used,bb.used);
    if(a.sign==b.sign) {
        uint64_t carry=0;r.sign=a.sign;r.used=n;
        for(unsigned i=0;i<n;++i) {
            const uint64_t first=aa.word[i]+bb.word[i];
            const bool c1=first<aa.word[i];
            const uint64_t total=first+carry;
            const bool c2=total<first;
            r.word[i]=total;carry=c1||c2;charge(s,6,64);s.limb_visits+=3;
        }
        if(carry) {require(n<LIMBS,6);r.word[n]=carry;r.used=n+1;}
    } else {
        const int order=magnitude_compare(aa,bb,s);if(!order){r.exponent=0;return r;}
        const D& large=order>0?aa:bb;const D& small=order>0?bb:aa;
        r.sign=order>0?a.sign:b.sign;r.used=n;uint64_t borrow=0;
        for(unsigned i=0;i<n;++i) {
            const uint64_t first=large.word[i]-small.word[i];
            const bool b1=large.word[i]<small.word[i];
            const uint64_t value=first-borrow;
            const bool b2=first<borrow;
            r.word[i]=value;borrow=b1||b2;charge(s,6,64);s.limb_visits+=3;
        }
        require(!borrow,7);
    }
    normalize(r,s);return r;
}
D half(double x,double y,Stats& s) {
    D a=decode(x,s),b=decode(y,s),r=add(a,b,s);
    if(r.sign) {require(r.exponent>-1075,4);--r.exponent;charge(s,1,64);}
    return r;
}
int compare(const D& a,const D& b,Stats& s) {
    validate(a,s);validate(b,s);charge(s,4,64);
    if(a.sign!=b.sign)return a.sign>b.sign?1:-1;
    if(!a.sign)return 0;
    const int la=int(width(a))+a.exponent,lb=int(width(b))+b.exponent;charge(s,3,64);
    if(la!=lb)return a.sign*(la>lb?1:-1);
    const int e=std::min(a.exponent,b.exponent);
    D aa=aligned(a,unsigned(a.exponent-e),s),bb=aligned(b,unsigned(b.exponent-e),s);
    return a.sign*magnitude_compare(aa,bb,s);
}
double positive_floor(const D& a,Stats& s) {
    validate(a,s);require(a.sign>0,8);const unsigned w=width(a),shift=w>53?w-53:0;
    const unsigned whole=shift/64,part=shift%64;
    uint64_t m=a.word[whole]>>part;
    if(part && whole+1<a.used)m|=a.word[whole+1]<<(64-part);
    charge(s,5,64);s.limb_visits+=2;
    const double result=std::ldexp(double(m),a.exponent+int(shift));s.floating_calls+=2;
    require(std::isfinite(result) && result>0,8);
    D candidate=decode(result,s);require(compare(candidate,a,s)<=0,9);return result;
}
template<class F> int guarded(Stats* s,F&& f) {
    if(!s)return 10;
    try {
        require(s->kernel_units<=UNIT_CAP,3);
        require(s->bit_work_envelope<=UNIT_CAP*uint64_t(BITS)*BITS
            && s->limb_visits<=UNIT_CAP*1024 && s->initialized_words<=UNIT_CAP*1024
            && s->copied_words_upper<=UNIT_CAP*4096 && s->floating_calls<=UNIT_CAP*8
            && s->peak_bits<=BITS && s->scope_bits<=BITS
            && s->proposed_contributions<=UNIT_CAP*LIMBS,13);
        f();return 0;
    }
    catch(const Refusal& r){return r.code;}catch(...){return 11;}
}
}
extern "C" {
uint32_t e16_dyadic_size(){return sizeof(E16Dyadic);}
uint32_t e16_stats_size(){return sizeof(E16Stats);}
int e16_decode(double value,E16Dyadic* out,E16Stats* s) {
    if(!out)return 10;
    return guarded(s,[&]{*out=blank(*s);*out=decode(value,*s);s->copied_words_upper+=LIMBS;});
}
int e16_add(const E16Dyadic* a,const E16Dyadic* b,E16Dyadic* out,E16Stats* s) {
    if(!a||!b||!out)return 10;
    return guarded(s,[&]{D value=add(*a,*b,*s);*out=value;s->copied_words_upper+=LIMBS;});
}
int e16_half(double a,double b,E16Dyadic* out,E16Stats* s) {
    if(!out)return 10;
    return guarded(s,[&]{*out=blank(*s);*out=half(a,b,*s);s->copied_words_upper+=LIMBS;});
}
int e16_compare(const E16Dyadic* a,const E16Dyadic* b,int32_t* out,E16Stats* s) {
    if(!a||!b||!out)return 10;
    return guarded(s,[&]{*out=compare(*a,*b,*s);});
}
int e16_floor(const E16Dyadic* a,double* out,E16Stats* s) {
    if(!a||!out)return 10;
    return guarded(s,[&]{*out=positive_floor(*a,*s);});
}
int e16_row_margin(double diagonal,uint32_t count,const double* outward,const double* reverse,E16Dyadic* out,E16Stats* s) {
    if(!out||(!outward&&count)||(!reverse&&count))return 10;
    return guarded(s,[&]{
        require(count<=128,12);*out=blank(*s);D margin=decode(diagonal,*s);
        for(uint32_t i=0;i<count;++i) {
            s->scope_bits=64;
            try {
                D symmetric=half(outward[i],reverse[i],*s);
                if(symmetric.sign<0)symmetric.sign=1;
                symmetric.sign=-symmetric.sign;charge(*s,2,64);
                margin=add(margin,symmetric,*s);s->copied_words_upper+=LIMBS;
            }
            catch(...) {s->proposed_contributions+=(s->scope_bits+63)/64;throw;}
            s->proposed_contributions+=(s->scope_bits+63)/64;
        }
        *out=margin;s->copied_words_upper+=LIMBS;
    });
}
}
