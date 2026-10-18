"""Source-only reconciliation. No hardware maximum is inferred."""
import hashlib
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / 'design/architecture-278/implementation'

def read(path):
    return json.loads(path.read_text())

def build():
    old = read(BASE / 'stage34/design-input.json')['current_budget']['links']
    inv = read(BASE / 'stage26/candidate-inventory.json')
    rows = []
    for link, conductors in old.items():
        for row in conductors:
            before = after = fault = 0.0
            changes = []
            for t in row['terms']:
                if t['kind'] == 'unknown':
                    continue
                n = t['count']
                value = t['V'][1] / t['R_ohm'][1] * n if t['kind'] == 'V_over_R' else t['A'][1] * n
                revised = value
                if t['term'].startswith('magnitude senses') or t['term'].startswith('clip LED'):
                    refs = ['R7130','R7131','R7132'] if t['term'].startswith('magnitude') else ['R7135']
                    revised = sum(t['V'][1] / (inv['selections'][r]['ratings']['value_SI'] * (1-inv['selections'][r]['ratings']['tolerance_fraction'])) for r in refs)
                    changes.append({'term': t['term'], 'candidate_refs': refs, 'before_A': value, 'after_initial_tolerance_A': revised})
                before += value
                after += revised
                fault += t.get('fault_A',0)*n
            # Comparator allowance is a scenario, never an interpolated guarantee.
            lm = 2 * 0.0008 if link == 'J-PWR' and row['pin'] in ('1','2') else 0.0
            rows.append({'link': link, 'pin': row['pin'], 'net': row['net'],
                         'before_conditional_A': before, 'after_candidate_resistors_A': after,
                         'LM393_36V_transfer_allowance_A': lm,
                         'scenario_with_LM_allowance_A': after+lm,
                         'inherited_fault_increment_A': fault,
                         'scenario_plus_inherited_fault_A': after+lm+fault if fault else None,
                         'guaranteed_conductor_max_A': None,
                         'unknown_terms_retained': [t['term'] for t in row['terms'] if t['kind']=='unknown'],
                         'changes': changes})
    paths = ['stage34/design-input.json','stage26/candidate-inventory.json']
    bindings = {p: hashlib.sha256((BASE/p).read_bytes()).hexdigest() for p in paths}
    refs = ['U7102','U7103','U7104','U7105','U7106','U7107','U7108','U7109','R7105','R7106','R7109','R7110','R7130','R7131','R7132','R7135']
    return {'status':'CONDITIONAL_SOURCE_RECONCILIATION_ONLY', 'canonical_changed':False,
            'source_sha256':bindings, 'pin_bindings':{r:inv['packages'][r] for r in refs},
            'resistor_candidates':{r:inv['selections'][r] for r in ['R7130','R7131','R7132','R7135']},
            'rows':rows}

def encoded():
    return json.dumps(build(),indent=2,sort_keys=True)+'\n'

if __name__ == '__main__':
    result=encoded()
    if '--check' in sys.argv:
        if (HERE/'ledger.json').read_text()!=result:
            raise SystemExit('FAIL: ledger stale')
        print('PASS deterministic ledger and source bindings')
    else:
        (HERE/'ledger.json').write_text(result)
