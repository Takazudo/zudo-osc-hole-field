#!/usr/bin/env python3
"""Small guarded proposal adapter; never applies copper or runs native checks."""
import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys
import subprocess
import time
import check
import matching


def guarded():
    check.require(all(os.environ.get(k) for k in ('EPIC242_NATIVE_SLICE', 'EPIC242_NATIVE_WORKER',
                                                'EPIC242_NATIVE_DEADLINE', 'EPIC242_NATIVE_HANDSHAKE')),
                  'requires separately admitted native_resource_guard worker')
    check.require(float(os.environ['EPIC242_NATIVE_DEADLINE']) > time.time(), 'expired worker deadline')


def numerical_versions():
    expected = {}
    for line in (check.ROOT/'scripts/pcbgen/numerical-requirements.txt').read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            name, required = line.split('==')
            expected[name] = required
    actual = {name: version(name) for name in expected}
    check.require(actual == expected, 'numerical environment version drift')
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domain', required=True, choices=('O1', 'F3', 'E1'))
    parser.add_argument('--board', required=True)
    parser.add_argument('--fixture', required=True, type=Path)
    args = parser.parse_args()
    guarded()  # No numerical imports/raster/search without explicit external admission.
    check.source_checks()
    report = check.read(check.HERE / 'matched-demands.json')
    spec = check.read(check.HERE / 'matching-spec.json')
    check.require(report['spec_sha256'] == check.digest(check.HERE / 'matching-spec.json'), 'stale method specification')
    domain = report['domains'][args.domain]
    check.require(args.board in domain['boards'], 'board outside matched domain')
    fixture = args.fixture.resolve()
    allowed = check.SPLIT / 'candidates/pilots/generated'
    check.require(fixture.is_relative_to(allowed), 'private repo-depth fixture required')
    receipt = check.read(fixture / 'fixture-lock.json')
    matching.validate_fixture_method(receipt, report, args.domain, args.board)
    check.require(receipt['source_tree_sha'] == subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=check.ROOT, text=True).strip(), 'fixture source commit differs from admitted checkout')
    for name, digest in receipt['files'].items():
        check.require(check.digest(fixture / name) == digest, 'fixture input drift: '+name)
    original = check.read(fixture / 'before/dump.json')
    check.require(check.digest(fixture / 'before/dump.json') == report['bindings'][args.board]['dump_sha256'], 'dump input drift')
    check.require(check.digest(fixture / 'before/osc-core.kicad_pcb') == original['board_sha256'], 'board input drift')
    proposal_path = fixture / 'matched-proposal.json'
    check.require(not proposal_path.exists(), 'proposal exists; no automatic retry')
    focused = matching.focused(original, domain)
    (fixture / 'matched-focused-dump.json').write_text(json.dumps(focused, separators=(',', ':'))+'\n')
    sys.path.insert(0, str(check.ROOT))
    versions = numerical_versions()
    from scripts.pcbgen.grid_router import route, copper_rows
    budget, policy = spec['budget'], spec['route_policy']
    diagnostics = []
    started = time.monotonic()
    results, removed = route(
        focused, nets=[domain['targets'][kind]['net_token'] for kind in policy['target_order']],
        res=budget['raster_mm'], clearance=budget['clearance_mm'],
        rail_nets=policy['rail_nets'], rail_width=budget['rail_width_mm'],
        signal_width=budget['signal_width_mm'], via_diameter=budget['via_diameter_mm'],
        via_drill=budget['via_drill_mm'], max_expansions=budget['max_expansions_per_search'],
        window_mm=budget['window_margin_mm'], bounds_mm=domain['common_bounds_mm'],
        planes={}, fill_guards=policy['fill_guards'], rip=(), full_board=False,
        rrr_rounds=0, diagnostics=diagnostics, log=lambda message: print(message, flush=True))
    rows, links = copper_rows(results, f'fixture-253-{args.domain}-{args.board}', 'matched-v1',
                              via_diameter=budget['via_diameter_mm'], via_drill=budget['via_drill_mm'])
    proposal = {'status': 'UNCHECKED PROPOSAL; exact closures and all native gates pending',
                'accepted': False, 'board_sha256': original['board_sha256'], 'removed_uuids': removed,
                'copper': rows, 'links': links,
                'unrouted': [{'net': r['net'], 'island': r['island']} for r in results if not r['path']]}
    matching.validate_proposal(proposal, original)
    proposal_path.write_text(json.dumps(proposal, indent=2)+'\n')
    (fixture / 'matched-search-diagnostics.json').write_text(json.dumps({
        'domain': args.domain, 'board': args.board, 'spec_sha256': report['spec_sha256'],
        'bounds_mm': domain['common_bounds_mm'], 'search_wall_seconds': time.monotonic()-started,
        'diagnostics': diagnostics, 'numerical_versions': versions, 'python_version': sys.version, 'accepted': False}, indent=2)+'\n')


if __name__ == '__main__':
    main()
