"""Stage56 host step: synchronise footprint fields on the disposable candidate PCB.

Usage: pcb_fields.py INPUT_PCB OUTPUT_PCB SCHEMATIC_RECEIPT RECEIPT_JSON
Edits only top-level `(property ...)` blocks of named footprints: sets `Decouples` on the
retained bypasses and synchronises each dropped ambiguous unit field the way the board
renderer emits it: Role and Island are always rendered (as "" once dropped), so they are
set to ""; LogicalCellKey is not rendered, so it is deleted. Every other byte is kept.
"""
import hashlib, json, re, sys
from pathlib import Path

src, dst, sch, out = map(Path, sys.argv[1:5])
assert not dst.exists() and not out.exists(), 'refuse overwrite'
schematic = json.loads(sch.read_text())
retained = {r['ref']: r['new_decouples'] for r in schematic['retained_bypasses']}
dropped = {}
for ref, field in schematic['dropped_unit_fields']['pairs']:
    dropped.setdefault(ref, set()).add(field)
RENDERED_EMPTY = {'Role', 'Island'}  # scripts/schgen/core.py ATTRIBUTES default to ''
text = src.read_text()


def block_end(s, start):
    depth, i, quoted = 0, start, False
    while True:
        ch = s[i]
        if quoted:
            if ch == '\\': i += 1
            elif ch == '"': quoted = False
        elif ch == '"': quoted = True
        elif ch == '(': depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1


footprints = [m.start()+1 for m in re.finditer(r'\n\t\(footprint ', text)]
changes, pieces, last = [], [], 0
seen = set()
for start in footprints:
    end = block_end(text, start)
    body = text[start:end]
    ref = re.search(r'\n\t\t\(property "Reference" "([^"]+)"', body)
    if not ref or (ref.group(1) not in retained and ref.group(1) not in dropped):
        continue
    ref = ref.group(1); seen.add(ref)
    new, pos = [], 0
    for m in re.finditer(r'\n\t\t\(property "([^"]+)" "((?:[^"\\]|\\.)*)"', body):
        name, value = m.group(1), m.group(2)
        p_start = m.start() + 1
        p_end = block_end(body, p_start + 2)
        if p_start < pos:
            continue
        if name in dropped.get(ref, ()) and name in RENDERED_EMPTY:
            new.append(body[pos:m.start()]); new.append(f'\n\t\t(property "{name}" ""'); pos = m.end()
            changes.append({'ref': ref, 'field': name, 'old': value, 'new': ''})
        elif name in dropped.get(ref, ()):
            new.append(body[pos:m.start()]); pos = p_end
            changes.append({'ref': ref, 'field': name, 'old': value, 'new': None})
        elif name == 'Decouples' and ref in retained:
            new.append(body[pos:m.start()]); new.append(f'\n\t\t(property "Decouples" "{retained[ref]}"'); pos = m.end()
            changes.append({'ref': ref, 'field': name, 'old': value, 'new': retained[ref]})
    new.append(body[pos:])
    pieces.append(text[last:start]); pieces.append(''.join(new)); last = end
pieces.append(text[last:])
result = ''.join(pieces)
want = sum(len(v) for v in dropped.values())
removed = sum(1 for c in changes if c['field'] != 'Decouples')
assert seen == set(retained) | set(dropped), 'footprint roster'
assert sum(1 for c in changes if c['field'] == 'Decouples') == len(retained), 'Decouples updates'
assert removed == want, 'every requested field synchronised'
dst.write_text(result)
receipt = {'input_sha256': hashlib.sha256(src.read_bytes()).hexdigest(), 'output_sha256': hashlib.sha256(dst.read_bytes()).hexdigest(),
           'requested_field_syncs': want, 'field_syncs': removed,
           'deleted': sum(1 for c in changes if c['new'] is None), 'emptied': sum(1 for c in changes if c['new'] == ''),
           'requested_fields_absent_on_pcb': want - removed, 'decouples_updates': len(retained), 'changes': changes}
out.write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
print(f'PASS fields: {removed}/{want} synchronised (absent: {want-removed}), {len(retained)} Decouples updated')
