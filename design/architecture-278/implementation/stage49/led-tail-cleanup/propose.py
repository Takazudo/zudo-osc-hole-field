"""Exact parent-authorized Stage48 LED_K tail cleanup, disposable only."""
from pathlib import Path
import json,sys,uuid
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import top_level_spans,kind,value,digest,copper_contract
BASE='d1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73'
NET='XA23B6CC73603CD7235D3'
RETIRED=('f3c671af-83ca-560f-8614-5a530082d051','a8007baf-45fa-5fc8-be0d-a0a22bae8b43','a63a488c-d65e-5563-90b3-e28bf3a61872','02d727f2-84bb-57f4-b095-90a15351d259','14e5290c-3c0a-51c3-9ddb-c71c7f2b33c3','1a635a05-179c-56a8-9299-9bdfe2cc2ca5','41da91b3-066c-59be-a6d5-e465426e70e9','4987e593-215d-56a9-a415-0501896d057c','cdc72bb1-5b70-5452-ba71-e04b9c8105e1','e70d01bd-e454-578a-b41f-6705ed031b1e')
def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'osc-stage49-led-tail/'+name))
def additions():
 return [dict(kind='segment',uuid=uid('B-stub'),net=NET,layer='B.Cu',start_nm=[271150000,132550000],end_nm=[271320000,132800000],width_nm=200000),dict(kind='segment',uuid=uid('F-trim'),net=NET,layer='F.Cu',start_nm=[271300000,131150000],end_nm=[271300000,132800000],width_nm=200000),dict(kind='via',uuid=uid('LED-via'),net=NET,at_nm=[271320000,132800000],diameter_nm=600000,drill_nm=300000)]
def build(raw):
 if digest(raw)!=BASE:raise ValueError('wrong baseline')
 rows=[]
 for index,(a,b) in enumerate(top_level_spans(raw)):
  block=raw[a:b]
  if kind(block) in ['segment','via'] and value(block,'uuid') in RETIRED:
   rows.append(dict(index=index,kind=kind(block),uuid=value(block,'uuid'),net=value(block,'net'),sha256=digest(block),contract=copper_contract(block)))
 if len(rows)!=10 or any(r['net']!=NET for r in rows):raise ValueError('retirement binding')
 return dict(board_sha256=BASE,removed_uuids=list(RETIRED),retirements=rows,copper=additions(),scope='exact two B segments, six F tail segments, one shortened F segment and obsolete LED via; no other geometry')
if __name__=='__main__':
 output=Path(sys.argv[2])
 if output.exists():raise ValueError('do not overwrite proposal')
 output.write_text(json.dumps(build(Path(sys.argv[1]).read_text()),indent=2,sort_keys=True)+'\n')
