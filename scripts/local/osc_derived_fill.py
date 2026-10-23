"""Derived-copy identity, reuse verification and pair classification (option C).

The published core is saved without zone fills on purpose (publication_copy
strips them above the 95 MiB cap), so a reader that does not refill cannot
tell a real wiring gap from a connection it simply cannot evaluate. This
module gives the diagnostic side a shared, pcbnew-free vocabulary for that:

- identity: the composite key of a derived board (source pins, project and
  rules, pinned image, KiCad version, selected zones, process version,
  optional parent derivation). Any change yields a different key.
- verify_derived: before reusing a saved derived board, recompute the real
  file hashes, the non-fill semantic hash against the current source and
  the fill ownership; a stale, altered or differently derived copy is
  rejected with a reason and is never success evidence.
- classify_pair: the status vocabulary that keeps "open because unfilled"
  apart from "open with every zone of the net filled". Neither is a repair
  verdict or board acceptance.
"""
import json
import re
from pathlib import Path

from osc_frozen_fill import MEMORY_CAP, digest, sha
from osc_single_zone_payload import PCB_LIMIT, WORKER_RESERVE, zone_fill_owners

PROCESS_VERSION = 'derived-fill/1'
MANIFEST_STATUS = 'DERIVED_FILL_MANIFEST_NOT_ACCEPTANCE'
LEGACY_STATUS = 'SINGLE_ZONE_CANDIDATE_EXPORTED_NOT_ACCEPTANCE'
SIDECAR = 'derived-identity.json'
KICAD_VERSION = '10.0.6'
BOARD_FILES = ('osc-core.kicad_pcb', 'osc-core.kicad_pro', 'osc-core.kicad_dru')
ZONE_LIMIT = 8
PAIR_LIMIT = 16
# CLEANUP_RESERVE mirrors hosted osc_fill_check.CLEANUP_RESERVE and SCRATCH_TMPFS_BYTES mirrors the '/scratch ... size=256m' mount in
# osc_fill_check.readonly_args; the hosted module is not part of the container bundle, so the local controller asserts both at import.
CLEANUP_RESERVE = 40
SCRATCH_TMPFS_BYTES = 256 * 1024 * 1024
SOURCE_BOARD_BYTES = 49819556   # pinned frozen core osc-core.kicad_pcb; the controller checks the real size against this
RUN3_PARENT_KEY = 'ecf170dbb48e07980d8c08e149ff6e5c223745b58cdd9f9abb09cfa4b5001d16'   # derive run 3: F.Cu AGND filled on the frozen core
RUN3_PARENT_BOARD_BYTES = 61320854
RUN3_PARENT_BOARD_SHA256 = '4a55e0c165efcc2215d920272da25476b54df1cc56ba59e95a31049b29ba4dc8'
TMPFS_SHARE_OF_MEMORY = 8      # tmpfs pages are charged to the 2 GiB cgroup: the input copy plus the output bound may use at most 1/8 of it
# Deadline chains, innermost first. 'standard' is the proven hosted-parity chain. 'fill-520-probe' is the
# single user-approved probe of the AGND F.Cu zone (2026-10-22 19:56 UTC): only the fill cap and the layers
# that must contain it grow; CPU, memory, swap, PIDs, network and mounts are unchanged. The output board bound
# grows because the F.Cu fill adds more polygon vertices than the inner-layer fills (In1.Cu added 11.3 MB to
# the 47.5 MiB source; the standard 64 MiB bound leaves 17.3 MB) while still fitting the 256 MiB scratch tmpfs
# next to the input copy.
BUDGETS = {
    'standard': {'payload': 420, 'stage_caps': {'prepare': 60, 'fill': 260, 'verify': 100}, 'attach': 430, 'wrapper': 450, 'controller': 590,
                 'outer_stop': 600, 'post_stop_cleanup': 60, 'heavy_guard_max_run': 720, 'pcb_limit': PCB_LIMIT,
                 'modes': ('zone', 'candidate', 'drc', 'derive', 'evaluate'), 'zones': None},
    'fill-520-probe': {'payload': 760, 'stage_caps': {'prepare': 60, 'fill': 520, 'verify': 100}, 'attach': 780, 'wrapper': 800, 'controller': 890,
                       'outer_stop': 900, 'post_stop_cleanup': 60, 'heavy_guard_max_run': 1020, 'pcb_limit': 128 * 1024 * 1024,
                       'modes': ('derive',), 'zones': ['601e02b2-8ccb-5c28-83e5-03789d47fbbd']},
    # Single user-approved chained diagnostic (2026-10-23 02:46 UTC, coordinator osc-moya-approved-queued-agnd-b6208767): the standard
    # time chain, the 128 MiB output bound, and a binding to the run-3 parent copy plus the two remaining AGND zones.
    'chained-agnd': {'payload': 420, 'stage_caps': {'prepare': 60, 'fill': 260, 'verify': 100}, 'attach': 430, 'wrapper': 450, 'controller': 590,
                     'outer_stop': 600, 'post_stop_cleanup': 60, 'heavy_guard_max_run': 720, 'pcb_limit': 128 * 1024 * 1024,
                     'modes': ('derive',), 'zones': ['e389d344-872d-538e-9bfc-39577adb1686', 'e67a5bc7-b575-52b6-a78a-9c84381053da'],
                     'parent_key': RUN3_PARENT_KEY, 'input_board_bytes': RUN3_PARENT_BOARD_BYTES, 'parent_board_sha256': RUN3_PARENT_BOARD_SHA256},
}


