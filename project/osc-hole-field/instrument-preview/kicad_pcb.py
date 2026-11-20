"""Streaming reader for native KiCad 10 ``.kicad_pcb`` files (read-only, stdlib only).

The board is never loaded as one S-expression tree. Top-level items are located by
their ``\\n\\t(`` line prefix, which pcbnew writes for every child of ``kicad_pcb``.
Tracks, vias and zone fills use targeted regular expressions; only footprints and
board graphics are parsed into small trees. A 92 MB board needs a few hundred MB.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

TOP = re.compile(rb'\n\t\(([a-z_]+)')
TOK = re.compile(rb'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')
NUM = rb'(-?[0-9.]+(?:e-?[0-9]+)?)'
SEG = {
    'start': re.compile(rb'\(start ' + NUM + rb' ' + NUM + rb'\)'),
    'mid': re.compile(rb'\(mid ' + NUM + rb' ' + NUM + rb'\)'),
    'end': re.compile(rb'\(end ' + NUM + rb' ' + NUM + rb'\)'),
    'width': re.compile(rb'\(width ' + NUM + rb'\)'),
    'layer': re.compile(rb'\(layer "([^"]+)"\)'),
}
VIA_AT = re.compile(rb'\(at ' + NUM + rb' ' + NUM + rb'\)')
VIA_SIZE = re.compile(rb'\(size ' + NUM + rb'\)')
VIA_DRILL = re.compile(rb'\(drill ' + NUM + rb'\)')
LAYERS = re.compile(rb'\(layers((?: "[^"]+")+)\)')
QUOTED = re.compile(rb'"([^"]+)"')
XY = re.compile(rb'\(xy ' + NUM + rb' ' + NUM + rb'\)')
LAYER_DEF = re.compile(rb'\n\t\t\((\d+) "([^"]+)" (signal|power|mixed|jumper|user)')


def _atom(tok: bytes):
    if tok[:1] == b'"':
        return tok[1:-1].decode('utf-8').replace('\\"', '"').replace('\\\\', '\\')
    return tok.decode('utf-8')


def parse_sexpr(chunk: bytes):
    """Parse one S-expression; returns nested lists of str atoms."""
    stack: list[list] = [[]]
    for m in TOK.finditer(chunk):
        t = m.group()
        if t == b'(':
            stack.append([])
        elif t == b')':
            done = stack.pop()
            stack[-1].append(done)
            if len(stack) == 1:
                break
        else:
            stack[-1].append(_atom(t))
    return stack[0][0]


def kids(node, name):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == name:
            return c
    return None


def rot(x, y, deg):
    """KiCad footprint-local to board offset; positive angle is counter-clockwise on screen (y down)."""
    if not deg:
        return x, y
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return x * c + y * s, -x * s + y * c


@dataclass
class Pad:
    shape: str
    kind: str
    x: float
    y: float
    angle: float
    w: float
    h: float
    layers: list
    drill: float
    rratio: float
    poly: list | None = None


@dataclass
class Footprint:
    lib: str
    side: str
    x: float
    y: float
    rot: float
    props: dict
    attrs: list
    sheet: str
    court: tuple | None
    fab: tuple | None
    padbox: tuple | None
    pads: list = field(default_factory=list)


@dataclass
class Board:
    path: str
    copper: list
    thickness: float
    footprints: list = field(default_factory=list)
    segments: dict = field(default_factory=dict)   # layer -> list[(x1,y1,x2,y2,w)]
    arcs: dict = field(default_factory=dict)       # layer -> list[(x1,y1,xm,ym,x2,y2,w)]
    vias: list = field(default_factory=list)       # (x,y,size,drill,layers)
    zones: dict = field(default_factory=dict)      # layer -> list[list[(x,y)]]
    zone_count: int = 0
    edges: list = field(default_factory=list)      # (x1,y1,x2,y2) after arc flattening
    counts: dict = field(default_factory=dict)


def _bbox_add(b, x, y):
    if b is None:
        return [x, y, x, y]
    b[0] = min(b[0], x); b[1] = min(b[1], y); b[2] = max(b[2], x); b[3] = max(b[3], y)
    return b


def _arc_points(sx, sy, mx, my, ex, ey, step_deg=10.0):
    ax, ay, bx, by, cx, cy = sx, sy, mx, my, ex, ey
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return [(sx, sy), (ex, ey)]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(p[1] - uy, p[0] - ux) for p in ((ax, ay), (bx, by), (cx, cy)))

    def norm(a):
        return a % (2 * math.pi)
    sweep = norm(a1 - a0)
    if norm(am - a0) > sweep:  # mid is on the other way round
        sweep -= 2 * math.pi
    n = max(2, int(abs(math.degrees(sweep)) / step_deg) + 1)
    return [(ux + r * math.cos(a0 + sweep * i / n), uy + r * math.sin(a0 + sweep * i / n)) for i in range(n + 1)]


def _graphic_box(node, b):
    """Extend bbox ``b`` by an fp_/gr_ graphic in its own coordinates."""
    t = node[0]
    if t in ('fp_line', 'gr_line', 'fp_rect', 'gr_rect'):
        for k in ('start', 'end'):
            p = kid(node, k)
            b = _bbox_add(b, float(p[1]), float(p[2]))
    elif t in ('fp_circle', 'gr_circle'):
        c, e = kid(node, 'center'), kid(node, 'end')
        cx, cy = float(c[1]), float(c[2])
        r = math.hypot(float(e[1]) - cx, float(e[2]) - cy)
        b = _bbox_add(_bbox_add(b, cx - r, cy - r), cx + r, cy + r)
    elif t in ('fp_arc', 'gr_arc'):
        s, m, e = kid(node, 'start'), kid(node, 'mid'), kid(node, 'end')
        for x, y in _arc_points(*(float(v) for p in (s, m, e) for v in p[1:3])):
            b = _bbox_add(b, x, y)
    elif t in ('fp_poly', 'gr_poly'):
        for xy in kids(kid(node, 'pts'), 'xy'):
            b = _bbox_add(b, float(xy[1]), float(xy[2]))
    return b


def _footprint(node) -> Footprint:
    at = kid(node, 'at')
    x, y = float(at[1]), float(at[2])
    r = float(at[3]) if len(at) > 3 else 0.0
    props = {p[1]: p[2] for p in kids(node, 'property') if len(p) > 2 and isinstance(p[2], str)}
    attr = kid(node, 'attr')
    sheet = kid(node, 'sheetname')
    court = fab = padbox = None
    pads = []
    for c in node[1:]:
        if not isinstance(c, list) or not c:
            continue
        if c[0].startswith('fp_') and c[0] != 'fp_text':
            lay = kid(c, 'layer')
            ln = lay[1] if lay else ''
            if ln.endswith('CrtYd'):
                court = _graphic_box(c, court)
            elif ln.endswith('Fab'):
                fab = _graphic_box(c, fab)
        elif c[0] == 'pad':
            pat = kid(c, 'at')
            px, py = float(pat[1]), float(pat[2])
            pa = float(pat[3]) if len(pat) > 3 else 0.0
            sz = kid(c, 'size')
            w, h = float(sz[1]), float(sz[2])
            lay = kid(c, 'layers')
            dr = kid(c, 'drill')
            drill = 0.0
            if dr is not None:
                nums = [v for v in dr[1:] if isinstance(v, str) and v != 'oval']
                drill = float(nums[0]) if nums else 0.0
            rr = kid(c, 'roundrect_rratio')
            poly = None
            if c[3] == 'custom':
                prim = kid(c, 'primitives')
                gp = kid(prim, 'gr_poly') if prim else None
                if gp is not None:
                    poly = [(float(q[1]), float(q[2])) for q in kids(kid(gp, 'pts'), 'xy')]
            pads.append(Pad(c[3], c[2], px, py, pa, w, h, list(lay[1:]) if lay else [], drill,
                            float(rr[1]) if rr else 0.0, poly))
            # pad angle in the file is absolute; local extent uses the relative angle
            lx, ly = px, py
            rel = pa - r
            hw, hh = w / 2, h / 2
            for sx, sy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
                ox, oy = rot(sx, sy, rel)
                padbox = _bbox_add(padbox, lx + ox, ly + oy)
    side = kid(node, 'layer')[1]
    return Footprint(node[1], side, x, y, r, props, list(attr[1:]) if attr else [],
                     sheet[1] if sheet else '', tuple(court) if court else None,
                     tuple(fab) if fab else None, tuple(padbox) if padbox else None, pads)


def _edge_segments(node):
    t = node[0]
    if t == 'gr_line':
        s, e = kid(node, 'start'), kid(node, 'end')
        return [(float(s[1]), float(s[2]), float(e[1]), float(e[2]))]
    if t == 'gr_rect':
        s, e = kid(node, 'start'), kid(node, 'end')
        x0, y0, x1, y1 = float(s[1]), float(s[2]), float(e[1]), float(e[2])
        return [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]
    if t == 'gr_arc':
        s, m, e = kid(node, 'start'), kid(node, 'mid'), kid(node, 'end')
        pts = _arc_points(*(float(v) for p in (s, m, e) for v in p[1:3]))
        return [(a[0], a[1], b[0], b[1]) for a, b in zip(pts, pts[1:])]
    if t == 'gr_circle':
        c, e = kid(node, 'center'), kid(node, 'end')
        cx, cy = float(c[1]), float(c[2])
        r = math.hypot(float(e[1]) - cx, float(e[2]) - cy)
        pts = [(cx + r * math.cos(i * math.pi / 18), cy + r * math.sin(i * math.pi / 18)) for i in range(37)]
        return [(a[0], a[1], b[0], b[1]) for a, b in zip(pts, pts[1:])]
    if t == 'gr_poly':
        pts = [(float(q[1]), float(q[2])) for q in kids(kid(node, 'pts'), 'xy')]
        pts.append(pts[0])
        return [(a[0], a[1], b[0], b[1]) for a, b in zip(pts, pts[1:])]
    return []


def read_board(path: Path) -> Board:
    data = path.read_bytes()
    head_end = data.find(b'\n\t(setup')
    copper = [(int(m.group(1)), m.group(2).decode()) for m in LAYER_DEF.finditer(data[:max(head_end, 0)])
              if m.group(3) != b'user']
    # copper stack order: F.Cu, In1..InN, B.Cu (KiCad ids are not in physical order)
    names = [n for _, n in copper]
    inner = sorted((n for n in names if n.startswith('In')), key=lambda n: int(n[2:-3]))
    order = ['F.Cu'] + inner + ['B.Cu']
    th = re.search(rb'\(thickness ' + NUM + rb'\)', data[:max(head_end, 0)])
    board = Board(str(path), order, float(th.group(1)) if th else 1.6)
    board.segments = {n: [] for n in order}
    board.arcs = {n: [] for n in order}
    board.zones = {n: [] for n in order}
    counts = {'footprint': 0, 'segment': 0, 'arc': 0, 'via': 0, 'zone': 0, 'filled_polygon': 0}
    starts = [(m.start() + 1, m.group(1).decode()) for m in TOP.finditer(data)]
    for i, (s, kind) in enumerate(starts):
        e = starts[i + 1][0] if i + 1 < len(starts) else len(data)
        chunk = data[s:e]
        if kind == 'segment':
            counts['segment'] += 1
            st, en = SEG['start'].search(chunk), SEG['end'].search(chunk)
            board.segments.setdefault(SEG['layer'].search(chunk).group(1).decode(), []).append(
                (float(st.group(1)), float(st.group(2)), float(en.group(1)), float(en.group(2)),
                 float(SEG['width'].search(chunk).group(1))))
        elif kind == 'arc':
            counts['arc'] += 1
            st, md, en = SEG['start'].search(chunk), SEG['mid'].search(chunk), SEG['end'].search(chunk)
            board.arcs.setdefault(SEG['layer'].search(chunk).group(1).decode(), []).append(
                tuple(float(v) for m in (st, md, en) for v in m.groups()) + (float(SEG['width'].search(chunk).group(1)),))
        elif kind == 'via':
            counts['via'] += 1
            at = VIA_AT.search(chunk)
            lay = QUOTED.findall(LAYERS.search(chunk).group(1))
            board.vias.append((float(at.group(1)), float(at.group(2)), float(VIA_SIZE.search(chunk).group(1)),
                               float(VIA_DRILL.search(chunk).group(1)), [x.decode() for x in lay]))
        elif kind == 'zone':
            counts['zone'] += 1
            parts = chunk.split(b'(filled_polygon')
            for part in parts[1:]:
                lay = SEG['layer'].search(part)
                pts = [(float(a), float(b)) for a, b in XY.findall(part)]
                if lay and len(pts) >= 3:
                    board.zones.setdefault(lay.group(1).decode(), []).append(pts)
                    counts['filled_polygon'] += 1
        elif kind == 'footprint':
            counts['footprint'] += 1
            board.footprints.append(_footprint(parse_sexpr(chunk)))
        elif kind.startswith('gr_') and b'"Edge.Cuts"' in chunk:
            board.edges.extend(_edge_segments(parse_sexpr(chunk)))
    board.counts = counts
    return board


def outline_loops(edges, tol=0.005):
    """Chain Edge.Cuts segments into closed loops (lists of points)."""
    segs = list(edges)
    loops = []
    while segs:
        x1, y1, x2, y2 = segs.pop()
        loop = [(x1, y1), (x2, y2)]
        grown = True
        while grown and segs:
            grown = False
            tx, ty = loop[-1]
            for i, (a, b, c, d) in enumerate(segs):
                if abs(a - tx) < tol and abs(b - ty) < tol:
                    loop.append((c, d)); segs.pop(i); grown = True; break
                if abs(c - tx) < tol and abs(d - ty) < tol:
                    loop.append((a, b)); segs.pop(i); grown = True; break
        if abs(loop[0][0] - loop[-1][0]) < tol and abs(loop[0][1] - loop[-1][1]) < tol:
            loop.pop()
        loops.append(loop)
    return loops


def polygon_area(pts):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
