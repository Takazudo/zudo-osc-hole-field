"""Read-only native outer-zone fill growth audit; never promote or waive findings."""
import argparse,hashlib,json,math,re,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.complete_native_warnings import SILK_TARGET_LAYERS
from scripts.pcbgen.uuid_tools import top_level_spans,replace_spans,UUID_RE
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting,new_silk_identities


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


def zone_fixture_parts(source_text, zone_uid, artwork_ids):
    """Parse a large source once; retain exact bytes for each paired fixture."""
    parts=[];cursor=0
    for a,b in top_level_spans(source_text):
        parts.append((None,source_text[cursor:a]));cursor=b
        block=source_text[a:b];kind=block[1:].split(None,1)[0].rstrip(')')
        match=UUID_RE.search(block);uid=match[1] if match else None
        if kind in ('segment','via') or (kind=='zone' and uid!=zone_uid):continue
        if kind=='footprint':
            edits=[(x,y,'') for x,y in top_level_spans(block)
                   if block[x+1:y].split(None,1)[0].rstrip(')')=='pad']
            block=replace_spans(block,edits)
        parts.append((uid if uid in artwork_ids else None,block))
    parts.append((None,source_text[cursor:]))
    return parts


def zone_fixture_text(parts, item_uid):
    return ''.join(block for uid,block in parts if uid is None or uid==item_uid)


def zone_fixture_batch_text(parts, item_uids):
    known={uid for uid,_ in parts if uid is not None}
    if not item_uids or len(set(item_uids))!=len(item_uids) or not set(item_uids)<=known:
        raise ValueError('empty, duplicate or unknown artwork batch')
    selected=set(item_uids)
    return ''.join(block for uid,block in parts if uid is None or uid in selected)


def artwork_batches(selected, batch_size):
    if type(batch_size) is not int or not 1<=batch_size<=16:
        raise ValueError('artwork batch size must be integer1..16')
    if len(set(selected))!=len(selected):
        raise ValueError('duplicate selected artwork')
    return [selected[i:i+batch_size] for i in range(0,len(selected),batch_size)]


def native_zone_signature(poly):
    # Pinned10.0.6 Format includes all outline/hole vertices and closure flags,
    # but omits arcs. Refuse those rather than comparing incomplete geometry.
    if poly.ArcCount():raise ValueError('native zone fingerprint does not support arcs')
    return hashlib.sha256(poly.Format().encode()).hexdigest()


