"""Mandatory complete source/native admission for actual O/EL conductors.

No missing, bare, failed, stale-source or partial contact export is admitted.
This gate is native geometry authority, not physical electrical acceptance.
"""
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.peripheral_ground_inventory import audit
from scripts.pcbgen.peripheral_project_source import derive

ROOT=Path(__file__).resolve().parents[2]
BOARDS={'osc-stage-optical',*(f'osc-octave-{n}' for n in range(1,6))}


def resolve(name):
    p=Path(name)
    if str(p).startswith('/work/'):p=ROOT/p.relative_to('/work')
    elif not p.is_absolute():p=ROOT/p
    p=p.resolve()
    if not p.is_relative_to(ROOT):raise ValueError('peripheral dependency outside worktree')
    return p


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify_unchanged(authority):
    if authority is not None:
        for path,value in authority['dependency_sha256'].items():
            if digest(path)!=value:raise ValueError('peripheral prerequisite changed: '+path)


def enter(source,native_bytes,receipt_path,manifest_path,include_loads,port_limit):
    helper_paths=[ROOT/'scripts/pcbgen'/name for name in ('peripheral_model_entry.py','peripheral_ground_inventory.py','peripheral_project_source.py','generate_peripheral_ground.py')]
    entry_helpers={str(p):digest(p) for p in helper_paths}
    native=json.loads(native_bytes);bid=native.get('board_id')
    if bid not in BOARDS:
        if receipt_path is not None or manifest_path is not None:raise ValueError('peripheral arguments require an actual O/EL board')
        return None
    if receipt_path is None or manifest_path is None:raise ValueError('peripheral successful native receipt and source manifest required')
    if port_limit or (bid=='osc-stage-optical' and not include_loads):raise ValueError('peripheral complete source basis requires port-limit 0 and EL include-loads')
    source,receipt_path,manifest_path=map(resolve,(source,receipt_path,manifest_path))
    raw=receipt_path.read_bytes();receipt=json.loads(raw)
    if receipt.get('board_id')!=bid or receipt.get('stage')!='ground_candidate' or receipt.get('native_model_prerequisite_passed') is not True or receipt.get('rule_error_count')!=0 or receipt.get('schematic_parity_count')!=0 or receipt.get('prior_physical_pad_hole_copper_and_reservations_preserved') is not True:
        raise ValueError('peripheral successful complete native prerequisite required; bare/failed export rejected')
    hashes={str(receipt_path):hashlib.sha256(raw).hexdigest()}
    for group in ('source_sha256','artifacts_sha256','companion_sha256'):
        if not receipt.get(group):raise ValueError('peripheral native receipt missing provenance')
        for name,value in receipt[group].items():
            p=resolve(name)
            if str(p) in hashes and hashes[str(p)]!=value:raise ValueError('peripheral conflicting source binding')
            if digest(p)!=value:raise ValueError('peripheral prerequisite dependency changed: '+name)
            hashes[str(p)]=value
    if hashes.get(str(source))!=hashlib.sha256(native_bytes).hexdigest() or str(manifest_path) not in hashes:
        raise ValueError('peripheral immutable export/manifest not bound')
    manifest=json.loads(manifest_path.read_bytes())
    if manifest['board_id']!=bid or manifest['initial_stage']!='ground_candidate':raise ValueError('peripheral source stage differs')
    if not manifest_path.name.endswith('.receipt.json'):raise ValueError('peripheral exact source manifest name required')
    definition=manifest_path.with_name(manifest_path.name.removesuffix('.receipt.json')+'.json')
    if hashes.get(str(definition))!=manifest['definition_sha256']:raise ValueError('peripheral definition authority missing')
    proposals=[resolve(p) for p in manifest['source_sha256'] if Path(p).name=='proposal.json']
    if len(proposals)!=1 or str(proposals[0]) not in hashes:raise ValueError('peripheral exact proposal required')
    proposal=json.loads(proposals[0].read_bytes())
    board=resolve(native['board'])
    if native['kicad_version']!='10.0.6' or native['board_sha256']!=receipt['board_sha256'] or hashes.get(str(board))!=receipt['board_sha256']:
        raise ValueError('peripheral native board/oracle binding differs')
    template=resolve(proposal['project_template']);canonical=ROOT/'boards'/bid/(bid+'.kicad_pro')
    if any(str(p) not in hashes for p in (template,canonical)):raise ValueError('peripheral source project inputs missing')
    expected,derivation=derive(template.read_bytes(),canonical.read_bytes(),definition.read_bytes(),board.with_suffix('.kicad_pro').name)
    recorded=receipt['project_source_derivation']
    if any(recorded.get(k)!=v for k,v in derivation.items()) or board.with_suffix('.kicad_pro').read_bytes()!=expected or native['project_sha256']!=hashlib.sha256(expected).hexdigest():
        raise ValueError('peripheral source-derived project differs')
    schematic=ROOT/'boards'/bid/(bid+'.kicad_sch')
    companions={str(board.with_suffix('.kicad_pro')):hashlib.sha256(expected).hexdigest(),str(board.with_suffix('.kicad_sch')):hashes.get(str(schematic)),str(board.with_suffix('.kicad_dru')):manifest['native_rule_sha256']}
    if {str(resolve(p)):h for p,h in receipt['companion_sha256'].items()}!=companions or any(hashes.get(p)!=h for p,h in companions.items()):raise ValueError('peripheral copied companions lack exact source authority')
    drcs=[resolve(p) for p in receipt['artifacts_sha256'] if Path(p).name=='native-drc.json']
    if len(drcs)!=1:raise ValueError('peripheral exact DRC artifact missing')
    drc=json.loads(drcs[0].read_bytes())
    if drc['source']!=board.name or drc['kicad_version']!='10.0.6' or drc['schematic_parity'] or any(r['severity']=='error' for r in drc['violations']):raise ValueError('peripheral actual DRC artifact fails')
    inputs=[resolve(proposal[k]) for k in ('partition','io')]
    if any(str(p) not in hashes for p in inputs):raise ValueError('peripheral independent source inventory missing')
    inventory=audit(native,manifest,*(json.loads(p.read_bytes()) for p in inputs))
    required=72 if bid=='osc-stage-optical' else 7
    if inventory!=receipt['source_ground_inventory'] or inventory['connected_count']!=required:raise ValueError('peripheral full source inventory differs')
    bridge=receipt.get('source_ground_bridge')
    if bid=='osc-stage-optical':
        if not bridge or bridge['source_bridge']!=proposal.get('source_ground_bridge') or manifest.get('source_added_copper')!={'tracks':0,'vias':1,'keepout_exceptions':0}:raise ValueError('EL exact source bridge authority missing')
        uid=bridge['via_uuid'];items=[i for i in native['items'] if i['uuid']==uid];holes=[i for i in native['holes'] if i['uuid']==uid]
        if len(items)!=1 or len(holes)!=1 or items[0]['net']!='AGND' or set(items[0]['copper'])!={'F.Cu','B.Cu'} or uid not in native['ground_reference_members'] or holes[0]['size_mm']!=[.3,.3] or holes[0]['xy_mm']!=[318,216] or not holes[0]['plated']:raise ValueError('EL actual bridge geometry/connectivity differs')
        if any(p['half_size_nm']!=[350000,350000] or p['centre_nm']!=[318000000,216000000] or p['kind']!='circle' for p in items[0]['analytic_primitives'].values()):raise ValueError('EL actual bridge annulus differs')
    elif bridge is not None or manifest.get('source_added_copper')!={'tracks':0,'vias':0,'keepout_exceptions':0}:raise ValueError('O source unexpectedly adds bridge copper')
    for path,value in entry_helpers.items():
        if path in hashes and hashes[path]!=value:raise ValueError('peripheral admission helper differs from native authority')
        hashes[path]=value
    result={'status':'PASS native prerequisite only; no physical contact/current/material or electrical acceptance','board_id':bid,'dependency_sha256':hashes,'source_ground_inventory':inventory,'named_reference':native['ground_reference']}
    verify_unchanged(result)
    return result