def footprint_check(*parts):
    """Every board copy in the scratch tmpfs is charged to the container's memory cgroup: the sum must fit the tmpfs and its share of the cap."""
    if any(type(p) is not int or p <= 0 for p in parts): raise ValueError('footprint parts')
    total = sum(parts)
    if total > SCRATCH_TMPFS_BYTES: raise ValueError('scratch footprint %d does not fit the %d-byte tmpfs' % (total, SCRATCH_TMPFS_BYTES))
    if total > MEMORY_CAP // TMPFS_SHARE_OF_MEMORY: raise ValueError('scratch footprint %d takes more than its share of the memory cap' % total)
    return total


def budget(name):
    """One deadline chain, checked for containment at every layer; a profile whose layers do not nest is a defect, not a setting."""
    if name not in BUDGETS: raise ValueError('unknown budget profile')
    b = BUDGETS[name]; caps = b['stage_caps']
    if set(caps) != {'prepare', 'fill', 'verify'} or any(type(v) is not int or v <= 0 for v in caps.values()): raise ValueError('stage caps')
    if max(caps.values()) > b['payload'] - WORKER_RESERVE: raise ValueError('a stage cap cannot be reached before the worker deadline')
    if b['attach'] < b['payload'] + 10: raise ValueError('attach does not contain the payload')
    if b['wrapper'] < b['attach'] + 17: raise ValueError('wrapper does not contain attach plus create')
    if b['controller'] < b['wrapper'] + CLEANUP_RESERVE + 7 + 40: raise ValueError('controller leaves under 40 s of setup before launch')
    if b['outer_stop'] <= b['controller']: raise ValueError('outer stop does not contain the controller')
    if b['heavy_guard_max_run'] < b['outer_stop'] + b['post_stop_cleanup'] + 60: raise ValueError('heavy-guard cap does not contain outer stop and cleanup')
    if b['zones'] is not None and (not b['zones'] or any(not UUID_RE.match(z) for z in b['zones'])): raise ValueError('budget zones')
    parent_key = b.get('parent_key')
    if parent_key is None:
        # Unbound profiles always start from the published source; a declared input size would be an unchecked number.
        if 'input_board_bytes' in b or 'parent_board_sha256' in b: raise ValueError('input size or parent hash declared without a parent binding')
        input_bytes = SOURCE_BOARD_BYTES; parent_sha = None
    else:
        input_bytes = b.get('input_board_bytes'); parent_sha = b.get('parent_board_sha256')
        if not hash_ok(parent_key) or b['zones'] is None or type(input_bytes) is not int or input_bytes <= 0 or not hash_ok(parent_sha) or 'derive' not in b['modes'] or len(b['modes']) != 1: raise ValueError('budget parent binding')
    footprint_check(input_bytes, b['pcb_limit'])
    return {**b, 'name': name, 'parent_key': parent_key, 'input_board_bytes': input_bytes, 'parent_board_sha256': parent_sha, 'launch_reserve': b['wrapper'] + CLEANUP_RESERVE + 7, 'worker_deadline': b['payload'] - WORKER_RESERVE}


