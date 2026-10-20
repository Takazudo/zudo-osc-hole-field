"""Stage55 native gates: ERC and DRC (refill, schematic parity, all severities) on the
disposable baseline copy and the candidate, through the pinned KiCad 10.0.6 oracle.

Usage: native.py run     # executes both sides, retains raw reports and receipts in evidence/
       native.py check   # re-evaluates the retained evidence without running KiCad
Both sides use identical commands and an identical project/rules copy, so deltas come
from the removal only. A clean result is a rule check of a disposable draft, never
manufacturing, analog or hardware validation.
"""
from pathlib import Path
from collections import Counter
import hashlib, json, re, subprocess, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CACHE = ROOT/'.circuit-cache/stage55'
EVIDENCE = HERE/'evidence'
BOARD = 'osc-core'
SIDES = ('baseline', 'candidate')
CAP = 199  # KiCad reports at most this many markers per DRC type


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok, msg):
    if not ok: raise ValueError(msg)
def rel(p): return str(Path(p).relative_to(ROOT))


def commands(side):
    d = CACHE/side/BOARD
    return {
        'erc': ['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'sch', 'erc', '--format', 'json', '--severity-all',
                '-o', rel(CACHE/f'{side}-erc.json'), rel(d/f'{BOARD}.kicad_sch')],
        'drc': ['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'pcb', 'drc', '--schematic-parity', '--refill-zones',
                '--format', 'json', '--severity-all', '-o', rel(CACHE/f'{side}-drc.json'), rel(d/f'{BOARD}.kicad_pcb')],
    }


def inputs(side):
    d = CACHE/side/BOARD
    return {rel(p): sha(p) for p in sorted(d.rglob('*')) if p.is_file() and p.suffix in ('.kicad_sch', '.kicad_pcb', '.kicad_pro', '.kicad_dru')}


