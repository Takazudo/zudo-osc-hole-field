#!/usr/bin/env python3
"""Download queued sources locally with real byte receipts. Does NOT promote evidence verdicts.
No network request occurs without --run. Redirected final URLs, errors and SHA-256 are recorded.
"""
import argparse,hashlib,json,urllib.request,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ids',nargs='*');p.add_argument('--output',type=Path,required=True);p.add_argument('--run',action='store_true');a=p.parse_args()
 src=json.loads((ROOT/'payload/research/osc-hole-field/sources.json').read_text());src=[s for s in src if s['url'] and (not a.ids or s['id'] in a.ids)]
 if a.ids and set(a.ids)-{s['id'] for s in src}:raise SystemExit('Unknown source IDs: '+str(set(a.ids)-{s['id'] for s in src}))
 for s in src:print(s['id'],s['url'])
 if not a.run:print('Dry run only; --run acquires these files. No evidence verdict is assigned.');return
 a.output.mkdir(parents=True,exist_ok=True);receipts=[]
 for s in src:
  rec={'id':s['id'],'requested_url':s['url'],'authority_claim_from_queue':s['authority'],'retrieved_at':datetime.now(timezone.utc).isoformat()}
  try:
   req=urllib.request.Request(s['url'],headers={'User-Agent':'zudo-osc-hole-field-source-acquisition/1.0'})
   with urllib.request.urlopen(req,timeout=30) as r:
    rec.update(final_url=r.geturl(),content_type=r.headers.get('content-type',''));data=r.read(25_000_001)
   if len(data)>25_000_000:raise ValueError('Larger than 25 MB acquisition limit; inspect manually')
   if s['id'] in ['LF398','OPA4197','PTV09'] and not data.startswith(b'%PDF-'):raise ValueError('Expected PDF but got other bytes (possibly an access page)')
   ext='.pdf' if data.startswith(b'%PDF-') else '.html';h=hashlib.sha256(data).hexdigest();name=s['id']+'-'+h[:16]+ext;out=a.output/name
   if out.exists() and out.read_bytes()!=data:raise ValueError('Content-addressed filename conflict')
   if not out.exists():out.write_bytes(data)
   rec.update(status='DOWNLOADED_NOT_AUDITED',sha256=h,bytes=len(data),local_file=name)
  except Exception as e:rec.update(status='SOURCE_UNAVAILABLE',sha256=None,error=str(e))
  receipts.append(rec);print(rec['id'],rec['status'])
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');(a.output/f'receipts-{stamp}.json').write_text(json.dumps({'scope':'Acquisition receipts only; inspect authority, contents, locator and exact identity before native evidence promotion','receipts':receipts},indent=2)+'\n')
if __name__=='__main__':main()
