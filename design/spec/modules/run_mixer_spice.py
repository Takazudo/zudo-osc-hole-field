"""Bounded MIX4 OTA model and MIX5 ideal summer checks.

The retained National/TI LM13700 single-OTA model excludes real opamps,
current-servo dynamics, package coupling, temperature and cable loading.
"""
import json,re,subprocess
from design.spec.cells._builder import ROOT

DIR=ROOT/'design/spec/modules/spice'
OUT=ROOT/'design/reports/spice/mixers.json'
OFFSET_WIPER_V=2.7
TIA_TRIM_OHM=9000


def run(deck):
    proc=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',str(deck.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
    output=proc.stdout+'\n'+proc.stderr
    if proc.returncode:raise RuntimeError(output)
    return output


def mixer5():
    return '''MIX5 five equal inputs, ideal amplifiers; +5 V each
V1 IN1 0 5
V2 IN2 0 5
V3 IN3 0 5
V4 IN4 0 5
V5 IN5 0 5
R1 IN1 SUM_NODE 100k
R2 IN2 SUM_NODE 100k
R3 IN3 SUM_NODE 100k
R4 IN4 SUM_NODE 100k
R5 IN5 SUM_NODE 100k
RF SUM_PRELEVEL SUM_NODE 40k
ESUM SUM_PRELEVEL 0 0 SUM_NODE 1e6
* LEVEL is a chosen pot position in this ideal deck, not hardware.
RLEVEL_TOP SUM_PRELEVEL LEVEL 5k
RLEVEL_BOTTOM LEVEL 0 5k
ELEVEL LEVEL_BUFFERED 0 LEVEL 0 1
RRESTORE LEVEL_BUFFERED RESTORE_NODE 100k
RRESTORE_FB SUM_OUT RESTORE_NODE 100k
ERESTORE SUM_OUT 0 0 RESTORE_NODE 1e6
.op
.print op v(SUM_PRELEVEL) v(SUM_OUT)
.end
'''


def mixer4(command, amplitude, offset_wiper=OFFSET_WIPER_V, tia_trim=TIA_TRIM_OHM):
    # The physical 10 kΩ trim is a ±5 V divider feeding 1 MΩ into a 1 kΩ return.
    # Only the bias servo is imposed; negative combined CV requests shutoff.
    ibias=max(0,command)/10000
    if not -5<offset_wiper<5 or not 0<=tia_trim<=10000:
        raise ValueError('calibration is outside the captured trim ranges')
    pot_top=(5-offset_wiper)*1000
    pot_bottom=(offset_wiper+5)*1000
    return f'''MIX4 vendor single OTA; ideal summer/TIA and imposed bias {ibias:g} A
.include "design/spec/modules/spice/filter-model/LM13700.MOD"
VP P_12V 0 12
VN N_12V 0 -12
VREFP REF5 0 5
VREFN REFN5 0 -5
VIN IN 0 SIN(0 {amplitude:g} 1k) AC {amplitude:g}
R1 IN SUM_NODE 100k
R2 IN SUM_NODE 100k
R3 IN SUM_NODE 100k
R4 IN SUM_NODE 100k
RF SUM_PRELEVEL SUM_NODE 50k
ESUM SUM_PRELEVEL 0 0 SUM_NODE 1e6
RATTEN SUM_PRELEVEL OTA_SIGNAL 100k
RATTEN_G OTA_SIGNAL 0 100
RPOT_TOP REF5 OFFSET_W {pot_top:g}
RPOT_BOTTOM OFFSET_W REFN5 {pot_bottom:g}
RFEED OFFSET_W OTA_OFFSET 1meg
ROFF OTA_OFFSET 0 1k
IABC P_12V CURRENT_SOURCE {ibias:g}
R_IABC_LIMIT CURRENT_SOURCE IABC1 10k
XOTA IABC1 DIODE OTA_SIGNAL OTA_OFFSET OTA_CURRENT N_12V 0 BUFFER_OUT P_12V LM13700/NS
RFB SUM_OUT FB_TRIM 100k
RTRIM FB_TRIM OTA_CURRENT {tia_trim:g}
ETIA SUM_OUT 0 0 OTA_CURRENT 1e6
RLOAD SUM_OUT 0 100k
.tran 1u 4m
.measure tran out_max MAX v(SUM_OUT) FROM=2m TO=4m
.measure tran out_min MIN v(SUM_OUT) FROM=2m TO=4m
.end
'''


def model_failures(rows):
    """Check the fixed model criteria; physical feedthrough has no limit yet."""
    failures=[]
    by_vector={(r['command_V'],r['input_peak_each_V']):r for r in rows}
    for row in rows:
        values=row['output_extrema_V']
        if row['command_V']<=0 and max(abs(v) for v in values.values())>0.01:
            failures.append(f"{row['deck']}: zero-bias shutoff exceeds 10 mV")
        if row['command_V']==5 and row['input_peak_each_V']==5 and max(abs(v) for v in values.values())>10:
            failures.append(f"{row['deck']}: full-scale output exceeds ±10 V")
    for command in (2.5,5):
        for amplitude in (1,5):
            if (command,amplitude) not in by_vector:
                continue
            row=by_vector[(command,amplitude)]
            values=row['output_extrema_V']
            swing=(values['out_max']-values['out_min'])/2
            requested=(command/5)*2*amplitude
            if not 0.9*requested<=swing<=1.1*requested:
                failures.append(f"{row['deck']}: gain-law swing {swing:g} V outside ±10% of {requested:g} V")
    return failures


