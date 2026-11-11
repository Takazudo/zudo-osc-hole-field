"""Deterministically build the disposable warning-shard fixture triple; --check verifies the committed bytes.

before/        two existing segments, silkscreen text/line, one footprint with a silk reference and a pad
after-clean/   before plus 70 segments and 10 untented vias, all clear of silkscreen (80 added objects)
after-planted/ after-clean plus one untented via centred on the F.SilkS line: a native silk_over_copper positive control

Not a design board: it only exercises the sharded complete-warning audit tooling.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

HERE=Path(__file__).resolve().parent
NAME='warning-shards'
NAMESPACE=uuid.UUID('6f1c2c55-5a43-4f0e-9a43-2d7a8f0e3b11')
PRO={'board':{'design_settings':{'rules':{'max_error':0.005,'min_clearance':0.0,'min_connection':0.0,'min_copper_edge_clearance':0.5,
      'min_hole_clearance':0.25,'min_hole_to_hole':0.25,'min_silk_clearance':0.0,'min_through_hole_diameter':0.3,'min_track_width':0.1,
      'min_via_annular_width':0.1,'min_via_diameter':0.5,'solder_mask_to_copper_clearance':0.0}}},
     'meta':{'filename':NAME+'.kicad_pro','version':3}}
DRU='(version 1)\n'


def uid(name):return str(uuid.uuid5(NAMESPACE,name))


def font(indent):
    t='\t'*indent
    return f'{t}(effects\n{t}\t(font\n{t}\t\t(size 1 1)\n{t}\t\t(thickness 0.15)\n{t}\t)\n{t})\n'


def header():
    layers=[(0,'F.Cu','signal'),(2,'B.Cu','signal'),(9,'F.Adhes','user "F.Adhesive"'),(11,'B.Adhes','user "B.Adhesive"'),(13,'F.Paste','user'),
            (15,'B.Paste','user'),(5,'F.SilkS','user "F.Silkscreen"'),(7,'B.SilkS','user "B.Silkscreen"'),(1,'F.Mask','user'),(3,'B.Mask','user'),
            (25,'Edge.Cuts','user'),(27,'Margin','user'),(31,'F.CrtYd','user "F.Courtyard"'),(29,'B.CrtYd','user "B.Courtyard"'),
            (35,'F.Fab','user'),(33,'B.Fab','user')]
    text='(kicad_pcb\n\t(version 20260206)\n\t(generator "pcbnew")\n\t(generator_version "10.0")\n'
    text+='\t(general\n\t\t(thickness 1.6)\n\t\t(legacy_teardrops no)\n\t)\n\t(paper "A4")\n\t(layers\n'
    text+=''.join(f'\t\t({n} "{name}" {kind})\n' for n,name,kind in layers)+'\t)\n'
    # Untented vias expose copper, so a via under silkscreen is a native silk_over_copper finding.
    text+='\t(setup\n\t\t(pad_to_mask_clearance 0)\n\t\t(allow_soldermask_bridges_in_footprints no)\n'
    text+='\t\t(tenting\n\t\t\t(front no)\n\t\t\t(back no)\n\t\t)\n\t\t(aux_axis_origin 100 50)\n\t\t(grid_origin 100 50)\n\t)\n'
    return text


def gr_line(name,x0,y0,x1,y1,layer,width):
    return (f'\t(gr_line\n\t\t(start {x0} {y0})\n\t\t(end {x1} {y1})\n\t\t(stroke\n\t\t\t(width {width})\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "{layer}")\n\t\t(uuid "{uid(name)}")\n\t)\n')


def artwork():
    text=''.join(gr_line('edge-'+str(i),*xy,'Edge.Cuts',0.05) for i,xy in enumerate([(100,50,170,50),(170,50,170,100),(170,100,100,100),(100,100,100,50)]))
    text+=f'\t(gr_text "WARNING SHARDS"\n\t\t(at 130 55 0)\n\t\t(layer "F.SilkS")\n\t\t(uuid "{uid("silk-text")}")\n'+font(2)+'\t)\n'
    text+=gr_line('silk-line',105,60,155,60,'F.SilkS',0.15)
    text+=(f'\t(footprint "fixture:PAD"\n\t\t(layer "F.Cu")\n\t\t(uuid "{uid("fp")}")\n\t\t(at 160 90 0)\n'
           f'\t\t(property "Reference" "TP1"\n\t\t\t(at 0 -3 0)\n\t\t\t(layer "F.SilkS")\n\t\t\t(uuid "{uid("fp-ref")}")\n'+font(3)+'\t\t)\n'
           f'\t\t(property "Value" "PAD"\n\t\t\t(at 0 3 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(uuid "{uid("fp-value")}")\n'+font(3)+'\t\t)\n'
           '\t\t(attr smd)\n'
           f'\t\t(fp_line\n\t\t\t(start -2 -1.8)\n\t\t\t(end 2 -1.8)\n\t\t\t(stroke\n\t\t\t\t(width 0.12)\n\t\t\t\t(type solid)\n\t\t\t)\n'
           f'\t\t\t(layer "F.SilkS")\n\t\t\t(uuid "{uid("fp-silk")}")\n\t\t)\n'
           f'\t\t(pad "1" smd rect\n\t\t\t(at 0 0 0)\n\t\t\t(size 1.5 1.5)\n\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n'
           f'\t\t\t(net "GND")\n\t\t\t(uuid "{uid("fp-pad")}")\n\t\t)\n\t)\n')
    return text


def segment(name,x0,y0,x1,y1,layer):
    return (f'\t(segment\n\t\t(start {x0} {y0})\n\t\t(end {x1} {y1})\n\t\t(width 0.25)\n\t\t(layer "{layer}")\n'
            f'\t\t(net "GND")\n\t\t(uuid "{uid(name)}")\n\t)\n')


def via(name,x,y):
    return (f'\t(via\n\t\t(at {x} {y})\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n'
            f'\t\t(net "GND")\n\t\t(uuid "{uid(name)}")\n\t)\n')


def boards():
    old=segment('old-0',105,95,115,95,'F.Cu')+segment('old-1',105,97,115,97,'B.Cu')
    added=''.join(segment(f'added-seg-{i}',105+(i%14)*4,66+(i//14)*3,107+(i%14)*4,66+(i//14)*3,'F.Cu' if i%2 else 'B.Cu') for i in range(70))
    added+=''.join(via(f'added-via-{i}',106+i*4,84) for i in range(10))
    planted=via('planted-via',130,60)
    end='\t(embedded_fonts no)\n)\n'
    base=header()+artwork()
    return {'before':base+old+end,'after-clean':base+old+added+end,'after-planted':base+old+added+planted+end}


def files():
    out={}
    for folder,text in boards().items():
        out[f'{folder}/{NAME}.kicad_pcb']=text.encode()
        out[f'{folder}/{NAME}.kicad_pro']=(json.dumps(PRO,indent=2)+'\n').encode()
        out[f'{folder}/{NAME}.kicad_dru']=DRU.encode()
    out['manifest.json']=(json.dumps({name:hashlib.sha256(data).hexdigest() for name,data in sorted(out.items())},indent=2)+'\n').encode()
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    expected=files()
    if args.check:
        stale=[name for name,data in expected.items() if not (HERE/name).is_file() or (HERE/name).read_bytes()!=data]
        if stale:sys.exit('stale warning-shard fixtures: '+', '.join(stale))
        print(f'PASS: {len(expected)} warning-shard fixture files match the builder');return
    for name,data in expected.items():(HERE/name).parent.mkdir(parents=True,exist_ok=True);(HERE/name).write_bytes(data)


if __name__=='__main__':main()
