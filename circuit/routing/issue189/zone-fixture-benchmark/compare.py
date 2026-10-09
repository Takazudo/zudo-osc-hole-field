"""Compare serializers on identical immutable native source bytes; no DRC claim."""
import hashlib,json,re,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.audit_zone_silk_scope import zone_fixture_parts,zone_fixture_text
from scripts.pcbgen.uuid_tools import top_level_spans,replace_spans,UUID_RE

def legacy(source_text,uid,all_ids,item_uid):
    edits=[]
    for a,b in top_level_spans(source_text):
        block=source_text[a:b];kind=block[1:].split(None,1)[0].rstrip(')');match=UUID_RE.search(block)
        block_uid=match[1] if match else None
        if kind in ('segment','via') or (kind=='zone' and block_uid!=uid) or (block_uid in all_ids and block_uid!=item_uid):
            edits.append((a,b,''))
        elif kind=='footprint':
            for x,y in top_level_spans(block):
                if block[x+1:y].split(None,1)[0].rstrip(')')=='pad':edits.append((a+x,a+y,''))
    return replace_spans(source_text,edits)

root=Path('.circuit-cache/issue189-downloaded/core-finer-ground-batch/.circuit-cache');rows=[]
expected={'start':'95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5','merge':'b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66'}
for stage in ['start','merge']:
    p=root/f'osc-core-grid-shards-{stage}'/'osc-core.kicad_pcb';source=p.read_text();digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest==expected[stage]
    ids=set();footprints=[]
    for a,b in top_level_spans(source):
        block=source[a:b];kind=block[1:].split(None,1)[0].rstrip(')');m=UUID_RE.search(block)
        if m and (kind=='footprint' or (kind.startswith('gr_') and '(layer "Edge.Cuts")' not in block)):
            ids.add(m[1])
            if kind=='footprint':footprints.append(m[1])
    selected=sorted(footprints)[:2];zone='601e02b2-8ccb-5c28-83e5-03789d47fbbd';legacy_hashes=[]
    t=time.monotonic()
    for item in selected:
        text=legacy(source,zone,ids,item);legacy_hashes.append(hashlib.sha256(text.encode()).hexdigest())
    old_seconds=time.monotonic()-t
    t=time.monotonic();parts=zone_fixture_parts(source,zone,ids)
    new_hashes=[hashlib.sha256(zone_fixture_text(parts,item).encode()).hexdigest() for item in selected];new_seconds=time.monotonic()-t
    assert legacy_hashes==new_hashes
    row=dict(stage=stage,input_sha256=digest,source_bytes=p.stat().st_size,artwork_count=len(ids),selected_footprints=selected,fixture_sha256=new_hashes,old_seconds=old_seconds,new_seconds=new_seconds,byte_identical=True)
    rows.append(row);print(row,flush=True)
Path(__file__).with_name('result.json').write_text(json.dumps(dict(status='BYTE-IDENTICAL SERIALIZATION ONLY; NO NEW NATIVE ACCEPTANCE',comparisons=rows),indent=2)+'\n')
