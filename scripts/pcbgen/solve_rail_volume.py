"""Run the shared four-foil conductor diagnostic for one explicit native rail.

Whole-board execution requires heavy-guard. Relabeling is a recorded extractor
role only; the native PCB/netlist and every conductor primitive are unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.power_load_ledger import mapping
from scripts.pcbgen.screen_rail_transfers import screen, bind_artifact_paths
from scripts.pcbgen.selected_conductor_export import select
from scripts.pcbgen.solve_conductor_volume import solve
from scripts.pcbgen.build_current_j_power_feed import derive as derive_current_feed
from scripts.pcbgen.current_j_rail_entry import verify_unchanged as verify_rail_unchanged


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_profile_receipt(receipt, expected_path):
    """Verify the solver's binding; never rebind changed bytes to its matrix."""
    profile = receipt.get('profile_receipt', {})
    if profile.get('path') != str(expected_path.resolve()):
        raise ValueError('solver profile receipt has an unexpected path')
    raw=expected_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != profile.get('sha256'):
        raise ValueError('solver profile changed after publication')
    return raw


def run(native_path, power_path, output, net, coarse, fine, refinement, origin, jack_receipt=None):
    native_path=Path(native_path);power_path=Path(power_path);output=Path(output)
    if jack_receipt is None:raise ValueError('current J rail requires its reviewed native v6 receipt')
    jack_receipt=Path(jack_receipt)
    role_path=output.with_name(output.stem+'-selected-native.json')
    raw_output=output.with_name(output.stem+'-raw.json')
    raw_profile=raw_output.with_name(raw_output.stem+'-profiles.json')
    profile_path=output.with_name(output.stem+'-profiles.json')
    ledger_path=output.with_name(output.stem+'-rail-ledger.json')
    screen_path=output.with_name(output.stem+'-screen.json')
    artifacts=(output,role_path,raw_output,raw_profile,profile_path,ledger_path,screen_path,
               raw_output.with_name(raw_output.stem+'-current-mesh.pickle'),
               raw_output.with_name(raw_output.stem+'-potential-mesh.pickle'))
    if any(path.exists() or path.is_symlink() for path in artifacts):
        raise ValueError('rail result, selected role or partial raw artifact occupies this stem; use a fresh stem')
    paths=[native_path,power_path,jack_receipt,Path(__file__),
           Path('scripts/pcbgen/selected_conductor_export.py'),
           Path('scripts/pcbgen/build_current_j_power_feed.py'),
           Path('scripts/pcbgen/current_j_rail_entry.py'),
           Path('scripts/pcbgen/jack_white_current_binding.py'),
           Path('scripts/pcbgen/power_load_ledger.py'),
           Path('scripts/pcbgen/source_contact_inventory.py'),
           Path('scripts/pcbgen/screen_rail_transfers.py'),
           Path('design/reports/io-partition.json'),Path('design/power/rail-ledger.json'),
           Path('design/partition/partition-input.json'),Path('design/partition/partition.json')]
    hashes={str(p.resolve()):digest(p) for p in paths}
    native_bytes=native_path.read_bytes();power_bytes=power_path.read_bytes()
    if hashes[str(native_path.resolve())]!=hashlib.sha256(native_bytes).hexdigest() or hashes[str(power_path.resolve())]!=hashlib.sha256(power_bytes).hexdigest():
        raise ValueError('current J rail native/feed source changed after entry')
    native=json.loads(native_bytes);power=json.loads(power_bytes)
    if derive_current_feed(native_path,jack_receipt)!=power:
        raise ValueError('current J rail feed mapping differs from exact native derivation')
    source_paths=(Path('design/reports/io-partition.json'),Path('design/power/rail-ledger.json'),
                  Path('design/partition/partition-input.json'),Path('design/partition/partition.json'))
    source_bytes={str(path):path.read_bytes() for path in source_paths}
    if any(hashes[str(path.resolve())]!=hashlib.sha256(source_bytes[str(path)]).hexdigest() for path in source_paths):
        raise ValueError('current J rail mapping source changed before parse')
    ledger=mapping(native,power,source_bytes)
    ledger['native_export_sha256']=hashes[str(native_path.resolve())]
    ledger['power_feed_receipt_sha256']=hashes[str(power_path.resolve())]
    for name,want in ledger['source_sha256'].items():
        key=str(Path(name).resolve())
        if key in hashes and hashes[key]!=want:raise ValueError('current J rail source ledger changed after parse: '+key)
        hashes[key]=want
    selected=select(native,net,hashes[str(native_path.resolve())])
    role_mapping=selected['conductor_role_mapping']
    with role_path.open('x') as handle:handle.write(json.dumps(selected,separators=(',',':'))+'\n')
    del native,selected
    solve(role_path,raw_output,coarse,fine,refinement,0,True,True,origin,True,
          rail_original=native_path,rail_receipt=jack_receipt,rail_net=net)
    raw_bytes=raw_output.read_bytes();raw_sha=hashlib.sha256(raw_bytes).hexdigest()
    raw_receipt=json.loads(raw_bytes)
    prerequisite=raw_receipt.get('rail_native_prerequisite')
    if prerequisite is None or prerequisite['physical_net']!=net:
        raise ValueError('raw rail model lacks its exact current J prerequisite')
    for name,want in prerequisite['dependency_sha256'].items():
        if name in hashes and hashes[name]!=want:raise ValueError('conflicting selected J rail source dependency: '+name)
        hashes[name]=want
    verify_rail_unchanged(prerequisite)
    profile_bytes=verify_profile_receipt(raw_receipt,raw_profile)
    receipt=dict(raw_receipt)
    receipt['conductor_role_mapping']=role_mapping
    receipt['raw_solver_receipt_sha256']=raw_sha
    receipt['rail_wrapper_source_sha256']=hashes
    receipt['profile_receipt']={'path':str(profile_path.resolve()),'sha256':raw_receipt['profile_receipt']['sha256']}
    receipt['physical_net']=net
    receipt['status']='NOT ACCEPTED: nominal finite-profile rail diagnostic only'
    receipt['all_native_rail_pad_component_mapping']=receipt.pop('all_native_AGND_pad_component_mapping')
    receipt['unused_native_rail_copper_uuids']=receipt.pop('unused_native_AGND_copper_uuids')
    receipt['common_private_K_current_allocation']='NOT RUN: combined common rail and positive K allocation remain required'
    result=screen(receipt,ledger,net)
    if any(digest(p)!=want for p,want in hashes.items()):
        raise ValueError('current J rail source or wrapper changed before final publication')
    if digest(raw_output)!=raw_sha:
        raise ValueError('raw selected J rail result changed before publication')
    if raw_profile.read_bytes()!=profile_bytes:
        raise ValueError('raw selected J rail profile changed before publication')
    with profile_path.open('xb') as handle:handle.write(profile_bytes)
    with ledger_path.open('x') as handle:handle.write(json.dumps(ledger,indent=2)+'\n')
    with output.open('x') as handle:handle.write(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    bind_artifact_paths(result,output,ledger_path)
    with screen_path.open('x') as handle:handle.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'physical_net':net,'worst':result['worst']},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('native', type=Path)
    parser.add_argument('power_receipt', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--net', required=True, choices=('+12V', '-12V', '+5V'))
    parser.add_argument('--coarse-mm', type=float, default=2.)
    parser.add_argument('--fine-mm', type=float, default=.125)
    parser.add_argument('--refinement', type=int, default=2)
    parser.add_argument('--origin-x', type=float, default=0.)
    parser.add_argument('--origin-y', type=float, default=0.)
    parser.add_argument('--jack-receipt',type=Path,required=True)
    args = parser.parse_args()
    run(args.native, args.power_receipt, args.output, args.net,
        args.coarse_mm, args.fine_mm, args.refinement, (args.origin_x, args.origin_y),args.jack_receipt)
