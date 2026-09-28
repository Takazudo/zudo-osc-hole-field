#!/usr/bin/env python3
"""KiCad oracle assertions for small routed fixture reports."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]/'.circuit-cache/router'
def report(case):return json.loads((ROOT/case/'reports/routing.json').read_text())
for case in ('one','four','six'):
    r=report(case)
    assert r['status'] in ('ROUTED DRAFT','UNCHANGED DRAFT'),(case,r['status'])
    after=r['after']
    assert after['rule_errors']==after['unconnected_items']==after['schematic_parity_issues']==0,(case,after)
    assert r['via_count']>0 and r['total_track_length_mm']>0,(case,r)
    print(f'{case}: 0 KiCad errors, 0 unconnected, 0 parity; {r["via_count"]} vias')
four=report('four')
assert {'GND','+12V'}.issubset(four['via_nets']),four['via_nets']
six=report('six')
assert six['preexisting_tracks_preserved']>=200 and six['preexisting_zones_preserved']>=1,six
rep=json.loads((ROOT/'six/reports/replication.json').read_text())
assert set(rep['targets'])=={f'S{i}' for i in range(2,7)} and rep['copied_track_count']>0,rep
unroute=report('unroutable')
assert unroute['status']=='TIMEOUT DRAFT' and unroute['unrouted_net_names'],unroute
print('plane via nets, five translated instances, and distinct named timeout: PASS')
