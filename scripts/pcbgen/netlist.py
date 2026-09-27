"""Small KiCad S-expression netlist reader with strict component keys."""
from __future__ import annotations
from dataclasses import dataclass
import json,re
from pathlib import Path

TOKEN=re.compile(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+')
def parse(tokens,i=0):
    if tokens[i]!='(':raise ValueError('expected opening parenthesis')
    out=[];i+=1
    while i<len(tokens) and tokens[i]!=')':
        if tokens[i]=='(':v,i=parse(tokens,i)
        else:v=json.loads(tokens[i]) if tokens[i].startswith('"') else tokens[i];i+=1
        out.append(v)
    if i>=len(tokens):raise ValueError('unclosed S-expression')
    return out,i+1

def one(node,name):
    found=[x for x in node if isinstance(x,list) and x and x[0]==name]
    if len(found)!=1:raise ValueError(f'expected one {name}')
    return found[0]

def many(node,name):return [x for x in node if isinstance(x,list) and x and x[0]==name]
@dataclass(frozen=True)
class Component:
    ref:str
    value:str
    footprint:str
    sheetname:str
    sheet_ts:str
    symbol_ts:str
    fields:tuple[tuple[str,str], ...]


def read_netlist(path:Path):
    tokens=TOKEN.findall(path.read_text());root,end=parse(tokens)
    if end!=len(tokens) or root[0]!='export':raise ValueError('invalid KiCad netlist')
    components=[]
    for n in many(one(root,'components'),'comp'):
        sheet=one(n,'sheetpath')
        properties=[]
        for prop in many(n,'property'):
            properties.append((one(prop,'name')[1],one(prop,'value')[1]))
        components.append(Component(one(n,'ref')[1],one(n,'value')[1],one(n,'footprint')[1],one(sheet,'names')[1],one(sheet,'tstamps')[1],one(n,'tstamps')[1],tuple(properties)))
    if len({c.ref for c in components})!=len(components):raise ValueError('duplicate netlist reference')
    pin_nets={}
    for n in many(one(root,'nets'),'net'):
        name=one(n,'name')[1]
        for node in many(n,'node'):
            key=(one(node,'ref')[1],one(node,'pin')[1])
            if key in pin_nets:raise ValueError(f'pin in two nets: {key}')
            pin_nets[key]=name
    return components,pin_nets
