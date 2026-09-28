"""F1--F3 four-OTA state-variable filter and parallel dry VCA draft.

PROPOSAL: G06 GAIN affects dry OUT only; owner confirmation remains open.
Component index reservation 21--23. All timing nodes are local and Sensitive.
"""
from dataclasses import replace
from design.spec.modules.io_partition import refined
from collections import defaultdict
import json
from scripts.schgen.core import Family, Instance
from design.spec.modules.oscillator import Builder, PLACEMENTS, RAILS
from design.spec.cells._builder import ROOT, SHORTLIST, CATALOG, cell_parts, load_symbol, STANDARD
from design.spec.modules.sample_hold import footprint

INSTANCES=('F1','F2','F3')
INPUTS=('IN','FREQ','RES','GAIN')
OUTPUTS=('LP','BP','HP','OUT')
CONTROLS=('FREQ','RES','GAIN','FREQ±','RES±','GAIN±')
PANEL=tuple('J:{}.{}'.format('{}',k) for k in INPUTS+OUTPUTS)+tuple('C:{}.{}'.format('{}',k) for k in CONTROLS)+tuple('L:{}.{}.mag'.format('{}',k) for k in INPUTS)
SENSITIVE=('BP_INT','LP_INT','EXPO_EMITTER','EXPO_REFERENCE','EXPO_COLLECTOR')


def panel_bindings():
    rows=[]
    for instance in INSTANCES:
        for template in PANEL:
            uid=template.format(instance);p=PLACEMENTS[uid]
            rows.append({'instance':instance,'uid':uid,'ref':p['ref'],'x_mm':p['x_mm'],'y_mm':p['y_mm']})
    assert len(rows)==len({r['uid'] for r in rows})==54
    return rows


