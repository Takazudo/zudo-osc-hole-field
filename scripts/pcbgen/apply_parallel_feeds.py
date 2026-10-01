"""Apply source-defined parallel local feeds and run pinned native gates.

Only explicitly added copper and source-owned plane refills may change.
Canonical boards and historical model/native receipts remain untouched.
"""
import argparse
import collections
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.apply_rail_transfers import apply as apply_transfers
from scripts.pcbgen.prepare_source_planes import prepare
from scripts.pcbgen.native_stack import apply as apply_stack
from scripts.pcbgen.audit_power_locality import audit
from scripts.pcbgen.extract_power_geometry import extract
from scripts.pcbgen.ratsnest import inspect


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(board_id,source,specification,definition,output,cache):
    if source.resolve()==output.resolve() or output.exists():raise ValueError('fresh separate parallel-feed candidate required')
    spec=json.loads(specification.read_text());definition_data=json.loads(definition.read_text())
    if spec['board_id']!=board_id or spec['board_sha256']!=digest(source) or spec['unresolved']:
        raise ValueError('parallel source is unresolved or belongs to a different board')
    paths=[source,specification,definition,definition.with_suffix('.kicad_dru'),
        source.with_suffix('.kicad_pro'),source.with_suffix('.kicad_sch')]
    paths.extend(ROOT/'scripts/pcbgen'/name for name in ('apply_parallel_feeds.py','apply_rail_transfers.py',
        'prepare_source_planes.py','native_stack.py','audit_power_locality.py','extract_power_geometry.py','ratsnest.py'))
    hashes={str(p):digest(p) for p in paths}
    cache.mkdir(parents=True,exist_ok=True);output.parent.mkdir(parents=True,exist_ok=True)
    for suffix in ('.kicad_pro','.kicad_sch'):shutil.copyfile(source.with_suffix(suffix),output.with_suffix(suffix))
    shutil.copyfile(definition.with_suffix('.kicad_dru'),output.with_suffix('.kicad_dru'))
    with tempfile.TemporaryDirectory(prefix='parallel-feed-',dir=cache) as directory:
        stage=Path(directory)/'added.kicad_pcb'
        apply_transfers(source,specification,stage,cache/'parallel-added-copper.json')
        prepare(board_id,stage,output,cache/'parallel-owned-planes.json',definition)
    updated,stack=apply_stack(output.read_text(),definition_data);output.write_text(updated)
    board_hash=digest(output)
    drc_path=cache/'parallel-drc.json'
    command=['kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--format','json','--severity-all','-o',str(drc_path),str(output)]
    subprocess.run(command,check=True)
    drc=json.loads(drc_path.read_text());baseline=json.loads((cache/'clean-drc.json').read_text())
    if drc['kicad_version']!='10.0.6' or any(v['severity']=='error' for v in drc['violations']) or drc['schematic_parity']:
        raise ValueError('parallel-feed native rule/parity gate failed')
    warnings=lambda r:collections.Counter(json.dumps(v,sort_keys=True) for v in r['violations'] if v['severity']=='warning')
    if warnings(drc)!=warnings(baseline):raise ValueError('parallel-feed candidate changed warning identities')
    power_path=cache/'parallel-power.json';audit(output,power_path);power=json.loads(power_path.read_text())
    if power['fitted_rail_pad_count']!=power['fitted_rail_pads_connected_to_load_land'] or power['open_AGND_pad_identities']:
        raise ValueError('parallel candidate lost fitted power or ground connectivity')
    if any(power[key]!=power['bypass_count'] for key in ('rail_loops_connected','rail_feeds_connected','bypass_AGND_returns_connected')):
        raise ValueError('parallel candidate lost local bypass coverage')
    rats=inspect(output);old=json.loads((cache/'clean-ratsnest.json').read_text())
    if rats['native_open_edges_by_net']!=old['native_open_edges_by_net']:
        raise ValueError('parallel candidate changed complete named remaining edges')
    rats_path=cache/'parallel-ratsnest.json';rats_path.write_text(json.dumps(rats,indent=2,sort_keys=True)+'\n')
    geometry_path=cache/'parallel-geometry.json';extract(board_id,output,geometry_path,definition)
    if digest(output)!=board_hash:raise ValueError('native gates changed candidate bytes')
    if any(digest(p)!=expected for p,expected in hashes.items()):raise ValueError('parallel source or model changed during native work')
    report={'status':'PASS - additional source-owned feed copper and native gates only; new electrical model NOT RUN',
        'board_id':board_id,'board_sha256':board_hash,'input_source_sha256':hashes,'native_stack':stack,
        'source_added_transfer_count':len(spec['added']),'shared_local_branch_count':len(spec['shared_branches']),
        'all_prior_copper_and_owner_state_preserved':'Verified by added-copper and source-owned-plane receipts; only declared stack metadata and owned plane refills also change.',
        'rule_errors':0,'parity_issues':0,'exact_warning_identity_count':sum(warnings(drc).values()),
        'fitted_rail_feeds':power['fitted_rail_pad_count'],'complete_bypass_loops_feeds_returns':power['bypass_count'],
        'open_AGND_pads':0,'full_named_remaining_edges':rats['native_unconnected_edges'],
        'model_invalidation':'All previous native-conductor matrices remain historical diagnostics. New vias and their plane clearances require fresh extraction, common/current/voltage calculations and profile checks; no receipt hash rebinding.',
        'artifact_sha256':{str(p):digest(p) for p in (drc_path,power_path,rats_path,geometry_path,cache/'parallel-added-copper.json',cache/'parallel-owned-planes.json')}}
    (cache/'parallel-native-receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(board_id,report['status'],report['source_added_transfer_count'],report['fitted_rail_feeds'],report['full_named_remaining_edges'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('board_id')
    for name in ('source','specification','definition','output','cache'):parser.add_argument(name,type=Path)
    a=parser.parse_args();run(a.board_id,a.source,a.specification,a.definition,a.output,a.cache)
