"""Independent source S-expression connectivity audit; never invokes KiCad.

Derives actual pin positions from embedded symbols and actual wires/labels/NC.
This is a bounded source-format check, not native ERC or netlist validation.
"""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]


def need(ok, message):
    if not ok:
        raise ValueError(message)


def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    def expression(i):
        need(i < len(tokens) and tokens[i] == '(', 'expected expression')
        row = []; i += 1
        while i < len(tokens) and tokens[i] != ')':
            if tokens[i] == '(':
                child, i = expression(i); row.append(child)
            else:
                row.append(json.loads(tokens[i]) if tokens[i].startswith('"') else tokens[i]); i += 1
        need(i < len(tokens), 'unclosed expression')
        return row, i + 1
    result, end = expression(0)
    need(end == len(tokens), 'trailing expressions')
    return result


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def one(node, key):
    rows = children(node, key)
    need(len(rows) == 1, 'expected one ' + key)
    return rows[0]


def properties(node):
    rows = children(node, 'property')
    need(len({r[1] for r in rows}) == len(rows), 'duplicate property')
    return {r[1]: r[2] for r in rows}


def xy(node):
    a = one(node, 'at'); p = tuple(round(float(x), 6) for x in a[1:3])
    need(all(math.isfinite(x) for x in p), 'nonfinite coordinate')
    return p


def pins(library, unit):
    result = {}
    need(not children(library, 'extends'), 'unresolved inherited library')
    for sub in children(library, 'symbol'):
        match = re.search(r'_(\d+)_(\d+)$', sub[1])
        need(match is not None, 'unrecognized library unit')
        if int(match[1]) not in (0, unit):
            continue
        need(int(match[2]) in (0, 1), 'alternate body unsupported')
        for pin in children(sub, 'pin'):
            number = one(pin, 'number')[1]
            need(number not in result, 'duplicate physical pin in library unit')
            result[number] = xy(pin)
    need(result, 'empty physical symbol unit')
    return result


