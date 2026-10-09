"""Filter a native-rejected batch and add a conservative D7504 alternative.

This is an explicit native isolation experiment, not a connectivity certificate.
"""
import json,hashlib,sys
from pathlib import Path
from shapely.geometry import Point,LineString
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups
sha='72a24ee996ae454c099ed165de1bd857721c42bef37861907a98ba5a4bf39d0c'
board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb';assert hashlib.sha256(board.read_bytes()).hexdigest()==sha
old=json.loads((HERE.parent/'jr-next-three/proposal.json').read_text());new=json.loads((HERE.parent/'jr-d7504-protected/proposal.json').read_text());assert old['board_sha256']==new['board_sha256']==sha and not old['removed_uuids'] and not new['removed_uuids']
excluded='X644D5B39CA94D516B1A0';rows=[r for r in old['copper'] if r['net']!=excluded]+new['copper'];assert len(rows)==57
existing=copper_block_groups(board.read_text());assert len({r['uuid'] for r in rows})==57 and all(r['uuid'] not in existing for r in rows)
def gap(a,b):
 if a['net']==b['net'] or (a['kind']==b['kind']=='segment' and a['layer']!=b['layer']):return float('inf')
 def shape(r):return (Point(r['at_nm']),r['diameter_nm']/2) if r['kind']=='via' else (LineString([r['start_nm'],r['end_nm']]),r['width_nm']/2)
 x,r=shape(a);y,s=shape(b);return (x.distance(y)-r-s)/1e6
minimum=min(gap(a,b) for i,a in enumerate(rows) for b in rows[:i]);assert minimum>=.25
p=HERE/'proposal.json';p.write_text(json.dumps({'board_sha256':sha,'removed_uuids':[],'copper':rows},indent=2)+'\n')
(HERE/'plan.json').write_text(json.dumps({'base_sha256':sha,'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'Two whole saved transactions50objects plus protected D7504 alternative7objects; exclude entire33-object U7106 transaction near native J900105.6 AGND split.57additions,zero removals. Full native gates mandatory.'},indent=2)+'\n')
(HERE/'selection.json').write_text(json.dumps({'status':'SELECTED; NATIVE NOT RUN','input_board_sha256':sha,'excluded_net':excluded,'excluded_objects':33,'retained_current_objects':sum(map(len,existing.values())),'added_objects':57,'removed_objects':0,'minimum_new_cross_net_gap_mm':minimum,'native_rejection_run':37917534758,'attribution':'U7106 proposed copper passes0.875mm from the split pad; other transactions are49.257mm and79.079mm away. Geometric inference only; isolation still requires native validation.'},indent=2)+'\n')
print('57objects on actual143; native NOT RUN')
