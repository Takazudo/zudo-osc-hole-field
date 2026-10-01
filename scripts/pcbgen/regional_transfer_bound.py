"""Regional reciprocal-transfer bounds without subtracting private diagonals.

Supplied regions must be a disjoint complete partition of one physical
conductor domain, with compatible conserved source/observation current trials.
This arithmetic helper checks ID coverage and energy consistency; it cannot
establish those geometric/physical premises or admit a manufactured board.
"""
from fractions import Fraction
from scripts.pcbgen.observation_support_bound import rational, sqrt_upper, upward, covered_rows


def downward(value):
    return -upward(-value)


def regional_bounds(*, region_ids, common_region_ids, regions,
                    source_energy_upper, source_energy_lower,
                    observation_energy_upper, observation_energy_lower):
    """Enclose physical regional integrals rho*J_source*J_observation.

    Trial current-field errors in the complete energy norm are at most
    sqrt(U_source-L_source) and sqrt(U_observation-L_observation). On a
    region union W, the error in the trial cross product is bounded by

      sqrt(U_source,W * gap_observation)
      + sqrt(U_observation,W * gap_source)
      + sqrt(gap_source * gap_observation).

    The last term is charged once for a union, not subtracted as private
    access uncertainty. Regional source/observation energies are outward
    upper bounds. They must sum to at most the supplied complete trial
    upper energies (which may also retain global numerical allowances).
    """
    rows = covered_rows(region_ids, regions, 'physical region')
    common = list(common_region_ids)
    if not rows or not common or len(set(common)) != len(common) or not set(common) <= set(rows):
        raise ValueError('nonempty unique common region identities inside full partition required')
    us = rational(source_energy_upper, 'source energy upper', True)
    ls = rational(source_energy_lower, 'source energy lower')
    ub = rational(observation_energy_upper, 'observation energy upper', True)
    lb = rational(observation_energy_lower, 'observation energy lower')
    ds, db = us-ls, ub-lb
    if min(ds,db) < 0:
        raise ValueError('negative complete current witness gap')
    parsed = {}
    for key, row in rows.items():
        try:
            a = rational(row['source_energy_upper'], key+' source regional energy', True)
            b = rational(row['observation_energy_upper'], key+' observation regional energy', True)
            lo = rational(row['trial_cross_lower'], key+' trial cross lower')
            hi = rational(row['trial_cross_upper'], key+' trial cross upper')
        except KeyError as exc:
            raise ValueError(key+': missing regional witness') from exc
        if lo > hi:
            raise ValueError(key+': inverted trial cross interval')
        # A reported cross interval must intersect its Cauchy envelope. Larger
        # intervals are permitted; a wholly inconsistent interval is refused.
        norm = sqrt_upper(a*b)
        if lo > norm or hi < -norm:
            raise ValueError(key+': trial cross interval contradicts regional energies')
        parsed[key] = (a,b,lo,hi)
    if sum(x[0] for x in parsed.values()) > us or sum(x[1] for x in parsed.values()) > ub:
        raise ValueError('regional upper energies exceed supplied complete trial upper')

    def enclose(keys):
        values=[parsed[key] for key in keys]
        a=sum((x[0] for x in values),Fraction(0));b=sum((x[1] for x in values),Fraction(0))
        lo=sum((x[2] for x in values),Fraction(0));hi=sum((x[3] for x in values),Fraction(0))
        error=sqrt_upper(a*db)+sqrt_upper(b*ds)+sqrt_upper(ds*db)
        return {'trial_cross_lower':downward(lo),'trial_cross_upper':upward(hi),
                'transfer_lower':downward(lo-error),'transfer_upper':upward(hi+error),
                'error_radius_upper':upward(error),
                'region_ids':sorted(keys)}

    return {
        'status':'CONDITIONAL REGIONAL WITNESS ONLY; physical region and trace admission required',
        'whole_domain':enclose(parsed),
        'common':enclose(common),
        'regions':{key:enclose([key]) for key in sorted(parsed)},
        'source_gap_upper':upward(ds),'observation_gap_upper':upward(db),
        'scope':[
            'Common is a named physical region union, not a difference of unrelated diagonals.',
            'Private regions remain present in whole-domain current and voltage objectives.',
            'Region geometry must be disjoint and complete, with matching source/observation functionals.',
            'No monotonicity of regional trial energy or physical hardware acceptance is asserted.',
        ],
    }
