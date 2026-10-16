"""Strict XML observation parser/comparator. Does not execute or admit native tools."""
import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import stage18_compat as source
p = source.p
need = p.need
MANDATORY = {'Reference','Value','Footprint','Datasheet','Description'}
TOKENS = dict(dblquote='"', quote="'", lt='<', gt='>', backslash='\\', slash='/',
              bar='|', comma=',', colon=':', space=' ', dollar='$', tab='\t',
              **{'return':'\n', 'brace':'{'})


def unescape(value):
    """KiCad 10.0.6 common/string_utils.cpp, UnescapeString (single recursive pass)."""
    result = ''
    i = 0
    previous = ''
    while i < len(value):
        char = value[i]
        if char != '{':
            result += char
            previous = char
            i += 1
            continue
        start = i + 1
        depth = 1
        i += 1
        while i < len(value):
            if value[i] == '{': depth += 1
            elif value[i] == '}': depth -= 1
            if depth == 0: break
            i += 1
        token = value[start:i]
        terminated = i < len(value)
        if not terminated:
            result += '{' + unescape(token)
        elif previous in ('$', '~', '^', '_'):
            result += '{' + unescape(token) + '}'
        elif token in TOKENS:
            result += TOKENS[token]
        else:
            result += '{' + unescape(token) + '}'
        previous = '}' if terminated else (value[-1] if value else '')
        i += 1
    return result


def net_names(names):
    """Retain both directions; refuse lossy aliases before comparing any observation."""
    forward = {}
    reverse = {}
    escaped = {}
    for name in sorted(set(names)):
        # Source text -> CTX_NETNAME -> generic XML UnescapeString, never decode XML twice.
        raw = name.replace('/', '{slash}').replace('\r','').replace('\n','')
        decoded = unescape(raw)
        need(decoded not in reverse or reverse[decoded]==name, 'net-name unescaping collision: '+repr(name))
        forward[name] = decoded
        reverse[decoded] = name
        escaped[name] = raw
    return {'source_to_xml':forward, 'xml_to_source':reverse, 'source_to_internal':escaped}


def one(node, tag):
    items = node.findall(tag)
    need(len(items)==1, 'expected one XML '+tag)
    return items[0]


def optional_text(node, tag):
    items=node.findall(tag)
    need(len(items)<=1, 'duplicate XML '+tag)
    return (items[0].text or '') if items else ''


def mapping(items, key, value):
    result={}
    for item in items:
        name=key(item)
        need(name not in result, 'duplicate XML member '+str(name))
        result[name]=value(item)
    return result


def parse_xml(text):
    need('<!DOCTYPE' not in text.upper() and '<!ENTITY' not in text.upper(), 'XML declarations/entities unsupported')
    root=ET.fromstring(text)
    need(root.tag=='export' and root.get('version')=='E', 'expected KiCad XML export E')
    design=one(root,'design')
    need(one(design,'tool').text=='Eeschema 10.0.6', 'observation requires exact KiCad 10.0.6')
    def component(c):
        lib=one(c,'libsource'); sheet=one(c,'sheetpath')
        return {'value':optional_text(c,'value'), 'footprint':optional_text(c,'footprint'),
            'datasheet':optional_text(c,'datasheet'), 'description':optional_text(c,'description'),
            'library':lib.attrib['lib'], 'part':lib.attrib['part'],
            'properties':mapping(c.findall('property'),lambda x:x.attrib['name'],lambda x:x.get('value','')),
            'fields':mapping(one(c,'fields').findall('field'),lambda x:x.attrib['name'],lambda x:x.text or ''),
            'tstamps':(one(c,'tstamps').text or '').split(),
            'sheetpath':dict(sheet.attrib),
            'units':mapping(one(c,'units').findall('unit'),lambda x:x.attrib['name'],
                lambda x:[pin.attrib['num'] for pin in one(x,'pins').findall('pin')])}
    comps=mapping(one(root,'components').findall('comp'),lambda x:x.attrib['ref'],component)
    libs=mapping(one(root,'libparts').findall('libpart'),lambda x:(x.attrib['lib'],x.attrib['part']),
        lambda x:[pin.attrib['num'] for pin in one(x,'pins').findall('pin')])
    nets=mapping(one(root,'nets').findall('net'),lambda x:x.attrib['name'],
        lambda x:{'code':x.attrib['code'],'nodes':[dict(n.attrib) for n in x.findall('node')]})
    need(len({n['code'] for n in nets.values()})==len(nets), 'duplicate net code')
    return {'format':'kicadxml','components':comps,'libraries':libs,'nets':nets}


