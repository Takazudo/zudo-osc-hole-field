"""Independent all-five live-source crossing identity and rule audit; no CAD runs."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from design.spec.instrument import specification
from scripts.schgen.core import designator
from design.spec.cells._builder import load_symbol

OUT=ROOT/'design/architecture-278/implementation'
OWNERS={'jack':'front-jack','control':'front-control','selector':'octave-selector','core':'rear-core'}
INSTANCES=[f'O{i}' for i in range(1,6)]
POWER={'+12V','-12V','+5V','AGND'}
SHARED={'OSC_REF5','OSC_REFN5','OSC_GATE_REF'}|{f'OSC_OCT{i}' for i in range(6)}

def need(condition,message):
    if not condition:raise ValueError(message)

def context():
    families,instances=specification();families={f.name:f for f in families};instances={i.name:i for i in instances}
    rows=[];bykey={};bypin={}
    for name in INSTANCES+['OCTAVE_REF']:
        inst=instances[name];family=families[inst.family]
        for p in family.parts:
            attrs={k:v.replace('${SHEETNAME}',name) for k,v in p.attributes.items()}
            pins={pin:(net if net is None or net in family.global_nets else '/'+name+'/'+net) for pin,net in p.pins.items()}
            ref=designator(p,inst)
            types={pin.number:pin.electrical for pin in load_symbol(p.symbol.split(':')[-1]).units[p.unit]} if p.symbol.startswith('zudo-osc-hole-field:') else {}
            row={'instance':name,'ref':ref,'unit':p.unit,'key':p.key,'pins':pins,'attributes':attrs,
                 'owner':'shared-reference' if name=='OCTAVE_REF' else OWNERS[attrs.get('BoardRegion','core')],
                 'footprint':p.footprint,'symbol':p.symbol,'pin_types':types}
            rows.append(row);bykey[name,p.key,p.unit]=row
            for pin,net in pins.items():
                need((ref,pin) not in bypin,'duplicate live pin')
                bypin[ref,pin]=(row,net)
    io=json.loads((ROOT/'design/reports/io-partition.json').read_text())
    retained={(p['ref'],p['unit']):p for p in io['package_units']}
    for row in rows:
        if not row['footprint']:continue
        original=retained[row['ref'],row['unit']]
        need(row['pins']==original['pins'],'live/retained pin mismatch '+row['ref'])
        need(row['attributes'].get('BoardRegion','core')==original['region'].replace('selector_front','selector').replace('selector_rear','selector'),'live/retained region mismatch')
    return {'rows':rows,'bykey':bykey,'bypin':bypin,'io':io,
        'crossings':{n['net']:n for n in io['allowed_crossings']},
        'locked':{p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}}

def map_endpoint(template,instance,ctx):
    ref,pin=template.split(':');row,_=ctx['bypin'][ref,pin]
    need(row['instance'] in ('O1','OCTAVE_REF'),'not template/shared endpoint')
    target=row if row['instance']=='OCTAVE_REF' else ctx['bykey'][instance,row['key'],row['unit']]
    return {'ref':target['ref'],'pin':pin,'unit':target['unit'],'net':target['pins'][pin],
            'owner':target['owner'],'source_instance':target['instance'],'panel_uid':target['attributes'].get('PanelUid','')}

def validate_row(row,ctx):
    instance=row['instance'];need(instance in INSTANCES,'wrong instance')
    need(row['length_limit_mm']==300 and row['capacitance_limit_pF']==1000,'relaxed crossing limit')
    need(math.isclose(sum(row['segments_mm'].values()),row['total_mm'],rel_tol=0,abs_tol=1e-9),'decomposition mismatch')
    expected_net=row['template_net'].replace('/O1/','/'+instance+'/')
    need(row['actual_net']==expected_net,'wrong actual net')
    for key,tkey in [('front','template_front_endpoint'),('other','template_other_endpoint')]:
        expected=map_endpoint(row[tkey],instance,ctx)
        need(row[key]==expected,'wrong instance/ref/pin/net endpoint '+key)
        need(expected['net']==row['actual_net'],'endpoint net mismatch')
    uid=row['actual_panel_uid']
    if row['template_panel_uid']:
        need(uid==row['template_panel_uid'].replace('O1',instance),'wrong panel UID')
        locked=ctx['locked'][uid];need(locked['block']==instance,'locked instance mismatch')
        panel=[p for p in ctx['rows'] if p['instance']==instance and p['attributes'].get('PanelUid')==uid]
        need(len(panel)==1 and panel[0]['ref']==locked['ref'],'locked/live panel reference mismatch')
        frontpart=ctx['bypin'][row['front']['ref'],row['front']['pin']][0]
        if uid.startswith('C:'):
            need(frontpart['attributes'].get('PanelUid')==uid,'control link assigned to wrong UID')
        else:
            logical=frontpart['attributes'].get('LogicalCellKey',frontpart['key'])
            match=re.search(r'_J_O1_1V_([^_]+)__',logical)
            need(match is not None and uid=='J:'+instance+'.'+match.group(1),'jack logical cell/UID mismatch')
    else:need(not uid and row['actual_net'] in SHARED,'unexpected absent UID')
    net=row['actual_net'];cross=ctx['crossings'].get(net)
    if cross:
        ids={(p['ref'],p['pin']) for p in cross['direction'].get('source_nodes',[])}
        need(bool(ids),'no canonical source nodes')
    else:
        need(net in SHARED,'missing crossing rule for nonshared net')
        ids={(p['ref'],pin) for p in ctx['rows'] for pin,n in p['pins'].items() if n==net and p['pin_types'].get(pin)=='output'}
        need(len(ids)==1,'ambiguous shared source')
    actual={(row[k]['ref'],row[k]['pin']) for k in ('front','other')}
    need(bool(ids&actual),'crossing omits canonical driver')
    return sorted(':'.join(x) for x in ids)

def validate_collection(rows,links,ctx):
    for row in rows:validate_row(row,ctx)
    unique=[(r['alternative'],r['instance'],r.get('link'),r.get('link_pin'),r['actual_net'],r['front']['ref'],r['front']['pin'],r['other']['ref'],r['other']['pin']) for r in rows]
    need(len(unique)==len(set(unique)),'duplicate audited endpoint path')
    for alternative in {r['alternative'] for r in rows}:
        selected=[r for r in rows if r['alternative']==alternative]
        instances={r['instance'] for r in selected}
        need(instances==(set(INSTANCES) if alternative=='five_card_two_rows' else {'O1','O2'}),'missing instance')
        expected={(i,l['id'],pin,net.replace('/O1/','/'+i+'/')) for i in instances for l in links.values() for pin,net in l['pins'].items() if net!='AGND'}
        actual={(r['instance'],r['link'],r['link_pin'],r['actual_net']) for r in selected if 'link' in r}
        need(actual==expected,'missing crossing link branch')
        for net in SHARED:need({r['instance'] for r in selected if r['actual_net']==net}==instances,'missing shared receiver instance')
        # Reconstruct endpoint combinations directly from every live unit/pin,
        # not from the assembly output or its O1-only endpoint selection.
        expected_pairs=set()
        for instance in instances:
            def endpoints(net,owners):
                return [(p['ref'],pin,p) for p in ctx['rows'] if p['owner'] in owners
                        and p['instance'] in (instance,'OCTAVE_REF') for pin,n in p['pins'].items() if n==net]
            for link in links.values():
                uid=link['uid'].replace('O1',instance)
                for pin,template_net in link['pins'].items():
                    if template_net=='AGND':continue
                    net=template_net.replace('/O1/','/'+instance+'/')
                    sources={(d['ref'],d['pin']) for d in ctx['crossings'][net]['direction']['source_nodes']}
                    front=endpoints(net,{'front-jack','front-control','octave-selector'})
                    if uid.startswith('C:'):front=[e for e in front if e[2]['attributes'].get('PanelUid')==uid]
                    front_sources=[e for e in front if e[:2] in sources]
                    if front_sources:front=front_sources
                    other=endpoints(net,{'shared-reference'} if net.startswith('OSC_OCT') else {'rear-core'})
                    other_sources=[e for e in other if e[:2] in sources]
                    if other_sources:other=other_sources
                    need(front and other,'empty independently reconstructed branch')
                    for f in front:
                        for o in other:expected_pairs.add((instance,link['id'],pin,net,f[0],f[1],o[0],o[1]))
            for net in ('OSC_REF5','OSC_REFN5','OSC_GATE_REF'):
                sources=[e for e in endpoints(net,{'shared-reference'}) if e[2]['pin_types'].get(e[1])=='output']
                need(len(sources)==1,'shared canonical source cardinality')
                for o in endpoints(net,{'rear-core'}):expected_pairs.add((instance,None,None,net,sources[0][0],sources[0][1],o[0],o[1]))
        actual_pairs={(r['instance'],r.get('link'),r.get('link_pin'),r['actual_net'],r['front']['ref'],r['front']['pin'],r['other']['ref'],r['other']['pin']) for r in selected}
        need(actual_pairs==expected_pairs,'missing or extra live-source endpoint pair')

def validate_return(row,ctx,links,pinmap):
    instance=row['instance'];need(instance in INSTANCES,'wrong return instance')
    owners=row['ground_endpoint_group'];owners=[owners] if isinstance(owners,str) else owners
    expected={(p['ref'],pin) for p in ctx['rows'] if p['instance']==instance and p['owner'] in owners and p['footprint']
              for pin,net in p['pins'].items() if net=='AGND'}
    mapped=[map_endpoint(e,instance,ctx) for e in row['endpoint_ids']]
    need(all(e['net']=='AGND' for e in mapped),'signal masquerading as return')
    need(Counter((e['ref'],e['pin']) for e in mapped)==Counter(expected),'return endpoint omission/duplication')
    if 'link' in row:
        need(links[row['link']]['pins'][row['contact']]=='AGND','wrong return contact')
    else:need(row['from'] in {'DIN:b'+p[1:] for p in pinmap.values()},'unpaired DIN return')
    need(row['resistance_mOhm'] is None,'unsubstantiated return impedance')
    return sorted(e['ref']+':'+e['pin'] for e in mapped)

def build():
    ctx=context();assembly=json.loads((OUT/'assembly-report.json').read_text())
    baseline=json.loads((OUT/'candidate-report.json').read_text());links={l['id']:l for l in baseline['front_links']}
    contract=json.loads((ROOT/'design/architecture-278/interface-contract.json').read_text())
    standard=json.loads((ROOT/'design/standard/electrical-standard.json').read_text())
    rule=standard['remote_controls'];need(rule['max_harness_length_m']==.3 and rule['max_harness_capacitance_F']==1e-9,'rule changed')
    mapping=[]
    for p in ctx['rows']:
        if p['instance']!='O1':continue
        targets={i:ctx['bykey'][i,p['key'],p['unit']] for i in INSTANCES}
        mapping.append({'key':p['key'],'unit':p['unit'],'refs':{i:t['ref'] for i,t in targets.items()},'pins':{i:t['pins'] for i,t in targets.items()}})
    legacy={(p['key'],p['unit']):p for p in contract['instance_mapping']}
    for row in mapping:
        old=legacy[row['key'],row['unit']]
        for i in old['refs']:
            need(old['refs'][i]==row['refs'][i] and old['pins'][i]==row['pins'][i],'retained mapping mismatch')
    locked_checks=[]
    for instance,placed in assembly['front_instances'].items():
        for p in placed:
            if not p.get('uid'):continue
            locked=ctx['locked'][p['uid']]
            live=next(r for r in ctx['rows'] if r['instance']==instance and r['attributes'].get('PanelUid')==p['uid'])
            need(locked['ref']==live['ref'],'locked reference drift')
            need(p['origin_mm']==[locked['x_mm'],locked['y_mm']] and p['quarter_turn']*90==locked['rot_deg'],'locked pose drift')
            locked_checks.append({'instance':instance,'template_ref':p['ref'],'actual_ref':live['ref'],'uid':p['uid'],'xy_mm':p['origin_mm'],'rotation_deg':locked['rot_deg']})
    audited=[]
    for alternative,alt in assembly['alternatives'].items():
        for index,p in enumerate(alt['paths']):
            need(p['net'] not in POWER,'power included in signal300mm audit')
            uid=links[p['link']]['uid'] if 'link' in p else ''
            row={'alternative':alternative,'row':index,'instance':p['instance'],'template_net':p['net'],
                 **{k:p[k] for k in ('link','link_pin') if k in p},
                 'actual_net':p['net'].replace('/O1/','/'+p['instance']+'/'),'template_front_endpoint':p['front_endpoint'],
                 'template_other_endpoint':p['other_endpoint'],'template_panel_uid':uid,'actual_panel_uid':uid.replace('O1',p['instance']),
                 'front':map_endpoint(p['front_endpoint'],p['instance'],ctx),'other':map_endpoint(p['other_endpoint'],p['instance'],ctx),
                 'segments_mm':p['segments'],'total_mm':p['total_mm'],'length_limit_mm':300,'capacitance_limit_pF':1000,
                 'capacitance_pF':p['capacitance_pF'],'capacitance_status':'OPEN: no extracted unique-segment/probe/connector capacitance',
                 'limit_authority':'OSC-ES-1 remote_controls; retained allowed_crossings for actual net; architecture278 complete-path rule',
                 'physical_qualification':'NOT RUN'}
            row['canonical_source_nodes']=validate_row(row,ctx)
            cross=ctx['crossings'].get(row['actual_net'])
            if cross:
                need(cross['max_harness_length_m']==.3 and cross['capacitance_F']['maximum']==1e-9,'per-net limit disagreement')
                row['canonical_crossing_kind']=cross['kind']
            else:row['canonical_crossing_kind']='shared-reference split; OSC-ES-1 buffered-reference rule'
            need(math.isclose(sum(row['segments_mm'].values()),row['total_mm'],abs_tol=1e-9),'decomposition mismatch')
            row['within_length_allocation']=row['total_mm']<=300
            audited.append(row)
    validate_collection(audited,links,ctx)
    return_checks=[]
    for alternative,alt in assembly['alternatives'].items():
        for index,row in enumerate(alt['returns']):
            actual=validate_return(row,ctx,links,alt['DIN_signal_labels'])
            return_checks.append({'alternative':alternative,'row':index,'instance':row['instance'],
                'link':row.get('link'),'contact':row.get('contact',row.get('from')),'actual_AGND_endpoints':actual,
                'status':'identity/complete owner-group PASS; plane connectivity/current sharing/impedance OPEN'})
    five=[r for r in audited if r['alternative']=='five_card_two_rows']
    need(len(five)==225 and all(any(r['instance']==i for r in five) for i in INSTANCES),'five-instance coverage')
    aggregates=[]
    for net in sorted(SHARED):
        rows=[r for r in five if r['actual_net']==net]
        need({r['instance'] for r in rows}==set(INSTANCES),'shared fanout missing instance')
        aggregates.append({'net':net,'instances':INSTANCES,'endpoint_rows':len(rows),'direct_capacitance_limit_pF':1000,
            'extracted_unique_segment_total_pF':None,'status':'OPEN; sum union of shared source/common and five branch conductors, pins, traces and probes; do not multiply common segment per endpoint',
            'receiver_dynamics':'OCT0..5: selected1kohm/100nF receivers are separate dynamic loads, not absorbed in direct1nF budget' if net.startswith('OSC_OCT') else 'five-instance buffered reference loads/stability/ground error remain OPEN'})
    sources=set(contract['source_sha256'])|{'design/architecture-278/interface-contract.json','design/standard/electrical-standard.json','design/reports/io-partition.json','design/grid/placements.lock.json','design/architecture-278/implementation/assembly-report.json','design/architecture-278/implementation/candidate-report.json',str(Path(__file__).relative_to(ROOT)),str(Path(__file__).with_name('test_stage3_crossing_audit.py').relative_to(ROOT))}
    return {'status':'ALL-FIVE LIVE SOURCE IDENTITY AUDIT PASS; electrical/native/physical acceptance OPEN',
        'live_unit_count':len(ctx['rows']),'five_oscillator_unit_count':sum(p['instance']!='OCTAVE_REF' for p in ctx['rows']),
        'source_mapping_all_five':mapping,'retained_mapping_prior_instances':['O1','O2','O5'],'newly_explicit_mapping_instances':['O3','O4'],
        'live_to_retained_physical_unit_pin_parity':'PASS allfive+shared; nonphysical flags explicitly excluded from retained physical rows',
        'locked_panel_checks':locked_checks,'audited_paths':audited,'audited_return_groups':return_checks,'five_instance_endpoint_path_count':len(five),
        'controlling_paths':sorted(five,key=lambda r:r['total_mm'],reverse=True)[:10],
        'shared_aggregate_capacitance':aggregates,
        'power_return_disposition':'Excluded from blanket signal300mm/1nF acceptance. Full source/common/branch/load/return graph and <=0.5mOhm return,<=1mOhm rail,<=20mVhot,<=0.20Vcomplete path,<=0.5A/GHcontact remain OPEN; no current-sharing or capacitance qualification.',
        'findings':['Legacy instance map omittedO3/O4; this audit explicitly maps allfive from live canonical specification and verifies retained physical source parity.',
            'Assembly refs/nets remain O1template labels. Exact actual identities are materialized here; template projection alone is not native allfive netlist acceptance.',
            'Every modeled crossing keeps300mm/1nF requirements including PWM, rawwipers and nine shared references; no exemption or relaxed limit introduced.',
            'All path capacitances remain null; inventory/length arithmetic cannot establish aggregate loading or complete electrical acceptance.'],
        'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(sources)}}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    r=build();data=json.dumps(r,indent=2,sort_keys=True)+'\n';p=OUT/'stage3-crossing-audit.json'
    if args.check:need(p.read_text()==data,'stale crossing audit')
    else:p.write_text(data)
    print(f"PASS allfive source audit; {len(r['audited_paths'])} alternative endpoint rows; {len(r['locked_panel_checks'])} locked UIDs; capacitance/native/physical OPEN")
