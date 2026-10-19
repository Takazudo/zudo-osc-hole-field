"""Recover the intended retained identities for diagnosis, never accept native repair.

Only baseline-identical geometry whose net was changed in the failed native
attempt is restored. No copper is removed or rerouted. Refilling is still pending.
"""
from pathlib import Path
import json,shutil,sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import inventory,digest,kind,value,top_level_spans
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import replace_spans

def recover(source,out):
    if out.parent.resolve()!=(ROOT/'.circuit-cache').resolve():raise ValueError('fresh disposable directory required')
    baseline=ROOT/'.circuit-cache/stage42-full-b1-fresh/osc-jack-left.kicad_pcb'
    old=baseline.read_text();raw=(source/baseline.name).read_text()
    if digest(old)!='975cd15d5ba69b9695e8d32a575a289306a27f1ea17d6b5f7a5819071dc5505b':raise ValueError('baseline')
    before=inventory(old);after=inventory(raw)
    nets={k[:3]:k[3] for k in before['copper']}
    changed={k[1]:(nets[k[:3]],k[3]) for k in after['copper'] if k[:3] in nets and nets[k[:3]]!=k[3]}
    if len(changed)!=11:raise ValueError('expected observed eleven relabels')
    parts={}
    for a,z in top_level_spans(old):
        p=old[a:z]
        if kind(p) in ('segment','via') and value(p,'uuid') in changed:
            if value(p,'uuid') in parts:raise ValueError('ambiguous UUID')
            parts[value(p,'uuid')]=p
    edits=[]
    for a,z in top_level_spans(raw):
        p=raw[a:z]
        if kind(p) in ('segment','via') and value(p,'uuid') in parts:edits.append((a,z,parts[value(p,'uuid')]))
    if len(edits)!=11:raise ValueError('restoration scope')
    out.mkdir(exist_ok=False)
    for p in source.iterdir():
        if p.name=='sheets':shutil.copytree(p,out/p.name)
        elif p.name in ('receipt.json','proposal.json','fp-lib-table','sym-lib-table') or p.suffix in ('.kicad_pro','.kicad_sch','.kicad_dru'):shutil.copy2(p,out/p.name)
    result=replace_spans(raw,edits);(out/baseline.name).write_text(result)
    (out/'recovery.json').write_text(json.dumps({'failed_native_sha256':digest(raw),'intended_sha256':digest(result),'restored_net_identities':changed,'limits':'Raw identity diagnosis only. Fills inherited from invalid attempt; no native qualification.'},indent=2)+'\n')
if __name__=='__main__':recover(Path(sys.argv[1]),Path(sys.argv[2]))
