#!/usr/bin/env python3
"""Audit the complete generated instrument against its locked panel and netlist."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from design.spec.instrument import specification
from design.spec.cells._builder import load_symbol
from scripts.schgen.core import LibrarySymbol,children,designator,parse,tokens,validate_family
from scripts.schgen.verify_netlist import verify

EXPECTED_MODULES={*(f'O{i}' for i in range(1,6)),*(f'F{i}' for i in range(1,4)),
                  'M5A','M5B','M4A','M4B',*(f'E{i}' for i in range(1,7)),
                  'W1','W2',*(f'A{i:02d}' for i in range(1,7)),
                  'B1','B2','H1','H2','X1','X2','N1'}
FIXTURES={'PWR_FLAG':'PWR_FLAG','GND':'GND','VCC':'VCC',
          'LM2902':'LM2902','LM2903':'LM2903','R':'R','Conn_01x02':'Conn_01x02'}


def unit_coverage_error(ref,entries,library):
    """Return a missing/duplicate unit fault even if only one unit is present."""
    symbol=entries[0][3]
    expected={u for u,pins in library[symbol].units.items() if pins}
    actual=[e[2] for e in entries]
    if len(actual)!=len(set(actual)) or set(actual)!=expected:
        return f'package unit mismatch {ref}: represented {sorted(actual)}, expected {sorted(expected)}'
    return None


def active_unit_termination_error(ref,parts):
    floating=[p['unit'] for p in parts if p['pins'] and all(v is None for v in p['pins'].values())]
    return f'all-NC active units {ref}: {floating}' if floating else None


def coverage_errors(bound,placements,panel_count):
    missing=sorted(set(placements)-set(bound))
    extra=sorted(set(bound)-set(placements))
    duplicate={k:v for k,v in bound.items() if len(v)!=1}
    errors=[]
    if missing:errors.append('unbound UIDs: '+', '.join(missing))
    if extra:errors.append('extra UIDs: '+', '.join(extra))
    if duplicate:errors.append('duplicate UID bindings: '+str(duplicate))
    if len(bound)!=438 or panel_count!=438:
        errors.append(f'panel count: {len(bound)} UIDs, {panel_count} parts; expected 438')
    return errors


def check(families,instances,netlist):
    errors=[]
    names=[i.name for i in instances]
    signal_instances=[i for i in instances if i.name in EXPECTED_MODULES]
    if (set(i.name for i in signal_instances)!=EXPECTED_MODULES or
            len(signal_instances)!=len(EXPECTED_MODULES)):
        errors.append(f'signal-module roster: expected exactly {len(EXPECTED_MODULES)} fixed modules {sorted(EXPECTED_MODULES)}, got {[i.name for i in signal_instances]}')
    if len(names)!=len(set(names)):
        errors.append(f'duplicate hierarchy instance name: {names}')
    if len({i.index for i in instances})!=len(instances):errors.append('duplicate instance index')
    library={}
    for f in families:
        for p in f.parts:
            if p.symbol not in library:
                if p.symbol.startswith('Fixture:'):
                    key=p.symbol.split(':',1)[1]
                    path=ROOT/'scripts/schgen/fixtures'/f'{FIXTURES[key]}.kicad_sympart'
                    library[p.symbol]=LibrarySymbol.from_fixture(p.symbol,path)
                else:library[p.symbol]=load_symbol(p.symbol.split(':',1)[1])
        validate_family(f,library)
    differences=verify(families,instances,netlist)
    if differences:errors.extend('netlist parity: '+x for x in differences[:30])
    placements={p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
    bound=defaultdict(list);refs=defaultdict(list);sensitive=[];islands=defaultdict(list)
    family_by_name={f.name:f for f in families}
    per_instance=Counter();by_symbol=Counter();by_prefix=Counter();ic_by_part=Counter()
    unit_packages=defaultdict(list);panel_count=0
    for inst in instances:
        f=family_by_name[inst.family]
        for p in f.parts:
            ref=designator(p,inst);symbol=p.symbol.split(':')[-1]
            uid=p.attributes.get('PanelUid','').replace('${SHEETNAME}',inst.name)
            island=p.attributes.get('Island','').replace('${SHEETNAME}',inst.name)
            refs[ref].append((inst.name,p.key,p.unit,p.symbol))
            if p.prefix!='#FLG':
                # Count one physical component per reference after the loop.
                unit_packages[ref].append({'unit':p.unit,'pins':p.pins,'symbol':p.symbol,'instance':inst.name})
            if island:islands[island].append(ref)
            if uid:
                panel_count+=1;bound[uid].append(ref)
                if uid not in placements:errors.append(f'unknown panel UID {uid} -> {ref}')
                elif placements[uid]['ref']!=ref:errors.append(f'panel reference mismatch {uid}: {ref} != {placements[uid]["ref"]}')
                if not (p.panel_refs or p.panel_ref):errors.append(f'panel UID lacks locked ref {uid}: {ref}')
            elif p.panel_refs or p.panel_ref:errors.append(f'panel ref lacks UID {ref}')
        for net in f.sensitive_nets:
            if net in f.global_nets:errors.append(f'sensitive global net {inst.name}/{net}')
            members=[]
            for p in f.parts:
                for pin,value in p.pins.items():
                    if value!=net:continue
                    ref=designator(p,inst);island=p.attributes.get('Island','').replace('${SHEETNAME}',inst.name)
                    uid=p.attributes.get('PanelUid','').replace('${SHEETNAME}',inst.name)
                    members.append({'ref':ref,'pin':pin,'island':island,'panel_uid':uid})
            if not members:errors.append(f'sensitive net unused {inst.name}/{net}')
            if any(not x['island'] for x in members):
                errors.append(f'sensitive net member lacks island {inst.name}/{net}: {members}')
            panels=[x for x in members if x['panel_uid']]
            for part in panels:
                if not part['island'] or any(x['island']!=part['island'] for x in members):
                    errors.append(f'sensitive panel net outside one island {inst.name}/{net}: {members}')
            sensitive.append({'net':net if net in f.global_nets else f'/{inst.name}/{net}',
                              'members':members,'islands':sorted({x['island'] for x in members})})
    errors.extend(coverage_errors(bound,placements,panel_count))
    power_families={f.name for f in families if any(
        p.attributes.get('Role','').startswith('power:') for p in f.parts)}
    power_refs={designator(p,inst) for inst in instances if inst.family in power_families
                for p in family_by_name[inst.family].parts}
    signal_ref_count=len(set(refs)-power_refs)
    # The signal/reference lock includes 20 newly required bipolar LM393
    # negative-rail bypass capacitors, two on each of ten offset/mixer instances.
    # #60 adds four mixer quads + eight bypasses, and two A/B remote
    # buffers (quad, two bypasses and two isolation resistors each).
    expected_signal_refs=5723+20+4*3+2*5+5*(6*3+2*3)+12  # #62 fanout plus #61 stage limiters
    if signal_ref_count!=expected_signal_refs:
        errors.append(f'signal/reference designator lock drift: {signal_ref_count} != {expected_signal_refs}')
    if len(refs)!=expected_signal_refs+len(power_refs):
        errors.append(f'designator lock drift: {len(refs)} != {expected_signal_refs} + {len(power_refs)} actual power refs')
    unit_audit=[]
    for ref,entries in sorted(refs.items()):
        symbols={e[3] for e in entries};units=[e[2] for e in entries]
        stems={(e[0],e[1].rsplit('.',1)[0]) for e in entries}
        if len(symbols)!=1 or len(units)!=len(set(units)) or len(stems)!=1:
            errors.append(f'designator/package/unit conflict {ref}: {entries}')
        p=entries[0];symbol=p[3].split(':')[-1]
        if p[3].split(':')[-1] in ('PWR_FLAG','VCC','GND'):continue
        per_instance[p[0]]+=1;by_symbol[symbol]+=1
        prefix=''.join(c for c in ref if not c.isdigit()).rstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ') or ref[0]
        by_prefix[prefix]+=1
        if ref.startswith('U'):ic_by_part[symbol]+=1
        unit_fault=unit_coverage_error(ref,entries,library)
        if unit_fault:errors.append(unit_fault)
        termination_fault=active_unit_termination_error(ref,unit_packages[ref])
        if termination_fault:errors.append(termination_fault)
        if len({u for u,pins in library[p[3]].units.items() if pins})>1:
            unit_audit.append({'ref':ref,'symbol':symbol,'instance':p[0],
                               'units':sorted(units),
                               'explicit_no_connect_pins':sum(v is None for q in unit_packages[ref] for v in q['pins'].values()),
                               'fully_no_connect_units':[q['unit'] for q in unit_packages[ref] if all(v is None for v in q['pins'].values())]})
    tree,end=parse(tokens(netlist))
    if end!=len(tokens(netlist)) or tree[0]!='export':errors.append('invalid KiCad netlist')
    nets=children(children(tree,'nets')[0],'net')
    distribution=Counter(len(children(n,'node')) for n in nets)
    exported={children(c,'ref')[0][1] for c in children(children(tree,'components')[0],'comp')}
    specified={ref for ref,entries in refs.items() if entries[0][3].split(':')[-1] not in ('PWR_FLAG','VCC','GND')}
    if exported!=specified:errors.append(f'component set drift: missing {sorted(specified-exported)[:20]}, extra {sorted(exported-specified)[:20]}')
    if errors:raise ValueError('\n'.join(errors))
    module_instance_names=sorted(i.name for i in signal_instances)
    power_instance_names=sorted(i.name for i in instances if i.family in power_families)
    audit={'schema_version':1,'status':'PASS - source/netlist connectivity gates only; unvalidated draft',
           'instance_count':len(instances),'module_count':len(module_instance_names),
           'module_instances':module_instance_names,
           'power_instance_count':len(power_instance_names),
           'power_instances':power_instance_names,
           'other_instance_count':len(instances)-len(module_instance_names)-len(power_instance_names),
           'panel_uid_count':len(bound),'designator_count':len(refs),
           'sensitive_nets':sensitive,
           'internal_cross_island_sensitive_nets':[x['net'] for x in sensitive if len(x['islands'])>1],
           'islands':{k:sorted(set(v)) for k,v in sorted(islands.items())},
           'multi_unit_packages':unit_audit,
           'note':'Internal sensitive nets crossing named islands are listed; panel-connected sensitive nets must stay within one island. Explicit NC pins are counted but no electrical behavior is qualified.'}
    stats={'schema_version':1,'source':'KiCad 10.0.6 exported master netlist plus design/spec/instrument.py',
           'status':'PASS - connectivity statistics, not hardware validation',
           'family_count':len(families),'instance_count':len(instances),
           'module_instance_count':len(module_instance_names),
           'power_instance_count':len(power_instance_names),
           'other_instance_count':len(instances)-len(module_instance_names)-len(power_instance_names),
           'module_instances':module_instance_names,'power_instances':power_instance_names,
           'component_count':len(specified),
           'components_by_type':dict(sorted(by_symbol.items())),
           'components_by_prefix':dict(sorted(by_prefix.items())),
           'components_by_instance':dict(sorted(per_instance.items())),
           'IC_count_by_part':dict(sorted(ic_by_part.items())),
           'net_count':len(nets),'pins_per_net_distribution':{str(k):v for k,v in sorted(distribution.items())},
           'panel_part_count':panel_count,'island_count':len(islands),
           'sensitive_net_count':len(sensitive),'multi_unit_package_count':len(unit_audit)}
    return audit,stats


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    a,s=check(*specification(),args.netlist.read_text())
    for path,data in [(ROOT/'design/reports/master-audit.json',a),(ROOT/'design/reports/netlist-stats.json',s)]:
        body=json.dumps(data,indent=2,ensure_ascii=False)+'\n'
        if args.check:
            if path.read_text()!=body:raise ValueError(f'drift: {path}')
        else:path.write_text(body)
    print('PASS: source-defined hierarchy',a['instance_count'],'instances;',a['module_count'],'fixed signal modules;',
          a['power_instance_count'],'power interface instances;',s['component_count'],'unique components;',
          s['net_count'],'nets;',len(a['sensitive_nets']),'sensitive nets; 438 panel UIDs')

if __name__=='__main__':main()
