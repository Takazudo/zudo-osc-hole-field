"""Geometric proximity evidence only; never infer native split causality."""
import hashlib,json
from pathlib import Path
from shapely.geometry import LineString,Polygon
root=Path('.circuit-cache/issue189-downloaded/core-short19/.circuit-cache/osc-core-grid-shards-start')
p=root/'dump.json';d=json.loads(p.read_text());here=Path(__file__).parent
proposal=json.loads((here/'proposal.json').read_text());wanted={'J900311.2','C4445.2','U4606.5','C4623.2'}
pads=[p for p in d['pads'] if p['ref']+'.'+p['pad'] in wanted];assert len(pads)==4
rows=[]
for p in pads:
    shape=Polygon(p['poly']);by_net={}
    for c in proposal['copper']:
        if c['layer'] not in p['layers']:continue
        gap=(shape.distance(LineString([c['start_nm'],c['end_nm']]))-c['width_nm']/2)/1e6
        if c['net'] not in by_net or gap<by_net[c['net']]['gap_mm']:
            by_net[c['net']]={'net':c['net'],'segment_uuid':c['uuid'],'layer':c['layer'],'gap_mm':gap}
    rows.append({'pad':p['ref']+'.'+p['pad'],'uuid':p['uuid'],'xy_nm':p['xy'],'nearest_three_transactions':sorted(by_net.values(),key=lambda r:r['gap_mm'])[:3]})
result={'status':'PROXIMITY ONLY; NOT CAUSAL ATTRIBUTION OR A NATIVE-ELIGIBLE SUBSET','dump_sha256':hashlib.sha256((root/'dump.json').read_bytes()).hexdigest(),'proposal_sha256':hashlib.sha256((here/'proposal.json').read_bytes()).hexdigest(),'split_pads':rows}
(here/'split-proximity.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
