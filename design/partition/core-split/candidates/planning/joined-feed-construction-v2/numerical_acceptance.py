"""Check reported solver diagnostics; a process exit alone is not acceptance.

This module performs no solve and never changes a tolerance or input. Passing
these diagnostics does not establish source/load, geometry or board acceptance.
"""
import math


def assess(phase, result, config):
    limits = config.get('numerical_tolerances', {})
    if not isinstance(limits, dict):
        limits = {}
    checks = []
    failures = []

    def check(name, value, tolerance):
        limit = limits.get(tolerance)
        valid_limit = type(limit) in (int, float) and math.isfinite(limit) and limit > 0
        valid_value = type(value) in (int, float) and math.isfinite(value) and value >= 0
        passed = valid_limit and valid_value and value <= limit
        checks.append({'name': name, 'value': value if valid_value else None,
                       'limit': limit if valid_limit else None, 'tolerance': tolerance,
                       'passed': passed})
        if not passed:
            failures.append(name + ': missing/nonfinite diagnostic or declared limit exceeded')

    if phase == 'reduce':
        reported = result.get('checks', {})
        if not isinstance(reported, dict):
            reported = {}
        for name, tolerance in (
            ('reciprocity_relative', 'reciprocity_relative'),
            ('load_solve_residual_relative', 'kcl_relative'),
            ('interface_solve_residual_relative', 'kcl_relative'),
        ):
            check(name, reported.get(name), tolerance)
    elif phase == 'dpoint':
        check('solve_residual_relative', result.get('solve_residual_relative'), 'kcl_relative')
    elif phase == 'couple':
        states = result.get('checks', {})
        if not isinstance(states, dict):
            states = {}
        expected = {'all-present'}
        if result.get('net') == 'AGND':
            returns = config.get('return_states', {})
            for group in ('single', 'double'):
                if not returns.get(group):
                    failures.append('configured return-state group missing: ' + group)
                for removed in returns.get(group, []):
                    expected.add('remove-' + '-'.join('W' + str(w) for w in removed))
        elif result.get('net') not in ('+12V', '-12V', '+5V'):
            failures.append('coupled net missing or unsupported')
        if set(states) != expected or type(result.get('states')) is not int or result['states'] != len(states):
            failures.append('coupled state diagnostics missing or count differs')
        for state, reported in states.items():
            if not isinstance(reported, dict):
                reported = {}
            for name, tolerance in (
                ('global_kcl_relative', 'kcl_relative'),
                ('max_free_node_kcl_relative', 'kcl_relative'),
                ('driving_point_solve_residual', 'kcl_relative'),
                ('energy_minus_load_work_relative', 'energy_relative'),
            ):
                check(state + '.' + name, reported.get(name), tolerance)
            if reported.get('nonnegative_energy') is not True:
                failures.append(state + '.nonnegative_energy: not proven')
    else:
        raise ValueError('unsupported numerical phase: ' + phase)
    return {'schema': 'e16-reported-numerical-checks-v1', 'phase': phase,
            'status': 'FAIL' if failures else 'PASS REPORTED NUMERICAL CHECKS ONLY',
            'checks': checks, 'failures': failures, 'electrical_acceptance': False}
