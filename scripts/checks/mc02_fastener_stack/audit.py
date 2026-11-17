"""Conditional four-site axial stack arithmetic; no hardware acceptance."""
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).with_name('evidence.json')
RULED = 'design/stack/fixings/ruled-list.json'
THREAD = 'design/stack/fixings/threading-procedure.json'
STACK = 'design/stack/geometry/stack-candidate.json'
SITES = {'SLV-U1': ('JL', [74, 28]), 'SLV-U2': ('JR', [244, 24]),
         'SLV-L1': ('P', [93, 276]), 'SLV-L2': ('P', [244, 230])}
UNKNOWN = ['screw identity and length tolerance', 'assembled grip tolerance including compression',
           'washer exact identity and thickness tolerance', 'required thread protrusion',
           'nut finish/version discrepancy']


def number(value):
    if not isinstance(value, str):
        raise ValueError('decimal input must be a string')
    try:
        out = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('invalid decimal') from exc
    if not out.is_finite() or out < 0:
        raise ValueError('nonfinite or negative dimension')
    return out


def interval(lower, upper):
    lo, hi = number(lower), number(upper)
    if lo > hi:
        raise ValueError('reversed interval')
    return lo, hi


def residual(screw, grip, nut):
    """Signed W+P capacity, where W=washer thickness and P=protrusion.

    Input intervals are explicit assumptions of the caller; arithmetic conveys
    no source authority and does not establish a selected washer or required P.
    """
    sl, su = interval(*screw); gl, gu = interval(*grip); nl, nu = interval(*nut)
    return {'lower': str(sl-gu-nu), 'upper': str(su-gl-nl), 'unit': 'mm'}


def audit(evidence, root=ROOT):
    if set(evidence['sha256']) != {RULED, THREAD, STACK}:
        raise ValueError('incomplete source closure')
    for path, expected in evidence['sha256'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest() != expected:
            raise ValueError('source pin changed: '+path)
    handoff = evidence['nut_handoff']
    verified_sha = 'b31545f168c90a3bc2d44f06b0f0a3003a6aaeef002b4366e11a44230637af44'
    if (handoff['status'] != 'PRIMARY_DIMENSION_VERIFIED'
            or handoff['verified_pdf_sha256'] != verified_sha or handoff['expected_pdf_sha256'] != verified_sha
            or handoff['verified_pdf_bytes'] != 172371
            or handoff['material_finish'] != 'steel / zinc plate (reviewed DWG 4708)'
            or handoff['retained_catalog_finish'] != 'steel / nickel'
            or handoff['reviewed_drawing']['number'] != '4708'
            or handoff['reviewed_drawing']['thread'] != 'M3 x 0.5'
            or handoff['reviewed_drawing']['revision'] is not None
            or handoff['identity'] != 'Keystone 4708'
            or handoff['nominal_mm'] != '2.40' or handoff['tolerance_mm'] != '0.25'
            or handoff['finish_disposition'] != 'UNRESOLVED_VERSION_DISCREPANCY'):
        raise ValueError('reviewed source contract changed; separate source review required')
    nom = number(handoff['nominal_mm']); tol = number(handoff['tolerance_mm'])
    nut = (str(nom-tol), str(nom+tol))
    ruled = json.loads((root/RULED).read_text())['sleeves']
    if len(ruled) != 4 or {r['id'] for r in ruled} != set(SITES):
        raise ValueError('four active sleeve identities changed')
    screws = json.loads((root/THREAD).read_text())['screws']
    planes = json.loads((root/STACK).read_text())['candidate']['planes']
    amendment=evidence['nut_source_amendment']
    if (screws['nut_height_mm']!=amendment['expected_height']
            or screws.get('nut_height_source')!=amendment['expected_source']):
        raise ValueError('canonical nut source differs from reviewed supplement')
    canonical=screws['nut_height_source']
    if (canonical['verified_pdf_sha256']!=handoff['verified_pdf_sha256']
            or canonical['verified_pdf_bytes']!=handoff['verified_pdf_bytes']
            or canonical['drawing_date']!=handoff['reviewed_drawing']['date_iso']
            or canonical['identity']!=handoff['identity']
            or canonical['finish_disposition']!=handoff['finish_disposition']
            or Decimal(str(screws['nut_height_mm']['nominal']))!=nom
            or Decimal(str(screws['nut_height_mm']['tolerance']))!=tol):
        raise ValueError('canonical nut and supplemental dimension identity disagree')
    working = screws['working_figure']
    if working['length_mm'] != 25 or working['status'] != 'ASSUMED' or working['countersunk']:
        raise ValueError('assumed screw contract changed')
    classes = {r['class']: r for r in screws['classes']}
    rows = []
    for site in ruled:
        board, xy = SITES[site['id']]
        if site['front_board'] != board or site['xy'] != xy:
            raise ValueError('fixed site changed')
        grip = Decimal(str(planes[board]['face_z_mm']))-Decimal(str(planes['K']['rear_z_mm']))
        cls = 'short sleeve, P to K' if board == 'P' else 'long sleeve, JL or JR to K'
        record = classes[cls]
        if grip != Decimal(str(record['grip_mm'])) or Decimal('25')-grip != Decimal(str(record['thread_behind_K_rear_mm'])):
            raise ValueError('plane/class/protrusion source mismatch')
        rows.append({'site': site['id'], 'front_board': board, 'xy_mm': xy,
                     'nominal_grip_mm': str(grip), 'nominal_screw_mm': '25',
                     'reviewed_nut_interval_mm': list(nut),
                     'conditional_washer_plus_protrusion_capacity_mm': residual(('25','25'),(str(grip),str(grip)),nut),
                     'constraint': 'W + P <= L - G - N; W and required P remain unknown',
                     'worst_case_washer_limit_mm': None,
                     'assembly_verdict': 'NOT_SHOWN', 'unknowns': list(UNKNOWN)})
    return {'engineering_commit': evidence['engineering_commit'], 'source_commit': evidence['source_commit'],
            'procedure_amendment': evidence['procedure_amendment'], 'nut_source_amendment': evidence['nut_source_amendment'], 'inputs_sha256': evidence['sha256'],
            'nut_handoff': handoff, 'sites': rows,
            'scope': 'Conditional arithmetic with nominal screw/grip and drawing-verified nut bounds only; finish/version remains unresolved. '
                     'Zero screw/grip tolerance is a sensitivity assumption, not a sourced guarantee. '
                     'Positive residual is not washer permission, guaranteed protrusion, strength, thread engagement, '
                     'creep, rear-envelope qualification, hardware adoption or manufacturing acceptance.'}


if __name__ == '__main__':
    print(json.dumps(audit(json.loads(EVIDENCE.read_text())), indent=2))
