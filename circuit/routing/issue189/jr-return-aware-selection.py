from pathlib import Path
import json,hashlib
from shapely.geometry import Point,LineString
root=Path('.circuit-cache');source=root/'issue189-jr-no-in3-probe.json';native=root/'issue189-downloaded/jr-subset/osc-jack-right-grid-189-jr-additive-subset/dump.json';probe=json.loads(source.read_text());dump=json.loads(native.read_text());names={'J900109.2','J900109.4','J900109.6','C7313.2','C7215.2'};near=[];excluded=set()
for p in dump['pads']:
 name=p['ref']+'.'+p['pad']
 if name not in names:continue
 point=Point(p['xy'])
 for row in probe['proposal']['copper']:
  shape=Point(row['at_nm']) if row['kind']=='via' else LineString([row['start_nm'],row['end_nm']]);distance=shape.distance(point)/1e6
  if distance<=3:
   excluded.add(row['net']);near.append({'pad':name,'pad_uuid':p['uuid'],'new_copper_uuid':row['uuid'],'net':row['net'],'distance_mm':distance})
proposal={**probe['proposal'],'copper':[r for r in probe['proposal']['copper'] if r['net'] not in excluded]}
assert not proposal['removed_uuids'] and all(r['kind']=='via' or r['layer']!='In3.Cu' for r in proposal['copper'])
out={'status':'GEOMETRIC HYPOTHESIS; NATIVE NOT RUN','source_probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native_failed_run':37883303894,'native_dump_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'scope':'Exclude In3 signal traces and complete net transactions within3mm of the five native-detached AGND pads; preserve all original copper. Proximity is not proof of causality; full native gate required.','excluded_nets':sorted(excluded),'nearby_objects':near,'proposal':proposal}
(root/'issue189-jr-return-aware-selection.json').write_text(json.dumps(out,indent=2)+'\n');print('excluded',sorted(excluded),'remaining objects',len(proposal['copper']),'nets',len({r['net'] for r in proposal['copper']}))
