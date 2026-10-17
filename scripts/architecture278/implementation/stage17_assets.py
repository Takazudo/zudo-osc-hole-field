"""Isolated A01 library source assets from frozen geometry; no native invocation."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import stage16_inputs as previous

ROOT = previous.ROOT
OUT = previous.OUT.parent/'stage17'
LIB = 'A01Candidate'
need = previous.need
sexpr = previous.packages.a.c.sexpr
field = previous.packages.a.c.field


def quoted(value):
    return json.dumps(str(value), ensure_ascii=False)


def symbol_block(text):
    """Return the one top-level source symbol, retaining original lexical data."""
    root = sexpr(text)
    syms = [n for n in root if isinstance(n, list) and n and n[0] == 'symbol']
    need(len(syms) == 1, 'expected one retained source symbol')
    start = re.search(r'\(symbol\s+"', text).start()
    depth = 0; in_string = False; escaped = False
    for i in range(start, len(text)):
        char = text[i]
        if in_string:
            if escaped: escaped = False
            elif char == '\\': escaped = True
            elif char == '"': in_string = False
        elif char == '"': in_string = True
        elif char == '(': depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0: return text[start:i+1], syms[0][1]
    raise ValueError('unterminated source symbol')


def replace_property(text, name, value):
    pattern = r'(\(property\s+' + re.escape(quoted(name)) + r'\s+)"(?:\\.|[^"\\])*"'
    text, count = re.subn(pattern, lambda m: m[1] + quoted(value), text)
    need(count == 1, 'one property required: ' + name)
    return text


def clone_symbol(source, name, row, footprint):
    text, old = symbol_block(source)
    text = re.sub(r'(\(symbol\s+")' + re.escape(old) + r'((?:_\d+_\d+)?)"',
                  lambda m: m[1] + name + m[2] + '"', text)
    text = replace_property(text, 'MPN', row['selected_mpn'] or '')
    text = replace_property(text, 'Manufacturer', row['selected_manufacturer'] or '')
    text = replace_property(text, 'Footprint', footprint)
    text = replace_property(text, 'Value', row['selected_mpn'] or row['unit_records'][0]['value'])
    # Never inherit a supplier code belonging to the generic template identity.
    text = replace_property(text, 'LCSC', row['supplier_order_code'] or '')
    return text


def property_source(name, value, y=0, hidden=True):
    return f'(property {quoted(name)} {quoted(value)} (at 0 {y} 0) (effects (font (size 1.27 1.27)){" (hide yes)" if hidden else ""}))'


def pin(number, name, x, angle, kind='passive'):
    return f'(pin {kind} line (at {x} 0 {angle}) (length 2.54) (name {quoted(name)} (effects (font (size 1.27 1.27)))) (number {quoted(number)} (effects (font (size 1.27 1.27)))))'


def new_symbol(name, row, footprint, network=False):
    props = [property_source('Reference', 'RN' if network else 'C', 5.08, False),
             property_source('Value', row['selected_mpn'], -5.08, False),
             property_source('MPN', row['selected_mpn']), property_source('Manufacturer', row['selected_manufacturer']),
             property_source('Footprint', footprint), property_source('Datasheet', 'https://www.analog.com/media/en/technical-documentation/data-sheets/5400fc.pdf' if network else 'https://content.kemet.com/datasheets/KEM_T2005_T491.pdf'),
             property_source('LCSC', '')]
    units = []
    if network:
        for unit, pair in enumerate(previous.packages.PAIRS, 1):
            units.append(f'(symbol "{name}_{unit}_1" (rectangle (start -2.54 1.27) (end 2.54 -1.27) (stroke (width 0.254) (type default)) (fill (type background))) {pin(pair[0], "R"+str(unit), -5.08, 0)} {pin(pair[1], "R"+str(unit), 5.08, 180)})')
        units.append(f'(symbol "{name}_5_1" (rectangle (start -2.54 1.27) (end 2.54 -1.27) (stroke (width 0.254) (type default)) (fill (type background))) {pin("9", "EP_SHIELD", -5.08, 0)})')
    else:
        # Symbol artwork is not component geometry. Explicit polarity is carried by names and plus mark.
        units.append(f'(symbol "{name}_0_1" (rectangle (start -2.54 2.54) (end 2.54 -2.54) (stroke (width 0.254) (type default)) (fill (type background))) (text "+" (at -1.27 1.27 0) (effects (font (size 1.27 1.27)))) {pin("1", "+", -5.08, 0)} {pin("2", "-", 5.08, 180)})')
    return f'(symbol "{name}" (in_bom yes) (on_board yes)\n' + '\n'.join(props+units) + '\n)'


def cap_footprint(name, geometry):
    x1,y1,x2,y2 = geometry['courtyard_mm']
    text = f'(footprint "{name}" (version 20240108) (generator "stage17-source") (layer "F.Cu") (attr smd)\n'
    text += f'(fp_rect (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))\n'
    text += '(fp_text user "+" (at -1 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
    for number in ('1','2'):
        x,y = geometry['pads_mm'][number]; w,h = geometry['pad_sizes_mm'][number]
        text += f'(pad "{number}" smd rect (at {x} {y}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
    return text + ')\n'


def symbol_metadata(text):
    root = sexpr(text); pins = {}; units = set()
    for node in root:
        if not isinstance(node, list) or not node or node[0] != 'symbol': continue
        match = re.search(r'_(\d+)_(\d+)$', node[1])
        need(match is not None, 'unit name required')
        if int(match[2]) != 1: continue
        unit = int(match[1])
        for item in node:
            if not isinstance(item, list) or not item or item[0] != 'pin': continue
            number = field(item, 'number')[0]
            need(number not in pins, 'duplicate physical symbol pin ' + number)
            pins[number] = {'unit': unit, 'at': field(item, 'at'), 'name': field(item, 'name')[0], 'electrical_type': item[1]}
            units.add(unit)
    return sorted(units), pins


def localize_models(footprint, files):
    models = []
    for match in list(re.finditer(r'\(model "([^"]+)"', footprint)):
        raw = match[1]; prefix = '${KIPRJMOD}/../../'
        need(raw.startswith(prefix), 'unsupported retained model path ' + raw)
        path = raw[len(prefix):]
        need((ROOT/path).is_file(), 'retained model asset missing ' + path)
        relative = '3dmodels/' + Path(path).name; content = (ROOT/path).read_text()
        need(relative not in files or files[relative] == content, 'model filename collision')
        files[relative] = content
        footprint = footprint.replace(quoted(raw), quoted('${KIPRJMOD}/' + relative))
        models.append({'source': path, 'isolated_path': relative, 'sha256': hashlib.sha256(content.encode()).hexdigest()})
    return footprint, models


def build_assets(inp):
    """Return (relative generated path->text, per-reference binding map)."""
    files = {}; bindings = {}; definitions = []
    for ref,row in sorted(inp['packages'].items()):
        name = 'A01_' + ref
        iscap = ref in inp['capacitor_overrides']; isnetwork = ref in ('RN7101','RN7102')
        source = row['footprint']['path']
        footprint_name = 'KEMET_' + row['selected_mpn'] if iscap else Path(source).stem
        target = LIB + '.pretty/' + footprint_name + '.kicad_mod'
        if iscap:
            footprint = cap_footprint(footprint_name, inp['capacitor_overrides'][ref]['geometry'])
        else:
            footprint = (ROOT/source).read_text()
        footprint, models = localize_models(footprint, files)
        need(target not in files or files[target] == footprint, 'footprint filename collision')
        files[target] = footprint
        lib_id = LIB + ':' + footprint_name
        if iscap or isnetwork:
            symbol = new_symbol(name, row, lib_id, isnetwork)
            source_symbols = []
        else:
            source_symbols = row['symbol']['canonical_paths']
            need(len(source_symbols) == 1, 'one retained library symbol per physical package')
            symbol = clone_symbol((ROOT/source_symbols[0]).read_text(), name, row, lib_id)
        units,pins = symbol_metadata(symbol)
        need(set(pins) == set(row['pins']), 'symbol physical pin coverage ' + ref)
        definitions.append(symbol)
        bindings[ref] = {'symbol_lib_id': LIB + ':' + name, 'footprint_lib_id': lib_id,
            'symbol_units': units, 'pin_to_unit': {p:v['unit'] for p,v in pins.items()}, 'pins': pins,
            'unresolved_mpn': row['selected_mpn'] is None, 'selected_mpn': row['selected_mpn'],
            'source_symbol_paths': source_symbols, 'source_footprint_path': source, 'models': models,
            'native_validated': False, 'asset_status': 'GENERATED_SOURCE_ONLY',
            'model_status': 'COPIED_RETAINED_SOURCE_NOT_FIT_VERIFIED' if models else 'NO_3D_MODEL_CLAIMED',
            'geometry_scope': 'Frozen land/courtyard source; F.Paste/F.Mask follow full rectangular lands for KEMET as source capture only; process/mask/paste/assembly not qualified.' if iscap else 'Retained footprint copper/mask/paste/courtyard geometry unchanged; model path localized only.',
            'unit_scope': 'Four resistor units plus explicit isolated EP shield unit5. Pin9 AGND by instance, never resistor common.' if isnetwork else 'Retained physical pin/unit assignment.'}
    files[LIB+'.kicad_sym'] = '(kicad_symbol_lib (version 20231120) (generator "stage17-source")\n' + '\n'.join(definitions) + '\n)\n'
    files['sym-lib-table'] = '(sym_lib_table (lib (name "A01Candidate") (type "KiCad") (uri "${KIPRJMOD}/A01Candidate.kicad_sym") (options "") (descr "Source-only isolated A01 candidate")))\n'
    files['fp-lib-table'] = '(fp_lib_table (lib (name "A01Candidate") (type "KiCad") (uri "${KIPRJMOD}/A01Candidate.pretty") (options "") (descr "Source-only isolated A01 candidate")))\n'
    transport = {}
    for ref, header in sorted(inp['transport_contract']['headers'].items()):
        source = header['source']; text = (ROOT/source).read_text(); name = Path(source).stem
        localized, models = localize_models(text, files)
        target = LIB+'.pretty/'+name+'.kicad_mod'
        need(target not in files or files[target] == localized, 'transport footprint collision')
        files[target] = localized
        transport[ref] = {'footprint_lib_id': LIB+':'+name, 'source': source,
            'source_sha256': hashlib.sha256(text.encode()).hexdigest(), 'selected_header_mpn': header['header_mpn'],
            'native_validated': False, 'models': models, 'scope': 'Retained footprint copied with model path localized only; no assembled connector/harness or native board binding inferred.'}
    files['transport-asset-bindings.json'] = json.dumps(transport,sort_keys=True,indent=2)+'\n'
    return files, bindings


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    inp=json.loads((previous.OUT/'inputs-report.json').read_text()); files,bindings=build_assets(inp)
    files['asset-bindings.json']=json.dumps(bindings,sort_keys=True,indent=2)+'\n'
    for path,text in files.items():
        dest=OUT/'generated'/path
        if args.check: need(dest.read_text()==text, 'stale generated asset '+path)
        else: dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
    print('PASS86 isolated symbol bindings; source-only libraries, native NOT RUN')


if __name__=='__main__':main()
