#!/usr/bin/env python3
"""Check issue-15 shortlist coverage, retained source hashes, and pin/pad maps."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/libgen'))
from gen_courtyards import parse,walk,node_name
LIB='zudo-osc-hole-field'
def child(node,name):return next((x for x in node if isinstance(x,list) and node_name(x)==name),None)
def source_hash(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 parts=json.loads((ROOT/'design/standard/parts-shortlist.json').read_text())['parts']
 capture=json.loads((ROOT/'design/standard/ic-library-capture.json').read_text())
 errors=[];captured=0;blocked=0;checked=0
 source_text='\n'.join(p.read_text() for p in (ROOT/'symbols/src').glob('*.kicad_sym'))
 if len(parts)!=capture['shortlist_count']:errors.append('shortlist count drift')
 for part in parts:
  id=part['id'];mpn=part['mpn'];exists=bool(re.search(r'\(property\s+"MPN"\s+"'+re.escape(mpn)+'"',source_text))
  row=next((x for x in capture['rows'] if x['id']==id),None)
  if row is None or row['mpn']!=mpn:errors.append(f'{id}: capture row missing or mismatched');continue
  if not exists:
   blocked+=1
   if id!='signal_diode' or not row['status'].startswith('BLOCKED'):errors.append(f'{id}: unexpected uncaptured part')
   continue
  captured+=1
  if row['status']!='CAPTURED DRAFT':errors.append(f'{id}: captured status drift')
  if id in ('pot_103','pot_104','pot_504','led_white','led_red'):continue
  path=ROOT/'design/standard/pin-maps'/(id+'.json')
  if not path.is_file():errors.append(f'{id}: pin map missing');continue
  data=json.loads(path.read_text());source=data['source'];pins=data['pins']
  if data['identity']['mpn']!=mpn:errors.append(f'{id}: pin-map identity mismatch')
  symbol_name=data['cad']['symbol'].split(':',1)[1];foot_name=data['cad']['footprint'].split(':',1)[1]
  symbol_path=ROOT/'symbols/src'/(symbol_name+'.kicad_sym');fp_path=ROOT/'footprints/kicad'/(LIB+'.pretty')/(foot_name+'.kicad_mod')
  if not symbol_path.is_file() or not fp_path.is_file():errors.append(f'{id}: CAD path missing');continue
  st=parse(symbol_path.read_text());s=child(st,'symbol')
  sp={child(p,'number')[1] for u in s if isinstance(u,list) and node_name(u)=='symbol' for p in walk(u) if node_name(p)=='pin'}
  fpad={p[1] for p in walk(parse(fp_path.read_text())) if node_name(p)=='pad'}
  mapped={x['symbol_pin'] for x in pins}
  if sp!=fpad or sp!=mapped:errors.append(f'{id}: symbol/pad/map mismatch {sp} {fpad} {mapped}')
  if source['availability']=='AVAILABLE':
   p=ROOT/source['retained_path']
   if not p.is_file() or not p.read_bytes().startswith(b'%PDF-') or source_hash(p)!=source['sha256']:errors.append(f'{id}: source PDF missing or hash drift')
   for x in pins:
    if 'physical PDF p.' not in x['source_locator'] or x['verdict']=='UNSOURCED':errors.append(f'{id}: available-source pin lacks page locator')
  else:
   if source['availability']=='SOURCE UNAVAILABLE' and source['sha256']!='0'*64:errors.append(f'{id}: unavailable source lacks zero hash')
   for x in pins:
    if x['verdict']!='UNSOURCED':errors.append(f'{id}: unresolved source has promoted pin row')
  checked+=1
 if capture['captured_count']!=captured or capture['blocked_count']!=blocked:errors.append('capture count mismatch')
 if captured!=35 or blocked!=1:errors.append(f'expected explicit 35/36 coverage, found {captured}/{len(parts)}')
 if errors:
  for e in errors:print('FAIL:',e,file=sys.stderr)
  return 1
 print(f'Issue-15 evidence check: PASS ({captured}/{len(parts)} shortlist rows captured; {blocked} exact-identity blocker; {checked} new pin maps and footprints checked)')
 return 0
if __name__=='__main__':raise SystemExit(main())
