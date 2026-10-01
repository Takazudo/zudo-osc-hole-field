"""Replay retained power routes and owned planes into a disposable native PCB.

Invoke with the pinned KiCad oracle through heavy-guard. This generates an
unselected draft; all native and electrical promotion gates remain separate.
"""
import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.apply_rail_transfers import apply as apply_transfers
from scripts.pcbgen.apply_terminal_bridges import apply as apply_bridges
from scripts.pcbgen.generate_power_candidate import generate
from scripts.pcbgen.prepare_source_planes import prepare
from scripts.pcbgen.native_stack import apply as apply_stack


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(specification,checkpoint,output,receipt):
    spec=json.loads(specification.read_text());board_id=spec['board_id']
    canonical=ROOT/'boards'/board_id/(board_id+'.kicad_pcb')
    if output.resolve() in (canonical.resolve(),checkpoint.resolve()):
        raise ValueError('power replay requires a separate disposable output')
    if digest(checkpoint)!=spec['checkpoint_board_sha256']:
        raise ValueError('power replay checkpoint differs from retained source')
    retirement_path=ROOT/spec['retirement_source']
    if digest(retirement_path)!=spec['retirement_source_sha256']:
        raise ValueError('power replay retirement contract changed')
    if digest(ROOT/spec['plane_proposal'])!=spec['plane_proposal_sha256']:
        raise ValueError('power replay plane/stack proposal changed')
    output.parent.mkdir(parents=True,exist_ok=True)
    for suffix in ('.kicad_pro','.kicad_sch'):
        shutil.copyfile(checkpoint.with_suffix(suffix),output.with_suffix(suffix))
    with tempfile.TemporaryDirectory(prefix='power-source-replay-',dir=output.parent) as temporary:
        temporary=Path(temporary)
        definition=temporary/(board_id+'.json')
        generate(board_id,ROOT/spec['plane_proposal'],spec['plane_profile'],definition)
        source_definition=json.loads(definition.read_text())
        shutil.copyfile(definition.with_suffix('.kicad_dru'),output.with_suffix('.kicad_dru'))
        bridges=temporary/'bridges.json'
        bridges.write_text(json.dumps({'board_id':board_id,'board_sha256':digest(checkpoint),
            'bridges':spec['terminal_bridges']})+'\n')
        stage1=temporary/'bridges.kicad_pcb';bridge_receipt=temporary/'bridges-receipt.json'
        apply_bridges(checkpoint,bridges,stage1,bridge_receipt)
        routing=source_definition['routing']
        rules={net:rule for rule in routing['net_classes'] for net in rule['nets']}
        transfers=temporary/'transfers.json'
        transfers.write_text(json.dumps({'board_id':board_id,'board_sha256':digest(stage1),
            'added':spec['transfers'],'rules_by_net':rules,
            'local_escape_overrides':routing['local_escape_overrides']})+'\n')
        stage2=temporary/'transfers.kicad_pcb';transfer_receipt=temporary/'transfers-receipt.json'
        apply_transfers(stage1,transfers,stage2,transfer_receipt)
        # Candidate-only retired vias are already omitted by the retained
        # source. Only the exact listed prior-copper retirements occur here.
        retirements=json.loads(retirement_path.read_text())
        retirements['boards'][board_id]=[r for r in retirements['boards'][board_id]
                                        if r['present_in_canonical_prior_copper']]
        retired=temporary/'prior-retirements.json';retired.write_text(json.dumps(retirements)+'\n')
        plane_receipt=temporary/'planes-receipt.json'
        prepare(board_id,stage2,output,plane_receipt,definition,retired)
        updated,stack_receipt=apply_stack(output.read_text(),source_definition)
        output.write_text(updated)
        reports={name:json.loads(path.read_text()) for name,path in (
            ('terminal_bridges',bridge_receipt),('local_transfers',transfer_receipt),('owned_planes',plane_receipt))}
        result={'status':'UNSELECTED replayed draft; native/electrical/qualification gates pending',
            'board_id':board_id,'specification_sha256':digest(specification),
            'checkpoint_sha256':digest(checkpoint),'output_sha256':digest(output),
            'definition':source_definition,'stage_receipts':reports,'native_stack_metadata':stack_receipt,
            'canonical_unchanged':digest(checkpoint)==spec['checkpoint_board_sha256']}
    receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(board_id,'source replay complete; native and electrical acceptance still pending')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for field in ('specification','checkpoint','output','receipt'):parser.add_argument(field,type=Path)
    args=parser.parse_args();replay(args.specification,args.checkpoint,args.output,args.receipt)
