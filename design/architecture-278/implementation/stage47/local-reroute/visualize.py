"""Native-coordinate before/after visual; no inferred physical qualification."""
from pathlib import Path
import json,sys
from shapely.geometry import shape,box,LineString,Point
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from propose import POINTS,RETIRE,NET

def main():
 data=json.loads((HERE.parents[1]/'stage46/ground-escape/geometry.json').read_text())
 window=box(268.5,130.9,272.3,136.4)
 old=next(shape(o['geometry']) for o in data['objects'] if o['id']==RETIRE)
 out=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="870" viewBox="0 0 1080 870">','<rect width="1080" height="870" fill="white"/>','<g font-family="sans-serif" fill="#182738"><text x="30" y="34" font-size="23">Stage47 · one local signal detour permits a ground via</text><text x="30" y="61" font-size="14">Native millimetres · disposable trial only · fixed footprints / netlist / stackup</text></g>']
 def draw(g,color):
  g=g.intersection(window)
  if not g.is_empty:out.append(g.svg(scale_factor=.003,fill_color=color).replace('opacity="0.6"','opacity="1"'))
 for x,title,after in [(40,'Before: In3.Cu blocks ground landing',False),(570,'After: four segments replace one',True)]:
  out.append(f'<text x="{x}" y="96" font-family="sans-serif" font-size="17">{title}</text>')
  out.append(f'<g transform="translate({x},120) scale(100) translate(-268.5,-130.9)">')
  for o in data['objects']:
   if o['id']=='fill:18':draw(shape(o['geometry']),'#bae1c9')
   elif 'In3.Cu' in o['layers'] and o['id']!=RETIRE:draw(shape(o['geometry']),'#aeb4bd')
  if after:
   draw(LineString(POINTS).buffer(.1,resolution=64),'#3674bd');draw(Point(270.3,133.3).buffer(.35,resolution=64),'#21894e');draw(Point(270.3,133.3).buffer(.15,resolution=64),'white')
  else:draw(old,'#d06c50')
  out.append('</g>')
 out.extend(['<g font-family="sans-serif" fill="#182738" font-size="15">','<text x="40" y="711">Orange: retired 0.20 mm 1_PROTECTED segment. Blue: same-net 0.20 mm replacement.</text>','<text x="40" y="738">Green: 0.70 / 0.30 mm ground through-via at (270.3,133.3), over the existing B.Cu island.</text>','<text x="40" y="765">Gray: retained In3.Cu copper. B.Cu LED_K and all footprints remain unchanged.</text>','<text x="40" y="792">Signal endpoints preserved: (270.4,131.6) and (270.4,135.9). Maximum detour: +0.625 mm X.</text>','<text x="40" y="819">Native acceptance requires exact AGND merge 117→116 and all other retained partitions unchanged.</text>','</g></svg>'])
 (HERE/'reroute.svg').write_text('\n'.join(out)+'\n')
if __name__=='__main__':main()
