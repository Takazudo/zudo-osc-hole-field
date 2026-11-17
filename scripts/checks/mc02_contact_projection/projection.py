"""Relative manufacturer-pattern vectors on virtual endpoint bases, not footprints."""
import argparse
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
MANIFEST=Path(__file__).with_name('manifest.json')
PDF_SHA='c3257beed2331e5c95e176bc28441b04b804301a44c11b462e486fb5cc649d07'
GATE='design/stack/geometry/links/link-gate.json'
MAPPING='scripts/checks/mc02_connector_mapping/mapping.py'
COUNTS=(8,14,26,40)
PROJECT_SUPPLIER_CODES={8:'C597995',14:'C5378715',26:'C202113',40:'C202114'}
CODES={8:'CL586-0744-5-55',14:'CL586-0533-0-55',26:'CL586-0576-2-55',40:'CL586-0527-7-55'}


def verify_manifest(m, root):
    if set(m['sha256'])!={GATE,MAPPING,'scripts/checks/mc02_connector_mapping/manifest.json'}:
        raise ValueError('source closure changed')
    for p,h in m['sha256'].items():
        if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h:
            raise ValueError('source pin changed: '+p)
    source=m['manufacturer']
    if (source['status']!='VERIFIED_PRIMARY_DOCUMENT' or source['verified_pdf_sha256']!=PDF_SHA
            or source['verified_pdf_bytes']!=1059562 or source['document']!='EDC3-150229-11'):
        raise ValueError('manufacturer source identity changed')
    if source['open_height_mm']!={'value':'4.8','kind':'reference_dimension','guaranteed_maximum':False}:
        raise ValueError('reference open height is not a maximum')
    if source['registration']!='NOT_ESTABLISHED':
        raise ValueError('absolute registration is not supplied')
    if set(m['variants'])!={str(n) for n in COUNTS}:raise ValueError('variant set changed')
    for n in COUNTS:
        row=m['variants'][str(n)];a=Decimal(n-1)/2
        if (row['sheet']!=(1 if n<=34 else 2) or row['code']!=CODES[n]
                or Decimal(row['A'])!=a or Decimal(row['F'])!=a+2 or Decimal(row['G'])!=a+Decimal('5.6')):
            raise ValueError('source dimension/sheet correspondence changed')


def pattern(n):
    if type(n) is not int or n not in COUNTS:raise ValueError('unsupported exact contact count')
    a=Decimal(n-1)/2;f=a+2;g=a+Decimal('5.6')
    return {'source_sheet':1 if n<=34 else 2,'source_table_sheet':5,
            'contacts':[{'contact':i,'relative_local_mm':[float(-a/2+Decimal(i-1)/2),0.0]}
                        for i in range(1,n+1)],
            'nominal_pad_size_mm':[0.3,1.3],
            'nominal_tab_rectangles_local_mm':[[float(-g/2),2.15,float(-f/2),4.35],
                                               [float(f/2),2.15,float(g/2),4.35]],
            'dimension_scope':'Nominal derived pattern only. Tolerances are not propagated into clearance acceptance.'}


def basis(direction, face, mirrored_source_view=False):
    if len(direction)!=2 or tuple(direction) not in ((1,0),(-1,0),(0,1),(0,-1)):
        raise ValueError('cardinal field-to-slot direction required')
    if face not in ('F','B') or type(mirrored_source_view) is not bool:
        raise ValueError('explicit face/view required')
    dx,dy=direction
    # Declared conditional convention: F view unreflected; B lateral axis reflected.
    parity=(1 if face=='F' else -1)*(-1 if mirrored_source_view else 1)
    x=[parity*dy,-parity*dx];y=[dx,dy]
    return {'x_basis':x,'y_basis':y,'matrix_columns_xy':[[x[0],y[0]],[x[1],y[1]]],
            'determinant':parity,'source_view':'mirrored_copy' if mirrored_source_view else 'component_top',
            'status':'CONDITIONAL_VIEW_CONVENTION_NOT_PHYSICAL_ORIENTATION'}


