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


def is_abstract_boundary(component: Component) -> bool:
    """Recognize only the deliberately unimplemented EXT contract symbols."""
    fields=dict(component.fields)
    marker=fields.get('AbstractBoundary')
    if marker is None:
        if component.ref in {'CN301','XB301'} and not component.footprint:
            raise ValueError(f'{component.ref}: unmarked footprintless power boundary')
        return False
    if marker!='true' or component.ref not in {'CN301','XB301'} or component.footprint or fields.get('MPN') or fields.get('Implementation')!='REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE':
        raise ValueError(f'{component.ref}: malformed abstract boundary in board netlist')
    return True


def read_netlist(path:Path, *, include_abstract:bool=False):
    tokens=TOKEN.findall(path.read_text());root,end=parse(tokens)
    if end!=len(tokens) or root[0]!='export':raise ValueError('invalid KiCad netlist')
    components=[]
    for n in many(one(root,'components'),'comp'):
        sheet=one(n,'sheetpath')
        properties=[]
        for prop in many(n,'property'):
            values=many(prop,'value')
            if len(values)>1:raise ValueError('duplicate component property value')
            properties.append((one(prop,'name')[1],values[0][1] if values else ''))
        footprints=many(n,'footprint')
        if len(footprints)>1:raise ValueError('duplicate component footprint')
        components.append(Component(one(n,'ref')[1],one(n,'value')[1],footprints[0][1] if footprints else '',one(sheet,'names')[1],one(sheet,'tstamps')[1],one(n,'tstamps')[1],tuple(properties)))
    if len({c.ref for c in components})!=len(components):raise ValueError('duplicate netlist reference')
    abstract_refs={c.ref for c in components if is_abstract_boundary(c)}
    if not include_abstract:
        components=[c for c in components if c.ref not in abstract_refs]
    pin_nets={}
    for n in many(one(root,'nets'),'net'):
        name=one(n,'name')[1]
        for node in many(n,'node'):
            key=(one(node,'ref')[1],one(node,'pin')[1])
            if not include_abstract and key[0] in abstract_refs:continue
            if key in pin_nets:raise ValueError(f'pin in two nets: {key}')
            pin_nets[key]=name
    return components,pin_nets
