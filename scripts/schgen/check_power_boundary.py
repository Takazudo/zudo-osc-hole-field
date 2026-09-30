#!/usr/bin/env python3
"""Check native netlist semantics of the non-orderable EXT draft boundary."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.schgen.core import children, parse, tokens

OUTPUT = ROOT/'design/reports/power-boundary.json'
RAW = {'+12V_IN':{('CN301','1'),('XB301','1')},
       '-12V_IN':{('CN301','2'),('XB301','2')},
       '+5V_IN':{('CN301','3'),('XB301','3')}}
LOAD = {'+12V':('XB301','4'),'-12V':('XB301','5'),'+5V':('XB301','6')}
AGND = {('CN301',str(n)) for n in range(5,9)}|{('XB301','7')}
STATUS = 'REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE'


def require(condition, message):
    if not condition: raise ValueError(message)


def build(netlist: str, bom: str | None = None):
    tree,end=parse(tokens(netlist))
    require(end==len(tokens(netlist)) and tree[0]=='export','incomplete native netlist')
    components={children(c,'ref')[0][1]:c for c in children(children(tree,'components')[0],'comp')}
    for ref,name in (('CN301','OSC_EXT_INLET_R1'),('XB301','OSC_EXT_BOUNDARY_R1')):
        require(ref in components,f'missing abstract component {ref} in native netlist')
        comp=components[ref]
        lib=children(comp,'libsource')[0]
        require(children(lib,'part')[0][1]==name,f'wrong abstract symbol {ref}')
        properties={children(p,'name')[0][1]:children(p,'value')[0][1]
                    for p in children(comp,'property') if children(p,'name') and children(p,'value')}
        require(properties.get('Implementation')==STATUS and properties.get('AbstractBoundary')=='true' and
                not properties.get('Footprint') and not properties.get('MPN'),
                f'abstract component {ref} lost non-orderable status')
    require(not any(ref.startswith(('#FLG',)) for ref in components), 'ERC power flag cannot prove implementation')
    nets={}
    for n in children(children(tree,'nets')[0],'net'):
        name=children(n,'name')[0][1]
        require(name not in nets,'duplicate net name: '+name)
        nets[name]={(children(node,'ref')[0][1],children(node,'pin')[0][1]) for node in children(n,'node')}
    for name,expected in RAW.items():
        require(nets.get(name)==expected,f'raw inlet net has missing, joined or unexpected nodes: {name}')
    for name,pin in LOAD.items():
        require(pin in nets.get(name,set()) and len(nets[name])>1,f'conditional load rail missing boundary or load: {name}')
        require(not any(ref=='CN301' for ref,_ in nets[name]),f'inlet directly joined to load: {name}')
    require(AGND <= nets.get('AGND',set()),'common AGND inlet and boundary nodes missing')
    require(not any(('CN301','4') in nodes for name,nodes in nets.items() if not name.startswith('unconnected-(')),
            'logical pin 4 must be NC')
    if bom is not None:
        require(all(ref not in bom for ref in ('CN301','XB301')),'abstract component leaked into KiCad BOM')
    return {'schema_version':1,
            'status':'PASS: native raw/load nets distinct; requirement-only boundary remains UNIMPLEMENTED',
            'netlist_boundary_components':{'inlet':'CN301','unimplemented_boundary':'XB301'},
            'raw_net_nodes':{name:sorted(nodes) for name,nodes in RAW.items()},
            'load_rail_boundary_nodes':{name:list(pin) for name,pin in LOAD.items()},
            'agnd_inlet_and_boundary_nodes':sorted(AGND),
            'orderable_footprint':None,'bom_entry':False if bom is not None else None,
            'erc_power_output_meaning':'Abstract declaration for ERC only; no protected continuity or physical source is implemented',
            'protection_implemented':False,'energization_authorized':False,
            'circuit_evidence_issue':'https://github.com/Takazudo/zudo-osc-hole-field/issues/59',
            'physical_qualification_issue':'https://github.com/Takazudo/zudo-osc-hole-field/issues/57'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist',type=Path)
    parser.add_argument('--bom',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    report=build(args.netlist.read_text(),args.bom.read_text() if args.bom else None)
    content=json.dumps(report,indent=2)+'\n'
    if args.check:require(OUTPUT.read_text()==content,'power-boundary report drift')
    else:OUTPUT.write_text(content)
    print(report['status'])

if __name__=='__main__':main()
