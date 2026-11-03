"""Deterministic engineering SVG from the exact local geometry export."""
from pathlib import Path
import html,json
from shapely.geometry import box
from analyze import HERE,analyze

def main():
 data=json.loads((HERE/'geometry.json').read_text());result,reachable,objects,seed=analyze(data)
 window=box(267.8,131.7,271.6,135.6)
 parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="750" viewBox="0 0 1080 750">',
 '<rect width="1080" height="750" fill="#fff"/>',
 '<g font-family="sans-serif" fill="#172333"><text x="32" y="35" font-size="23">Stage46 · R8270:2 additive ground escape</text>',
 '<text x="32" y="63" font-size="14">Native millimetres · pinned Stage44 B1+B2 board · proposed source screen, no PCB edits</text></g>']
 def draw(g,color,opacity=1):
  g=g.intersection(window)
  if g.is_empty:return
  # Shapely paths preserve polygon holes via evenodd fill.
  parts.append('<g fill="'+color+'" fill-opacity="'+str(opacity)+'" stroke="none">'+g.svg(scale_factor=.005,fill_color=color).replace('opacity="0.6"','opacity="1"')+'</g>')
 for x,layer,title in [(40,'B.Cu','B.Cu: isolated ground enclosed by signal copper'),(565,'In3.Cu','In3.Cu: through-via landings obstructed')]:
  parts.append(f'<text x="{x}" y="102" font-family="sans-serif" font-size="16">{title}</text>')
  parts.append(f'<g transform="translate({x},125) scale(120) translate(-267.8,-131.7)">')
  draw(seed,'#8bd1a6')
  if layer=='B.Cu': draw(reachable,'#4d8fcc',.45)
  for o,g in objects:
   if layer in o['layers'] and o['net']!='AGND':draw(g,'#c65b57' if layer=='B.Cu' else '#9d76ca')
  parts.append('</g>')
 parts.extend(['<g font-family="sans-serif" fill="#172333" font-size="15">',
 '<text x="40" y="620">Green: source-connected AGND island (3.1230 mm²). Blue: optimistic 0.10 mm track-center reach.</text>',
 '<text x="40" y="647">Red: retained B.Cu signal copper. Purple: retained In3.Cu copper; all-layer obstacles used in analysis.</text>',
 '<text x="40" y="674">No 0.50 / 0.60 / 0.70 mm through-via landing, even with 0.01 mm extra clearance allowance.</text>',
 '<text x="40" y="701">Result is a bounded source obstruction screen; 117 opens remain. No native repair accepted.</text>',
 '</g></svg>'])
 (HERE/'obstruction.svg').write_text('\n'.join(parts)+'\n')
if __name__=='__main__':main()
