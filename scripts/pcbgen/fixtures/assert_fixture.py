#!/usr/bin/env python3
"""Host-side fixture assertions on board text and DRC JSON."""
from pathlib import Path
import json,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.pcbgen.uuid_tools import stable_uuid,top_level_spans,REF_RE
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware
from scripts.pcbgen.netlist import read_netlist

ROOT=Path(__file__).resolve().parents[3]
def footprint_blocks(body):
 result={}
 for a,b in top_level_spans(body):
  block=body[a:b]
  if block.startswith('(footprint'):
   match=REF_RE.search(block)
   if match:result[match[1]]=block
 return result
mode=sys.argv[1];board=Path(sys.argv[2]);text=board.read_text()
if mode=='full':
 refs=[r for r in footprint_blocks(text) if re.fullmatch(r'J\d+',r)]
 assert len(refs)==10 and len(set(refs))==10,refs
 assert '(property "Reference" "MH_1"' in text
 assert text.count('(zone\n')>=2 or text.count('\n\t(zone')>=2
 d=load_definition(ROOT/'design/boards/fixture-jacks.json');lock=load_lock(ROOT/'design/grid/placements.lock.json')
 for p in selected_hardware(d,lock):
  uid=stable_uuid('fixture-jacks','footprint:'+p['ref'],'root')
  block=footprint_blocks(text)[p['ref']]
  assert f'(uuid "{uid}")' in block,p['ref']
  xy=f'(at {p["x_mm"]+100:g} {p["y_mm"]+50:g})'
  assert xy in block,(p['ref'],xy)
  assert '(locked yes)' in block,p['ref']
 report=json.loads((ROOT/'boards/fixture-jacks/reports/drc.json').read_text())
 assert len(report['schematic_parity'])==0,report['schematic_parity']
 print('ten lockfile positions, stable UUIDs and zero schematic parity issues: PASS')
elif mode=='owner':
 assert 'OWNER SILK' in text
 ids=json.loads((board.parent/'owner-ids.json').read_text())
 for kind,uid in ids.items():assert f'(uuid "{uid}")' in text,kind
 print('unowned track, via, zone, silk text and graphic preserved: PASS')
elif mode=='renet':
 block=footprint_blocks(text)['J101']
 assert '(net ' in block and '"/JACKS/FAULT_NET"' in block
 ids=json.loads((board.parent/'owner-ids.json').read_text())
 for kind,uid in ids.items():assert f'(uuid "{uid}")' in text,kind
 print('J101 re-netted in place; owner items preserved: PASS')
elif mode=='reduced':
 refs=[r for r in footprint_blocks(text) if re.fullmatch(r'J\d+',r)]
 assert len(refs)==9 and 'J110' not in refs,refs
 assert 'OWNER SILK' in text
 ids=json.loads((board.parent/'owner-ids.json').read_text())
 for kind,uid in ids.items():assert f'(uuid "{uid}")' in text,kind
 if len(sys.argv)>3:
  before=footprint_blocks(Path(sys.argv[3]).read_text());after=footprint_blocks(text)
  for ref in refs:assert before[ref]==after[ref],f'{ref}: footprint changed during unrelated removal'
 print('removed J110; other nine footprints and all owner items preserved: PASS')
else:raise SystemExit('unknown mode')
