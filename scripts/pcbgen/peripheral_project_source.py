"""Deterministic complete PCB projects for the bounded O/EL prerequisites.

The original minimal schematic project stays retained. Board defaults come
from one pinned repository PCB template, with only declared related changes.
Expected bytes are derived before native loading and never rebound to output.
"""
import copy
import hashlib
import json
from pathlib import Path

# Complete Default record observed from the pinned 10.0.6 fresh BOARD in the
# retained O1-v1 native project. The constructor's whole record is checked,
# not merely its adjustable routing fields. This is native-tool behavior,
# not a fabricated physical/manufacturing property.
FRESH_DEFAULT_CLASS={'bus_width':12,'clearance':.2,'diff_pair_gap':.25,
    'diff_pair_via_gap':.25,'diff_pair_width':.2,'line_style':0,
    'microvia_diameter':.3,'microvia_drill':.1,'name':'Default',
    'pcb_color':'rgba(0, 0, 0, 0.000)','priority':2147483647,
    'schematic_color':'rgba(0, 0, 0, 0.000)','track_width':.2,
    'tuning_profile':'','via_diameter':.6,'via_drill':.3,'wire_width':6}


def derive(template_bytes,canonical_bytes,definition_bytes,destination):
    template=json.loads(template_bytes);canonical=json.loads(canonical_bytes);definition=json.loads(definition_bytes)
    if definition['layers']!=2 or not (definition['board_id']=='osc-stage-optical' or definition['board_id'].startswith('osc-octave-')):
        raise ValueError('exact peripheral two-layer definition required')
    if set(canonical)!={'meta','sheets','text_variables'} or canonical['meta']!={'filename':definition['board_id']+'.kicad_pro','version':1}:
        raise ValueError('canonical schematic-only project differs from its known source form')
    if Path(destination).name!=destination or not destination.endswith('.kicad_pro'):
        raise ValueError('destination must be a project basename')
    result=copy.deepcopy(template)
    result['meta']['filename']=destination
    result['sheets']=copy.deepcopy(canonical['sheets']);result['text_variables']=copy.deepcopy(canonical['text_variables'])
    # The PCB-only prerequisite has no editor-cached schematic root. Never
    # carry the template's JL root into another board's project. The actual
    # copied target schematic is separately retained and checked by parity.
    result['schematic']['top_level_sheets']=[]
    defaults=[c for c in template['net_settings']['classes'] if c['name']=='Default']
    if len(defaults)!=1:raise ValueError('complete template requires one Default class')
    classes=[];specs=definition['routing']['net_classes']
    if len(specs)!=3 or {c['name'] for c in specs}!={'Default','Ground','Rails'}:
        raise ValueError('exact three source net classes required')
    for spec in sorted(specs,key=lambda c:c['name']):
        cls=copy.deepcopy(defaults[0]);cls.update(name=spec['name'],priority=2147483647 if spec['name']=='Default' else -1,
            clearance=spec['clearance_mm'],track_width=spec['track_width_mm'],via_diameter=spec['via_diameter_mm'],via_drill=spec['via_drill_mm'])
        classes.append(cls)
    result['net_settings']['classes']=classes
    result['net_settings']['netclass_patterns']=[{'netclass':c['name'],'pattern':net} for c in specs if c['name']!='Default' for net in c['nets']]
    rules=result['board']['design_settings']['rules'];old=template['board']['design_settings']['rules']
    minimum=definition['routing']['min_track_width_mm']
    if minimum<old['min_track_width'] or rules['min_copper_edge_clearance']!=.5:
        raise ValueError('peripheral source cannot weaken original global width or edge rules')
    rules['min_track_width']=minimum
    expected_rules={**old,'min_track_width':minimum}
    if rules!=expected_rules:raise ValueError('unrelated project rules changed')
    # Prove the complete template transformation by reversing its explicit
    # changed paths, rather than comparing a handful of selected fields.
    reverse=copy.deepcopy(result)
    for key in ('meta','sheets','text_variables'):reverse[key]=copy.deepcopy(template[key])
    for key in ('classes','netclass_patterns'):reverse['net_settings'][key]=copy.deepcopy(template['net_settings'][key])
    reverse['schematic']['top_level_sheets']=copy.deepcopy(template['schematic']['top_level_sheets'])
    reverse['board']['design_settings']['rules']['min_track_width']=old['min_track_width']
    if reverse!=template:raise ValueError('unexpected complete project transformation')
    data=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode();sha=lambda b:hashlib.sha256(b).hexdigest()
    return data,{'template_sha256':sha(template_bytes),'canonical_project_sha256':sha(canonical_bytes),
        'definition_sha256':sha(definition_bytes),'expected_project_sha256':sha(data),'destination_basename':destination,
        'only_changed_template_paths':['/meta/filename','/sheets','/text_variables','/schematic/top_level_sheets','/net_settings/classes','/net_settings/netclass_patterns','/board/design_settings/rules/min_track_width'],
        'canonical_schematic_metadata_preserved':True,'project_format_version':result['meta']['version'],
        'global_minimum_track_width_mm':minimum,'global_copper_edge_clearance_mm':rules['min_copper_edge_clearance'],
        'all_unrelated_template_values_unchanged':True}


def fresh_sync_project(final_bytes,template_bytes):
    """Exact pinned fresh-BOARD constructor stage, before source classes.

KiCad 10.0.6 SaveBoard serializes its fresh Default-only net settings even
when a full source project was written first. This is an intermediate stage
only. All unrelated values stay identical to the final source expectation.
"""
    result=json.loads(final_bytes);template=json.loads(template_bytes)
    defaults=[c for c in template['net_settings']['classes'] if c['name']=='Default']
    if defaults!=[FRESH_DEFAULT_CLASS]:
        raise ValueError('template Default differs from the retained pinned constructor')
    if result['schematic']['top_level_sheets']:
        raise ValueError('peripheral PCB project must not retain another schematic root')
    result['net_settings']['classes']=copy.deepcopy(defaults)
    result['net_settings']['netclass_patterns']=[]
    return (json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
