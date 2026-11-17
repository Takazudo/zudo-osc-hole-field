"""Source-only applicability contract; never imports or executes numerical models."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PDF = '.circuit-cache/sources/manufacturer-transfer-20261118/1st one.pdf'
INPUT = 'design/stack/link-electrical/inputs.json'
KERNEL = 'scripts/stack/link_electrical/link_electrical.py'
RATIOS = 'scripts/stack/link_electrical/link_ratios.py'
FACTS = {
    'manufacturer': 'Molex', 'mpn': '150200075', 'document': 'SD-15020-001', 'revision': 'F',
    'contacts': 8, 'type': 'A', 'length_mm': ['49', '53'], 'width_mm': ['0.27', '0.33'],
    'copper_nominal_mm': '0.10', 'copper_interval_mm': None, 'rho_ohm_m_of_T': None,
    'effective_dielectric': None, 'end_equivalent_mm': None, 'assembled_contact_resistance_ohm': None,
}


def validate_facts(facts):
    if facts != FACTS:
        raise ValueError('reviewed source facts changed or unknown/nominal value promoted')


def conditional_factor(facts, assumed_thickness_mm=None):
    validate_facts(facts)
    if assumed_thickness_mm is None:
        return None
    if assumed_thickness_mm != '0.10':
        raise ValueError('only explicit nominal-thickness counterfactual is declared')
    t = Fraction(assumed_thickness_mm)
    low = Fraction(facts['length_mm'][0]) / (Fraction(facts['width_mm'][1]) * t)
    high = Fraction(facts['length_mm'][1]) / (Fraction(facts['width_mm'][0]) * t)
    return {'assumption': 't = 0.10 mm fixed exactly; ignores unknown thickness tolerance',
            'quantity': 'L/(w*t)', 'unit': '1/mm',
            'exact_rational_interval': [str(low), str(high)],
            'interpretation': 'Conditional geometry only, not guaranteed product resistance bounds'}


def contract(facts, inputs):
    validate_facts(facts)
    cable = inputs['cable']; r = inputs['conductor_resistance_mohm']['pitch_0_5']
    if inputs['ds62']['pitch'] != 'pitch_0_5' or cable['pitch_0_5']['conductor_thickness_mm'] != .035:
        raise ValueError('legacy model selection changed')
    if [r['min'], r['max']] != [65.3, 106.4]:
        raise ValueError('legacy independent resistance interval changed')
    matrix = [
        {'model': 'capacitance_matrix / cable_matrices', 'locator': KERNEL+':capacitance_matrix; '+RATIOS+':cable_matrices',
         'consumes': ['pitch/centers', 'width', 'eps_eff', 'length + 2*end_equivalent'],
         'does_not_consume': ['copper thickness', 'rho(T)'],
         'limitation': 'Coplanar zero-thickness strips in homogeneous medium. Changing thickness does not change C; dielectric sweep does not validate finite-thickness applicability.'},
        {'model': 'lp_matrix / effective_mutual', 'locator': KERNEL+':lp_self, lp_mutual, lp_matrix, effective_mutual',
         'consumes': ['length + 2*end_equivalent', 'width', 'thickness', 'pitch/centers', 'ground-return window'],
         'does_not_consume': ['rho(T)', 'dielectric'],
         'limitation': 'Nonlinear partial-inductance functions and solved return split. Sampling 49/53 mm is not a proven interval extremum bound.'},
        {'model': 'ground_paths_at', 'locator': RATIOS+':ground_paths_at',
         'consumes': ['separate S-FLEX conductor resistance min/max', 'length/50', 'two contact resistances'],
         'does_not_consume': ['width', 'copper thickness', 'rho(T)', 'end-equivalent coupling length'],
         'limitation': 'Changing cable geometry alone leaves legacy resistance parameters unchanged; not a Molex resistance model.'},
        {'model': 'victim_peak', 'locator': KERNEL+':victim_peak',
         'consumes': ['Cm', 'Cv_total', 'M_eff', 'aggressor edge/load', 'victim source resistance/input capacitance'],
         'does_not_consume': ['Molex identity or qualification'],
         'limitation': 'Nonlinear transfer and absolute inductive term do not certify full coupled parameter intervals from endpoint samples.'},
    ]
    out = {'status': 'SOURCE_TO_MODEL_APPLICABILITY_ONLY', 'candidate': facts,
           'parameter_consumption': matrix,
           'legacy': {'geometry': cable['pitch_0_5'], 'eps_eff': cable['eps_eff'],
                      'end_equivalent_mm': cable['end_equivalent_mm'],
                      'conductor_resistance_50mm_mohm': r,
                      'contact': inputs['contact']},
           'resistance': {'symbolic': 'R_conductor = rho(T) * L / (w * t)',
                          'units': 'rho in ohm*m; L,w,t in m; R in ohm; contacts excluded',
                          'guaranteed_product_interval_ohm': None,
                          'conditional_geometry': conditional_factor(facts, '0.10')},
           'missing_for_product_model': ['copper thickness tolerance', 'rho(T) and temperature domain',
                 'finite-thickness/effective-dielectric applicability', 'end-region equivalent/coupling data',
                 'assembled cable/contact resistance applicability', 'full interval extrema proof including return-network response'],
           'prior_51mm_result_scope': 'Unchanged LX-based material inputs, nominal length-only counterfactual; not Molex qualification',
           'product_qualified': False, 'guaranteed_electrical_bounds': None,
           'numerical_study': 'NOT_RUN', 'native': 'NOT_RUN',
           'holds': ['DRC', 'zone fill', 'formal hardware adoption', 'manufacturing']}
    validate_output(out)
    return out


def validate_output(result):
    if result['product_qualified'] is not False or result['guaranteed_electrical_bounds'] is not None:
        raise ValueError('product qualification or guaranteed electrical bounds forbidden')
    if result['resistance']['guaranteed_product_interval_ohm'] is not None:
        raise ValueError('unknown thickness/rho cannot yield guaranteed product resistance interval')


def audit(root=ROOT):
    evidence = json.loads((HERE/'evidence.json').read_text())
    required = {PDF, INPUT, KERNEL, RATIOS, 'scripts/checks/mc02_length_sensitivity/study.py',
                'scripts/checks/mc02_molex_model_inputs/audit.py'}
    if set(evidence['sha256']) != required:
        raise ValueError('source closure incomplete')
    for name, sha in evidence['sha256'].items():
        path = root/name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError('source drift: '+name)
    result = contract(evidence['facts'], json.loads((root/INPUT).read_text()))
    result.update({'source_commit': evidence['source_commit'], 'engineering_commit': evidence['engineering_commit'],
                   'source_locators': evidence['locators'], 'sha256': evidence['sha256']})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path); args = parser.parse_args()
    # Reserve output before reading inputs; preserve failure evidence without overwriting.
    stream = args.output.open('x') if args.output else None
    try:
        result = audit()
    except Exception as exc:
        if stream:
            json.dump({'status': 'FAILED', 'error': str(exc)}, stream, indent=2); stream.close()
        raise
    if stream:
        json.dump(result, stream, indent=2); stream.write('\n'); stream.close()
    else:
        print(json.dumps(result, indent=2))
