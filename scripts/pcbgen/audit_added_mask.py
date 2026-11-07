"""Native evidence for every new copper/silkscreen interaction; never promote a board.

Requires exact non-copper/non-zone invariance, additive copper by default, unmasked new
tracks, no mask zones/custom silk rules, and zero mask-healing width. A fixture
contains all unchanged silkscreen and outline geometry, no old mask objects,
and one new copper object. Both silk warning categories are checked below their caps. Any cap hit or
unsupported scope fails closed. Explicit unique reviewed cuts are checked separately;
every uncut object remains immutable. A router stage's own rip-up delta may stand in for
the reviewed list (StageRemovals): it lifts only the twelve-cut review bound, never the
exact, unique, non-reused accounting of every removed object. Full-board checks remain mandatory.
"""
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.uuid_tools import top_level_spans, replace_spans, UUID_RE

REVIEWED_CUT_LIMIT=12
UUID_TEXT=re.compile(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}')


class StageRemovals(tuple):
    """Every segment/via a router stage removed, derived from its own before/after delta.

    The reviewed-cut path bounds a human review at twelve UUIDs. A rip-up stage removes
    far more, and no person reviews it, so the bound does not apply. Soundness does not
    rest on the bound: each removed object must still be named exactly once and absent
    from the after board, vanished holes must be exactly the removed vias, every growing
    zone and every added object keeps its complete native fixtures, and removing copper
    cannot itself place silk over copper.
    """
    source='stage'


def stage_removed_uuids(before, after):
    """StageRemovals for every top-level segment/via of before that after no longer holds."""
    def copper(text):
        return collections.Counter(text[a:b] for a,b in top_level_spans(text)
            if text[a+1:b].split(None,1)[0].rstrip(')') in ('segment','via'))
    removed=copper(before)-copper(after);uuids=[]
    for block,n in removed.items():
        match=UUID_RE.search(block)
        if not match:raise ValueError('source copper UUID missing')
        uuids.extend([match[1]]*n)
    return StageRemovals(sorted(uuids))


def removal_source(cuts):
    return 'stage' if isinstance(cuts,StageRemovals) else 'reviewed'


def write_stage_removals(path, before_path, after_path, cuts):
    path=Path(path)
    path.write_text(json.dumps(dict(source='stage',before_sha256=hashlib.sha256(Path(before_path).read_bytes()).hexdigest(),
        after_sha256=hashlib.sha256(Path(after_path).read_bytes()).hexdigest(),removed_uuids=sorted(cuts)),indent=1)+'\n')
    return path


def read_stage_removals(path, before_path, after_path):
    """A stage removal file is valid only for the exact two boards it was derived from."""
    data=json.loads(Path(path).read_text())
    if data.get('source')!='stage' or set(data)!={'source','before_sha256','after_sha256','removed_uuids'}:
        raise ValueError('unsupported stage removal scope')
    for key,board in (('before_sha256',before_path),('after_sha256',after_path)):
        if data[key]!=hashlib.sha256(Path(board).read_bytes()).hexdigest():raise ValueError('stage removal scope source mismatch')
    cuts=StageRemovals(data['removed_uuids'])
    if list(cuts)!=list(stage_removed_uuids(Path(before_path).read_text(),Path(after_path).read_text())):
        raise ValueError('stage removal scope differs from the board delta')
    return cuts


def removal_arguments(cuts, scope_path, before_path, after_path):
    """Command-line form of a removal scope for the native audit scripts."""
    if isinstance(cuts,StageRemovals):
        return ['--stage-removal-scope',str(write_stage_removals(scope_path,before_path,after_path,cuts))]
    return [arg for uid in sorted(cuts) for arg in ('--reviewed-cut-uuid',uid)]


