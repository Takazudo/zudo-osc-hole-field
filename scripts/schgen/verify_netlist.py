#!/usr/bin/env python3
"""Compare every physical symbol pin in the KiCad export to the functional spec."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.schgen.core import children, designator, parse, tokens  # noqa: E402
from design.spec.instrument import specification  # noqa: E402


def expected_pin_nets(families, instances):
    result={}
    for inst in instances:
        family=next(f for f in families if f.name==inst.family)
        for part in family.parts:
            if part.symbol.rsplit(':', 1)[-1] in {'PWR_FLAG', 'VCC', 'GND'}:
                continue  # KiCad omits power symbols and flags from exported component/net nodes.
            ref=designator(part,inst)
            for pin,net in part.pins.items():
                key=(ref,pin)
                if key in result: raise ValueError(f'duplicate specified pin {key}')
                sheet_name = inst.name if part.page == 1 else f'{inst.name}-P{part.page}'
                result[key]=None if net is None else net if net in family.global_nets else f'/{sheet_name}/{net}'
    return result


def exported_pin_nets(netlist):
    tree,end=parse(tokens(netlist))
    if end!=len(tokens(netlist)) or tree[0]!='export': raise ValueError('not a complete KiCad export')
    nets=children(children(tree,'nets')[0],'net')
    result={}
    for net in nets:
        name=children(net,'name')[0][1]
        for node in children(net,'node'):
            ref=children(node,'ref')[0][1]
            pin=children(node,'pin')[0][1]
            key=(ref,pin)
            if key in result: raise ValueError(f'duplicate exported pin {key}')
            result[key]=None if name.startswith('unconnected-(') else name
    return result


def verify(families, instances, netlist):
    expected=expected_pin_nets(families,instances)
    actual=exported_pin_nets(netlist)
    differences=[]
    for key in sorted(expected.keys() | actual.keys()):
        if expected.get(key,'<absent>') != actual.get(key,'<absent>'):
            differences.append(f'{key[0]}.{key[1]}: spec={expected.get(key,"<absent>")!r}, export={actual.get(key,"<absent>")!r}')
    return differences


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist',type=Path)
    args=parser.parse_args()
    differences=verify(*specification(),args.netlist.read_text())
    if differences:
        print('\n'.join(differences),file=sys.stderr)
        return 1
    print('PASS: all specified symbol pins match KiCad netlist')
    return 0

if __name__=='__main__': raise SystemExit(main())
