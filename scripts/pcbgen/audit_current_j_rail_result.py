"""Recheck every published current-J rail diagnostic and its exact inputs.

This audit confirms retained numerical provenance only. It does not qualify a
physical contact, manufacturing class, current waveform or electrical target.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.screen_rail_transfers import screen,content_hash
from scripts.pcbgen.selected_conductor_export import select


def sha(data):return hashlib.sha256(data).hexdigest()


def audit(output,net):
    output=Path(output);stem=output.stem
    paths={suffix:output.with_name(stem+suffix+'.json') for suffix in
           ('','-profiles','-rail-ledger','-screen','-raw','-raw-profiles','-selected-native')}
    raw={key:path.read_bytes() for key,path in paths.items()}
    data={key:json.loads(value) for key,value in raw.items()}
    result=data[''];ledger=data['-rail-ledger'];screening=data['-screen'];prerequisite=result['rail_native_prerequisite']
    solver=data['-raw'];profile=data['-profiles']
    if (result['status']!='NOT ACCEPTED: nominal finite-profile rail diagnostic only'
        or result['physical_net']!=net or prerequisite['physical_net']!=net
        or prerequisite['board_id'] not in ('osc-jack-left','osc-jack-right')):
        raise ValueError('current J rail result identity/status differs')
    if result['raw_solver_receipt_sha256']!=sha(raw['-raw']):
        raise ValueError('raw current J rail solver receipt differs')
    if raw['-profiles']!=raw['-raw-profiles'] or result['profile_receipt']['sha256']!=sha(raw['-profiles']):
        raise ValueError('current J rail original finite profile bytes differ')
    if (solver['profile_receipt']['path']!=str(paths['-raw-profiles'].resolve())
        or solver['profile_receipt']['sha256']!=sha(raw['-raw-profiles'])):
        raise ValueError('current J raw solver original profile digest/path differs')
    if result['profile_receipt']['path']!=str(paths['-profiles'].resolve()):
        raise ValueError('current J rail profile path differs')
    for key in ('native_export_sha256','model_source_sha256','reference_contact','active_sheet_layers',
                'physical_foil_layers','core_native_prerequisite','control_native_prerequisite',
                'peripheral_native_prerequisite','jack_native_prerequisite','rail_native_prerequisite'):
        if profile[key]!=solver[key]:
            raise ValueError('current J rail profile/source sidecar differs: '+key)
    ordered=[(p['ref'],p['pad'],p['layer'],p['kind']) for p in profile['profiles']]
    ports=[(p['ref'],p['pad'],p['layer'],p['kind']) for p in solver['ports']]
    reference=solver['reference_contact']
    if len(ordered)!=len(ports)+1 or ordered[:-1]!=ports or ordered[-1]!=(reference['ref'],reference['pad'],reference['layer'],reference['kind']):
        raise ValueError('current J rail sidecar profile order/reference differs')
    expected_final=copy.deepcopy(solver)
    expected_final['conductor_role_mapping']=data['-selected-native']['conductor_role_mapping']
    expected_final['raw_solver_receipt_sha256']=sha(raw['-raw'])
    expected_final['rail_wrapper_source_sha256']=result['rail_wrapper_source_sha256']
    expected_final['profile_receipt']={'path':str(paths['-profiles'].resolve()),
                                       'sha256':solver['profile_receipt']['sha256']}
    expected_final['physical_net']=net
    expected_final['status']='NOT ACCEPTED: nominal finite-profile rail diagnostic only'
    expected_final['all_native_rail_pad_component_mapping']=expected_final.pop('all_native_AGND_pad_component_mapping')
    expected_final['unused_native_rail_copper_uuids']=expected_final.pop('unused_native_AGND_copper_uuids')
    expected_final['common_private_K_current_allocation']='NOT RUN: combined common rail and positive K allocation remain required'
    if expected_final!=result:
        raise ValueError('published current J rail matrix differs from exact raw solver transformation')
    if screening['input_receipts']['matrix_content_sha256']!=content_hash(result) or screening['input_receipts']['ledger_content_sha256']!=content_hash(ledger):
        raise ValueError('current J rail screen JSON input differs')
    for key in ('matrix','ledger'):
        row=screening['input_artifacts'][key]
        expected=output if key=='matrix' else paths['-rail-ledger']
        if row['path']!=str(expected.resolve()) or row['sha256']!=sha(expected.read_bytes()):
            raise ValueError('current J rail screen artifact differs: '+key)
    for source in (result['rail_wrapper_source_sha256'],prerequisite['dependency_sha256']):
        for name,want in source.items():
            if sha(Path(name).read_bytes())!=want:
                raise ValueError('current J rail dependency differs: '+name)
    for name,want in result['model_source_sha256'].items():
        path=Path(name) if name.startswith('design/') else Path('scripts/pcbgen')/name
        if sha(path.read_bytes())!=want:raise ValueError('current J rail model source differs: '+name)
    originals=[Path(name) for name,want in prerequisite['dependency_sha256'].items()
               if Path(name).name=='native-geometry.json' and want==prerequisite['original_native_export_sha256']]
    if len(originals)!=1:raise ValueError('one exact current J original export dependency required')
    original_path=originals[0]
    original_bytes=original_path.read_bytes()
    if prerequisite['original_native_export_sha256']!=sha(original_bytes):
        raise ValueError('current J original native differs')
    original=json.loads(original_bytes);selected=data['-selected-native'];selected_sha=sha(raw['-selected-native'])
    generated=(json.dumps(select(original,net,sha(original_bytes)),separators=(',',':'))+'\n').encode()
    if raw['-selected-native']!=generated or prerequisite['selected_native_export_sha256']!=selected_sha:
        raise ValueError('selected J rail export differs from original native')
    if (any(row['native_export_sha256']!=selected_sha for row in (solver,result,profile))
        or any(row['board_sha256']!=original['board_sha256'] for row in (solver,result,ledger))
        or ledger['native_export_sha256']!=sha(original_bytes)
        or prerequisite['board_id']!=original['board_id'] or selected['board_id']!=original['board_id']):
        raise ValueError('current J rail selected/original/result board and export identities differ')
    expected={(row['ref'],row['pad']) for row in prerequisite['expected_load_contacts']}
    actual={(row['ref'],row['pad']) for row in result['ports']}
    if len(actual)!=len(result['ports']) or actual!=expected or len(result['matrices_ohm']['upper'])!=len(expected):
        raise ValueError('current J rail fitted profile matrix population differs')
    recomputed=screen(result,ledger,net)
    if set(screening)!=set(recomputed)|{'input_artifacts'} or any(screening[key]!=value for key,value in recomputed.items()):
        raise ValueError('current J rail screen does not recompute')
    if any(path.read_bytes()!=raw[key] for key,path in paths.items()):
        raise ValueError('current J rail artifact changed during audit')
    for source in (result['rail_wrapper_source_sha256'],prerequisite['dependency_sha256']):
        for name,want in source.items():
            if sha(Path(name).read_bytes())!=want:
                raise ValueError('current J rail dependency changed during audit: '+name)
    for name,want in result['model_source_sha256'].items():
        path=Path(name) if name.startswith('design/') else Path('scripts/pcbgen')/name
        if sha(path.read_bytes())!=want:raise ValueError('current J rail model source changed during audit: '+name)
    return {'status':'PASS retained current J nominal rail artifact audit only; physical/electrical acceptance OPEN',
            'board_id':prerequisite['board_id'],'net':net,'fitted_profiles':len(expected),
            'current_residual_A':result['counts']['current']['maximum_equation_residual_A'],
            'potential_residual_A':result['counts']['potential']['maximum_equation_residual_A'],
            'worst':screening['worst'],
            'sha256':{key:sha(value) for key,value in raw.items()},
            'dependency_counts':{'model':len(result['model_source_sha256']),
                                 'rail':len(prerequisite['dependency_sha256']),
                                 'wrapper':len(result['rail_wrapper_source_sha256'])}}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    parser.add_argument('--net',required=True,choices=('+12V','-12V','+5V'))
    args=parser.parse_args()
    print(json.dumps(audit(args.output,args.net),indent=2,sort_keys=True))
