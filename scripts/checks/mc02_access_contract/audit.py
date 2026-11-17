"""Keep reference dimensions, tool reach and assembled manual access distinct."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).with_name('evidence.json')
THREAD = 'design/stack/fixings/threading-procedure.json'
LAND = 'design/stack/connectors/flex-land-patterns.json'
HANDOFF_SHA = 'c3257beed2331e5c95e176bc28441b04b804301a44c11b462e486fb5cc649d07'


def validate_handoff(h):
    if h['status'] != 'VERIFIED_PRIMARY_DOCUMENT' or h['verified_pdf_sha256'] != HANDOFF_SHA or h['verified_pdf_bytes'] != 1059562:
        raise ValueError('verified document identity/receipt changed; source review required')
    if h['reported_document'] != 'EDC3-150229-11' or h['expected_pdf_sha256'] != HANDOFF_SHA:
        raise ValueError('document identity changed')
    if h['open_height_mm'] != {'value':'4.8','kind':'reference_dimension','guaranteed_maximum':False}:
        raise ValueError('reference opening cannot become a guaranteed maximum')
    if h['closed_height_mm'] != {'nominal':'2.0','tolerance':'0.2','kind':'toleranced_drawing_dimension'}:
        raise ValueError('closed tolerance cannot be transferred to open geometry')
    if h['actuation'] != {'method':'central manual actuator operation','reported_pages':[6,8],
                           'operation_mode':'hand_only','tools_or_fingernails_inside_connector':'prohibited'}:
        raise ValueError('central manual operation must not become tool-only operation')


def validate_claim(c):
    if c['access_verdict'] != 'NOT SHOWN' or c['manual_access_shown'] is not False:
        raise ValueError('manual access evidence absent; promotion forbidden')
    if c['guaranteed_open_envelope_mm'] is not None:
        raise ValueError('no guaranteed open envelope available')
    if c['manual_corridor_mm'] is not None:
        raise ValueError('no sourced manual corridor or anthropometric allowance')
    # These may be separately demonstrated in future, but neither implies manual access.
    for name in ('tool_reach_shown','contact1_mapping_shown'):
        if type(c[name]) is not bool:
            raise ValueError('explicit evidence flag required: '+name)
    return ['mounted actuator swept envelope/tolerances not established',
            'central manual operation in the stated assembly sequence not demonstrated',
            'neighbour mounted heights and assembly tolerances not established',
            'cable threading/fold retention not demonstrated']


def audit(evidence, root=ROOT):
    if set(evidence['sha256']) != {THREAD, LAND}:
        raise ValueError('source closure changed')
    for path, sha in evidence['sha256'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest() != sha:
            raise ValueError('source pin changed: '+path)
    validate_handoff(evidence['handoff'])
    t=json.loads((root/THREAD).read_text())
    conflicts=[{'step':x['n'],'text':x['do'],'operations':x['parts'],
                'phase':'front' if x['n']==7 else 'K'} for x in t['steps'] if 'plastic tool' in x['do']]
    if conflicts!=evidence['expected_source_method_conflicts']:
        raise ValueError('source operation conflicts changed; explicit procedure review required')
    cases=t['latch']['not_shown']
    if cases != evidence['expected_not_shown'] or len(cases) != 31 or len({x['link'] for x in cases}) != 31:
        raise ValueError('exact 31 NOT SHOWN cases changed')
    if set(evidence['case_claims']) != {x['link'] for x in cases}:
        raise ValueError('case evidence coverage changed')
    links={x['id']:x for x in t['links']}
    if len(links)!=len(t['links']): raise ValueError('duplicate threading link')
    hand={x['link'] for x in t['holding_hand']}
    if len(hand)!=12 or len(t['holding_hand'])!=12:
        raise ValueError('supporting-hand operation set changed')
    stages={}
    for stage in t['lowering']['stages']:
        for ident in stage['links']:
            if ident in stages: raise ValueError('duplicate lowering stage link')
            stages[ident]=stage['stage']
    rows=[]
    for case in cases:
        ident=case['link'];link=links[ident];claim=evidence['case_claims'][ident]
        if link['latch']!='NOT SHOWN' or link['latch_neighbours_remaining']!=case['neighbours']:
            raise ValueError('latch row/summary mismatch')
        if link['holding_hand'] != (ident in hand): raise ValueError('supporting-hand source mismatch')
        missing=validate_claim(claim)
        if ident in hand: missing.append('concurrent supporting hand at K edge must be accommodated')
        rows.append({'link':ident,'neighbours':case['neighbours'],'K_connector':link['K_connector'],
                     'front_board':link['front_board'],'connector_size':link['size'],
                     'lowering_stage':stages[ident],'requires_supporting_hand':ident in hand,
                     'reported_manual_operation':evidence['handoff']['actuation'],
                     'source_status':evidence['handoff']['status'],'access_verdict':'NOT SHOWN',
                     'declared_tool_reach_shown':claim['tool_reach_shown'],
                     'declared_contact1_mapping_shown':claim['contact1_mapping_shown'],
                     'guaranteed_open_envelope_mm':None,'manual_corridor_mm':None,'missing':missing})
    land=json.loads((root/LAND).read_text())['entries']['hirose_fh12_0_5sh']['st01h']
    return {'engineering_commit':evidence['engineering_commit'],'inputs_sha256':evidence['sha256'],
            'handoff':evidence['handoff'],'existing_open_assumption':land['actuator_open_envelope'],
            'cases':rows,'case_count':31,'access_verdict':'NOT SHOWN',
            'source_method_conflicts':conflicts,'source_method_conflict_count':len(conflicts),
            'source_method_conflict_scope':'Procedure steps7/12 offer a plastic-tool alternative; verified manufacturer instruction is central hand-only operation. Each step covers61 links,122 endpoint operations total. This is a method conflict separate from31 geometric NOT SHOWN cases, not proof that all hand operations physically fail.',
            'scope':'Evidence-separation contract only. No contact mapping or height recalculation, hand/tool corridor construction, '
                    'native geometry, physical validation, hardware adoption or DRC/fill. Reference 4.8 mm and assumed 5 mm '
                    'do not establish guaranteed clearance; tool reach/contact mapping do not establish manual access.'}


def verify_pdf(path):
    raw=Path(path).read_bytes()
    if len(raw)!=1059562 or hashlib.sha256(raw).hexdigest()!=HANDOFF_SHA:
        raise ValueError('manufacturer PDF bytes do not match reviewed source')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pdf',type=Path,help='Optional independent verification of retained raw bytes')
    args=parser.parse_args()
    if args.source_pdf:verify_pdf(args.source_pdf)
    print(json.dumps(audit(json.loads(EVIDENCE.read_text())),indent=2))
