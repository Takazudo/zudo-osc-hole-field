"""E1–E6 AR proposal. G07 is specified in envelope_logic.py before capture.

Index allocation 41–46; only rails are global. No physical validation claimed.
"""
from design.spec.modules.io_partition import refined
from collections import defaultdict
from dataclasses import replace
from design.spec.modules.oscillator import Builder,PLACEMENTS,RAILS
from design.spec.cells._builder import ROOT,SHORTLIST,CATALOG,cell_parts
from scripts.schgen.core import Family,Instance
from design.spec.modules.envelope_logic import INSTANCES,EXPRESSIONS

INPUTS=('SIG','RISE','FALL');OUTPUTS=('ENV','BIP','EOC','STG')
PANEL=tuple('J:{}.{}'.format('{}',k) for k in INPUTS+OUTPUTS)+tuple('C:{}.{}'.format('{}',k) for k in ('MODE','SHAPE','STAGE','TRIG','RISE','FALL'))+tuple('L:{}.{}.mag'.format('{}',k) for k in INPUTS)+tuple('L:{}.{}.stage'.format('{}',k) for k in ('RISE','FALL'))
SENSITIVE=('ENV_STORAGE','RISE_EXPO_EMITTER','RISE_EXPO_REF','RISE_EXPO_COLLECTOR','FALL_EXPO_EMITTER','FALL_EXPO_REF','FALL_EXPO_COLLECTOR','EOC_C','EOC_RCX','CLOCK_RC')


def panel_bindings():
 rows=[]
 for i in INSTANCES:
  for t in PANEL:
   uid=t.format(i);p=PLACEMENTS[uid]
   rows.append({'instance':i,'uid':uid,'ref':p['ref'],'x_mm':p['x_mm'],'y_mm':p['y_mm']})
 assert len(rows)==len({r['uid'] for r in rows})==108
 return rows


