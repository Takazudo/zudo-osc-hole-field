"""Source-derived A01 overview, not fabrication geometry or a fit certificate."""
import argparse,hashlib,html,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'design/architecture-278/implementation/stage10'
def draw(r):
    esc=lambda x:html.escape(str(x),quote=True)
    rows=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="940" viewBox="0 0 1200 940"><rect width="1200" height="940" fill="white"/><style>text{font-family:Arial,sans-serif;fill:#172d40} .small{font-size:10px}</style>', '<text x="24" y="30" font-size="23">A01 OFFSET1 — independent candidate source geometry</text><text x="24" y="52" font-size="13">90 whole packages / 9 fixed devices • proposed supports and enclosure changes • physical acceptance OPEN</text>']
    def rect(box,fill,stroke,extra=''):
        x,y,u,v=box;return f'<rect x="{x}" y="{y}" width="{u-x}" height="{v-y}" fill="{fill}" stroke="{stroke}" stroke-width=".5" {extra}/>'
    for index,(title,names)in enumerate([('Front assemblies',{'A01-jack','A01-control','A01-fixed'}),('Middle interface',{'A01-middle'}),('Rear core',{'A01-core'})]):
        x0=25+index*395
        rows +=[f'<text x="{x0}" y="84" font-size="19">{title}</text>',f'<svg x="{x0}" y="96" width="370" height="550" viewBox="184 80 145 242">',rect([184,80,329,322],'#fbfcfe','#cad4dc'),'<path d="M184 298H329" stroke="#c43" stroke-dasharray="2 2" stroke-width=".6"/><text x="186" y="296" font-size="3.8">Panel lower edge Y298</text>']
        for board,b in r['boards'].items():
            if board not in names:continue
            rows +=[rect(b['outline_mm'],'#e9f1ff','#357'),f'<text x="{b["outline_mm"][0]}" y="{b["outline_mm"][1]-2}" font-size="4">{esc(board)} / Z{b["z_mm"][0]}..{b["z_mm"][1]}</text>']
        framekey={'Front assemblies':['jack','control'],'Middle interface':['middle'],'Rear core':['rear']}[title]
        for key in framekey:
            f=r['carrier_frames'].get(key,{})
            for b in f.get('rails_boxes_mm',[])+f.get('crossmembers_boxes_mm',[]):rows.append(rect(b,'#cde9dc','#397b5c','fill-opacity=".6"'))
            for x,y in f.get('anchors_mm',[]):rows.append(f'<circle cx="{x}" cy="{y}" r="2.5" fill="none" stroke="#173"/><text x="{x-4}" y="{y-3}" font-size="3">anchor</text>')
        if index==1:
            for b in r.get('middle_access_edge_notches_mm',[]):rows.append(rect(b,'#fbfcfe','#b65'))
        if index==0:
            rows.append(rect(r['fixed_LED_substrate']['outline_mm'],'#fcecc8','#987'))
            for h in r['pot_rearshaft_relief_holes']:rows.append(f'<circle cx="{h["centre_mm"][0]}" cy="{h["centre_mm"][1]}" r="{h["diameter_proposal_mm"]/2}" fill="white" stroke="#733"/>')
        for ref,p in r['placements'].items():
            if p['board']not in names:continue
            rows.append(rect(p['box_mm'],'none','#915',f'id="package-{esc(ref)}"'))
            if ref.startswith('U')or p['panel_uid']:rows.append(f'<text x="{p["box_mm"][2]+.6}" y="{p["box_mm"][1]+2}" font-size="3">{esc(ref)}</text>')
        for ref,h in r['headers'].items():
            if h['board']in names:rows +=[rect(h['box_mm'],'#f5cc86','#865'),f'<text x="{h["box_mm"][0]}" y="{h["box_mm"][1]-1}" font-size="3">{esc(h["link"])}</text>']
        if index in (1,2):rows.append(rect(r['din_connectors']['middle'if index==1 else'rear']['box_mm'],'none','#b65'))
        for m in r['mounts']:
            if m['board']in names:rows.append(f'<circle cx="{m["xy_mm"][0]}" cy="{m["xy_mm"][1]}" r="2.5" fill="white" stroke="#273"/>')
        rows.append('</svg>')
    rows +=['<text x="25" y="675" font-size="18">Depth section and proposed service</text>','<text x="25" y="696" font-size="12">Z positive toward rear; fixed shaft centres stay unchanged. Front silhouettes are projections across different depths.</text>']
    faces=r['board_pad_faces_mm']
    planes=[('Panel rear',r['pot_datum']['panel_rear_z_mm']),('Pot PCB',faces['A01-control']['panel']),('Fixed jack/LED datum',faces['A01-fixed']['panel']),('Active jack PCB',faces['A01-jack']['panel']),('Middle rear face',faces['A01-middle']['rear']),('Core front face',faces['A01-core']['panel']),('Cover proposal',105)]
    for i,(name,z)in enumerate(planes):
        x=50+z*4.2;rows +=[f'<path d="M{x} 716V825" stroke="#357" stroke-width="2"/>',f'<path d="M{x} 825L{600} {720+i*18}" stroke="#b5c5d0"/>',f'<text x="610" y="{725+i*18}" font-size="14">{esc(name)}: Z{z} mm</text>']
    rows +=['<text x="25" y="851" font-size="13">Green: proposed rails/cleats; blue: PCBs; gold: connectors; magenta: complete source packages.</text>','<text x="25" y="873" font-size="13">Rear core: power off/discharge → unplug power → release captive screws → supported 40 mm withdrawal.</text>','<text x="25" y="895" font-size="13">Front repair needs proposed removable panel/right-side access. Unknown neighbors and exact clamp strength remain OPEN.</text>','<text x="25" y="920" font-size="14" fill="#a32">SOURCE ILLUSTRATION ONLY — no native ERC/DRC, simulation, physical fit, fabrication or hardware acceptance.</text></svg>']
    return '\n'.join(rows)+'\n'
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();source=OUT/'mechanical-report.json';r=json.loads(source.read_text());body=draw(r);target=OUT/'overview.svg'
    if args.check:
        if target.read_text()!=body:raise ValueError('stale A01 overview')
    else:target.write_text(body)
    print('A01 overview:90 source packages; independent board/support views; not physical acceptance')
if __name__=='__main__':main()
