"""Disposable owned-plane regeneration with byte-preserved owner copper."""
from __future__ import annotations
import argparse,hashlib,json,re,sys,tempfile
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.route_kicad import apply_classes,ensure_zones
from scripts.pcbgen.definition import load_definition
from scripts.pcbgen.uuid_tools import normalize_file,stable_uuid,top_level_spans,UUID_RE
from scripts.pcbgen.verify_local_links import blocks
from scripts.pcbgen.source_zones import retire
from scripts.pcbgen.source_copper import retire_vias
ROOT=Path(__file__).resolve().parents[2]

def prepare(board_id,source,output,receipt,definition_path=None,retired_vias_path=None):
    if source.resolve()==output.resolve():raise ValueError('plane candidate must be disposable')
    original=blocks(source);definition=load_definition(definition_path or ROOT/'design/boards'/f'{board_id}.json')
    if definition.board_id!=board_id:raise ValueError('candidate definition belongs to another board')
    filtered,retired=retire(source.read_text(),board_id,definition.routing)
    retired_vias=[]
    if retired_vias_path:
        filtered,retired_vias=retire_vias(filtered,board_id,json.loads(retired_vias_path.read_text()))
    retired_via_ids={r['uuid'] for r in retired_vias}
    with tempfile.TemporaryDirectory(prefix='source-pours-',dir=output.parent) as temporary:
        native_input=Path(temporary)/'input.kicad_pcb';native_input.write_text(filtered)
        board=pcbnew.LoadBoard(str(native_input))
    board.SetFileName(str(output));apply_classes(board,definition.routing);new_ids,managed=ensure_zones(board,board_id,definition);managed.update(retired)
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):raise ValueError('native owned-plane refill failed')
    pcbnew.SaveBoard(str(output),board)
    refs={fp.GetReference() for fp in board.GetFootprints() if fp.m_Uuid.AsString()==stable_uuid(board_id,'footprint:'+fp.GetReference(),'root')}
    normalize_file(output,board_id,refs,new_ids,False,managed)
    # Preserve all prior copper exactly, including owner lock state.
    text=output.read_text();replacements=[]
    for start,end in top_level_spans(text):
        block=text[start:end];kind=re.match(r'\(([A-Za-z0-9_]+)',block)
        if kind and kind[1] in ('segment','via','arc'):
            key=UUID_RE.search(block)[1]
            if key not in original[kind[1]]:raise ValueError('plane regeneration unexpectedly introduced copper')
            replacements.append((start,end,original[kind[1]][key]))
    for start,end,block in reversed(replacements):text=text[:start]+block+text[end:]
    output.write_text(text);candidate=blocks(output)
    for kind in ('footprint','segment','via','arc'):
        expected={k:v for k,v in original[kind].items() if kind!='via' or k not in retired_via_ids}
        if expected!=candidate[kind]:raise ValueError(f'owned-plane regeneration changed {kind}')
    # Only explicitly source-owned pour blocks may change; reservations and
    # owner graphics/configuration remain byte-identical.
    old_nonzone=original['non_copper'].copy();new_nonzone=candidate['non_copper'].copy()
    for key,block in original['zone'].items():
        if key in managed:old_nonzone[block]-=1
        elif candidate['zone'].get(key)!=block:raise ValueError('source regeneration changed a keepout/owner zone')
    for key,block in candidate['zone'].items():
        if key in managed:new_nonzone[block]-=1
    if +old_nonzone!=+new_nonzone:raise ValueError('source regeneration changed non-zone owner state')
    report={'status':'DISPOSABLE DRAFT; native rule/parity/warning/connectivity gates pending','board_id':board_id,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'all_prior_copper_blocks_preserved':True,'all_footprints_graphics_keepouts_preserved':True,'source_owned_pour_count':len(managed),'new_owned_zone_count':len(set(candidate['zone'])-set(original['zone']))}
    report['all_prior_copper_blocks_preserved']=not retired_vias
    report['explicit_source_owned_retired_vias']=retired_vias
    report['all_other_prior_copper_blocks_preserved']=True
    receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(f'{board_id}: source planes prepared; {len(retired_vias)} explicit source via retirements; remaining owner copper/footprints/keepouts byte-preserved')

def main():
    p=argparse.ArgumentParser();p.add_argument('board_id');p.add_argument('--board',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--definition',type=Path);p.add_argument('--retire-vias',type=Path);a=p.parse_args();prepare(a.board_id,a.board,a.output,a.receipt,a.definition,a.retire_vias)
if __name__=='__main__':main()
