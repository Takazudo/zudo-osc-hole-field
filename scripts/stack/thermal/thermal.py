"""ST-05 thermal paper screen: every figure of design/stack/thermal/README.md from thermal-screen.json.

Python 3 standard library only; no network and no KiCad. A screen on unvalidated drafts, not a measurement.
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCREEN = ROOT / 'design/stack/thermal/thermal-screen.json'
BOARDS_FRONT = ('EL', 'JL', 'JR', 'P', 'O1', 'O2', 'O3', 'O4', 'O5')


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
    if re.search(r'led|indicator|magnitude', low):
        kind = 'stage' if 'stage' in low else 'clip' if 'clip' in low else 'mag'
        where = d['inputs']['led_uid_boards'][inst + '.' + kind]
        n = sum(where.values())
        return 'LED', {b: c / n for b, c in where.items()}, 0.0
    if re.search(r'output load|jack loads|external load|output_loads', low):
        ext = row['count'] * term(d, 'external_output_V') ** 2 / term(d, 'external_output_ohm')
        return 'OUT', {jack_board(d, inst): 1.0}, ext
    if re.search(r'pot\b|manual control tracks|track/harness drive', low) and 'signal pots' not in low:
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


def scales(d, case):
    if case == 'normal':
        return [1.0, 1.0, 1.0]
    total = term(d, 'ledger_total_mA')
    return [c / t for c, t in zip(term(d, 'contract_mA'), total)]


def power_map(d, case='normal'):
    pk = packages_by(d)
    s = scales(d, case)
    boards, external, rows_out, rules = {}, 0.0, [], {}
    for row in all_rows(d):
        rule, frac, ext = classify(d, row, pk)
        p_in = row_power_W(d, [i * k for i, k in zip(row['mA'], s)])
        internal = p_in - ext
        for b, f in frac.items():
            boards[b] = boards.get(b, 0.0) + internal * f
        external += ext
        rules[rule] = rules.get(rule, 0.0) + p_in
        rows_out.append({'id': row['id'], 'rule': rule, 'W': p_in, 'external_W': ext, 'boards': frac})
    total_in = row_power_W(d, [t * k for t, k in zip(term(d, 'ledger_total_mA'), s)])
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


def network(d, depth, orient, level, case='normal', supply='outside', eta=None, vent_cm2=0.0,
            eps_override=None, extra_W=0.0):
    key = (id(d), depth, orient, level, case, supply, eta, vent_cm2, eps_override, extra_W)
    hit = _CACHE.get(key)
    if hit is not None and hit[0] is d:
        return hit[1]
    out = _network(d, depth, orient, level, case, supply, eta, vent_cm2, eps_override, extra_W)
    _CACHE[key] = (d, out)
    return out


def _network(d, depth, orient, level, case, supply, eta, vent_cm2, eps_override, extra_W):
    coef = coefficients(d, level)
    if eps_override is not None:
        coef = dict(coef, eps_case=eps_override, eps_inner=eps_override)
    ta = term(d, 'ambient_C') + 273.15
    pm = power_map(d, case)
    pairs = facing_pairs(d, depth)
    nodes = sorted({p[k] for p in pairs for k in ('upper', 'lower')} - {'shell'})
    q = {n: pm['boards'].get(n, 0.0) for n in nodes}
    q['K'] = q.get('K', 0.0) + extra_W
    q_shell = 0.0
    if supply == 'inside':
        q_shell = pm['internal_W'] * (1.0 / eta - 1.0)
    idx = {n: i for i, n in enumerate(nodes + ['shell'])}
    temps = {n: ta + 10.0 for n in idx}
    area_nodes = {n: sum(p['area_mm2'] for p in pairs if n in (p['upper'], p['lower'])) for n in nodes}
    for _ in range(80):
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
            break
        temps = {n: 0.5 * temps[n] + 0.5 * new[n] for n in idx}
    rise = {n: temps[n] - ta for n in idx}
    gaps = [{'upper': p['upper'], 'lower': p['lower'], 'gap_mm': p['gap_mm'], 'area_cm2': p['area_mm2'] / 100.0,
             'Nu': nu, 'h': h, 'air_rise': (rise[p['upper']] + rise[p['lower']]) / 2} for p, nu, h, g in g_pair]
    g_k = sum(g for p, nu, h, g in g_pair if 'K' in (p['upper'], p['lower']))
    q_total = sum(q.values()) + q_shell
    vent_W = g_v * (t_mean - ta)
    return {'rise': rise, 'gaps': gaps, 'q_W': q_total, 'vent_W': vent_W, 'G_K': g_k,
            'K_area_m2': area_nodes.get('K', 0.0) * 1e-6 / 2.0, 'nodes': nodes}


def surface_rise(d, depth, orient, level, q_W, eps_override=None):
    coef = coefficients(d, level)
    ta = term(d, 'ambient_C') + 273.15
    ts = ta + 10.0
    for _ in range(200):
        g = shell_conductance(d, depth, orient, coef, ts, ta, eps_override)
        new = ta + q_W / g
        if abs(new - ts) < 1e-9:
            break
        ts = 0.5 * ts + 0.5 * new
    return ts - ta


def plan_h_range(d):
    b = plan_h_backsolve(d)
    values = [v for pair in b.values() for v in pair]
    return min(values), max(values)


def plan_method(d, depth, q_W):
    h = plan_h_range(d)
    a = outer_area_m2(d, depth)
    return q_W / (a * h[1]), q_W / (a * h[0])


def plan_h_backsolve(d):
    lo, hi = term(d, 'plan_heat_W')
    r34, r120 = term(d, 'plan_rise_K')['34'], term(d, 'plan_rise_K')['120']
    a34, a120 = outer_area_m2(d, 34), outer_area_m2(d, 120)
    return {'34': (lo / (a34 * r34[0]), hi / (a34 * r34[1])), '120': (lo / (a120 * r120[0]), hi / (a120 * r120[1]))}



def package_powers(d, case='normal'):
    pk = packages_by(d)
    s = scales(d, case)
    per = {}
    for row in all_rows(d):
        rule, frac, ext = classify(d, row, pk)
        if rule not in ('IC', 'NOISE2', 'REF', 'LOGIC'):
            continue
        symbols = {'REF': ['REF5050AIDR'], 'LOGIC': ['SN74HC14DR', 'CD74HC221M96']}.get(
            rule, [family(row['label'].split()[0].replace('/', '_')) if rule == 'IC' else 'NOISE2'])
        pkgs = [p for sym in symbols for p in pk.get((row['instance'], sym), [])]
        if not pkgs:
            continue
        p_in = row_power_W(d, [i * k for i, k in zip(row['mA'], s)])
        for p in pkgs:
            per[p['ref']] = per.get(p['ref'], 0.0) + p_in / len(pkgs)
    return per


def k_power_points(d, case='normal'):
    pk = packages_by(d)
    s = scales(d, case)
    by_ref = {p['ref']: p for p in d['inputs']['ic_packages']}
    points = []
    for ref, w in package_powers(d, case).items():
        if by_ref[ref]['board'] == 'K':
            points.append((by_ref[ref]['xy'], w))
    spread = 0.0
    for row in all_rows(d):
        rule, frac, ext = classify(d, row, pk)
        if rule in ('IC', 'NOISE2', 'REF', 'LOGIC') or 'K' not in frac:
            continue
        w = (row_power_W(d, [i * k for i, k in zip(row['mA'], s)]) - ext) * frac['K']
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


def k_cells(d, case='normal', depth=40, orient='V', level='low'):
    size = term(d, 'cell_mm')
    rects = k_rects(d)
    k_area = sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects)
    points, spread = k_power_points(d, case)
    cells = {}
    for (x, y), w in points:
        key = (int(x // size), int(y // size))
        cells[key] = cells.get(key, 0.0) + w
    keys = {(i, j) for i in range(0, 7) for j in range(0, 6)}
    out = {}
    for key in sorted(keys):
        box = (key[0] * size, key[1] * size, (key[0] + 1) * size, (key[1] + 1) * size)
        area = sum(rect_overlap(box, r) for r in rects)
        if area <= 0:
            continue
        out[key] = {'area_mm2': area, 'W': cells.get(key, 0.0) + spread * area / k_area}
    total = sum(c['W'] for c in out.values())
    q_mean = total / (k_area * 1e-6)
    net = network(d, depth, orient, level, case)
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


def cell_name(key):
    return f'x{int(key[0] * 50)}-{int(key[0] * 50 + 50)} y{int(key[1] * 50)}-{int(key[1] * 50 + 50)}'


def cell_of(d, xy):
    size = term(d, 'cell_mm')
    return int(xy[0] // size), int(xy[1] // size)


def per_unit_W(d, case='normal'):
    s = scales(d, case)
    out = {}
    for row in term(d, 'ledger_rows'):
        sym = row['label'].split()[0].replace('/', '_')
        if not re.match(r'(OPA|LM|TMUX|SN74|CD74|AS3340|LF398|NOISE2|REF5050)', sym) or row['unit'] == 'draft allowance':
            continue
        if sym == 'AS3340D':
            sym = 'AS3340D'
        if sym in ('NOISE2',) or row['label'] == 'AS3340D core' or sym.startswith(('OPA', 'LM', 'TMUX', 'SN74', 'CD74', 'LF398')):
            w = row_power_W(d, [i * k for i, k in zip(row['mA'], s)]) / row['count']
            if w > out.get(sym, (0.0, None))[0]:
                out[sym] = (w, row['id'])
    for row in all_rows(d):
        if row['label'].startswith('REF5050') or row['id'].endswith(':reference'):
            w = row_power_W(d, [i * k for i, k in zip(row['mA'], s)])
            if w > out.get('REF5050AIDR', (0.0, None))[0]:
                out['REF5050AIDR'] = (w, row['id'])
    return out


def hot_classes(d, case='normal'):
    units = per_unit_W(d, case)
    classes = {}
    for p in d['inputs']['ic_packages']:
        sym = p['symbol']
        key = 'OPA4197IDR' if sym == 'OPA4197IDR' else sym
        if family(sym) == 'OPA4197':
            w, rid = max(units.get('OPA4197IDR', (0, None)), units.get('OPA4197IPWR', (0, None)))
        else:
            w, rid = units.get(sym, (0.0, None))
        c = classes.setdefault(key, {'symbol': key, 'max_W': w, 'row': rid, 'refs': [], 'boards': {},
                                     'courtyard_mm2': p['courtyard_mm2']})
        c['refs'].append(p['ref'])
        c['boards'][p['board']] = c['boards'].get(p['board'], 0) + 1
    for c in classes.values():
        c['density_mW_mm2'] = 1000.0 * c['max_W'] / c['courtyard_mm2']
    bl = term(d, 'bleeder_body_mm')
    classes['RC0603FR-072K2L bleeder'] = {'symbol': 'RC0603FR-072K2L bleeder', 'max_W': term(d, 'bleeder_mW') / 1000.0,
                                          'refs': ['inlet'], 'boards': {term(d, 'inlet_board'): 6},
                                          'courtyard_mm2': bl[0] * bl[1],
                                          'density_mW_mm2': term(d, 'bleeder_mW') / (bl[0] * bl[1])}
    i = term(d, 'magnitude_led_mA_per_rail') / 1000.0
    w = i * i * term(d, 'magnitude_sense_ohm')
    classes['magnitude sense resistor 5600 ohm'] = {'symbol': 'magnitude sense resistor 5600 ohm', 'max_W': w,
                                                    'refs': ['92 magnitude branches'], 'boards': {'JL': 1, 'JR': 1},
                                                    'courtyard_mm2': bl[0] * bl[1],
                                                    'density_mW_mm2': 1000.0 * w / (bl[0] * bl[1])}
    return classes


def as3340_split_W(d):
    core = term(d, 'as3340_icc_mA') * 12.0 / 1000.0
    row = next(r for r in term(d, 'ledger_rows') if r['label'] == 'AS3340D core')
    vee = row['mA'][1] / row['count'] / 1000.0
    return {'row_W': row_power_W(d, row['mA']) / row['count'], 'core_W': core + vee * term(d, 'as3340_vee_V'),
            'vee_driver_W': vee * (12.0 - term(d, 'as3340_vee_V'))}


def top_ten(d, case='contract'):
    classes = hot_classes(d, case)
    by_p = sorted(classes.values(), key=lambda c: -c['max_W'])
    by_q = sorted(classes.values(), key=lambda c: -c['density_mW_mm2'])
    chosen = []
    for a, b in zip(by_p, by_q):
        for c in (a, b):
            if c['symbol'] not in [x['symbol'] for x in chosen]:
                chosen.append(c)
        if len(chosen) >= 10:
            break
    return chosen[:10]


def local_temperature(d, board, xy=None, case='contract', depth=40, orient='V'):
    worst = None
    for o in ('V', 'H'):
        net = network(d, depth, o, 'low', case)
        r = net['rise'].get(board, net['rise'].get('K'))
        if worst is None or r > worst[0]:
            worst = (r, o)
    rise = worst[0]
    lateral = 0.0
    if board == 'K' and xy is not None:
        cells, _ = k_cells(d, case, depth, worst[1], 'low')
        lateral = max(0.0, cells.get(cell_of(d, xy), {'rise_smooth_K': 0.0})['rise_smooth_K'])
    return term(d, 'ambient_C') + rise + lateral, worst[1], lateral


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


def hot_k_packages(d, case='contract', n=10):
    per = package_powers(d, case)
    by_ref = {p['ref']: p for p in d['inputs']['ic_packages']}
    k = sorted(((w, r) for r, w in per.items() if by_ref[r]['board'] == 'K'), reverse=True)[:n]
    return [{'ref': r, 'W': w, 'xy': by_ref[r]['xy'], 'symbol': by_ref[r]['symbol']} for w, r in k]


def sensitive_table(d, case='contract'):
    cells, meta = k_cells(d, case, 40, 'V', 'low')
    cells120, meta120 = k_cells(d, case, 120, 'V', 'low')
    hot = hot_k_packages(d, case, 20)
    move = term(d, 'move_mm')
    size = term(d, 'cell_mm')
    out = []
    for s in sensitive_sites(d):
        key = cell_of(d, s['xy'])
        others = [h for h in hot if h['ref'] != s['ref']]
        dist = min(math.dist(s['xy'], h['xy']) for h in others)
        near = min(others, key=lambda h: math.dist(s['xy'], h['xy']))
        neighbours = {cell_of(d, (s['xy'][0] + dx, s['xy'][1] + dy)) for dx in (-move, 0, move) for dy in (-move, 0, move)}
        signs = {cells[k]['rise_smooth_K'] > 0 for k in neighbours if k in cells}
        out.append({**s, 'cell': cell_name(key), 'rise_40': cells.get(key, {}).get('rise_smooth_K'),
                    'rise_120': cells120.get(key, {}).get('rise_smooth_K'),
                    'bound_40': cells.get(key, {}).get('rise_bound_K'), 'nearest_hot': near['ref'],
                    'nearest_hot_symbol': near['symbol'], 'distance_mm': dist,
                    'within_cell': dist <= size, 'move_changes_distance_verdict': abs(dist - size) <= move,
                    'move_changes_sign': len(signs) > 1})
    return out



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



def results(d):
    out = {}
    for case in ('normal', 'contract'):
        out['map_' + case] = power_map(d, case)
    out['ledger_cases_W'] = ledger_case_W(d)
    out['areas'] = {depth: outer_area_m2(d, depth) for depth in (40, 34, 120)}
    return out