def execute():
    EVIDENCE.mkdir(exist_ok=True)
    for side in SIDES:
        for kind, cmd in commands(side).items():
            before = inputs(side)
            out = CACHE/f'{side}-{kind}.json'
            require(not out.exists(), 'refuse overwrite '+rel(out))
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            receipt = {'command': cmd, 'returncode': r.returncode, 'stdout_tail': r.stdout[-4000:], 'stderr_tail': r.stderr[-4000:],
                       'input_sha256': before, 'output_sha256': sha(out) if out.exists() else None}
            # kicad-cli DRC saves refilled zones only in memory; inputs must be unchanged.
            receipt['inputs_unchanged'] = inputs(side) == before
            if out.exists():
                (EVIDENCE/out.name).write_bytes(out.read_bytes())  # retained raw report
            (EVIDENCE/f'{side}-{kind}.execution.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
            require(r.returncode == 0 and receipt['inputs_unchanged'], f'{side} {kind} failed; receipt retained')


def erc_summary(path):
    d = json.loads(Path(path).read_text())
    v = [x for s in d['sheets'] for x in s['violations']]
    key = lambda x: (x['type'], x['severity'], tuple(sorted(i['description'] for i in x.get('items', []))))
    return d['kicad_version'], Counter(key(x) for x in v), Counter((x['type'], x['severity']) for x in v)


def drc_summary(path):
    d = json.loads(Path(path).read_text())
    viol = Counter((x['type'], x['severity']) for x in d['violations'])
    items = Counter((x['type'], tuple(sorted(i['description'] for i in x['items']))) for x in d['violations'])
    unconnected = Counter()
    for x in d['unconnected_items']:
        nets = sorted({i['description'].split('[')[-1].split(']')[0] for i in x['items'] if '[' in i['description']})
        unconnected[tuple(nets)] += 1
    return d, viol, items, unconnected


def gate(result):
    """Pure acceptance gates over an audit result (unit-tested with mutations)."""
    d = result['drc']
    capped_types = result['drc']['capped_types_at_199']
    gates = {
        'oracle_10_0_6': all(v == '10.0.6' for v in result['oracle']['erc'] + result['oracle']['drc']),
        'no_new_erc_errors': result['erc']['candidate_errors'] <= result['erc']['baseline_errors'],
        'no_new_erc_signatures': result['erc']['new_violation_signatures'] == 0,
        'no_drc_errors': d['candidate_errors'] == 0,
        'baseline_schematic_parity_zero': d['schematic_parity'][0] == 0,
        'candidate_parity_only_preexisting_unit_field_ambiguity': d['parity_items_not_preexisting_ambiguity'] == [],
        'no_new_uncapped_drc_signatures': all(k.split(' :: ')[0] in capped_types for k in d['new_violation_signatures']),
        'complete_ratsnest_no_net_gains_edges': result['ratsnest']['nets_with_more_edges'] == {},
        'complete_ratsnest_no_new_open_net': result['ratsnest']['new_open_nets'] == [],
        'removed_private_nets_absent_from_ratsnest': result['ratsnest']['candidate_private_net_edges'] == 0,
        'rail_clusters_equal_baseline_minus_removed_pads': all(v['identical_after_projection'] and v['split_clusters'] == 0
                                                               for v in result['rail_clusters'].values()),
        'no_candidate_violation_names_removed_item': d['violations_mentioning_removed_refs_or_nets']['candidate'] == [],
    }
    return gates


ALLOWED_PARITY = {('U111', 'Role')}  # the one reviewed pre-existing unit-field ambiguity


def parity_unexplained(items, conflicts):
    """Parity items NOT explained by the reviewed pre-existing unit-field ambiguity.

    Accepted only when the (ref, field) is explicitly allowed, and both the PCB value and
    the schematic value are among that ref's unit values in the baseline and candidate.
    """
    out = []
    for x in items:
        m = re.match(r"Field '([^']+)' differs \(PCB: '([^']*)', Schematic: '([^']*)'\)$", x['description'])
        refs = [i['description'].removeprefix('Footprint ') for i in x['items']]
        ok = x['type'] == 'footprint_symbol_field_mismatch' and m and len(refs) == 1
        if ok:
            field, pcb, sch = m.groups()
            ok = (refs[0], field) in ALLOWED_PARITY and all(
                {pcb, sch} <= set(conflicts[s].get(field, {}).get(refs[0], [])) for s in ('baseline', 'candidate'))
        if not ok:
            out.append(x['description'])
    return out


def ratsnest_delta(private):
    b, c = (json.loads((EVIDENCE/f'{s}-ratsnest.json').read_text()) for s in SIDES)
    pcb = json.loads((EVIDENCE/'pcb-receipt.json').read_text())
    require(b['source_sha256_host'] == pcb['source_sha256'] and c['source_sha256_host'] == pcb['output_sha256'], 'ratsnest board binding')
    eb, ec = b['native_open_edges_by_net'], c['native_open_edges_by_net']
    return {'native_unconnected_edges': [b['native_unconnected_edges'], c['native_unconnected_edges']],
            'open_nets': [b['native_open_net_count'], c['native_open_net_count']],
            'nets_with_fewer_edges': {n: [eb[n], ec.get(n, 0)] for n in sorted(eb) if ec.get(n, 0) < eb[n]},
            'nets_with_more_edges': {n: [eb.get(n, 0), ec[n]] for n in sorted(ec) if ec[n] > eb.get(n, 0)},
            'new_open_nets': sorted(set(ec) - set(eb)),
            'candidate_private_net_edges': sum(ec.get(n, 0) for n in private),
            'baseline_private_net_edges': sum(eb.get(n, 0) for n in private)}


def capped_near(pcb, capped_types, radius=6.0):
    """Informational screen, not a gate: capped-type markers within `radius` mm of a removed
    footprint origin, per side. Truncation means absence in a list proves nothing."""
    origins = [r['at'] for r in pcb['removed_footprints']]
    out = {}
    for s in SIDES:
        d = json.loads((EVIDENCE/f'{s}-drc.json').read_text())
        hits = [[x['type'], [i['description'] for i in x['items']]] for x in d['violations'] if x['type'] in capped_types and
                any(((i['pos']['x']-o[0])**2+(i['pos']['y']-o[1])**2) ** 0.5 <= radius for i in x['items'] for o in origins)]
        out[s] = sorted(hits)
    return {'radius_mm': radius, 'baseline': out['baseline'], 'candidate': out['candidate'],
            'candidate_only': [h for h in out['candidate'] if h not in out['baseline']]}


def rail_cluster_delta(removed):
    """Candidate rail clusters must equal baseline clusters with removed pads dropped: no cut, no merge."""
    rats = {s: json.loads((EVIDENCE/f'{s}-ratsnest.json').read_text()) for s in SIDES}
    data = {s: json.loads((EVIDENCE/f'{s}-rail-clusters.json').read_text()) for s in SIDES}
    for s in SIDES:
        require(data[s]['board_sha256'] == rats[s]['refilled_board_sha256_host'], 'rail cluster board binding '+s)
    out = {}
    for rail, base in data['baseline']['clusters'].items():
        cand = data['candidate']['clusters'][rail]
        where = {p: i for i, c in enumerate(cand) for p in c['pads']}
        surviving = lambda c: tuple(p for p in c['pads'] if p.split('.')[0] not in removed)
        removed_only = [c['pads'] for c in base if not surviving(c)]
        splits = sum(1 for c in base if surviving(c) and len({where.get(p) for p in surviving(c)}) != 1)
        out[rail] = {'clusters': [len(base), len(cand)], 'removed_only_clusters': removed_only,
                     'baseline_clusters_losing_removed_pads': sum(1 for c in base if surviving(c) and len(surviving(c)) < len(c['pads'])),
                     'split_clusters': splits,
                     'identical_after_projection': sorted(surviving(c) for c in base if surviving(c)) == sorted(tuple(c['pads']) for c in cand)}
    return out


def evaluate():
    schematic = json.loads((EVIDENCE/'schematic-receipt.json').read_text())
    pcb = json.loads((EVIDENCE/'pcb-receipt.json').read_text())
    removed = set(schematic['removed_refs']); private = set(schematic['removed_board_net_tokens'])
    for side in SIDES:
        for kind in ('erc', 'drc'):
            r = json.loads((EVIDENCE/f'{side}-{kind}.execution.json').read_text())
            require(r['returncode'] == 0 and r['inputs_unchanged'] and r['output_sha256'] == sha(EVIDENCE/f'{side}-{kind}.json'), f'receipt binding {side} {kind}')
            require(r['command'] == commands(side)[kind], 'command binding')
    require(json.loads((EVIDENCE/'candidate-drc.execution.json').read_text())['input_sha256'][rel(CACHE/'candidate'/BOARD/f'{BOARD}.kicad_pcb')] == pcb['output_sha256'], 'candidate PCB binding')
    require(sha(ROOT/'boards'/BOARD/f'{BOARD}.kicad_pcb') == pcb['source_sha256'], 'baseline PCB is canonical')
    # Baseline ERC/DRC inputs are byte copies of the canonical board tree.
    for kind in ('erc', 'drc'):
        for path, digest in json.loads((EVIDENCE/f'baseline-{kind}.execution.json').read_text())['input_sha256'].items():
            canonical = ROOT/'boards'/BOARD/Path(path).relative_to(rel(CACHE/'baseline'/BOARD))
            if canonical.suffix in ('.kicad_sch', '.kicad_pcb'):
                require(canonical.exists() and sha(canonical) == digest, 'baseline input not canonical '+path)
        cand = json.loads((EVIDENCE/f'candidate-{kind}.execution.json').read_text())['input_sha256']
        for name, digest in schematic['candidate_schematic_sha256'].items():
            require(cand[rel(CACHE/'candidate'/BOARD/name)] == digest, 'candidate schematic binding '+name)
    ev_b, erc_items_b, erc_types_b = erc_summary(EVIDENCE/'baseline-erc.json')
    ev_c, erc_items_c, erc_types_c = erc_summary(EVIDENCE/'candidate-erc.json')
    db, vb, ib, ub = drc_summary(EVIDENCE/'baseline-drc.json')
    dc, vc, ic, uc = drc_summary(EVIDENCE/'candidate-drc.json')
    mentions = lambda items: sorted({t for (_, descs) in items for d in descs for t in removed | private if f' {t} ' in f' {d} ' or f'[{t}]' in d})
    capped_types = sorted({t for (t, _), n in (vb + vc).items() if max(vb[(t, _)], vc[(t, _)]) >= CAP})
    new_drc = {f'{k[0]} :: ' + ' | '.join(k[1]): n for k, n in (ic - ib).items()}
    gone_drc = {f'{k[0]} :: ' + ' | '.join(k[1]): n for k, n in (ib - ic).items()}
    errors = lambda c: sum(n for (t, s), n in c.items() if s == 'error')
    result = {
        'status': 'NATIVE RULE CHECKS of a DISPOSABLE candidate; not adoption, manufacturing, analog or hardware validation',
        'oracle': {'erc': [ev_b, ev_c], 'drc': [db['kicad_version'], dc['kicad_version']]},
        'pcb_removal': {'footprints': len(pcb['removed_footprints']), 'deleted_copper_counts': pcb['deleted_copper_counts'],
                        'candidate_pcb_sha256': pcb['output_sha256'], 'baseline_pcb_sha256': pcb['source_sha256']},
        'erc': {'baseline_types': {f'{t}/{s}': n for (t, s), n in sorted(erc_types_b.items())},
                'candidate_types': {f'{t}/{s}': n for (t, s), n in sorted(erc_types_c.items())},
                'baseline_errors': errors(erc_types_b), 'candidate_errors': errors(erc_types_c),
                'new_violation_signatures': sum((erc_items_c - erc_items_b).values()),
                'removed_violation_signatures': sum((erc_items_b - erc_items_c).values())},
        'drc': {'baseline_types': {f'{t}/{s}': n for (t, s), n in sorted(vb.items())},
                'candidate_types': {f'{t}/{s}': n for (t, s), n in sorted(vc.items())},
                'baseline_errors': errors(vb), 'candidate_errors': errors(vc),
                'schematic_parity': [len(db['schematic_parity']), len(dc['schematic_parity'])],
                'capped_types_at_199': capped_types,
                'new_violation_signatures': new_drc, 'removed_violation_signatures': gone_drc,
                'violations_mentioning_removed_refs_or_nets': {'baseline': mentions(ib), 'candidate': mentions(ic)},
                'parity_items': [[x['type'], x['description'], [i['description'] for i in x['items']]] for x in dc['schematic_parity']],
                'parity_items_not_preexisting_ambiguity': parity_unexplained(dc['schematic_parity'], schematic['multi_unit_field_conflicts']),
                'cli_unconnected_items_truncated': [len(db['unconnected_items']), len(dc['unconnected_items'])],
                'cli_unconnected_note': 'kicad-cli lists at most 499 unconnected items; complete counts are in ratsnest'},
        'ratsnest': ratsnest_delta(private),
        'rail_clusters': rail_cluster_delta(removed),
        'capped_markers_near_removed_parts': capped_near(pcb, capped_types),
    }
    gates = gate(result)
    result['gates'] = gates
    result['capped_type_limit'] = ('Types reaching 199 markers are truncated by KiCad; their nonregression is NOT established '
                                    'by count comparison and is reported as unresolved, as in Stage53.') if capped_types else None
    result['verdict'] = 'PASS' if all(gates.values()) else 'FAIL'
    (HERE/'native-audit.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(result['verdict'], json.dumps(gates))
    return result


if __name__ == '__main__':
    if sys.argv[1:] == ['run']:
        execute(); evaluate()
    elif sys.argv[1:] == ['check']:
        evaluate()
    else:
        raise SystemExit('usage: native.py run|check')