def reviewed_copper_removals(before, after, reviewed_removed_uuids=()):
    """Permit only explicitly named, unique cuts; never permit replacement in place."""
    stage=isinstance(reviewed_removed_uuids,StageRemovals)
    cuts=list(reviewed_removed_uuids)
    if len(cuts)!=len(set(cuts)) or any(not isinstance(u,str) or not UUID_TEXT.fullmatch(u) for u in cuts):
        raise ValueError('stage removals require distinct UUIDs' if stage else 'reviewed cuts require at most twelve distinct UUIDs')
    if not stage and len(cuts)>REVIEWED_CUT_LIMIT:
        raise ValueError('reviewed cuts require at most twelve distinct UUIDs')
    def copper(text):
        return collections.Counter(text[a:b] for a,b in top_level_spans(text)
            if text[a+1:b].split(None,1)[0].rstrip(')') in ('segment','via'))
    old,new=copper(before),copper(after);removed=old-new
    if removed and not cuts:raise ValueError('not additive copper')
    if not cuts:return {}
    by_id=collections.defaultdict(list)
    for block,n in old.items():
        match=UUID_RE.search(block)
        if not match:raise ValueError('source copper UUID missing')
        by_id[match[1]].extend([block]*n)
    scope={}
    for uid in cuts:
        blocks=by_id.get(uid,[])
        if len(blocks)!=1 or removed[blocks[0]]!=1:
            raise ValueError('reviewed cut is missing, retained or ambiguous')
        if any(UUID_RE.search(block)[1]==uid for block in new):
            raise ValueError('reviewed cut UUID reused')
        scope[uid]=blocks[0][1:].split(None,1)[0].rstrip(')')
    if sum(removed.values())!=len(cuts):raise ValueError('unreviewed copper removed or changed')
    return scope


def unchanged_nonrouting(before, after, reviewed_removed_uuids=()):
    def blocks(text):
        return collections.Counter(text[a:b] for a,b in top_level_spans(text)
            if text[a+1:b].split(None,1)[0].rstrip(')') not in ('segment','via','zone'))
    a,b=blocks(before),blocks(after)
    if a!=b:raise ValueError('nonrouting geometry/settings changed')
    reviewed_copper_removals(before,after,reviewed_removed_uuids)
    return sum(a.values())


def added_copper_scope(before, after, expected_copper=None, expected_vias=None, reviewed_removed_uuids=()):
    """Bind every additive source object; retained historical UUID duplicates are allowed."""
    unchanged_nonrouting(before, after, reviewed_removed_uuids)
    def copper(text):
        return collections.Counter(text[a:b] for a,b in top_level_spans(text)
            if text[a+1:b].split(None,1)[0].rstrip(')') in ('segment','via'))
    old,new=copper(before),copper(after)
    old_ids={UUID_RE.search(block)[1] for block in old}
    scope={}
    for block,n in (new-old).items():
        match=UUID_RE.search(block)
        if not match:raise ValueError('new copper UUID missing')
        uid=match[1]
        if n!=1 or uid in old_ids or uid in scope:raise ValueError('new copper UUID reused or duplicated')
        scope[uid]=block[1:].split(None,1)[0].rstrip(')')
    if not scope:raise ValueError('empty added copper scope')
    actual=(len(scope),sum(kind=='via' for kind in scope.values()))
    for expected,found in zip((expected_copper,expected_vias),actual):
        if expected is not None and (type(expected) is not int or expected<0 or expected!=found):
            raise ValueError('added copper/via count mismatch')
    return scope


def new_silk_identities(drc, via_uuid):
    types=('silk_over_copper','silk_overlap')
    rows=[v for v in drc['violations'] if v['type'] in types]
    if any(sum(v['type']==kind for v in rows)>=199 for kind in types):
        raise ValueError('silk fixture reached report cap; subdivide it')
    return [v for v in rows if any(i['uuid']==via_uuid for i in v['items'])]


