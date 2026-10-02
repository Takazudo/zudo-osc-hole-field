"""Derive the adapter's complete rule configuration from a retained native base."""
import copy
import json
from pathlib import Path

TEMPLATE=Path('scripts/pcbgen/fixtures/octave-project-template.json')
BASE_COMMIT='b8795bfbceaeb13e8e3f6d29d9ef57729299fd68'
BASE_PATH='boards/osc-jack-left/osc-jack-left.kicad_pro'


def expected_configuration(template_bytes,routing):
    template=json.loads(template_bytes)
    design=copy.deepcopy(template['board']['design_settings'])
    design['rules']['min_track_width']=routing['min_track_width_mm']
    net=copy.deepcopy(template['net_settings'])
    default=next(c for c in net['classes'] if c['name']=='Default')
    classes=[]
    for spec in routing['net_classes']:
        row=copy.deepcopy(default)
        row['name']=spec['name'];row['priority']=2147483647 if spec['name']=='Default' else -1
        for src,dst in [('track_width_mm','track_width'),('clearance_mm','clearance'),('via_diameter_mm','via_diameter'),('via_drill_mm','via_drill')]:row[dst]=spec[src]
        classes.append(row)
    net['classes']=classes
    net['netclass_patterns']=[{'netclass':s['name'],'pattern':n} for s in routing['net_classes'] if s['name']!='Default' for n in s['nets']]
    return design,net


def verify_project(project,template_bytes,routing):
    design,net=expected_configuration(template_bytes,routing)
    if project['board']['design_settings']!=design:raise ValueError('complete adapter design rules/severities/exclusions differ')
    if project['net_settings']!=net:raise ValueError('complete adapter net classes/assignments differ')