def world(local, symbol):
    a = one(symbol, 'at'); angle = float(a[3]) if len(a) > 3 else 0
    need(angle in (0, 90, 180, 270), 'unsupported symbol angle')
    need(not children(symbol, 'mirror'), 'mirrored symbol unsupported')
    x, y = local
    for _ in range(int(angle // 90)):
        x, y = -y, x
    return round(float(a[1]) + x, 6), round(float(a[2]) - y, 6)


def on_segment(point, a, b):
    x, y = point; ax, ay = a; bx, by = b
    return abs((x-ax)*(by-ay)-(y-ay)*(bx-ax)) < 1e-8 and min(ax,bx)-1e-8 <= x <= max(ax,bx)+1e-8 and min(ay,by)-1e-8 <= y <= max(ay,by)+1e-8


def table(root, filename):
    root = root.resolve()
    p = root / filename
    need(p.is_file(), 'missing library table ' + str(p))
    result = {}
    for row in children(parse(p.read_text()), 'lib'):
        name = one(row, 'name')[1]; uri = one(row, 'uri')[1]
        need(name not in result, 'duplicate library nickname')
        uri = uri.replace('${KIPRJMOD}', str(root))
        target = Path(uri)
        if not target.is_absolute(): target = root / target
        need(target.resolve().is_relative_to(root.resolve()), 'library escapes isolated root')
        result[name] = target
    return result


def audit_documents(documents):
    """Return actual physical pins and properties, with named-net connectivity."""
    parents = {}; points = set(); wire_rows = []; labels = []; ncs = []; instances = []
    def find(k):
        parents.setdefault(k, k)
        if parents[k] != k: parents[k] = find(parents[k])
        return parents[k]
    def union(a, b): parents[find(a)] = find(b)
    for path, tree in documents:
        embedded = {x[1]: x for x in children(one(tree, 'lib_symbols'), 'symbol')}
        need(len(embedded) == len(children(one(tree, 'lib_symbols'), 'symbol')), 'duplicate embedded library')
        def point(p):
            k = (str(path), *p); points.add(k); return k
        for sym in children(tree, 'symbol'):
            props = properties(sym); ref = props.get('Reference'); unit = int(one(sym, 'unit')[1]); lib = one(sym, 'lib_id')[1]
            need(ref and lib in embedded, 'unbound instance')
            actual = {pin: point(world(pos, sym)) for pin,pos in pins(embedded[lib], unit).items()}
            declared = [p[1] for p in children(sym, 'pin')]
            need(Counter(declared) == Counter(actual.keys()), 'instance physical pin UUID inventory differs ' + ref)
            instances.append({'ref':ref,'unit':unit,'lib_id':lib,'library':embedded[lib],'properties':props,'pins':actual,'symbol':sym,'sheet':Path(path).resolve()})
        for kind in ('label','global_label'):
            for node in children(tree, kind):
                labels.append((point(xy(node)), ('global' if kind == 'global_label' else str(path), node[1]), node[1]))
        need(not children(tree, 'hierarchical_label') and not children(tree, 'bus') and not children(tree, 'bus_entry'), 'unsupported connectivity construct')
        for node in children(tree, 'no_connect'): ncs.append(point(xy(node)))
        for node in children(tree, 'junction'): point(xy(node))
        for node in children(tree, 'wire'):
            coords = children(one(node, 'pts'), 'xy'); need(len(coords) == 2, 'wire needs two endpoints')
            a,b = [point(tuple(round(float(v),6) for v in c[1:3])) for c in coords]
            need(a != b, 'zero length wire'); wire_rows.append((a,b))
    for a,b in wire_rows:
        union(a,b)
        for p in points:
            if p[0] == a[0] and on_segment(p[1:], a[1:], b[1:]): union(a,p)
    named = {}
    for p,key,_ in labels:
        if key in named: union(p,named[key])
        else: named[key] = p
    component_labels = defaultdict(set)
    for p,_,name in labels: component_labels[find(p)].add(name)
    for names in component_labels.values(): need(len(names) == 1, 'shorted distinct named nets')
    nc_counts = Counter(ncs); pin_counts = Counter(p for row in instances for p in row['pins'].values())
    wire_points = {p for a,b in wire_rows for p in points if p[0] == a[0] and on_segment(p[1:], a[1:], b[1:])}
    all_pin_points = set(pin_counts)
    label_points = [p for p,_,_ in labels]
    need(all(n == 1 for n in Counter(label_points).values()), 'duplicate labels at connection')
    need(set(label_points) <= all_pin_points | wire_points, 'orphan circuit label')
    need(set(ncs) <= all_pin_points, 'orphan NC marker')
    for row in instances:
        resolved = {}
        for pin,p in row['pins'].items():
            names = component_labels.get(find(p), set())
            if nc_counts[p]:
                need(nc_counts[p] == 1 and pin_counts[p] == 1 and p not in wire_points and not names, 'NC marker connected to circuit')
                resolved[pin] = None
            else:
                need(len(names) == 1, 'unlabelled or disconnected physical pin '+row['ref']+':'+pin)
                resolved[pin] = next(iter(names))
        row['resolved'] = resolved
    return instances


def hierarchy(path):
    root = path.parent.resolve(); visited = set(); documents = []
    def visit(p):
        p = p.resolve(); need(p.is_relative_to(root), 'sheet escapes isolated root'); need(p not in visited, 'duplicate/cyclic sheet')
        visited.add(p); tree = parse(p.read_text()); need(tree[0] == 'kicad_sch','wrong schematic root'); documents.append((p,tree))
        for sheet in children(tree, 'sheet'):
            need(not children(sheet, 'pin'), 'hierarchical sheet pin unsupported')
            visit(p.parent / properties(sheet)['Sheetfile'])
    visit(path)
    uuids = []
    def collect(node):
        if isinstance(node,list):
            if node and node[0] == 'uuid': uuids.append(node[1])
            for child in node: collect(child)
    for _,tree in documents: collect(tree)
    need(len(uuids) == len(set(uuids)), 'duplicate schematic UUID')
    return documents


def transport_expected(inputs):
    """Independent projection of frozen graph; never imports transport emitter."""
    graph=inputs['transport_contract']; result={}; represented=set()
    mechanical=json.loads((ROOT/'design/architecture-278/implementation/stage10/mechanical-report.json').read_text())
    def add(ref, pinmap, nodes, mpn, manufacturer, value, footprint, kind, fitted=True):
        need(set(pinmap)==set(nodes),'transport endpoint coverage')
        for pin,node in nodes.items():
            need(node not in represented and graph['nodes'][node]['net']==pinmap[pin],'transport graph bijection')
            represented.add(node)
        result[ref]={'pins':pinmap,'selected_mpn':mpn,'selected_manufacturer':manufacturer,
            'unit_records':[{'unit':1,'pins':pinmap,'value':value}], 'symbol':{'paths':[]},
            'footprint':{'path':footprint},'extra_package_pins_outside_element_units':{},
            '_transport':True,'_fitted':fitted,'_source_nodes':nodes,'_kind':kind}
    for i,(source,header) in enumerate(sorted(graph['headers'].items()),17901):
        add('J'+str(i),header['pins'],{pin:source+':'+pin for pin in header['pins']},
            header['header_mpn'],'JST',header['header_mpn'],header['source'],'GH')
    for i,side in enumerate(('middle','rear'),17909):
        source='A01:DIN:'+side
        selected={n:v for n,v in graph['nodes'].items() if v['kind']=='DIN' and v['ref']==source}
        pins={v['pin']:v['net'] for v in selected.values()};nodes={v['pin']:n for n,v in selected.items()}
        mpn=mechanical['din_connectors'][side]['mpn']
        add('J'+str(i),pins,nodes,mpn,'HARTING',mpn,None,'DIN')
    tails=sorted((n,v) for n,v in graph['nodes'].items() if v['kind'] in ('terminal_land','LED_wire_land'))
    for i,(node,v) in enumerate(tails,17901):
        add('TP'+str(i),{v['pin']:v['net']},{v['pin']:node},None,None,'Source land: '+node,None,v['kind'],False)
    need(represented=={n for n,v in graph['nodes'].items() if v['kind']!='source'},'complete transport graph partition')
    need(len(result)==32 and sum(len(r['pins']) for r in result.values())==270,'transport counts')
    return result


def check(schematic_path, inputs, asset_root=None):
    path = Path(schematic_path); root = Path(asset_root) if asset_root else path.parent
    documents = hierarchy(path); instances = audit_documents(documents); expected = {**inputs['packages'],**transport_expected(inputs)}
    trees = {file:tree for file,tree in documents}; paths = {}
    def bind(file, instance_path):
        paths[file] = instance_path
        for sheet in children(trees[file],'sheet'):
            project = one(one(sheet,'instances'),'project')
            need(project[1] == path.stem and one(project,'path')[1] == instance_path, 'sheet hierarchy instance mismatch')
            child = (file.parent/properties(sheet)['Sheetfile']).resolve()
            bind(child,instance_path+'/'+one(sheet,'uuid')[1])
    bind(path.resolve(),'/'+one(trees[path.resolve()],'uuid')[1])
    need({r['ref'] for r in instances} == set(expected), 'exact circuit population differs')
    symbols = table(root, 'sym-lib-table'); footprints = table(root, 'fp-lib-table')
    observed = defaultdict(dict); unit_sets = defaultdict(set); external_cache = {}
    for row in instances:
        ref = row['ref']; p = expected[ref]; props = row['properties']; unit = row['unit']
        symbol = row['symbol']
        fitted='yes' if p.get('_fitted',True) else 'no'
        for key,value in (('in_bom',fitted),('on_board',fitted),('dnp','no'),('exclude_from_sim','no')):
            need(one(symbol,key)[1] == value,'circuit population flag mismatch '+ref)
        project = one(one(symbol,'instances'),'project'); instance = one(project,'path')
        need(project[1] == path.stem and instance[1] == paths[row['sheet']], 'symbol hierarchy instance mismatch '+ref)
        need(one(instance,'reference')[1] == ref and int(one(instance,'unit')[1]) == unit, 'symbol instance reference/unit mismatch '+ref)
        record = next((u for u in p['unit_records'] if int(u['unit']) == unit), None)
        wanted_value = record['value'] if record else p['unit_records'][0]['value']
        need(props.get('Value') == wanted_value, 'unit value mismatch '+ref)
        need(unit not in unit_sets[ref], 'duplicate symbol unit '+ref); unit_sets[ref].add(unit)
        wanted_pins = next((u['pins'] for u in p['unit_records'] if int(u['unit']) == unit), None)
        if unit == 5 and p['extra_package_pins_outside_element_units']: wanted_pins = p['extra_package_pins_outside_element_units']
        need(wanted_pins is not None and row['resolved'] == wanted_pins, 'symbol unit pin assignment mismatch '+ref)
        need(row['lib_id'] == ('A01Transport:A01_' if p.get('_transport') else 'A01Candidate:A01_')+ref, 'wrong exact per-reference symbol binding '+ref)
        need(not set(observed[ref]) & set(row['resolved']), 'physical pin repeated across units '+ref)
        observed[ref].update(row['resolved'])
        if p.get('_transport'):
            need(json.loads(props.get('SourceGraphNodes','{}'))==p['_source_nodes'],'actual transport graph mapping differs '+ref)
            need(props.get('SourceRole')=='TRANSPORT','transport source role missing '+ref)
            need(props.get('SourceKind')==p['_kind'],'transport source kind differs '+ref)
            need(props.get('FootprintStatus')==('RETAINED_SOURCE_FOOTPRINT' if p['footprint']['path'] else 'UNBOUND_SCHEMATIC_ONLY'),'transport footprint disposition missing '+ref)
        need((props.get('MPN') or None) == p['selected_mpn'], 'MPN mismatch '+ref)
        need((props.get('Manufacturer') or None) == p['selected_manufacturer'], 'manufacturer mismatch '+ref)
        nickname,name = row['lib_id'].split(':',1); need(nickname in symbols,'symbol nickname not bound')
        libpath = symbols[nickname]
        if libpath not in external_cache: external_cache[libpath] = {n[1]:n for n in children(parse(libpath.read_text()),'symbol')}
        need(name in external_cache[libpath], 'external symbol missing')
        actual = list(row['library']); actual[1] = name
        need(actual == external_cache[libpath][name], 'embedded/external symbol mismatch '+ref)
        defaults = properties(actual)
        need((defaults.get('MPN') or None)==p['selected_mpn'] and (defaults.get('Manufacturer') or None)==p['selected_manufacturer'], 'library default identity mismatch '+ref)
        for key in ('in_bom','on_board'):
            flags=children(actual,key)
            need(not flags or (len(flags)==1 and flags[0][1]==fitted),'library population flag mismatch '+ref)
        def signatures(definition):
            return {(int(sub[1].rsplit('_',2)[1]),one(pin,'number')[1]):pin for sub in children(definition,'symbol') for pin in children(sub,'pin')}
        sig = signatures(actual)
        if p['symbol']['paths']:
            source = one(parse((ROOT/p['symbol']['paths'][0]).read_text()),'symbol')
            need(sig == signatures(source),'retained symbol pin specification drift '+ref)
        else:
            for (pinunit,number),pin in sig.items():
                need(pin[1]=='passive','new candidate pin electrical type drift '+ref)
                if ref in inputs['capacitor_overrides']:
                    need(one(pin,'name')[1] == {'1':'+','2':'-'}[number], 'capacitor symbol polarity drift')
                elif number == '9' and not p.get('_transport'): need(pinunit==5 and one(pin,'name')[1]=='EP_SHIELD','network shield symbol drift')
        fp = props.get('Footprint','')
        if p.get('_transport') and p['footprint']['path'] is None:
            need(fp=='' and defaults.get('Footprint','')=='','unbound transport footprint invented '+ref)
            continue
        need(':' in fp,'missing footprint binding '+ref)
        need(defaults.get('Footprint')==fp,'library default footprint mismatch '+ref)
        fn,member = fp.split(':',1); need(fn in footprints,'footprint nickname not bound')
        cap = inputs['capacitor_overrides'].get(ref)
        wanted_member = 'KEMET_'+p['selected_mpn'] if cap else Path(p['footprint']['path']).stem
        need(fp == 'A01Candidate:'+wanted_member, 'wrong exact candidate footprint binding '+ref)
        file = footprints[fn] / (member+'.kicad_mod'); need(file.resolve().is_relative_to(root.resolve()),'footprint escapes root')
        footprint_tree = parse(file.read_text())
        if not cap:
            source_tree = parse((ROOT/p['footprint']['path']).read_text())
            for model in children(source_tree,'model'):
                model[1] = '${KIPRJMOD}/3dmodels/'+Path(model[1]).name
            need(footprint_tree == source_tree, 'retained footprint source geometry drift '+ref)
        else:
            geometry = cap['geometry']
            for pad in children(footprint_tree,'pad'):
                n = pad[1]; need(n in geometry['pads_mm'], 'unexpected capacitor pad')
                need(list(xy(pad)) == geometry['pads_mm'][n], 'capacitor pad position drift')
                need([float(v) for v in one(pad,'size')[1:]] == geometry['pad_sizes_mm'][n], 'capacitor land size drift')
                need(pad[2:4] == ['smd','rect'] and one(pad,'layers')[1:] == ['F.Cu','F.Paste','F.Mask'], 'capacitor pad type/layers drift')
            courtyard = [rect for rect in children(footprint_tree,'fp_rect') if one(rect,'layer')[1] == 'F.CrtYd']
            need(len(courtyard)==1, 'capacitor courtyard missing')
            need([float(x) for key in ('start','end') for x in one(courtyard[0],key)[1:]] == geometry['courtyard_mm'], 'capacitor courtyard drift')
        pad_rows = children(footprint_tree,'pad'); pad_names = {pad[1] for pad in pad_rows if pad[1]}
        need(pad_names == set(p['pins']), 'footprint physical pin coverage '+ref)
    for ref,p in expected.items():
        need(observed[ref] == p['pins'], 'derived physical pin/net mismatch '+ref)
        wanted = {int(u['unit']) for u in p['unit_records']}
        if p['extra_package_pins_outside_element_units']: wanted.add(5)
        need(unit_sets[ref] == wanted, 'unit coverage mismatch '+ref)
    return {'status':'PASS independent source-derived circuit pin/net/NC/library parity','packages':len(observed),'physical_pins':sum(map(len,observed.values())),'circuit_packages':len(inputs['packages']),'circuit_pins':sum(len(x['pins']) for x in inputs['packages'].values()),'transport_components':32,'transport_pins':270,'symbol_units':len(instances),'native':'NOT RUN','ERC':'NOT RUN','hardware_acceptance':False,'scope':'Source format and connectivity only; not KiCad-import, native netlist or electrical acceptance.'}


def check_transport(path, inputs):
    seen = []
    for _,tree in hierarchy(Path(path)):
        need(not children(tree,'symbol'),'transport diagram not circuit hierarchy')
        labels = defaultdict(list)
        for kind in ('label','global_label'):
            for node in children(tree,kind): labels[xy(node)].append(node[1])
        endpoints = Counter()
        for wire in children(tree,'wire'):
            coords = children(one(wire,'pts'),'xy'); need(len(coords)==2,'transport wire endpoints')
            names = []
            for coord in coords:
                at = tuple(round(float(v),6) for v in coord[1:3]); need(len(labels[at])==1,'transport endpoint label missing/duplicate')
                endpoints[at] += 1; names.append(labels[at][0])
            seen.append(tuple(sorted(names)))
        need(set(labels)==set(endpoints) and all(n==1 for n in endpoints.values()),'orphan label or shared transport diagram endpoint')
    graph = inputs['transport_contract']
    want = [tuple(sorted((e['from'],e['to']))) for e in graph['edges']]
    need(Counter(seen)==Counter(want),'transport edge topology differs')
    need(json.loads((Path(path).parent/'transport-source.json').read_text())==graph,'complete transport source roster differs')
    return {'edge_diagram_segments':len(seen),'node_roster':len(graph['nodes']),'physical_transport_materialized':False,'scope':'Separate source allocation edge diagram and exact node roster; not circuit connector netlist or routed copper.'}
