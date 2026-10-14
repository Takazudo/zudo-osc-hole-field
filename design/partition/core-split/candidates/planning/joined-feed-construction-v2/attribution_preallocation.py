"""Metadata-only construction preflight; neither an execution grant nor a heap proof.

Call only on already admitted/decoded inputs. The existing worker admission does
not enable this new internal path. A future caller must bind/review its declared
allocation envelope independently; this helper cannot authenticate that review.
No original coefficient, support weight or node-index value is read here.
"""

MAX_RAW_ENTRIES = 16_000_000
WORKER_BYTES = 1216 * 1024**2
ENVELOPE_FIELDS = {
    'live_baseline_bytes_upper', 'other_constructor_bytes_upper',
    'native_workspace_bytes_upper', 'allocator_and_tail_bytes_upper',
    'evidence_reference',
}


def need(condition, message):
    if not condition:
        raise ValueError('raw-stamp preallocation: ' + message)


def integer(value, name, minimum=0):
    need(type(value) is int and minimum <= value, name + ' must be an exact bounded integer')
    return value


def array_metadata(a, kind, name):
    """Read descriptors, never convert/copy or index an array."""
    need(a.ndim == 1, name + ' must be one dimensional')
    size = integer(a.size, name + ' size')
    need(a.shape == (size,), name + ' shape differs')
    if kind == 'float':
        need(a.dtype.name == 'float64' and a.dtype.itemsize == 8, name + ' must be binary64')
    else:
        need(a.dtype.kind == 'i' and a.dtype.itemsize in (4, 8), name + ' index dtype unsupported')
    return size


def extract_metadata(op, checkpoint):
    """Bounded descriptor traversal within the caller's existing deadline."""
    checkpoint()
    need(type(op) is dict, 'operator metadata must be a dictionary')
    n = integer(op['N'], 'N', 1)
    need(n <= MAX_RAW_ENTRIES, 'node bound exceeds structural preflight ceiling')
    visits = 0

    def visit():
        nonlocal visits
        visits += 1
        need(visits <= MAX_RAW_ENTRIES, 'metadata visit cap')
        checkpoint()

    stored = []
    for name in ('Kg_face', 'Kg_inner'):
        visit()
        a = op[name]
        need(a.format == 'csr' and a.shape == (n, n), name + ' CSR/shape differs')
        need(a.dtype.name == 'float64', name + ' must be binary64')
        count = array_metadata(a.data, 'float', name + ' data')
        need(count <= MAX_RAW_ENTRIES, name + ' stored-array ceiling')
        need(array_metadata(a.indices, 'index', name + ' indices') == count,
             name + ' index/data length differs')
        need(array_metadata(a.indptr, 'index', name + ' pointers') == n + 1,
             name + ' pointer length differs')
        stored.append(count)
    need(type(op['barrels']) is dict, 'barrel metadata type')
    intervals = 0
    for barrel in op['barrels'].values():
        visit()
        need(type(barrel) is dict and type(barrel['taps']) in (list, tuple), 'barrel tap metadata type')
        intervals += max(len(barrel['taps']) - 1, 0)
        need(4 * intervals <= MAX_RAW_ENTRIES, 'raw barrel ceiling')
    terminals = op['terminals']
    need(type(terminals) in (list, tuple) and 0 < len(terminals) <= 8,
         'terminal count/type outside existing border contract')
    need(all(type(t) is str for t in terminals) and len(set(terminals)) == len(terminals),
         'duplicate/nonstring terminal identity')
    need(type(op['supports']) is dict, 'support metadata type')
    lengths = []
    for terminal in terminals:
        visit()
        need(terminal in op['supports'], 'missing actual terminal support')
        pair = op['supports'][terminal]
        need(type(pair) in (list, tuple) and len(pair) == 2, 'terminal support pair shape')
        size = array_metadata(pair[0], 'index', 'support nodes')
        need(size <= MAX_RAW_ENTRIES, 'support length ceiling')
        need(array_metadata(pair[1], 'float', 'support weights') == size, 'support lengths differ')
        lengths.append(size)
    return {'N': n, 'face_stored': stored[0], 'inner_stored': stored[1],
            'barrel_intervals': intervals, 'terminal_lengths': tuple(lengths),
            'metadata_visits': visits}


