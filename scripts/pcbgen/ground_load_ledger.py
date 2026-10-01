"""Map every native ground pad to its exact source role and current-basis scope.

Fitted geometry coverage is not a per-component current guarantee. Normal-state
transfer bounds may use an aggregate absolute-current envelope over the possible
return basis, while terminals remain observations and external boundaries.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.source_contact_inventory import expected_contacts, reconcile_native


def mapping(native):
    partition_path=Path('design/reports/io-partition.json')
    ledger_path=Path('design/power/rail-ledger.json')
    assignment_path=Path('design/partition/partition.json')
    partition=json.loads(partition_path.read_text())
    ledger=json.loads(ledger_path.read_text())
    packages={p['ref']:p for p in partition['physical_packages'] if not p['dnp']}
    expected=expected_contacts(native['board_id'],json.loads(assignment_path.read_text()),partition,('AGND',))
    reconcile_native(native,expected,set(packages),('AGND',))
    supplies={p['ref']:p for p in ledger['physical_ic_packages']}
    ground=next(n for n in partition['allowed_crossings'] if n['net']=='AGND')
    members=collections.defaultdict(list)
    for member in ground['members']:members[(member['ref'],member['pin'])].append(member)
    main=set(native['main_rail_members']['AGND']);rows=[]
    for item in native['items']:
        if item['net']!='AGND' or 'ref' not in item:continue
        if item['uuid'] not in main:raise ValueError('fitted AGND pad is outside the native main component')
        ref,pad=item['ref'],item['pad'];package=packages.get(ref);source=members[(ref,pad)]
        if ref.startswith('J900'):
            category='GH_return_observation';basis=False
        elif ref.startswith('TP990'):
            category='main_wire_boundary';basis=False
        else:
            if package is None or not source:
                raise ValueError('native ground pad lacks exact fitted source membership: '+ref+':'+pad)
            basis=True
            if supplies.get(ref,{}).get('supply_pins',{}).get(pad)=='AGND':
                category='IC_supply_return'
            elif package.get('decouples_ref'):
                category='IC_bypass_return'
            elif package['symbol']=='WQP518MA':
                category='external_patch_return'
            elif all(m['type']=='input' for m in source):
                category='signal_input_or_unused_channel'
            else:
                category='passive_or_other_return'
        rows.append({'ref':ref,'pad':pad,'uuid':item['uuid'],'category':category,
            'possible_normal_return_basis':basis,'source_members':source,
            'instance':package['instance'] if package else None,
            'symbol':package['symbol'] if package else None,
            'decouples_ref':package.get('decouples_ref') if package else None})
    identities=[(r['ref'],r['pad']) for r in rows]
    if len(set(identities))!=len(identities):raise ValueError('native ground pad identity is duplicated')
    return {'status':'SOURCE MAPPING ONLY; finite physical contact and electrical bounds remain unaccepted',
        'board_sha256':native['board_sha256'],'board_id':native['board_id'],
        'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (partition_path,ledger_path,assignment_path)},
        'independent_expected_source_contact_count':len(expected),
        'category_counts':dict(collections.Counter(r['category'] for r in rows)),
        'pads':rows,
        'normal_transfer_envelope':{
            'aggregate_absolute_current_A':4.6,
            'interpretation':'One aggregate sum of absolute currents over the possible-return basis, not 4.6 A at every pad simultaneously.',
            'terminal_scope':'GH terminals are voltage/current observations; main-wire terminals are alternative source/sink boundaries. Neither is an arbitrary fitted-load injection.',
            'unused_and_passive_scope':'Including a passive or unused source pad in the basis conservatively covers a possible return location; it does not assert powered load or substitute a planning current for a guaranteed maximum.',
            'conditions':'Normal source envelope only, with no additional external-source circulation or reactive discharge outside the aggregate bound. Startup, patch/fault and physical hot qualification remain their explicit open source obligations.',
            'individual_package_maximum':'Not established by this mapping; quiescent worksheet allowances are not used as guaranteed bounds.'}}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('native',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();report=mapping(json.loads(args.native.read_text()))
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['board_id'],len(report['pads']),report['category_counts'])