def classify_zone(before_path,after_path,output,before,after,uid,layer,growth,pcbnew,batch_size=1,resume=None):
    """Native full-zone/silk pairs wherever added filled area could collide."""
    settings=json.loads(after_path.with_suffix('.kicad_pro').read_text())['board']['design_settings']['rules']
    margin=max(0,math.ceil(settings['min_silk_clearance']*1e6))+5_000_000
    boxes=[growth.Outline(i).BBox() for i in range(growth.OutlineCount())]
    for box in boxes:box.Inflate(margin)
    items=list(after.GetFootprints())+[x for x in after.GetDrawings() if x.GetLayer()!=pcbnew.Edge_Cuts]
    selected=[]
    for item in items:
        box=item.GetBoundingBox(True,True) if item.Type()==pcbnew.PCB_FOOTPRINT_T else item.GetBoundingBox()
        if any(box.Intersects(region) for region in boxes):selected.append(item.m_Uuid.AsString())
    selected=sorted(selected);batches=artwork_batches(selected,batch_size);all_ids={x.m_Uuid.AsString() for x in items}
    # Retain the actual scope and completed fixtures if a bounded job stops.
    # Progress is diagnostic only; result.json must still certify full coverage.
    scope=dict(
        zone_uuid=uid,layer=pcbnew.LayerName(layer),artwork_count=len(items),
        selected_item_uuids=selected,conservative_margin_nm=margin,
        growth_boxes_nm=[[b.GetX(),b.GetY(),b.GetWidth(),b.GetHeight()] for b in boxes])
    from scripts.pcbgen.zone_batch_resume import completed_prefix,verified_report
    completed=completed_prefix(resume,uid,scope,batches)
    (output/f'zone-{uid}-scope.json').write_text(json.dumps(scope,indent=2)+'\n')
    progress=output/f'zone-{uid}-progress.jsonl';progress.write_text('')
    print(f'zone {uid}: {len(selected)}/{len(items)} artwork items, {2*len(batches)} paired fixtures',flush=True)
    def text_rows(board):
        objects=list(board.GetDrawings())
        for fp in board.GetFootprints():objects.extend([*fp.GetFields(),*fp.GraphicalItems()])
        return {x.m_Uuid.AsString():x.GetShownText(True) for x in objects if hasattr(x,'GetShownText')}
    sources=[(before_path,before),(after_path,after)];receipts=[];unions=[set(),set()];source_signatures={}
    for stage,(source,board) in enumerate(sources):
        source_text=source.read_text();texts=text_rows(board);native_zone=next(z for z in board.Zones() if z.m_Uuid.AsString()==uid)
        source_signatures[str(stage)]=native_zone_signature(native_zone.GetFilledPolysList(layer))
        parts=zone_fixture_parts(source_text,uid,all_ids)
        for index,item_uids in enumerate(batches):
            label=f'{stage}-{index:04d}' if batch_size==1 else f'{stage}-batch-{index:04d}'
            folder=output/f'zone-{uid}'/label;folder.mkdir(parents=True,exist_ok=True)
            fixture=folder/source.name
            fixture.write_text(zone_fixture_text(parts,item_uids[0]) if batch_size==1 else zone_fixture_batch_text(parts,item_uids))
            for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(source.with_suffix(suffix),fixture.with_suffix(suffix))
            loaded=pcbnew.LoadBoard(str(fixture));zones=list(loaded.Zones())
            if len(zones)!=1 or zones[0].m_Uuid.AsString()!=uid:raise ValueError('fixture zone identity changed')
            if list(loaded.GetTracks()) or any(list(fp.Pads()) for fp in loaded.GetFootprints()):raise ValueError('unrelated fixture copper remains')
            actual_ids=[x.m_Uuid.AsString() for x in list(loaded.GetFootprints())+[x for x in loaded.GetDrawings() if x.GetLayer()!=pcbnew.Edge_Cuts]]
            if len(actual_ids)!=len(set(actual_ids)) or set(actual_ids)!=set(item_uids):raise ValueError('fixture artwork scope changed')
            actual=text_rows(loaded)
            if any(texts.get(k)!=v for k,v in actual.items()):raise ValueError('fixture rendered text changed')
            geometry_signature=native_zone_signature(zones[0].GetFilledPolysList(layer))
            if geometry_signature!=source_signatures[str(stage)]:raise ValueError('fixture native zone shape changed')
            report=folder/'drc.json'
            if (stage,index) in completed:
                report.write_bytes(verified_report(resume,uid,label,fixture,completed[(stage,index)],geometry_signature))
            else:
                subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--output',str(report),str(fixture)],check=True,stdout=subprocess.DEVNULL)
            for suffix in ('.kicad_pro','.kicad_dru'):
                if source.with_suffix(suffix).read_bytes()!=fixture.with_suffix(suffix).read_bytes():raise ValueError('fixture native context changed')
            rows=new_silk_identities(json.loads(report.read_text()),uid)
            identities={(v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items']))) for v in rows};unions[stage].update(identities)
            receipts.append(dict(stage=stage,**({'resumed_report':True} if (stage,index) in completed else {}),**({'item_uuid':item_uids[0]} if batch_size==1 else {'item_uuids':item_uids,'batch_index':index}),fixture=str(fixture),fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),native_geometry_sha256=geometry_signature,report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),identities=sorted(identities)))
            with progress.open('a') as stream:stream.write(json.dumps(receipts[-1])+'\n')
            print(f'zone {uid} stage{stage} {"item" if batch_size==1 else "batch"}{index+1}/{len(batches)} identities{len(identities)}',flush=True)
    return dict(**({} if batch_size==1 else {'artwork_batch_size':batch_size}),selected_item_uuids=selected,conservative_margin_nm=margin,native_geometry_method='exact_native_coordinates_no_arcs',source_geometry_sha256=source_signatures,fixtures=receipts,before_identities=sorted(unions[0]),after_identities=sorted(unions[1]),new_identities=sorted(unions[1]-unions[0]))


def main(before_path,after_path,output,classify=False,batch_size=1,resume=None):
    import pcbnew
    artwork_batches([],batch_size)
    version=subprocess.check_output(['kicad-cli','version'],text=True).strip()
    if version!='10.0.6':raise ValueError('requires pinned native10.0.6')
    if resume is not None:
        from scripts.pcbgen.zone_batch_resume import validate_source
        if not classify:raise ValueError('resume requires full classification')
        resume=validate_source(resume,before_path,after_path,batch_size,output)
    output.mkdir(parents=True,exist_ok=True)
    result=dict(status='STARTED; NO COMPLETE ZONE EVIDENCE',version=version,before_sha256=hashlib.sha256(before_path.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(after_path.read_bytes()).hexdigest())
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    for suffix in ('.kicad_pro','.kicad_dru'):
        if before_path.with_suffix(suffix).read_bytes()!=after_path.with_suffix(suffix).read_bytes():raise ValueError('source context changed')
    if zone_metadata(before_path.read_text())!=zone_metadata(after_path.read_text()):raise ValueError('zone metadata or outline changed')
    unchanged_nonrouting(before_path.read_text(),after_path.read_text())
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
            if classify and not p.IsEmpty():rows[-1]['native_silk_pairs']=classify_zone(before_path,after_path,output,before,after,uid,layer,p,pcbnew,batch_size,resume)
    result.update(status='READ-ONLY NATIVE ZONE SHAPE EVIDENCE; NO PROMOTION',zone_metadata_and_outline_unchanged=True,zones=rows,all_silk_relevant_zone_shapes_are_subsets=all(r['native_added_shape_empty'] for r in rows))
    result['zone_silk_scope_complete']=classify
    result['new_zone_silk_identities']=sorted({tuple([a,b,tuple(c)]) for row in rows for a,b,c in row.get('native_silk_pairs',{}).get('new_identities',[])})
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('before',type=Path);parser.add_argument('after',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--classify',action='store_true');parser.add_argument('--batch-size',type=int,default=1);parser.add_argument('--resume-from',type=Path);args=parser.parse_args();main(args.before,args.after,args.output,args.classify,args.batch_size,args.resume_from)
