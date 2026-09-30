#!/usr/bin/env python3
"""Compute deliberately generous #34 options without changing captured loads."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
RAILS=('+12V','-12V','+5V')
# Read-only preparatory planning estimate, not a source-backed maximum.
PREP_PACKING_N12_MA={'ADG_package_consolidation':43.4,
                      'sample_hold_opamp_packing':38.0,
                      'comparator_package_consolidation':10.0}


def build():
    budget=json.loads((ROOT/'design/power/rail-budget.json').read_text())
    stats=json.loads((ROOT/'design/reports/netlist-stats.json').read_text())
    standard=json.loads((ROOT/'design/standard/rail-budget-preliminary.json').read_text())
    loads={x['id']:x for x in standard['loads']}
    placements=json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']
    lamps=Counter(x['uid'].split('.')[-1] for x in placements if x['uid'].startswith('L:'))
    n_precision=stats['IC_count_by_part']['OPA4197IPWR']
    n_dc=stats['components_by_type']['PTV09A-4020F-B104']
    iq_precision=loads['opamp_precision']['planning_unit_mA']['-12V']
    iq_replacement=loads['opamp_audio']['planning_unit_mA']['-12V']
    # Issue #60 added two real precision and four audio quads while keeping
    # the panel hardware fixed. Revisit this lock whenever package packing
    # changes; #62 adds ten precision fanout quads. The earlier issue #34
    # numbers remain historical evidence.
    if (n_precision,stats['IC_count_by_part']['OPA4196IDR'],n_dc,lamps)!= (89,174,48,Counter({'mag':92,'stage':12,'clip':10})):
        raise ValueError('captured package/panel count changed; re-evaluate options')
    if (iq_precision,iq_replacement)!=(6.0,1.0):
        raise ValueError('source-backed whole-quad maximum Iq changed; re-evaluate')
    role_saving=n_precision*(iq_precision-iq_replacement)
    analog_lamp_saving=lamps['mag']*loads['magnitude_leds']['planning_unit_mA']['-12V']+lamps['clip']*loads['clip_leds']['planning_unit_mA']['-12V']
    dimmed_saving=lamps['mag']*(loads['magnitude_leds']['planning_unit_mA']['-12V']-.6)+lamps['clip']*(loads['clip_leds']['planning_unit_mA']['-12V']-.6)
    pot_saving=n_dc*loads['dc_pots']['planning_unit_mA']['-12V']
    baseline=budget['reported_planning_upper_subtotal_mA']
    def remaining(saving):return {r:round(baseline[r]-(saving if r in ('+12V','-12V') else 0),6) for r in RAILS}
    base=remaining(0);r1=remaining(role_saving);r2=remaining(role_saving+analog_lamp_saving)
    r3=remaining(role_saving+analog_lamp_saving+pot_saving)
    # The read-only pre-analysis estimate includes sample/hold opamp packing;
    # that overlaps the all-precision migration. Show it only as an extra
    # intentionally overstated sensitivity, never as booked/additive saving.
    prep_extra=sum(PREP_PACKING_N12_MA.values())
    r4=remaining(role_saving+analog_lamp_saving+pot_saving+prep_extra)
    return {'schema_version':1,'status':'CONDITIONAL PLANNING SENSITIVITY ONLY; zero savings booked; no guaranteed maxima established',
            'source_budget':'design/power/rail-budget.json','source_counts':'design/reports/netlist-stats.json and design/grid/placements.lock.json',
            'source_opamp_maxima':'TI OPA4197 and OPA4196 retained PDFs, physical PDF page index 7, Power Supply IQ row; full-temperature per-amplifier maxima 1.5 mA and 0.25 mA, respectively (6 and 1 mA per quad).',
            'source_led_and_pot_allowances':'design/standard/rail-budget-preliminary.json loads magnitude_leds, clip_leds and dc_pots; planning allowances, not manufacturer maxima.',
            'captured_counts':{'OPA4197IPWR_quads':n_precision,'OPA4196IDR_quads':stats['IC_count_by_part']['OPA4196IDR'],'B104_100k_DC_pots':n_dc,'magnitude_LEDs':lamps['mag'],'clip_LEDs':lamps['clip'],'stage_LEDs':lamps['stage']},
            'baseline_planning_upper_mA':base,'ceilings_mA':budget['design_ceiling_mA'],
            'cases':[
                {'case':'1 all precision quads changed to low-Iq family','analog_rail_saving_mA':role_saving,'remaining_mA':r1,'qualification':'Impossible as a blanket role edit without offset/noise/stability review; this is a mathematical upper bound on Iq savings.'},
                {'case':'1 plus all analog indicator current set to zero','analog_rail_saving_mA':role_saving+analog_lamp_saving,'remaining_mA':r2,'qualification':'Deliberately unusable visibility bound; indicator current allowances may be embedded in module reserves, so no saving is booked.'},
                {'case':'1 plus zero analog indicators plus all 48 DC pot current removed','analog_rail_saving_mA':role_saving+analog_lamp_saving+pot_saving,'remaining_mA':r3,'qualification':'Deliberately overgenerous; B104 values are fixed 100k hardware and most pot currents are not separately disaggregated in module reports.'},
            ],
            'practical_indicator_dimming_diagnostic_mA_per_analog_rail':round(dimmed_saving,6),
            'non_additive_packing_stress_test':{
                'exploratory_minus12_terms_mA':PREP_PACKING_N12_MA,
                'hypothetical_remaining_mA':r4,
                'qualification':'Deliberately overstated comparison only, not an option-1–3 budget subtraction: sample/hold opamp packing overlaps the all-precision migration; no package reallocation is generated.'},
            'preparatory_packing_estimate_source':'Read-only preparatory count estimate retained and qualified in design/power/rail-budget-resolution.md; not manufacturer maxima or bookable savings. The sample/hold opamp term overlaps case 1.',
            'booked_savings_mA':{r:0 for r in RAILS},
            'guaranteed_maximum_mA':budget['guaranteed_maximum_mA'],
            'conclusion':'No supported option 1–3 establishes a <=640 mA -12 V maximum for the inherited single-source ceiling. The selected conditional EXT requirement contract is in design/power/supply-architecture.json; source capacity and qualification remain unknown.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    p=ROOT/'design/power/rail-options.json';body=json.dumps(build(),indent=2,ensure_ascii=False)+'\n'
    if args.check:
        if p.read_text()!=body:raise ValueError('rail options report drift')
    else:p.write_text(body)
    print(build()['non_additive_packing_stress_test']['hypothetical_remaining_mA'])

if __name__=='__main__':main()
