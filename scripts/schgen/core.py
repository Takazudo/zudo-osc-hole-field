"""Deterministic KiCad 10 hierarchical schematic writer (stdlib only)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import re
import uuid

NAMESPACE = uuid.UUID('aa653cf0-7a02-48aa-9577-8e96f32234cd')
ATTRIBUTES = ('MPN', 'Manufacturer', 'LCSC', 'Block', 'Role', 'PanelUid', 'Island')


def uid(key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, key))


def q(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def tokens(text: str) -> list[str]:
    return re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)


def parse(items: list[str], pos: int = 0):
    if items[pos] != '(':
        raise ValueError('expected opening parenthesis')
    out = []
    pos += 1
    while pos < len(items) and items[pos] != ')':
        if items[pos] == '(':
            node, pos = parse(items, pos)
            out.append(node)
        else:
            item = items[pos]
            out.append(json.loads(item) if item.startswith('"') else item)
            pos += 1
    if pos >= len(items):
        raise ValueError('unclosed expression')
    return out, pos + 1


def children(node, kind):
    return [x for x in node if isinstance(x, list) and x and x[0] == kind]


@dataclass(frozen=True)
class Pin:
    number: str
    x: float
    y: float
    angle: int
    electrical: str


@dataclass(frozen=True)
class LibrarySymbol:
    lib_id: str
    body: str
    units: dict[int, tuple[Pin, ...]]

    @classmethod
    def from_fixture(cls, lib_id: str, path: Path):
        source = path.read_text()
        node, end = parse(tokens(source))
        if end != len(tokens(source)):
            raise ValueError(f'extra fixture expressions: {path}')
        base = lib_id.split(':', 1)[1]
        if children(node, 'extends'):
            raise ValueError(f'inherited stock symbol unsupported: {lib_id}')
        units = {}
        for child in children(node, 'symbol'):
            match = re.fullmatch(re.escape(base) + r'_(\d+)_\d+', child[1])
            if not match:
                raise ValueError(f'unexpected sub-symbol {child[1]}')
            number = int(match[1])
            pins = []
            for p in children(child, 'pin'):
                a = children(p, 'at')[0]
                pins.append(Pin(str(children(p, 'number')[0][1]), float(a[1]), float(a[2]), int(float(a[3])), str(p[1])))
            units[number] = tuple((*units.get(number, ()), *pins))
        if not units or not any(units.values()):
            raise ValueError(f'no pins: {lib_id}')
        body = source.replace(f'(symbol "{base}"', f'(symbol "{lib_id}"', 1).strip()
        return cls(lib_id, body, units)


@dataclass(frozen=True)
class Part:
    key: str
    symbol: str
    prefix: str
    ordinal: int
    unit: int
    x: float
    y: float
    pins: dict[str, str | None]  # None is an explicit no-connect
    value: str = ''
    footprint: str = ''
    rotation: int = 0
    attributes: dict[str, str] = field(default_factory=dict)
    panel_ref: str = ''
    page: int = 1


@dataclass(frozen=True)
class Family:
    name: str
    parts: tuple[Part, ...]
    global_nets: tuple[str, ...] = ()
    sensitive_nets: tuple[str, ...] = ()


@dataclass(frozen=True)
class Instance:
    family: str
    name: str
    index: int


def designator(part: Part, instance: Instance) -> str:
    if part.panel_ref:
        return part.panel_ref
    if instance.index < 1 or instance.index > 999 or part.ordinal < 1 or part.ordinal > 99:
        raise ValueError('instance index must be 1..999 and part ordinal 1..99')
    return f'{part.prefix}{instance.index * 100 + part.ordinal}'


def validate_family(family: Family, library: dict[str, LibrarySymbol]) -> None:
    keys = set()
    packages: dict[str, set[int]] = {}
    for p in family.parts:
        if p.key in keys:
            raise ValueError(f'duplicate part key: {p.key}')
        keys.add(p.key)
        if p.page < 1:
            raise ValueError(f'page must be positive: {p.key}')
        if p.rotation not in (0, 90, 180, 270):
            raise ValueError(f'rotation must be multiple of 90: {p.key}')
        sym = library[p.symbol]
        if p.unit not in sym.units:
            raise ValueError(f'bad unit: {p.key}')
        expected = {pin.number for pin in sym.units[p.unit]}
        if set(p.pins) != expected:
            raise ValueError(f'{p.key}: pin map must include every pin, using None for no-connect; expected {expected}')
        package = p.key.split('.', 1)[0]
        packages.setdefault(package, set()).add(p.unit)
    net_pages: dict[str, set[int]] = {}
    for p in family.parts:
        for net in p.pins.values():
            if net is not None:
                net_pages.setdefault(net, set()).add(p.page)
    for net, pages in net_pages.items():
        if len(pages) > 1 and net not in family.global_nets:
            raise ValueError(f'{family.name}: local net {net} spans pages {sorted(pages)}')
    # A multi-unit package must explicitly account for all electrically populated units.
    for package, assigned in packages.items():
        entries = [p for p in family.parts if p.key.split('.', 1)[0] == package]
        if len({p.symbol for p in entries}) != 1 or len({p.ordinal for p in entries}) != 1:
            raise ValueError(f'{package}: package units disagree')
        available = {u for u, pins in library[entries[0].symbol].units.items() if pins}
        if assigned != available or len(assigned) != len(entries):
            raise ValueError(f'{package}: all symbol units must be assigned exactly once: {available}')


def _xy(p: Part, pin: Pin) -> tuple[float, float, int]:
    # KiCad symbol coordinates are Cartesian; schematic y is downward.
    x, y = pin.x, pin.y
    if p.rotation == 90: x, y = -y, x
    elif p.rotation == 180: x, y = -x, -y
    elif p.rotation == 270: x, y = y, -x
    return round(p.x + x, 4), round(p.y - y, 4), (pin.angle + p.rotation) % 360


def _prop(name, value, x, y, hidden=False):
    hide = ' (hide yes)' if hidden else ''
    return f'    (property {q(name)} {q(value)} (at {x:g} {y:g} 0) (effects (font (size 1.27 1.27)){hide}))'


def _header(sheet_key, symbols, paper="A3"):
    lines = ['(kicad_sch', '  (version 20260306)', '  (generator "zudo_schgen")', '  (generator_version "10.0")', f'  (uuid {q(uid(sheet_key))})', f'  (paper {q(paper)})', '  (lib_symbols']
    lines += ['    ' + symbol.body.replace('\t', '  ').replace('\n', '\n    ') for symbol in symbols]
    lines += ['  )']
    return lines


def _label(net, x, y, angle, key, global_net):
    kind = 'global_label' if global_net else 'label'
    shape = ' (shape passive)' if global_net else ''
    # The connection point of a left-facing pin is left of its symbol body.
    # Right justification keeps the label text outside that body instead of
    # drawing it over the pin number and the symbol outline.
    justify = 'right' if angle % 360 in (0, 270) else 'left'
    return f'  ({kind} {q(net)}{shape} (at {x:g} {y:g} {angle:g}) (effects (font (size 1.27 1.27)) (justify {justify})) (uuid {q(uid(key))}))'


def _nc(x, y, key):
    return f'  (no_connect (at {x:g} {y:g}) (uuid {q(uid(key))}))'


def _symbol(p: Part, family: Family, instances: tuple[Instance, ...], library: dict[str, LibrarySymbol], root_id: str, sheet_ids: dict[str, str], project: str):
    sym = library[p.symbol]
    refs = [(f'/{root_id}/{sheet_ids[(i.name, p.page)]}', designator(p, i)) for i in instances]
    ref = refs[0][1]
    lines = [f'  (symbol (lib_id {q(p.symbol)}) (at {p.x:g} {p.y:g} {p.rotation}) (unit {p.unit})',
             '    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)',
             f'    (uuid {q(uid(f"part:{family.name}:{p.key}"))})',
             _prop('Reference', ref, p.x+3, p.y-3), _prop('Value', p.value or p.symbol.split(':')[-1], p.x+3, p.y+3),
             _prop('Footprint', p.footprint, p.x, p.y, True), _prop('Datasheet', '', p.x, p.y, True)]
    attrs = {**{a: '' for a in ATTRIBUTES}, **p.attributes}
    # Per-instance Block is encoded in KiCad's instance path, since shared child file has one property set.
    attrs['Block'] = '${SHEETNAME}'
    attrs['Sensitive'] = ','.join(sorted({net for net in p.pins.values() if net in family.sensitive_nets}))
    for name, value in attrs.items():
        lines.append(_prop(name, value, p.x, p.y, True))
    for pin in sym.units[p.unit]:
        lines.append(f'    (pin {q(pin.number)} (uuid {q(uid(f"pin:{family.name}:{p.key}:{pin.number}"))}))')
    lines.append(f'    (instances (project {q(project)}')
    for path, r in refs:
        lines.append(f'      (path {q(path)} (reference {q(r)}) (unit {p.unit}))')
    lines += ['    ))', '  )']
    return lines


def render(families: tuple[Family, ...], instances: tuple[Instance, ...], library: dict[str, LibrarySymbol], project='zudo-osc-hole-field') -> dict[str, str]:
    names = {f.name for f in families}
    if len(names) != len(families) or len({i.name for i in instances}) != len(instances):
        raise ValueError('duplicate family or instance name')
    for f in families: validate_family(f, library)
    if any(i.family not in names for i in instances): raise ValueError('unknown instance family')
    # Multiple units of one package intentionally share a reference.
    by_ref = {}
    for i in instances:
        f = next(f for f in families if f.name == i.family)
        for p in f.parts:
            r = designator(p, i)
            pkg = (i.name, p.key.split('.', 1)[0])
            if r in by_ref and by_ref[r] != pkg: raise ValueError(f'designator collision: {r}')
            by_ref[r] = pkg
    root_id = uid('root')
    pages = {f.name: sorted({p.page for p in f.parts}) for f in families}
    sheet_ids = {(i.name, page): uid(f'sheet:{i.name}:p{page}') for i in instances for page in pages[i.family]}
    result = {}
    for f in families:
        relevant = tuple(i for i in instances if i.family == f.name)
        if not relevant: continue
        for page in pages[f.name]:
            page_parts = tuple(p for p in f.parts if p.page == page)
            symbols = [library[name] for name in sorted({p.symbol for p in page_parts})]
            filename = f.name if page == 1 else f'{f.name}-p{page}'
            lines = _header(f'child:{f.name}:p{page}', symbols)
            for p in page_parts:
                lines += _symbol(p, f, relevant, library, root_id, sheet_ids, project)
                for pin in library[p.symbol].units[p.unit]:
                    x, y, angle = _xy(p, pin)
                    net = p.pins[pin.number]
                    key = f'{f.name}:{p.key}:{pin.number}'
                    lines.append(_nc(x, y, f'nc:{key}') if net is None else _label(net, x, y, (360-angle)%360, f'label:{key}', net in f.global_nets))
            lines += ['  (embedded_fonts no)', ')']
            result[f'sheets/{filename}.kicad_sch'] = '\n'.join(lines)+'\n'
    root = _header('root', [], 'A0')
    sheets = [(i, page) for i in instances for page in pages[i.family]]
    for n, (i, page) in enumerate(sheets):
        x, y = 30 + (n % 3)*65, 30 + (n // 3)*35
        su = sheet_ids[(i.name, page)]
        sheet_name = i.name if page == 1 else f'{i.name}-P{page}'
        filename = i.family if page == 1 else f'{i.family}-p{page}'
        root += [f'  (sheet (at {x:g} {y:g}) (size 45 20)',
                 '    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)',
                 '    (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0))',
                 f'    (uuid {q(su)})',
                 _prop('Sheetname', sheet_name, x, y-1), _prop('Sheetfile', f'sheets/{filename}.kicad_sch', x, y+21),
                 f'    (instances (project {q(project)} (path {q("/"+root_id)} (page {q(str(n+2))}))))', '  )']
    root += ['  (sheet_instances (path "/" (page "1")))', '  (embedded_fonts no)', ')']
    result[f'{project}.kicad_sch'] = '\n'.join(root)+'\n'
    return result