def shown_text(board):
    items=list(board.GetDrawings())
    for fp in board.GetFootprints():items.extend([*fp.GetFields(),*fp.GraphicalItems()])
    return sorted((x.m_Uuid.AsString(),x.GetShownText(True)) for x in items if hasattr(x,'GetShownText'))


def signature(v):
    import pcbnew
    if v.Type()==pcbnew.PCB_TRACE_T:
        return ('segment',v.GetStart().x,v.GetStart().y,v.GetEnd().x,v.GetEnd().y,v.GetWidth(),
                v.GetLayer(),v.HasSolderMask(),v.GetSolderMaskExpansion(),
                v.IsTented(pcbnew.F_SilkS),v.IsTented(pcbnew.B_SilkS))
    return (v.GetPosition().x,v.GetPosition().y,v.GetDrillValue(),v.GetWidth(pcbnew.F_Cu),
            list(v.GetLayerSet().Seq()),v.GetSolderMaskExpansion(),
            v.IsTented(pcbnew.F_SilkS),v.IsTented(pcbnew.B_SilkS))


def as_json(value):return json.loads(json.dumps(value))


PROBE_FLAG='--native-fixture-probe';PROBE_PREFIX='NATIVE-FIXTURE-PROBE ';PROBE_BATCH=32


def native_fixture_view(fixture):
    """Every native fixture observation the parent checks, from one loaded board."""
    import pcbnew
    loaded=pcbnew.LoadBoard(str(fixture));tracks=list(loaded.GetTracks())
    return dict(fixture=str(fixture),sha256=hashlib.sha256(Path(fixture).read_bytes()).hexdigest(),track_uuids=[t.m_Uuid.AsString() for t in tracks],
                signature=as_json(signature(tracks[0])) if len(tracks)==1 else None,
                pads=any(list(fp.Pads()) for fp in loaded.GetFootprints()),texts=as_json(shown_text(loaded)))


def probe_fixtures(fixtures):
    # pcbnew.LoadBoard boards are never released (taking SWIG ownership breaks the next
    # load), so fixtures are read in short-lived children, PROBE_BATCH at a time, as in
    # audit_zone_silk_scope.py; the parent keeps no per-fixture board.
    out=subprocess.run([sys.executable,__file__,PROBE_FLAG,*map(str,fixtures)],check=True,stdout=subprocess.PIPE,text=True).stdout
    rows=[json.loads(line[len(PROBE_PREFIX):]) for line in out.splitlines() if line.startswith(PROBE_PREFIX)]
    if [r.get('fixture') for r in rows]!=[str(f) for f in fixtures]:raise ValueError('native fixture probe did not return one observation per fixture')
    return rows


