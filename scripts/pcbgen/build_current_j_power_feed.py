"""Derive exact fitted rail-pad connectivity from a current white-pad J export.

This is a source/native contact mapping only, not a fresh routing or electrical
qualification receipt. The original native board and DRC are bound by v6.
"""
import argparse
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.jack_white_current_binding import verify as verify_jack_native
from scripts.pcbgen.source_contact_inventory import expected_contacts,reconcile_native

ROOT=Path(__file__).resolve().parents[2]
RAILS=('+12V','-12V','+5V')
COUNT={'osc-jack-left':599,'osc-jack-right':553}


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def derive(native_path,receipt_path):
    native_path=Path(native_path);receipt_path=Path(receipt_path)
    helpers=(ROOT/'scripts/pcbgen/build_current_j_power_feed.py',
             ROOT/'scripts/pcbgen/source_contact_inventory.py',
             ROOT/'scripts/pcbgen/jack_white_current_binding.py')
    helper_sha={str(p.resolve()):digest(p) for p in helpers}
    native_bytes=native_path.read_bytes();native=json.loads(native_bytes)
    bid=native.get('board_id')
    if bid not in COUNT:raise ValueError('one current J half required')
    receipt_bytes=receipt_path.read_bytes();prior=json.loads(receipt_bytes)
    if (prior.get('board_id')!=bid or prior['native_export_sha256']!=hashlib.sha256(native_bytes).hexdigest()
        or verify_jack_native(bid.removeprefix('osc-jack-'))!=prior):
        raise ValueError('current J source/native authority differs')
    partition_path=ROOT/'design/partition/partition.json';io_path=ROOT/'design/reports/io-partition.json'
    partition_bytes=partition_path.read_bytes();io_bytes=io_path.read_bytes()
    partition=json.loads(partition_bytes);io=json.loads(io_bytes)
    board=next(b for b in partition['boards'] if b['id']==bid)
    fitted={r['ref'] for r in partition['assignment']['components'] if r['board']==board['board_key'] and r['fitted']}
    expected=expected_contacts(bid,partition,io,set(RAILS))
    pads=reconcile_native(native,expected,fitted,set(RAILS))
    if len(pads)!=COUNT[bid]:raise ValueError('current J rail fitted contact count differs')
    result=[]
    for (ref,pad,net),item in sorted(pads.items()):
        result.append({'ref':ref,'pad':pad,'net':net,'uuid':item['uuid'],
                       'connected_to_load_land':item['uuid'] in native['main_rail_members'][net]})
    if not all(row['connected_to_load_land'] for row in result):
        raise ValueError('current J native fitted rail feed is disconnected')
    paths=(native_path,receipt_path,partition_path,io_path,*helpers)
    sources=dict(helper_sha)
    for path in paths:
        key=str(path.resolve());value=digest(path)
        if key in sources and sources[key]!=value:
            raise ValueError('current J power mapping helper changed during derivation: '+key)
        sources[key]=value
    if (sources[str(native_path.resolve())]!=hashlib.sha256(native_bytes).hexdigest()
        or sources[str(receipt_path.resolve())]!=hashlib.sha256(receipt_bytes).hexdigest()
        or sources[str(partition_path.resolve())]!=hashlib.sha256(partition_bytes).hexdigest()
        or sources[str(io_path.resolve())]!=hashlib.sha256(io_bytes).hexdigest()):
        raise ValueError('current J power mapping input changed after parse')
    for name,want in prior['source_sha256'].items():
        path=(ROOT/name).resolve();key=str(path)
        if key in sources and sources[key]!=want:
            raise ValueError('conflicting current J power source dependency: '+key)
        sources[key]=want
    for name,want in sources.items():
        if digest(name)!=want:raise ValueError('current J rail source changed during feed mapping: '+name)
    return {'status':'DERIVED current native fitted rail feed identity/connectivity mapping only; resistance/current/material/contact acceptance OPEN',
            'board_id':bid,'board_sha256':native['board_sha256'],
            'native_export_sha256':hashlib.sha256(native_bytes).hexdigest(),
            'native_receipt_sha256':hashlib.sha256(receipt_bytes).hexdigest(),
            'source_sha256':sources,'fitted_rail_pad_feeds':result,
            'scope':'Exact current native main-component membership of every fitted source rail pad. No route locality, temperature, physical contact, rail-drop or common-budget conclusion.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('native','receipt','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('fresh current J power mapping path required')
    report=derive(args.native,args.receipt)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as handle:json.dump(report,handle,indent=2,sort_keys=True);handle.write('\n')
    print(report['board_id'],len(report['fitted_rail_pad_feeds']),report['status'])
