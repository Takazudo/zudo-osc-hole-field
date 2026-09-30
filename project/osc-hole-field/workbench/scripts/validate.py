#!/usr/bin/env python3
"""Structural/data checks only. Not native CAD, electrical or mechanical qualification."""
from pathlib import Path
from collections import Counter
import json,csv,re,xml.etree.ElementTree as ET,hashlib
R=Path(__file__).resolve().parents[1];D=json.loads((R/'layout/grid.json').read_text());P=json.loads((R/'parts/components.json').read_text());checks=[]
def c(name,condition):checks.append({'test':name,'pass':bool(condition)});assert condition,name
ports=D['ports'];controls=D['controls'];allq=ports+controls
c('180 ports / 144 controls',len(ports)==180 and len(controls)==144)
c('Every screenshot cell occupied exactly once',Counter((q['col'],q['row']) for q in ports)==Counter({(x,y):1 for x in range(18) for y in range(10)}))
c('Every control occupies a unique cell',len({(q['col'],q['row']) for q in controls})==144)
c('Control ranges and all 144 cells filled',set((c,r) for c in range(18) for r in range(8))-{(q['col'],q['row']) for q in controls}==set())
c('Unique interactive ids',len({q['uid'] for q in allq})==324)
actual={(q['col'],q['row']):(q['block'],q['key'],q['direction']) for q in ports}
# Independently reproduce the high-level screenshot rows to detect accidental remapping.
for i in range(5):
 exp=['1V','FM','PWM','SYNC','SIN','TRI','SAW','PUL']
 c(f'OSC {i+1} exact rows',all(actual[i,r]==(f'O{i+1}',k,'in' if r<4 else 'out') for r,k in enumerate(exp)))
for i in range(3):
 exp=['IN','FREQ','RES','GAIN','LP','BP','HP','OUT']
 c(f'FILTER {i+1} exact rows',all(actual[i+5,r]==(f'F{i+1}',k,'in' if r<4 else 'out') for r,k in enumerate(exp)))
for i,b in enumerate(['M5A','M5B','M4A','M4B']):
 exp=['1','2','3','4','5' if i<2 else 'ATTEN','SUM']
 c(f'{b} exact rows',all(actual[i+8,r]==(b,k,'out' if r==5 else 'in') for r,k in enumerate(exp)))
for i in range(6):
 exp=['SIG','RISE','FALL','ENV','BIP','EOC','STG','IN','OFFSET','OUT']
 c(f'ENV/OFFSET {i+1} exact column',all(actual[i+12,r]==(f'E{i+1}' if r<7 else f'A{i+1:02}',k,'out' if r in [3,4,5,6,9] else 'in') for r,k in enumerate(exp)))
for b,cc in [('W2',8),('W1',10)]:c(b+' exact tile',all(actual[x,y]==(b,k,d) for x,y,k,d in [(cc,6,'IN','in'),(cc+1,6,'FOLD','in'),(cc,7,'BIAS','in'),(cc+1,7,'OUT','out')]))
for b,cc in [('B1',0),('B2',2)]:c(b+' exact 1-to-3 tile',all(actual[x,y]==(b,k,d) for x,y,k,d in [(cc,8,'IN','in'),(cc+1,8,'1','out'),(cc,9,'2','out'),(cc+1,9,'3','out')]))
for i,r in [(1,8),(2,9)]:
 c(f'S&H {i} exact row',all(actual[x,r]==(f'H{i}',k,d) for x,k,d in [(4,'TRIGGER','in'),(5,'IN','in'),(6,'OUT','out')]))
 c(f'SWITCH {i} exact row',all(actual[x,r]==(f'X{i}',k,d) for x,k,d in [(7,'IN-A','in'),(8,'IN-B','in'),(9,'OUT','out')]))
c('Four noise outputs exact positions',all(actual[x,y]==('N1',k,'out') for x,y,k in [(10,8,'WHITE'),(11,8,'PINK'),(10,9,'BLUE'),(11,9,'BROWN')]))
c('Correct actuator kinds',Counter(q['kind'] for q in controls)=={'pot':101,'octave':5,'switch':30,'button':8})
c('No fader remnants in active controls',all(q['kind']!='fader' for q in controls))
c('Toggle count / states',Counter(len(q['positions']) for q in controls if q['kind']=='switch')=={2:19,3:11})
c('Indicators updated',sum(q['led'] for q in ports)==92 and sum(q['clip'] for q in ports)==10 and sum('stage' in q for q in controls)==12)
c('Exact rows represented by groups',all(sum(g['block']==q['block'] and g['field']==q['field'] and g['col']<=q['col']<g['col']+g['cols'] and g['row']<=q['row']<g['row']+g['rows'] for g in D['groups'])==1 for q in allq))
c('Parts register unique ids',len(P)==22 and len({q['id'] for q in P})==22)
c('Every component record exists',set(q['component'] for q in allq)<={q['id'] for q in P})
c('All decisions have source URLs',all(q['sources'] and all(s['url'].startswith('https://') for s in q['sources']) for q in P))
c('No silent normal connections',D['no_interblock_normals'] is True)
c('Offline build contains actual sources',all(tag in (R/'index.html').read_text() for tag in ['window.GRID_DATA','window.Grid3D','Sample, hold & slew','180 jacks']))
c('No unfilled template markers',not re.search(r'<!--(?:DATA|ENGINE|APP|BOOT|RENDER|CSS)-->',(R/'index.html').read_text()))
if (R/'panels/panel.svg').exists():
 svg=ET.parse(R/'panels/panel.svg').getroot();c('SVG actual millimetre dimensions',svg.attrib['width']=='318mm' and svg.attrib['height']=='298mm')
if (R/'reports/browser-tests.json').exists():
 b=json.loads((R/'reports/browser-tests.json').read_text());c('Browser report actually passes',b['passed']==b['total'])
report={'scope':'Structure and file integrity only, no ERC/DRC or assembly approval','passed':len(checks),'total':len(checks),'checks':checks}
(R/'reports/structural-tests.json').write_text(json.dumps(report,indent=2));print(len(checks),'structural checks passed')
