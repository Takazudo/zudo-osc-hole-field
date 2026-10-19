"""Prepare B2-specific electronics with source-bound local branch retirements."""
from pathlib import Path
from collections import Counter
import copy, json, re, shutil, sys
import pcbnew
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import inventory, digest, kind
from native_guard import check_native
from scripts.pcbgen.uuid_tools import top_level_spans, replace_spans, stable_uuid
BASE = ROOT/'.circuit-cache/stage42-full-b1-fresh/osc-jack-left.kicad_pcb'
BASE_HASH = '975cd15d5ba69b9695e8d32a575a289306a27f1ea17d6b5f7a5819071dc5505b'

from branches import REFS

def prepare(out, branches_path, adjustments_path):
    if out.resolve().parent != (ROOT/'.circuit-cache').resolve(): raise ValueError('disposable direct child required')
    raw = BASE.read_text()
    if digest(raw) != BASE_HASH or pcbnew.GetBuildVersion() != '10.0.6': raise ValueError('baseline/version')
    out.mkdir(exist_ok=False)
    for p in BASE.parent.iterdir():
        if p.name == 'sheets': shutil.copytree(p, out/p.name)
        elif p.suffix in ('.kicad_pro', '.kicad_sch', '.kicad_dru') or p.name in ('fp-lib-table','sym-lib-table'): shutil.copy2(p, out/p.name)
    plan = json.loads((ROOT/'design/architecture-278/implementation/stage40/mult-copper-plan/plan.json').read_text())
    evidence = ROOT/'design/architecture-278/implementation/stage42/full-b1/evidence'
    poses = json.loads((evidence/'prepare-receipt.json').read_text())['poses']
    refs = {r: v['B2_ref'] for r,v in plan['candidate_B1'].items()}
    moved = {refs[r['ref']] for r in poses}
    board = pcbnew.LoadBoard(str(BASE)); check_native(board,raw)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    nets = {}
    for a,b in refs.items():
        ap = {p.GetNumber():p for p in fps[a].Pads()}; bp = {p.GetNumber():p for p in fps[b].Pads()}
        if ap.keys()!=bp.keys(): raise ValueError('pin mismatch')
        for pin,p in ap.items():
            old,new = p.GetNetname(),bp[pin].GetNetname()
            if old in nets and nets[old]!=new: raise ValueError('nonfunctional net mapping')
            nets[old]=new
    if len(set(nets.values()))!=len(nets): raise ValueError('noninjective mapping')
    private = set(nets.values()) - {'AGND','+12V','-12V','+5V'} - {r['native_net'] for r in plan['NC_equivalence']}
    if len(refs)!=36 or len(moved)!=31 or len(private)!=24: raise ValueError('scope')
    private_rows=[r for r in plan['private_net_retire_copper'] if r['net'] in private]
    branch=json.loads(branches_path.read_text())
    if branch['baseline_sha256']!=BASE_HASH or set(branch['scope_refs'])!=REFS:raise ValueError('branch proof baseline/scope')
    shared_rows=branch['screened_retirements']
    expected=Counter(r['sha256'] for r in private_rows+shared_rows)
    if len(expected)!=len(private_rows)+len(shared_rows):raise ValueError('ambiguous retirement')
    before = inventory(raw)
    retire=[]; edits=[]
    for a,z in top_level_spans(raw):
        part=raw[a:z]; h=digest(part)
        if h in expected:
            retire.append(h); edits.append((a,z,''))
    if Counter(retire)!=expected or len(private_rows)!=830: raise ValueError('B2 occurrence binding')
    stripped=replace_spans(raw,edits)
    target=out/BASE.name; target.write_text(stripped)
    board=pcbnew.LoadBoard(str(target));check_native(board,stripped)
    fps={f.GetReference():f for f in board.GetFootprints()}
    adjustments=json.loads(adjustments_path.read_text())
    if not set(adjustments)<=moved:raise ValueError('adjustments outside B2 electronics')
    final_poses=[]
    for pose in poses:
        ref=refs[pose['ref']]
        f=fps[ref]; source_fp=fps[pose['ref']]
        layer=source_fp.GetLayer()
        xy=[source_fp.GetPosition().x+34000000,source_fp.GetPosition().y]
        angle=source_fp.GetOrientationDegrees()
        if ref=='R3209':layer=f.GetLayer();xy=[f.GetPosition().x,f.GetPosition().y];angle=f.GetOrientationDegrees()
        if ref in adjustments:
            change=adjustments[ref]
            xy=[xy[i]+round(change.get('delta_mm',[0,0])[i]*1000000) for i in (0,1)]
            if 'xy_mm' in change:xy=[round(v*1000000) for v in change['xy_mm']]
            if 'angle' in change:angle=change['angle']
        pose=dict(pose,origin=[xy[0]/1000000-100,xy[1]/1000000-50],native_angle=angle,layer=board.GetLayerName(layer))
        if f.GetLayer()!=layer:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(pose['native_angle'])
        f.SetPosition(pcbnew.VECTOR2I(*xy))
        final_poses.append({'ref':ref,'origin_nm':xy,'native_angle':angle,'layer':board.GetLayerName(layer),'pads':[{'pin':p.GetNumber(),'uuid':p.m_Uuid.AsString(),'net':p.GetNetname(),'xy_nm':[p.GetPosition().x,p.GetPosition().y]} for p in f.Pads()]})
    check_native(board,stripped)
    serialization=out/'serialization.kicad_pcb';pcbnew.SaveBoard(str(serialization),board)
    generated={}
    serialized=serialization.read_text()
    for a,z in top_level_spans(serialized):
        part=serialized[a:z]
        if kind(part)=='footprint':
            ref=re.search(r'\(property\s+"Reference"\s+"([^"]+)"',part)[1]
            if ref in moved:generated[ref]=part
    edits=[]
    for a,z in top_level_spans(stripped):
        part=stripped[a:z]
        if kind(part)=='footprint':
            ref=re.search(r'\(property\s+"Reference"\s+"([^"]+)"',part)[1]
            if ref in moved:edits.append((a,z,generated[ref]))
    prepared=replace_spans(stripped,edits); target.write_text(prepared)
    after=inventory(prepared)
    expected_copper=before['copper'].copy()
    for h in retire:
        if len(before['raw_copper'][h])!=1: raise ValueError('ambiguous retirement')
        expected_copper.subtract(before['raw_copper'][h])
    expected_copper=+expected_copper
    if after['copper']!=expected_copper:raise ValueError('retained copper changed')
    if any(h!=after['footprints'][r] for r,h in before['footprints'].items() if r not in moved):raise ValueError('foreign footprint changed')
    owners={n:sorted({f.GetReference() for f in board.GetFootprints() for p in f.Pads() if p.GetNetname()==n}) for n in private}
    if any(not set(o)<=set(refs.values()) for o in owners.values()):raise ValueError('foreign private owner')
    receipt={'baseline_sha256':BASE_HASH,'prepared_sha256':digest(prepared),'mapping':refs,'net_mapping':nets,'moved':sorted(moved),'poses':final_poses,'private_net_owners':owners,'retired_hashes':retire,'retired_private_copper':private_rows,'retired_local_supply_copper':shared_rows,'prepared_footprint_hashes':after['footprints'],'branch_proof_sha256':digest(branches_path.read_text()),'adjustments_sha256':digest(adjustments_path.read_text())}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'prepared_sha256':digest(prepared),'retired':len(retire),'shared_retirements':len(shared_rows),'moved':len(moved)}))

if __name__=='__main__':prepare(*(Path(p) for p in sys.argv[1:]))
