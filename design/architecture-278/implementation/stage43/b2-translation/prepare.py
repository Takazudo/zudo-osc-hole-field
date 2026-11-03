"""Exact B1-to-B2 translation experiment; never canonical or accepted hardware."""
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

from translation import translated

def prepare(out):
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
    expected = Counter(r['sha256'] for r in plan['private_net_retire_copper'] if r['net'] in private)
    before = inventory(raw)
    retire=[]; edits=[]
    for a,z in top_level_spans(raw):
        part=raw[a:z]; h=digest(part)
        if h in expected:
            retire.append(h); edits.append((a,z,''))
    if Counter(retire)!=expected or len(retire)!=830: raise ValueError('B2 occurrence binding')
    stripped=replace_spans(raw,edits)
    target=out/BASE.name; target.write_text(stripped)
    board=pcbnew.LoadBoard(str(target));check_native(board,stripped)
    fps={f.GetReference():f for f in board.GetFootprints()}
    for pose in poses:
        f=fps[refs[pose['ref']]]; layer=board.GetLayerID(pose['layer'])
        if f.GetLayer()!=layer:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(pose['native_angle'])
        f.SetPosition(pcbnew.VECTOR2I(*(round(v*1000000) for v in (pose['origin'][0]+134,pose['origin'][1]+50))))
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
    rows=[]
    for name in ('power-proposal.json','signal-proposal.json'):
        rows += [translated(r,nets) for r in json.loads((evidence/name).read_text())['copper']]
    (out/'proposal.json').write_text(json.dumps({'board_sha256':digest(prepared),'removed_uuids':[],'copper':rows},indent=2)+'\n')
    (out/'receipt.json').write_text(json.dumps({'baseline_sha256':BASE_HASH,'prepared_sha256':digest(prepared),'mapping':refs,'net_mapping':nets,'moved':sorted(moved),'retired_hashes':retire,'prepared_footprint_hashes':after['footprints'],'added_count':len(rows),'shared_retirements':0,'translation_nm':[34000000,0]},indent=2)+'\n')
    print(json.dumps({'prepared_sha256':digest(prepared),'retired':len(retire),'new':len(rows),'moved':len(moved)}))

if __name__=='__main__':prepare(Path(sys.argv[1]))
