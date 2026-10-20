"""Structural diff of the canonical osc-core PCB and the Stage56 candidate PCB (both unfilled
source files, before any refill), as the basis for the 199-capped DRC types.

Classifies every top-level board item by (kind, uuid):
- removed items, with a conservative bounding box each;
- added items (must be none);
- changed items, which must be either zones whose text differs only in whitespace, or
  footprints whose text is identical once the hidden Role / LogicalCellKey / Island /
  Decouples property blocks are dropped, with each such block hidden on both sides.

Writes `evidence/capped-diff.json`, or checks it with `--check`.
Usage: capped_diff.py [--check]
"""
from pathlib import Path
from collections import Counter
import hashlib, json, math, re, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CANON = ROOT/'boards/osc-core/osc-core.kicad_pcb'
CAND = ROOT/'.circuit-cache/stage56/candidate/osc-core/osc-core.kicad_pcb'
FIELDS = ('Role', 'LogicalCellKey', 'Island', 'Decouples')
MARGIN = 1.0  # mm added to every removed-item box (clearances checked here are 0.25 mm or less)


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def require(ok, msg):
    if not ok:
        raise SystemExit('FAIL: '+msg)


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


def items(path):
    s = Path(path).read_text()
    out = {}
    for m in re.finditer(r'\n\t\((\w+)', s):
        a = m.start() + 1
        b = block_end(s, a)
        body = s[a:b]
        u = re.search(r'\n\t\t\(uuid "([^"]+)"\)|^\(\w+ [^\n]*\(uuid "([^"]+)"\)', body)
        uid = (u.group(1) or u.group(2)) if u else hashlib.sha256(body.encode()).hexdigest()
        out[(m.group(1), uid)] = body
    return out


def nums(text, tag): return [(float(x), float(y)) for x, y in re.findall(r'\(' + tag + r' (-?[\d.]+) (-?[\d.]+)', text)]


def bbox(kind, body):
    if kind == 'footprint':
        ox, oy = nums(body, 'at')[0]
        local = nums(body, 'start') + nums(body, 'end') + nums(body, 'xy') + nums(body, 'at')[1:]
        r = max((math.hypot(x, y) for x, y in local), default=0.0) + MARGIN
        return [ox - r, oy - r, ox + r, oy + r]
    pts = nums(body, 'start') + nums(body, 'end') + nums(body, 'at') + nums(body, 'mid')
    w = max([float(x) for x in re.findall(r'\((?:width|size) ([\d.]+)', body)] or [0.0])
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [min(xs) - w - MARGIN, min(ys) - w - MARGIN, max(xs) + w + MARGIN, max(ys) + w + MARGIN]


def drop_fields(body):
    kept, pos, hidden = [], 0, []
    for m in re.finditer(r'\n\t\t\(property "(' + '|'.join(FIELDS) + r')" ', body):
        a = m.start() + 1; b = block_end(body, a)
        kept.append(body[pos:m.start()]); pos = b
        hidden.append('(hide yes)' in body[a:b])
    kept.append(body[pos:])
    return ''.join(kept), hidden


def compute():
    a, b = items(CANON), items(CAND)
    removed = sorted(set(a) - set(b)); added = sorted(set(b) - set(a))
    changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    unexplained = []
    for k in changed:
        if k[0] == 'zone':
            if re.sub(r'\s+', '', a[k]) != re.sub(r'\s+', '', b[k]):
                unexplained.append(list(k))
        elif k[0] == 'footprint':
            ra, ha = drop_fields(a[k]); rb, hb = drop_fields(b[k])
            if re.sub(r'\s+', '', ra) != re.sub(r'\s+', '', rb) or not all(ha) or not all(hb):
                unexplained.append(list(k))
        else:
            unexplained.append(list(k))
    boxes = [{'kind': k[0], 'uuid': k[1], 'bbox_mm': [round(v, 3) for v in bbox(k[0], a[k])]} for k in removed]
    union = [min(x['bbox_mm'][0] for x in boxes), min(x['bbox_mm'][1] for x in boxes),
             max(x['bbox_mm'][2] for x in boxes), max(x['bbox_mm'][3] for x in boxes)]
    return {
        'status': 'Structural diff of canonical vs Stage56 candidate osc-core PCB (unfilled sources)',
        'canonical_sha256': sha(CANON), 'candidate_sha256': sha(CAND),
        'removed_counts': dict(Counter(k[0] for k in removed)), 'added_counts': dict(Counter(k[0] for k in added)),
        'changed_counts': dict(Counter(k[0] for k in changed)), 'changed_unexplained': unexplained,
        'removed_items': boxes, 'removed_union_bbox_mm': [round(v, 3) for v in union],
    }


if __name__ == '__main__':
    result = compute()
    body = json.dumps(result, indent=2, sort_keys=True)+'\n'
    path = HERE/'evidence/capped-diff.json'
    if '--check' in sys.argv:
        require(path.read_text() == body, 'capped diff replay drift')
    else:
        path.write_text(body)
    require(result['added_counts'] == {} and result['changed_unexplained'] == [], 'candidate adds or alters geometry')
    print('PASS diff:', result['removed_counts'], 'changed', result['changed_counts'], 'union bbox', result['removed_union_bbox_mm'])
