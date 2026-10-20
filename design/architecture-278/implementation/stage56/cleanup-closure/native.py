"""Stage56 native gates. The baseline side is the retained Stage55 canonical-copy evidence
(same canonical inputs, bound by hash); only the candidate is executed here.

Usage: native.py run | audit | check   (check compares with the retained native-audit.json)
"""
from pathlib import Path
from collections import Counter
import importlib.util, json, subprocess, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
S55 = ROOT/'design/architecture-278/implementation/stage55/idle-quad-cleanup'
CACHE = ROOT/'.circuit-cache/stage56'
EVIDENCE = HERE/'evidence'
BOARD = 'osc-core'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


n55 = load('stage55_native', S55/'native.py')
sha, require, rel = n55.sha, n55.require, n55.rel
CAND = CACHE/'candidate'/BOARD


def commands():
    return {
        'erc': ['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'sch', 'erc', '--format', 'json', '--severity-all',
                '-o', rel(CACHE/'candidate-erc.json'), rel(CAND/f'{BOARD}.kicad_sch')],
        'drc': ['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'pcb', 'drc', '--schematic-parity', '--refill-zones',
                '--format', 'json', '--severity-all', '-o', rel(CACHE/'candidate-drc.json'), rel(CAND/f'{BOARD}.kicad_pcb')],
        'ratsnest': ['bash', 'scripts/kicad/run.sh', 'python3', rel(S55/'ratsnest_refilled.py'), rel(CAND/f'{BOARD}.kicad_pcb'),
                     rel(CACHE/'candidate-refilled.kicad_pcb'), rel(CACHE/'candidate-ratsnest.json')],
        'rail-clusters': ['bash', 'scripts/kicad/run.sh', 'python3', rel(S55/'rail_clusters.py'), rel(CACHE/'candidate-refilled.kicad_pcb'),
                          rel(CACHE/'candidate-rail-clusters.json')],
    }


def inputs():
    return {rel(p): sha(p) for p in sorted(CAND.rglob('*')) if p.is_file() and p.suffix in ('.kicad_sch', '.kicad_pcb', '.kicad_pro', '.kicad_dru')}