class FilterBuilder(Builder):
    def __init__(self):super().__init__('FILTER_CORE:${SHEETNAME}')

    def panel_attributes(self,template):
        return ({'PanelUid':template.replace('{}','${SHEETNAME}')},{i:PLACEMENTS[template.format(i)]['ref'] for i in INSTANCES}) if template else ({'PanelUid':''},{})

    def cell(self,id,tag,nets,*,panel=None,led=False):
        uid=(panel or 'J:{}.IN').format('F1')
        for p in cell_parts(id,uid,nets,ordinal_start=1,instance_tag=tag):
            attrs={**p.attributes,'PanelUid':'','Island':'FILTER_LEDS:${SHEETNAME}' if led else self.island};refs={}
            if panel and (p.prefix=='RV' or (led and p.symbol.endswith('0603Whitelight_C2290'))):
                x,refs=self.panel_attributes(panel);attrs.update(x)
                if not led:attrs['Island']=''
            self.parts.append(replace(p,attributes=attrs,panel_refs=refs))

    def complete(self):
        # Keep the four indicator drivers with their LEDs, on an island separate
        # from the integrators. Pack quads independently in each physical island.
        led=[p for p in self.parts if p.attributes.get('Island')=='FILTER_LEDS:${SHEETNAME}']
        core=[p for p in self.parts if p not in led]
        compiled=[]
        for tag,parts in [('CORE',core),('LED',led)]:
            builder=Builder();builder.parts=parts
            f=builder.finish('filter',globals=RAILS)
            for p in f.parts:
                attrs={**p.attributes,'Role':p.attributes.get('Role','').replace('oscillator:','filter:')}
                if p.key.startswith('C_DEC_'):attrs['Island']='FILTER_'+('LEDS' if tag=='LED' else 'CORE')+':${SHEETNAME}'
                compiled.append(replace(p,key=tag+'_'+p.key,attributes=attrs))
        assigned={};counts=defaultdict(int);out=[]
        for p in compiled:
            prefix='R' if p.prefix=='RB' else p.prefix;package=p.key.rsplit('.',1)[0];group=(prefix,package)
            if group not in assigned:counts[prefix]+=1;assigned[group]=counts[prefix]
            n=assigned[group];finalprefix=prefix if n<=99 else prefix+'B';ordinal=(n-1)%99+1
            i=len(out);out.append(replace(p,prefix=finalprefix,ordinal=ordinal,x=45.72+(i%17)*63.5,y=66.04+(i//17)*38.1))
        return Family('filter',tuple(out),global_nets=RAILS,sensitive_nets=SENSITIVE,paper='A0')


@refined
def family():
    panel_bindings();b=FilterBuilder()
    b.cell('reference_generator','LOCAL',{'REF_5V':'REF5','REF_N5V':'REFN5'})
    for k in INPUTS:
        b.device('WQP518MA','J_'+k,'J',{'T':k+'_TIP','S':'AGND','TN':None},panel='J:{}.{}'.format('{}',k),island='')
        b.cell('input_fault_switch',k,{'JACK':k+'_TIP','PROTECTED':k+'_PROTECTED'})
        b.cell('high_impedance_input',k,{'PROTECTED':k+'_PROTECTED','BUFFERED':k+'_BUFFER'})
        b.cell('magnitude_indicator',k,{'MONITOR':k+'_BUFFER'},panel='L:{}.{}.mag'.format('{}',k),led=True)
    for k in ('FREQ','RES','GAIN'):
        b.cell('remote_buffer',k,{'SIGNAL':k+'_BUFFER','REMOTE':k+'_REMOTE'})
        b.cell('bipolar_attenuverter',k,{'REMOTE_INPUT':k+'_REMOTE','BUFFERED_INPUT':k+'_BUFFER','OUT':k+'_DEPTH'},panel='C:{}.{}±'.format('{}',k))
        b.cell('dc_control_source',k,{'REF_LOW':'AGND','REF_HIGH':'REF5','OUT':k+'_MANUAL'},panel='C:{}.{}'.format('{}',k))
    # Exponential command: 2*(manual-2.5 V)+attenuverted CV, ~1 V/oct.
    b.amp('FREQ_SUM','cv','AGND','FREQ_SUM','FREQ_NEG')
    for key,value,net in [('MAN','50 kΩ','FREQ_MANUAL'),('CV','100 kΩ','FREQ_DEPTH'),('OFFSET','100 kΩ','REFN5')]:b.r('FREQ_'+key,value,net,'FREQ_SUM')
    b.r('FREQ_FEEDBACK','100 kΩ','FREQ_NEG','FREQ_SUM')
    b.amp('EXPO_SCALE','precision','AGND','EXPO_SCALE_SUM','EXPO_COMMAND')
    b.r('EXPO_SCALE_IN','100 kΩ','FREQ_NEG','EXPO_SCALE_SUM');b.r('EXPO_SCALE_FIXED','1.3 kΩ','EXPO_COMMAND','EXPO_SCALE_TRIM');b.trim('EXPO_SCALE_TRIM','1 kΩ','EXPO_SCALE_TRIM','EXPO_SCALE_SUM')
    b.r('EXPO_BASE_LIMIT','1 kΩ','EXPO_COMMAND','EXPO_BASE')
    b.amp('EXPO_SERVO','precision','AGND','EXPO_REFERENCE','EXPO_EMITTER')
    b.r('EXPO_REF_FIXED','300 kΩ','REF5','EXPO_REF_TRIM');b.trim('EXPO_BASE_TRIM','50 kΩ','EXPO_REF_TRIM','EXPO_REFERENCE')
    b.device('BCM847BS_115','EXPO_PAIR','Q',{'1':'EXPO_EMITTER','2':'AGND','3':'EXPO_COLLECTOR','4':'EXPO_EMITTER','5':'EXPO_BASE','6':'EXPO_REFERENCE'})
    b.r('EXPO_MAX_CURRENT','22 kΩ','MIRROR_BASE','EXPO_COLLECTOR')
    b.device('MMBT3906_215','MIRROR_REF','Q',{'1':'MIRROR_BASE','2':'+12V','3':'MIRROR_BASE'})
    for k in ('BP','LP'):
        b.device('MMBT3906_215','MIRROR_'+k,'Q',{'1':'MIRROR_BASE','2':'+12V','3':k+'_BIAS_SOURCE'})
        b.r(k+'_BIAS_LIMIT','22 kΩ',k+'_BIAS_SOURCE',k+'_IABC')
    # State-variable loop: HP=IN-LP-2*BP-RES_NEG; RES_NEG=-g*BP.
    b.r('HP_IN_TOP','40 kΩ','IN_BUFFER','HP_PLUS');b.r('HP_IN_BOTTOM','10 kΩ','HP_PLUS','AGND')
    b.amp('HP_SUM','audio','HP_PLUS','HP_SUM','HP_CORE')
    for key,value,net in [('BP','50 kΩ','BP_CORE'),('LP','100 kΩ','LP_CORE'),('RES','100 kΩ','RES_NEG')]:b.r('HP_'+key,value,net,'HP_SUM')
    b.r('HP_FEEDBACK','100 kΩ','HP_CORE','HP_SUM')
    for k,input in [('BP','HP_CORE'),('LP','BP_CORE'),('RES','BP_CORE'),('DRY','IN_BUFFER')]:
        b.r(k+'_ATTEN_TOP','100 kΩ',input,k+'_OTA_SIGNAL');b.r(k+'_ATTEN_BOTTOM','200 Ω',k+'_OTA_SIGNAL','AGND')
        b.trim(k+'_OFFSET','10 kΩ','REFN5',k+'_OFFSET_TRIM','REF5')
        b.r(k+'_OFFSET_FEED','470 kΩ',k+'_OFFSET_TRIM',k+'_OFFSET');b.r(k+'_OFFSET_RETURN','1 kΩ',k+'_OFFSET','AGND')
    b.c('BP_INTEGRATOR','150 pF C0G','BP_INT','AGND');b.c('LP_INTEGRATOR','150 pF C0G','LP_INT','AGND')
    b.amp('BP_BUFFER','audio','BP_INT','BP_CORE','BP_CORE');b.amp('LP_BUFFER','audio','LP_INT','LP_CORE','LP_CORE')
    # Current sources for resonance and dry VCA. PNP emitter servo provides
    # commanded current, and independent collector resistance limits fault bias.
    b.r('REF25_TOP','100 kΩ','REF5','REF25');b.r('REF25_BOTTOM','100 kΩ','REF25','AGND')
    for role,source,rsense in [('RES','RES','49.9 kΩ'),('DRY','GAIN','12.4 kΩ')]:
        b.amp(role+'_CONTROL_SUM','cv','AGND',role+'_CONTROL_SUM',role+'_CONTROL_NEG')
        for tag in ('MANUAL','DEPTH'):b.r(role+'_CONTROL_'+tag,'100 kΩ',source+'_'+tag,role+'_CONTROL_SUM')
        b.r(role+'_CONTROL_FEEDBACK','100 kΩ',role+'_CONTROL_NEG',role+'_CONTROL_SUM')
        b.amp(role+'_CONTROL_INVERT','cv','AGND',role+'_CONTROL_INV',role+'_CONTROL_RAW')
        b.r(role+'_CONTROL_INV_IN','100 kΩ',role+'_CONTROL_NEG',role+'_CONTROL_INV');b.r(role+'_CONTROL_INV_FB','100 kΩ',role+'_CONTROL_RAW',role+'_CONTROL_INV')
        b.r(role+'_CONTROL_LIMIT','10 kΩ',role+'_CONTROL_RAW',role+'_CONTROL_CLAMP')
        b.device('BAT54S_215',role+'_CONTROL_CLAMP','D',{'1':'AGND','3':role+'_CONTROL_CLAMP','2':'REF5'})
        b.amp(role+'_CONTROL_BUFFER','cv',role+'_CONTROL_CLAMP',role+'_COMMAND',role+'_COMMAND')
        b.amp(role+'_EMITTER_TARGET','cv','REF25',role+'_TARGET_SUM',role+'_TARGET')
        b.r(role+'_TARGET_IN','100 kΩ',role+'_COMMAND',role+'_TARGET_SUM');b.r(role+'_TARGET_FB','100 kΩ',role+'_TARGET',role+'_TARGET_SUM')
        b.amp(role+'_CURRENT_SERVO','cv',role+'_TARGET',role+'_EMITTER',role+'_BASE_DRIVE')
        b.r(role+'_SENSE',rsense,'REF5',role+'_EMITTER');b.r(role+'_BASE_R','10 kΩ',role+'_BASE_DRIVE',role+'_BASE')
        b.device('MMBT3906_215',role+'_PNP','Q',{'1':role+'_BASE','2':role+'_EMITTER','3':role+'_CURRENT'})
        b.device(CATALOG[SHORTLIST['signal_diode']['mpn']],role+'_REVERSE_BE','D',{'2':role+'_BASE','1':role+'_EMITTER'})
        b.c(role+'_SERVO_COMP','100 pF',role+'_BASE_DRIVE',role+'_EMITTER')
        b.r(role+'_IABC_LIMIT','22 kΩ',role+'_CURRENT',role+'_IABC')
    # Two packages, four OTAs; Darlington buffers unused and their inputs grounded.
    def ota(key,a,z):
        b.device('LM13700M_NOPB',key,'U',{'1':a+'_IABC','2':None,'3':a+'_OTA_SIGNAL','4':a+'_OFFSET','5':a+'_INT','6':'-12V','7':'AGND','8':None,'9':None,'10':'AGND','11':'+12V','12':z+'_INT','13':z+'_OFFSET' if z!='DRY' else z+'_OTA_SIGNAL','14':z+'_OTA_SIGNAL' if z!='DRY' else z+'_OFFSET','15':None,'16':z+'_IABC'})
    ota('OTA_INTEGRATORS','BP','LP');ota('OTA_GAIN_RESONANCE','RES','DRY')
    b.amp('RESONANCE_TIA','audio','AGND','RES_INT','RES_NEG')
    b.r('RESONANCE_FIXED','330 kΩ','RES_NEG','RESONANCE_TRIM');b.trim('RESONANCE_MAX','500 kΩ','RESONANCE_TRIM','RES_INT')
    # Eight diodes each way plus 100k in the feedback path lower incremental
    # resonance gain when oscillation grows. Threshold is device/current dependent.
    b.r('RESONANCE_LIMIT_R','100 kΩ','RES_NEG','RES_LIMIT')
    for polarity in ('POS','NEG'):
        previous='RES_LIMIT'
        for i in range(8):
            end='RES_INT' if i==7 else 'RES_'+polarity+str(i)
            a,k=(previous,end) if polarity=='POS' else (end,previous)
            b.device(CATALOG[SHORTLIST['signal_diode']['mpn']],'RES_LIMIT_'+polarity+str(i),'D',{'2':a,'1':k});previous=end
    b.amp('DRY_TIA','audio','AGND','DRY_INT','DRY_CORE');b.r('DRY_GAIN','68.1 kΩ','DRY_CORE','DRY_INT')
    for k,net in [('LP','LP_CORE'),('BP','BP_CORE'),('HP','HP_CORE'),('OUT','DRY_CORE')]:
        b.cell('general_output',k,{'SIGNAL':net,'JACK':k+'_TIP'})
        b.device('WQP518MA','J_'+k,'J',{'T':k+'_TIP','S':'AGND','TN':None},panel='J:{}.{}'.format('{}',k),island='')
    return b.complete()


def specification():return (family(),),tuple(Instance('filter',name,21+i) for i,name in enumerate(INSTANCES))
