"""Bounded MIX4 OTA model and MIX5 ideal summer checks.

The retained National/TI LM13700 single-OTA model excludes real opamps,
current-servo dynamics, package coupling, temperature and cable loading.
"""
import json,re,subprocess
from design.spec.cells._builder import ROOT

DIR=ROOT/'design/spec/modules/spice'
OUT=ROOT/'design/reports/spice/mixers.json'


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


def mixer4(command, amplitude):
    ibias=command/10000
    return f'''MIX4 vendor single OTA; ideal summer/TIA and imposed bias {ibias:g} A
.include "design/spec/modules/spice/filter-model/LM13700.MOD"
VP P_12V 0 12
VN N_12V 0 -12
VIN IN 0 SIN(0 {amplitude:g} 1k) AC {amplitude:g}
R1 IN SUM_NODE 100k
R2 IN SUM_NODE 100k
R3 IN SUM_NODE 100k
R4 IN SUM_NODE 100k
RF SUM_PRELEVEL SUM_NODE 50k
ESUM SUM_PRELEVEL 0 0 SUM_NODE 1e6
RATTEN SUM_PRELEVEL OTA_SIGNAL 100k
RATTEN_G OTA_SIGNAL 0 100
ROFF OTA_OFFSET 0 1k
IABC P_12V IABC1 {ibias:g}
XOTA IABC1 DIODE OTA_SIGNAL OTA_OFFSET OTA_CURRENT N_12V 0 BUFFER_OUT P_12V LM13700/NS
RFB SUM_OUT FB_TRIM 100k
RTRIM FB_TRIM OTA_CURRENT 4200
ETIA SUM_OUT 0 0 OTA_CURRENT 1e6
RLOAD SUM_OUT 0 100k
.tran 1u 4m
.measure tran out_max MAX v(SUM_OUT) FROM=2m TO=4m
.measure tran out_min MIN v(SUM_OUT) FROM=2m TO=4m
.end
'''


def main():
    DIR.mkdir(exist_ok=True);results=[]
    deck=DIR/'mix5-ideal.cir';deck.write_text(mixer5());output=run(deck)
    match=re.search(r'^0\s+([-+\d.eE]+)\s+([-+\d.eE]+)',output,re.M)
    op={'sum_prelevel':float(match[1]),'sum_out':float(match[2])} if match else {}
    if len(op)!=2:raise RuntimeError(output)
    assert abs(op['sum_prelevel']+10)<.01,op
    assert abs(op['sum_out']-5)<.01,op
    results.append({'deck':str(deck.relative_to(ROOT)),'status':'PASS - ideal model only','result_V':op,'condition':'All five inputs +5 V, all input attenuverters at +1, LEVEL at midpoint. No saturation or tolerance modeled.'})
    for command in (0,2.5,5):
        for amplitude in (1,5):
            deck=DIR/f'mix4-vendor-{str(command).replace(".","p")}-{amplitude}v.cir';deck.write_text(mixer4(command,amplitude));output=run(deck)
            values={k:float(v) for k,v in re.findall(r'^(out_(?:max|min))\s*=\s*([-+\d.eE]+)',output,re.M)}
            if len(values)!=2:raise RuntimeError(output)
            results.append({'deck':str(deck.relative_to(ROOT)),'status':'MODEL TARGET FAIL - exceeds ±10 V' if max(abs(v) for v in values.values())>10 else 'MEASURED - vendor single OTA model only','command_V':command,
                        'imposed_bias_uA':command*100,'input_peak_each_V':amplitude,'output_extrema_V':values,
                        'condition':'Four coherent 1 kHz sine inputs; 100k/100 Ω OTA input divider; ideal ±12 V amplifier stages and 104.2k TIA feedback.'})
    report={'schema_version':1,'authority':'PROPOSAL - unvalidated','oracle':'KiCad 10.0.6 ngspice via scripts/kicad/run.sh',
            'status':'Bounded ideal/Macromodel diagnostics only; no qualification',
            'runs':results,
            'not_run':[{'subject':'MIX4 complete VCA linearity, feedthrough, control servo, headroom, stability, negative CV and temperature','status':'NOT RUN','reason':'Retained LM13700 model is one OTA only and warns bandwidth/phase margin overestimate >2x; ideal amplifier and imposed bias fixtures omit real servo, saturation and package effects.'},
                       {'subject':'MIX5 cable stability, short/fault protection, ±10 V internal headroom and clip window tolerance','status':'NOT RUN','reason':'No complete vendor models or hardware bench measurements for full signal chain.'}]}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n')
    for row in results:print(row)

if __name__=='__main__':main()