def select_ports(geometry,authority):
    if authority is None:return
    if geometry['data']['board_id']!=authority['board_id']:raise ValueError('peripheral extraction board changed')
    expected={(r['ref'],r['pad']):r for r in authority['source_ground_inventory']['contacts']}
    ports=geometry['ports']
    if len(ports)!=len(expected):raise ValueError('peripheral extraction omitted source contacts')
    seen=set()
    for p in ports:
        key=p['ref'],p['pad']
        if key not in expected or key in seen:raise ValueError('peripheral wrong or duplicate profile')
        row=expected[key];seen.add(key)
        face=geometry['active_sheet_layers'][p['layer']]
        kind='load' if row['kind']=='own_load' else row['kind']
        actual=[i for i in geometry['data']['items'] if i.get('ref')==key[0] and i.get('pad')==key[1]]
        if len(actual)!=1 or actual[0]['uuid']!=row['uuid'] or actual[0]['net']!='AGND':raise ValueError('peripheral source profile UUID/net differs')
        if p['kind']!=kind or face not in row['native_layers']:raise ValueError('peripheral actual source face/kind differs')
    named=authority['named_reference']
    matches=[p for p in ports if (p['ref'],p['pad'])==(named['ref'],named['pad'])]
    if len(matches)!=1:raise ValueError('peripheral exact reference profile absent')
    ref=matches[0]
    if (ref['ref'],ref['pad'])!=(named['ref'],named['pad']) or geometry['active_sheet_layers'][ref['layer']]!=named['layer']:raise ValueError('peripheral extracted reference differs')
