"""Select local signal nets for a disposable Freerouting pilot.

The full KiCad DSN remains intact. Only network class membership changes;
all pads, net descriptors, rules, keepouts, planes and prior wiring remain.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

ATOM=re.compile(r'^[A-Za-z0-9_+./:-]+$')
HEAD=re.compile(r'\(\s*([^\s()]+)')
TOKEN=re.compile(r'"(?:\\.|[^"\\])*"|[^\s]+')
def valid_token(token):return bool(ATOM.fullmatch(token) or re.fullmatch(r'"(?:\\.|[^"\\])*"',token))

def nodes(source):
    stack=[];result=[];quoted=False;escaped=False
    for i,ch in enumerate(source):
        if quoted:
            if escaped:escaped=False
            elif ch=='\\':escaped=True
            elif ch=='"':quoted=False
        elif ch=='"':
            # SPECCTRA declares its quote character as a bare token here.
            if not source[max(0,i-14):i].endswith('(string_quote '):quoted=True
        elif ch=='(':
            stack.append(i)
        elif ch==')':
            if not stack:raise ValueError('unbalanced DSN close')
            start=stack.pop();m=HEAD.match(source,start)
            if not m:raise ValueError('DSN node without head')
            result.append((start,i+1,len(stack),m.group(1)))
        elif ch==';':raise ValueError('unsupported DSN comment')
    if quoted or stack:raise ValueError('unclosed DSN string or node')
    return result

def direct(items,parent):
    start,end,depth,_=parent
    return sorted((x for x in items if x[2]==depth+1 and start<x[0]<x[1]<end),key=lambda x:x[0])

def class_parts(source,items,node):
    children=direct(items,node)
    if [x[3] for x in children]!=['circuit','rule']:
        raise ValueError('unknown class child layout')
    prefix=TOKEN.findall(source[node[0]+1:children[0][0]])
    if len(prefix)<2 or prefix[0]!='class' or any(not valid_token(t) for t in prefix):
        raise ValueError('unknown class token layout')
    return prefix[1],prefix[2:],source[children[0][0]:node[1]-1]

def transform(source,selected):
    if not selected or len(set(selected))!=len(selected) or any(not ATOM.fullmatch(n) for n in selected):
        raise ValueError('pilot nets must be unique simple DSN atoms')
    items=nodes(source);root=[x for x in items if x[2]==0]
    if len(root)!=1 or root[0][3]!='pcb':raise ValueError('expected one pcb root')
    top=direct(items,root[0]);heads=[x[3] for x in top]
    if heads!=['parser','resolution','unit','structure','placement','library','network','wiring']:
        raise ValueError(f'unknown DSN top-level structure {heads}')
    network=top[-2];children=direct(items,network)
    if any(x[3] not in ('net','class') for x in children):raise ValueError('unknown network child')
    nets=[x for x in children if x[3]=='net'];classes=[x for x in children if x[3]=='class']
    if not nets or len(classes)!=3 or children!=nets+classes:raise ValueError('unexpected network ordering')
    net_names=[]
    for node in nets:
        parts=TOKEN.findall(source[node[0]+1:direct(items,node)[0][0]])
        if len(parts)!=2 or parts[0]!='net' or not valid_token(parts[1]):raise ValueError('unknown net descriptor')
        if [x[3] for x in direct(items,node)]!=['pins']:raise ValueError('unknown net child')
        net_names.append(parts[1])
    if len(set(net_names))!=len(net_names):raise ValueError('duplicate DSN net')
    parsed=[class_parts(source,items,x) for x in classes]
    by_name={name:(members,body,node) for (name,members,body),node in zip(parsed,classes)}
    if set(by_name)!={'kicad_default','Ground','Rails'}:raise ValueError('unexpected DSN classes')
    members=[n for group,_,_ in by_name.values() for n in group]
    if len(members)!=len(set(members)) or set(members)!=set(net_names):raise ValueError('class membership does not exactly cover nets')
    default,body,node=by_name['kicad_default']
    if not set(selected)<=set(default):raise ValueError('pilot net absent from default signal class')
    if any(n in ('AGND','+12V','-12V','+5V') for n in selected):raise ValueError('shared rail/ground cannot be pilot net')
    retained=[n for n in default if n not in set(selected)]
    replacement='(class kicad_default '+' '.join(retained)+'\n'+body+')'
    pilot='\n    (class Pilot '+' '.join(selected)+'\n'+body+')'
    result=source[:node[0]]+replacement+source[node[1]:network[1]-1]+pilot+source[network[1]-1:]
    after=nodes(result);newroot=[x for x in after if x[2]==0][0];newtop=direct(after,newroot)
    for old,new in zip(top,newtop):
        if old[3]!='network' and source[old[0]:old[1]]!=result[new[0]:new[1]]:raise ValueError('non-network DSN changed')
    newnet=next(x for x in newtop if x[3]=='network');newchildren=direct(after,newnet)
    newnets=[x for x in newchildren if x[3]=='net']
    if len(newnets)!=len(nets) or any(source[a[0]:a[1]]!=result[b[0]:b[1]] for a,b in zip(nets,newnets)):
        raise ValueError('net descriptor changed')
    newclasses={p[0]:p for p in (class_parts(result,after,x) for x in newchildren if x[3]=='class')}
    if set(newclasses)!={'kicad_default','Ground','Rails','Pilot'}:raise ValueError('post-filter classes changed')
    if newclasses['Pilot'][1]!=selected or newclasses['Pilot'][2]!=body or newclasses['kicad_default'][1]!=retained:
        raise ValueError('pilot class verification failed')
    for name in ('Ground','Rails'):
        if newclasses[name]!=parsed[[x[0] for x in parsed].index(name)]:raise ValueError('protected class changed')
    return result,{'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'pilot_sha256':hashlib.sha256(result.encode()).hexdigest(),'pilot_nets':selected,'unchanged_net_descriptors':len(nets),'unchanged_non_network_sections':[x[3] for x in top if x[3]!='network'],'ignored_classes':['kicad_default','Ground','Rails']}

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('receipt',type=Path);p.add_argument('nets',nargs='+');a=p.parse_args()
    result,receipt=transform(a.source.read_text(),a.nets)
    a.output.write_text(result);a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
