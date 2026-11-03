import sys,json,hashlib
from pathlib import Path
repo=Path('/mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-verifier')
sys.path.insert(0,str(repo/'scripts/architecture278/implementation'))
import stage18_observation as s
run=Path('/home/takazudo/osc-stage18-native-001')
raw=(run/'retained/netlist.xml').read_bytes();obs=s.parse_xml(raw.decode());expected=s.expected_from_source()
errors=[]
def check(ok,kind,ref,actual=None,wanted=None):
    if not ok:errors.append({'kind':kind,'reference':ref,'observed':actual,'expected':wanted})
comps=obs['components'];check(set(comps)==set(expected),'reference_roster',None,sorted(comps),sorted(expected))
endpoints={};duplicates=[]
for net,row in obs['nets'].items():
    check(bool(row['nodes']),'empty_net',net)
    for node in row['nodes']:
        key=(node['ref'],node['pin'])
        if key in endpoints:duplicates.append(list(key))
        endpoints[key]=(net,node)
check(not duplicates,'duplicate_endpoints',None,duplicates,[])
wanted_endpoints={(ref,pin) for ref,w in expected.items() for pin in w['pins']}
check(set(endpoints)==wanted_endpoints,'pin_roster',None,{'missing':sorted(wanted_endpoints-set(endpoints)),'extra':sorted(set(endpoints)-wanted_endpoints)},None)
names=s.net_names(net for w in expected.values() for net in w['pins'].values() if net is not None)
coverage=[]
for ref,w in expected.items():
    if ref not in comps:continue
    c=comps[ref];before=len(errors)
    for key in ('value','footprint','datasheet','description','library','part','properties','sheetpath'):
        check(c[key]==w[key],key,ref,c[key],w[key])
    check(any(c['fields']==x['fields'] for x in w['field_candidates']),'fields',ref,c['fields'],[x['fields'] for x in w['field_candidates']])
    check(len(c['tstamps'])==len(set(c['tstamps'])) and sorted(c['tstamps'])==w['tstamps'],'uuid',ref,c['tstamps'],w['tstamps'])
    check(set(c['units'])==set(w['units']),'unit_slots',ref,c['units'],w['units'])
    for unit,pins in c['units'].items():
        check(unit in w['units'] and len(pins)==len(set(pins)) and sorted(pins)==w['units'].get(unit),'unit_pins',ref,{'unit':unit,'pins':pins},w['units'])
    libpins=obs['libraries'].get((w['library'],w['part']),[])
    check(len(libpins)==len(set(libpins)) and set(libpins)==set(w['pins']),'library_pins',ref,libpins,sorted(w['pins']))
    for pin,net in w['pins'].items():
        key=(ref,pin)
        if key not in endpoints:continue
        name,node=endpoints[key]
        if net is None:
            check(name.startswith('unconnected-') and len(obs['nets'][name]['nodes'])==1 and node.get('pintype','').endswith('+no_connect') and name not in names['xml_to_source'],'NC',ref+':'+pin,name,None)
        else:
            check(name==names['source_to_xml'][net] and not node.get('pintype','').endswith('+no_connect'),'pin_net',ref+':'+pin,{'name':name,'pintype':node.get('pintype')},names['source_to_xml'][net])
    coverage.append({'reference':ref,'pins_checked':len(w['pins']),'unit_UUIDs_checked':len(w['tstamps']),'mismatches':len(errors)-before})
check(set(obs['libraries'])=={(w['library'],w['part']) for w in expected.values()},'library_roster',None)
from collections import Counter
result={'status':'FAIL' if errors else 'PASS diagnostic only','official_comparator_status':'FAIL; unchanged; unit slot roster mismatch C7101','observation_sha256':hashlib.sha256(raw).hexdigest(),'source_commit':'91403f4d78b72757187d8cfdbb4d2dc436a3cf72','verification_commit':'a57e02f6bfd770e55ebf448bc067e79fc6b08eb5','coverage':coverage,'expected_counts':{'references':len(expected),'pins':len(wanted_endpoints),'unit_UUIDs':sum(len(w['tstamps']) for w in expected.values())},'observed_counts':{'references':len(comps),'pins':len(endpoints),'unit_UUIDs':sum(len(c['tstamps']) for c in comps.values())},'mismatch_counts':dict(Counter(x['kind'] for x in errors)),'mismatches':errors,'omission_waivers':[],'hardware_acceptance':False,'note':'Exhaustive source-only diagnostic against unchanged comparator expectations; no altered acceptance semantics and no native replay.'}
(run/'full-parity-diagnostic.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('coverage','mismatches')},indent=2));print(json.dumps(errors[:3],indent=2))
