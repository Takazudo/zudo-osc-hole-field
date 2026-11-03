"""Source-only comparison of retained circuit/BOM metadata and B2 pose differences."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import digest,kind,value,direct,top_level_spans

def footprints(raw):
    result={}
    for a,z in top_level_spans(raw):
        part=raw[a:z]
        if kind(part)!='footprint':continue
        props={json.loads(k):json.loads(v) for k,v in re.findall(r'\(property\s+("(?:[^"\\]|\\.)*")\s+("(?:[^"\\]|\\.)*")',part)}
        ref=props.pop('Reference')
        at=next(x for x in direct(part) if kind(x)=='at')[1:-1].split()[1:]
        result[ref]={'properties':props,'library_id':re.match(r'\(footprint\s+("(?:[^"\\]|\\.)*")',part)[1], 'at':[float(v) for v in at], 'layer':value(part,'layer')}
    return result

CONTEXT_FIELDS={'Block','FootprintOriginMm','KiCadOrientationDeg','BoardSide','PanelUid'}

def summarize(candidate,output):
    base=ROOT/'.circuit-cache/stage42-full-b1-fresh/osc-jack-left.kicad_pcb';old=base.read_text();raw=candidate.read_text()
    if digest(old)!='975cd15d5ba69b9695e8d32a575a289306a27f1ea17d6b5f7a5819071dc5505b':raise ValueError('baseline')
    plan=json.loads((ROOT/'design/architecture-278/implementation/stage40/mult-copper-plan/plan.json').read_text())
    before,after=footprints(old),footprints(raw);rows=[]
    for a,v in plan['candidate_B1'].items():
        b=v['B2_ref'];x,y=before[a],after[b]
        if before[b]['properties']!=y['properties'] or before[b]['library_id']!=y['library_id']:raise ValueError('B2 metadata change')
        rows.append({'B1':a,'B2':b,'same_library_id':x['library_id']==y['library_id'],'common_nonplacement_properties':{k:v for k,v in x['properties'].items() if k not in CONTEXT_FIELDS}=={k:v for k,v in y['properties'].items() if k not in CONTEXT_FIELDS},'property_differences_B1_B2':{k:[x['properties'].get(k),y['properties'].get(k)] for k in x['properties'].keys()|y['properties'].keys() if x['properties'].get(k)!=y['properties'].get(k)},'B2_properties':y['properties'],'baseline_B2_at':before[b]['at'],'candidate_B2_at':y['at'],'candidate_layer':y['layer'],'translated_B1_at':[x['at'][0]+34,*x['at'][1:]]})
    output.write_text(json.dumps({'baseline_sha256':digest(old),'candidate_sha256':digest(raw),'B2_metadata_unchanged':True,'context_property_fields':sorted(CONTEXT_FIELDS),'native_pose_changes':sum(r['baseline_B2_at']!=r['candidate_B2_at'] for r in rows),'all_common_library_ids':all(r['same_library_id'] for r in rows),'all_common_nonplacement_properties':all(r['common_nonplacement_properties'] for r in rows),'packages':rows,'limits':'Source placement properties remain unchanged provenance, not authoritative candidate coordinates. Native/source metadata and circuit mapping are retained; manual inventory has no declared placement binding. No new exact manufacturer/supplier/physical qualification is established.'},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'packages':len(rows),'metadata_differences':sum(bool(r['property_differences_B1_B2']) for r in rows)}))
if __name__=='__main__':summarize(Path(sys.argv[1]),Path(sys.argv[2]))
