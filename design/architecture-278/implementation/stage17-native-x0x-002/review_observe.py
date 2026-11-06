"""Read-only independent observation of retained native output; no CAD commands."""
import json
from pathlib import Path
import sys

base=Path(__file__).resolve().parent
repo=base.parent/'osc-validation-run002'
sys.path.insert(0,str(repo/'scripts/architecture278/implementation'))
import stage17_parity as p

tree=p.parse((base/'retained/netlist.net').read_text())
components=p.children(p.one(tree,'components'),'comp')
native_refs={p.one(c,'ref')[1] for c in components}
source=p.audit_documents(p.hierarchy(repo/'design/architecture-278/implementation/stage17/generated/a01.kicad_sch'))
source_refs={r['ref'] for r in source}
missing=sorted(source_refs-native_refs)
lands=[r for r in source if r['ref'] in missing]
unit_differences=[]
for comp in components:
    ref=p.one(comp,'ref')[1]
    expected={p.one(r['symbol'],'uuid')[1] for r in source if r['ref']==ref}
    actual=set(p.one(comp,'tstamps')[1:])
    if actual!=expected:
        lost=expected-actual
        unit_differences.append({'ref':ref,'missing_uuids':sorted(lost),'extra_uuids':sorted(actual-expected),
            'missing_units':[{'unit':r['unit'],'pins':r['resolved']} for r in source
                if r['ref']==ref and p.one(r['symbol'],'uuid')[1] in lost]})
observation={
    'source_references':len(source_refs),'source_units':len(source),
    'source_pins':sum(len(r['pins']) for r in source),
    'native_references':len(native_refs),
    'native_units_from_tstamps':sum(len(p.one(c,'tstamps'))-1 for c in components),
    'native_library_pins':sum(len(p.children(p.one(lib,'pins'),'pin')) for lib in p.children(p.one(tree,'libparts'),'libpart')),
    'missing':missing,'extra':sorted(native_refs-source_refs),
    'present_component_unit_differences':unit_differences,
    'missing_source_annotations':[{'ref':r['ref'],'unit':r['unit'],
        'pins':r['resolved'],'in_bom':p.one(r['symbol'],'in_bom')[1],
        'on_board':p.one(r['symbol'],'on_board')[1],
        'footprint':r['properties'].get('Footprint')} for r in lands],
    'scope':'Independent source/native roster observation; not waiver of full parity failure.'}
(base/'review-observation.json').write_text(json.dumps(observation,indent=2)+'\n')
print(json.dumps(observation,indent=2))
