"""Read-only native outer-zone fill growth audit; never promote or waive findings."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.complete_native_warnings import SILK_TARGET_LAYERS
from scripts.pcbgen.uuid_tools import top_level_spans,replace_spans,UUID_RE


def zone_metadata(text):
    rows={}
    for a,b in top_level_spans(text):
        block=text[a:b]
        if not block.startswith('(zone'):continue
        uid=UUID_RE.search(block)[1]
        if uid in rows:raise ValueError('ambiguous zone UUID')
        cuts=[(x,y,'') for x,y in top_level_spans(block) if block[x+1:y].split(None,1)[0].rstrip(')') in ('filled_polygon','fill_segments')]
        rows[uid]=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',replace_spans(block,cuts))
    return rows


def main(before_path,after_path,output):
    import pcbnew
    version=subprocess.check_output(['kicad-cli','version'],text=True).strip()
    if version!='10.0.6':raise ValueError('requires pinned native10.0.6')
    output.mkdir(parents=True,exist_ok=True)
    result=dict(status='STARTED; NO COMPLETE ZONE EVIDENCE',version=version,before_sha256=hashlib.sha256(before_path.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(after_path.read_bytes()).hexdigest())
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    for suffix in ('.kicad_pro','.kicad_dru'):
        if before_path.with_suffix(suffix).read_bytes()!=after_path.with_suffix(suffix).read_bytes():raise ValueError('source context changed')
    if zone_metadata(before_path.read_text())!=zone_metadata(after_path.read_text()):raise ValueError('zone metadata or outline changed')
    before=pcbnew.LoadBoard(str(before_path));after=pcbnew.LoadBoard(str(after_path))
    old={z.m_Uuid.AsString():z for z in before.Zones()};new={z.m_Uuid.AsString():z for z in after.Zones()}
    if old.keys()!=new.keys():raise ValueError('native zone identities changed')
    rows=[]
    for uid,z in new.items():
        if z.GetIsRuleArea():continue
        prior=old[uid]
        if z.GetNetname()!=prior.GetNetname() or list(z.GetLayerSet().Seq())!=list(prior.GetLayerSet().Seq()):raise ValueError('native zone context changed')
        for layer in z.GetLayerSet().Seq():
            if pcbnew.LayerName(layer) not in SILK_TARGET_LAYERS:continue
            p=z.GetFilledPolysList(layer).CloneDropTriangulation();q=prior.GetFilledPolysList(layer)
            before_area=q.Area();after_area=p.Area();p.BooleanSubtract(q)
            rows.append(dict(uuid=uid,layer=pcbnew.LayerName(layer),net=z.GetNetname(),before_area_nm2=before_area,after_area_nm2=after_area,native_added_area_nm2=p.Area(),native_added_shape_empty=p.IsEmpty(),native_added_outline_count=p.OutlineCount()))
    result.update(status='READ-ONLY NATIVE ZONE SHAPE EVIDENCE; NO PROMOTION',zone_metadata_and_outline_unchanged=True,zones=rows,all_silk_relevant_zone_shapes_are_subsets=all(r['native_added_shape_empty'] for r in rows))
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main(*(Path(p) for p in sys.argv[1:4]))
