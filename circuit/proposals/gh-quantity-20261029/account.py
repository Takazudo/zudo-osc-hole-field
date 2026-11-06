"""Read-only draft partition accounting; no generator/native imports."""
import argparse,csv,hashlib,json
from collections import Counter
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('supplement',type=Path);ap.add_argument('variants',type=Path);a=ap.parse_args()
p=json.loads((a.supplement/'partition.json').read_text());f=json.loads((a.supplement/'floorplan-candidate.json').read_text())
headers={c['id']:c for c in p['connectors']}; assert len(headers)==len(p['connectors'])
refs={x['ref'] for x in p['assignment']['components']}; assert len(refs)==len(p['assignment']['components'])
assert refs=={x['ref'] for x in f['placements']}
seen=[]; wires=0; unused=0
for h in p['harnesses']:
 assert len(h['header_ids'])==2
 x,y=[headers[k] for k in h['header_ids']];seen+=h['header_ids']
 assert x['contacts']==y['contacts'] and x['pin_map']==y['pin_map']
 assert set(x['pin_map'])=={str(i) for i in range(1,x['contacts']+1)}
 nc=sum(v in (None,'NC') for v in x['pin_map'].values())
 assert nc==h['unused_contacts']
 n=x['contacts']-nc; assert n==h['signal_count']+h['return_contacts']+h.get('rail_contacts',0)
 wires+=n;unused+=nc
assert Counter(seen)==Counter({k:1 for k in headers})
capacity=sum(c['contacts'] for c in headers.values());assert capacity==2*(wires+unused)
hr={c['pcb_reference'] for c in headers.values()}; assert len(hr)==len(headers) and not hr&refs
variant_results={}; hashes={}
for v in ['UNI_ROYAL/BA1','UNI_ROYAL/RevP','YAGEO/BA1','YAGEO/RevP']:
 path=a.variants/v/'candidate/source-records/candidate-bom.csv';rows=list(csv.DictReader(path.open()));physical={r['ref'] for r in rows if r['population'] in ('FITTED','DNP') and r['footprint'] and r['on_board']=='yes'}
 variant_results[v]={'rows':len(rows),'physical_population_labels':dict(Counter(r['population'] for r in rows)),'assigned_not_in_candidate_physical':sorted(refs-physical),'candidate_physical_not_assigned':sorted(physical-refs),'header_refs_in_master':sorted(hr&{r['ref'] for r in rows})}
 hashes[str(path.relative_to(a.variants))]=hashlib.sha256(path.read_bytes()).hexdigest()
for n in ['partition.json','partition-input.json','floorplan-candidate.json','receipt.json']:hashes[n]=hashlib.sha256((a.supplement/n).read_bytes()).hexdigest()
result={'status':p['status'],'scope':'One supplied repository partition, not four adopted alternatives or a released assembly BOM','headers_by_mpn':dict(Counter(c['header_mpn'] for c in headers.values())),'housings_for_all_declared_ends':dict(Counter(c['housing_mpn'] for c in headers.values())),'header_positions_including_NC':capacity,'unused_positions_both_ends':unused*2,'derived_fitted_crimp_contacts':wires*2,'crimp_mpn_set':sorted({c['contact_mpn'] for c in headers.values()}),'harnesses':len(p['harnesses']),'wired_conductors_GH':wires,'signal_conductors':sum(h['signal_count'] for h in p['harnesses']),'return_conductors':sum(h['return_contacts'] for h in p['harnesses']),'rail_conductors':sum(h.get('rail_contacts',0) for h in p['harnesses']),'master_assigned_packages':len(refs),'master_fitted_packages':sum(x['fitted'] for x in p['assignment']['components']),'master_DNP_packages':sum(not x['fitted'] for x in p['assignment']['components']),'load_side_solder_lands_excluded_from_BOM':len(p['load_side_terminals']),'separate_load_side_wires':len(p['load_side_wires']),'load_side_wire_mpn_counts':dict(Counter(w['wire_mpn'] for w in p['load_side_wires'])),'abstract_exclusions':p['assignment']['abstract_boundaries'],'variant_comparison':variant_results,'input_sha256':hashes,'checks':'PASS paired pin maps/counts, unique header ownership, NC accounting, assignment/floorplan ref equality; no native/generation'}
print(json.dumps(result,indent=2))
