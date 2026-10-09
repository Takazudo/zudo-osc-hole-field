"""Independently reconcile the isolated native adoption, without publishing copper."""
import collections,hashlib,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups
from scripts.pcbgen.route_jack_grid import connectivity_signature,promotion_gate
out=Path(__file__).parent
root=Path('.circuit-cache/issue189-downloaded/jl-r8276-adoption')
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta=read(out/'adoption-download.json')
assert sha(Path('/tmp/issue189-jl-r8276-adoption.zip'))==meta['zip_sha256']
paths={s:root/'.circuit-cache'/('osc-jack-left-grid-shards-'+s) for s in ('start','merge','fresh')}
d={s:read(p/'dump.json') for s,p in paths.items()}
dr={s:read(p/'drc.json') for s,p in paths.items()}
texts={s:(p/'osc-jack-left.kicad_pcb').read_text() for s,p in paths.items()}
counts={s:collections.Counter(x for rows in copper_block_groups(t).values() for x in rows) for s,t in texts.items()}
r=read(root/'boards/osc-jack-left/reports/grid-routing/shards-issue189-r8276-joint.json')
pilot=read(out/'pilot.json');plan=read(out/'adoption-plan.json')
assert r['adopted'] and r['input_board_sha256']==plan['base_sha256']
assert r['candidate_board_sha256']==pilot['candidate_sha256']
assert r['copper_replay']['sha256']==pilot['replay_sha256']
for s in ('merge','fresh'):
    assert promotion_gate(d['start'],d[s],dr['start'],dr[s])['adopted']
    assert d[s]['open_edges']==118
    assert sha(paths[s]/'osc-jack-left.kicad_pcb')==r['candidate_board_sha256']
assert connectivity_signature(d['merge'])==connectivity_signature(d['fresh'])
assert counts['merge']==counts['fresh']
assert sum((counts['start']&counts['merge']).values())==33346
assert sum((counts['start']-counts['merge']).values())==2
assert sum((counts['merge']-counts['start']).values())==75
for k in ('pads','edges','keepouts','layers'):assert d['start'][k]==d['merge'][k]==d['fresh'][k]
for suffix in ('kicad_pro','kicad_dru'):assert len({(p/('osc-jack-left.'+suffix)).read_bytes() for p in paths.values()})==1
worker='origin/agent-fix/189-jl-r8276-adopt-worker'
bot=subprocess.check_output(['git','show',worker+':boards/osc-jack-left/osc-jack-left.kicad_pcb'])
assert hashlib.sha256(bot).hexdigest()==r['candidate_board_sha256']
assert sha(Path('boards/osc-jack-left/osc-jack-left.kicad_pcb')) in (r['input_board_sha256'],r['candidate_board_sha256'])
errors={s:sum(v['severity']=='error' for v in report['violations']) for s,report in dr.items()}
parity={s:len(report['schematic_parity']) for s,report in dr.items()}
warnings={s:sum(v['severity']=='warning' for v in report['violations']) for s,report in dr.items()}
assert set(errors.values())=={0} and set(parity.values())=={0} and set(warnings.values())=={477}
proof=dict(meta,status='NATIVE ADOPTION VERIFIED; LOCAL PUBLICATION NOT PERFORMED BY THIS SCRIPT',bot_commit=subprocess.check_output(['git','rev-parse',worker]).decode().strip(),published_sha256=r['candidate_board_sha256'],replay_sha256=r['copper_replay']['sha256'],identical_uncut_objects=33346,added_objects=75,reviewed_removed_objects=2,native_edges=118,drc_errors=errors,parity=parity,warnings=warnings,new_warning_identities=[],split_pad_groups=[],fresh_agrees=True,physical_geometry_and_project_rules_unchanged=True,pilot_candidate_and_replay_match=True)
(out/'adoption.json').write_text(json.dumps(r,indent=2)+'\n')
(out/'adoption-artifact.json').write_text(json.dumps(proof,indent=2)+'\n')
print(proof)
