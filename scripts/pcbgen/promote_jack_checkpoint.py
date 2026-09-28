"""Promote a byte-audited native draft checkpoint, never ground acceptance."""
import argparse,collections,hashlib,json,re
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.verify_local_links import blocks,TRACK_NET_RE
from scripts.pcbgen.uuid_tools import stable_uuid

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def promote(board_id,candidate,cache):
    source=Path('boards')/board_id/(board_id+'.kicad_pcb');reports=source.parent/'reports';side='left' if board_id.endswith('left') else 'right';before=blocks(source);after=blocks(candidate);definition=json.loads((Path('design/boards')/(board_id+'.json')).read_text());managed={stable_uuid(board_id,'pour',z['name']+':'+layer) for z in definition['routing']['zones'] for layer in z['layers']}
    for kind in ('footprint','segment','via','arc'):
        if any(after[kind].get(k)!=v for k,v in before[kind].items()):raise ValueError('checkpoint changed existing '+kind)
    old_owner=before['non_copper'].copy();new_owner=after['non_copper'].copy()
    for key,block in before['zone'].items():
        if key in managed:old_owner[block]-=1
        elif after['zone'].get(key)!=block:raise ValueError('owner zone/keepout changed')
    for key,block in after['zone'].items():
        if key in managed:new_owner[block]-=1
        elif key not in before['zone']:raise ValueError('unapproved new owner zone')
    if +old_owner!=+new_owner:raise ValueError('checkpoint changed non-pour owner state')
    signal=json.loads((cache/('left-source-signals.json' if side=='left' else 'right-source-local-signal-final.json')).read_text());bypass=json.loads((cache/(side+'-bypass-routed.json')).read_text());expected_tracks={t['uuid']:row['net'] for receipt in (signal,bypass) for row in receipt['added'] for t in row['tracks']};expected_vias={}
    for suffix in ('agnd-arrays','plus12-array','minus12-array','plus5-array'):
        receipt=json.loads((cache/(side+'-'+suffix+'.json')).read_text())
        expected_vias.update({uid:receipt['net'] for row in receipt['added'] for uid in row['via_uuids']})
    for kind,expected in (('segment',expected_tracks),('via',expected_vias),('arc',{})):
        added={k:v for k,v in after[kind].items() if k not in before[kind]}
        if set(added)!=set(expected):raise ValueError('unexpected new '+kind+' identities')
        for key,block in added.items():
            match=TRACK_NET_RE.search(block)
            if not match or match[1]!=expected[key]:raise ValueError('new copper exact net mismatch')
    before_native=json.loads((cache/(board_id+'-checkpoint-before-ratsnest.json')).read_text());rats=json.loads((cache/('planes-left-ratsnest.json' if side=='left' else 'right-signal-ratsnest.json')).read_text());power=json.loads((cache/('left-power-locality-final.json' if side=='left' else 'right-signal-power-locality.json')).read_text());drc=json.loads((cache/(side+'-bypass-drc.json' if side=='left' else 'right-signal-drc.json')).read_text());baseline=json.loads((reports/'drc.json').read_text())
    if before_native['board_sha256']!=sha(source) or rats['board_sha256']!=sha(candidate) or power['board_sha256']!=sha(candidate):raise ValueError('native receipt SHA mismatch')
    if rats['native_unconnected_edges']>=before_native['native_unconnected_edges']:raise ValueError('native edge decrease gate failed')
    if drc['kicad_version']!='10.0.6' or any(v['severity']=='error' for v in drc['violations']) or drc['schematic_parity']:raise ValueError('native rule/parity failed')
    warning_types=lambda d:collections.Counter(v['type'] for v in d['violations'] if v['severity']=='warning')
    old_warnings=warning_types(baseline);new_warnings=warning_types(drc)
    if any(n>old_warnings[k] for k,n in new_warnings.items()):raise ValueError('native warning regression')
    if power['open_AGND_pad_identities'] or any(not r['connected_to_main_returns'] for r in power['GH_return_contacts']):raise ValueError('main native AGND component incomplete')
    if any(not r['connected_to_main_AGND_component'] for r in power['load_terminals'] if r['net']=='AGND'):raise ValueError('main AGND land outside target component')
    if any(not r['connected_to_same_net_filled_plane'] for r in power['load_terminals']):raise ValueError('load terminal lacks actual rail/ground plane transfer')
    if power['rail_loops_connected']!=power['bypass_count'] or power['bypass_AGND_returns_connected']!=power['bypass_count'] or not power['all_same_face'] or power['maximum_pad_distance_mm']>2.8875+1e-8:raise ValueError('mandatory native bypass gate failed')
    receipt={'status':'UNVALIDATED DRAFT CHECKPOINT - #38 OPEN; not issue completion','board_id':board_id,'source_sha256':sha(source),'candidate_sha256':sha(candidate),'all_prior_copper_and_footprints_byte_preserved':True,'all_non_pour_owner_graphics_keepouts_outline_state_byte_preserved':True,'only_source_owned_pour_changes_allowed':sorted(managed),'source_owned_pour_changes':[k for k in managed if before['zone'].get(k)!=after['zone'].get(k)],'new_source_local_signal_links':len(signal['added']),'new_direct_IC_bypass_links':len(bypass['added']),'new_segments':len(expected_tracks),'new_load_terminal_vias':len(expected_vias),'native_edges_before':before_native['native_unconnected_edges'],'native_edges_after':rats['native_unconnected_edges'],'rule_errors':0,'parity_issues':0,'warnings_before':dict(old_warnings),'warnings_after':dict(new_warnings),'bypass_loops_native_connected':power['bypass_count'],'open_AGND_pads':0,'rail_feeds_connected':power['rail_feeds_connected'],'ground_resistance_current_acceptance':'NOT ACCEPTED - finite interface/ownership extraction unresolved; Astra handoff, #38 OPEN','manufacturing_process_and_hot_qualification':'NOT RUN #65; arrays require explicitly qualified solder/filled-capped process'}
    source.write_bytes(candidate.read_bytes());receipt['promoted_sha256']=sha(source)
    if receipt['promoted_sha256']!=receipt['candidate_sha256']:raise ValueError('promotion changed stage bytes')
    (reports/'checkpoint-preservation.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(board_id,receipt['status'],receipt['native_edges_before'],'->',receipt['native_edges_after'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('board_id');p.add_argument('candidate',type=Path);p.add_argument('--cache',type=Path,default=Path('.circuit-cache/issue38-recovery'));a=p.parse_args();promote(a.board_id,a.candidate,a.cache)
