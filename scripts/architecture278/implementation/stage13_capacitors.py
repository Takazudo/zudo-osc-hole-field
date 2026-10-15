"""One larger-package T491 reference pair; qualification data are not hardware acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'design/architecture-278/implementation/stage13'
EXPECTED = {
    'C7101': ('T491C475K050AT', 4.7e-6, 50, 1.4, 2.4e-6, 'C', [6,3.2,2.5], [2.37,2.23], 2.57, [7.82,4]),
    'C7102': ('T491D226K035AT', 22e-6, 35, .7, 7.7e-6, 'D', [7.3,4.3,2.8], [2.37,2.43], 3.87, [9.12,5.1]),
}
PRIMARY_SHA = {'C7101':'ddcf6c45b9ff3cc0331329679e96c6eca8295cf941a47738b17ea23219de06e9',
               'C7102':'608b5c99cb0a5cdf8504d697085b714bf7fefe62d2eba6c0d9c5dd97c4f891a4',
               'family':'c3c5bb70009b606c87b40156259670ca9c8452f172b73faa9e2dbf2fcee3522d'}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def analyze(spec, inventory, previous):
    need(spec['candidate_only'] is True and set(spec['parts']) == set(EXPECTED), 'two-cap candidate scope')
    packages = inventory['packages']
    need(len(packages) == 90 and sum(len(p['units']) for p in packages.values()) == 118, 'source conservation')
    need(spec['application'] == previous['REF5050_application'] and
         spec['evidence']['reference'] == previous['sources']['REF50-app'], 'REF5050AI application provenance')
    app = spec['application']
    need(all(spec['evidence'][key]['sha256'] == sha for key,sha in PRIMARY_SHA.items()), 'retained primary bytes')
    family = spec['evidence']['family']
    need(family['url'] == 'https://content.kemet.com/datasheets/KEM_T2005_T491.pdf' and
         family['physical_pdf_page_index'] == 1 and family['printed_page_label'] == '2' and
         [(r['physical_pdf_page_index'],r['printed_page_label']) for r in family['additional_locators']] ==
         [(2,'3'),(11,'12'),(12,'13'),(13,'14'),(14,'15')], 'family qualification/land locators')
    need(app['output_cap_range_F'] == [1e-6,50e-6] and app['recommended_input_bypass_F'] == [1e-6,1e-5]
         and app['stability_ESR_max_ohm'] == 1.5 and app['noise_recommended_ESR_ohm'] == [1,1.5], 'distinct application conditions')
    q = spec['qualification']
    need(q['temperature_C_to_delta_fraction'] == {'-55':.1,'85':.1,'125':.2} and
         q['endurance_hours'] == 2000 and q['endurance_delta_fraction'] == .1, 'specified qualification conditions')
    need(q['joint_operating_bias_temperature_age_guarantee'] is None and q['continuous_reverse_allowed'] is False,
         'qualification must not become combined-service guarantee')
    need(q['recommended_voltage_fraction'] == {'through85C':.5,'above85_to125C':.33} and
         q['leakage_multiplier_at_temperature'] == {'25':1,'85':10,'125':12} and
         q['reverse_transient_fraction_at_temperature'] == {'25':.15,'85':.05,'125':.01}, 'derating/leakage/polarity source')
    need(spec['source_envelope']['input_proposed_max_V'] == 13.2 and
         spec['source_envelope']['output_nominal_V'] == 5 and
         spec['source_envelope']['reference_charging_current_A'] is None, 'voltage/startup boundary')
    need(spec['retained_local_bypass'] == 'C7107' and packages['C7107']['unit_records'][0]['value'] == '100 nF'
         and packages['C7107']['source_package']['decouples_ref'] == 'U7101', 'retained local bypass')
    rows = {}
    for ref, exact in EXPECTED.items():
        p = spec['parts'][ref]
        source = packages[ref]
        actual = (p['MPN'],p['nominal_F'],p['rated_voltage_at85C_V'],p['ESR_max_100kHz25C_ohm'],
                  p['leakage_max_5min25C_A'],p['case'],p['body_nominal_mm'],p['land_pad_size_xy_mm'],
                  p['land_gap_mm'],p['courtyard_size_xy_mm'])
        need(actual == exact and p['tolerance_fraction'] == .1 and p['dielectric'] == 'MnO2 tantalum', 'exact specified part')
        need(p['body_tolerance_mm'] == [.3,.3,.3] and
             p['body_max_mm'] == [round(v+.3,2) for v in p['body_nominal_mm']] and p['land_density'] == 'B', 'maximum body/land dimensions')
        centre = (p['land_gap_mm']+p['land_pad_size_xy_mm'][0])/2
        need(p['pin1_positive_local_xy_mm'] == [-centre,0] and p['pin2_negative_local_xy_mm'] == [centre,0], 'polarized pad geometry')
        need(p['pins'] == source['pins'] and p['units'] == source['units'] and
             p['captured_value'] == source['unit_records'][0]['value'] and
             p['captured_MPN'] == source['attributes']['MPN'] and p['captured_footprint'] == source['footprint'], 'captured whole-package binding')
        need(p['pins']['2'] == 'AGND' and p['pins']['1'] == ('+12V' if ref == 'C7101' else '/A01/C534b2a_RAW_5V'), 'polarity net assignment')
        ev = spec['evidence'][ref]
        need(ev['url'].endswith('/specsheet/'+p['MPN']) and len(ev['sha256']) == 64 and
             ev['physical_pdf_page_index'] == 0 and ev['printed_page_label'] == 'unlabelled', 'exact primary locator')
        C, V = p['nominal_F'], p['rated_voltage_at85C_V']
        need(math.isclose(p['rated_voltage_at125C_V'], .67*V), 'rated hot voltage')
        initial = [C*.9, C*1.1]
        temps = {t: [initial[0]*(1-d), initial[1]*(1+d)] for t,d in q['temperature_C_to_delta_fraction'].items()}
        operating = 13.2 if ref == 'C7101' else 5
        rows[ref] = {**p, 'initial_120Hz25C_interval_F': initial,
            'temperature_qualification_intervals_F': temps,
            'temperature_scope': 'Specified temperature-stability qualification steps relative to initial capacitance; not a simultaneous DC-bias/lifetime service guarantee or arbitrary interpolation.',
            'endurance_test_interval_F': [initial[0]*.9,initial[1]*1.1],
            'endurance_scope': 'Separate2000h85C/ratedV or125C/2/3ratedV test. Not multiplied into temperature or claimed as service lifetime.',
            'effective_service_C_guaranteed_F': None, 'DC_bias_numeric_guarantee': None,
            'recommended_max_application_V': {'through85C':V*.5,'above85_to125C':V*.33},
            'proposed_operating_V': operating, 'within_recommended_voltage_at125C': operating <= V*.33,
            'leakage_temperature_test_limits_A': {t:p['leakage_max_5min25C_A']*m for t,m in q['leakage_multiplier_at_temperature'].items()},
            'leakage_scope': 'Specified rated-voltage/time qualification conditions; startup leakage and actual circuit current remain unbounded.',
            'reverse_transient_limits_V': {t:V*m for t,m in q['reverse_transient_fraction_at_temperature'].items()},
            'continuous_reverse_allowed': False,
            'startup': {'nominal_charge_C': C*operating, 'initial_tolerance_max_charge_C': initial[1]*operating,
                'initial_tolerance_max_energy_J': .5*initial[1]*operating**2,
                'charge_current_for_proposed_10ms_linear_ramp_A': initial[1]*operating/.010,
                'actual_startup_time_s': None, 'actual_peak_inrush_A': None,
                'scope': 'Q=C*dV, E=C*V²/2 and I=C*dV/dt are sensitivities.10ms is an explicit diagnostic only, not source behavior or accepted requirement.'}}
    topology = {r:{k:p[k] for k in ('pins','units','owner')} for r,p in packages.items()}
    return {'status':'ONE LARGER-PACKAGE CAPACITOR PAIR; APPLICATION ACCEPTANCE OPEN',
        'parts':rows, 'application':app, 'evidence':spec['evidence'],
        'geometry_contract': 'Two replacement package footprints only; pin1positive local-X, pin2AGND local+X before whole-package rear mirroring/rotation. Mechanical report owns placement and actual padXYZ.',
        'conservation':{'packages':90,'units':118,'changed_refs':sorted(rows),'unchanged_refs':sorted(set(packages)-set(rows)),
            'added_packages':[],'removed_packages':[],'topology_changed':False,
            'topology_sha256':hashlib.sha256(json.dumps(topology,sort_keys=True).encode()).hexdigest()},
        'input_bypass_nominal_F':4.8e-6, 'output_nominal_F':22e-6,
        'output_comparison':{'captured_charge_at5V_C':5e-6,'candidate_charge_at5V_C':110e-6,
            'charge_ratio':22,'ESR_max_100kHz25C_ohm':.7,'below_TI_stability_limit_at_documented_condition':True,
            'full_temperature_frequency_ESR_ohm':None,'stability_qualified':False,
            'noise_1_to1p5ohm_recommendation_established':False,
            'scope':'0.7Ω is a specified maximum at100kHz25C, not a lower bound or a full REF5050 stability-frequency/temperature envelope. No added series resistor.'},
        'improvement':'Exact part values, formal temperature/endurance qualification, specified leakage/ESR and recommended lands replace the prior MLCC bias-curve-only argument. These remain conditioned data, not assembled proof.',
        'limitations':['Required environment/lifetime and exact combined bias/temperature/age capacitance remain unknown',
            'MnO2 tantalum requires correct polarity; rail sequencing/reversal and REF output discharge into unpowered circuitry are unverified',
            'C/D series surge screening does not qualify unlimited low-impedance hot-plug/inrush; source impedance/current limiting unknown',
            'Larger22uF output increases charge demand22fold; reference current limit/startup/recovery and leakage budget need evaluation',
            'ESR noise recommendation and full-condition stability remain open; no topology addition authorized',
            'Lands/body limits are primary recommendations; assembly/placement/physical clearance assessed separately'],
        'canonical_values_changed':False,'candidate_values_changed':True,'candidate_footprints_changed':True,
        'hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}


def build():
    paths=[OUT/'capacitor-input.json',OUT.parent/'stage10/inventory-report.json',OUT.parent/'stage11/identity-input.json']
    result=analyze(*[json.loads(p.read_text()) for p in paths])
    paths += [Path(__file__),Path(__file__).with_name('test_stage13_capacitors.py'),ROOT/'scripts/checks/partition35.py']
    result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=json.dumps(build(),sort_keys=True,indent=2,allow_nan=False)+'\n';path=OUT/'capacitor-report.json'
    if args.check:need(path.read_text()==text,'stale Stage13 capacitor report')
    else:path.write_text(text)
    print('PASS two polarized T491 candidates; source topology preserved; application NOT QUALIFIED')


if __name__=='__main__':main()