def relative_vector(point,direction,face,mirrored_source_view=False):
    b=basis(direction,face,mirrored_source_view)
    x,y=point
    if mirrored_source_view:x=-x  # Reflect BOTH the source coordinates and its basis.
    return [round(b['x_basis'][j]*x+b['y_basis'][j]*y,4) for j in (0,1)]


def project_endpoint(e):
    n=e['contacts'];p=pattern(n);d=e['direction_from_field_toward_slot'];face=e['board_face']
    if e['connector_identity']!=f'FH12-{n}S-0.5SH(55), {PROJECT_SUPPLIER_CODES[n]}':raise ValueError('exact connector mismatch')
    if (e['physical_mapping_status']!='NOT_ESTABLISHED' or e['pad1_panel_mm'] is not None
            or e['footprint_rotation_deg'] is not None):
        raise ValueError('physical mapping requires a different reviewed contract')
    contacts=[{'manufacturer_contact':x['contact'],
               'relative_panel_vector_mm':relative_vector(x['relative_local_mm'],d,face)} for x in p['contacts']]
    return {'endpoint_id':e['endpoint_id'],'link_id':e['link_id'],'endpoint':e['endpoint'],
            'board':e['board'],'board_face':face,'contacts':n,'connector_identity':e['connector_identity'],
            'manufacturer_code':CODES[n],'source_pattern':p,'conditional_basis':basis(d,face),
            'field_to_slot_direction':d,'field_center_panel_mm':e['field_center_panel_mm'],
            'field_center_scope':'Virtual field center is NOT the registered signal-row midpoint.',
            'manufacturer_contacts_relative_vectors':contacts,
            'logical_positions':e['logical_positions'],'logical_to_physical_contact_mapping':'NOT_ESTABLISHED',
            'row_midpoint_offset_from_field_center_mm':None,'row_midpoint_panel_mm':None,
            'physical_pad1_local_mm':None,'physical_pad1_panel_mm':None,'physical_footprint_rotation_deg':None,
            'physical_end_to_end_cable_parity':'UNESTABLISHED',
            'parametric_equation':'P_i = field_center + unknown_row_midpoint_offset + conditional_basis * local_contact_i',
            'registration_missing':'A reviewed registration from the virtual courtyard-level body field to the manufacturer signal-pad row; physical footprint origin/face/rotation and cable fold/material frame are not instantiated.',
            'assumptions':['Manufacturer component-top view used; x right and y toward entry.',
                           'Local y is conditionally aligned to the virtual field-to-slot vector.',
                           'F reference view is unreflected; B view reflects the lateral axis. This is an explicit chosen convention, not observed board orientation.',
                           'Cable sheet3 contact1-right depiction is not copied onto this top-view basis or used to infer end-to-end continuity.']}


def run(root=ROOT):
    m=json.loads(MANIFEST.read_text());verify_manifest(m,root)
    spec=importlib.util.spec_from_file_location('_mc02_endpoint_mapping_for_projection',root/MAPPING)
    mapping=importlib.util.module_from_spec(spec);spec.loader.exec_module(mapping)
    links=[r for r in json.loads((root/GATE).read_text())['links'] if not r.get('gone')]
    if len(links)!=61 or len({r['id'] for r in links})!=61 or not all(r.get('placed') for r in links):
        raise ValueError('61 unique placed virtual links required')
    endpoints=[project_endpoint(e) for link in links for e in mapping.endpoint_rows(link)]
    verify_manifest(m,root)
    return {'engineering_commit':m['engineering_commit'],'inputs_sha256':m['sha256'],
            'manufacturer':m['manufacturer'],'virtual_endpoints':len(endpoints),'physical_mappings_established':0,
            'endpoints':endpoints,'scope':'Relative parametric source correspondence only; no physical footprint, absolute pad registration, cable parity, mounted access, open-envelope guarantee or hardware acceptance.'}


def verify_pdf(path):
    raw=Path(path).read_bytes()
    if len(raw)!=1059562 or hashlib.sha256(raw).hexdigest()!=PDF_SHA:
        raise ValueError('manufacturer PDF bytes mismatch')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-pdf',type=Path)
    args=p.parse_args()
    if args.source_pdf:verify_pdf(args.source_pdf)
    print(json.dumps(run(),indent=2))