def aggregate_fields(units, per_unit, representative_unit):
    need(len(units)<=5, 'unsupported aggregation search size')
    outcomes={}
    for order in itertools.permutations(range(len(units))):
        fields={}
        minimum=representative_unit
        for index in order:
            unit=units[index]['unit']
            for key,value in per_unit[index].items():
                if key not in MANDATORY and (unit<minimum or key not in fields):fields[key]=value
            minimum=min(unit,minimum)
        decoded={unescape(k):unescape(v) for k,v in fields.items()}
        need(len(decoded)==len(fields), 'field-name unescaping collision')
        decoded.update({k:unescape(per_unit[0].get(k,'')) for k in ('Footprint','Datasheet','Description')})
        signature=source.json_text(decoded)
        outcomes.setdefault(signature,{'fields':decoded,'one_feasible_traversal':[units[i]['unit'] for i in order]})
    return [outcomes[k] for k in sorted(outcomes)]


def expected_from_source(root=source.GENERATED/'a01.kicad_sch'):
    _, rows=source.source_check(root)
    docs=dict(p.hierarchy(root)); groups=defaultdict(list); sheets={}
    for sh in p.children(docs[root.resolve()],'sheet'):
        props=p.properties(sh)
        sheets[(root.parent/props['Sheetfile']).resolve()]={
            'properties':props, 'names':'/'+props['Sheetname']+'/',
            'tstamps':'/'+p.one(sh,'uuid')[1]+'/'}
    for row in rows:groups[row['ref']].append(row)
    expected={}
    for ref, units in sorted(groups.items()):
        units=sorted(units,key=lambda r:r['unit'])
        representative=min(units,key=lambda r:p.one(r['symbol'],'uuid')[1])
        sheet=sheets[representative['sheet']]
        def shown(props):
            result={k:v.replace('${SHEETNAME}',sheet['properties']['Sheetname']) for k,v in props.items()}
            need(not any('${' in v for v in result.values()), 'unsupported source text variable '+ref)
            return result
        per_unit=[shown(r['properties']) for r in units]
        # EE_RTREE traversal is spatial, not file/unit order. Retain whole-dictionary
        # outcomes of the pinned running-minimum algorithm, never per-field value bags.
        for key in MANDATORY:
            need(len({props.get(key,'') for props in per_unit})==1, 'nonuniform mandatory field '+ref)
        candidates = aggregate_fields(units, per_unit, representative['unit'])
        fields = candidates[0]['fields']
        props={k:v for k,v in shown(representative['properties']).items() if k not in MANDATORY}
        need(not (set(props)&set(sheet['properties'])), 'sheet/property collision '+ref)
        props.update(sheet['properties'])
        for key,flag in (('in_bom','exclude_from_bom'),('on_board','exclude_from_board')):
            if p.one(representative['symbol'],key)[1]=='no': props[flag]=''
        if p.one(representative['symbol'],'dnp')[1]=='yes':props['dnp']=''
        pins={pin:net for r in units for pin,net in r['resolved'].items()}
        expected[ref]={'value':unescape(per_unit[0]['Value']) or '~',
            'footprint':fields['Footprint'],'datasheet':fields['Datasheet'],'description':fields['Description'],
            'library':representative['lib_id'].split(':')[0], 'part':representative['lib_id'].split(':')[1],
            'properties':props,'field_candidates':candidates,'pins':pins,
            'tstamps':sorted(p.one(r['symbol'],'uuid')[1] for r in units),
            'sheetpath':{k:sheet[k] for k in ('names','tstamps')},
            'units':{chr(64+r['unit']):sorted(r['resolved']) for r in units},
            'representative_uuid':p.one(representative['symbol'],'uuid')[1],
            'unit_metadata':{str(r['unit']):{'uuid':p.one(r['symbol'],'uuid')[1],
                'properties':r['properties'],'pins':r['resolved']} for r in units}}
    need(len(expected)==118 and sum(len(w['pins']) for w in expected.values())==561
         and sum(len(w['tstamps']) for w in expected.values())==154, 'complete source contract')
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
                     and node.get('pintype','').endswith('+no_connect')
                     and name not in names['xml_to_source'], 'NC pin connected or marker missing '+ref+':'+pin)
                nc.append(ref+':'+pin)
            else:
                need(name==names['source_to_xml'][net], 'pin/net mismatch '+ref+':'+pin)
                need(not node.get('pintype','').endswith('+no_connect'), 'connected pin marked NC '+ref+':'+pin)
    need(set(observed['libraries'])=={(w['library'],w['part']) for w in expected.values()}, 'library roster differs')
    return {'status':'PASS complete XML logical source parity','references':118,'physical_pins':561,
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
    except (ValueError,KeyError,IndexError,ET.ParseError,UnicodeError) as exc:result['error']=str(exc)
    result['observation_sha256']=hashlib.sha256(raw).hexdigest()
    args.output.write_text(source.json_text(result))
    print(result['status'])
    return 0 if result['status'].startswith('PASS') else 1


if __name__=='__main__':raise SystemExit(main())
