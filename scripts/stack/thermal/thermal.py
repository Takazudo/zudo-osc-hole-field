"""ST-05 thermal paper screen: every figure of design/stack/thermal/README.md from thermal-screen.json.

Python 3 standard library only; no network and no KiCad. A screen on unvalidated drafts, not a measurement.
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCREEN = ROOT / 'design/stack/thermal/thermal-screen.json'


def load(path=SCREEN):
    return json.loads(Path(path).read_text())


def term(d, name):
    value = d['terms'][name]['value']
    if isinstance(value, str) and value.startswith('inputs.'):
        obj = d
        for key in value.split('.'):
            obj = obj[key]
        return obj
    return value


def lo_hi(d, name):
    v = term(d, name)
    return (v[0], v[1]) if isinstance(v, list) else (v, v)


def polygon_area(pts):
    return abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2.0


def inside(pts, x, y):
    hit = False
    for i in range(len(pts)):
        (x1, y1), (x2, y2) = pts[i - 1], pts[i]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit



def row_power_W(d, mA):
    return sum(v * i for v, i in zip(term(d, 'rails_V'), mA)) / 1000.0


def family(symbol):
    return 'OPA4197' if symbol.startswith('OPA4197') else symbol


def packages_by(d):
    out = {}
    for p in d['inputs']['ic_packages']:
        out.setdefault((p['instance'], family(p['symbol'])), []).append(p)
    return out


def symbol_mismatches(d):
    counts = {}
    for p in d['inputs']['ic_packages']:
        counts[(p['instance'], p['symbol'])] = counts.get((p['instance'], p['symbol']), 0) + 1
    ledger = {}
    for r in term(d, 'ledger_rows'):
        key = (r['instance'], r['label'].split()[0].replace('/', '_'))
        if key in counts or any(k[0] == key[0] and family(k[1]) == family(key[1]) for k in counts):
            if key[1].startswith(('OPA', 'LM', 'TMUX', 'SN74', 'CD74', 'AS3340', 'LF398', 'REF5050AIDR')):
                ledger[key] = ledger.get(key, 0) + r['count']
    return sorted((k, v, counts.get(k, 0)) for k, v in ledger.items() if counts.get(k, 0) != v)


def board_fractions(pkgs):
    n = len(pkgs)
    out = {}
    for p in pkgs:
        out[p['board']] = out.get(p['board'], 0.0) + 1.0 / n
    return out


def jack_board(d, inst):
    split = d['inputs']['jack_split']
    return 'JL' if inst in split['left'] else 'JR' if inst in split['right'] else 'K'


def classify(d, row, pk):
    label, inst = row['label'], row['instance']
    symbol = family(label.split()[0].replace('/', '_'))
    if (inst, symbol) in pk:
        return 'IC', board_fractions(pk[(inst, symbol)]), 0.0
    if 'NOISE2' in label:
        return 'NOISE2', board_fractions(pk[(inst, 'NOISE2')]), 0.0
    if 'REF5050' in label or row['id'].endswith(':reference'):
        pkgs = pk.get((inst, 'REF5050AIDR'))
        return 'REF', board_fractions(pkgs) if pkgs else {'K': 1.0}, 0.0
    if row['id'].endswith(':logic'):
        pkgs = pk.get((inst, 'SN74HC14DR'), []) + pk.get((inst, 'CD74HC221M96'), [])
        return 'LOGIC', board_fractions(pkgs), 0.0
    if inst == 'inlet':
        return 'INLET', {term(d, 'inlet_board'): 1.0}, 0.0
    low = label.lower()
    words = set(re.split(r'[^a-z0-9]+', low))
    if words & {'led', 'leds', 'indicator', 'indicators', 'magnitude'}:
        kind = 'stage' if 'stage' in words else 'clip' if 'clip' in words else 'mag'
        where = d['inputs']['led_uid_boards'].get(inst + '.' + kind)
        if where is None:
            raise ValueError(f"LED row {row['id']} has no LED uid {inst}.{kind} on any board")
        n = sum(where.values())
        return 'LED', {b: c / n for b, c in where.items()}, 0.0
    if re.search(r'output load|jack loads|external load|output_loads', low):
        ext = row['count'] * term(d, 'external_output_V') ** 2 / term(d, 'external_output_ohm')
        return 'OUT', {jack_board(d, inst): 1.0}, ext
    if (words & {'pot', 'pots'} or re.search(r'manual control tracks|track/harness drive', low)) and 'signal pots' not in low:
        return 'POT', {'P': 1.0}, 0.0
    if 'control-contact pulls' in low:
        return 'PULL', {'P': 1.0}, 0.0
    if 'enable' in low:
        pkgs = pk.get((inst, 'TMUX7412FRRPR'))
        return 'ENABLE', board_fractions(pkgs) if pkgs else {'K': 1.0}, 0.0
    if 'comparator pullups' in low:
        return 'PULLUP', board_fractions(pk[(inst, 'LM393BIDR')]), 0.0
    return 'K', {'K': 1.0}, 0.0


def all_rows(d):
    rows = [dict(r) for r in term(d, 'ledger_rows')]
    total = term(d, 'ledger_total_mA')
    used = [sum(r['mA'][i] for r in rows) for i in range(3)]
    rows.append({'id': 'bleeders', 'instance': 'inlet', 'label': 'inlet bleeder residual', 'count': 2,
                 'unit': 'residual', 'mA': [total[i] - used[i] for i in range(3)]})
    return rows


CASES = ('normal', 'contract', 'low')


def scales(d, case):
    if case in ('normal', 'low'):
        return [1.0, 1.0, 1.0]
    if case != 'contract':
        raise ValueError('unknown load case ' + case)
    total = term(d, 'ledger_total_mA')
    return [c / t for c, t in zip(term(d, 'contract_mA'), total)]


def typical_mA(d, spec, keys='keys'):
    fact = d['inputs']['bundle_facts'][spec['fact']]['value']
    per = term(d, 'amplifiers_per_package') if spec['per'] == 'amplifier' else 1
    scale = 0.001 if spec['unit'] == 'uA' else 1.0
    return [fact[spec[keys][r]] * scale * per if r in spec[keys] else 0.0 for r in d['inputs']['rails']]


def low_heat_rows(d):
    specs = {s['symbol']: s for s in term(d, 'low_heat_typicals')}
    out = {}
    for row in term(d, 'ledger_rows'):
        sym = row['label'].split()[0].replace('/', '_')
        if sym not in specs or row['unit'] == 'draft allowance':
            continue
        basis = [row['count'] * m for m in typical_mA(d, specs[sym], 'ledger_basis_keys')]
        if any(abs(m - b) > 1e-9 for m, b in zip(row['mA'], basis)):
            raise ValueError(f"ledger row {row['id']} is not count x the bundle maximum: {row['mA']} against {basis}")
        low = [row['count'] * t for t in typical_mA(d, specs[sym])]
        out[row['id']] = {'mA': low, 'fact': specs[sym]['fact'], 'symbol': sym}
    return out


def case_rows(d, case):
    s = scales(d, case)
    low = low_heat_rows(d) if case == 'low' else {}
    rows = []
    for row in all_rows(d):
        mA = low[row['id']]['mA'] if row['id'] in low else row['mA']
        rows.append(dict(row, mA=[i * k for i, k in zip(mA, s)]))
    return rows


def case_total_mA(d, case):
    s = scales(d, case)
    total = [t * k for t, k in zip(term(d, 'ledger_total_mA'), s)]
    if case == 'low':
        rows = {r['id']: r for r in term(d, 'ledger_rows')}
        for rid, low in low_heat_rows(d).items():
            total = [t - (m - n) for t, m, n in zip(total, rows[rid]['mA'], low['mA'])]
    return total


_STATIC = {}


def static_cached(fn):
    def wrapper(d, *args):
        terms = tuple((k, id(v)) for k, v in sorted(d['terms'].items()) if k != 'ambient_C')
        key = (fn.__name__, id(d['inputs']), terms, args)
        hit = _STATIC.get(key)
        if hit is not None and hit[0] is d['inputs'] and all(hit[1][k] is v for k, v in d['terms'].items() if k != 'ambient_C'):
            return hit[2]
        out = fn(d, *args)
        _STATIC[key] = (d['inputs'], dict(d['terms']), out)
        return out
    wrapper.__name__ = fn.__name__
    wrapper.__wrapped__ = fn
    return wrapper


@static_cached
def power_map(d, case='normal'):
    pk = packages_by(d)
    boards, external, rows_out, rules = {}, 0.0, [], {}
    for row in case_rows(d, case):
        rule, frac, ext = classify(d, row, pk)
        p_in = row_power_W(d, row['mA'])
        internal = p_in - ext
        for b, f in frac.items():
            boards[b] = boards.get(b, 0.0) + internal * f
        external += ext
        rules[rule] = rules.get(rule, 0.0) + p_in
        rows_out.append({'id': row['id'], 'rule': rule, 'W': p_in, 'external_W': ext, 'boards': frac})
    total_in = row_power_W(d, case_total_mA(d, case))
    return {'boards': boards, 'external_W': external, 'input_W': total_in,
            'internal_W': sum(boards.values()),
            'residual_W': total_in - sum(boards.values()) - external, 'rows': rows_out, 'rules_W': rules}


def ledger_case_W(d):
    return {k: row_power_W(d, v) for k, v in term(d, 'ledger_other_cases_mA').items()}


def board_areas_cm2(planes):
    return {k: polygon_area(v['outline']) / 100.0 for k, v in planes.items()}


def output_count(d):
    pk = packages_by(d)
    return sum(r['count'] for r in all_rows(d) if classify(d, r, pk)[0] == 'OUT')



def planes_for(d, depth):
    if depth == 120:
        return {k: v for k, v in d['inputs']['boards_120'].items()}
    return dict(d['inputs']['planes_40'])


def compressed_cells(d, planes):
    x0, y0, x1, y1 = term(d, 'enclosure_internal_xy_mm')
    xs, ys = {x0, x1}, {y0, y1}
    for v in planes.values():
        for x, y in v['outline']:
            xs.add(x)
            ys.add(y)
    xs, ys = sorted(xs), sorted(ys)
    cells = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            members = [k for k, v in planes.items() if inside(v['outline'], cx, cy)]
            cells.append(((xs[i], ys[j], xs[i + 1], ys[j + 1]), members))
    return cells


@static_cached
def facing_pairs(d, depth):
    planes = planes_for(d, depth)
    panel = term(d, 'panel_thickness_mm')
    pairs = {}
    for rect, members in compressed_cells(d, planes):
        area = (rect[2] - rect[0]) * (rect[3] - rect[1])
        stack = sorted(members, key=lambda k: -planes[k]['face_z_mm'])
        surfaces = [('shell', -panel, -panel)] + [
            (k, planes[k]['face_z_mm'], planes[k]['face_z_mm'] - planes[k]['thickness_mm']) for k in stack] + [
            ('shell', -depth, -depth)]
        for (a, _, a_rear), (b, b_face, _) in zip(surfaces, surfaces[1:]):
            if a == 'shell' and b == 'shell':
                continue
            key = (a, b, round(a_rear - b_face, 3))
            p = pairs.setdefault(key, {'upper': a, 'lower': b, 'gap_mm': key[2], 'area_mm2': 0.0,
                                       'y': [rect[1], rect[3]]})
            p['area_mm2'] += area
            p['y'] = [min(p['y'][0], rect[1]), max(p['y'][1], rect[3])]
    return sorted(pairs.values(), key=lambda p: (-p['area_mm2']))


def outer_box_m(d, depth, wall=None):
    wall = term(d, 'wall_mm') if wall is None else wall
    x0, y0, x1, y1 = term(d, 'enclosure_internal_xy_mm')
    return (x1 - x0 + 2 * wall) / 1000.0, (y1 - y0 + 2 * wall) / 1000.0, (depth + wall) / 1000.0


def outer_area_m2(d, depth, wall=None):
    w, h, z = outer_box_m(d, depth, wall)
    return 2 * (w * h + w * z + h * z)


def faces(d, depth, orient):
    w, h, z = outer_box_m(d, depth)
    if orient == 'V':
        return [('vertical', 2 * w * h + 2 * h * z), ('up', w * z), ('resting', w * z)]
    return [('up', w * h), ('resting', w * h), ('vertical', 2 * w * z + 2 * h * z)]



def coefficients(d, level):
    if level not in ('low', 'high'):
        raise ValueError('unknown coefficient end ' + level)
    k = 0 if level == 'low' else 1
    return {'h_vertical': lo_hi(d, 'h_conv_vertical')[k], 'h_up': lo_hi(d, 'h_conv_up')[k],
            'h_resting': term(d, 'h_conv_resting'), 'eps_case': lo_hi(d, 'eps_case')[k],
            'eps_board': lo_hi(d, 'eps_board')[k], 'eps_inner': lo_hi(d, 'eps_inner')[k],
            'convective_gaps': level == 'high'}


def h_rad(d, t1, t2, e1, e2):
    s = term(d, 'sigma')
    return s * (t1 * t1 + t2 * t2) * (t1 + t2) / (1.0 / e1 + 1.0 / e2 - 1.0)


def nusselt(d, pair, t_up, t_low, orient, convective):
    if not convective:
        return term(d, 'gap_nu_low')
    air = term(d, 'air')
    L = pair['gap_mm'] / 1000.0
    dT = abs(t_up - t_low)
    ra = term(d, 'gravity') / ((t_up + t_low) / 2) * dT * L ** 3 / (air['nu'] * air['alpha'])
    if orient == 'V':
        c = term(d, 'gap_nu_vertical')
        height = (pair['y'][1] - pair['y'][0]) / 1000.0
        if ra <= 0:
            return 1.0
        return max(1.0, c['C'] * (air['Pr'] / (0.2 + air['Pr']) * ra) ** c['n'] * (height / L) ** c['aspect_exp'])
    c = term(d, 'gap_nu_heated_below')
    if t_low > t_up and ra > c['Ra_crit']:
        return max(1.0, c['C'] * ra ** c['n'] * air['Pr'] ** c['pr_exp'])
    return 1.0


def shell_conductance(d, depth, orient, coef, ts, ta, eps_case=None):
    eps = coef['eps_case'] if eps_case is None else eps_case
    g = 0.0
    for kind, area in faces(d, depth, orient):
        if kind == 'resting':
            g += area * coef['h_resting']
            continue
        h = coef['h_vertical'] if kind == 'vertical' else coef['h_up']
        g += area * (h + h_rad(d, ts, ta, eps, 1.0))
    return g


def vent_conductance(d, depth, orient, area_cm2, t_mean, ta):
    if not area_cm2 or t_mean <= ta:
        return 0.0
    air = term(d, 'air')
    hv = term(d, 'vent_height_m')
    height = hv['V'] if orient == 'V' else hv['H_fraction_of_depth'] * depth / 1000.0
    a_eff = term(d, 'vent_cd') * area_cm2 * 1e-4 / math.sqrt(2.0)
    flow = a_eff * math.sqrt(2 * term(d, 'gravity') * height * (t_mean - ta) / ta)
    return air['rho'] * air['cp'] * flow


def solve_linear(a, b):
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c and m[r][c]:
                f = m[r][c] / m[c][c]
                for k in range(c, n + 1):
                    m[r][k] -= f * m[c][k]
    return [m[i][n] / m[i][i] for i in range(n)]


_CACHE = {}


NETWORK_ROUNDS = 400
SURFACE_ROUNDS = 400


def network(d, depth, orient, level, case='normal', supply='outside', eta=None, vent_cm2=0.0,
            eps_override=None, extra_W=0.0, h_resting=None):
    key = (id(d), depth, orient, level, case, supply, eta, vent_cm2, eps_override, extra_W, h_resting)
    hit = _CACHE.get(key)
    if hit is not None and hit[0] is d:
        return hit[1]
    out = _network(d, depth, orient, level, case, supply, eta, vent_cm2, eps_override, extra_W, h_resting)
    _CACHE[key] = (d, out)
    return out


def _network(d, depth, orient, level, case, supply, eta, vent_cm2, eps_override, extra_W, h_resting=None):
    coef = coefficients(d, level)
    if eps_override is not None:
        coef = dict(coef, eps_case=eps_override, eps_inner=eps_override)
    if h_resting is not None:
        coef = dict(coef, h_resting=h_resting)
    ta = term(d, 'ambient_C') + 273.15
    pm = power_map(d, case)
    pairs = facing_pairs(d, depth)
    nodes = sorted({p[k] for p in pairs for k in ('upper', 'lower')} - {'shell'})
    dropped = {b: w for b, w in pm['boards'].items() if b not in nodes and abs(w) > 1e-12}
    if dropped:
        raise ValueError(f'power on boards outside the network at {depth} mm: {dropped}')
    q = {n: pm['boards'].get(n, 0.0) for n in nodes}
    q['K'] = q.get('K', 0.0) + extra_W
    q_shell = 0.0
    if supply == 'inside':
        if not eta or not 0.0 < eta <= 1.0:
            raise ValueError(f'a supply inside needs an efficiency in (0, 1], not {eta!r}')
        q_shell = pm['input_W'] * (1.0 / eta - 1.0)
    idx = {n: i for i, n in enumerate(nodes + ['shell'])}
    temps = {n: ta + 10.0 for n in idx}
    area_nodes = {n: sum(p['area_mm2'] for p in pairs if n in (p['upper'], p['lower'])) for n in nodes}
    converged = False
    for _ in range(NETWORK_ROUNDS):
        size = len(idx)
        a = [[0.0] * size for _ in range(size)]
        b = [0.0] * size
        g_pair = []
        for p in pairs:
            u, l = p['upper'], p['lower']
            eu = coef['eps_inner'] if u == 'shell' else coef['eps_board']
            el = coef['eps_inner'] if l == 'shell' else coef['eps_board']
            nu = nusselt(d, p, temps[u], temps[l], orient, coef['convective_gaps'])
            h = nu * term(d, 'air')['k'] / (p['gap_mm'] / 1000.0) + h_rad(d, temps[u], temps[l], eu, el)
            g = h * p['area_mm2'] * 1e-6
            g_pair.append((p, nu, h, g))
            i, j = idx[u], idx[l]
            a[i][i] += g
            a[j][j] += g
            a[i][j] -= g
            a[j][i] -= g
        g_sh = shell_conductance(d, depth, orient, coef, temps['shell'], ta)
        a[idx['shell']][idx['shell']] += g_sh
        b[idx['shell']] += g_sh * ta + q_shell
        total_area = sum(area_nodes.values())
        t_mean = sum(temps[n] * area_nodes[n] for n in nodes) / total_area
        g_v = vent_conductance(d, depth, orient, vent_cm2, t_mean, ta)
        for n in nodes:
            gn = g_v * area_nodes[n] / total_area
            a[idx[n]][idx[n]] += gn
            b[idx[n]] += q[n] + gn * ta
        sol = solve_linear(a, b)
        new = {n: sol[idx[n]] for n in idx}
        if max(abs(new[n] - temps[n]) for n in idx) < 1e-7:
            temps = new
            converged = True
            break
        temps = {n: 0.5 * temps[n] + 0.5 * new[n] for n in idx}
    if not converged:
        raise RuntimeError(f'network did not converge in {NETWORK_ROUNDS} rounds ({depth} mm, {orient}, {level}, {case})')
    rise = {n: temps[n] - ta for n in idx}
    gaps = [{'upper': p['upper'], 'lower': p['lower'], 'gap_mm': p['gap_mm'], 'area_cm2': p['area_mm2'] / 100.0,
             'Nu': nu, 'h': h, 'air_rise': (rise[p['upper']] + rise[p['lower']]) / 2} for p, nu, h, g in g_pair]
    g_k = sum(g for p, nu, h, g in g_pair if 'K' in (p['upper'], p['lower']))
    q_total = sum(q.values()) + q_shell
    vent_W = g_v * (t_mean - ta)
    return {'rise': rise, 'gaps': gaps, 'q_W': q_total, 'vent_W': vent_W, 'G_K': g_k,
            'K_area_m2': area_nodes.get('K', 0.0) * 1e-6 / 2.0, 'nodes': nodes}


def surface_rise(d, depth, orient, level, q_W, eps_override=None, h_resting=None):
    coef = coefficients(d, level)
    if h_resting is not None:
        coef = dict(coef, h_resting=h_resting)
    ta = term(d, 'ambient_C') + 273.15
    ts = ta + 10.0
    for _ in range(SURFACE_ROUNDS):
        g = shell_conductance(d, depth, orient, coef, ts, ta, eps_override)
        new = ta + q_W / g
        if abs(new - ts) < 1e-9:
            return new - ta
        ts = 0.5 * ts + 0.5 * new
    raise RuntimeError(f'surface rise did not converge in {SURFACE_ROUNDS} rounds ({depth} mm, {orient}, {level})')



@static_cached
def package_powers(d, case='normal'):
    pk = packages_by(d)
    per = {}
    for row in case_rows(d, case):
        rule, frac, ext = classify(d, row, pk)
        if rule not in ('IC', 'NOISE2', 'REF', 'LOGIC'):
            continue
        symbols = {'REF': ['REF5050AIDR'], 'LOGIC': ['SN74HC14DR', 'CD74HC221M96']}.get(
            rule, [family(row['label'].split()[0].replace('/', '_')) if rule == 'IC' else 'NOISE2'])
        pkgs = [p for sym in symbols for p in pk.get((row['instance'], sym), [])]
        if not pkgs:
            continue
        p_in = row_power_W(d, row['mA'])
        for p in pkgs:
            per[p['ref']] = per.get(p['ref'], 0.0) + p_in / len(pkgs)
    return per


@static_cached
def k_power_points(d, case='normal'):
    pk = packages_by(d)
    by_ref = {p['ref']: p for p in d['inputs']['ic_packages']}
    points = []
    for ref, w in package_powers(d, case).items():
        if by_ref[ref]['board'] == 'K':
            points.append((by_ref[ref]['xy'], w))
    spread = 0.0
    for row in case_rows(d, case):
        rule, frac, ext = classify(d, row, pk)
        if rule in ('IC', 'NOISE2', 'REF', 'LOGIC') or 'K' not in frac:
            continue
        w = (row_power_W(d, row['mA']) - ext) * frac['K']
        cen = d['inputs']['module_K_centroids'].get(row['instance'])
        if cen:
            points.append((cen['centroid'], w))
        else:
            spread += w
    return points, spread


def rect_overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def k_rects(d):
    planes = d['inputs']['planes_40']
    return [r for r, m in compressed_cells(d, {'K': planes['K']}) if 'K' in m]


def cell_grid(d, rects):
    size = term(d, 'cell_mm')
    x0 = math.floor(min(r[0] for r in rects) / size)
    x1 = math.ceil(max(r[2] for r in rects) / size)
    y0 = math.floor(min(r[1] for r in rects) / size)
    y1 = math.ceil(max(r[3] for r in rects) / size)
    return [(i, j) for i in range(x0, x1) for j in range(y0, y1)]


def k_cells(d, case='normal', depth=40, orient='V', level='low', h_resting=None):
    size = term(d, 'cell_mm')
    rects = k_rects(d)
    k_area = sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects)
    points, spread = k_power_points(d, case)
    cells = {}
    for (x, y), w in points:
        key = (math.floor(x / size), math.floor(y / size))
        cells[key] = cells.get(key, 0.0) + w
    out = {}
    for key in cell_grid(d, rects):
        box = (key[0] * size, key[1] * size, (key[0] + 1) * size, (key[1] + 1) * size)
        area = sum(rect_overlap(box, r) for r in rects)
        if area <= 0:
            continue
        out[key] = {'area_mm2': area, 'W': cells.get(key, 0.0) + spread * area / k_area}
    dropped = {k: w for k, w in cells.items() if k not in out and abs(w) > 1e-12}
    if dropped:
        raise ValueError(f'K power in cells outside K: {dropped}')
    total = sum(c['W'] for c in out.values())
    q_mean = total / (k_area * 1e-6)
    net = network(d, depth, orient, level, case, h_resting=h_resting)
    h_k = net['G_K'] / (k_area * 1e-6)
    ls = spreading_length_mm(d, h_k)[0]
    for key, c in out.items():
        c['q_W_m2'] = c['W'] / (c['area_mm2'] * 1e-6)
        c['rise_bound_K'] = (c['q_W_m2'] - q_mean) / h_k
    for key, c in out.items():
        wsum = qsum = 0.0
        for other, o in out.items():
            r = size * math.dist(key, other)
            w = o['area_mm2'] * math.exp(-r / ls)
            wsum += w
            qsum += w * o['q_W_m2']
        c['q_smooth_W_m2'] = qsum / wsum
        c['rise_smooth_K'] = (c['q_smooth_W_m2'] - q_mean) / h_k
    return out, {'K_W': total, 'q_mean': q_mean, 'h_K': h_k, 'K_area_mm2': k_area, 'L_s_mm': ls}


def spreading_length_mm(d, h_k):
    sp = term(d, 'h_spread_cu')
    k = d['inputs']['boards_120']['K']
    layers, oz = k['layers'], k['copper_oz']
    out = []
    for cov in sp['coverage']:
        kt = sp['k'] * layers * oz * sp['oz_um'] * 1e-6 * cov
        out.append(1000.0 * math.sqrt(kt / h_k))
    return out


def cell_name(d, key):
    size = term(d, 'cell_mm')
    return f'x {key[0] * size:g} to {(key[0] + 1) * size:g}, y {key[1] * size:g} to {(key[1] + 1) * size:g}'


def cell_of(d, xy):
    size = term(d, 'cell_mm')
    return math.floor(xy[0] / size), math.floor(xy[1] / size)


def as3340_split_W(d):
    vcc, vee_rail = term(d, 'rails_V')[0], term(d, 'rails_V')[1]
    core = term(d, 'as3340_icc_mA') * vcc / 1000.0
    row = next(r for r in term(d, 'ledger_rows') if r['label'] == 'AS3340D core')
    vee = row['mA'][1] / row['count'] / 1000.0
    return {'row_W': row_power_W(d, row['mA']) / row['count'], 'core_W': core + vee * term(d, 'as3340_vee_V'),
            'vee_driver_W': vee * (vee_rail - term(d, 'as3340_vee_V'))}


ENDS = {'worst': ('normal', 'low'), 'best': ('low', 'high')}
DEPTHS = (40, 120)
ORIENTS = ('V', 'H')
WORDS = ('MET ON PAPER', 'EXCEEDED ON PAPER', 'NOT SHOWN')
_CELLS = {}


def k_cells_cached(d, case, depth, orient, level, h_resting=None):
    key = (id(d), case, depth, orient, level, h_resting)
    hit = _CELLS.get(key)
    if hit is not None and hit[0] is d:
        return hit[1]
    out = k_cells(d, case, depth, orient, level, h_resting)
    _CELLS[key] = (d, out)
    return out


def class_places(d, symbol):
    exact = d['inputs']['exact_part_places']
    if symbol in exact:
        return [dict(p, symbol=symbol) for p in exact[symbol]]
    return [p for p in d['inputs']['ic_packages'] if p['symbol'] == symbol]


def place_reading(d, p, depth, orient, case, level, h_resting=None):
    net = network(d, depth, orient, level, case, h_resting=h_resting)
    if p['board'] not in net['rise']:
        return None
    out = {'ref': p['ref'], 'board': p['board'], 'cell': None, 'lateral_K': None,
           'board_mean_C': term(d, 'ambient_C') + net['rise'][p['board']]}
    out['T_C'] = out['board_mean_C']
    if p['board'] == 'K':
        cells, _ = k_cells_cached(d, case, depth, orient, level, h_resting)
        key = cell_of(d, p['xy'])
        if key not in cells:
            raise ValueError(f"{p['ref']} on K lies in no cell of K: {p['xy']}")
        out.update(cell=key, lateral_K=cells[key]['rise_smooth_K'])
        out['T_C'] += out['lateral_K']
    return out


def board_at_part(d, places, depth, orient, case, level, board=None, h_resting=None):
    readings = [place_reading(d, p, depth, orient, case, level, h_resting) for p in places
                if board is None or p['board'] == board]
    readings = [x for x in readings if x is not None]
    if not readings:
        return None
    return max(readings, key=lambda r: (r['T_C'], r['ref']))


def of_record(r):
    return str(r.get('verdict', '')).startswith('PASS')


def retained_limit(d, symbol):
    ranges = [r for r in d['inputs']['operating_ranges'].get(symbol, []) if of_record(r)]
    if not ranges:
        return None
    best = min(ranges, key=lambda r: r['maximum'])
    return {'limit_C': float(best['maximum']), 'fact_id': best['fact_id'], 'minimum_C': float(best['minimum']),
            'class': best.get('class')}


def information_ranges(d, symbol):
    return [r for r in d['inputs']['operating_ranges'].get(symbol, []) if not of_record(r)]


def thermal_figures(d, symbol):
    bundle = d['inputs']['class_bundles'][symbol]
    ranges = {r['fact_id'] for r in d['inputs']['operating_ranges'].get(symbol, [])}
    skip = set(term(d, 'thermal_survey_not_figures'))
    return [f for f in d['inputs']['bundle_thermal_survey'].get(bundle, []) if f not in ranges and f not in skip]


WORD_RANK = {'MET ON PAPER': 0, 'NOT SHOWN': 1, 'EXCEEDED ON PAPER': 2}


def worst_word(words):
    return max(words, key=lambda w: WORD_RANK[w])


def word(limit, worst_C, best_C):
    if limit is None or worst_C is None or best_C is None:
        return 'NOT SHOWN'
    if worst_C <= limit:
        return 'MET ON PAPER'
    if best_C > limit:
        return 'EXCEEDED ON PAPER'
    return 'NOT SHOWN'


def class_comparison(d, symbol, depth, board=None):
    places = [p for p in class_places(d, symbol) if board is None or p['board'] == board]
    lim = retained_limit(d, symbol)
    limit = None if lim is None else lim['limit_C']
    per = {}
    for orient in ORIENTS:
        worst = board_at_part(d, places, depth, orient, *ENDS['worst'])
        if worst is None:
            per[orient] = None
            continue
        best = board_at_part(d, places, depth, orient, *ENDS['best'], board=worst['board'])
        per[orient] = {'worst': worst, 'best': best, 'word': word(limit, worst['T_C'], best['T_C'])}
    held = [o for o in ORIENTS if per[o] is not None]
    if not held:
        return {'symbol': symbol, 'depth': depth, 'board': board, 'limit': lim, 'orients': per, 'worse': None,
                'word': None, 'places': len(places)}
    worse = max(held, key=lambda o: (per[o]['worst']['T_C'], o))
    return {'symbol': symbol, 'depth': depth, 'board': board, 'limit': lim, 'orients': per, 'worse': worse,
            'word': worst_word([per[o]['word'] for o in held]), 'places': len(places)}


def panel_parts(d):
    return list(d['inputs'].get('panel_parts', []))


def limit_classes(d):
    panel = set(panel_parts(d))
    return sorted(s for s in d['inputs']['operating_ranges'] if retained_limit(d, s) is not None
                  and class_places(d, s) and s != 'RC0603FR-072K2L' and s not in panel)


def no_limit_classes(d):
    syms = sorted({p['symbol'] for p in d['inputs']['ic_packages']})
    return [s for s in syms if retained_limit(d, s) is None]


def class_boards(d, symbol):
    return sorted({p['board'] for p in class_places(d, symbol)})


def panel_rows(d):
    rows = []
    for s in panel_parts(d):
        for b in class_boards(d, s):
            rows.append({'symbol': s, 'board': b, 'count': sum(1 for p in class_places(d, s) if p['board'] == b),
                         'depths': {depth: class_comparison(d, s, depth, board=b) for depth in DEPTHS}})
    return rows


def panel_class_word(d, symbol, depth):
    words = [r['depths'][depth]['word'] for r in panel_rows(d) if r['symbol'] == symbol and r['depths'][depth]['word']]
    return worst_word(words) if words else None


def board_table(d):
    out = {}
    for depth in DEPTHS:
        for o in ORIENTS:
            for e, (case, level) in ENDS.items():
                rise = network(d, depth, o, level, case)['rise']
                for b, r in rise.items():
                    out.setdefault(b, {})[(depth, o, e)] = term(d, 'ambient_C') + r
    return out


def board_shift(table, board, o, e):
    row = table[board]
    if (40, o, e) not in row or (120, o, e) not in row:
        return None
    return row[(40, o, e)] - row[(120, o, e)]


def derating_ratio(d, fact_id, t_C):
    v = d['inputs']['panel_facts'][fact_id]['value']
    full, end_t = v['full_power_up_to_ambient_C'], v['curve_end_ambient_C']
    end_r = v['curve_end_power_ratio_percent'] / 100.0
    if t_C <= full:
        return v['full_power_ratio_percent'] / 100.0
    if t_C <= end_t:
        return 1.0 + (end_r - 1.0) * (t_C - full) / (end_t - full)
    return None


def pot_powers(d):
    volts = dict(d['inputs']['rail_voltages_V'])
    volts.update({n: 0.0 for n in term(d, 'ground_nets')})
    tol = term(d, 'pot_resistance_tolerance')
    out = []
    for e in d['inputs']['pot_ends']:
        a, b = volts.get(e['pin1']), volts.get(e['pin3'])
        res = d['inputs']['panel_facts'][f"fact-{e['value'].split('-')[-1].lower()}-resistance"]['value']
        w = None if a is None or b is None else (a - b) ** 2 / (res * (1.0 - tol))
        out.append({'ref': e['ref'], 'value': e['value'], 'W': w})
    return out


def ambient_at(d, symbol, depth, orient, which, limit, board=None, lo=-20.0, hi=80.0, tol=0.01):
    case, level = ENDS[which]

    def temp(amb):
        dd = dict(d, terms=dict(d['terms'], ambient_C=dict(d['terms']['ambient_C'], value=amb)))
        places = [p for p in class_places(dd, symbol) if board is None or p['board'] == board]
        r = board_at_part(dd, places, depth, orient, case, level)
        return None if r is None else r['T_C']
    x0 = term(d, 'ambient_C')
    f0 = temp(x0)
    if f0 is None:
        return None
    x1 = x0 + (limit - f0)
    for _ in range(12):
        x1 = min(max(x1, lo), hi)
        f1 = temp(x1)
        if abs(f1 - limit) < tol:
            return x1
        if f1 == f0:
            break
        x0, f0, x1 = x1, f1, x1 + (limit - f1) * (x1 - x0) / (f1 - f0)
        if (x1 <= lo and temp(lo) > limit) or (x1 >= hi and temp(hi) < limit):
            return None
    raise RuntimeError(f'ambient at the limit did not converge for {symbol} at {depth} mm')


def comparison(d):
    return {(s, depth): class_comparison(d, s, depth)
            for s in limit_classes(d) + no_limit_classes(d) for depth in DEPTHS}


def depth_shift_K(d, symbols):
    shifts = []
    for s in symbols:
        a, b = class_comparison(d, s, 40), class_comparison(d, s, 120)
        for o in ORIENTS:
            for end in ENDS:
                shifts.append(a['orients'][o][end]['T_C'] - b['orients'][o][end]['T_C'])
    return min(shifts), max(shifts)


def bleeder_note(d, depth, orient):
    rth = term(d, 'bleeder_rth_K_per_W')
    w = term(d, 'bleeder_mW') / 1000.0
    limit = term(d, 'solder_joint_limit_C')
    region = term(d, 'ds96_bleeder_region_mm')
    out = []
    for p in class_places(d, 'RC0603FR-072K2L'):
        r = place_reading(d, p, depth, orient, *ENDS['worst'])
        body = r['T_C'] + w * rth
        out.append({'ref': p['ref'], 'xy': p['xy'], 'board_C': r['T_C'], 'body_C': body, 'margin_K': limit - body,
                    'allowed_mW': 1000.0 * max(0.0, limit - r['T_C']) / rth,
                    'in_region': region[0] <= p['xy'][0] <= region[2] and region[1] <= p['xy'][1] <= region[3]})
    return out


SENSITIVE = (('O1', 'AS3340D'), ('O2', 'AS3340D'), ('O3', 'AS3340D'), ('O4', 'AS3340D'), ('O5', 'AS3340D'),
             ('H1', 'LF398M_NOPB'), ('H2', 'LF398M_NOPB'))


def sensitive_sites(d):
    pk = packages_by(d)
    sites = []
    for inst, sym in SENSITIVE:
        for p in pk.get((inst, sym), []):
            sites.append({'function': f'{inst} {"core" if sym == "AS3340D" else "S&H"}', 'ref': p['ref'],
                          'xy': p['xy'], 'basis': 'package placement'})
    for inst in ('F1', 'F2', 'F3'):
        sites.append({'function': f'{inst} exponential converter', 'ref': 'module centroid',
                      'xy': d['inputs']['module_K_centroids'][inst]['centroid'], 'basis': 'module K centroid'})
    sites.append({'function': 'OCTAVE_REF shared reference', 'ref': 'module centroid',
                  'xy': d['inputs']['module_K_centroids']['OCTAVE_REF']['centroid'], 'basis': 'module K centroid'})
    refs = [p for p in d['inputs']['ic_packages'] if p['symbol'] == 'REF5050AIDR']
    for p in refs:
        sites.append({'function': f'{p["instance"]} REF5050', 'ref': p['ref'], 'xy': p['xy'], 'basis': 'package placement'})
    return sites


def hot_packages(d, case='normal'):
    per = package_powers(d, case)
    by_ref = {p['ref']: p for p in d['inputs']['ic_packages']}
    limit = term(d, 'hot_package_W')
    hot = [{'ref': r, 'W': w, 'xy': by_ref[r]['xy'], 'symbol': by_ref[r]['symbol']}
           for r, w in per.items() if by_ref[r]['board'] == 'K' and w >= limit - 1e-12]
    return sorted(hot, key=lambda h: (-h['W'], h['ref']))


def sensitive_table(d, case='normal', orient='V', level='low'):
    cells, _ = k_cells_cached(d, case, 40, orient, level)
    cells120, _ = k_cells_cached(d, case, 120, orient, level)
    hot = hot_packages(d, case)
    near = term(d, 'hot_within_mm')
    out = []
    for s in sensitive_sites(d):
        key = cell_of(d, s['xy'])
        close = [h for h in hot if h['ref'] != s['ref'] and math.dist(s['xy'], h['xy']) <= near]
        out.append({**s, 'cell': cell_name(d, key) if key in cells else None,
                    'rise_40': cells[key]['rise_smooth_K'] if key in cells else None,
                    'rise_120': cells120[key]['rise_smooth_K'] if key in cells120 else None,
                    'hot_near': len(close), 'hot_near_W': sum(h['W'] for h in close)})
    return out


def warm_region(d, cells):
    top = max(c['rise_smooth_K'] for c in cells.values())
    keep = [k for k, c in cells.items() if c['rise_smooth_K'] >= term(d, 'hot_region_fraction') * top]
    size = term(d, 'cell_mm')
    box = (min(k[0] for k in keep) * size, min(k[1] for k in keep) * size,
           (max(k[0] for k in keep) + 1) * size, (max(k[1] for k in keep) + 1) * size)
    hottest = max(cells, key=lambda k: (cells[k]['rise_smooth_K'], k))
    return {'box_mm': box, 'cells': sorted(keep), 'lateral_K': (min(cells[k]['rise_smooth_K'] for k in keep), top),
            'hottest': hottest}


def in_box(box, xy):
    return box[0] <= xy[0] <= box[2] and box[1] <= xy[1] <= box[3]


def post_conductance(d):
    af = term(d, 'post_af_mm') / 1000.0
    bore = term(d, 'post_bore_mm') / 1000.0
    area = math.sqrt(3) / 2 * af * af - math.pi * bore * bore / 4
    out = []
    for k in lo_hi(d, 'brass_k'):
        g = 0.0
        for f in d['inputs']['fixings_active']:
            if f['kind'] == 'post':
                g += k * area / (f['gap_mm'] / 1000.0)
        out.append(g)
    return out, area


def post_i2r_bound_W(d):
    r = term(d, 'post_joint_ohm')
    return sum((i / 1000.0) ** 2 * r for i in term(d, 'contract_mA'))