def budget_allows(b, mode, zones, chained=False, parent_key=None):
    """A bound profile covers exactly its approved mode, zone set and input: the published source (no parent) or one named parent derivation."""
    if mode not in b['modes']: raise ValueError('budget ' + b['name'] + ' does not cover payload ' + mode)
    if b['zones'] is not None and sorted(zones or []) != sorted(b['zones']): raise ValueError('budget ' + b['name'] + ' is bound to a different zone set')
    if b['zones'] is not None and b['parent_key'] is None and chained: raise ValueError('budget ' + b['name'] + ' does not cover a chained derivation: its input board would not be the published source')
    if b['parent_key'] is not None:
        if not chained: raise ValueError('budget ' + b['name'] + ' covers only a derivation chained from its approved parent')
        if parent_key != b['parent_key']: raise ValueError('budget ' + b['name'] + ' is bound to a different parent derivation')


def parent_record(candidate_dir):
    """Identity key and exported board hash recorded by a parent derivation's own manifest; any unreadable or malformed input is a ValueError."""
    candidate_dir = Path(candidate_dir)
    try:
        manifest = json.loads((candidate_dir / 'manifest.json').read_text())
        ident, _, exported, _ = manifest_identity(manifest, candidate_dir)
        return identity_key(ident), exported['osc-core.kicad_pcb']
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError('parent manifest: ' + type(exc).__name__ + ': ' + str(exc)[:200])


def parent_board(candidate_dir):
    """The parent's board file as the tmpfs input copy: a regular file, never a symlink; returns its size."""
    board = Path(candidate_dir) / 'after' / 'osc-core.kicad_pcb'
    if board.is_symlink() or not board.is_file(): raise ValueError('parent board missing or symlinked')
    return board.stat().st_size


def check_bound_parent(b, recorded_key, exported_sha, board_bytes, actual_sha=None):
    """For a parent-bound profile, the mounted parent must be the approved file: key, recorded hash, size and (when given) the real file hash."""
    if b['parent_key'] is None: return
    if recorded_key != b['parent_key']: raise ValueError('budget ' + b['name'] + ' is bound to a different parent derivation')
    if exported_sha != b['parent_board_sha256']: raise ValueError('parent manifest records a board other than the one bound to budget ' + b['name'])
    if board_bytes != b['input_board_bytes']: raise ValueError('parent board size differs from the budget table assumption')
    if actual_sha is not None and actual_sha != b['parent_board_sha256']: raise ValueError('parent board file differs from the one bound to budget ' + b['name'])
UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
CLASSES = {
    'CONNECTED_ON_INPUT': 'pads shared a native cluster on the input board before this derivation filled anything',
    'CONNECTED_VIA_SELECTED_FILL': 'open on the input board, connected after filling only the selected zones: the open was a missing fill cache, not a wiring gap',
    'UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN': 'still open, but copper zones of this net remain unfilled on the derived board, so connectivity cannot be evaluated; not a repair basis',
    'OPEN_WITH_ALL_NET_ZONES_FILLED': 'still open although every copper zone of this net is filled on the derived board: a wiring-gap candidate for review, not a verdict',
    'OPEN_WITHOUT_NET_ZONES': 'still open and this net has no copper zone, so no fill can change it: a wiring-gap candidate for review, not a verdict',
}


def hash_ok(value):
    return isinstance(value, str) and len(value) == 64 and all(ch in '0123456789abcdef' for ch in value)


def identity(source_pins, zones, image_id, kicad=KICAD_VERSION, parent_key=None, process=PROCESS_VERSION):
    """Composite identity of one derived board; every field participates in the key."""
    if set(source_pins) != set(BOARD_FILES) or not all(hash_ok(v) for v in source_pins.values()): raise ValueError('source pins')
    zones = sorted(zones)
    if not zones or len(zones) > ZONE_LIMIT or len(set(zones)) != len(zones) or not all(UUID_RE.match(z) for z in zones): raise ValueError('zones')
    if not isinstance(image_id, str) or not image_id.startswith('sha256:') or len(image_id) != 71: raise ValueError('image id')
    if kicad != KICAD_VERSION: raise ValueError('kicad version')
    if parent_key is not None and not hash_ok(parent_key): raise ValueError('parent key')
    return {'source': {k: source_pins[k] for k in BOARD_FILES}, 'zones': zones, 'image_id': image_id, 'kicad': kicad, 'process': process, 'parent_key': parent_key}


