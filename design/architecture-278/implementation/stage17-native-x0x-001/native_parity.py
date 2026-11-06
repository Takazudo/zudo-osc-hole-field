"""Independent frozen-source/native observation comparator. Never invokes KiCad."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys


def require(ok, message):
    if not ok:
        raise ValueError(message)


def expected_from_source(repo):
    sys.path.insert(0, str(repo/'scripts/architecture278/implementation'))
    import stage17_parity as p
    inp = json.loads((repo/'design/architecture-278/implementation/stage16/inputs-report.json').read_text())
    root = repo/'design/architecture-278/implementation/stage17/generated/a01.kicad_sch'
    p.check(root, inp)
    expected = {**inp['packages'], **p.transport_expected(inp)}
    units = defaultdict(list)
    for row in p.audit_documents(p.hierarchy(root)):
        units[row['ref']].append(p.one(row['symbol'], 'uuid')[1])
    require(len(expected)==118 and sum(len(x['pins']) for x in expected.values())==561, 'source count contract')
    require(sum(map(len, units.values()))==154, 'source unit contract')
    result = {}
    for ref, row in expected.items():
        fp = row['footprint']['path']
        if ref in inp['capacitor_overrides']:
            fp = 'KEMET_'+row['selected_mpn']
        elif fp:
            fp = Path(fp).stem
        result[ref] = {'pins':row['pins'], 'mpn':row['selected_mpn'] or '',
            'manufacturer':row['selected_manufacturer'] or '',
            'value':row['unit_records'][0]['value'],
            'footprint':('A01Candidate:'+fp) if fp else '',
            'library':'A01Transport' if row.get('_transport') else 'A01Candidate',
            'part':'A01_'+ref, 'tstamps':sorted(units[ref]),
            'fitted':row.get('_fitted', True)}
    return result, p


def compare(tree, expected, p):
    require(tree[0]=='export', 'not native export S-expression')
    comps = {}
    for node in p.children(p.one(tree,'components'),'comp'):
        ref=p.one(node,'ref')[1]
        require(ref not in comps, 'duplicate component '+ref)
        comps[ref]=node
    missing=sorted(set(expected)-set(comps)); extra=sorted(set(comps)-set(expected))
    # Never silently waive native omission of on_board=no source annotations.
    require(not missing and not extra, 'component roster differs; missing='+str(missing)+' extra='+str(extra)+'; source-land exclusion is not complete native parity')
    libraries={}
    for lib in p.children(p.one(tree,'libparts'),'libpart'):
        key=(p.one(lib,'lib')[1],p.one(lib,'part')[1])
        require(key not in libraries, 'duplicate native libpart')
        numbers=[p.one(x,'num')[1] for x in p.children(p.one(lib,'pins'),'pin')]
        require(len(numbers)==len(set(numbers)), 'duplicate native library pin')
        libraries[key]=set(numbers)
    observed={}; nc_omissions=[]; units=0
    for net in p.children(p.one(tree,'nets'),'net'):
        name=p.one(net,'name')[1]
        for node in p.children(net,'node'):
            key=(p.one(node,'ref')[1],p.one(node,'pin')[1])
            require(key not in observed, 'pin repeated in native nets '+str(key))
            require(key[0] in expected and key[1] in expected[key[0]]['pins'], 'unexpected native endpoint '+str(key))
            observed[key]=name
    for ref, wanted in expected.items():
        c=comps[ref]
        def optional(key):
            rows=p.children(c,key)
            require(len(rows)<=1, 'duplicate component field '+key)
            return rows[0][1] if rows else ''
        require(optional('value')==wanted['value'], 'value mismatch '+ref)
        require(optional('footprint')==wanted['footprint'], 'footprint mismatch '+ref)
        props={}
        for prop in p.children(c,'property'):
            name=p.one(prop,'name')[1]; vals=p.children(prop,'value')
            require(name not in props and len(vals)<=1, 'duplicate native property '+ref)
            props[name]=vals[0][1] if vals else ''
        fields=p.children(c,'fields')
        for group in fields:
            for field in p.children(group,'field'):
                name=p.one(field,'name')[1]
                value=field[-1] if isinstance(field[-1],str) else ''
                require(name not in props or props[name]==value, 'conflicting field '+ref)
                props[name]=value
        require(props.get('MPN','')==wanted['mpn'], 'MPN mismatch '+ref)
        require(props.get('Manufacturer','')==wanted['manufacturer'], 'manufacturer mismatch '+ref)
        src=p.one(c,'libsource'); key=(p.one(src,'lib')[1],p.one(src,'part')[1])
        require(key==(wanted['library'],wanted['part']), 'library identity mismatch '+ref)
        require(libraries.get(key)==set(wanted['pins']), 'complete library pin roster mismatch '+ref)
        stamps=p.one(c,'tstamps')[1:]
        require(sorted(stamps)==wanted['tstamps'], 'native unit UUID coverage mismatch '+ref)
        units+=len(stamps)
        if not wanted['fitted']:
            require('exclude_from_bom' in props and 'exclude_from_board' in props, 'source-land population flags absent '+ref)
        for pin, net in wanted['pins'].items():
            key=(ref,pin)
            if net is None:
                if key not in observed:
                    nc_omissions.append(ref+':'+pin)
                else:
                    # KiCad can include NC as unique unconnected-* singleton nets.
                    name=observed[key]
                    require(name.startswith('unconnected-') and list(observed.values()).count(name)==1, 'NC pin connected '+str(key))
            else:
                require(observed.get(key)==net, 'pin/net mismatch '+str(key)+' expected='+str(net)+' actual='+str(observed.get(key)))
    return {'status':'PASS native logical source parity', 'references':len(comps),
        'physical_pins':sum(len(x['pins']) for x in expected.values()), 'units':units,
        'native_net_nodes':len(observed), 'explicit_source_NC_omitted_from_native_nets':nc_omissions,
        'hardware_acceptance':False, 'ERC':'NOT RUN', 'DRC':'NOT RUN',
        'limitation':'Source/netlist parity only; unresolved MPNs and DIN/land footprints remain; no electrical or procurement/PCB acceptance.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--netlist',type=Path,required=True); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report={'status':'FAIL', 'hardware_acceptance':False}
    try:
        expected,p=expected_from_source(args.repo.resolve())
        report=compare(p.parse(args.netlist.read_text()),expected,p)
    except (ValueError,KeyError,IndexError) as exc:
        report['error']=str(exc)
    report['netlist_sha256']=hashlib.sha256(args.netlist.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    sys.exit(0 if report['status'].startswith('PASS') else 1)
