"""Explicit unselected Ohm-law conditions for exact source ground shunts.

Ohm's law bounds the resistive contribution only. Using that number as a TOTAL
terminal-current cap is a separate unselected project requirement, including
parasitic displacement and leakage. No dynamic guarantee follows from nominal
values, tolerance, component voltage ratings or unspecified MPNs.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from scripts.pcbgen.netlist import read_netlist


def derive(ledger, components, pin_nets, voltage, minimum_fraction):
    if not math.isfinite(voltage) or voltage<=0 or not math.isfinite(minimum_fraction) or not 0<minimum_fraction<=1:
        raise ValueError('positive finite voltage and operating resistance fraction in (0,1] required')
    components=list(components);lookup={c.ref:c for c in components}
    if len(lookup)!=len(components):raise ValueError('duplicate source component identity')
    result=copy.deepcopy(ledger);caps={};conditions=[]
    for row in result['pads']:
        if not row['possible_normal_return_basis']:continue
        key=(row['ref'],row['pad'])
        if pin_nets.get(key)!='AGND':raise ValueError('source netlist lacks exact ground return contact: '+str(key))
        # This reusable logical resistor symbol is not an MPN assignment.
        # Exact resistance and orderable identity come from this component.
        if row.get('symbol') not in ('RC0603FR-07100KL','RT0603BRD07100KL'):continue
        component=lookup[row['ref']]
        numeric=component.value.removesuffix(' Ω')
        try:nominal=float(numeric)
        except ValueError as exc:raise ValueError('resistor has no exact numeric source value') from exc
        if not math.isfinite(nominal) or nominal<=0:raise ValueError('positive finite source resistor value required')
        other=[net for (ref,pad),net in pin_nets.items() if ref==row['ref'] and pad!=row['pad']]
        if len(other)!=1 or other[0]=='AGND':raise ValueError('expected one actual non-ground shunt endpoint')
        minimum=minimum_fraction*nominal;maximum=voltage/minimum
        role='conditional_resistor_'+format(nominal,'.12g')+'ohm'
        caps[role]=maximum
        row['category_before_conditional_resistor_class']=row['category'];row['category']=role
        conditions.append({'ref':row['ref'],'pad':row['pad'],'other_net':other[0],
            'logical_symbol':row['symbol'],'source_nominal_ohm':nominal,'source_MPN':dict(component.fields).get('MPN',''),
            'conditional_operating_minimum_ohm':minimum,'conditional_voltage_magnitude_maximum_V':voltage,
            'conditional_resistive_current_maximum_A':maximum,
            'separate_unselected_total_terminal_current_requirement_A':maximum})
    if not conditions:raise ValueError('no exact source resistor shunts found')
    result['normal_transfer_envelope']['conditional_resistor_class']={
        'status':'UNSELECTED PROJECT REQUIREMENT / NEEDS BENCH; not a manufacturer guarantee',
        'voltage_magnitude_maximum_V':voltage,'minimum_operating_resistance_fraction_of_source_value':minimum_fraction,
        'scope':'The voltage and actual operating minimum resistance conditions bound only resistive current. Nominal or 25 C tolerance alone does not establish the minimum. Blank MPNs remain unspecified; no component inherits another resistor value or exact-part evidence.',
        'total_terminal_current_condition':'The returned caps may bound actual terminal flux only if a SEPARATE total-terminal-current requirement at each listed value is established, counting parasitic C*dV/dt, leakage and other permitted dynamic contributions. Voltage/resistance alone does not establish this requirement. No zero parasitic contribution or dynamic cancellation is assumed. Until then this remains a resistive-only sensitivity screen, not an adopted total-current class.',
        'qualification_obligations':'OPEN #57 normal source and permitted waveform/current envelope; #59 external patch/fault/transient scope; #65 actual operating resistance, parasitic/leakage/temperature/process and terminal-current verification. No new fitted limiting hardware or protection is inferred.',
        'aggregate_scope':'All signed currents remain admissible under the unchanged one aggregate sum of absolute currents. No bypass, sleeve, IC or input current is reduced by these resistor conditions.',
        'contacts':conditions}
    return result,caps


def main():
    parser=argparse.ArgumentParser()
    for name in ('ledger','netlist','output_ledger','output_caps'):parser.add_argument(name,type=Path)
    parser.add_argument('--voltage-bound-V',type=float,required=True)
    parser.add_argument('--minimum-resistance-fraction',type=float,required=True)
    args=parser.parse_args()
    paths=(args.ledger,args.netlist,Path(__file__))
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    components,pin_nets=read_netlist(args.netlist)
    result,caps=derive(json.loads(args.ledger.read_text()),components,pin_nets,args.voltage_bound_V,args.minimum_resistance_fraction)
    result['conditional_resistor_derivation_source_sha256']=hashes
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=expected for p,expected in hashes.items()):
        raise ValueError('conditional resistor input changed during derivation')
    args.output_ledger.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    args.output_caps.write_text(json.dumps(caps,indent=2,sort_keys=True)+'\n')
    print('UNSELECTED resistor contacts',len(result['normal_transfer_envelope']['conditional_resistor_class']['contacts']),caps)


if __name__=='__main__':main()