def exit_on_model_failures(failures):
    if failures:
        raise SystemExit('\n'.join(failures))


def main():
    DIR.mkdir(exist_ok=True);results=[]
    deck=DIR/'mix5-ideal.cir';deck.write_text(mixer5());output=run(deck)
    match=re.search(r'^0\s+([-+\d.eE]+)\s+([-+\d.eE]+)',output,re.M)
    op={'sum_prelevel':float(match[1]),'sum_out':float(match[2])} if match else {}
    if len(op)!=2:raise RuntimeError(output)
    if abs(op['sum_prelevel']+10)>=.01 or abs(op['sum_out']-5)>=.01:
        raise RuntimeError(f'MIX5 ideal summer target failed: {op}')
    results.append({'deck':str(deck.relative_to(ROOT)),'status':'PASS - ideal model only','result_V':op,'condition':'All five inputs +5 V, all input attenuverters at +1, LEVEL at midpoint. No saturation or tolerance modeled.'})
    mix4_rows=[]
    for command in (-5,0,2.5,5):
        for amplitude in (0,1,5):
            deck=DIR/f'mix4-vendor-{str(command).replace("-","n").replace(".","p")}-{amplitude}v.cir';deck.write_text(mixer4(command,amplitude));output=run(deck)
            values={k:float(v) for k,v in re.findall(r'^(out_(?:max|min))\s*=\s*([-+\d.eE]+)',output,re.M)}
            if len(values)!=2:raise RuntimeError(output)
            row={'deck':str(deck.relative_to(ROOT)),'status':'MEASURED - vendor single OTA model only','command_V':command,
                        'imposed_bias_uA':max(0,command)*100,'input_peak_each_V':amplitude,'output_extrema_V':values,
                        'condition':'Four coherent 1 kHz ideal sources stand in for protected input/attenuverter chains; captured summer, 100k/100 Ω OTA divider, offset pot, IABC series resistor and TIA; ideal ±12 V amplifier stages; 100k output load replaces output cell; frozen calibration.'}
            results.append(row);mix4_rows.append(row)
    failures=model_failures(mix4_rows)
    report={'schema_version':2,'authority':'PROPOSAL - unvalidated','oracle':'KiCad 10.0.6 ngspice via scripts/kicad/run.sh',
            'status':'MODEL TARGET FAIL' if failures else 'Bounded waveform and zero-bias model checks met; feedthrough open; hardware unvalidated',
            'model':'Retained TI/National LM13700/NS single OTA; model pin order IABC, DIODE, IN+, IN-, OUT, V-, BUFFER_IN, BUFFER_OUT, V+ matches physical OTA1 pins 1,2,3,4,5,6,7,8,11.',
            'calibration':{'procedure':'At +5 V command and zero input, adjust the existing ±5 V offset wiper to near-zero output. At four coherent 5 V peak inputs, adjust the existing 100–110 kΩ TIA feedback below the ±10 V envelope. Freeze both settings for all vectors.',
                           'offset_wiper_unloaded_V':OFFSET_WIPER_V,'pot_top_ohm':(5-OFFSET_WIPER_V)*1000,'pot_bottom_ohm':(OFFSET_WIPER_V+5)*1000,'tia_feedback_ohm':100000+TIA_TRIM_OHM,'frozen_across_runs':True},
            'model_check_criteria':'Nonzero exit for output beyond ±10 V at +5 V command / four 5 V peak inputs, more than 10 mV at zero imposed bias, or positive-command gain swing outside ±10% of the ideal linear request. The gain tolerance is a fixture diagnostic, not a hardware specification.',
            'feedthrough_diagnostic_V':{'command_2p5_zero_input':next(r['output_extrema_V']['out_max'] for r in mix4_rows if r['command_V']==2.5 and r['input_peak_each_V']==0),
                                         'command_5_zero_input':next(r['output_extrema_V']['out_max'] for r in mix4_rows if r['command_V']==5 and r['input_peak_each_V']==0),
                                         'acceptance':'OPEN - no numeric hardware limit or measurement'},
            'failures':failures,
            'runs':results,
            'not_run':[{'subject':'MIX4 physical silence/feedthrough, complete servo, real opamp headroom, package, temperature and stability','status':'NOT RUN','reason':'The model predicts residual silence output at half command; no numeric feedthrough acceptance is specified. Retained model is one OTA only and warns bandwidth/phase-margin overestimate >2x; ideal amplifiers and imposed bias omit real servo and saturation.'},
                       {'subject':'MIX5 cable stability, short/fault protection, ±10 V internal headroom and clip window tolerance','status':'NOT RUN','reason':'No complete vendor models or hardware bench measurements for full signal chain.'}]}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n')
    for row in results:print(row)
    exit_on_model_failures(failures)

if __name__=='__main__':main()
