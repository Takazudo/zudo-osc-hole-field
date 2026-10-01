"""Require an actual successful, hash-bound K native prerequisite before a model.

The selected coupling ports do not represent K's own loads as zero currents.
Their full inventory is retained; whole-network load acceptance remains open.
"""
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.core_ground_inventory import audit

ROOT=Path(__file__).resolve().parents[2]


def path_in_worktree(name):
    path=Path(name)
    if path.is_absolute():
        if str(path).startswith('/work/'):
            path=ROOT/path.relative_to('/work')
        else:
            path=path.resolve()
    else:path=ROOT/path
    if not path.resolve().is_relative_to(ROOT):raise ValueError('K model dependency lies outside the worktree')
    return path


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_native_companions(board,native,source_hashes,drc):
    """Verify copied companions against retained source digests, never rebind."""
    board=Path(board)
    if drc.get('source')!=board.name:raise ValueError('K DRC artifact belongs to a different native board')
    expected_sources={str(path_in_worktree(n)):h for n,h in source_hashes.items()}
    schematic_source=str(ROOT/'boards/osc-core/osc-core.kicad_sch')
    if schematic_source not in expected_sources:raise ValueError('K native receipt lacks schematic source digest')
    rules=[(n,h) for n,h in expected_sources.items() if n.endswith('.kicad_dru')]
    if len(rules)!=1:raise ValueError('K native receipt needs one exact source rule companion')
    expected={str(board):native['board_sha256'],str(board.with_suffix('.kicad_pro')):native['project_sha256'],
        str(board.with_suffix('.kicad_sch')):expected_sources[schematic_source],
        str(board.with_suffix('.kicad_dru')):rules[0][1]}
    for name,value in expected.items():
        if digest(name)!=value:raise ValueError('K native board or copied companion changed: '+name)
    return expected


def require_native_prerequisite(native_path,receipt_path,manifest_path):
    native_path=Path(native_path);receipt_path=Path(receipt_path);manifest_path=Path(manifest_path)
    receipt_bytes=receipt_path.read_bytes();receipt=json.loads(receipt_bytes)
    if receipt.get('rule_error_count')!=0 or receipt.get('schematic_parity_count')!=0:
        raise ValueError('K model requires a successful native rule/parity receipt')
    hashes={str(receipt_path.resolve()):hashlib.sha256(receipt_bytes).hexdigest()}
    for group in ('source_sha256','artifacts_sha256'):
        if not receipt.get(group):raise ValueError('K native prerequisite lacks dependency digests')
        for name,expected in receipt[group].items():
            path=path_in_worktree(name)
            if digest(path)!=expected:raise ValueError('K native prerequisite dependency changed: '+name)
            hashes[str(path.resolve())]=expected
    native_bytes=native_path.read_bytes();native_hash=hashlib.sha256(native_bytes).hexdigest()
    if hashes.get(str(native_path.resolve()))!=native_hash:
        raise ValueError('K model native export was not certified by this native receipt')
    native=json.loads(native_bytes)
    if native['board_id']!='osc-core' or native['kicad_version']!='10.0.6' or native['board_sha256']!=receipt['board_sha256']:
        raise ValueError('K model native board/oracle identity mismatch')
    board=path_in_worktree(native['board'])
    drc_paths=[path_in_worktree(n) for n in receipt['artifacts_sha256'] if n.endswith('ground-feasibility-drc.json')]
    if len(drc_paths)!=1:raise ValueError('K prerequisite needs one actual native DRC artifact')
    drc=json.loads(drc_paths[0].read_text())
    hashes.update(verify_native_companions(board,native,receipt['source_sha256'],drc))
    if drc['kicad_version']!='10.0.6' or drc['schematic_parity'] or any(v['severity']=='error' for v in drc['violations']):
        raise ValueError('K native DRC artifact is not a passing geometry/parity gate')
    if str(manifest_path.resolve()) not in hashes:raise ValueError('K source manifest is not bound by the native receipt')
    manifest=json.loads(manifest_path.read_text())
    partition_path=ROOT/'design/partition/partition.json';io_path=ROOT/'design/reports/io-partition.json'
    for path in (partition_path,io_path):
        if str(path) not in hashes:raise ValueError('K source inventory is not bound by the native receipt')
    inventory=audit(native,manifest,json.loads(partition_path.read_text()),json.loads(io_path.read_text()))
    if inventory!=receipt['source_ground_inventory']:raise ValueError('K source/native ground inventory differs from native receipt')
    if len(inventory['selected_contacts'])!=215 or inventory['selected_disconnected']:
        raise ValueError('K model lacks every selected 206 GH and nine main contacts')
    for name in ('core_model_gate.py','core_ground_inventory.py','source_contact_inventory.py'):
        path=ROOT/'scripts/pcbgen'/name;actual=digest(path)
        if str(path) in hashes and hashes[str(path)]!=actual:raise ValueError('K prerequisite helper changed during verification')
        hashes.setdefault(str(path),actual)
    if any(digest(p)!=expected for p,expected in hashes.items()):raise ValueError('K model prerequisite changed during verification')
    return {'status':'PASS native coupling-port prerequisite only; electrical and physical acceptance OPEN',
        'dependency_sha256':hashes,'selected_contacts':inventory['selected_contacts'],
        'full_source_ground_inventory':inventory,
        'own_load_scope':'All 1903 fitted K AGND contacts remain real source contacts. A selected coupling basis does not set their currents to zero. Actual joined/common/voltage acceptance must add supported K source-network loads or independently bound their effect; #43 must re-extract the final routed geometry.'}
