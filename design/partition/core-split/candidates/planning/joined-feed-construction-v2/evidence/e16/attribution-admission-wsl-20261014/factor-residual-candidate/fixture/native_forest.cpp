// Synthetic-only virtual joined forest. Borrowed buffers; no original-data IO.
#include "native_exact.cpp"
#include <array>
extern "C" {
struct E16Board {
    uint32_t n, nnz, terminals;
    const int32_t *indptr, *indices, *columns;
    const double *data, *coupling;
};
struct E16ForestResult {
    double bound, ground, radius, deficit, q, midpoint_bound, interval_radius, interval_q;
    uint32_t root, edges;
    uint64_t index_visits[6], coefficient_reads[6], row_visits;
    E16Stats phases[6];
};
}
namespace {
// All fixed scratch remains charged for the entire invocation, including phases
// where portions are no longer used. No fictitious release/25n byte claim.
struct ForestScratch {
    uint32_t dsu[128], size[128], stack[128];
    double path[128];
    uint8_t state[128];
};
struct Scope {
    Stats& s;
    explicit Scope(Stats& stats):s(stats){s.scope_bits=64;}
    ~Scope(){s.proposed_contributions+=(s.scope_bits+63)/64;}
};
struct View {
    uint32_t count, terminals, free=0, n=0;
    const E16Board* boards;const double* midpoint;
    E16ForestResult& result;
    unsigned phase=0;
    void indices(uint64_t k=1){result.index_visits[phase]+=k;require(result.index_visits[phase]<=1000000,20);}
    double read(const double* ptr){++result.coefficient_reads[phase];require(std::isfinite(*ptr),21);return *ptr;}
    void validate(){
        require(count>0 && count<=2 && terminals<=8 && boards && (!terminals || midpoint),22);
        for(uint32_t b=0;b<count;++b){
            const auto& a=boards[b];indices();
            require(a.n>0 && a.n<=128 && a.nnz<=16384 && a.terminals<=terminals
                && a.indptr && a.indices && a.data && (!a.terminals || (a.columns && a.coupling)),22);
            require(a.indptr[0]==0 && a.indptr[a.n]==int32_t(a.nnz),22);indices(2);
            for(uint32_t i=0;i<a.n;++i){
                int32_t first=a.indptr[i],end=a.indptr[i+1];indices(2);
                require(first>=0 && end>=first && end<=int32_t(a.nnz),22);int32_t prev=-1;
                for(int32_t k=first;k<end;++k){indices();int32_t j=a.indices[k];require(j>prev && j<int32_t(a.n),22);prev=j;require(read(a.data+k)!=0.,22);}
            }
            for(uint32_t j=0;j<a.terminals;++j){indices();require(a.columns[j]>=0 && a.columns[j]<int32_t(terminals),22);
                for(uint32_t k=0;k<j;++k){indices(2);require(a.columns[k]!=a.columns[j],22);}}
            for(uint32_t k=0;k<a.n*a.terminals;++k)read(a.coupling+k);
            free+=a.n;
        }
        n=free+terminals;require(n<=128,22);
        for(uint32_t k=0;k<terminals*terminals;++k)read(midpoint+k);
    }
    double lookup(uint32_t i,uint32_t j){
        uint32_t offset=0;
        for(uint32_t b=0;b<count;++b){
            const auto& a=boards[b];indices();
            if(i>=offset && i<offset+a.n){
                uint32_t local=i-offset;
                if(j>=offset && j<offset+a.n){
                    int32_t lo=a.indptr[local],end=a.indptr[local+1],hi=end;indices(2);
                    while(lo<hi){int32_t mid=lo+(hi-lo)/2;indices();if(a.indices[mid]<int32_t(j-offset))lo=mid+1;else hi=mid;}
                    indices();require(lo<end && a.indices[lo]==int32_t(j-offset),23);return read(a.data+lo);
                }
                if(j>=free)for(uint32_t t=0;t<a.terminals;++t){indices();if(a.columns[t]==int32_t(j-free)){double v=read(a.coupling+local*a.terminals+t);require(v!=0.,23);return v;}}
                throw Refusal{23};
            }
            offset+=a.n;
        }
        if(j<free)return lookup(j,i);
        double v=read(midpoint+(i-free)*terminals+j-free);require(v!=0.,23);return v;
    }
    template<class F> void row(uint32_t i,F&& visit){
        ++result.row_visits;uint32_t offset=0;
        for(uint32_t b=0;b<count;++b){
            const auto& a=boards[b];indices();
            if(i>=offset && i<offset+a.n){
                const uint32_t local=i-offset;indices(2);
                for(int32_t k=a.indptr[local];k<a.indptr[local+1];++k){indices(2);visit(offset+a.indices[k],read(a.data+k));}
                for(uint32_t t=0;t<a.terminals;++t){double v=read(a.coupling+local*a.terminals+t);indices();if(v!=0.)visit(free+a.columns[t],v);}
                return;
            }
            offset+=a.n;
        }
        offset=0;
        for(uint32_t b=0;b<count;++b){const auto& a=boards[b];
            for(uint32_t t=0;t<a.terminals;++t){indices();if(a.columns[t]==int32_t(i-free))
                for(uint32_t k=0;k<a.n;++k){double v=read(a.coupling+k*a.terminals+t);if(v!=0.)visit(offset+k,v);}}
            offset+=a.n;
        }
        for(uint32_t j=0;j<terminals;++j){double v=read(midpoint+(i-free)*terminals+j);if(v!=0.)visit(free+j,v);}
    }
};
double upward(double v,Stats& s){s.floating_calls+=2;require(std::isfinite(v)&&v>=0.,24);v=std::nextafter(v,std::numeric_limits<double>::infinity());require(std::isfinite(v),24);return v;}
double divup(double a,double b,Stats& s){require(b>0. && std::isfinite(b),24);++s.floating_calls;return upward(a/b,s);}
double addup(double a,double b,Stats& s){++s.floating_calls;return upward(a+b,s);}
double mulup(double a,double b,Stats& s){++s.floating_calls;return upward(a*b,s);}
double upper(const D& a,Stats& s){
    if(!a.sign)return 0.;
    double lo=positive_floor(a,s);double hi=upward(lo,s);
    require(compare(a,decode(hi,s),s)<=0,24);return hi;
}
void forest(View& v,uint32_t* parent,double* edge){
    v.validate();const uint32_t n=v.n;auto& r=v.result;
    ForestScratch scratch{};v.indices(5*128);
    auto& dsu=scratch.dsu;auto& size=scratch.size;
    for(uint32_t i=0;i<n;++i){parent[i]=dsu[i]=i;edge[i]=0.;size[i]=1;v.indices(4);}
    auto find=[&](uint32_t x){uint32_t root=x,steps=0;
        while(true){v.indices();uint32_t p=dsu[root];if(p==root)break;root=p;require(++steps<=n,25);}
        while(x!=root){v.indices(2);uint32_t p=dsu[x];dsu[x]=root;x=p;}return root;};
    auto reroot=[&](uint32_t x){uint32_t cur=x,prev=x,steps=0;double carry=0.;
        while(true){v.indices(4);uint32_t next=parent[cur];double old=edge[cur];parent[cur]=prev;edge[cur]=carry;
            require(++steps<=n,25);if(next==cur)break;prev=cur;carry=old;cur=next;}};
    D best{},deficit{};r.phases[2].initialized_words+=2*LIMBS;r.root=n;
    for(uint32_t i=0;i<n;++i){v.phase=1;auto& s=r.phases[1];D margin=decode(v.lookup(i,i),s);s.copied_words_upper+=2*LIMBS;
        v.row(i,[&](uint32_t j,double value){
            v.phase=1;if(j==i)return;D symmetric;s.copied_words_upper+=4*LIMBS;
            {Scope scope(s);symmetric=half(value,v.lookup(j,i),s);D negative=symmetric;
             negative.sign=-std::abs(negative.sign);charge(s,2);margin=add(margin,negative,s);s.copied_words_upper+=2*LIMBS;}
            v.phase=2;auto& selection=r.phases[2];
            if(i<j && symmetric.sign<0){uint32_t ru=find(i),rv=find(j);if(ru!=rv){double c;
                {Scope scope(selection);D positive=symmetric;positive.sign=1;selection.copied_words_upper+=LIMBS;c=positive_floor(positive,selection);}
                uint32_t u=i,w=j;v.indices(2);if(size[ru]>size[rv]){std::swap(u,w);std::swap(ru,rv);}
                v.indices(4);require(parent[ru]==ru && parent[rv]==rv && size[ru]+size[rv]<=n,25);
                reroot(u);parent[u]=w;edge[u]=c;dsu[ru]=rv;size[rv]+=size[ru];v.indices(6);++r.edges;
            }}v.phase=1;
        });
        v.phase=2;auto& reduction=r.phases[2];if(compare(margin,best,reduction)>0){best=margin;r.root=i;reduction.copied_words_upper+=LIMBS;}
        margin.sign=-margin.sign;charge(reduction,1);if(compare(margin,deficit,reduction)>0){deficit=margin;reduction.copied_words_upper+=LIMBS;}
        uint64_t used=0;for(const auto& phase:r.phases)used+=phase.kernel_units;require(used<=UNIT_CAP,3);
    }
    require(r.root<n && r.edges==n-1,26);v.phase=3;auto& s=r.phases[3];
    {Scope scope(s);r.ground=positive_floor(best,s);}reroot(r.root);
    auto& path=scratch.path;auto& state=scratch.state;auto& stack=scratch.stack;
    {Scope scope(s);path[r.root]=divup(1.,r.ground,s);}state[r.root]=2;v.indices(2);
    for(uint32_t start=0;start<n;++start){v.indices();if(state[start]==2)continue;uint32_t cur=start,depth=0;
        while(true){v.indices();if(state[cur]==2)break;v.indices();require(state[cur]==0 && depth<n,25);
            state[cur]=1;stack[depth++]=cur;cur=parent[cur];v.indices(3);}
        while(depth){uint32_t node=stack[--depth],p=parent[node];v.indices(4);require(state[p]==2 && edge[node]>0.,25);
            {Scope scope(s);path[node]=addup(path[p],divup(1.,edge[node],s),s);}state[node]=2;v.indices(4);}
    }
    v.phase=4;auto& norm=r.phases[4];double maximum=0.;
    for(uint32_t i=0;i<n;++i){v.indices(2);maximum=std::max(maximum,path[i]);}
    {Scope scope(norm);r.radius=mulup(double(n),maximum,norm);}
    {Scope scope(norm);r.deficit=upper(deficit,norm);}
    {Scope scope(norm);r.q=mulup(r.deficit,r.radius,norm);}require(r.q<1.,27);
    double denominator;
    {Scope scope(norm);norm.floating_calls+=2;denominator=std::nextafter(1.-r.q,-std::numeric_limits<double>::infinity());}
    {Scope scope(norm);r.bound=divup(r.radius,denominator,norm);}
}
}
extern "C" {
uint32_t e16_forest_result_size(){return sizeof(E16ForestResult);}
uint32_t e16_forest_scratch_size(){return sizeof(ForestScratch);}
int e16_forest(uint32_t count,const E16Board* boards,uint32_t terminals,const double* midpoint,
               const double* lower,const double* upper_end,
               uint32_t* parent,double* edge,E16ForestResult* result){
    if(!parent||!edge||!result)return 10;
    *result=E16ForestResult{};
    try{
        require(!terminals || (lower && upper_end),22);
        View v{count,terminals,0,0,boards,midpoint,*result};forest(v,parent,edge);
        v.phase=5;auto& s=result->phases[5];result->midpoint_bound=result->bound;
        double radius=0.;
        for(uint32_t i=0;i<terminals;++i){double row=0.;
            for(uint32_t j=0;j<terminals;++j){const uint32_t k=i*terminals+j;
                const double lo=v.read(lower+k),hi=v.read(upper_end+k),mid=v.read(midpoint+k);
                require(lo<=hi,28);Scope scope(s);s.floating_calls+=4;
                double dl=std::nextafter(lo-mid,-std::numeric_limits<double>::infinity());
                double dh=std::nextafter(hi-mid,std::numeric_limits<double>::infinity());
                require(std::isfinite(dl)&&std::isfinite(dh),24);
                row=addup(row,std::max(std::abs(dl),std::abs(dh)),s);
            }radius=std::max(radius,row);
        }
        result->interval_radius=radius;
        {Scope scope(s);result->interval_q=mulup(result->bound,radius,s);}
        require(result->interval_q<1.,29);double denominator;
        {Scope scope(s);s.floating_calls+=2;denominator=std::nextafter(1.-result->interval_q,-std::numeric_limits<double>::infinity());}
        {Scope scope(s);result->bound=divup(result->bound,denominator,s);}
        uint64_t total=0;for(const auto& phase:result->phases)total+=phase.kernel_units;
        require(total<=UNIT_CAP,3);return 0;
    }
    catch(const Refusal& r){return r.code;}catch(...){return 11;}
}
}
