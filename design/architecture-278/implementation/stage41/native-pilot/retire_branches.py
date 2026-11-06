"""Retire only five exact, separately reviewed local supply occurrences."""
from pathlib import Path
import argparse
import json
import shutil
from identity_guard import digest, inventory, compare, bound_retirements, top_level_spans
ROOT=Path(__file__).resolve().parents[5]


def retire(source, proof_path, output):
    cache=(ROOT/'.circuit-cache').resolve()
    if output.resolve().parent!=cache or source.resolve().parent!=cache or output.exists():
        raise ValueError('requires existing source/new direct disposable cache directories')
    proof=json.loads(proof_path.read_text());receipt=json.loads((source/'prepare-receipt.json').read_text())
    if receipt.get('retired_local_supply_copper'):raise ValueError('already retired')
    if proof['native_version']!='10.0.6' or proof['canonical_sha256']!=receipt['canonical_sha256']:
        raise ValueError('branch proof baseline/version binding')
    rows=[r for branch in proof['branches'] for r in branch['objects'] if r['proposed_retirement']]
    receipt['retired_local_supply_copper']=rows
    canonical=(ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb').read_text()
    if digest(canonical)!=receipt['canonical_sha256']:raise ValueError('canonical baseline binding')
    bound_retirements(receipt,canonical)
    receipt['local_supply_contact_proof_sha256']=digest(proof_path.read_text())
    board=source/'osc-jack-left.kicad_pcb';raw=board.read_text();hashes={r['sha256'] for r in rows}
    spans=[(a,b) for a,b in top_level_spans(raw) if digest(raw[a:b]) in hashes]
    if len(spans)!=5 or len(hashes)!=5:raise ValueError('five exact occurrences not found')
    edited=raw
    for a,b in reversed(spans):edited=edited[:a]+edited[b:]
    gate=compare(inventory(raw),inventory(edited),hashes,[])
    if not gate['accepted']:raise ValueError('unexpected raw changes')
    output.mkdir()
    for item in source.iterdir():
        if item.is_dir():shutil.copytree(item,output/item.name)
        elif item.suffix in ('.kicad_pro','.kicad_sch','.kicad_dru') or item.name in ('fp-lib-table','sym-lib-table'):
            shutil.copy2(item,output/item.name)
    (output/board.name).write_text(edited)
    (output/'prepare-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'retired_local_supply_objects':5,'source_sha256':digest(raw),'output_sha256':digest(edited),'status':'RAW DELTA ONLY; native gates pending'}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('source','proof','output'):p.add_argument(name,type=Path)
    a=p.parse_args();retire(a.source,a.proof,a.output)