def identity_key(ident):
    return digest(identity(ident['source'], ident['zones'], ident['image_id'], ident['kicad'], ident.get('parent_key'), ident['process']))


def load_spec(path, expected_pads):
    """Validate a diagnostic spec: selected zone UUIDs and pad pairs on one net each."""
    spec = json.loads(Path(path).read_text())
    if not isinstance(spec, dict) or set(spec) - {'zones', 'pairs', 'note'} or not isinstance(spec.get('zones'), list) or not isinstance(spec.get('pairs'), list): raise ValueError('spec shape')
    zones = spec['zones']
    if not zones or len(zones) > ZONE_LIMIT or len(set(zones)) != len(zones) or not all(isinstance(z, str) and UUID_RE.match(z) for z in zones): raise ValueError('spec zones')
    pairs = []
    for pair in spec['pairs']:
        if not isinstance(pair, list) or len(pair) != 2 or pair[0] == pair[1] or any(p not in expected_pads for p in pair): raise ValueError('spec pair')
        if expected_pads[pair[0]]['net'] != expected_pads[pair[1]]['net']: raise ValueError('spec pair nets differ')
        pairs.append((pair[0], pair[1]))
    if not pairs or len(pairs) > PAIR_LIMIT or len(set(pairs)) != len(pairs): raise ValueError('spec pairs')
    note = spec.get('note', '')
    if not isinstance(note, str) or len(note) > 500: raise ValueError('spec note')
    return {'zones': sorted(zones), 'pairs': pairs, 'note': note}


def classify_pair(connected_before, connected_after, net_zones):
    """Status of one pad pair after the selected fill.

    net_zones: copper zones of the pair's net on the derived board, each with
    'uuid', 'filled' (every layer of the zone has at least one fill outline)
    and 'selected'. The result is an observation class, never acceptance.
    """
    if type(connected_before) is not bool or type(connected_after) is not bool: raise ValueError('connectivity flags')
    rows = sorted(net_zones, key=lambda z: z['uuid'])
    unfilled = [z['uuid'] for z in rows if not z['filled']]
    if connected_before: cls = 'CONNECTED_ON_INPUT'
    elif connected_after: cls = 'CONNECTED_VIA_SELECTED_FILL'
    elif not rows: cls = 'OPEN_WITHOUT_NET_ZONES'
    elif unfilled: cls = 'UNEVALUABLE_UNFILLED_NET_ZONES_REMAIN'
    else: cls = 'OPEN_WITH_ALL_NET_ZONES_FILLED'
    return {'class': cls, 'meaning': CLASSES[cls], 'connected_before': connected_before, 'connected_after': connected_after,
            'net_zones': [z['uuid'] for z in rows], 'unfilled_net_zones': unfilled, 'selected_net_zones': [z['uuid'] for z in rows if z.get('selected')],
            'repair_basis': False}