def construction_bounds(metadata, max_raw_entries):
    """Pure integer bounds, including duplicates, zeros and held supports."""
    need(type(metadata) is dict and set(metadata) == {
        'N', 'face_stored', 'inner_stored', 'barrel_intervals', 'terminal_lengths', 'metadata_visits'},
        'structural metadata schema')
    ceiling = integer(max_raw_entries, 'raw entry ceiling', 1)
    need(ceiling <= MAX_RAW_ENTRIES, 'raw entry ceiling increase forbidden')
    n = integer(metadata['N'], 'N', 1)
    need(n <= MAX_RAW_ENTRIES, 'node bound exceeds structural preflight ceiling')
    face = integer(metadata['face_stored'], 'face stored')
    inner = integer(metadata['inner_stored'], 'inner stored')
    intervals = integer(metadata['barrel_intervals'], 'barrel intervals')
    visits = integer(metadata['metadata_visits'], 'metadata visits')
    need(max(face, inner, intervals, visits) <= MAX_RAW_ENTRIES, 'structural count ceiling')
    lengths = metadata['terminal_lengths']
    need(type(lengths) is tuple and 0 < len(lengths) <= 8, 'terminal length tuple')
    for size in lengths:
        need(integer(size, 'support length') <= MAX_RAW_ENTRIES, 'support length ceiling')
    barrel = 4 * intervals
    k_upper = face + inner + barrel
    stamps = sum(size * size for size in lengths)
    raw = k_upper + stamps
    need(raw <= ceiling, f'raw coordinate ceiling exceeded (upper={raw}, maximum={ceiling})')
    largest = max(size * size for size in lengths)
    terminal_count = len(lengths)
    named_arrays = {
        # Original + concatenated triples, copied COO indices and compressed output.
        'coordinate_conversion_arrays_upper': 80 * raw + 8 * (n + 1),
        'active_outer_float_buffers_upper': 16 * largest,
        'dense_B_D_upper': 8 * n * terminal_count + 8 * terminal_count**2,
    }
    return {'method': 'metadata-raw-stamp-preflight-v1', 'raw_preflight': 'PASS',
            'N': n, 'terminal_count': terminal_count, 'metadata_visits': visits,
            'barrel_raw_triples': barrel, 'K_stored_upper': k_upper,
            'termination_raw_triples': stamps, 'largest_outer_entries': largest,
            'raw_coordinate_upper': raw, 'max_raw_entries': ceiling,
            'named_array_bytes': named_arrays, 'named_array_bytes_upper': sum(named_arrays.values()),
            'full_pipeline_qualification': 'NOT_QUALIFIED',
            'scope': 'structural raw bound only; native workspace, masks, sparse class operations and live baseline are separate'}


def require_declared_envelope(report, envelope):
    """Check a caller-owned, separately reviewed declaration; do not certify it.

    Nothing in the production request compiler supplies this declaration today.
    Missing terms refuse before numerical allocation. The evidence reference is
    a traceable caller assertion, not an authenticated approval or a fit result.
    """
    need(type(envelope) is dict and set(envelope) == ENVELOPE_FIELDS,
         'complete declared memory envelope unavailable (NOT_QUALIFIED)')
    reference = envelope['evidence_reference']
    need(type(reference) is str and 0 < len(reference) <= 512, 'memory evidence reference missing')
    extras = {}
    for name in ENVELOPE_FIELDS - {'evidence_reference'}:
        extras[name] = integer(envelope[name], name)
        need(extras[name] <= WORKER_BYTES, 'declared memory component exceeds worker cap')
    # Zero may be justified for a tiny special case, but every named term must be explicit.
    total = report['named_array_bytes_upper'] + sum(extras.values())
    need(total <= WORKER_BYTES, f'declared construction envelope exceeds worker cap ({total}>{WORKER_BYTES})')
    return {**report, 'declared_envelope_gate': 'PASS', 'declared_worker_bytes_upper': total,
            'worker_bytes': WORKER_BYTES, 'envelope_components': extras,
            'envelope_evidence_reference': reference,
            'scope': 'raw bound and caller-declared construction envelope; no execution authority or full-pipeline qualification'}


def preflight(op, policy, checkpoint):
    need(type(policy) is dict and set(policy) == {'max_raw_entries', 'memory_envelope'}, 'internal policy schema')
    metadata = extract_metadata(op, checkpoint)
    report = construction_bounds(metadata, policy['max_raw_entries'])
    checkpoint()
    return require_declared_envelope(report, policy['memory_envelope'])
