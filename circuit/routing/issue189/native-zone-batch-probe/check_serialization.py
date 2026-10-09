import sys,zipfile,json,time,hashlib,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from scripts.pcbgen.probe_zone_batches import INDICES,ZONE,ARCHIVE_SHA,BEFORE_SHA,batch_text,sha
from scripts.pcbgen.audit_zone_silk_scope import zone_fixture_parts
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE
parser=argparse.ArgumentParser(description='Offline serialization only; no native acceptance')
parser.add_argument('source',type=Path);parser.add_argument('archive',type=Path);parser.add_argument('output',type=Path)
args=parser.parse_args();source=args.source;archive=args.archive
assert sha(source)==BEFORE_SHA and sha(archive)==ARCHIVE_SHA
started=time.monotonic()
def artwork(text):
 out=[]
 for a,b in top_level_spans(text):
  block=text[a:b];kind=block[1:].split(None,1)[0].rstrip(')')
  if (kind=='footprint' or kind.startswith('gr_')) and '(layer "Edge.Cuts")' not in block:
   out.append(UUID_RE.search(block)[1])
 return out
text=source.read_text();parts=zone_fixture_parts(text,ZONE,set(artwork(text)));rows=[]
with zipfile.ZipFile(archive) as z:
 for i in INDICES:
  data=z.read(f'zone-{ZONE}/0-{i:04d}/osc-core.kicad_pcb');ids=artwork(data.decode());assert len(ids)==1
  assert batch_text(parts,ids).encode()==data
  rows.append(dict(index=i,item_uuid=ids[0],fixture_sha256=hashlib.sha256(data).hexdigest()))
result=dict(status='OFFLINE SERIALIZATION ONLY; NO NATIVE RUN',source_sha256=BEFORE_SHA,archive_sha256=ARCHIVE_SHA,fixtures=rows,elapsed_seconds=time.monotonic()-started)
args.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'count':len(rows),'elapsed_seconds':result['elapsed_seconds']}))
