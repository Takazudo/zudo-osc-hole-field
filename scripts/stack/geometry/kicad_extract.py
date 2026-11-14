"""Plain-Python footprint extract of a KiCad 10 board file, in panel coordinates.

Only footprint placement, courtyard and pad geometry are read. Tracks, vias,
zones and pad nets are ignored, so a routing-only change of a board leaves the
extract, and the canonical digest built from it, unchanged.

Geometry conventions follow the KiCad file format: footprint-local graphics are
stored unrotated (already mirrored for B.Cu), the footprint `(at x y a)` angle is
applied with KiCad's RotatePoint convention, and a pad's own `(at ...)` angle is
absolute. The panel frame is the board frame minus `frame.kicad_translation_mm`
of the placement lock.
"""
import math
import re

NUM = r'(-?\d+(?:\.\d+)?(?:[eE]-?\d+)?)'
AT_RE = re.compile(r'\n\t\t\(at ' + NUM + ' ' + NUM + '(?: ' + NUM + ')?\\)')
LAYER_RE = re.compile(r'\n\t\t\(layer "([^"]+)"\)')
PROP_RE = re.compile(r'\(property "([^"]+)" "([^"]*)"')
ITEM_START_RE = re.compile(r'\n\t\t\((fp_line|fp_rect|fp_poly|fp_circle|fp_arc|pad)\s')
XY_RE = re.compile(r'\(xy ' + NUM + ' ' + NUM + r'\)')
ROUND = 4


def rotate(x, y, angle_deg):
    t = math.radians(angle_deg)
    c, s = math.cos(t), math.sin(t)
    return x * c + y * s, -x * s + y * c


def _items(block):
    """Yield (kind, text) for each footprint child item at two-tab indent."""
    starts = [(m.start(), m.group(1)) for m in ITEM_START_RE.finditer(block)]
    for i, (pos, kind) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(block)
        yield kind, block[pos:end]


def _pt(text, key):
    m = re.search(r'\(' + key + ' ' + NUM + ' ' + NUM + r'\)', text)
    return (float(m.group(1)), float(m.group(2))) if m else None


def _layer(text):
    m = re.search(r'\(layer "([^"]+)"\)', text)
    return m.group(1) if m else None


def _graphic_points(kind, text):
    if kind in ('fp_line', 'fp_rect'):
        a, b = _pt(text, 'start'), _pt(text, 'end')
        if kind == 'fp_rect':
            return [a, (b[0], a[1]), b, (a[0], b[1])]
        return [a, b]
    if kind == 'fp_poly':
        return [(float(x), float(y)) for x, y in XY_RE.findall(text)]
    if kind == 'fp_circle':
        c, e = _pt(text, 'center'), _pt(text, 'end')
        r = math.hypot(e[0] - c[0], e[1] - c[1])
        return [(c[0] + r * math.cos(k * math.pi / 8), c[1] + r * math.sin(k * math.pi / 8)) for k in range(16)]
    if kind == 'fp_arc':
        return [p for p in (_pt(text, 'start'), _pt(text, 'mid'), _pt(text, 'end')) if p]
    return []


def _pad(text, x0, y0, angle, tx, ty):
    head = re.match(r'\n\t\t\(pad "([^"]*)" (\w+) (\w+)', text)
    at = re.search(r'\(at ' + NUM + ' ' + NUM + '(?: ' + NUM + r')?\)', text)
    size = re.search(r'\(size ' + NUM + ' ' + NUM + r'\)', text)
    drill = re.search(r'\(drill(?: oval)? ' + NUM + '(?: ' + NUM + ')?', text)
    layers = re.search(r'\(layers ([^)]*)\)', text)
    px, py = float(at.group(1)), float(at.group(2))
    pad_angle = float(at.group(3) or 0)
    sx, sy = (float(size.group(1)), float(size.group(2))) if size else (0.0, 0.0)
    bx, by = rotate(px, py, angle)
    t = math.radians(pad_angle)
    half_w = abs(sx / 2 * math.cos(t)) + abs(sy / 2 * math.sin(t))
    half_h = abs(sx / 2 * math.sin(t)) + abs(sy / 2 * math.cos(t))
    cx, cy = x0 + bx - tx, y0 + by - ty
    d = float(drill.group(1)) if drill else 0.0
    return {
        'number': head.group(1),
        'type': head.group(2),
        'shape': head.group(3),
        'center': [round(cx, ROUND), round(cy, ROUND)],
        'bbox': [round(cx - half_w, ROUND), round(cy - half_h, ROUND), round(cx + half_w, ROUND), round(cy + half_h, ROUND)],
        'drill': d,
        'layers': layers.group(1).replace('"', '').split() if layers else [],
    }


def parse_board(path, translation):
    """Return the footprint list of a board file in panel coordinates."""
    tx, ty = translation
    text = open(path, encoding='utf-8').read()
    starts = [m.start() for m in re.finditer(r'\n\t\(footprint "', text)]
    footprints = []
    for i, a in enumerate(starts):
        e = text.find('\n\t)', a + 1)
        block = text[a:e + 3]
        lib = re.match(r'\n\t\(footprint "([^"]*)"', block).group(1)
        layer = LAYER_RE.search(block).group(1)
        at = AT_RE.search(block)
        x0, y0, angle = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        head_end = block.find('\n\t\t(fp_')
        pad_pos = block.find('\n\t\t(pad ')
        cut = min(p for p in (head_end, pad_pos, len(block)) if p >= 0)
        props = dict(PROP_RE.findall(block[:cut] if cut > 0 else block))
        court = []
        pads = []
        for kind, item in _items(block):
            if kind == 'pad':
                pads.append(_pad(item, x0, y0, angle, tx, ty))
                continue
            lay = _layer(item)
            if lay not in ('F.CrtYd', 'B.CrtYd'):
                continue
            court += [rotate(px, py, angle) for px, py in _graphic_points(kind, item)]
        courtyard = None
        if court:
            courtyard = [round(x0 + min(p[0] for p in court) - tx, ROUND), round(y0 + min(p[1] for p in court) - ty, ROUND),
                         round(x0 + max(p[0] for p in court) - tx, ROUND), round(y0 + max(p[1] for p in court) - ty, ROUND)]
        footprints.append({
            'ref': props.get('Reference', ''),
            'lib': lib.split(':')[-1],
            'value': props.get('Value', ''),
            'side': 'F' if layer == 'F.Cu' else 'B',
            'origin': [round(x0 - tx, ROUND), round(y0 - ty, ROUND)],
            'angle': angle,
            'courtyard': courtyard,
            'pads': pads,
        })
    footprints.sort(key=lambda f: (f['ref'], f['origin']))
    return footprints
