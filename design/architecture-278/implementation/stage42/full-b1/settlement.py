"""Collect three equal native memberships and a separately loaded fresh copy."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json

CAPS={'silk_overlap','silk_over_copper'}


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def warnings(report):
    return Counter((r['type'],tuple(sorted(x['uuid'] for x in r['items']))) for r in report['violations'] if r['severity']=='warning' and r['type'] not in CAPS)


def uncapped(report):
    counts=Counter(r['type'] for r in report['violations'] if r['severity']=='warning')
    return all(n < (499 if kind in ('clearance','unconnected_items') else 199) for kind,n in counts.items() if kind not in CAPS)


def collect(baseline,clean,fresh,output):
    old=read(baseline/'connectivity-complete.json');old_drc=read(baseline/'drc-first.json')
    if sha(baseline/'osc-jack-left.kicad_pcb')!=old['board_sha256']:raise ValueError('baseline snapshot binding')
    receipt=read(clean/'prepare-receipt.json');retired={r['uuid'] for field in ('retired_private_copper','retired_stage42_supply_copper') for r in receipt[field]}
    receipt_hash=sha(clean/'prepare-receipt.json')
    if receipt['canonical_sha256']!=old['board_sha256'] or sha(fresh/'prepare-receipt.json')!=receipt_hash:
        raise ValueError('receipt baseline/fresh binding')
    first=read(clean/'connectivity-complete-pass1.json');rows=[];bindings={}
    files=[(clean,'1','drc-signals-pass1.json','connectivity-complete-pass1.json','connectivity-comparison-pass1.json','power-connections-pass1.json','identity-audit-pass1.json')]
    files += [(clean,str(n),f'drc-pass{n}.json',f'connectivity-pass{n}.json',f'comparison-pass{n}.json',f'power-pass{n}.json',f'identity-pass{n}.json') for n in (2,3)]
    files += [(fresh,'fresh','drc-passfresh.json','connectivity-passfresh.json','comparison-passfresh.json','power-passfresh.json','identity-passfresh.json')]
    candidate_hash=sha(clean/'osc-jack-left.kicad_pcb')
    for path in (baseline/'osc-jack-left.kicad_pcb',baseline/'connectivity-complete.json',baseline/'drc-first.json',clean/'prepare-receipt.json',fresh/'prepare-receipt.json'):
        bindings[str(path)]=sha(path)
    if sha(fresh/'osc-jack-left.kicad_pcb')!=candidate_hash:raise ValueError('fresh board differs')
    for folder,label,*names in files:
        drc,snapshot,comparison,power,audit=[read(folder/n) for n in names]
        for name in names:bindings[str(folder/name)]=sha(folder/name)
        checks={
            'exact_native_version':drc['kicad_version']==snapshot['version']==power['version']=='10.0.6',
            'no_reported_error_or_parity':not drc['schematic_parity'] and not any(v['severity']=='error' for v in drc['violations']),
            'complete_membership_stable':snapshot['groups']==first['groups'] and snapshot['objects']==first['objects'],
            'exact_board_binding':snapshot['board_sha256']==power['board_sha256']==audit['raw_sha256']==comparison['candidate_sha256']==candidate_hash,
            'identity_gate':audit['accepted_identity_only'],
            'audit_receipt_baseline_binding':audit['receipt_sha256']==receipt_hash and audit['canonical_sha256']==old['board_sha256'],
            'connectivity_gate':comparison['accepted_connectivity_only'] and comparison['baseline_sha256']==old['board_sha256'],
            'exact_disturbed_target_set':set(comparison['target_net_closed'])==set(receipt['private_net_owners']) and all(comparison['target_net_closed'].values()),
            'baseline_open_count':snapshot['native_open_edges']==old['native_open_edges']==len(drc['unconnected_items']),
            'power_gate':power['accepted_native_connections_only'] and len(power['paths'])==18,
            'no_added_uncapped_warnings':not (warnings(drc)-warnings(old_drc)),
            'no_additional_capped_warning_category':uncapped(drc) and uncapped(old_drc),
            'removed_uncapped_warnings_only_retired_objects':all(set(k[1])<=retired for k in warnings(old_drc)-warnings(drc)),
        }
        if not all(checks.values()):raise ValueError('settlement failure '+label+': '+str(checks))
        rows.append({'pass':label,'checks':checks,'open_edges':snapshot['native_open_edges'],
                     'reported_warning_counts':dict(Counter(v['type'] for v in drc['violations'] if v['severity']=='warning')),
                     'removed_uncapped_warnings':[{'type':k[0],'uuids':k[1],'count':v} for k,v in (warnings(old_drc)-warnings(drc)).items()]})
    result={'accepted_bounded_full_b1_native_study':True,'candidate_sha256':candidate_hash,'baseline_sha256':old['board_sha256'],
            'baseline_objects':len(old['objects']),'candidate_objects':len(first['objects']),
            'private_retirements':len(receipt['retired_private_copper']),'separate_local_supply_retirements':len(receipt['retired_stage42_supply_copper']),
            'added_objects':audit['new_objects'],'disturbed_nets':sorted(receipt['private_net_owners']),'passes':rows,'evidence_sha256':bindings,
            'limits':'117 pre-existing opens remain. KiCad 10.0.6 caps silk_overlap and silk_over_copper at199; sample identities vary, so exhaustive silkscreen warning nonregression is UNRESOLVED. No full-board DRC pass, architecture adoption, manufacturing or physical/electrical performance qualification.'}
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'accepted_bounded_full_b1_native_study':True,'passes':len(rows),'candidate_sha256':candidate_hash}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('baseline','clean','fresh','output'):p.add_argument(n,type=Path)
    a=p.parse_args();collect(a.baseline,a.clean,a.fresh,a.output)
