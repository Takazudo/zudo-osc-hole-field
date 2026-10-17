"""Source-only X1 geometry views; not production CAD or fabrication output."""
import argparse
import html
import json
from pathlib import Path
import stage8_rebudget as r
import assembly

def build():
    m=json.loads((r.OUT/'mechanical-report.json').read_text());l=json.loads((r.OUT/'locality-report.json').read_text())
    for report in (m,l):r.validate_bindings(report)
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 1000"><rect width="1500" height="1000" fill="#fbfaf7"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#202a32} .caption{font-size:15px} .title{font-size:23px;font-weight:bold}</style>',
         '<text x="30" y="36" class="title">X1 source geometry — conditional proposal, not routed/physical acceptance</text>',
         '<text x="30" y="65" class="caption">Orange: removed substrate envelope · Blue: package courtyard · Coloured: proposed critical copper corridor</text>',
         '<text x="30" y="88" class="caption">Solid copper = panel face; dashed = rear face. Circles mark vias/mounts. All dimensions derive from source reports.</text>']
    def rect(box,fill,stroke,width=.2):
        out.append(f'<rect x="{box[0]}" y="{box[1]}" width="{box[2]-box[0]}" height="{box[3]-box[1]}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    for board,x,y,scale in [('X1-jack',30,145,8.5),('X1-control',30,690,7.5)]:
        b=m['boards'][board]['outline_mm'];out.append(f'<text x="{x}" y="{y-15}" class="title">{board}</text>')
        out.append(f'<g transform="translate({x},{y}) scale({scale}) translate({-b[0]},{-b[1]})">');rect(b,'#eaf0e5','#46594d')
        for cut in m['manufacturing_sweep_bounds']:
            if cut['board']==board:rect(cut['box_mm'],'#f7c89f','#c77837',.1)
        for p in m['placements'].values():
            if p['board']!=board:continue
            rect(p['box_mm'],'none','#8aafc8',.13);px,py=p['origin_mm'];out.append(f'<text x="{px}" y="{py}" font-size="1.2" text-anchor="middle">{html.escape(p["ref"])}</text>')
        for p in m['header_obstacles'].values():
            if p['board']==board:rect(p['box_mm'],'none','#734b98',.2)
        for mount in m['mounts']:
            if mount['board']==board:
                px,py=mount['centre_mm'];out.append(f'<circle cx="{px}" cy="{py}" r="{mount["hole_diameter_mm"]/2}" fill="#fbfaf7" stroke="#333" stroke-width=".2"/>')
        if board=='X1-jack':
            colours=['#8c2448','#26704a','#6750a0','#b2581e','#186c9a','#787322','#aa3c47','#557b29','#285f9a','#843a91']
            for row,colour in zip(l['corridors'],colours):
                for segment in row.get('segments',[]):
                    a,bp=segment['from_xy_mm'],segment['to_xy_mm'];dash=' stroke-dasharray=".6 .35"'if segment['layer']==1 else''
                    out.append(f'<path d="M {a[0]} {a[1]} L {bp[0]} {bp[1]}" fill="none" stroke="{colour}" stroke-width="{row["width_mm"]}"{dash}/>')
                for via in row.get('vias',[]):
                    px,py=via['xy_mm'];out.append(f'<circle cx="{px}" cy="{py}" r="{via["diameter_mm"]/2}" fill="none" stroke="{colour}" stroke-width=".1"/>')
        out.append('</g>')
    out.append('<text x="770" y="130" class="title">Carrier proposal / fixed hardware projection</text><g transform="translate(790,150) scale(2)">')
    rect([0,0,318,298],'none','#555',.5)
    lock=json.loads((r.ROOT/'design/grid/placements.lock.json').read_text())
    for h in assembly.locked_hardware(lock['placements']):rect(h['box_mm'],'#e4e6e7','#c4c9ca',.08)
    for member in m['carrier_routed_members']:
        pts=' '.join(f'{p[0]},{p[1]}'for p in member.get('centreline_mm',[]));out.append(f'<polyline points="{pts}" fill="none" stroke="#376a52" stroke-width="{member["width_mm"]}" stroke-linejoin="round"/>')
    for anchor in m['carrier_proposal']['anchor_proposals']:
        x,y=anchor['centre_mm'];out.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#c48725" stroke="#573d15" stroke-width=".3"/>')
    out.append('</g><text x="770" y="785" class="caption">Green: routed carrier ribs; gold: proposed new enclosure anchors.</text><text x="770" y="812" class="caption">Attachment, tolerances and full frame mechanics remain conditional.</text><text x="770" y="839" class="caption">Read STAGE8.md for process and service constraints.</text></svg>')
    return '\n'.join(out)+'\n'

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();data=build();path=r.OUT/'geometry.svg'
    if args.check:assert path.read_text()==data,'stale Stage8 geometry view'
    else:path.write_text(data)
    print('Stage8 source geometry view reproduced; not fabrication CAD')

if __name__=='__main__':main()
