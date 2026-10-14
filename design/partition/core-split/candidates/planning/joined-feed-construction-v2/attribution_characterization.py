"""Source-only raw metadata characterization. No CLI or live admission dispatch.

Call only after independent exact request binding inside the existing guard.
Transport interprets the whole trusted pickle; only subsequent descriptor access
is metadata-only. This module does not authenticate an admission grant.
"""
import gc
import hashlib
from pathlib import Path

import attribution_preallocation as G
from attribution_transport import decode, Output, canonical

MAX_CHECKPOINTS = 16_000_000
MAX_ROW_BYTES = 8192
MAX_SUMMARY_BYTES = 4096
SOURCES = ('attribution_characterization.py', 'attribution_preallocation.py',
           'attribution_transport.py', 'resistance_attribution.py')


def source_identity(budget):
    root = Path(__file__).resolve().parent
    identities = {}
    for name in SOURCES:
        h = hashlib.sha256(); size = 0
        with (root / name).open('rb') as source:
            while True:
                budget.check()
                chunk = source.read(65536)
                if not chunk: break
                size += len(chunk)
                G.need(size <= 256 * 1024, 'source identity byte ceiling')
                h.update(chunk)
        identities[name] = h.hexdigest()
    return identities


def binding_identity(binding):
    G.need(type(binding) is dict and set(binding) <= {
        'path', 'bytes', 'sha256', 'decoded_limit', 'format', 'gzip', 'decoded_sha256'}, 'binding keys')
    G.need({'path', 'bytes', 'sha256', 'decoded_limit', 'format'} <= set(binding), 'binding fields')
    path = binding['path']
    G.need(type(path) is str and 0 < len(path) <= 4096 and Path(path).is_absolute(), 'binding path')
    for name in ('bytes', 'decoded_limit'):
        G.need(type(binding[name]) is int and 0 < binding[name] <= 512 * 1024**2, 'binding byte ceiling')
    G.need(binding['format'] == 'pickle' and type(binding.get('gzip', True)) is bool, 'operator encoding')
    for name in ('sha256', 'decoded_sha256'):
        if name in binding:
            value = binding[name]
            G.need(type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'binding digest')
    # Do not retain paths/large objects in component output. Bind the exact record.
    return hashlib.sha256(canonical(binding)).hexdigest()


def bounds(metadata):
    """Report an excessive raw bound as evidence, never successful preflight."""
    n = metadata['N']; lengths = metadata['terminal_lengths']; t = len(lengths)
    k = metadata['face_stored'] + metadata['inner_stored'] + 4 * metadata['barrel_intervals']
    outer = sum(s*s for s in lengths); largest = max(s*s for s in lengths)
    raw = k + outer
    arrays = {'coordinate_conversion_arrays_upper': 80*raw + 8*(n+1),
              'active_outer_float_buffers_upper': 16*largest,
              'dense_B_D_upper': 8*n*t + 8*t*t}
    return {'metadata': metadata, 'K_stored_upper': k, 'termination_raw_triples': outer,
            'raw_coordinate_upper': raw, 'largest_outer_entries': largest,
            'raw_ceiling': G.MAX_RAW_ENTRIES,
            'raw_bound_outcome': 'WITHIN_RAW_BOUND' if raw <= G.MAX_RAW_ENTRIES else 'EXCEEDS_RAW_BOUND',
            'named_array_bytes': arrays, 'named_array_bytes_upper': sum(arrays.values()),
            'full_pipeline_qualification': 'NOT_QUALIFIED'}


def _one(binding, budget, checkpoint):
    op = None; report = None; error = None
    try:
        op = decode(binding, budget)
        report = bounds(G.extract_metadata(op, checkpoint))
        checkpoint()
    except Exception as exc:
        # Preserve only bounded text, not traceback frames retaining the operator.
        error = str(exc)[:2048]
    finally:
        op = None
        gc.collect()
    return report, error


def characterize(bindings, output_root, budget):
    """Two sequential exact operator bindings, inherited clock/output accounting.

    COMPLETE means characterization output exhausted, never qualification.
    Failures after Output creation receive a module INCOMPLETE receipt; early
    validation/output-creation failures belong to the authenticated outer host
    failure lifecycle. This function grants no execution right.
    """
    budget.check()
    G.need(type(bindings) is dict and set(bindings) == {'KA', 'KB'}, 'exact KA/KB operator bindings required')
    identities = {board: binding_identity(bindings[board]) for board in ('KA', 'KB')}
    source_hashes = source_identity(budget)
    checkpoints = 0
    def checkpoint():
        nonlocal checkpoints
        checkpoints += 1
        G.need(checkpoints <= MAX_CHECKPOINTS, 'aggregate metadata checkpoint ceiling')
        budget.check()
    output = Output(output_root, budget)
    try:
        for board in ('KA', 'KB'):
            budget.phase = 'raw-metadata-' + board
            report, error = _one(bindings[board], budget, checkpoint)
            if error is not None:
                raise ValueError(error)
            row = {'board': board, 'purpose': 'CHARACTERIZATION_ONLY',
                   'operator_binding_sha256': identities[board], **report}
            G.need(len(canonical(row)) <= MAX_ROW_BYTES, 'characterization row output ceiling')
            output.row(row)
            del report, row
        summary = {'purpose': 'CHARACTERIZATION_ONLY', 'full_pipeline_qualification': 'NOT_QUALIFIED',
                   'source_sha256': source_hashes, 'operator_bindings_sha256': identities,
                   'metadata_checkpoints': checkpoints, 'max_metadata_checkpoints': MAX_CHECKPOINTS,
                   'access_scope': 'decode supplied KA/KB operator only; descriptor sizes/shapes/dtypes/support lengths; no construction, solve, mesh or numerical coefficient inspection',
                   'lifetime': 'each decoded operator released and garbage collection completed before next decode',
                   'resource_scope': 'pickle object graph requires existing enforced worker memory; no complete construction envelope'}
        G.need(source_identity(budget) == source_hashes, 'characterization source changed')
        G.need(len(canonical(summary)) <= MAX_SUMMARY_BYTES, 'characterization summary ceiling')
        return output.finish(summary)
    except BaseException as exc:
        output.fail(exc)
        raise
