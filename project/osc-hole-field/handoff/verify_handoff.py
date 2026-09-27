#!/usr/bin/env python3
"""Validate payload counts, unchanged coordinates, local links and publication hashes.
No official circuit-doc, native CAD, bench or inventory qualification is inferred.
"""
from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as ET
from collections import Counter
R=Path(__file__).resolve().parent;P=R/'payload';W=P/'project/osc-hole-field/workbench';checks=[]
def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
D=json.loads((W/'layout/grid.json').read_text());B=json.loads((W/'reference/r20-grid.json').read_text());Q=json.loads((P/'project/osc-hole-field/current-spec.json').read_text())
ck('180 exact R20 jack records retained',D['ports']==B['ports'] and len(D['ports'])==180)
old={q['uid']:q for q in B['controls']};now={q['uid']:q for q in D['controls']}
ck('All 142 prior controls retained byte-equivalently as JSON values',len(old)==142 and all(now[k]==v for k,v in old.items()))
ck('Only two new controls',set(now)-set(old)=={'C:H1.SLEW','C:H2.SLEW'})
ck('New controls have intended cells',[(now[f'C:H{i}.SLEW']['col'],now[f'C:H{i}.SLEW']['row']) for i in [1,2]]==[(7,6),(7,7)])
ck('144 lower cells exactly occupied',Counter((q['col'],q['row']) for q in D['controls'])==Counter({(c,r):1 for c in range(18) for r in range(8)}))
ck('Actuator count',Counter(q['kind'] for q in D['controls'])=={'pot':101,'octave':5,'switch':30,'button':8})
ck('101 pots in summary',Q['counts']['continuous_pots']==101)
ck('No default normals',D['no_interblock_normals'])
ck('No fake generated catalog payload',not (P/'doc/src/content/docs/components').exists())
ck('No replacement native evidence or runtime config',not (P/'.claude').exists() and not (P/'circuit.config.ts').exists() and not (P/'package.json').exists())
ck('Public workbench matches rebuilt source artifact',(P/'doc/public/assets/osc-hole-field/workbench.html').read_bytes()==(W/'index.html').read_bytes())
for f in P.rglob('*.json'):
 try:json.loads(f.read_text())
 except Exception as e:raise AssertionError(str(f)+': '+str(e))
ck('All payload JSON parses',True)
for f in (P/'doc/public/assets/osc-hole-field').glob('*.svg'):ET.parse(f)
ck('All public SVG parses',True)
mdx=list((P/'doc/src/content/docs').rglob('*.mdx'));ck('45 authored documentation pages',len(mdx)==45)
missing=[]
for f in mdx:
 text=f.read_text();ck('Frontmatter '+f.name,text.startswith('---\n') and '\ntitle: ' in text)
 for target in re.findall(r'\]\(([^\s)]+)',text):
  if target.startswith(('https:','http:','#')):continue
  target=target.split('#')[0]
  dst=(P/'doc/public'/target.lstrip('/')) if target.startswith('/assets/') else f.parent/target
  if not dst.exists():missing.append((str(f.relative_to(P)),target))
ck('All authored document resource links resolve',not missing)
for name in ['structural-tests','logic-tests','slew-tests','browser-tests']:
 r=json.loads((W/f'reports/{name}.json').read_text());ck(name+' has actual passing report',r['passed']==r['total'])
receipts=json.loads((P/'research/osc-hole-field/sources.json').read_text());ck('No invented original-source hashes',all(s['sha256'] is None and s['original_file_retained'] is False for s in receipts))
ck('No shipped fonts or transient artifacts',not any(p.suffix.lower() in ['.ttf','.otf','.woff','.woff2','.pyc'] for p in R.rglob('*') if 'cache' not in str(p)))
manifest=R/'SHA256SUMS.json'
if manifest.exists():
 M=json.loads(manifest.read_text());bad=[x for x,h in M['files'].items() if not (R/x).is_file() or hashlib.sha256((R/x).read_bytes()).hexdigest()!=h];ck('All immutable delivery hashes match',not bad)
report={'scope':'Handoff structure, own tests and links only; not official circuit-doc, native KiCad or hardware validation','passed':len(checks),'total':len(checks),'checks':checks}
(R/'reports/handoff-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(f'{len(checks)} handoff checks passed')
