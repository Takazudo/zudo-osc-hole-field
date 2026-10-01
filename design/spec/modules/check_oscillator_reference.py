"""Source-derived normal-operation reference loads; no short-current guarantee."""
import json
from collections import Counter
from .oscillator import ROOT, family, octave_family, specification
from .io_partition import AMP_MAPS
from .run_oscillator_spice import number
from scripts.schgen.core import designator

CONFIG=ROOT/'design/spec/modules/oscillator-reference.json'
OUT=ROOT/'design/reports/oscillator-reference-fanout.json'


def build(f=None):
    c=json.loads(CONFIG.read_text()); f=f or family(); parts={p.key:p for p in f.parts}
    evidence=json.loads((ROOT/'.claude/skills/component-ti-opa4197ipwr/facts.json').read_text())
    bias_fact=next(x for x in evidence['facts'] if x['fact_id']=='fact-op-precision-input-bias-current-full-temperature')
    assert bias_fact['unit']=='nA' and c['input_bias_bound_A']>=bias_fact['value']['maximum']*1e-9-1e-20,'reference bias bound is below the retained exact-package maximum'
    v=c['reference_abs_max_V']; rail=c['supply_abs_max_V']; tol=c['fixed_resistance_tolerance_fraction']; bias=c['input_bias_bound_A']*1000
    receiver=c['nonprecision_receiver_current_allowance_A']*1000
    assert c['driver_limit_mA']==2 and c['maximum_panel_pots_per_pair']==6
    # Passive divider branches terminate at AGND and one high-impedance input.
    dividers={f'R_{stem}_TOP.0':f'R_{stem}_BOT.0' for stem in ('REF4','TRI_BIAS','SAW_BIAS','REF25')}
    rows=[]
    for group in c['groups']:
        for pol in ('5','N5'):
            net=group+'_REF'+pol; loads=[]; pots=0
            for p in f.parts:
                if net not in p.pins.values():continue
                if p.key in (f'R_{net}_ISO.0', f'R_{net}_FB.0'):continue
                if p.prefix.startswith('RV'):
                    panel=bool(p.panel_refs);pots+=panel
                    assert p.symbol.endswith('PTV09A-4020F-B104') if panel else number(p.value)==10000, f'unexpected potentiometer identity/value {p.key}'
                    resistance=100000 if panel else 10000
                    t=c['pot_resistance_tolerance_fraction'] if panel else c['trim_resistance_tolerance_fraction']
                    span=v if 'AGND' in p.pins.values() else 2*v
                    # Wiper may load either end: count the entire worst wiper demand
                    # on each endpoint, in addition to end-to-end current.
                    if panel:
                        w=p.pins['2'];series=next(q for q in f.parts if q.prefix in ('R','RB') and w in q.pins.values() and q!=p)
                        sense=next(n for n in series.pins.values() if n!=w)
                        fail=next(q for q in f.parts if q.prefix.startswith('R') and set(q.pins.values())=={sense,'AGND'})
                        wiper=v/((number(series.value)+number(fail.value))*(1-tol))*1000+bias
                    else:
                        feed=parts['R_BASE_FEED.0' if group=='BASE' else 'R_SINE_OFFSET.0']
                        assert p.pins['2'] in feed.pins.values()
                        wiper=(v+rail)/(number(feed.value)*(1-tol))*1000
                    current=span/(resistance*(1-t))*1000+wiper
                    loads.append({'key':p.key,'kind':'panel pot' if panel else 'trim','nominal_ohm':resistance,'resistance_tolerance_fraction':t,'wiper_bound_mA':wiper,'maximum_mA':current})
                elif p.prefix.startswith('R'):
                    resistance=number(p.value); voltage=v+rail
                    if p.key in dividers:
                        lower=parts[dividers[p.key]]
                        assert set(lower.pins.values())=={p.pins['2'],'AGND'}
                        resistance+=number(lower.value);voltage=v
                    loads.append({'key':p.key,'kind':'fixed branch','maximum_mA':voltage/(resistance*(1-tol))*1000+receiver})
                elif p.symbol.endswith(('OPA4196IDR','OPA4197IPWR')) and p.unit in range(1,5):
                    out,minus,plus=AMP_MAPS[p.unit-1];assert p.pins[plus]==net
                    loads.append({'key':p.key,'kind':'input bias','maximum_mA':bias if p.symbol.endswith('OPA4197IPWR') else receiver})
                else:raise ValueError(f'unclassified reference load {p.key}')
            assert loads,f'missing local fanout {net}'
            assert pots<=c['maximum_panel_pots_per_pair'],'panel fanout exceeded'
            driver=next(p for p in f.parts if p.symbol.endswith('OPA4197IPWR') and p.unit in range(1,5) and p.pins[AMP_MAPS[p.unit-1][0]]==net+'_DRIVE')
            out,minus,plus=AMP_MAPS[driver.unit-1]
            assert driver.pins[plus]=='OSC_REF'+pol and driver.pins[minus]==net+'_FB'
            for suffix,value in [('ISO',c['isolation_ohm']),('FB',c['feedback_ohm']),('FAST',c['compensation_F'])]:
                part=parts[('C_' if suffix=='FAST' else 'R_')+net+'_'+suffix+'.0']
                assert number(part.value)==value
                assert set(part.pins.values())==({net+'_DRIVE',net} if suffix=='ISO' else {net,net+'_FB'} if suffix=='FB' else {net+'_DRIVE',net+'_FB'})
            maximum=sum(x['maximum_mA'] for x in loads)+bias
            assert maximum<c['driver_limit_mA'],f'{net} overload {maximum}'
            rows.append({'net':net,'driver_key':driver.key,'output_pin':out,'panel_pots':pots,'loads':loads,'maximum_mA':maximum,'output_drive_abs_max_V':v+maximum/1000*c['isolation_ohm']*(1+tol),'connector_branch_mA':sum(x['maximum_mA'] for x in loads if x['kind']=='panel pot')})
    # Raw master references can drive only local buffer inputs in oscillator sheets.
    for p in f.parts:
        for pin,net in p.pins.items():
            if net not in ('OSC_REF5','OSC_REFN5'):continue
            assert p.symbol.endswith('OPA4197IPWR') and p.unit in range(1,5) and pin==AMP_MAPS[p.unit-1][2],f'raw source loaded by {p.key}'
    source=[]
    for pol in ('5','N5'):
        net='OSC_REF'+pol;loads=[]
        for p in octave_family().parts:
            if net not in p.pins.values() or not p.prefix.startswith('R'):continue
            # Conservative rail-bounded remote node, except the inverting virtual
            # ground whose normal-operation error envelope is +/-100 mV.
            voltage=v+.1 if p.attributes['Role'] in ('reference_generator:R_INV','reference_generator:R_FB') else v+rail
            resistance=number(p.value)
            if p.attributes['Role']=='reference_generator:R_GTOP':
                bottom=next(q for q in octave_family().parts if q.attributes['Role']=='reference_generator:R_GBOT')
                assert set(bottom.pins.values())=={p.pins['2'],'AGND'}
                resistance+=number(bottom.value);voltage=v
            loads.append({'key':p.key,'maximum_mA':voltage/(resistance*(1-tol))*1000})
        maximum=sum(x['maximum_mA'] for x in loads)+15*bias
        assert maximum<2,f'master source overload {net}: {maximum}'
        source.append({'net':net,'loads':loads,'maximum_mA':maximum,'connector_input_bias_mA_per_oscillator':3*bias})
    receivers=[{'instance':inst.name,'ref':designator(p,inst),'pin':pin,'source_net':net,'partial_power_status':'NOT RUN - #59 injection/isolation gate'}
               for inst in specification()[1][:5] for p in f.parts for pin,net in p.pins.items() if net in ('OSC_REF5','OSC_REFN5')]
    assert len(receivers)==30
    packages=Counter(p.symbol.split(':')[-1] for p in f.parts if p.prefix=='U' and p.unit==1)
    attribution=[]
    for inst in specification()[1][:5]:
        for p in f.parts:
            if p.symbol.endswith('OPA4197IPWR') and p.unit==5:
                caps=[q for q in f.parts if q.attributes.get('Decouples')==p.key.rsplit('.',1)[0]]
                assert len(caps)==2 and {n for q in caps for n in q.pins.values()}=={'+12V','-12V','AGND'}
                attribution.append({'ref':designator(p,inst),'supply_pins':p.pins,'bypass_refs':[designator(q,inst) for q in caps],'bypass_F_each':1e-7})
    positive=sum(x['maximum_mA'] for x in rows if x['net'].endswith('REF5'))
    negative=sum(x['maximum_mA'] for x in rows if x['net'].endswith('REFN5'))
    # End-to-end bipolar/unipolar pot current always sources the positive
    # driver and sinks the negative driver. Allow every wiper/fixed/input
    # branch to reverse independently: charge that bound to the opposite rail
    # as well, rather than assuming positive-net current uses only +12 V.
    def reversible(polarity):
        return sum((load['wiper_bound_mA'] if load['kind'] in ('trim','panel pot') else load['maximum_mA'])
                   for row in rows if row['net'].endswith(polarity) for load in row['loads'])+3*bias
    rail_bounds={'+12V':positive+reversible('REFN5'),'-12V':negative+reversible('REF5')}
    return {'schema_version':1,'status':'PASS - conditional powered load arithmetic; UNVALIDATED DRAFT','conditions':c,'local_outputs_per_oscillator':rows,'master_sources':source,'shared_source_receiver_inputs':receivers,'physical_IC_packages_per_oscillator':dict(packages),'precision_package_supply_and_bypass':attribution,'increment_over_issue60':{'physical_OPA4197IPWR_packages':10,'quiescent_mA_per_analog_rail':60,'bypass_uF_per_analog_rail':1,'reference_load_reserve_mA_per_analog_rail':25,'total_planning_mA_per_analog_rail':85,'basis':'Two additional quads/oscillator at 6 mA/rail; add 5 mA/rail/oscillator without crediting the existing 12 mA local or 8 mA shared reserves.'},'per_oscillator_output_current_sum_mA':{'+5V':positive,'-5V':negative},'conservative_AGND_return_bound_mA_per_oscillator':positive+negative,'per_rail_output_current_bound_mA_per_oscillator':rail_bounds,'rail_planning_check':all(value<5 for value in rail_bounds.values()),'minimum_driver_rail_headroom_V':c['supply_abs_min_V']-max(x['output_drive_abs_max_V'] for x in rows),'calibration':{'nominal_TUNE_V':[-5,5],'nominal_FINE_V':[-5,5],'nominal_PW_V':[0,5],'nominal_BASE_and_SINE_trim_V':[-5,5],'tune_pitch_contribution_V':[-2,2],'fine_pitch_contribution_V':[-.1,.1],'local_offset_sensitivity_uV_per_100uV_amplifier_offset':100,'input_bias_bound_A':c['input_bias_bound_A'],'local_bias_error_uV_at_source_bound':c['input_bias_bound_A']*c['feedback_ohm']*1e6,'note':'Remote DC feedback cancels the 100 ohm isolation drop at the local sense point. Harness drop and master-reference error remain additional; 100 uV offset source is at +/-18 V, 25 C and is a sensitivity calculation, not a +/-12 V guarantee. Full-temperature bias is the PW-package row; actual common-mode and loaded corner applicability remains conditional.'},'not_run':c['physical_gates']}


def main():
    import sys
    report=build();assert report['rail_planning_check'];body=json.dumps(report,indent=2)+'\n'
    if '--check' in sys.argv:assert OUT.read_text()==body,'fanout report drift'
    else:OUT.write_text(body)
    print('PASS oscillator fanout:',[(r['net'],round(r['maximum_mA'],6)) for r in report['local_outputs_per_oscillator']])
if __name__=='__main__':main()
