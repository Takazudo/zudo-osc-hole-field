"""Native evidence for every new copper/silkscreen interaction; never promote a board.

Requires exact non-copper/non-zone invariance, additive copper, unmasked new
tracks, no mask zones/custom silk rules, and zero mask-healing width. A fixture
contains all unchanged silkscreen and outline geometry, no old mask objects,
and one new copper object. Both silk warning categories are checked below their caps. Any cap hit or
unsupported scope fails closed. Full-board checks remain mandatory.
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


def unchanged_nonrouting(before, after):
    def blocks(text):
        return collections.Counter(text[a:b] for a,b in top_level_spans(text)
            if text[a+1:b].split(None,1)[0].rstrip(')') not in ('segment','via','zone'))
    a,b=blocks(before),blocks(after)
    if a!=b:raise ValueError('nonrouting geometry/settings changed')
    def copper(text):
        return collections.Counter(text[a:b] for a,b in top_level_spans(text) if text[a+1:b].split(None,1)[0].rstrip(')') in ('segment','via'))
    ca,cb=copper(before),copper(after)
    if ca-cb:raise ValueError('not additive copper')
    return sum(a.values())


def new_silk_identities(drc, via_uuid):
    types=('silk_over_copper','silk_overlap')
    rows=[v for v in drc['violations'] if v['type'] in types]
    if any(sum(v['type']==kind for v in rows)>=199 for kind in types):
        raise ValueError('silk fixture reached report cap; subdivide it')
    return [v for v in rows if any(i['uuid']==via_uuid for i in v['items'])]


def main(before_path, after_path, out):
    import pcbnew
    version=subprocess.check_output(['kicad-cli','version'],text=True).strip()
    if version!='10.0.6':raise ValueError('requires pinned native10.0.6')
    out.mkdir(parents=True,exist_ok=True)
    (out/'started.json').write_text(json.dumps(dict(status='STARTED; NO NATIVE MASK RESULT YET',version=version,before_sha256=hashlib.sha256(before_path.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(after_path.read_bytes()).hexdigest()),indent=2)+'\n')
    count=unchanged_nonrouting(before_path.read_text(),after_path.read_text())
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
    if len(added)!=382:raise ValueError('not the pinned382-object ground trial')
    vias=[]
    for item in added:
        if item.Type()==pcbnew.PCB_VIA_T:vias.append(item)
        elif item.Type()!=pcbnew.PCB_TRACE_T or item.HasSolderMask():
            raise ValueError('new non-via mask geometry unsupported')
    if len(vias)!=38:raise ValueError('expected38new vias')
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
    def shown_text(board):
        items=list(board.GetDrawings())
        for fp in board.GetFootprints():items.extend([*fp.GetFields(),*fp.GraphicalItems()])
        return sorted((x.m_Uuid.AsString(),x.GetShownText(True)) for x in items if hasattr(x,'GetShownText'))
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
    for i,via in enumerate(sorted(added,key=lambda v:v.m_Uuid.AsString())):
        folder=out/f'fixture-{i:03d}';folder.mkdir(exist_ok=True)
        path=folder/after_path.name
        for suffix in ('.kicad_pro','.kicad_dru'):
            shutil.copyfile(after_path.with_suffix(suffix),path.with_suffix(suffix))
        box=via.GetBoundingBox();margin=max(0,via.GetSolderMaskExpansion())+max(0,silk_clearance)+5_000_000;box.Inflate(margin)
        selected={u for u,bbox in scoped_items if bbox.Intersects(box)}
        scoped=replace_spans(common,[(a,b,'') for a,b,u in scoped_blocks if u not in selected])
        end=scoped.rfind(')');path.write_text(scoped[:end]+via_blocks[via.m_Uuid.AsString()]+'\n'+scoped[end:])
        loaded=pcbnew.LoadBoard(str(path));tracks=list(loaded.GetTracks())
        if len(tracks)!=1 or tracks[0].m_Uuid.AsString()!=via.m_Uuid.AsString():raise ValueError('fixture copper identity changed')
        def signature(v):
            if v.Type()==pcbnew.PCB_TRACE_T:
                return ('segment',v.GetStart().x,v.GetStart().y,v.GetEnd().x,v.GetEnd().y,v.GetWidth(),
                        v.GetLayer(),v.HasSolderMask(),v.GetSolderMaskExpansion(),
                        v.IsTented(pcbnew.F_SilkS),v.IsTented(pcbnew.B_SilkS))
            return (v.GetPosition().x,v.GetPosition().y,v.GetDrillValue(),v.GetWidth(pcbnew.F_Cu),
                    list(v.GetLayerSet().Seq()),v.GetSolderMaskExpansion(),
                    v.IsTented(pcbnew.F_SilkS),v.IsTented(pcbnew.B_SilkS))
        if signature(tracks[0])!=signature(via):raise ValueError('fixture mask/hole geometry changed')
        if any(list(fp.Pads()) for fp in loaded.GetFootprints()):raise ValueError('old pad masks remain')
        actual_text=shown_text(loaded);text_ids={u for u,_ in actual_text}
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
                added_copper_scope_complete=True,
                new_mask_identities=sorted(identities),fixtures=receipts)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main(*(Path(p) for p in sys.argv[1:4]))
