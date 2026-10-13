#!/usr/bin/env python3
"""Separately admitted F3 proposal only; no apply/native acceptance action."""
import argparse
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from route_matched import guarded, numerical_versions
import check
import matching
from f3_fixture import validate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board', choices=('K1402', 'two-A'), required=True)
    p.add_argument('--fixture', type=Path, required=True)
    p.add_argument('--fixture-lock-sha256', required=True, help='Literal immutable digest from reviewed packet')
    args = p.parse_args()
    guarded()  # Before numerical/raster/adapter imports; parent admission required.
    versions = numerical_versions()
    fixture = args.fixture.resolve()
    check.require(fixture.is_relative_to(check.SPLIT/'candidates/pilots/generated'), 'private fixture required')
    check.require(not (fixture/'matched-proposal.json').exists(), 'no retry/overwrite')
    original, manifest, lock = validate(fixture, args.board, args.fixture_lock_sha256)
    from f3_adapter import run, saved_pool
    spec = check.read(HERE.parent/'matching-spec.json')
    evidence = check.read(HERE/'cohort-validation.json')
    domain = manifest['domains']['F3']
    started = time.monotonic()
    proposal = run(original, domain, saved_pool(evidence, domain), spec['budget'], spec['route_policy'], args.board)
    validate(fixture, args.board, args.fixture_lock_sha256)  # Recheck every sealed input after search.
    matching.validate_proposal(proposal, original)
    check.require(len(proposal['demands']) == 4 and not proposal['coupled_connectivity_success'], 'demand/credit contract')
    (fixture/'matched-proposal.json').write_text(json.dumps(proposal, indent=2)+'\n')
    (fixture/'matched-search-diagnostics.json').write_text(json.dumps({
        'domain': 'F3', 'board': args.board, 'method_sha': lock['source_tree_sha'],
        'original_input_method_sha': lock['original_input_method_sha'], 'access_tool_sha256': lock['access_tool_sha256'],
        'bounds_mm': domain['common_bounds_mm'], 'search_wall_seconds': time.monotonic()-started,
        'demands': proposal['demands'], 'numerical_versions': versions, 'accepted': False,
        'native_exact_pair_closed': False, 'coupled_connectivity_success': False}, indent=2)+'\n')


if __name__ == '__main__':
    main()
