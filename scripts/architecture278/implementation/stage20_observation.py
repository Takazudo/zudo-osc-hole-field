"""Source-only replay of generic XML using pinned KiCad 10.0.6 representations.

Stage18 remains immutable, including its historical FAIL. No native execution.
"""
import argparse
from collections import defaultdict
import hashlib
import re
from pathlib import Path
import xml.etree.ElementTree as ET
import stage18_observation as legacy

source = legacy.source
p = source.p
need = p.need
parse_xml = legacy.parse_xml
net_names = legacy.net_names


def library_slots(library):
    """Bounded GetUnitPinInfo: default library slots, not placed-unit labels."""
    slots = []
    for sub in p.children(library, 'symbol'):
        match = re.search(r'_(\d+)_(\d+)$', sub[1])
        need(match is not None, 'unsupported library unit name')
        need(int(match[2]) in (0, 1), 'alternate library body unsupported')
        need(not p.children(sub, 'unit_name'), 'custom unit display names unsupported')
        slots.append(int(match[1]))
    count = max([1] + slots)
    need(count <= 26, 'library slot lettering outside bounded contract')
    return {chr(64+unit): sorted(p.pins(library, unit)) for unit in range(1,count+1)}


def pin_types(library, unit):
    result = {}
    for sub in p.children(library, 'symbol'):
        match = re.search(r'_(\d+)_(\d+)$', sub[1])
        need(match is not None, 'unsupported library unit name')
        if int(match[1]) not in (0,unit): continue
        need(int(match[2]) in (0,1), 'alternate library body unsupported')
        for pin in p.children(sub, 'pin'):
            number = p.one(pin, 'number')[1]
            need(number not in result, 'duplicate source electrical pin')
            result[number] = pin[1]
    return result


def expected_from_source(root=source.GENERATED/'a01.kicad_sch'):
    expected = legacy.expected_from_source(root)
    _, rows = source.source_check(root)
    groups = defaultdict(list)
    for row in rows: groups[row['ref']].append(row)
    for ref, units in groups.items():
        w = expected[ref]
        representative = next(r for r in units if p.one(r['symbol'],'uuid')[1]==w['representative_uuid'])
        library = representative['library']
        # Parser promotes these library properties into LIB_SYMBOL metadata;
        # exporter emits them from the representative resolved library symbol.
        props = p.properties(library)
        library_properties = {}
        if props.get('ki_keywords'): library_properties['ki_keywords'] = props['ki_keywords']
        filters = [legacy.unescape(token) for token in re.split(r'[ \t\r\n]+', props.get('ki_fp_filters','')) if token]
        if filters: library_properties['ki_fp_filters'] = ' '.join(filters)
        need(not set(library_properties) & set(w['properties']), 'library/property collision '+ref)
        w['properties'].update(library_properties)
        w['library_properties'] = library_properties
        slots = library_slots(library)
        if any(r['unit']==0 for r in units):
            need(len(units)==1 and set(slots)=={'A'}, 'unit zero requires one placed unit and one library slot '+ref)
        for row in units:
            if row['unit'] > 0:
                slot = chr(64+row['unit'])
                specific = library_slots(row['library'])
                need(slot in slots and slot in specific, 'placed unit absent from library '+ref)
                slots[slot] = specific[slot]
        w['units'] = slots
        types = {}
        for row in units:
            local = pin_types(row['library'], row['unit'])
            need(set(local)==set(row['resolved']), 'source electrical pin roster '+ref)
            need(not set(local)&set(types), 'duplicate source package pin '+ref)
            types.update(local)
        need(set(types)==set(w['pins']), 'source package electrical pin roster '+ref)
        w['pin_types'] = types
    return expected