def main(before_path, after_path, out, expected_copper=382, expected_vias=38, reviewed_removed_uuids=()):
    import pcbnew
    version=subprocess.check_output(['kicad-cli','version'],text=True).strip()
    if version!='10.0.6':raise ValueError('requires pinned native10.0.6')
    out.mkdir(parents=True,exist_ok=True)
    (out/'started.json').write_text(json.dumps(dict(status='STARTED; NO NATIVE MASK RESULT YET',version=version,before_sha256=hashlib.sha256(before_path.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(after_path.read_bytes()).hexdigest()),indent=2)+'\n')
    count=unchanged_nonrouting(before_path.read_text(),after_path.read_text(),reviewed_removed_uuids)
    scope=added_copper_scope(before_path.read_text(),after_path.read_text(),expected_copper,expected_vias,reviewed_removed_uuids)
    for suffix in ('.kicad_pro','.kicad_dru'):
        if before_path.with_suffix(suffix).read_bytes()!=after_path.with_suffix(suffix).read_bytes():
            raise ValueError('project/rules changed')
    rules=after_path.with_suffix('.kicad_dru').read_text()
    if re.search(r'\(\s*constraint\s+(?:silk|solder)',rules):raise ValueError('custom silk/mask rule unsupported')
    before=pcbnew.LoadBoard(str(before_path));after=pcbnew.LoadBoard(str(after_path))
    for board in (before,after):
        if board.GetDesignSettings().m_SolderMaskMinWidth!=0:raise ValueError('mask healing unsupported')
        if any(z.IsOnLayer(l) for z in board.Zones() for l in (pcbnew.F_Mask,pcbnew.B_Mask)):
            raise ValueError('mask zones unsupported')
    old_ids={x.m_Uuid.AsString() for x in before.GetTracks()}
    added=[x for x in after.GetTracks() if x.m_Uuid.AsString() not in old_ids]
    native_scope={x.m_Uuid.AsString():('via' if x.Type()==pcbnew.PCB_VIA_T else 'segment') for x in added}
    if len(added)!=len(scope) or native_scope!=scope:raise ValueError('native/source added copper scope mismatch')
    vias=[]
    for item in added:
        if item.Type()==pcbnew.PCB_VIA_T:vias.append(item)
        elif item.Type()!=pcbnew.PCB_TRACE_T or item.HasSolderMask():
            raise ValueError('new non-via mask geometry unsupported')
    if len(vias)!=expected_vias:raise ValueError('native added via count mismatch')
    # Native silk_overlap also tests Cu shapes of unmasked tracks: checking
    # HasSolderMask alone cannot exclude them. Audit every added copper object.
    # Retain the exact native-serialized silk/context bytes; remove only pads,
    # copper and copper/rule zones from disposable fixtures.
    text=after_path.read_text();edits=[];via_blocks={}
    for a,b in top_level_spans(text):
        block=text[a:b];kind=block[1:].split(None,1)[0].rstrip(')')
        if kind in ('segment','via','zone'):
            if kind in ('via','segment'):
                uid=UUID_RE.search(block)[1]
                if uid not in old_ids:via_blocks[uid]=block
            edits.append((a,b,''))
        elif kind=='footprint':
            for x,y in top_level_spans(block):
                if block[x+1:y].split(None,1)[0].rstrip(')')=='pad':edits.append((a+x,a+y,''))
    common=replace_spans(text,edits)
    source_text=shown_text(after)
    settings=json.loads(after_path.with_suffix('.kicad_pro').read_text())['board']['design_settings']['rules']
    silk_clearance=math.ceil(settings['min_silk_clearance']*1_000_000)
    scoped_items=[(fp.m_Uuid.AsString(),fp.GetBoundingBox(True,True)) for fp in after.GetFootprints()]+[(x.m_Uuid.AsString(),x.GetBoundingBox()) for x in after.GetDrawings() if x.GetLayer()!=pcbnew.Edge_Cuts]
    scoped_ids={u for u,_ in scoped_items}
    scoped_blocks=[]
    for a,b in top_level_spans(common):
        match=UUID_RE.search(common[a:b])
        if match and match[1] in scoped_ids:scoped_blocks.append((a,b,match[1]))
    artwork=list(after.GetDrawings())+[x for fp in after.GetFootprints() for x in [*fp.GetFields(),*fp.GraphicalItems()]]
    if any(x.IsOnLayer(l) for x in artwork for l in (pcbnew.F_Mask,pcbnew.B_Mask)):
        raise ValueError('non-pad mask artwork unsupported')
    out.mkdir(parents=True,exist_ok=True);receipts=[];identities=set()
    def write_fixture(i,via):
        folder=out/f'fixture-{i:03d}';folder.mkdir(exist_ok=True)
        path=folder/after_path.name
        for suffix in ('.kicad_pro','.kicad_dru'):
            shutil.copyfile(after_path.with_suffix(suffix),path.with_suffix(suffix))
        box=via.GetBoundingBox();margin=max(0,via.GetSolderMaskExpansion())+max(0,silk_clearance)+5_000_000;box.Inflate(margin)
        selected={u for u,bbox in scoped_items if bbox.Intersects(box)}
        scoped=replace_spans(common,[(a,b,'') for a,b,u in scoped_blocks if u not in selected])
        end=scoped.rfind(')');path.write_text(scoped[:end]+via_blocks[via.m_Uuid.AsString()]+'\n'+scoped[end:])
        return folder,path,selected,margin
    ordered=sorted(added,key=lambda v:v.m_Uuid.AsString())
    for first in range(0,len(ordered),PROBE_BATCH):
        chunk=[(i,via,*write_fixture(i,via)) for i,via in enumerate(ordered[first:first+PROBE_BATCH],first)]
        for (i,via,folder,path,selected,margin),view in zip(chunk,probe_fixtures([c[3] for c in chunk])):
            if view['sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('native fixture probe read other bytes')
            if view['track_uuids']!=[via.m_Uuid.AsString()]:raise ValueError('fixture copper identity changed')
            if view['signature']!=as_json(signature(via)):raise ValueError('fixture mask/hole geometry changed')
            if view['pads']:raise ValueError('old pad masks remain')
            actual_text=[tuple(r) for r in view['texts']];text_ids={u for u,_ in actual_text}
            if actual_text!=[(u,t) for u,t in source_text if u in text_ids]:raise ValueError('fixture text rendering changed')
            report=folder/'drc.json'
            subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--output',str(report),str(path)],check=True,stdout=subprocess.DEVNULL)
            drc=json.loads(report.read_text());rows=new_silk_identities(drc,via.m_Uuid.AsString())
            for v in rows:
                ids=tuple(sorted(x['uuid'] for x in v['items']))
                if via.m_Uuid.AsString() not in ids:raise ValueError('silk warning not attributable to sole new copper object')
                identities.add((v['type'],v['severity'],ids))
            receipts.append(dict(copper_uuid=via.m_Uuid.AsString(),kind='via' if via.Type()==pcbnew.PCB_VIA_T else 'segment',native_mask_signature=signature(via),selected_native_bbox_uuids=sorted(selected),conservative_bbox_margin_nm=margin,
                                 violations=rows,report_sha256=hashlib.sha256(report.read_bytes()).hexdigest()))
            print(f'{i+1}/{len(added)} copper fixtures, {len(identities)} new silk identities',flush=True)
    result=dict(status='READ-ONLY NATIVE ADDED-MASK EVIDENCE; PROMOTION GATE UNCHANGED',version=version,
                before_sha256=hashlib.sha256(before_path.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(after_path.read_bytes()).hexdigest(),
                unchanged_nonrouting_objects=count,added_unmasked_tracks=len(added)-len(vias),
                added_copper_scope_complete=True,added_copper_source_scope=scope,
                new_mask_identities=sorted(identities),fixtures=receipts)
    if reviewed_removed_uuids:
        result['reviewed_copper_removals']=reviewed_copper_removals(before_path.read_text(),after_path.read_text(),reviewed_removed_uuids)
        result['copper_removal_source']=removal_source(reviewed_removed_uuids)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__' and sys.argv[1:2]==[PROBE_FLAG]:
    for fixture in sys.argv[2:]:print(PROBE_PREFIX+json.dumps(native_fixture_view(Path(fixture))),flush=True)
elif __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    for name in ('before','after','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--expected-copper',type=int,default=382)
    parser.add_argument('--expected-vias',type=int,default=38)
    parser.add_argument('--reviewed-cut-uuid',action='append',default=[])
    parser.add_argument('--stage-removal-scope',type=Path)
    args=parser.parse_args()
    if args.stage_removal_scope and args.reviewed_cut_uuid:parser.error('use reviewed cuts or a stage removal scope, not both')
    cuts=read_stage_removals(args.stage_removal_scope,args.before,args.after) if args.stage_removal_scope else args.reviewed_cut_uuid
    main(args.before,args.after,args.output,args.expected_copper,args.expected_vias,cuts)
