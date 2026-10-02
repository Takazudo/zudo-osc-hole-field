#!/usr/bin/env python3
"""Source-bound REF output capacitance range; no full reference qualification."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = '.claude/skills/component-monitor-permit-candidates/'
MPN = 'C1206C104F3GACTU'
RECORD = 'rec-monitor-c1206c104f3gactu'
FACT_PREFIX = 'fact-monitor-c1206c104f3gactu-'
SOURCE_PREFIX = 'src-monitor-c1206c104f3gactu-'
REF_RECORD = 'rec-monitor-ref3433tidbvr'
REF_FACT = 'fact-monitor-ref3433tidbvr-stable-capacitance'
SOURCE_LOCKS = {
    SOURCE_PREFIX+'datasheet': 'f5c22b668f632aa28ad2696645232c9b3554b82ff9028888a0b10c86f5c42716',
    SOURCE_PREFIX+'land': '02d179914aeb9585eb2229ba8e18ef9d6b01c77c056de2af295d6950a2a5cc0d',
    'src-monitor-ref3433tidbvr-datasheet': 'cbf64eb240e023dfdbb063d9f515212718f8b1732fc5b582e52f268dfbd5d665',
}
INPUTS = {
    'spec': 'design/power/monitor-permit-draft.json',
    'catalog': 'design/power/monitor-permit-parts.json',
    'facts': OWNER+'facts.json', 'sources': OWNER+'sources.json',
    'manifest': OWNER+'manifest.json', 'pin_maps': OWNER+'pin-map.json',
    'inventory': '.claude/skills/component-spec-audit/references/inventory.json',
}
REPORT = ROOT/'design/power/monitor-reference-capacitance-report.json'
# Reviewed transcriptions. A new source/value/condition needs renewed review;
# changing a fact cannot silently widen this admission.
FACT_LOCKS = {
    'capacitance': (100, 'nF', 'datasheet', 'Nominal capacitance at 1 kHz, 1.0 Vrms; C0G family has zero aging and no applied-DC-voltage change within rating.'),
    'tolerance': (.01, 'fraction', 'datasheet', 'Initial tolerance at the stated capacitance measurement condition; temperature coefficient is applied separately.'),
    'rated-voltage': (25, 'V', 'datasheet', 'DC rated voltage; no system fault/overshoot survival qualification.'),
    'temperature-coefficient': (30, 'ppm/°C', 'datasheet', 'Absolute C0G coefficient relative to +25 C and 0 VDC, at 1 kHz/1 Vrms, over -55..125 C; applied-DC behavior is a separate family fact.'),
    'temperature-range': ({'minimum':-55,'maximum':125}, '°C', 'datasheet', 'Component operating temperature range; actual installed temperature is not established.'),
    'voltage-change': (0, 'fraction', 'land', 'C0G family capacitance does not change with applied rated DC voltage; no bound beyond the exact part voltage rating.'),
    'aging': (0, 'fraction', 'datasheet', 'Zero loss per decade-hour; environmental stress qualification has separate limits.'),
}


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('nonfinite or nonnumeric electrical input')
    return F(str(value))


def keyed(rows, key):
    result = {}
    for row in rows:
        if row[key] in result:
            raise ValueError('duplicate '+key)
        result[row[key]] = row
    return result


def bank_interval(count, nominal, tolerance, coefficient, reference, temperatures):
    if isinstance(count,bool) or not isinstance(count,int) or count <= 0:
        raise ValueError('invalid capacitor count')
    n,t,k,r = map(number,(nominal,tolerance,coefficient,reference))
    lo,hi = map(number,temperatures)
    if n <= 0 or not 0 <= t < 1 or k < 0 or lo > hi:
        raise ValueError('invalid capacitance domain')
    excursion = max(abs(lo-r),abs(hi-r))
    shift = excursion*k
    if shift >= 1:
        raise ValueError('temperature factor removes capacitance')
    return count*n*(1-t)*(1-shift), count*n*(1+t)*(1+shift)


def require_range(bounds, allowed):
    minimum,maximum = map(number,allowed)
    if not 0 < minimum < maximum or not minimum < bounds[0] <= bounds[1] < maximum:
        raise ValueError('bank interval is not strictly inside REF stable-capacitance range')


def enclosing_float(value, upper):
    out = float(value)
    if not math.isfinite(out):
        raise ValueError('capacitance conversion overflow')
    if (upper and F.from_float(out) < value) or (not upper and F.from_float(out) > value):
        out = math.nextafter(out,math.inf if upper else -math.inf)
    return out


def calculate(data):
    spec = data['spec']
    if spec['canonical_protection_implemented'] is not False or spec['qualification_accepted'] is not False:
        raise ValueError('candidate qualification cannot be promoted')
    parts = keyed(spec['components'],'ref')
    records = keyed(data['manifest']['records'],'record_id')
    facts = keyed(data['facts']['facts'],'fact_id')
    sources = keyed(data['sources']['sources'],'source_id')
    entries = keyed(data['catalog']['parts'],'mpn')
    record = records[RECORD]
    if record['mpn'] != MPN or record['manufacturer'] != 'KEMET':
        raise ValueError('C0G record identity differs')
    inv = keyed(data['inventory']['lines'],'line_id')[record['line_id']]
    if inv['mpn'] != MPN or inv['dnp'] is not True:
        raise ValueError('candidate inventory identity/population differs')
    expected_pins = {'1':'unpolarized terminal','2':'unpolarized terminal'}
    entry = entries[MPN]
    mappings = [p for p in data['pin_maps']['pin_maps'] if p['record_id']==RECORD]
    if len(mappings) != 1:
        raise ValueError('candidate needs one pin map')
    mapping = mappings[0]
    if (entry['kind'] != 'capacitor' or entry['pins'] != expected_pins
            or entry['symbol'] != MPN or entry['footprint'] != 'KEMET_C1206_C0G_DensityB'
            or mapping['symbol'] != entry['symbol'] or mapping['footprint'] != entry['footprint']):
        raise ValueError('candidate capacitor catalogue or pin-map differs')
    for key,sid in [('source',SOURCE_PREFIX+'datasheet'),('land_source',SOURCE_PREFIX+'land')]:
        if entry[key]['sha256'] != SOURCE_LOCKS[sid]:
            raise ValueError('catalogue source closure differs')
    used = {}
    for suffix,(value,unit,origin,conditions) in FACT_LOCKS.items():
        fid = FACT_PREFIX+suffix
        f = facts[fid]
        sid = SOURCE_PREFIX+origin
        if (type(f['value']) is not type(value) or f['value'] != value
                or f['unit'] != unit or f['conditions'] != conditions
                or f['class'] != 'GUARANTEED_ELECTRICAL' or f['source_id'] != sid
                or f['record_id'] != RECORD or fid not in record['fact_ids']):
            raise ValueError('C0G source fact/condition differs: '+suffix)
        used[fid] = f
    rf = facts[REF_FACT]
    rr = records[REF_RECORD]
    if (parts['U103']['mpn'] != rr['mpn'] or rr['mpn'] != 'REF3433TIDBVR'
            or parts['U103']['pins'] != {'1':None,'2':'AGND','3':None,'4':'+5V','5':None,'6':'REF'}
            or rf['record_id'] != REF_RECORD or REF_FACT not in rr['fact_ids']
            or rf['source_id'] != 'src-monitor-ref3433tidbvr-datasheet'
            or rf['class'] != 'RECOMMENDED_OPERATION' or rf['unit'] != 'F'
            or rf['value'] != {'minimum':1e-7,'maximum':1e-5}
            or rf['conditions'] != 'Effective output capacitance over -40..125C; nominal bypass markings alone do not establish it.'):
        raise ValueError('REF source/pin applicability differs')
    used[REF_FACT] = rf
    for f in used.values():
        s = sources[f['source_id']]
        r = records[f['record_id']]
        if (f['provenance'] != 'PRIMARY-SPEC' or f['verdict'] != 'PASS - primary-source confirmed'
                or s['record_id'] != r['record_id'] or s['source_id'] not in r['source_ids']
                or s['authority_class'] != 'MANUFACTURER_PRIMARY' or s['availability'] != 'AVAILABLE'
                or s['sha256'] != SOURCE_LOCKS[s['source_id']]):
            raise ValueError('primary source closure failed')
    bank = [p for p in parts.values() if p['kind']=='capacitor' and 'REF' in p['pins'].values()]
    if {p['ref'] for p in bank} != {'C104','C105','C106'}:
        raise ValueError('REF output bank coverage differs')
    nominal = number(used[FACT_PREFIX+'capacitance']['value']) / 10**9
    for p in bank:
        if (p.get('dnp', False) is not False or p['mpn'] != MPN or set(p['pins']) != {'1','2'} or set(p['pins'].values()) != {'REF','AGND'}
                or number(p['value']) != nominal or number(entry['capacitance_F']) != nominal):
            raise ValueError('REF capacitor identity/value/connectivity differs')
    # Component-temperature screen matches the REF row. No claim that installed
    # temperatures follow ambient, or that ESR/ESL parasitics are bounded.
    temperature = [-40,125]
    component_range = used[FACT_PREFIX+'temperature-range']['value']
    if not component_range['minimum'] <= temperature[0] <= temperature[1] <= component_range['maximum']:
        raise ValueError('temperature applicability differs')
    bounds = bank_interval(len(bank),float(nominal),used[FACT_PREFIX+'tolerance']['value'],
                           used[FACT_PREFIX+'temperature-coefficient']['value']/1e6,25,temperature)
    allowed = [rf['value']['minimum'],rf['value']['maximum']]
    require_range(bounds,allowed)
    return {
        'status':'SOURCE-BOUND CAPACITANCE RANGE ONLY; unselected native candidate',
        'capacitors':sorted(p['ref'] for p in bank), 'mpn':MPN,
        'component_temperature_C':temperature, 'reference_temperature_C':25,
        'nominal_bank_F':float(len(bank)*nominal),
        'capacitance_interval_F':[enclosing_float(bounds[0],False),enclosing_float(bounds[1],True)],
        'exact_interval_F':[str(v) for v in bounds],
        'REF_stable_capacitance_range_F':allowed,
        'capacitance_value_range_admitted':True,
        'common_table_COUT_F':1e-5, 'common_accuracy_timing_condition_matched':False,
        'canonical_protection_implemented':False, 'qualification_accepted':False,
        'installed_reference_stability_qualified':False, 'precision_reference_validity_qualified':False,
        'source_fact_ids':sorted(used),
        'primary_source_sha256':SOURCE_LOCKS,
        'conditions':['Exact part tolerance at 1 kHz/1 Vrms; C0G temperature factor relative to25C.',
            'Family no applied-rated-DC-voltage capacitance change and zero aging; not beyond25V.',
            'Component temperature within -40..125C is a screen, not an installed thermal result.',
            'No full-temperature capacitor leakage bound is added to the conditional DC current ledger.'],
        'remaining':['REF table common10uF accuracy, Iq and timing condition remains unmatched.',
            'Startup/slow-slew/shutdown, line-load cross-condition and3.29..3.31V reference validity remain open.',
            'Installed ESR/ESL, board parasitics, soldering/environmental stress and physical fit remain unqualified.',
            'LVC ICC/partial-power/release, return integrity and real signal isolation remain open.'],
    }


def snapshot():
    paths = [ROOT/p for p in INPUTS.values()] + [Path(__file__).resolve()]
    return {p:p.read_bytes() for p in paths}


def run(check=False):
    frozen = snapshot()
    data = {key:json.loads(frozen[ROOT/path]) for key,path in INPUTS.items()}
    result = calculate(data)
    # Retained bytes are optional on clean CI, but any available copy must
    # match. The committed result never claims a CI cache download happened.
    checked = 0
    for part in data['catalog']['parts']:
        if part['mpn'] not in (MPN,'REF3433TIDBVR'):
            continue
        for key in ('source','land_source'):
            if key not in part:
                continue
            src = part[key]; path = ROOT/src['file']
            if path.exists():
                if hashlib.sha256(path.read_bytes()).hexdigest() != src['sha256']:
                    raise ValueError('retained source bytes differ: '+str(path))
                checked += 1
    result['input_sha256'] = {str(p.relative_to(ROOT)):hashlib.sha256(b).hexdigest() for p,b in frozen.items()}
    text = json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if any(p.read_bytes()!=b for p,b in frozen.items()):
        raise ValueError('capacitance source inputs changed during calculation')
    if check:
        if not REPORT.exists() or REPORT.read_text()!=text:
            raise ValueError('reference capacitance report drift')
    else:
        REPORT.write_text(text)
    print(f'PASS: source-bound REF capacitance interval only; {checked} available cached PDFs hash-checked; missing cache downloads NOT RUN')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    run(parser.parse_args().check)