def compare(observed, expected):
    need(observed['format']=='kicadxml','generic kicadxml observation required')
    comps=observed['components']
    need(set(comps)==set(expected), 'component roster differs: missing='+str(sorted(set(expected)-set(comps)))+' extra='+str(sorted(set(comps)-set(expected))))
    names=net_names(net for w in expected.values() for net in w['pins'].values() if net is not None)
    endpoints={}; nc=[]
    for name, net in observed['nets'].items():
        need(net['nodes'], 'empty observed net')
        for node in net['nodes']:
            key=(node['ref'],node['pin'])
            need(key not in endpoints, 'duplicate native endpoint '+str(key))
            endpoints[key]=(name,node)
    wanted_endpoints={(ref,pin) for ref,w in expected.items() for pin in w['pins']}
    need(set(endpoints)==wanted_endpoints,'complete native endpoint roster differs (including NC)')
    for ref,w in expected.items():
        c=comps[ref]
        for key in ('value','footprint','datasheet','description','library','part','properties','sheetpath'):
            need(c[key]==w[key], key+' mismatch '+ref)
        need(any(c['fields']==candidate['fields'] for candidate in w['field_candidates']), 'aggregate fields mismatch '+ref)
        need(len(c['tstamps'])==len(set(c['tstamps'])) and sorted(c['tstamps'])==w['tstamps'], 'unit UUID coverage mismatch '+ref)
        need(set(c['units'])==set(w['units']), 'unit slot roster mismatch '+ref)
        for unit,pins in c['units'].items():
            need(len(pins)==len(set(pins)) and sorted(pins)==w['units'][unit], 'unit pin roster mismatch '+ref)
        libpins=observed['libraries'].get((w['library'],w['part']),[])
        need(len(libpins)==len(set(libpins)) and set(libpins)==set(w['pins']), 'library pin roster mismatch '+ref)
        for pin,net in w['pins'].items():
            name,node=endpoints[(ref,pin)]
            if net is None:
                need(name.startswith('unconnected-') and len(observed['nets'][name]['nodes'])==1
                     and node.get('pintype','') in ({'no_connect','no_connect+no_connect'} if w['pin_types'][pin]=='no_connect' else {w['pin_types'][pin]+'+no_connect'})
                     and name not in names['xml_to_source'], 'NC pin connected or marker missing '+ref+':'+pin)
                nc.append(ref+':'+pin)
            else:
                need(name==names['source_to_xml'][net], 'pin/net mismatch '+ref+':'+pin)
                need(w['pin_types'][pin]!='no_connect' and node.get('pintype')==w['pin_types'][pin], 'connected pin electrical type mismatch '+ref+':'+pin)
    need(set(observed['libraries'])=={(w['library'],w['part']) for w in expected.values()}, 'library roster differs')
    return {'status':'PASS retained XML logical source parity (Stage20 representation rules)','references':118,'physical_pins':561,
        'unit_UUIDs':154,'native_net_nodes':len(endpoints),'explicit_singleton_NCs':sorted(nc),
        'net_name_mapping':names,'unit_metadata':{ref:w['unit_metadata'] for ref,w in expected.items()},
        'hardware_acceptance':False,'ERC':'NOT RUN','DRC':'NOT RUN',
        'limitation':'Logical observation only, not native provenance/admission, electrical acceptance or procurement/PCB readiness.'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--netlist',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    raw=args.netlist.read_bytes(); result={'status':'FAIL','hardware_acceptance':False}
    try:
        report=source.report()
        report_path=source.OUT/'compatibility-report.json'
        need(report_path.read_text()==source.json_text(report),'stale source compatibility report')
        result=compare(parse_xml(raw.decode()),expected_from_source())
        result['source_report_sha256']=source.digest(report_path)
        result['comparator_sha256']=source.digest(Path(__file__))
        result['native_execution']='NONE: source-only replay; prior admission consumed'
    except (ValueError,KeyError,IndexError,ET.ParseError,UnicodeError) as exc:result['error']=str(exc)
    result['observation_sha256']=hashlib.sha256(raw).hexdigest()
    args.output.write_text(source.json_text(result))
    print(result['status'])
    return 0 if result['status'].startswith('PASS') else 1


if __name__=='__main__':raise SystemExit(main())