def manifest_identity(manifest, directory):
    """Identity recorded for a derived board plus the zones its ancestors filled: native manifest, or a legacy candidate manifest with its adoption sidecar."""
    status = manifest.get('status')
    if status == MANIFEST_STATUS:
        ident = manifest.get('identity')
        if not isinstance(ident, dict) or manifest.get('identity_key') != identity_key(ident): raise ValueError('manifest identity key')
        parent = manifest.get('parent') or {}
        ancestors = parent.get('zones') or []
        if not isinstance(ancestors, list) or not all(isinstance(u, str) and UUID_RE.match(u) for u in ancestors) or set(ancestors) & set(ident['zones']): raise ValueError('manifest ancestor zones')
        if (ident.get('parent_key') is None) != (not ancestors) or (ancestors and parent.get('identity_key') != ident.get('parent_key')): raise ValueError('manifest parent record')
        return ident, 'manifest', manifest['exported']['after'], sorted(ancestors)
    if status == LEGACY_STATUS:
        sidecar = Path(directory) / SIDECAR
        if not sidecar.is_file(): raise ValueError('legacy candidate without adoption sidecar')
        side = json.loads(sidecar.read_text())
        if side.get('manifest_sha256') != sha(Path(directory) / 'manifest.json'): raise ValueError('sidecar manifest hash')
        ident = side.get('identity')
        if not isinstance(ident, dict) or side.get('identity_key') != identity_key(ident) or ident['zones'] != [manifest.get('target_zone')] or ident['source'] != manifest.get('input'): raise ValueError('sidecar identity')
        return ident, 'legacy-sidecar:' + str(side.get('attestation', ''))[:200], manifest['exported']['after'], []
    raise ValueError('manifest status')


def verify_derived(directory, expected_identity, source_semantic_hash, semantic_hash):
    """Decide whether a saved derived board may be reused; every mismatch is a reason, never an exception."""
    directory = Path(directory); checks = {}
    def reject(reason): return {'reusable': False, 'reason': reason, 'checks': checks}
    try:
        manifest = json.loads((directory / 'manifest.json').read_text())
        ident, provenance, exported, ancestors = manifest_identity(manifest, directory)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return reject('manifest: ' + type(exc).__name__ + ': ' + str(exc)[:200])
    checks['provenance'] = provenance; checks['ancestor_zones'] = ancestors
    try:
        expected_key = identity_key(expected_identity); actual_key = identity_key(ident)
    except (ValueError, KeyError, TypeError) as exc:
        return reject('identity: ' + str(exc)[:200])
    checks['identity_key'] = {'expected': expected_key, 'actual': actual_key}
    if actual_key != expected_key:
        differing = sorted(k for k in set(ident) | set(expected_identity) if ident.get(k) != expected_identity.get(k))
        return reject('identity key mismatch in ' + ','.join(differing))
    for name in BOARD_FILES:
        p = directory / 'after' / name
        if p.is_symlink() or not p.is_file(): return reject('missing after/' + name)
        actual = sha(p); checks['after/' + name] = actual
        if actual != exported.get(name): return reject('stale or altered after/' + name + ': hash differs from manifest')
    if exported.get('osc-core.kicad_pro') != ident['source']['osc-core.kicad_pro'] or exported.get('osc-core.kicad_dru') != ident['source']['osc-core.kicad_dru']: return reject('project/rules differ from identity')
    board = directory / 'after' / 'osc-core.kicad_pcb'
    try: nonfill = semantic_hash(board)
    except Exception as exc: return reject('semantic hash: ' + type(exc).__name__ + ': ' + str(exc)[:200])
    checks['nonfill_sha256'] = nonfill
    if nonfill != source_semantic_hash: return reject('non-fill semantics differ from the current source')
    owners = zone_fill_owners(board); checks['owners'] = owners
    if set(owners['filled_polygon_by_zone']) != set(ident['zones']) | set(ancestors): return reject('fill ownership differs from the identity zone set plus its ancestors')
    return {'reusable': True, 'reason': 'all recomputed checks match', 'checks': checks, 'identity': ident, 'ancestor_zones': ancestors}


def legacy_sidecar(manifest_path, image_id, attestation, kicad=KICAD_VERSION):
    """Adopt a legacy single-zone candidate directory: identity recomputed from its manifest plus an explicit attestation of image and version."""
    manifest = json.loads(Path(manifest_path).read_text())
    if manifest.get('status') != LEGACY_STATUS: raise ValueError('not a legacy candidate manifest')
    ident = identity(manifest['input'], [manifest['target_zone']], image_id, kicad)
    if not isinstance(attestation, str) or not 16 <= len(attestation) <= 500: raise ValueError('attestation text')
    return {'identity': ident, 'identity_key': identity_key(ident), 'manifest_sha256': sha(manifest_path), 'attestation': attestation, 'process': PROCESS_VERSION,
            'meaning': 'Image id and KiCad version are attested from the recorded run receipt, not recomputed from the board; file hashes, semantics and ownership are recomputed on every reuse.'}
