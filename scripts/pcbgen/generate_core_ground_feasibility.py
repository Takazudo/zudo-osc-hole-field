"""Generate the bounded fixed-port K conductor definition without canonical edits."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.core_terminal_access import source_entries,rules


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def generate(proposal_path,output):
    proposal=json.loads(proposal_path.read_text());source=Path(proposal['canonical_definition'])
    if output.resolve()==source.resolve() or output.stem!=proposal['board_id']:
        raise ValueError('separate exact-board-name K feasibility definition required')
    original=json.loads(source.read_text());definition=copy.deepcopy(original)
    if definition['board_id']!='osc-core' or definition['layers']!=4 or definition['thickness_mm']!=1.6:
        raise ValueError('K fixed outline/layer source changed')
    stack=[];z=0.;names=['F.Cu','In1.Cu','In2.Cu','B.Cu']
    for index,layer in enumerate(names):
        thickness=proposal['nominal_copper_thickness_mm'][index]
        if thickness<=0:raise ValueError('positive K copper band required')
        stack.append({'layer':layer,'role':'UNSELECTED K AGND feasibility' if layer in proposal['AGND_layers'] else 'Reserved rail routing; no rail plane modeled',
                      'copper_oz':thickness/.035,'copper_thickness_mm':thickness,'nominal_midplane_depth_mm':z+thickness/2})
        z+=thickness
        if index<3:
            thickness=proposal['nominal_dielectric_thickness_mm'][index]
            if thickness<=0:raise ValueError('positive K dielectric band required')
            stack.append({'layer':'dielectric-'+str(index+1),'thickness_mm':thickness,'material':'UNSELECTED conditional pressed dielectric'});z+=thickness
    if abs(z-1.6)>1e-10:raise ValueError('K nominal stack must sum to unchanged1.6mm')
    definition['stackup']=stack
    classes=[]
    for name,nets in [('Default',[]),('Rails',['+12V','-12V','+5V']),('Ground',['AGND'])]:
        cls={'name':name,'nets':nets,'track_width_mm':proposal['class_track_width_mm'][name],
             'clearance_mm':proposal['clearance_mm'],'via_diameter_mm':proposal['via_diameter_mm'],
             'via_drill_mm':proposal['via_drill_mm']}
        if name=='Ground':
            cls['local_escape_track_width_mm']=proposal['local_ground_escape_width_mm']
        classes.append(cls)
    definition['routing']={'min_track_width_mm':proposal['minimum_track_width_mm'],'net_classes':classes,
        'zones':[{'name':'agnd_feasibility','net':'AGND','layers':proposal['AGND_layers'],
                  'clearance_mm':proposal['clearance_mm'],'min_thickness_mm':proposal['minimum_fill_neck_mm'],'pad_connection':'full'}]}
    for key in original:
        if key not in ('stackup','routing') and original[key]!=definition[key]:raise ValueError('K feasibility changed fixed source field '+key)
    partition_path=Path(proposal['source_partition']);partition=json.loads(partition_path.read_text())
    headers=[c for c in partition['connectors'] if c['board']=='K' and any(c['id'].startswith(prefix) for prefix in proposal['selected_interface_prefixes'])]
    ports=[{'ref':c['pcb_reference'],'pad':pin,'header_id':c['id'],'side':c['side'],
            'source_footprint_origin_mm':c['footprint_origin_mm'],'native_orientation_deg':c['kicad_orientation_deg']}
           for c in headers for pin,net in c['pin_map'].items() if net=='AGND']
    lands=[t for t in partition['load_side_terminals'] if t['board']=='K']
    if len(headers)!=52 or len(ports)!=206 or len(lands)!=18:raise ValueError('exact K source interface inventory changed')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(definition,indent=2,sort_keys=True)+'\n')
    output.with_suffix('.kicad_dru').write_text(rules(source_entries(definition,lands)))
    receipt={'status':proposal['status'],'proposal_sha256':digest(proposal_path),'canonical_definition_sha256':digest(source),
        'partition_sha256':digest(partition_path),'netlist_sha256':digest(proposal['source_netlist']),
        'generator_sha256':digest(__file__),'definition_sha256':digest(output),'fixed_source_geometry_preserved':True,
        'main_via_plan_sha256':digest(proposal['main_via_plan']),
        'header_stitch_plan_sha256':digest(proposal['header_stitch_plan']),
        'selected_K_ground_ports':ports,'all_K_main_lands':lands,'conditional_class':proposal}
    output.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('K feasibility source:',len(headers),'headers',len(ports),'J-facing ground contacts',len(lands),'main lands; canonical unchanged')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('proposal',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args();generate(args.proposal,args.output)
