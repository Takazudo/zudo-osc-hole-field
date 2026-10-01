"""Derive exact P candidate project bytes before native class application.

The pinned bare project has one Default class. KiCad's source-defined class
application also serializes the destination project filename. All other
project settings remain exact; a candidate's current bytes are never used as
the expected source authority.
"""
import copy
import hashlib
import json
from pathlib import Path


def derive(bare_bytes, definition_bytes, destination_name):
    original = json.loads(bare_bytes)
    definition = json.loads(definition_bytes)
    if definition['board_id'] != 'osc-control' or Path(destination_name).name != destination_name or not destination_name.endswith('.kicad_pro'):
        raise ValueError('Exact P source and destination project basename required')
    source_classes = definition['routing']['net_classes']
    if {row['name'] for row in source_classes} != {'Default', 'Ground', 'Rails'} or len(source_classes) != 3:
        raise ValueError('Expected the three explicit P source net classes')
    current = original['net_settings']['classes']
    if len(current) != 1 or current[0]['name'] != 'Default' or original['net_settings']['netclass_patterns']:
        raise ValueError('Original bare P project has unexpected class authority')
    default = current[0]
    # These retained bare class fields match the pinned KiCad 10.0.6 NETCLASS
    # constructor, independently checked against the stopped native v1 output.
    # Reject differing style/default semantics rather than silently copying a
    # custom Default class into new native classes.
    constructor = {'bus_width': 12, 'diff_pair_gap': .25, 'diff_pair_via_gap': .25,
        'diff_pair_width': .2, 'line_style': 0, 'microvia_diameter': .3,
        'microvia_drill': .1, 'pcb_color': 'rgba(0, 0, 0, 0.000)',
        'schematic_color': 'rgba(0, 0, 0, 0.000)', 'tuning_profile': '', 'wire_width': 6}
    adjustable = {'name', 'priority', 'clearance', 'track_width', 'via_diameter', 'via_drill'}
    if set(default) != set(constructor) | adjustable or any(default[key] != value for key, value in constructor.items()) or default['priority'] != 2147483647:
        raise ValueError('Bare class differs from the retained pinned native constructor')
    result = copy.deepcopy(original)
    result['meta']['filename'] = destination_name
    classes = []
    for row in sorted(source_classes, key=lambda value: value['name']):
        native = copy.deepcopy(default)
        native.update(name=row['name'], priority=2147483647 if row['name'] == 'Default' else -1,
            clearance=row['clearance_mm'], track_width=row['track_width_mm'],
            via_diameter=row['via_diameter_mm'], via_drill=row['via_drill_mm'])
        classes.append(native)
    result['net_settings']['classes'] = classes
    # Preserve the declared class/net order used by apply_classes, rather than
    # reordering regex pattern precedence.
    result['net_settings']['netclass_patterns'] = [{'netclass': row['name'], 'pattern': net}
        for row in source_classes if row['name'] != 'Default' for net in row['nets']]
    expected = (json.dumps(result, indent=2, sort_keys=True)+'\n').encode()
    sha = lambda value: hashlib.sha256(value).hexdigest()
    return expected, {'status': 'Exact source-derived P project; native serialization must match these precomputed bytes',
        'bare_project_sha256': sha(bare_bytes), 'definition_sha256': sha(definition_bytes),
        'destination_basename': destination_name, 'expected_project_sha256': sha(expected),
        'only_changed_paths': ['/meta/filename', '/net_settings/classes', '/net_settings/netclass_patterns'],
        'board_design_rules_unchanged': result['board']['design_settings']['rules'] == original['board']['design_settings']['rules'],
        'classes': classes, 'patterns': result['net_settings']['netclass_patterns']}