class EnvelopeBuilder(Builder):
 def __init__(self):super().__init__('ENV_CORE:${SHEETNAME}');self.logic_count=0;self.logic_cache={};self.nand_cache={};self.inversions={}
 def panel_attributes(self,t):
  return ({'PanelUid':t.replace('{}','${SHEETNAME}')},{i:PLACEMENTS[t.format(i)]['ref'] for i in INSTANCES}) if t else ({'PanelUid':''},{})
 def cell(self,id,tag,nets,*,panel=None,led=False):
  for p in cell_parts(id,(panel or 'J:{}.SIG').format('E1'),nets,ordinal_start=1,instance_tag=tag):
   attrs={**p.attributes,'PanelUid':'','Island':'ENV_LEDS:${SHEETNAME}' if led else self.island};refs={}
   if panel and (p.prefix=='RV' or (led and p.symbol.endswith('0603Whitelight_C2290'))):
    a,refs=self.panel_attributes(panel);attrs.update(a)
    if not led:attrs['Island']=''
   self.parts.append(replace(p,attributes=attrs,panel_refs=refs))
 def schmitt(self,key,a,z):self.device('SN74HC14DR',key,'U',{str(i):{1:a,2:z,7:'AGND',14:'+5V'}.get(i) for i in range(1,15)})
 def nand(self,a,b,z=None):
  pair=tuple(sorted((a,b)))
  if z is None and pair in self.nand_cache:return self.nand_cache[pair]
  self.logic_count+=1;z=z or f'L{self.logic_count:03}'
  self.nand_cache[pair]=z
  self.device('SN74HC00DR',f'NAND{self.logic_count}','U',{str(i):{1:a,2:b,3:z,7:'AGND',14:'+5V'}.get(i) for i in range(1,15)})
  return z
 def invert(self,a,out=None):
  if out is None and a in self.inversions:return self.inversions[a]
  z=self.nand(a,a,out);self.inversions[a]=z;self.inversions[z]=a;return z
 def logic(self,e,out=None):
  if isinstance(e,str):return e
  if out is None and e in self.logic_cache:return self.logic_cache[e]
  result=self._logic(e,out)
  if out is None:self.logic_cache[e]=result
  return result
 def _logic(self,e,out=None):
  op,*args=e;v=[self.logic(a) for a in args]
  if op=='not':return self.invert(v[0],out)
  for i,z in enumerate(v[1:]):
   final=out if i==len(v)-2 else None
   if op=='and':n=self.nand(v[0],z);v[0]=self.invert(n,final)
   else:v[0]=self.nand(self.invert(v[0]),self.invert(z),final)
  return v[0]
 def ff(self,key,d,q,reset='READY'):
  self.inversions[q]=q+'_N';self.inversions[q+'_N']=q
  self.device('SN74HC74DR',key,'U',{str(i):{1:reset,2:d,3:'CLOCK',4:'+5V',5:q,6:q+'_N',7:'AGND',14:'+5V'}.get(i) for i in range(1,15)})
 def cmp(self,key,plus,minus,out):
  self.device('LM393BIDR',key,'U',{str(i):{1:out,2:minus,3:plus,4:'AGND',8:'+12V'}.get(i) for i in range(1,9)})
  self.r(key+'_PULL','4.7 kΩ','+5V',out)
 def switch(self,key,channels):
  # ADG5412F channel tuples are (IN,S,D); all four channels captured.
  pins={'13':'+12V','4':'-12V','5':'AGND','12':None}
  for ns,(en,s,d) in zip([('1','3','2'),('16','15','14'),('9','10','11'),('8','7','6')],channels):pins.update(zip(ns,(en,s,d)))
  self.device('ADG5412FBRUZ',key,'U',pins)
 def finish_envelope(self):
  # Pack real logic/comparator channels, preserving canonical pin functions.
  configs={
   'SN74HC14DR':([{'1':str(a),'2':str(z)} for a,z in [(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)]],{'7':'AGND','14':'+5V'},{'1':'AGND','2':None}),
   'SN74HC00DR':([dict(zip(('1','2','3'),map(str,row))) for row in [(1,2,3),(4,5,6),(9,10,8),(12,13,11)]],{'7':'AGND','14':'+5V'},{'1':'AGND','2':'AGND','3':None}),
   'SN74HC74DR':([dict(zip(map(str,range(1,7)),map(str,row))) for row in [(1,2,3,4,5,6),(13,12,11,10,9,8)]],{'7':'AGND','14':'+5V'},{'1':'AGND','2':'AGND','3':'AGND','4':'+5V','5':None,'6':None}),
   'LM393BIDR':([{'1':'1','2':'2','3':'3'},{'1':'7','2':'6','3':'5'}],{'4':'AGND','8':'+12V'},{'1':None,'2':'REF5','3':'AGND'}),
  }
  # Remove gates made redundant by complemented-output sharing.
  while True:
   uses=defaultdict(int)
   for p in self.parts:
    for v in p.pins.values():uses[v]+=1
   dead={p.key.rsplit('.',1)[0] for p in self.parts if p.symbol.endswith('SN74HC00DR') and p.unit==1 and uses[p.pins['3']]==1}
   if not dead:break
   self.parts=[p for p in self.parts if p.key.rsplit('.',1)[0] not in dead]
  groups=defaultdict(list);rest=[]
  for p in self.parts:
   sym=p.symbol.split(':')[-1]
   if sym in configs:
    if p.unit==1:groups[sym].append(p)
   else:rest.append(p)
  for sym,channels in groups.items():
   maps,power,unused=configs[sym]
   for start in range(0,len(channels),len(maps)):
    batch=channels[start:start+len(maps)];base=batch[0];stem=f'LOGIC_{sym}_{start//len(maps)}'
    for n,mapping in enumerate(maps):
     p=batch[n] if n<len(batch) else base;pinmap=p.pins if n<len(batch) else unused
     attrs={**p.attributes,'LogicalCellKey':p.key if n<len(batch) else ''}
     rest.append(replace(p,key=stem+f'.{n+1}',unit=n+1,pins={z:pinmap[a] for a,z in mapping.items()},attributes=attrs))
    rest.append(replace(base,key=stem+f'.{len(maps)+1}',unit=len(maps)+1,pins=power,attributes={**base.attributes,'Role':'envelope:logic supply'}))
  # Unused complement outputs are explicit no-connects, not isolated labels.
  uses=defaultdict(int)
  for p in rest:
   for v in p.pins.values():uses[v]+=1
  rest=[replace(p,pins={k:(None if v and uses[v]==1 and p.symbol.endswith('SN74HC74DR') and k in ('5','6','9','8') else v) for k,v in p.pins.items()}) for p in rest]
  self.parts=rest
  led=[p for p in rest if p.attributes.get('Island')=='ENV_LEDS:${SHEETNAME}'];core=[p for p in rest if p not in led];compiled=[]
  for tag,parts in [('CORE',core),('LED',led)]:
   b=Builder();b.parts=parts
   for p in b.finish('envelope',globals=RAILS).parts:
    if p.key.startswith('C_DEC_'):continue
    compiled.append(replace(p,key=tag+'_'+p.key,attributes={**p.attributes,'Role':p.attributes.get('Role','').replace('oscillator:','envelope:')}))
  self.parts=compiled
  packages={p.key.rsplit('.',1)[0]:p for p in compiled if p.prefix=='U'}
  for key,p in packages.items():
   sym=p.symbol.split(':')[-1];rails=('+5V',) if 'HC' in sym else ('+12V',) if sym in ('LM393BIDR','REF5050AIDR') else ('+12V','-12V')
   old=self.island;self.island=p.attributes['Island']
   for j,rail in enumerate(rails):self.c('DEC_'+key+'_'+str(j),'100 nF',rail,'AGND')
   self.island=old
  counts=defaultdict(int);assigned={};out=[]
  for p in self.parts:
   prefix='R' if p.prefix=='RB' else p.prefix;key=(prefix,p.key.rsplit('.',1)[0])
   if key not in assigned:counts[prefix]+=1;assigned[key]=counts[prefix]
   n=assigned[key];index=len(out)
   out.append(replace(p,prefix=prefix if n<=99 else prefix+'B',ordinal=(n-1)%99+1,x=40.64+(index%22)*50.8,y=50.8+(index//22)*31.75,attributes={**p.attributes,'Role':p.attributes.get('Role','').replace('oscillator:','envelope:')}))
  assert len(out)<=528,len(out)
  return Family('envelope',tuple(out),global_nets=RAILS,sensitive_nets=SENSITIVE,paper='A0')


@refined
def family():
 panel_bindings();b=EnvelopeBuilder()
 b.cell('reference_generator','LOCAL',{'REF_5V':'REF5','REF_N5V':'REFN5','GATE_REF':'GATE_REF'})
 for k in INPUTS:
  b.device('WQP518MA','J_'+k,'J',{'T':k+'_TIP','S':'AGND','TN':None},panel='J:{}.{}'.format('{}',k),island='')
  b.cell('input_fault_switch',k,{'JACK':k+'_TIP','PROTECTED':k+'_PROTECTED'})
  b.cell('high_impedance_input',k,{'PROTECTED':k+'_PROTECTED','BUFFERED':k+'_BUFFER'})
  b.cell('magnitude_indicator',k,{'MONITOR':k+'_BUFFER'},panel='L:{}.{}.mag'.format('{}',k),led=True)
 b.cell('gate_trigger_input','SIG',{'BUFFERED':'SIG_BUFFER','REF_5V':'REF5','GATE_REF':'GATE_REF','GATE_HIGH':'SIG_GATE'})
 b.device('B3F-1020','BUTTON','SW',{'4':'TRIG_CONTACT','3':'TRIG_CONTACT','2':'AGND','1':'AGND'},panel='C:{}.TRIG',island='')
 b.device('2MS3T1B1M2QES','MODE','SW',{'1':'ASR_CONTACT','2':'AGND','3':'LOOP_CONTACT'},panel='C:{}.MODE',island='')
 for key in ('SHAPE','STAGE'):
  contact='CURVED' if key=='SHAPE' else 'STAGE_FALL'
  b.device('2MS1T1B1M2QES-5',key,'SW',{'1':None,'2':'AGND','3':contact+'_CONTACT'},panel='C:{}.{}'.format('{}',key),island='')
 for key in ('TRIG','ASR','LOOP','CURVED','STAGE_FALL'):
  b.cell('switch_button_input',key,{'CONTACT':key+'_CONTACT','ACTIVE':key+'_RAW' if key in ('ASR','LOOP') else key+'_ACTIVE' if key=='TRIG' else key})
 # Standard 1ms contact filter is strengthened for the trigger button to 10ms.
 for n,p in enumerate(b.parts):
  if p.attributes.get('Role')=='switch_button_input:C_DB' and '_TRIG__' in p.key:
   b.parts[n]=replace(p,value='1 µF',attributes={**p.attributes,'MPN':'','Manufacturer':'','LCSC':''})
 b.logic(('or','SIG_GATE','TRIG_ACTIVE'),'GATE_RAW')
 # RC reset is an initial proposal, not a guaranteed brownout supervisor.
 b.r('POR_PULL','100 kΩ','+5V','POR_RC');b.c('POR_DELAY','1 µF','POR_RC','AGND')
 b.device(CATALOG[SHORTLIST['signal_diode']['mpn']],'POR_DISCHARGE','D',{'2':'POR_RC','1':'+5V'})
 b.schmitt('POR_INVERT','POR_RC','POR_LOW');b.schmitt('POR_BUFFER','POR_LOW','RESET_N')
 b.r('CLOCK','47 kΩ','CLOCK','CLOCK_RC');b.c('CLOCK','1 nF C0G','CLOCK_RC','AGND');b.schmitt('CLOCK_OSC','CLOCK_RC','CLOCK')
 b.ff('RESET_SYNC1','+5V','READY1','RESET_N');b.ff('RESET_SYNC2','READY1','READY','RESET_N')
 for k,source in [('GATE','GATE_RAW'),('ASR','ASR_RAW'),('LOOP','LOOP_RAW')]:
  b.ff(k+'_SYNC1',source,k+'_SYNC');b.ff(k+'_SYNC2',k+'_SYNC',k)
 b.ff('GATE_PREVIOUS','GATE','GATE_PREV')
 for key in ('TOP','BOTTOM'):
  b.ff(key+'_SYNC1',key+'_RAW',key+'_SYNC');b.ff(key+'_SYNC2',key+'_SYNC',key)
 for key in ('RISE','HOLD','FALL'):b.ff('STATE_'+key,'D_'+key,key)
 b.ff('END_EVENT','D_COMPLETE','COMPLETE')
 for key,expr in EXPRESSIONS.items():b.logic(expr,key)
 for k in ('RISE','FALL'):b.logic(('not',k),'NOT_'+k)
 # Non-retriggerable EOC; selected existing source-backed one-shot package.
 b.device('CD74HC221M96','EOC_TIMER','U',{'1':'AGND','2':'COMPLETE','3':'READY','14':'EOC_C','15':'EOC_RCX','4':'EOC','13':None,'9':'AGND','10':'AGND','11':'AGND','6':None,'7':None,'12':None,'5':None,'16':'+5V','8':'AGND'})
 b.r('EOC_TIME','47 kΩ','+5V','EOC_RCX');b.device(CATALOG[SHORTLIST['c_slew']['mpn']],'EOC_TIME','C',{'1':'EOC_RCX','2':'EOC_C'},value='100 nF C0G')
 # Local references 8V peak, 9V curved target, 1V pedestal and 50mV floor.
 for key,rf in [('REF8','60 kΩ'),('REF9','80 kΩ')]:
  b.amp(key,'precision','REF5',key+'_FB',key);b.r(key+'_FB',rf,key,key+'_FB');b.r(key+'_RG','100 kΩ',key+'_FB','AGND')
 b.r('REF1_TOP','40 kΩ','REF5','REF1_RAW');b.r('REF1_BOTTOM','10 kΩ','REF1_RAW','AGND');b.amp('REF1','precision','REF1_RAW','REF1','REF1')
 b.r('FLOOR_TOP','79 kΩ','REF5','FLOOR_REF');b.r('FLOOR_BOTTOM','22 kΩ','FLOOR_REF','AGND')
 b.r('TOP_THRESHOLD','100 kΩ','REF9','TOP_THRESHOLD');b.r('TOP_HYSTERESIS','10 MΩ','TOP_LOW','TOP_THRESHOLD')
 b.r('BOTTOM_SENSE','100 kΩ','FALL_CURVE_V','BOTTOM_SENSE');b.r('BOTTOM_HYSTERESIS','10 MΩ','BOTTOM_LOW','BOTTOM_SENSE')
 b.cmp('TOP_CMP','TOP_THRESHOLD','FALL_CURVE_V','TOP_LOW');b.schmitt('TOP_LOGIC','TOP_LOW','TOP_RAW')
 b.cmp('BOTTOM_CMP','BOTTOM_SENSE','FLOOR_REF','BOTTOM_LOW');b.schmitt('BOTTOM_LOGIC','BOTTOM_LOW','BOTTOM_RAW')
 # Two independently controlled exponential bias currents; +CV lengthens time.
 for k in ('RISE','FALL'):
  b.cell('dc_control_source',k,{'REF_LOW':'AGND','REF_HIGH':'REF5','OUT':k+'_MANUAL'},panel='C:{}.{}'.format('{}',k))
  b.amp(k+'_TIME_SUM','cv','AGND',k+'_TIME_SUM',k+'_TIME_NEG')
  for tag,value,net in [('MAN','100 kΩ',k+'_MANUAL'),('CV','200 kΩ',k+'_BUFFER')]:b.r(k+'_'+tag,value,net,k+'_TIME_SUM')
  b.r(k+'_TIME_FB','100 kΩ',k+'_TIME_NEG',k+'_TIME_SUM')
  b.amp(k+'_TIME_INV','cv','AGND',k+'_TIME_INV',k+'_TIME_RAW');b.r(k+'_INV_IN','100 kΩ',k+'_TIME_NEG',k+'_TIME_INV');b.r(k+'_INV_FB','100 kΩ',k+'_TIME_RAW',k+'_TIME_INV')
  b.r(k+'_CONTROL_LIMIT','10 kΩ',k+'_TIME_RAW',k+'_TIME_CLAMP')
  b.device('BAT54S_215',k+'_CONTROL_CLAMP','D',{'1':'AGND','3':k+'_TIME_CLAMP','2':'REF5'})
  b.amp(k+'_TIME_BUFFER','cv',k+'_TIME_CLAMP',k+'_TIME',k+'_TIME')
  b.amp(k+'_EXPO_SCALE','precision','AGND',k+'_EXPO_SUM',k+'_EXPO_DRIVE')
  b.r(k+'_EXPO_IN','100 kΩ',k+'_TIME',k+'_EXPO_SUM');b.r(k+'_EXPO_OFFSET','200 kΩ','REFN5',k+'_EXPO_SUM')
  b.r(k+'_EXPO_SCALE','3.3 kΩ',k+'_EXPO_DRIVE',k+'_SCALE_TRIM');b.trim(k+'_SCALE','1 kΩ',k+'_SCALE_TRIM',k+'_EXPO_SUM')
  b.r(k+'_BASE_LIMIT','1 kΩ',k+'_EXPO_DRIVE',k+'_EXPO_BASE')
  b.amp(k+'_EXPO_SERVO','precision','AGND',k+'_EXPO_REF',k+'_EXPO_EMITTER')
  b.r(k+'_REF_FIXED','300 kΩ','REF5',k+'_REF_TRIM');b.trim(k+'_BASE','50 kΩ',k+'_REF_TRIM',k+'_EXPO_REF')
  b.device('BCM847BS_115',k+'_PAIR','Q',{'1':k+'_EXPO_EMITTER','2':'AGND','3':k+'_EXPO_COLLECTOR','4':k+'_EXPO_EMITTER','5':k+'_EXPO_BASE','6':k+'_EXPO_REF'})
  b.r(k+'_EXPO_LIMIT','22 kΩ',k+'_MIRROR_BASE',k+'_EXPO_COLLECTOR')
  b.device('MMBT3906_215',k+'_MIRROR_REF','Q',{'1':k+'_MIRROR_BASE','2':'+12V','3':k+'_MIRROR_BASE'})
  b.device('MMBT3906_215',k+'_MIRROR_OUT','Q',{'1':k+'_MIRROR_BASE','2':'+12V','3':k+'_BIAS_SOURCE'})
  b.r(k+'_BIAS_LIMIT','22 kΩ',k+'_BIAS_SOURCE',k+'_IABC')
  b.trim(k+'_OFFSET','10 kΩ','REFN5',k+'_OFFSET_TRIM','REF5');b.r(k+'_OFFSET_FEED','470 kΩ',k+'_OFFSET_TRIM',k+'_OFFSET');b.r(k+'_OFFSET_RETURN','1 kΩ',k+'_OFFSET','AGND')
 # Curved slopes approach +9V and -1V, crossing finite 8V/50mV thresholds.
 b.r('REF45_TOP','100 kΩ','REF9','REF45');b.r('REF45_BOTTOM','100 kΩ','REF45','AGND')
 b.amp('RISE_CURVE','cv','REF45','RISE_CURVE_SUM','RISE_CURVE_V');b.r('RISE_CURVE_IN','100 kΩ','ENV_BUFFER','RISE_CURVE_SUM');b.r('RISE_CURVE_FB','100 kΩ','RISE_CURVE_V','RISE_CURVE_SUM')
 b.r('FALL_CURVE_ENV','100 kΩ','ENV_BUFFER','FALL_CURVE_PLUS');b.r('FALL_CURVE_REF','100 kΩ','REF1','FALL_CURVE_PLUS')
 b.amp('FALL_CURVE','cv','FALL_CURVE_PLUS','FALL_CURVE_FB','FALL_CURVE_V');b.r('FALL_CURVE_FB','100 kΩ','FALL_CURVE_V','FALL_CURVE_FB');b.r('FALL_CURVE_RG','100 kΩ','FALL_CURVE_FB','AGND')
 b.switch('SLOPE_SELECT',[('RISE_LINEAR','REF9','RISE_DRIVE'),('RISE_CURVE','RISE_CURVE_V','RISE_DRIVE'),('FALL_LINEAR','REF9','FALL_DRIVE'),('FALL_CURVE','FALL_CURVE_V','FALL_DRIVE')])
 for k in ('RISE','FALL'):
  b.r(k+'_DRIVE_TOP','899 kΩ',k+'_DRIVE',k+'_OTA_SIGNAL');b.r(k+'_DRIVE_BOTTOM','1 kΩ',k+'_OTA_SIGNAL','AGND')
 b.device('LM13700M_NOPB','OTA','U',{'1':'RISE_IABC','2':None,'3':'RISE_OTA_SIGNAL','4':'RISE_OFFSET','5':'RISE_OTA_CURRENT','6':'-12V','7':'AGND','8':None,'9':None,'10':'AGND','11':'+12V','12':'FALL_OTA_CURRENT','13':'FALL_OTA_SIGNAL','14':'FALL_OFFSET','15':None,'16':'FALL_IABC'})
 for k in ('RISE','FALL'):b.r(k+'_CURRENT_SUM','100 Ω',k+'_OTA_CURRENT','ENV_STORAGE')
 b.device(CATALOG[SHORTLIST['c_slew']['mpn']],'TIMING_CAP','C',{'1':'ENV_STORAGE','2':'AGND'},value='100 nF C0G')
 b.amp('ENV_BUFFER','precision','ENV_STORAGE','ENV_BUFFER','ENV_BUFFER')
 # Local integrator clamp: holds peak or discharges residual floor during idle/reset.
 b.switch('STORAGE_CLAMP',[('HOLD_ENABLE','REF8','HOLD_CLAMP'),('RESET_CAP','AGND','IDLE_CLAMP'),('AGND','AGND','AGND'),('AGND','AGND','AGND')])
 b.r('HOLD_CLAMP','100 Ω','HOLD_CLAMP','ENV_STORAGE');b.r('IDLE_CLAMP','100 Ω','IDLE_CLAMP','ENV_STORAGE')
 # BIP=1.25*ENV-5: plus=ENV*5/9, noninverting gain2.25, REF5 feed1.
 b.r('BIP_PLUS_TOP','64 kΩ','ENV_BUFFER','BIP_PLUS');b.r('BIP_PLUS_BOTTOM','80 kΩ','BIP_PLUS','AGND')
 b.amp('BIP','cv','BIP_PLUS','BIP_SUM','BIP_CORE');b.r('BIP_REF','100 kΩ','REF5','BIP_SUM');b.r('BIP_FB','100 kΩ','BIP_CORE','BIP_SUM');b.r('BIP_GROUND','400 kΩ','BIP_SUM','AGND')
 for k in ('RISE','FALL'):b.cell('stage_indicator',k,{'ENV_BUFFERED':'ENV_BUFFER','NOT_OWN_STAGE':'NOT_'+k},panel='L:{}.{}.stage'.format('{}',k),led=True)
 for key,signal in [('ENV','ENV_BUFFER'),('BIP','BIP_CORE'),('EOC','EOC'),('STG','STAGE_HIGH')]:
  b.cell('general_output',key,{'SIGNAL':signal,'JACK':key+'_TIP'})
  b.device('WQP518MA','J_'+key,'J',{'T':key+'_TIP','S':'AGND','TN':None},panel='J:{}.{}'.format('{}',key),island='')
 return b.finish_envelope()


def specification():return (family(),),tuple(Instance('envelope',n,41+i) for i,n in enumerate(INSTANCES))
