"""Read-only classification of retained observations, with explicit name decoding."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
base=Path(__file__).resolve().parent
repo=base.parent/'osc-validation-run002'
sys.path.insert(0,str(repo/'scripts/architecture278/implementation'))
import stage17_parity as p
tree=p.parse((base/'retained/netlist.net').read_text())
source=p.audit_documents(p.hierarchy(repo/'design/architecture-278/implementation/stage17/generated/a01.kicad_sch'))
components=p.children(p.one(tree,'components'),'comp')
actual={}
for net in p.children(p.one(tree,'nets'),'net'):
    raw=p.one(net,'name')[1]
    for node in p.children(net,'node'):
        key=(p.one(node,'ref')[1],p.one(node,'pin')[1])
        if key in actual: raise ValueError('duplicate native pin')
        actual[key]=raw
conflicts=[]; missing_unit_pins=[]
for comp in components:
    ref=p.one(comp,'ref')[1]
    props={}
    for prop in p.children(comp,'property'):
        values=p.children(prop,'value')
        props[p.one(prop,'name')[1]]=values[0][1] if values else ''
    for group in p.children(comp,'fields'):
        for field in p.children(group,'field'):
            name=p.one(field,'name')[1]
            value=field[-1] if isinstance(field[-1],str) else ''
            if name in props and props[name]!=value:
                conflicts.append({'ref':ref,'name':name,'property':props[name],'field':value,
                    'source_unit_properties':[{'unit':r['unit'],'value':r['properties'].get(name)} for r in source if r['ref']==ref]})
    native_stamps=set(p.one(comp,'tstamps')[1:])
    for row in source:
        if row['ref']!=ref or p.one(row['symbol'],'uuid')[1] in native_stamps: continue
        pins=[]
        for pin,wanted in row['resolved'].items():
            raw=actual.get((ref,pin)); decoded=raw.replace('{slash}','/') if raw is not None else None
            disposition='MATCH after explicit slash decoding' if wanted is not None and decoded==wanted else 'NC omitted' if wanted is None and raw is None else 'NC singleton representation' if wanted is None and raw.startswith('unconnected-') and list(actual.values()).count(raw)==1 else 'DIFFERENCE'
            pins.append({'pin':pin,'source':wanted,'native_raw':raw,'native_decoded':decoded,'disposition':disposition})
        missing_unit_pins.append({'ref':ref,'unit':row['unit'],'source_uuid':p.one(row['symbol'],'uuid')[1],'pins':pins})
selected_pin_checks=[]
for row in source:
    if row['ref'] not in ('RN7101','RN7102'): continue
    for pin,wanted in row['resolved'].items():
        if pin!='9' and wanted is not None: continue
        raw=actual.get((row['ref'],pin)); decoded=raw.replace('{slash}','/') if raw else raw
        matches=(wanted is not None and wanted==decoded) or (wanted is None and raw is not None and raw.startswith('unconnected-') and list(actual.values()).count(raw)==1)
        selected_pin_checks.append({'ref':row['ref'],'pin':pin,'source':wanted,'native_raw':raw,'matches':matches})
field_values_from_source=all(all(v in {r['value'] or '' for r in c['source_unit_properties']} for v in (c['property'],c['field'])) for c in conflicts)
exhaustive=json.loads((base/'pin-classification.json').read_text())
declared={(r['reference'],r['pin']):r for r in exhaustive['pins']}
source_pins={(r['ref'],pin):net for r in source for pin,net in r['resolved'].items()}
assert len(declared)==len(exhaustive['pins'])==561 and set(declared)==set(source_pins)
assert set(actual)<=set(source_pins)
counts=Counter()
for key,wanted in source_pins.items():
    raw=actual.get(key); decoded=raw.replace('{slash}','/') if raw is not None else None
    classification=('NC_OMITTED' if raw is None else 'NC_SINGLETON' if raw.startswith('unconnected-') and list(actual.values()).count(raw)==1 else 'NC_CONNECTED_MISMATCH') if wanted is None else ('EXACT' if raw==wanted else 'SLASH_ENCODING_ONLY' if decoded==wanted else 'ABSENT' if raw is None else 'NET_MISMATCH')
    row=declared[key]
    assert (row['expected'],row['native_raw'],row['native_slash_decoded'],row['classification'])==(wanted,raw,decoded,classification)
    counts[classification]+=1
assert dict(counts)==exhaustive['counts']
report={'status':'CLASSIFICATION ONLY; full parity FAIL not waived',
    'netlist_sha256':hashlib.sha256((base/'retained/netlist.net').read_bytes()).hexdigest(),
    'normalization':'Only replace literal {slash} with / in native net names for diagnostic comparison; retain raw names.',
    'field_property_conflicts':conflicts,'missing_uuid_unit_pin_observations':missing_unit_pins,
    'lt5400_nc_and_ep_checks':selected_pin_checks,
    'field_conflicts_are_existing_unit_metadata_values':field_values_from_source,
    'independently_verified_exhaustive_pin_counts':dict(counts),
    'pin_classification_sha256':hashlib.sha256((base/'pin-classification.json').read_bytes()).hexdigest(),
    'classification':{'fields':'All8 conflicts concern Role, LogicalCellKey or Island unit-specific metadata; both native values exist among source units. They do not show MPN, manufacturer, value, footprint or pin/net disagreement.',
        'missing_unit_uuids':'All18 pins on the six units with omitted UUIDs remain represented:17connected nets align after explicit slash decoding,1NC remains a singleton unconnected net. Missing UUIDs are a unit-traceability/representation difference, not evidence of lost connectivity for these pins.',
        'source_lands':'All22 source-land components/pins remain absent; source flags exclude BOM/board. This is native observation coverage loss, not proven rewiring; full118/561/154 parity remains FAIL.',
        'net_encoding':'Literal {slash} differs from source / in raw native names. Diagnostic decoding is explicit and must not hide other character/name changes.'},
    'scope':'Read-only source/native observation. No CAD execution or source edits; no electrical acceptance.'}
(base/'review-classification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
