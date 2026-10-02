#!/usr/bin/env python3
"""Generate the isolated, unselected monitor/permit test schematic."""
import argparse
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.schgen.core import Family, Instance, LibrarySymbol, Part, Pin, render, _prop, designator
from design.spec.cells._builder import load_symbol

SPEC = ROOT/'design/power/monitor-permit-draft.json'
OUTPUT = ROOT/'schematic/candidates/monitor-permit'


def supply_symbol():
    name = 'IdealTestSources'
    pins = tuple(Pin(str(i), -10.16, 3.81-(i-1)*2.54, 0, 'power_out') for i in range(1,5))
    body = (f'(symbol "monitor-study:{name}" (in_bom no) (on_board no)\n'
            ' (property "Reference" "J" (at 0 7.62 0) (effects (font (size 1.27 1.27))))\n'
            ' (property "Value" "IDEAL TEST SOURCES" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))\n'
            f' (symbol "{name}_1_1" (rectangle (start -7.62 6.35) (end 7.62 -6.35) '
            '(stroke (width 0.254) (type default)) (fill (type background)))\n')
    for pin, label in zip(pins, ('+12 test','negative test','+5 test','test return')):
        body += (f' (pin power_out line (at {pin.x} {pin.y:g} 0) (length 2.54) '
                 f'(name "{label}" (effects (font (size 1.27 1.27)))) '
                 f'(number "{pin.number}" (effects (font (size 1.27 1.27)))))\n')
    return LibrarySymbol('monitor-study:'+name, body+' ))', {1:pins})


