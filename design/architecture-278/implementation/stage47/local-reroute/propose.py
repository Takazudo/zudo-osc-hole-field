"""Exactly one retained signal retirement, four replacements, one ground via."""
from pathlib import Path
import hashlib,json,sys,uuid
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import top_level_spans,kind,value,digest,copper_contract
BASE='d1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73'
RETIRE='e5c9ec98-084e-5361-a6f6-d8875087ae94'
NET='X58FDDB7628A1C5322DD0'
POINTS=[(270.4,131.6),(271.025,132.225),(271.025,134.875),(270.4,135.5),(270.4,135.9)]
def nm(p):return [round(x*1e6) for x in p]
def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'osc-stage47-local-reroute/'+name))
def propose(board,output):
 raw=board.read_text()
 if digest(raw)!=BASE:raise ValueError('wrong baseline')
 rows=[]
 for index,(a,b) in enumerate(top_level_spans(raw)):
  block=raw[a:b]
  if kind(block)=='segment' and value(block,'uuid')==RETIRE:
   rows.append(dict(index=index,kind='segment',uuid=RETIRE,net=value(block,'net'),sha256=digest(block),contract=copper_contract(block)))
 if len(rows)!=1 or rows[0]['net']!=NET:raise ValueError('retirement binding')
 copper=[dict(kind='segment',uuid=uid('signal-'+str(i)),net=NET,layer='In3.Cu',start_nm=nm(a),end_nm=nm(b),width_nm=200000) for i,(a,b) in enumerate(zip(POINTS,POINTS[1:]))]
 copper.append(dict(kind='via',uuid=uid('ground-via'),net='AGND',at_nm=nm((270.3,133.3)),diameter_nm=700000,drill_nm=300000))
 proposal=dict(board_sha256=BASE,removed_uuids=[RETIRE],retirements=rows,copper=copper,scope='one In3.Cu signal segment; no footprint or LED_K changes')
 if output.exists():raise ValueError('do not overwrite proposal')
 output.write_text(json.dumps(proposal,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':propose(Path(sys.argv[1]),Path(sys.argv[2]))
