"""Deterministic isolated A01 source schematic; never invokes KiCad or a simulator."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import stage11_assessment as common
import stage16_handoff as previous
import stage17_assets as assets
import stage17_transport as transport_components

ROOT = common.ROOT
OUT = ROOT / 'design/architecture-278/implementation/stage17'
GENERATED = OUT / 'generated'
BASE = '4c4b42267d435bea38bee8196910d48f9f43f202'
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
import core
need = common.need


def inputs():
    path = previous.OUT / 'inputs-report.json'
    inp = json.loads(path.read_text())
    common.bindings(inp)
    return inp


def library_objects(text, namespace="A01Candidate"):
    """Retain original token quoting while extracting merged library symbols."""
    toks = core.tokens(text)
    root, end = core.parse(toks)
    need(end == len(toks) and root[0] == 'kicad_symbol_lib', 'symbol library root')
    result = {}; depth = 0; start = None
    for i, tok in enumerate(toks):
        if tok == '(':
            if depth == 1 and toks[i+1] == 'symbol': start = i
            depth += 1
        elif tok == ')':
            depth -= 1
            if depth == 1 and start is not None:
                node, _ = core.parse(toks[start:i+1]); name = node[1]
                units = {}
                for child in core.children(node, 'symbol'):
                    unit = int(child[1].rsplit('_', 2)[1]); pins = []
                    for pin in core.children(child, 'pin'):
                        at = core.children(pin, 'at')[0]
                        pins.append(core.Pin(core.children(pin, 'number')[0][1], float(at[1]), float(at[2]), int(at[3]), pin[1]))
                    units[unit] = tuple((*units.get(unit, ()), *pins))
                units = {u: pins for u, pins in units.items() if pins}
                lib_id = namespace + ':' + name
                body = '(' + ' '.join([toks[start+1], core.q(lib_id), *toks[start+3:i+1]])
                need(lib_id not in result, 'duplicate library symbol')
                result[lib_id] = core.LibrarySymbol(lib_id, body, units)
                start = None
    return result


def circuit(inp, files, bindings, transport_rows):
    library = library_objects(files['A01Candidate.kicad_sym'])
    library.update(library_objects(files['A01Transport.kicad_sym'], 'A01Transport'))
    parts = []
    for ref, row in sorted({**inp['packages'], **transport_rows}.items()):
        binding = bindings[ref]; sym = library[binding['symbol_lib_id']]
        records = {int(u['unit']): u for u in row['unit_records']}
        for unit, pins in sorted(sym.units.items()):
            n = len(parts); page, slot = divmod(n, 20)
            # Deliberately independent schematic layout, not physical PCB coordinates.
            x, y = 90 + (slot % 4)*195, 65 + (slot//4)*100
            record = records.get(unit)
            need(record is not None or (ref.startswith('RN') and unit == 5), 'unexpected logical unit')
            attrs = dict(record.get('attributes', {})) if record else {}
            attrs.update(MPN=row['selected_mpn'] or '', Manufacturer=row['selected_manufacturer'] or '',
                         IdentityStatus=row['identity_status'], SourceRef=ref,
                         SourceBoard=row['placement']['board'], CandidateStatus='UNVALIDATED SOURCE CANDIDATE')
            pinmap = {p.number: row['pins'][p.number] for p in pins}
            value = record['value'] if record else row['unit_records'][0]['value']
            if record is None: attrs['Role'] = 'exposed pad shield; AGND; not resistor common'
            parts.append(core.Part(key=f'{ref}.{unit}', symbol=sym.lib_id, prefix=ref.rstrip('0123456789'),
                ordinal=1, unit=unit, x=x, y=y, pins=pinmap, value=value,
                footprint=binding['footprint_lib_id'], attributes=attrs, panel_ref=ref, page=page+1,
                in_bom=row.get('in_bom', True), on_board=row.get('on_board', True)))
    need(len(parts) == 154, '120 logical units plus two EP and32 transport units')
    family = core.Family('a01-circuit', tuple(parts), global_nets=tuple(sorted(inp['nets'])), paper='A1')
    return core.render((family,), (core.Instance('a01-circuit', 'A01', 71),), library, project='a01')


def transport(inp):
    """Separate source graph drawing, never a component/assembly/netlist substitute."""
    result = {}; edges = inp['transport_contract']['edges']; rootid = core.uid('a01-transport-root')
    root = core._header('a01-transport-root', [], 'A1')
    root.append('  (text "SOURCE ALLOCATION GRAPH ONLY - NOT PHYSICAL CONNECTOR CAPTURE OR ROUTED COPPER" (at 30 20 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid '+core.q(core.uid('transport-warning'))+'))')
    for page, offset in enumerate(range(0, len(edges), 40), 1):
        name = f'transport/edges-{page:02d}.kicad_sch'; key = f'transport-edges-{page}'
        lines = core._header(key, [], 'A1')
        for index, edge in enumerate(edges[offset:offset+40], offset):
            slot = index-offset; x = 90+(slot%2)*400; y=35+(slot//2)*26
            for endpoint, dx in [('from', 0), ('to', 220)]:
                lines.append(core._label(edge[endpoint], x+dx, y, 0 if dx == 0 else 180, f'transport:{index}:{endpoint}', True))
            lines.append(f'  (wire (pts (xy {x} {y}) (xy {x+220} {y})) (stroke (width 0) (type default)) (uuid {core.q(core.uid("transport-wire:"+str(index)))}))')
            title = f'EDGE {index}: {edge["kind"]}; allocated {edge["allocated_developed_mm"]:.6f} mm; copper UNKNOWN'
            lines.append(f'  (text {core.q(title)} (at {x} {y+5} 0) (effects (font (size 0.9 0.9)) (justify left)) (uuid {core.q(core.uid("transport-note:"+str(index)))}))')
        lines += ['  (embedded_fonts no)', ')']
        result[name]='\n'.join(lines)+'\n'
        x=30+((page-1)%4)*190; y=60+((page-1)//4)*50
        root += [f'  (sheet (at {x} {y}) (size 170 25)',
                 '    (exclude_from_sim yes) (in_bom no) (on_board no) (dnp no)',
                 '    (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0))',
                 f'    (uuid {core.q(core.uid("transport-sheet:"+key))})',
                 core._prop('Sheetname', f'Source edges {offset}-{min(offset+39,len(edges)-1)}',x,y-1),
                 core._prop('Sheetfile',name,x,y+26),
                 f'    (instances (project "transport-graph" (path {core.q("/"+rootid)} (page "{page+1}"))))', '  )']
    root += ['  (sheet_instances (path "/" (page "1")))', '  (embedded_fonts no)', ')']
    result['transport-graph.kicad_sch']='\n'.join(root)+'\n'
    result['transport-source.json']=json.dumps(inp['transport_contract'],sort_keys=True,indent=2,allow_nan=False)+'\n'
    return result


def build_files(inp=None):
    inp = inputs() if inp is None else inp
    files, bindings = assets.build_assets(inp)
    files = dict(files)
    extra, transport_bindings, transport_rows = transport_components.build_transport(inp)
    files.update(extra)
    files['sym-lib-table'] = files['sym-lib-table'].rstrip()[:-1] + '\n  (lib (name \"A01Transport\") (type \"KiCad\") (uri \"${KIPRJMOD}/A01Transport.kicad_sym\") (options \"\") (descr \"Isolated logical transport source\")))\n'
    files.update(circuit(inp, files, {**bindings, **transport_bindings}, transport_rows)); files.update(transport(inp))
    files['asset-bindings.json']=json.dumps(bindings,sort_keys=True,indent=2,allow_nan=False)+'\n'
    return files


def preserve():
    scope=json.loads((OUT/'scope.json').read_text())
    names=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,*common.PREFIXES],cwd=ROOT,text=True).splitlines())-common.MUTABLE
    need(scope['baseline_commit']==BASE and set(scope['preserved_prior_source_sha256'])==names,'historical inventory')
    for name,sha in scope['preserved_prior_source_sha256'].items():
        need(common.digest(ROOT/name)==sha==hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest(),'preserved '+name)
    return len(names)


def predecessor():
    preserve()
    need((previous.OUT/'handoff-report.json').read_text()==json.dumps(previous.build(),sort_keys=True,indent=2,allow_nan=False)+'\n','historical Stage16 report')
    for role in ('root','code','electrical'):
        receipt=json.loads((previous.OUT/('review-'+role+'.json')).read_text())
        need(receipt.get('independent_review') and receipt.get('authorship_exclusion'),'historical review attribution')
        for name,sha in receipt['source_sha256'].items():
            actual=hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest() if name in common.MUTABLE else common.digest(ROOT/name)
            need(actual==sha,'historical review binding '+name)


def write_files(files, destination=GENERATED, check=False):
    existing={str(p.relative_to(destination)) for p in destination.rglob('*') if p.is_file()} if destination.exists() else set()
    need(not existing-set(files),'unexpected generated files')
    for name, text in files.items():
        path=destination/name
        need(not Path(name).is_absolute() and '..' not in Path(name).parts and path.resolve().is_relative_to(destination.resolve()),'unsafe generated path')
        if check:
            need(path.is_file() and path.read_text()==text,'generated drift '+name)
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)


def report(files):
    import stage17_parity
    inp=inputs()
    circuit_check=stage17_parity.check(GENERATED/'a01.kicad_sch',inp,GENERATED)
    transport_check=stage17_parity.check_transport(GENERATED/'transport-graph.kicad_sch',inp)
    bound=[ROOT/'design/architecture-278/implementation/stage5/din-evidence.json',ROOT/'design/architecture-278/implementation/stage10/mechanical-report.json',previous.OUT/'inputs-report.json',OUT/'scope.json',ROOT/'scripts/schgen/core.py',
           ROOT/'scripts/architecture278/implementation/check_source.py',ROOT/'design/architecture-278/implementation/STAGE17.md']
    bound += sorted((ROOT/'scripts/architecture278/implementation').glob('*stage17*.py'))
    for binding in json.loads(files['asset-bindings.json']).values():
        bound += [ROOT/p for p in binding['source_symbol_paths']]
        if binding['source_footprint_path']: bound.append(ROOT/binding['source_footprint_path'])
        bound += [ROOT/model['source'] for model in binding['models']]
    for binding in json.loads(files['transport-asset-bindings.json']).values():
        bound.append(ROOT/binding['source'])
        bound += [ROOT/model['source'] for model in binding['models']]
    bound = sorted(set(bound))
    return {'status':'ISOLATED SCHEMATIC SOURCE GENERATED; NATIVE ACCEPTANCE UNVERIFIED',
        'baseline_commit':BASE,'preserved_predecessor_files':preserve(),'circuit_source_parity':circuit_check,
        'transport_source_diagram_parity':transport_check,'prototype_availability':'UNCONFIRMED',
        'unresolved_exact_MPNs':[ref for ref,p in inp['packages'].items() if p['selected_mpn'] is None],
        'native':'NOT RUN','ERC':'NOT RUN','DRC':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN',
        'native_admission_granted':False,'hardware_acceptance':False,'PCB_materialized':False,
        'generated_sha256':{name:hashlib.sha256(text.encode()).hexdigest() for name,text in sorted(files.items())},
        'source_sha256':{str(p.relative_to(ROOT)):common.digest(p) for p in bound}}


def reviews():
    for role,required in {'code':{'stage17_schematic.py','stage17_assets.py','stage17_transport.py'},'electrical':{'stage17_schematic.py','stage17_parity.py'},'root':{'stage17_assets.py','stage17_parity.py','stage17_transport.py'}}.items():
        r=json.loads((OUT/f'review-{role}.json').read_text());common.bindings(r)
        need(r.get('independent_review') and r.get('authorship_exclusion'),'review authorship')
        need(required<={Path(n).name for n in r['source_sha256']},'review coverage '+role)


def compare_historical_extract(actual, expected, new_paths):
    extra=set(actual['source_sha256'])-set(expected['source_sha256'])
    need(extra==set(new_paths), 'unexpected historical extraction source expansion')
    normalized={**actual, 'source_sha256':{k:v for k,v in actual['source_sha256'].items() if k not in extra}}
    need(normalized==expected, 'historical interface extraction drift')
    for name in new_paths:
        need(actual['source_sha256'][name]==common.digest(ROOT/name), 'new library source binding drift')


def packet_predecessor():
    sys.path.insert(0,str(ROOT))
    from scripts.architecture278 import check_packet, extract
    changed=subprocess.check_output(['git','diff','--name-only',check_packet.BASE],cwd=ROOT,text=True).splitlines()
    changed+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    check_packet.validate_paths(changed)
    expected=json.loads(extract.OUTPUT.read_text())
    # Historical scanner recursively collects every design/*.kicad_sym. Preserve
    # its complete old result while explicitly accounting for the two new libraries.
    new_paths=[str((GENERATED/name).relative_to(ROOT)) for name in ('A01Candidate.kicad_sym','A01Transport.kicad_sym')]
    # Stage16 local source-copy bundles are also under design/. Accept only
    # complete, independently reverified exports, never arbitrary ignored files.
    for manifest in sorted((previous.OUT/'runs').glob('*/manifest.json')):
        previous.verify_export(manifest.parent.name)
        copied=json.loads(manifest.read_text())['files']
        new_paths += [str((manifest.parent/name).relative_to(ROOT)) for name in copied if name.endswith('.kicad_sym')]
    compare_historical_extract(extract.build(), expected, new_paths)
    for name in ('ledger.py','mechanics.py','electrical.py','populated_mechanics.py','revision_electrical.py','orientation_sweep.py'):
        subprocess.run([sys.executable,str(ROOT/'scripts/architecture278'/name),'--check'],cwd=ROOT,check=True)
    print('PASS historical packet plus exact new library scanner inputs; no historical bytes rewritten')


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--check-predecessor',action='store_true');p.add_argument('--check-packet-predecessor',action='store_true');args=p.parse_args()
    if args.check_packet_predecessor:packet_predecessor();return
    if args.check_predecessor:predecessor();print('PASS frozen Stage16 evidence');return
    files=build_files();write_files(files,check=args.check)
    r=report(files);text=json.dumps(r,sort_keys=True,indent=2,allow_nan=False)+'\n';path=OUT/'schematic-report.json'
    if args.check:need(path.read_text()==text,'stale schematic report');reviews()
    else:path.write_text(text)
    print('PASS isolated source generation/parity; native acceptance NOT RUN')

if __name__=='__main__':main()
