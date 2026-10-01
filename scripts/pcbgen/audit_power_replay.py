"""Pinned native reproducibility gates for a separate source replay draft."""
import argparse
import collections
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.audit_power_locality import audit
from scripts.pcbgen.extract_power_geometry import extract
from scripts.pcbgen.generate_power_candidate import generate
from scripts.pcbgen.native_stack import apply as apply_stack
from scripts.pcbgen.ratsnest import inspect
from scripts.pcbgen.verify_local_links import blocks
from scripts.pcbgen.replay_equivalence import compare as compare_geometry, verify_export_provenance


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(board_id,clean,replay,cache,specification):
    before=digest(replay);source=json.loads(specification.read_text())
    original_geometry_path=cache/'clean-analytic-geometry.json'
    original_geometry_sha256=digest(original_geometry_path)
    original=json.loads(original_geometry_path.read_text())
    extractor=ROOT/'scripts/pcbgen/extract_power_geometry.py'
    original_provenance=verify_export_provenance(original,board_id,clean,clean.with_suffix('.kicad_pro'),extractor)
    replay_receipt=json.loads((cache/'source-replay.json').read_text())
    if replay_receipt['output_sha256']!=before or replay_receipt['specification_sha256']!=digest(specification):
        raise ValueError('replay source/board receipt mismatch')
    definition=cache/'source-replay-definition'/(board_id+'.json')
    definition.parent.mkdir(parents=True,exist_ok=True)
    generate(board_id,ROOT/source['plane_proposal'],source['plane_profile'],definition)
    definition_data=json.loads(definition.read_text())
    if definition_data!=replay_receipt['definition']:raise ValueError('replayed source definition changed')
    if digest(replay.with_suffix('.kicad_dru'))!=digest(definition.with_suffix('.kicad_dru')):
        raise ValueError('native replay custom rules differ from the exact generated source')
    companions={str(replay.with_suffix(suffix)):digest(replay.with_suffix(suffix))
                for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru')}
    expected_text,stack=apply_stack(clean.read_text(),definition_data)
    with tempfile.TemporaryDirectory(prefix='replay-owner-',dir=cache) as temporary:
        expected=Path(temporary)/'expected.kicad_pcb';expected.write_text(expected_text)
        old,new=blocks(expected),blocks(replay)
        for kind in ('footprint','zone','via','segment','arc','non_copper'):
            if old[kind]!=new[kind]:raise ValueError('replay differs beyond explicit source stack metadata: '+kind)
    drc_path=cache/'source-replay-drc.json'
    command=['kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--format','json','--severity-all','-o',str(drc_path),str(replay)]
    subprocess.run(command,check=True)
    drc=json.loads(drc_path.read_text());baseline=json.loads((cache/'clean-drc.json').read_text())
    if drc['kicad_version']!='10.0.6' or any(v['severity']=='error' for v in drc['violations']) or drc['schematic_parity']:
        raise ValueError('native replay rule/parity gate failed')
    warnings=lambda r:collections.Counter(json.dumps(v,sort_keys=True) for v in r['violations'] if v['severity']=='warning')
    if warnings(drc)!=warnings(baseline):raise ValueError('native replay changed exact warning identities')
    power_path=cache/'source-replay-power.json';audit(replay,power_path)
    power=json.loads(power_path.read_text())
    if power['fitted_rail_pad_count']!=power['fitted_rail_pads_connected_to_load_land'] or power['open_AGND_pad_identities']:
        raise ValueError('replayed native power connectivity is incomplete')
    if any(power[k]!=power['bypass_count'] for k in ('rail_loops_connected','rail_feeds_connected','bypass_AGND_returns_connected')):
        raise ValueError('replayed native bypass loop/feed/return gate failed')
    rats=inspect(replay);old_rats=json.loads((cache/'clean-ratsnest.json').read_text())
    if rats['native_open_edges_by_net']!=old_rats['native_open_edges_by_net']:
        raise ValueError('replay changed complete named native edge inventory')
    rats_path=cache/'source-replay-ratsnest.json';rats_path.write_text(json.dumps(rats,indent=2,sort_keys=True)+'\n')
    geometry_path=cache/'source-replay-geometry.json';extract(board_id,replay,geometry_path,definition)
    current=json.loads(geometry_path.read_text())
    current_provenance=verify_export_provenance(current,board_id,replay,replay.with_suffix('.kicad_pro'),extractor)
    assignment_path=ROOT/'design/partition/partition.json'
    metadata_delta=compare_geometry(original,current,json.loads(assignment_path.read_text()))
    if digest(replay)!=before:raise ValueError('native audit mutated the replay board')
    if any(digest(path)!=expected for path,expected in companions.items()):raise ValueError('native companion changed during audit')
    if verify_export_provenance(original,board_id,clean,clean.with_suffix('.kicad_pro'),extractor)!=original_provenance:
        raise ValueError('clean native inputs changed during audit')
    if digest(original_geometry_path)!=original_geometry_sha256:
        raise ValueError('cached clean native export changed during audit')
    result={'status':'PASS - source replay and native equivalence only; electrical/source selection and physical qualification remain OPEN',
        'board_id':board_id,'clean_board_sha256':digest(clean),'replay_board_sha256':before,
        'source_specification_sha256':digest(specification),'source_definition_sha256':digest(definition),
        'native_project_schematic_custom_rule_sha256':companions,
        'native_stack_metadata':stack,'exact_footprint_and_all_copper_blocks_preserved':True,
        'only_non_copper_change':'Exact source-generated native stack metadata; every other top-level block preserved',
        'exact_native_conductor_geometry_equivalence':True,
        'inapplicable_other_board_metadata_delta':metadata_delta,
        'independent_board_assignment_sha256':digest(assignment_path),
        'original_native_export_sha256':digest(original_geometry_path),'replayed_native_export_sha256':digest(geometry_path),
        'verified_original_export_inputs':original_provenance,'verified_replayed_export_inputs':current_provenance,
        'rule_errors':0,'schematic_parity_issues':0,'warning_identity_count':sum(warnings(drc).values()),
        'fitted_rail_feeds':power['fitted_rail_pad_count'],'bypass_loops_feeds_returns':power['bypass_count'],
        'open_AGND_pads':0,'native_full_named_open_edges':rats['native_unconnected_edges'],
        'artifacts_sha256':{str(p):digest(p) for p in (drc_path,power_path,rats_path,geometry_path)},
        'model_source_sha256':{name:digest(ROOT/'scripts/pcbgen'/name) for name in
            ('audit_power_replay.py','replay_equivalence.py','extract_power_geometry.py','audit_power_locality.py','ratsnest.py','native_stack.py','generate_power_candidate.py')},
        'native_drc_command':command}
    (cache/'source-replay-native-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(board_id,result['status'],result['fitted_rail_feeds'],result['bypass_loops_feeds_returns'],result['native_full_named_open_edges'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('board_id')
    for name in ('clean','replay','cache','specification'):p.add_argument(name,type=Path)
    a=p.parse_args();run(a.board_id,a.clean,a.replay,a.cache,a.specification)
