"""OSC-ES-1 oscillator and shared octave draft; no bench/tracking claim.

Reserved master indices: O1..O5 = 11..15; OCTAVE_REF = 16.
ALFA 2020 v7 source/pin evidence: design/standard/pin-maps/vco.json.
"""
from collections import defaultdict
from dataclasses import replace
import json, re
from scripts.schgen.core import Family, Instance, Part
from design.spec.cells._builder import ROOT, STANDARD, SHORTLIST, CATALOG, CELLS, cell_parts, load_symbol
from design.spec.modules.sample_hold import footprint

INSTANCES = ('O1','O2','O3','O4','O5')
RAILS = ('+12V','-12V','+5V','AGND')
REFS = ('OSC_REF5','OSC_REFN5','OSC_GATE_REF',*(f'OSC_OCT{i}' for i in range(6)))
PLACEMENTS = {p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
PANEL = tuple('J:{}.{}'.format('{}', k) for k in ('1V','FM','PWM','SYNC','SIN','TRI','SAW','PUL')) + tuple('C:{}.{}'.format('{}',k) for k in ('OCT','VCO/LFO','SYNC','TUNE','FINE','FM±','PW','PWM±'))


def panel_bindings():
    rows=[]
    for instance in INSTANCES:
        for template in PANEL:
            uid=template.format(instance); p=PLACEMENTS[uid]
            rows.append({'instance':instance,'uid':uid,'ref':p['ref'],'x_mm':p['x_mm'],'y_mm':p['y_mm']})
    assert len(rows)==len({r['uid'] for r in rows})==80
    return rows


class Builder:
    def __init__(self, island='OSC_CORE:${SHEETNAME}'):
        self.parts=[]; self.island=island

    def panel_attributes(self, template):
        return ({'PanelUid':template.replace('{}','${SHEETNAME}')},
                {i:PLACEMENTS[template.format(i)]['ref'] for i in INSTANCES}) if template else ({'PanelUid':''},{})

    def device(self, name, key, prefix, pins, *, value=None, panel=None, mpn=None, island=None):
        symbol=load_symbol(name)
        props=dict(re.findall(r'\(property "([^\"]+)" "([^\"]*)"',symbol.body))
        identity=props.get('MPN','') if mpn is None else mpn
        attrs={'Role':'oscillator:'+key,'MPN':identity,'Manufacturer':props.get('Manufacturer','') if identity else '', 'LCSC':props.get('LCSC','') if identity else '', 'Island':self.island if island is None else island}
        panelattrs,refs=self.panel_attributes(panel);attrs.update(panelattrs)
        allpins={p.number for ps in symbol.units.values() for p in ps}
        if set(pins)!=allpins:raise ValueError((name,key,set(pins)^allpins))
        for unit,ps in symbol.units.items():
            if not ps:continue
            self.parts.append(Part(f'{key}.{unit}',symbol.lib_id,prefix,1,unit,50.8,50.8,{p.number:pins[p.number] for p in ps},value=value or props.get('MPN',name),footprint=footprint(symbol),attributes=attrs,panel_refs=refs))

    def passive(self, kind, key, value, a, b):
        identity='r_precision' if kind=='R' else ('c_bypass' if value=='100 nF' else 'c_small')
        exact=(kind=='R' and value=='100 kΩ') or (kind=='C' and value in ('100 pF','100 nF'))
        self.device(CATALOG[SHORTLIST[identity]['mpn']],kind+'_'+key,kind,{'1':a,'2':b},value=value,mpn=None if exact else '')

    def r(self,key,value,a,b):self.passive('R',key,value,a,b)
    def c(self,key,value,a,b):self.passive('C',key,value,a,b)

    def amp(self,key,role,plus,minus,out):
        record=SHORTLIST[STANDARD['roles'][role]['part_id']]
        self.device(CATALOG[record['mpn']],key,'U',{str(n):{1:out,2:minus,3:plus,4:'+12V',11:'-12V'}.get(n) for n in range(1,15)})

    def trim(self,key,value,a,w,b=None):
        identity='trim_102' if value=='1 kΩ' else 'trim_103'
        self.device(CATALOG[SHORTLIST[identity]['mpn']],key,'RV',{'1':a,'2':w,'3':b or w},value=value,mpn=SHORTLIST[identity]['mpn'] if value in ('1 kΩ','10 kΩ') else '')

    def cell(self,id,tag,nets,*,panel=None,role=None):
        uid=(panel or 'J:{}.1V').format('O1')
        generated=cell_parts(id,uid,nets,ordinal_start=1,instance_tag=tag)
        for p in generated:
            attrs={**p.attributes,'PanelUid':'','Island':self.island};refs={}
            if panel and p.prefix=='RV':
                x,refs=self.panel_attributes(panel);attrs.update(x);attrs['Island']=''
            if role and p.symbol.split(':')[-1].startswith('OPA'):
                record=SHORTLIST[STANDARD['roles'][role]['part_id']];symbol=load_symbol(CATALOG[record['mpn']])
                attrs.update(MPN=record['mpn'],Manufacturer=record['manufacturer'],LCSC=record['lcsc'])
                p=replace(p,symbol=symbol.lib_id,footprint=footprint(symbol),value=record['mpn'])
            self.parts.append(replace(p,attributes=attrs,panel_refs=refs))

    def finish(self,name,*,sensitive=(),globals=RAILS+REFS):
        # Pack amplifier channels on the same explicitly local island. Standard
        # cell compiler emits whole quads; preserve every used channel and tie
        # unused channels as followers at ground, including power units.
        groups=defaultdict(list);rest=[]
        for p in self.parts:
            if p.symbol.endswith(('OPA4196IDR','OPA4197IPWR')):
                if p.unit==1:groups[(p.symbol,p.attributes['Island'])].append(p)
            else:rest.append(p)
        for (symbol,island),channels in groups.items():
            maps=[{'1':'1','2':'2','3':'3'},{'1':'7','2':'6','3':'5'},{'1':'8','2':'9','3':'10'},{'1':'14','2':'13','3':'12'}]
            for start in range(0,len(channels),4):
                batch=channels[start:start+4];base=batch[0];stem=f'PACK_{symbol.split(":")[-1]}_{start//4}'
                for n,mapping in enumerate(maps):
                    if n<len(batch):
                        q=batch[n];pins={mapping[k]:q.pins[k] for k in ('1','2','3')};attrs={**q.attributes,'LogicalCellKey':q.key}
                    else:
                        q=base;out=stem+'_UNUSED'+str(n);pins={mapping['1']:out,mapping['2']:out,mapping['3']:'AGND'};attrs={**base.attributes,'Role':'oscillator:unused grounded follower','LogicalCellKey':''}
                    rest.append(replace(q,key=stem+f'.{n+1}',unit=n+1,pins=pins,attributes=attrs))
                rest.append(replace(base,key=stem+'.5',unit=5,pins={'4':'+12V','11':'-12V'},attributes={**base.attributes,'Role':'oscillator:package supply'}))
        self.parts=rest
        # Bypass every physical IC rail. The core negative bypass is local VEE5.
        packages={}
        for p in self.parts:
            if p.prefix=='U':packages[p.key.rsplit('.',1)[0]]=p
        for key,p in packages.items():
            sym=p.symbol.split(':')[-1]
            rails=('+5V',) if sym=='SN74HC14DR' else ('NOISE_VDD',) if sym=='NOISE2' else ('+12V',) if sym in ('LM393BIDR','REF5050AIDR') else ('+12V','VEE5') if sym=='AS3340D' else ('+12V','-12V')
            for j,rail in enumerate(rails):self.c('DEC_'+key+'_'+str(j),'100 nF',rail,'AGND')
        assigned={};counts=defaultdict(int);out=[]
        for p in self.parts:
            stem=p.key.rsplit('.',1)[0];group=(p.prefix,stem)
            if group not in assigned:counts[p.prefix]+=1;assigned[group]=counts[p.prefix]
            number=assigned[group]
            # Extra resistor banks use an explicit valid reference prefix rather
            # than expanding the generator's fixed 100-reference instance stride.
            # Internal diodes/trimmers must not collide with fixed envelope
            # D13xx / RV13xx panel references. Preserve panel references.
            base_prefix=p.prefix+'O' if name=='oscillator' and p.prefix in ('D','RV') and not p.panel_refs else p.prefix
            prefix=base_prefix if number<=99 else base_prefix+'B'
            number=(number-1)%99+1
            n=len(out);columns=8 if name=='octave_reference' else 17
            out.append(replace(p,prefix=prefix,ordinal=number,page=1,x=45.72+(n%columns)*63.5,y=66.04+(n//columns)*38.1))
        return Family(name,tuple(out),global_nets=globals,sensitive_nets=sensitive,paper='A2' if name=='octave_reference' else 'A0')


def family():
    panel_bindings();b=Builder()
    for key in ('1V','FM','PWM','SYNC'):
        template='J:{}.{}'.format('{}',key)
        b.device('WQP518MA','J_'+key,'J',{'T':key+'_TIP','S':'AGND','TN':None},panel=template,island='')
        b.cell('input_fault_switch',key,{'JACK':key+'_TIP','PROTECTED':key+'_PROTECTED'})
        b.cell('high_impedance_input',key,{'PROTECTED':key+'_PROTECTED','BUFFERED':key+'_BUFFER'},role='precision' if key=='1V' else 'cv')
    for key in ('FM','PWM'):
        b.cell('remote_buffer',key,{'SIGNAL':key+'_BUFFER','REMOTE':key+'_REMOTE'})
        b.cell('bipolar_attenuverter',key,{'REMOTE_INPUT':key+'_REMOTE','BUFFERED_INPUT':key+'_BUFFER','OUT':key+'_DEPTH'},panel='C:{}.{}±'.format('{}',key))
    for key in ('TUNE','FINE','PW'):
        b.cell('dc_control_source',key,{'REF_LOW':'AGND' if key=='PW' else 'OSC_REFN5','REF_HIGH':'OSC_REF5','OUT':key+'_MANUAL'},panel='C:{}.{}'.format('{}',key),role='precision' if key!='PW' else 'cv')
    # All octave taps are shared buffered references; the selected contact is
    # filtered and rebuffered locally. Open contact tends to zero octaves.
    pins={'1':'OCT_SELECTED','10':'OCT_SELECTED','8':None,'9':None,'MP1':None,'MP2':None,**{str(i+2):f'OSC_OCT{i}' for i in range(6)}}
    b.device('SRBV160803','OCT_SELECTOR','SW',pins,panel='C:{}.OCT',island='')
    b.r('OCT_SER','1 kΩ','OCT_SELECTED','OCT_FILTER');b.r('OCT_PD','10 MΩ','OCT_FILTER','AGND');b.c('OCT_FILTER','100 nF','OCT_FILTER','AGND');b.amp('OCT_RECEIVER','precision','OCT_FILTER','OCT_CV','OCT_CV')
    b.amp('LFO_OFFSET','cv','OSC_REFN5','LFO_FB','LFO_REF');b.r('LFO_RF','40 kΩ','LFO_REF','LFO_FB');b.r('LFO_RG','100 kΩ','LFO_FB','AGND')
    b.device('2MS1T1B1M2QES-5','RANGE','SW',{'3':'LFO_REF','2':'RANGE_CV','1':'AGND'},panel='C:{}.VCO/LFO',island='')
    b.r('RANGE_PD','10 MΩ','RANGE_CV','AGND')
    for key,value,net in [('PITCH','100 kΩ','1V_BUFFER'),('OCT','100 kΩ','OCT_CV'),('TUNE','250 kΩ','TUNE_MANUAL'),('FINE','5 MΩ','FINE_MANUAL'),('FM','200 kΩ','FM_DEPTH'),('RANGE','100 kΩ','RANGE_CV'),('BIAS','82.5 kΩ','OSC_REF5')]:b.r('PITCH_'+key,value,net,'EXPO_SUM')
    b.trim('BASE_TRIM','10 kΩ','OSC_REFN5','BASE_ADJ','OSC_REF5');b.r('BASE_FEED','1 MΩ','BASE_ADJ','EXPO_SUM')
    # ALFA external -5 V recommendation avoids contradictory internal-zener
    # narrative versus VEE absolute limit. Driver/load sequencing remains a gate.
    b.amp('VEE_DRIVER','precision','OSC_REFN5','VEE_FB','VEE_DRIVE');b.r('VEE_ISO','100 Ω','VEE_DRIVE','VEE5');b.r('VEE_FB','10 kΩ','VEE5','VEE_FB');b.c('VEE_FAST','100 pF','VEE_DRIVE','VEE_FB')
    b.device('AS3340D','CORE','U',{str(i):net for i,net in enumerate(['SCALE1','SCALE2','VEE5','PULSE_RAW','PWM_PIN','HARD_PIN','HF_PIN','SAW_RAW','SOFT_PIN','TRI_RAW','TIMING_CAP','AGND','LINEAR_REF','SCALE_PIN','EXPO_SUM','+12V'],1)})
    b.parts.append(Part('VEE_POWER_FLAG','Fixture:PWR_FLAG','#FLG',1,0,50.8,50.8,{'1':'VEE5'},value='LOCAL_BUFFER_SUPPLY',attributes={'Role':'oscillator:driven local -5 V declaration','MPN':'','Manufacturer':'','LCSC':'','PanelUid':'','Island':b.island}))
    b.r('RZ_FIXED','24 kΩ','SCALE1','RZ_TRIM');b.trim('RZ_TRIM','10 kΩ','RZ_TRIM','AGND')
    b.r('RT','5.72 kΩ','SCALE2','AGND')
    b.r('RS_FIXED','1.5 kΩ','SCALE_PIN','SCALE_ADJ');b.trim('SCALE_TRIM','1 kΩ','SCALE_ADJ','AGND')
    b.c('SCALE_BYPASS','100 nF','SCALE_PIN','AGND');b.c('CF','1 nF C0G','TIMING_CAP','AGND')
    b.r('LINEAR_REFERENCE','1.2 MΩ','+12V','LINEAR_REF');b.r('LINEAR_FILTER','470 Ω','LINEAR_REF','LINEAR_FILTER');b.c('LINEAR_FILTER','10 nF','LINEAR_FILTER','AGND')
    b.trim('HF_TRIM','20 kΩ','HF_PIN','LINEAR_REF','AGND')
    b.r('PULSE_LOAD','51 kΩ','PULSE_RAW','AGND')
    b.cell('gate_trigger_input','SYNC',{'BUFFERED':'SYNC_BUFFER','REF_5V':'OSC_REF5','GATE_REF':'OSC_GATE_REF','GATE_HIGH':'SYNC_GATE'})
    b.device('2MS3T1B1M2QES','SYNC_SELECT','SW',{'2':'SYNC_GATE','3':'SOFT_DRIVE','1':'HARD_DRIVE'},panel='C:{}.SYNC',island='')
    for mode in ('SOFT','HARD'):
        b.r(mode+'_PD','100 kΩ',mode+'_DRIVE','AGND');b.r(mode+'_LIMIT','10 kΩ',mode+'_DRIVE',mode+'_EDGE');b.c(mode+'_AC','1 nF',mode+'_EDGE',mode+'_PIN')
    # PWM command .2 + .72*manual + .36*depth, then clamp near 0..4 V.
    b.amp('PWM_SUM','cv','AGND','PWM_SUM','PWM_NEG');b.r('PWM_FB','72 kΩ','PWM_NEG','PWM_SUM')
    for name,value,net in [('MAN','100 kΩ','PW_MANUAL'),('CV','200 kΩ','PWM_DEPTH'),('OFFSET','1.8 MΩ','OSC_REF5')]:b.r('PWM_'+name,value,net,'PWM_SUM')
    b.amp('PWM_INVERT','cv','AGND','PWM_INV','PWM_DRIVE');b.r('PWM_INV_IN','100 kΩ','PWM_NEG','PWM_INV');b.r('PWM_INV_FB','100 kΩ','PWM_DRIVE','PWM_INV')
    b.r('REF4_TOP','25 kΩ','OSC_REF5','REF4_RAW');b.r('REF4_BOT','100 kΩ','REF4_RAW','AGND');b.amp('REF4','cv','REF4_RAW','REF4','REF4')
    b.r('PWM_LIMIT','10 kΩ','PWM_DRIVE','PWM_PIN');b.device('BAT54S_215','PWM_CLAMP','D',{'1':'AGND','3':'PWM_PIN','2':'REF4'})
    # Scale inferred raw 0..4 V triangle / 0..8 V saw at +12 V.
    for key,rinput,rtop in [('TRI','40 kΩ','250 kΩ'),('SAW','80 kΩ','125 kΩ')]:
        b.r(key+'_BIAS_TOP',rtop,'OSC_REF5',key+'_BIAS');b.r(key+'_BIAS_BOT','100 kΩ',key+'_BIAS','AGND')
        b.amp(key+'_SCALE','audio',key+'_BIAS',key+'_SUM',key+'_SCALED');b.r(key+'_IN',rinput,key+'_RAW',key+'_SUM');b.r(key+'_FB','100 kΩ',key+'_SCALED',key+'_SUM')
    # Pulse is squared in a 0/5 V domain so its amplitude does not depend on
    # the unqualified AS3340 pulse high level at +12 V.
    b.r('PUL_DIV_TOP','100 kΩ','PULSE_RAW','PULSE_HALF');b.r('PUL_DIV_BOT','100 kΩ','PULSE_HALF','AGND')
    b.r('REF25_TOP','100 kΩ','OSC_REF5','REF25');b.r('REF25_BOT','100 kΩ','REF25','AGND')
    b.device('LM393BIDR','PULSE_CMP','U',{'1':'PULSE_LOGIC','2':'PULSE_HALF','3':'REF25','4':'AGND','5':'AGND','6':'+5V','7':None,'8':'+12V'})
    b.r('PUL_PULL','4.7 kΩ','+5V','PULSE_LOGIC');b.amp('PUL_SCALE','audio','PULSE_LOGIC','PUL_SUM','PUL_SCALED');b.r('PUL_RF','100 kΩ','PUL_SCALED','PUL_SUM');b.r('PUL_RREF','100 kΩ','OSC_REF5','PUL_SUM')
    # Matched-pair soft saturation: approximately tanh(Vdiff/(2*VT)).
    b.r('SINE_ATTEN','68 kΩ','TRI_SCALED','SINE_BASE');b.r('SINE_BASE_GND','1 kΩ','SINE_BASE','AGND')
    b.trim('SINE_SYMMETRY','10 kΩ','OSC_REFN5','SINE_OFFSET','OSC_REF5');b.r('SINE_OFFSET','1 MΩ','SINE_OFFSET','SINE_BASE')
    b.device('BCM847BS_115','SINE_PAIR','Q',{'1':'SINE_TAIL','2':'SINE_BASE','3':'SINE_C2','4':'SINE_TAIL','5':'AGND','6':'SINE_C1'})
    b.r('SINE_TAIL','10 kΩ','SINE_TAIL','-12V')
    for n in (1,2):b.r(f'SINE_COLLECTOR{n}','10 kΩ','+12V',f'SINE_C{n}')
    b.amp('SINE_DIFF','audio','SINE_PLUS','SINE_MINUS','SINE_DIFF')
    for key,a,z in [('PLUS','SINE_C2','SINE_PLUS'),('GROUND','SINE_PLUS','AGND'),('MINUS','SINE_C1','SINE_MINUS'),('FB','SINE_DIFF','SINE_MINUS')]:b.r('SINE_DIFF_'+key,'100 kΩ',a,z)
    b.amp('SINE_GAIN','audio','AGND','SINE_GAIN_SUM','SIN_SCALED');b.r('SINE_GAIN_IN','100 kΩ','SINE_DIFF','SINE_GAIN_SUM');b.r('SINE_GAIN_FIXED','49.9 kΩ','SIN_SCALED','SINE_GAIN_TRIM');b.trim('SINE_LEVEL','10 kΩ','SINE_GAIN_TRIM','SINE_GAIN_SUM')
    for key in ('SIN','TRI','SAW','PUL'):
        b.cell('general_output',key,{'SIGNAL':key+'_SCALED','JACK':key+'_TIP'})
        b.device('WQP518MA','J_'+key,'J',{'T':key+'_TIP','S':'AGND','TN':None},panel='J:{}.{}'.format('{}',key),island='')
    return b.finish('oscillator',sensitive=('TIMING_CAP','EXPO_SUM','SCALE_PIN','SCALE1','SCALE2','LINEAR_REF','HF_PIN'))


def octave_family():
    b=Builder('OSC_SHARED_REFERENCE')
    b.cell('reference_generator','SHARED',{'REF_5V':'OSC_REF5','REF_N5V':'OSC_REFN5','GATE_REF':'OSC_GATE_REF'})
    b.cell('octave_reference','SHARED',{'REF_5V':'OSC_REF5','T0':'OCT_BOTTOM','BOTTOM':'OCT_BOTTOM','T5':'OCT_TOP','TOP':'OCT_TOP',**{f'OCT{i}':f'OSC_OCT{i}' for i in range(6)}})
    return b.finish('octave_reference',sensitive=(),globals=RAILS+REFS)


def specification():
    return (family(),octave_family()),tuple(Instance('oscillator',n,11+i) for i,n in enumerate(INSTANCES))+(Instance('octave_reference','OCTAVE_REF',16),)
