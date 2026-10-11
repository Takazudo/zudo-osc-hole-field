import collections,gzip,html,json
from pathlib import Path
p=Path('design/partition/core-split/candidates/pilots/f3-whole-east-v1');e=p/'evidence'
def read(n):return json.loads(gzip.decompress((e/n).read_bytes()) if n.endswith('.gz') else (e/n).read_text())
counts={}
for n in ['pad-clearance-conflicts.json.gz','pad-copper-conflicts.json.gz','all-drilled-hole-conflicts.json.gz']:
 rows=read(n);groups=collections.Counter((r.get('origin','UNCLASSIFIED'),r.get('other_scope',r.get('object_scope','NOT_CLASSIFIED_IN_RECEIPT'))) for r in rows)
 counts[n]=[{'origin':k[0],'scope':k[1],'count':v} for k,v in sorted(groups.items())]
x=read('transformed-copper-obstructions.json.gz')
counts['transformed_copper']={k:[{'origin':a[0],'scope':a[1],'count':n} for a,n in sorted(collections.Counter((r.get('origin','LOCATION_DEPENDENT'),r.get('other_scope','NOT_CLASSIFIED_IN_RECEIPT')) for r in rows).items())] for k,rows in x.items()}
x=read('fixed-contact-reconstruction.json.gz');net_contacts=collections.Counter(r['net_token'] for r in x);pad_contacts=collections.Counter(r['pad_uuid'] for r in x)
counts['boundary']={'original_contacts':len(x),'distinct_original_objects':len({r['fixed_object_key'] for r in x}),'moved_pads_with_original_contacts':len(pad_contacts),'broken_original_contacts':sum(r['destination_gap_mm']>1e-7 for r in x),'contact_classes':dict(collections.Counter(r['net_class'] for r in x)),'nets':[{'net':r['source_net'],'classification':r['classification'],'fixed_source_objects':len(r['all_original_objects']),'original_moved_pad_contacts':net_contacts[r['net_token']],'moved_pads_without_original_copper_contact':[u for u in r['moved_pad_uuids'] if not pad_contacts[u]]} for r in read('boundary-net-obligations.json.gz')]}
x=read('internal-copper-classification.json.gz');counts['internal']={'kinds':dict(collections.Counter(r['kind'] for r in x)),'same_net_contact_records_directed':sum(len(r['contacts']['same_net_copper']) for r in x),'original_pad_contact_records':sum(len(r['contacts']['original_pad_contacts']) for r in x),'scope':'Source polygon contacts; no native or zone acceptance.'}
(e/'result-counts.json').write_text(json.dumps(counts,indent=2)+'\n')
b=json.load(open('design/partition/core-split/candidates/two.json'))['boards']['two-A'];selected=read('selected-courtyards.json');moved={r['ref'] for r in selected}
out=['<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="820" viewBox="0 0 1060 820">','<rect width="1060" height="820" fill="#fafafa"/>','<style>text{font-family:Arial,sans-serif;fill:#172033}.caption{font-size:13px}.label{font-size:9px}</style>','<text x="28" y="30" font-size="22">Whole F3 eastern relocation: rejected fixed candidate</text>','<text x="28" y="54" class="caption">Saved census geometry only · red: translated F3 · blue: fixed circuitry · grey: reservations</text>']
for k,face in enumerate(['F.Cu','B.Cu']):
 ox=30+525*k;oy=90;scale=5
 def pt(x,y):return (ox+(x-162)*scale,oy+(y-46)*scale)
 def poly(points,color,opacity,stroke):
  coords=' '.join(f'{a:.3f},{z:.3f}' for x,y in points for a,z in [pt(x,y)])
  return f'<polygon points="{coords}" fill="{color}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width=".65"/>'
 out += [f'<text x="{ox}" y="80" font-size="17">{face}</text>',f'<defs><clipPath id="c{k}"><rect x="{ox}" y="{oy}" width="430" height="640"/></clipPath></defs>',f'<g clip-path="url(#c{k})">']
 for r in b['measurement']['faces'][face]['reservation_polygons_mm']:
  for q in r['polygons']:out.append(poly(q,'#888',.25,'#888'))
 for r in b['placements']:
  if r['side']==face and r['ref'] not in moved:
   for q in r['courtyard_polygons_mm']:out.append(poly(q,'#2359a6',.28,'#2359a6'))
 for r in selected:
  if r['side']==face:
   for q in r['physical_polygons_mm']:out.append(poly([[x-100,y-50] for x,y in q],'#e43939',.33,'#b21717'))
   if r['ref'] in {'U2306','U2309','U2316','RV2311','C2325'}:
    q=r['physical_polygons_mm'][0];x,y=pt(q[0][0]-100,q[0][1]-50);out.append(f'<text x="{x:.2f}" y="{y-2:.2f}" class="label">{r["ref"]}</text>')
 x,y=pt(164,48);out += [f'<rect x="{x}" y="{y}" width="400" height="600" fill="none" stroke="#653da0" stroke-width="1.5" stroke-dasharray="5 4"/>','</g>']
 out.append(f'<text x="{ox}" y="754" class="caption">Window X164–244, Y48–168 mm; candidate coordinates</text>')
out += ['<text x="28" y="790" class="caption">24 foreign-courtyard failures + 1 inherited gap failure · 10 reservation overlaps · 3 service-hole collisions</text>','</svg>']
(p/'audited-placement.svg').write_text('\n'.join(out)+'\n')
print('Saved result-only counts and illustration; no audit rerun')
