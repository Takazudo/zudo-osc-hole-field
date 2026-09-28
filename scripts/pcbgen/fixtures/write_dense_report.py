#!/usr/bin/env python3
"""Summarize measured dense-slice attempts without turning route gaps into passes."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
cache=ROOT/'.circuit-cache/router'
def read(path):return json.loads(path.read_text()) if path.exists() else None
def last_pass(path):
    if not path.exists():return None
    matches=list(re.finditer(r'Auto-routing pass #(\d+).*?\((\d+) unrouted and',path.read_text()))
    return {'pass':int(matches[-1][1]),'unrouted_items':int(matches[-1][2])} if matches else None
source=read(cache/'dense-source/reports/routing.json')
latest=read(cache/'dense/reports/routing.json')
first=read(cache/'dense/four-layer-first-pass-routing.json')
best=latest if latest and latest.get('after') else first
reps=[read(cache/f'dense/reports/replicate-C{i}.json') for i in range(1,11)]
place=read(cache/'dense/reports/placement.json')
two=read(cache/'dense/two-layer-routing.json')
preexisting=read(cache/'dense/routing-work/preexisting-stats.json')
result={
 'schema_version':1,'status':'UNVALIDATED DRAFT','router_image':(best or latest or {}).get('router_image'),
 'geometry':{'full_board_copper_layers':4,'jack_columns':3,'jack_rows':10,'jack_pitch_x_mm':17,'jack_pitch_y_mm':14,'selected_jacks':30,'indicator_cells':30,'connector_count':1,'footprints':211},
 'source_column':{'status':source.get('status') if source else 'NOT RUN','router_runtime_sec':source.get('router_runtime_sec') if source else None,'sampled_peak_memory_mb':source.get('sampled_peak_memory_mb') if source else None,'unrouted_nets':source.get('unrouted_net_names') if source else None,'local_cell_nets_complete':bool(source and not any(n.startswith('/C') for n in source.get('unrouted_net_names',[])))},
 'replication':{'row_templates':10,'target_columns':2,'copied_tracks':sum(r.get('copied_track_count',0) for r in reps if r),'copied_vias':sum(r.get('copied_via_count',0) for r in reps if r),'all_runs_reported':all(reps)},
 'best_saved_board':{'status':best.get('status') if best else 'NOT RUN','router_runtime_sec':best.get('router_runtime_sec') if best else None,'total_runtime_sec':best.get('runtime_sec') if best else None,'sampled_peak_memory_mb':best.get('sampled_peak_memory_mb') if best else None,'via_count':best.get('via_count') if best else None,'total_track_length_mm':best.get('total_track_length_mm') if best else None,'preexisting_tracks_preserved':best.get('preexisting_tracks_preserved') if best else None,'preexisting_zones_preserved':best.get('preexisting_zones_preserved') if best else None,'drc':best.get('after') if best else None,'completion':bool(best and best.get('status')=='ROUTED DRAFT')},
 'latest_attempt':{'status':latest.get('status') if latest else 'NOT RUN','time_limit_sec':latest.get('time_limit_sec') if latest else None,'router_runtime_sec':latest.get('router_runtime_sec') if latest else None,'sampled_peak_memory_mb':latest.get('sampled_peak_memory_mb') if latest else None,'unrouted_nets':latest.get('unrouted_net_names') if latest else None,'unrouted_name_basis':latest.get('unrouted_name_basis') if latest else None,'last_router_pass':last_pass(cache/'dense/routing-work/freerouting-live.log')},
 'two_layer_diagnostic':{'status':two.get('status') if two else 'NOT RUN','time_limit_sec':two.get('time_limit_sec') if two else None,'router_runtime_sec':two.get('router_runtime_sec') if two else None,'sampled_peak_memory_mb':two.get('sampled_peak_memory_mb') if two else None,'last_router_pass':last_pass(cache/'dense/two-layer-freerouting.log')},
 'placement':{'status':place.get('status') if place else 'NOT RUN','placed_free_footprints':len(place.get('placements',[])) if place else None},
 'pre_route_vias':preexisting.get('via_count') if preexisting else None,
 'open_gate':{'requirement':'Full dense slice: zero KiCad rule errors, zero unconnected items, zero schematic parity issues',
              'observed':'Three GND unconnected items remain on the best saved four-layer board; no successful continuation SES',
              'next_action':'Review ground return and plane stitching near C1607 and J310, then reroute and repeat KiCad 10 DRC'},
 'qualification':'NOT RUN — routing and PCB remain unvalidated; mechanical, thermal and fabrication review are open'
}
path=ROOT/'scripts/pcbgen/fixtures/dense-slice-report.json';path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(f'dense report: best {result["best_saved_board"]["status"]}, latest {result["latest_attempt"]["status"]}')
