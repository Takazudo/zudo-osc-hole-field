"""Render the exact unimplemented F-tail cleanup scope in native millimetres."""
import json
from pathlib import Path
from shapely.geometry import shape,box,LineString,Point
HERE=Path(__file__).resolve().parent
TAIL={'02d727f2-84bb-57f4-b095-90a15351d259','14e5290c-3c0a-51c3-9ddb-c71c7f2b33c3','1a635a05-179c-56a8-9299-9bdfe2cc2ca5','41da91b3-066c-59be-a6d5-e465426e70e9','4987e593-215d-56a9-a415-0501896d057c','cdc72bb1-5b70-5452-ba71-e04b9c8105e1','e70d01bd-e454-578a-b41f-6705ed031b1e','a63a488c-d65e-5563-90b3-e28bf3a61872'}
B={'f3c671af-83ca-560f-8614-5a530082d051','a8007baf-45fa-5fc8-be0d-a0a22bae8b43'}
def render():
 data=json.loads((HERE.parents[1]/'stage46/ground-escape/geometry.json').read_text());window=box(269.5,130.8,272.5,135.2)
 out=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="790" viewBox="0 0 1080 790">','<rect width="1080" height="790" fill="white"/>','<g font-family="sans-serif" fill="#182738"><text x="30" y="35" font-size="22">Stage49 · off-pad LED transition; assembly limit remains</text><text x="30" y="64" font-size="15">DISPOSABLE CANDIDATE · native coordinates · no canonical adoption</text></g>']
 def draw(g,c):
  g=g.intersection(window)
  if not g.is_empty:out.append(g.svg(scale_factor=.002,fill_color=c).replace('opacity="0.6"','opacity="1"'))
 for x,title,after in [(45,'Baseline: existing LED layer transition',False),(580,'Authorized cleanup after new transition',True)]:
  out.append(f'<text x="{x}" y="105" font-family="sans-serif" font-size="17">{title}</text><g transform="translate({x},125) scale(95) translate(-269.5,-130.8)">')
  for o in data['objects']:
   if o['id'].startswith('fill:'):continue
   if o['id'] in TAIL|B:
    if not after:draw(shape(o['geometry']),'#c86546' if o['id'] in TAIL else '#9874a9')
   elif 'F.Cu' in o['layers'] or 'B.Cu' in o['layers']:draw(shape(o['geometry']),'#c2c9cf')
  if after:
   draw(LineString([(271.3,131.15),(271.3,132.8)]).buffer(.1),'#397abd')
   draw(LineString([(271.15,132.55),(271.32,132.8)]).buffer(.1),'#9874a9')
   draw(Point(271.32,132.8).buffer(.3),'#21894e');draw(Point(271.32,132.8).buffer(.15),'white')
  out.append('<rect x="269.4" y="132.3" width="1.82" height="3.28" fill="none" stroke="#b14545" stroke-width=".018" stroke-dasharray=".07 .04"/>')
  out.append('</g>')
 for y,t in [(620,'Orange: retired tail / via. Blue: trimmed F segment. Dashed red: R8270 courtyard.'),(648,'Purple: B.Cu LED_K reroute already studied. Green: proposed off-pad 0.60 / 0.30 mm LED via.'),(676,'New via (271.32,132.8); F endpoint (271.3,132.8). No ground via or SMT-pad drilling.'),(704,'Pad gap 0.280 mm; drill gap 0.430 mm. Annulus enters courtyard 0.20 mm; drill 0.05 mm.'),(732,'Native: 117→116 intended closure, zero rule/parity errors, no added uncapped warnings.'),(760,'Ground fills omitted. Exact body / assembly process unresolved; no manufacturing qualification.')]:
  out.append(f'<text x="30" y="{y}" font-family="sans-serif" font-size="15" fill="#182738">{t}</text>')
 out.append('</svg>');(HERE/'cleanup.svg').write_text('\n'.join(out)+'\n')
if __name__=='__main__':render()