def execute():
    EVIDENCE.mkdir(exist_ok=True)
    for kind, cmd in commands().items():
        out = CACHE/f'candidate-{kind}.json'
        require(not out.exists(), 'refuse overwrite '+rel(out))
        before = inputs()
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        receipt = {'command': cmd, 'returncode': r.returncode, 'stdout_tail': r.stdout[-4000:], 'stderr_tail': r.stderr[-4000:],
                   'input_sha256': before, 'inputs_unchanged': inputs() == before, 'output_sha256': sha(out) if out.exists() else None}
        if kind == 'ratsnest' and out.exists():
            data = json.loads(out.read_text())
            data['source_sha256_host'] = sha(CAND/f'{BOARD}.kicad_pcb')
            data['refilled_board_sha256_host'] = sha(CACHE/'candidate-refilled.kicad_pcb')
            out.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n'); receipt['output_sha256'] = sha(out)
        if out.exists():
            (EVIDENCE/out.name).write_bytes(out.read_bytes())
        (EVIDENCE/f'candidate-{kind}.execution.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
        require(r.returncode == 0 and receipt['inputs_unchanged'], f'candidate {kind} failed; receipt retained')


def gate(result):
    d, r = result['drc'], result['ratsnest']
    return {
        'oracle_10_0_6': all(v == '10.0.6' for v in result['oracle']),
        'erc_errors_zero_and_signatures_unchanged': result['erc']['candidate_errors'] == 0 and result['erc']['new_violation_signatures'] == 0,
        'no_drc_errors': d['candidate_errors'] == 0,
        'baseline_schematic_parity_zero': d['baseline_schematic_parity'] == 0,
        'schematic_parity_zero': d['schematic_parity'] == 0,
        'no_new_uncapped_drc_signatures': all(k.split(' :: ')[0] in d['capped_types_at_199'] for k in d['new_violation_signatures']),
        'no_candidate_violation_names_removed_item': d['violations_mentioning_removed_refs_or_nets'] == [],
        'complete_ratsnest_no_net_gains_edges': r['nets_with_more_edges'] == {},
        'complete_ratsnest_no_new_open_net': r['new_open_nets'] == [],
        'removed_private_nets_absent_from_ratsnest': r['candidate_private_net_edges'] == 0,
        'rail_clusters_equal_baseline_minus_removed_pads': all(v['identical_after_projection'] and v['split_clusters'] == 0
                                                               for v in result['rail_clusters'].values()),
    }


def evaluate(write=True):
    sch = json.loads((EVIDENCE/'schematic-receipt.json').read_text())
    pcb = json.loads((EVIDENCE/'pcb-receipt.json').read_text())
    fields = json.loads((EVIDENCE/'fields-receipt.json').read_text())
    removed, private = set(sch['removed_refs']), set(sch['removed_board_net_tokens'])
    require(pcb['source_sha256'] == sha(ROOT/'boards'/BOARD/f'{BOARD}.kicad_pcb'), 'cleanup input is canonical')
    require(fields['input_sha256'] == pcb['output_sha256'], 'field step follows cleanup')
    cand_pcb = rel(CAND/f'{BOARD}.kicad_pcb')
    for kind, cmd in commands().items():
        r = json.loads((EVIDENCE/f'candidate-{kind}.execution.json').read_text())
        require(r['command'] == cmd and r['returncode'] == 0 and r['inputs_unchanged'], 'receipt '+kind)
        require(r['output_sha256'] == sha(EVIDENCE/f'candidate-{kind}.json'), 'output binding '+kind)
        require(r['input_sha256'][cand_pcb] == fields['output_sha256'], 'candidate PCB binding '+kind)
        for name, digest in sch['candidate_schematic_sha256'].items():
            require(r['input_sha256'][rel(CAND/name)] == digest, 'candidate schematic binding '+name)
        for path, digest in r['input_sha256'].items():
            name = Path(path).relative_to(rel(CAND)).as_posix()
            if path != cand_pcb and name not in sch['candidate_schematic_sha256']:
                require(digest == sha(ROOT/'boards'/BOARD/name), 'unchanged input equals canonical '+name)
    # Stage55 baseline evidence is of the same canonical inputs.
    s55 = json.loads((S55/'evidence/pcb-receipt.json').read_text())
    require(s55['source_sha256'] == pcb['source_sha256'], 'Stage55 baseline is the same canonical board')
    ev_b, erc_b, _ = n55.erc_summary(S55/'evidence/baseline-erc.json')
    ev_c, erc_c, erc_types_c = n55.erc_summary(EVIDENCE/'candidate-erc.json')
    db, vb, ib, _ = n55.drc_summary(S55/'evidence/baseline-drc.json')
    dc, vc, ic, _ = n55.drc_summary(EVIDENCE/'candidate-drc.json')
    capped = sorted({t for (t, s) in set(vb) | set(vc) if max(vb[(t, s)], vc[(t, s)]) >= n55.CAP})
    names = removed | private
    mentions = sorted({t for (_, descs) in ic for x in descs for t in names if f' {t} ' in f' {x} ' or f'[{t}]' in x})
    rb = json.loads((S55/'evidence/baseline-ratsnest.json').read_text())
    rc = json.loads((EVIDENCE/'candidate-ratsnest.json').read_text())
    require(rb['source_sha256_host'] == pcb['source_sha256'] and rc['source_sha256_host'] == fields['output_sha256'], 'ratsnest bindings')
    eb, ec = rb['native_open_edges_by_net'], rc['native_open_edges_by_net']
    cb = json.loads((S55/'evidence/baseline-rail-clusters.json').read_text())
    cc = json.loads((EVIDENCE/'candidate-rail-clusters.json').read_text())
    require(cb['board_sha256'] == rb['refilled_board_sha256_host'] and cc['board_sha256'] == rc['refilled_board_sha256_host'], 'cluster bindings')
    clusters = {}
    require(set(cb['clusters']) == set(cc['clusters']), 'rail cluster roster')
    for rail, base in cb['clusters'].items():
        cand = cc['clusters'][rail]; where = {p: i for i, c in enumerate(cand) for p in c['pads']}
        surv = lambda c: tuple(p for p in c['pads'] if p.split('.')[0] not in removed)
        clusters[rail] = {'clusters': [len(base), len(cand)], 'removed_only_clusters': [c['pads'] for c in base if not surv(c)],
                          'split_clusters': sum(1 for c in base if surv(c) and len({where.get(p) for p in surv(c)}) != 1),
                          'identical_after_projection': sorted(surv(c) for c in base if surv(c)) == sorted(tuple(c['pads']) for c in cand)}
    errors = lambda c: sum(k for (t, s), k in c.items() if s == 'error')
    result = {
        'status': 'NATIVE RULE CHECKS of the DISPOSABLE Stage56 candidate; not adoption or validation',
        'oracle': [ev_b, ev_c, db['kicad_version'], dc['kicad_version']],
        'erc': {'candidate_types': {f'{t}/{s}': k for (t, s), k in sorted(erc_types_c.items())}, 'candidate_errors': errors(erc_types_c),
                'new_violation_signatures': sum((erc_c - erc_b).values()), 'removed_violation_signatures': sum((erc_b - erc_c).values())},
        'drc': {'baseline_types': {f'{t}/{s}': k for (t, s), k in sorted(vb.items())},
                'candidate_types': {f'{t}/{s}': k for (t, s), k in sorted(vc.items())},
                'candidate_errors': errors(vc), 'schematic_parity': len(dc['schematic_parity']),
                'baseline_schematic_parity': len(db['schematic_parity']),
                'parity_items': [x['description'] for x in dc['schematic_parity']],
                'capped_types_at_199': capped,
                'new_violation_signatures': {f'{k[0]} :: ' + ' | '.join(k[1]): v for k, v in (ic - ib).items()},
                'removed_violation_signature_count': sum((ib - ic).values()),
                'violations_mentioning_removed_refs_or_nets': mentions},
        'ratsnest': {'native_unconnected_edges': [rb['native_unconnected_edges'], rc['native_unconnected_edges']],
                     'nets_with_fewer_edges': {k: [eb[k], ec.get(k, 0)] for k in sorted(eb) if ec.get(k, 0) < eb[k]},
                     'nets_with_more_edges': {k: [eb.get(k, 0), ec[k]] for k in sorted(ec) if ec[k] > eb.get(k, 0)},
                     'new_open_nets': sorted(set(ec) - set(eb)), 'candidate_private_net_edges': sum(ec.get(k, 0) for k in private)},
        'rail_clusters': clusters,
        'field_sync': {k: fields[k] for k in ('field_syncs', 'requested_field_syncs', 'deleted', 'emptied', 'decouples_updates')},
    }
    result['gates'] = gate(result)
    result['verdict'] = 'PASS' if all(result['gates'].values()) else 'FAIL'
    body = json.dumps(result, indent=2, sort_keys=True)+'\n'
    if write:
        (HERE/'native-audit.json').write_text(body)
    else:
        require((HERE/'native-audit.json').read_text() == body, 'native audit replay drift')
    print(result['verdict'], json.dumps(result['gates']))
    return result


if __name__ == '__main__':
    if sys.argv[1:] == ['run']:
        execute(); evaluate()
    elif sys.argv[1:] == ['audit']:
        evaluate()
    elif sys.argv[1:] == ['check']:
        evaluate(write=False)
    else:
        raise SystemExit('usage: native.py run|audit|check')
