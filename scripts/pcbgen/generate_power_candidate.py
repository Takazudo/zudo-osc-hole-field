"""Generate a disposable board definition from an explicit power-plane proposal."""
import argparse
import hashlib
import json
from pathlib import Path


def generate(board_id, proposal, profile_name, output):
    source = Path('design/boards')/(board_id+'.json')
    definition = json.loads(source.read_text())
    proposals = json.loads(proposal.read_text()); profile = proposals['profiles'][profile_name]
    if output.resolve() == source.resolve() or output.stem != board_id:
        raise ValueError('candidate definition must have its own directory and exact board-id filename')
    zones = []
    for layer, net in proposals['plane_nets'].items():
        zones.append({'name': 'agnd_plane' if net == 'AGND' else net+'_plane',
            'net': net, 'layers': [layer],
            'clearance_mm': profile['AGND_clearance_mm'] if net == 'AGND' else .25,
            'min_thickness_mm': profile['AGND_minimum_fill_neck_mm'] if net == 'AGND' else .15,
            'pad_connection': 'full'})
    definition['routing']['zones'] = zones
    definition['routing']['local_escape_overrides'] = proposals['local_escape_overrides']
    for net_class in definition['routing']['net_classes']:
        if any(net in proposals['plane_nets'].values() for net in net_class['nets']):
            net_class['local_escape_track_width_mm'] = proposals['local_escape_track_width_mm']
    for layer in definition['stackup']:
        if layer['layer'] in proposals['plane_nets']:
            name = layer['layer']; thickness = profile['copper_thickness_mm'][name]
            layer.update({'role': 'DISPOSABLE '+proposals['plane_nets'][name]+' plane',
                          'copper_oz': thickness/.035, 'copper_thickness_mm': thickness})
            if name == 'In1.Cu' and 'all_In1_copper_clearance_mm' in profile:
                layer['minimum_copper_clearance_mm'] = profile['all_In1_copper_clearance_mm']
    coppers = [r for r in definition['stackup'] if r['layer'].endswith('.Cu')]
    stack = []; z = 0.
    for index, layer in enumerate(coppers):
        layer['nominal_midplane_depth_mm'] = z+layer['copper_thickness_mm']/2
        stack.append(layer); z += layer['copper_thickness_mm']
        if index < 3:
            thickness = profile['nominal_dielectric_mm'][index]
            if thickness <= 0:
                raise ValueError('source dielectric thickness must be finite positive')
            stack.append({'layer': 'dielectric-'+str(index+1), 'thickness_mm': thickness,
                          'material': 'UNSELECTED conditional pressed dielectric'})
            z += thickness
    if abs(z-definition['thickness_mm']) > 1e-9:
        raise ValueError('source copper/dielectric stack does not sum to board thickness')
    definition['stackup'] = stack
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(definition, indent=2, sort_keys=True)+'\n')
    clearance = profile.get('all_In1_copper_clearance_mm')
    rule_text = '(version 1)\n'
    if clearance:
        rule_text += (f'(rule "Conditional thick In1 copper"\n  (layer "In1.Cu")\n'
                      f'  (constraint clearance (min {clearance}mm))\n'
                      f'  (constraint track_width (min {clearance}mm)))\n')
    output.with_suffix('.kicad_dru').write_text(rule_text)
    receipt = {'status': 'DISPOSABLE SOURCE DEFINITION; not selected or qualified',
        'profile': profile_name, 'board_id': board_id,
        'canonical_definition_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'proposal_sha256': hashlib.sha256(proposal.read_bytes()).hexdigest(),
        'candidate_definition_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'nominal_remaining_dielectric_mm': definition['thickness_mm']-sum(profile['copper_thickness_mm'].values()),
        'fixed_outline_layers_hardware_keepouts_preserved': True}
    output.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('board_id'); parser.add_argument('profile')
    parser.add_argument('output', type=Path)
    parser.add_argument('--proposal', type=Path, default=Path('design/partition/rail-plane-proposals.json'))
    args = parser.parse_args()
    generate(args.board_id, args.proposal, args.profile, args.output)
