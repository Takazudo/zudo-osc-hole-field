"""Exact fitted rail-contact inventory and source-envelope proof scope.

This mapping does not turn planning or quiescent allowances into maxima. It
keeps native continuity distinct from paid access, normal load and transient
qualification, and records every fitted rail contact before resistance work.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.source_contact_inventory import expected_contacts, reconcile_native

RAILS=('+12V','-12V','+5V')


def mapping(native,power_receipt,source_bytes=None):
    paths=[Path('design/reports/io-partition.json'),Path('design/power/rail-ledger.json'),
           Path('design/partition/partition-input.json'),Path('design/partition/partition.json')]
    retained={str(p):(p.read_bytes() if source_bytes is None else source_bytes[str(p)]) for p in paths}
    partition,ledger,source,assignment=[json.loads(retained[str(p)]) for p in paths]
    if native['board_sha256']!=power_receipt['board_sha256']:
        raise ValueError('native geometry and rail-feed receipt have different board identities')
    packages={p['ref']:p for p in partition['physical_packages'] if not p['dnp']}
    expected=expected_contacts(native['board_id'],assignment,partition,RAILS)
    actual=reconcile_native(native,expected,set(packages),RAILS)
    supplies={p['ref']:p for p in ledger['physical_ic_packages']}
    members={net:collections.defaultdict(list) for net in RAILS}
    for crossing in partition['allowed_crossings']:
        if crossing['net'] in RAILS:
            for m in crossing['members']:members[crossing['net']][m['ref'],m['pin']].append(m)
    feeds={(r['ref'],r['pad'],r['net']):r for r in power_receipt['fitted_rail_pad_feeds']}
    if len(feeds)!=len(power_receipt['fitted_rail_pad_feeds']):
        raise ValueError('duplicate native rail feed identity')
    if set(feeds)!=set(expected):
        raise ValueError('rail feed receipt does not cover exact board source contacts')
    rows=[]
    for item in native['items']:
        if item['net'] not in RAILS or item.get('ref') not in packages:continue
        ref,pad,net=item['ref'],item['pad'],item['net'];package=packages[ref]
        identity=(ref,pad,net)
        if identity not in feeds or not members[net][ref,pad]:
            raise ValueError('fitted rail pad lacks exact native/source membership: '+str(identity))
        if feeds[identity]['uuid']!=actual[identity]['uuid']:
            raise ValueError('rail feed UUID differs from exact native contact UUID')
        connected=item['uuid'] in native['main_rail_members'][net]
        if connected!=feeds[identity]['connected_to_load_land']:
            raise ValueError('rail feed connectivity disagrees with native main membership')
        if supplies.get(ref,{}).get('supply_pins',{}).get(pad)==net:
            role='IC_supply'
        elif package.get('decouples_ref'):
            role='IC_bypass'
        elif ref.startswith('R'):
            role='passive_resistor'
        else:role='other_fitted_rail_contact'
        rows.append({'ref':ref,'pad':pad,'net':net,'uuid':item['uuid'],'role':role,
            'source_instance':package['instance'],'source_symbol':package['symbol'],
            'decouples_ref':package.get('decouples_ref'),
            'source_members':members[net][ref,pad],
            'native_connected_to_load_land':connected,
            'individual_current_maximum_A':None,
            'individual_current_status':'NOT ESTABLISHED; no planning allowance promoted to a maximum'})
    identities={(r['ref'],r['pad'],r['net']) for r in rows}
    if len(identities)!=len(rows) or identities!=set(feeds):
        raise ValueError('native rail inventory has missing or duplicate fitted identities')
    if any(p.read_bytes()!=retained[str(p)] for p in paths):
        raise ValueError('rail source changed during exact fitted contact mapping')
    return {'status':'SOURCE/NATIVE MAPPING; resistance and physical current qualification remain open',
        'board_id':native['board_id'],'board_sha256':native['board_sha256'],
        'source_sha256':{str(p):hashlib.sha256(retained[str(p)]).hexdigest() for p in paths},
        'fitted_rail_pad_count':len(rows),
        'independent_expected_source_contact_count':len(expected),
        'source_completeness':'Exact fitted board assignment plus source allowed-crossing pin/net identities, independently reconciled with native geometry, unique UUIDs and feed identities.',
        'net_counts':dict(collections.Counter(r['net'] for r in rows)),
        'role_counts':dict(collections.Counter(r['role'] for r in rows)),
        'pads':rows,
        'source_envelope_A':source['load_distribution']['rail_max_A'],
        'required_gates':{'combined_J_K_common_rail_ohm':.001,'hot_distribution_V':.020,
            'access_accounting':'Every local pad, neck, track, via and main-land transfer is included in the conductor. Any separately allocated access drop requires supported per-load currents and aggregate consistency.',
            'reactive_scope':'Input source-current ceilings alone do not bound local capacitor discharge or circulating currents. Their admitted normal waveform/transient class remains explicit #57/#65 work.',
            'normal_scope':'A whole-source concentration screen is conservative only within its stated normal current class; it is not a component maximum or a fault guarantee.'}}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('native',type=Path);p.add_argument('power',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();report=mapping(json.loads(a.native.read_text()),json.loads(a.power.read_text()))
    report['native_export_sha256']=hashlib.sha256(a.native.read_bytes()).hexdigest()
    report['power_feed_receipt_sha256']=hashlib.sha256(a.power.read_bytes()).hexdigest()
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['board_id'],report['fitted_rail_pad_count'],report['net_counts'],report['role_counts'])