def specification():
    spec = json.loads(SPEC.read_text())
    if spec['canonical_protection_implemented'] or spec['qualification_accepted']:
        raise ValueError('isolated draft cannot admit canonical protection')
    catalog = json.loads((ROOT/spec['source_catalog']).read_text())['parts']
    exact = {p['mpn']:p for p in catalog}
    selected = {p['mpn']:(p['symbol'],p['footprint'],p['manufacturer']) for p in catalog}
    needed = {p['mpn'] for p in spec['components']}
    inventory = json.loads((ROOT/'.claude/skills/component-spec-audit/references/inventory.json').read_text())
    for line in inventory['lines']:
        if line['mpn'] in selected or line['mpn'] not in needed:
            continue
        bundle = ROOT/'.claude/skills'/line['owner_skill']
        manifest = json.loads((bundle/'manifest.json').read_text())
        record = next(r for r in manifest['records'] if r['line_id']==line['line_id'])
        mapping = next(p for p in json.loads((bundle/'pin-map.json').read_text())['pin_maps']
                       if p['record_id']==record['record_id'])
        selected[line['mpn']] = (mapping['symbol'],mapping['footprint'],line['manufacturer'])
    library = {}; parts = []; positions = {1:0,2:0}; seen = set()
    for component in spec['components']:
        ref = component['ref']
        evidence = exact.get(component['mpn'])
        if evidence and component['kind'] != evidence['kind']:
            raise ValueError('candidate kind differs from exact catalog: '+ref)
        if component['kind'] in ('resistor','capacitor'):
            value = component.get('value')
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value <= 0:
                raise ValueError('invalid passive value: '+ref)
        if evidence and component['kind']=='resistor' and component['value'] != evidence['resistance_ohm']:
            raise ValueError('resistance differs from exact MPN: '+ref)
        if evidence and component['kind']=='capacitor' and component['value'] != evidence['capacitance_F']:
            raise ValueError('capacitance differs from exact MPN: '+ref)
        if ref in seen:
            raise ValueError('duplicate candidate reference')
        seen.add(ref)
        name, footprint, manufacturer = selected[component['mpn']]
        symbol = load_symbol(name); library[symbol.lib_id] = symbol
        actual = {pin.number for pins in symbol.units.values() for pin in pins}
        if set(component['pins']) != actual:
            raise ValueError('incomplete physical pin capture: '+ref)
        match = re.fullmatch(r'([A-Z]+)(\d+)', ref)
        if not match:
            raise ValueError('invalid reference')
        ordinal = int(match[2])-100
        value = component['mpn']
        if component['kind']=='resistor': value = f"{component['value']:g} ohm"
        if component['kind']=='capacitor': value = f"{component['value']*1e9:g} nF"
        for unit, pins in sorted(symbol.units.items()):
            if not pins:
                continue
            page = component['page']; index = positions[page]; positions[page] += 1
            parts.append(Part(key=ref+'.'+str(unit), symbol=symbol.lib_id, prefix=match[1],
                ordinal=ordinal, unit=unit, x=30.48+(index%5)*76.2, y=35.56+(index//5)*38.1,
                pins={p.number:component['pins'][p.number] for p in pins}, value=value,
                footprint='zudo-osc-hole-field:'+footprint, page=page,
                attributes={'MPN':component['mpn'],'Manufacturer':manufacturer,
                            'Role':'UNSELECTED DRAFT: '+component['role']}))
    source = supply_symbol(); library[source.lib_id] = source
    index = positions[1]
    parts.append(Part(key='J101',symbol=source.lib_id,prefix='J',ordinal=1,unit=1,
        x=30.48+(index%5)*76.2,y=35.56+(index//5)*38.1,pins=spec['ideal_test_supply']['pins'],
        value='IDEAL TEST SOURCES / NOT AN INLET', in_bom=False,on_board=False,abstract=True,
        attributes={'Implementation':'REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE',
                    'Role':spec['ideal_test_supply']['scope']}))
    family = Family('MonitorPermit',tuple(parts),tuple(spec['global_nets']),paper='A3')
    return (family,), (Instance('MonitorPermit','MONITOR',1),), library


def generated_files():
    spec = json.loads(SPEC.read_text())
    families, instances, library = specification()
    files = render(families, instances, library, spec['project'])
    title = ('\n  (title_block (title "UNSELECTED monitor/permit test draft") (rev "WIP") '
             '(comment 1 "NOT ORDERABLE / NOT ENERGIZABLE; no installed protection"))')
    for path in files:
        if path.endswith('.kicad_sch'):
            for inst in instances:
                family = next(f for f in families if f.name==inst.family)
                for part in family.parts:
                    for key, value, old_y, new_y in (
                        ('Reference',designator(part,inst),part.y-3,part.y-11.43),
                        ('Value',part.value or part.symbol.split(':')[-1],part.y+3,part.y+11.43)):
                        files[path] = files[path].replace(
                            _prop(key,value,part.x+3,old_y),_prop(key,value,part.x,new_y))
            files[path] = re.sub(r'  \(paper "[^"]+"\)',lambda m:m[0]+title,files[path],count=1)
    files[spec['project']+'.kicad_pro'] = json.dumps({'meta':{'filename':spec['project']+'.kicad_pro','version':1},
        'sheets':[],'text_variables':{}},indent=2)+'\n'
    files['sym-lib-table'] = ('(sym_lib_table (version 7)\n'
        ' (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../../symbols/zudo-osc-hole-field.kicad_sym") (options "") (descr "Project source symbols"))\n'
        ' (lib (name "monitor-study") (type "KiCad") (uri "${KIPRJMOD}/monitor-study.kicad_sym") (options "") (descr "Nonphysical test assumptions only")))\n')
    source = supply_symbol().body.replace('(symbol "monitor-study:IdealTestSources"','(symbol "IdealTestSources"',1)
    files['monitor-study.kicad_sym'] = '(kicad_symbol_lib (version 20231120) (generator "zudo_monitor_study")\n'+source+'\n)\n'
    files['fp-lib-table'] = ('(fp_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") '
        '(uri "${KIPRJMOD}/../../../footprints/kicad/zudo-osc-hole-field.pretty") (options "") (descr "Unqualified family footprints")))\n')
    return files


def run(check=False):
    for name, text in generated_files().items():
        path = OUTPUT/name
        if check:
            if not path.exists() or path.read_text()!=text:
                raise ValueError('monitor/permit schematic drift: '+name)
        else:
            path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)
    print('Generated isolated monitor/permit draft; qualification remains OPEN')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    run(parser.parse_args().check)
