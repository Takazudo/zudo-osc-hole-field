"""Generate a disposable P ground prerequisite without canonical edits."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.prerequisite_terminal_access import source_entries,rules
from scripts.pcbgen.control_geometry_replan import revise, neighbor_envelopes


def generate(proposal_path,output):
    code=Path(__file__).read_bytes()
    proposal_path=Path(proposal_path);output=Path(output);raw=proposal_path.read_bytes();p=json.loads(raw)
    source=Path(p['canonical_definition']);source_bytes=source.read_bytes();original=json.loads(source_bytes)
    netlist_path=Path(p['source_netlist']);netlist_bytes=netlist_path.read_bytes()
    if output.resolve()==source.resolve() or output.stem!='osc-control' or original['board_id']!='osc-control' or original['layers']!=4 or original['thickness_mm']!=1.6:
        raise ValueError('separate fixed P definition required')
    pp=Path(p['source_partition']);partition_bytes=pp.read_bytes();partition=json.loads(partition_bytes)
    lands=[t for t in partition['load_side_terminals'] if t['board']=='P']
    definition,geometry_change=revise(original,p,lands)
    extra_paths=[Path('design/mechanical/selector-assembly.json'),Path('design/partition/partition-input.json'),Path('design/grid/placements.lock.json'),Path('scripts/pcbgen/control_geometry_replan.py')]
    extra_bytes={str(path):path.read_bytes() for path in extra_paths}
    neighbor=neighbor_envelopes(*(json.loads(extra_bytes[str(path)]) for path in extra_paths[:3]),p['geometry_replan']['RV601_tab']['left_x_mm'])
    stack=[];z=0.
    for i,layer in enumerate(['F.Cu','In1.Cu','In2.Cu','B.Cu']):
        t=p['nominal_copper_thickness_mm'][i]
        if t<=0:raise ValueError('positive foil thickness required')
        stack.append({'layer':layer,'role':'UNSELECTED P ground prerequisite' if layer in p['AGND_layers'] else 'Reserved future rail routing',
            'copper_oz':t/.035,'copper_thickness_mm':t,'nominal_midplane_depth_mm':z+t/2});z+=t
        if i<3:
            t=p['nominal_dielectric_thickness_mm'][i]
            if t<=0:raise ValueError('positive dielectric gap required')
            stack.append({'layer':'dielectric-'+str(i+1),'thickness_mm':t,'material':'UNSELECTED conditional pressed dielectric'});z+=t
    if abs(z-1.6)>1e-10:raise ValueError('nominal P stack changed total thickness')
    definition['stackup']=stack;classes=[]
    for name,nets in [('Default',[]),('Rails',['+12V','-12V','+5V']),('Ground',['AGND'])]:
        c={'name':name,'nets':nets,'track_width_mm':p['class_track_width_mm'][name],'clearance_mm':p['clearance_mm'],
            'via_diameter_mm':p['via_diameter_mm'],'via_drill_mm':p['via_drill_mm']}
        if name=='Ground':c['local_escape_track_width_mm']=p['local_ground_escape_width_mm']
        classes.append(c)
    definition['routing']={'min_track_width_mm':p['minimum_track_width_mm'],'net_classes':classes,
        'zones':[{'name':'agnd_feasibility','net':'AGND','layers':p['AGND_layers'],'clearance_mm':p['clearance_mm'],
            'min_thickness_mm':p['minimum_fill_neck_mm'],'pad_connection':'full'}]}
    if any(definition[k]!=v for k,v in original.items() if k not in ('stackup','routing','outline','keepouts')):
        raise ValueError('P fixed source geometry changed')
    headers=[c for c in partition['connectors'] if c['board']=='P']
    ports=[{'ref':c['pcb_reference'],'pad':pin,'side':c['side'],'header_id':c['id'],
        'source_footprint_origin_mm':c['footprint_origin_mm'],'native_orientation_deg':c['kicad_orientation_deg']}
        for c in headers for pin,net in c['pin_map'].items() if net=='AGND']
    entries=source_entries(definition,lands)
    if len(ports)!=127 or len(lands)!=6 or {r['ref'] for r in entries}!={land['reference'] for land in lands}:
        raise ValueError('exact P ground/reservation inventory changed')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(definition,indent=2,sort_keys=True)+'\n')
    output.with_suffix('.kicad_dru').write_text(rules(entries))
    sha=lambda b:hashlib.sha256(b).hexdigest()
    if proposal_path.read_bytes()!=raw or source.read_bytes()!=source_bytes or pp.read_bytes()!=partition_bytes or netlist_path.read_bytes()!=netlist_bytes or Path(__file__).read_bytes()!=code or any(Path(path).read_bytes()!=value for path,value in extra_bytes.items()):
        raise ValueError('P source changed during definition generation')
    receipt={'status':p['status'],'proposal_sha256':sha(raw),'canonical_definition_sha256':sha(source_bytes),
        'partition_sha256':sha(partition_bytes),'netlist_sha256':sha(netlist_bytes),
        'generator_sha256':sha(code),'definition_sha256':sha(output.read_bytes()),
        'native_rule_sha256':sha(output.with_suffix('.kicad_dru').read_bytes()),
        'fixed_component_geometry_preserved':True,'explicit_geometry_change':geometry_change,
        'neighbor_envelope_screen':neighbor,'geometry_source_sha256':{path:sha(value) for path,value in extra_bytes.items()},
        'selected_P_ground_ports':ports,'all_P_main_lands':lands,'own_terminal_entries':entries,'conditional_class':p}
    output.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('proposal',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=generate(a.proposal,a.output)
    print('P source:',len(r['selected_P_ground_ports']),'GH grounds, six fixed lands, six individual reservations and explicit local edge tab')
