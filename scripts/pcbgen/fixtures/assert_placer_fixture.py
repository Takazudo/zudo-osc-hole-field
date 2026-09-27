#!/usr/bin/env python3
"""Assertions over KiCad 10 oracle output for placer fixtures."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[3]/'.circuit-cache/placer'
reports={case:json.loads((root/case/'reports/placement.json').read_text()) for case in ('one','six','island','overflow')}
for case,count in (('one',5),('six',30),('island',6)):
    report=reports[case]
    assert report['status']=='PLACED DRAFT',(case,report['status'])
    assert len(report['placements'])==count,(case,len(report['placements']))
    assert len(report['regions'])== (6 if case=='six' else 1)
    assert all(p['side']=='B.Cu' for p in report['placements'])
    drc=json.loads((root/case/'drc.json').read_text())
    assert drc['kicad_version']=='10.0.6'
    assert not drc['schematic_parity'],(case,drc['schematic_parity'])
    courtyard=[v for v in drc['violations'] if 'courtyard' in v['type']]
    assert not courtyard,(case,courtyard)
    print(f'{case}: {count} placed, 0 courtyard violations, 0 parity issues; {len(drc["unconnected_items"])} expected unconnected')
six=reports['six']
for p in six['placements']:
    if p['block']=='S1':continue
    source=next(q for q in six['placements'] if q['block']=='S1' and q['ref'][2:]==p['ref'][2:] and q['ref'][0]==p['ref'][0])
    n=int(p['block'][1:])-1
    assert abs(p['x_mm']-source['x_mm']-17*n)<1e-6,(p,source)
    assert abs(p['y_mm']-source['y_mm'])<1e-6,(p,source)
assert any(c['cluster']=='ic:U202' for c in six['clusters']),six['clusters']
one=reports['one'];placements={p['ref']:p for p in one['placements']}
assert 'C106' in placements and 'U102' in placements
c=placements['C106'];u=placements['U102']
assert abs(c['x_mm']-u['x_mm'])<=5 and abs(c['y_mm']-u['y_mm'])<=10,(c,u)
island=reports['island']
assert any(c['cluster'].startswith('island:J:') and c['refs']==['R107'] for c in island['clusters']),island['clusters']
island_positions={p['ref']:p for p in island['placements']}
assert island_positions['R107']['y_mm']<island_positions['U102']['y_mm'],island_positions
overflow=reports['overflow']
assert overflow['status']=='OVERFLOW' and len(overflow['overflow'])==1,overflow
item=overflow['overflow'][0]
assert item['instance']=='S1' and item['area_needed_mm2']>item['area_available_mm2'],item
print('six translations, IC cluster, island binding and overflow report: PASS')
