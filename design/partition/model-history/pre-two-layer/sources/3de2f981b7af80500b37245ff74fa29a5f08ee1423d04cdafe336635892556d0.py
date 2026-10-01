"""Explicit source-owned native stack metadata for an unselected PCB draft.

Only the setup/stackup child changes. No material permittivity, loss tangent,
factory laminate or qualified process is inferred from nominal layer depths.
"""
import hashlib
import math
import re
from scripts.pcbgen.uuid_tools import top_level_spans


def stack_block(definition):
    rows=definition['stackup'];copper=[];total=0.;lines=['(stackup']
    if len(rows)!=7 or [rows[i]['layer'] for i in (0,2,4,6)]!=['F.Cu','In1.Cu','In2.Cu','B.Cu']:
        raise ValueError('source copper and dielectric bands must alternate')
    dielectric=0
    for row in rows:
        name=row['layer']
        if name.endswith('.Cu'):
            copper.append(name);thickness=row['copper_thickness_mm'];kind='copper'
        else:
            dielectric+=1;name='dielectric '+str(dielectric)
            thickness=row['thickness_mm'];kind='dielectric'
        if not math.isfinite(thickness) or thickness<=0:raise ValueError('positive finite stack thickness required')
        total+=thickness
        lines.extend([f'\t(layer "{name}"',f'\t\t(type "{kind}")',f'\t\t(thickness {thickness:.12g})'])
        if kind=='dielectric':lines.append('\t\t(material "UNSELECTED conditional pressed dielectric")')
        lines.append('\t)')
    if copper!=['F.Cu','In1.Cu','In2.Cu','B.Cu'] or dielectric!=3:
        raise ValueError('this source requires exactly four ordered copper and three dielectric bands')
    if abs(total-definition['thickness_mm'])>1e-10:raise ValueError('source stack does not sum to board thickness')
    return '\n'.join(lines+[')'])


def apply(text,definition):
    layers=[text[a:b] for a,b in top_level_spans(text) if text[a:b].startswith('(layers')]
    if len(layers)!=1 or re.findall(r'\(\d+\s+"([^"]+\.Cu)"',layers[0])!=['F.Cu','In1.Cu','In2.Cu','B.Cu']:
        raise ValueError('source metadata requires the existing four native copper layers')
    general=[text[a:b] for a,b in top_level_spans(text) if text[a:b].startswith('(general')]
    if len(general)!=1:raise ValueError('one native general block required')
    thickness=re.search(r'\(thickness\s+([0-9.eE+-]+)\)',general[0])
    if thickness is None or abs(float(thickness[1])-definition['thickness_mm'])>1e-10:
        raise ValueError('source stack cannot change nominal native board thickness')
    setup=[(a,b) for a,b in top_level_spans(text) if text[a:b].startswith('(setup')]
    if len(setup)!=1:raise ValueError('one native setup block required')
    a,b=setup[0];old=text[a:b]
    existing=[(x,y) for x,y in top_level_spans(old) if old[x:y].startswith('(stackup')]
    if len(existing)>1:raise ValueError('duplicate native stackup metadata')
    fragment=stack_block(definition)
    indented=fragment.replace('\n','\n\t\t')
    if existing:
        x,y=existing[0];new=old[:x]+indented+old[y:]
    else:new=old[:len('(setup')]+ '\n\t\t'+indented+old[len('(setup'):]
    updated=text[:a]+new+text[b:]
    return updated,{'status':'UNSELECTED nominal native stack metadata; physical qualification NOT RUN #65',
        'source_owned_exception':'Only setup/stackup is added or replaced; all other native text is preserved',
        'prior_stackup_sha256':[hashlib.sha256(old[x:y].encode()).hexdigest() for x,y in existing],
        'stackup_sha256':hashlib.sha256(fragment.encode()).hexdigest(),
        'native_type_scope':'Dielectric is a neutral nominal band label, not a selected core/prepreg construction or material guarantee.',
        'editor_default_scope':'KiCad 10.0.6 may serialize epsilon_r 4.5 and loss_tangent 0.02 when resaving omitted dielectric properties. These editor defaults are not source material facts and are not used by the DC conductor model. This generator emits neither value.'}
