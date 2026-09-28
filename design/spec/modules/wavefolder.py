"""W2(left)/W1(right) feed-forward wavefolder; OSC-ES-1 proposal.

Index allocation W2=51, W1=52. No hardware or stability qualification claimed.
"""
from collections import defaultdict
from dataclasses import replace
from design.spec.modules.oscillator import Builder,PLACEMENTS,RAILS
from design.spec.cells._builder import ROOT,SHORTLIST,CATALOG,cell_parts
from scripts.schgen.core import Family,Instance

INSTANCES=('W2','W1')
PANEL=tuple('J:{}.{}'.format('{}',k) for k in ('IN','FOLD','BIAS','OUT'))+tuple('C:{}.{}'.format('{}',k) for k in ('FOLD','FOLD±','BIAS','LEVEL'))+tuple('L:{}.{}.mag'.format('{}',k) for k in ('IN','FOLD','BIAS'))
SENSITIVE=('PRE_GAIN_SUM','FOLDER_SUM','AC_NODE',*(f'F{i}_CLIP' for i in range(1,5)),*(f'F{i}_SUM' for i in range(1,5)))


def panel_bindings():
 rows=[]
 for i in INSTANCES:
  for template in PANEL:
   uid=template.format(i);p=PLACEMENTS[uid]
   rows.append({'instance':i,'uid':uid,'ref':p['ref'],'x_mm':p['x_mm'],'y_mm':p['y_mm']})
 assert len(rows)==len({r['uid'] for r in rows})==22
 assert PLACEMENTS['J:W2.IN']['x_mm']<PLACEMENTS['J:W1.IN']['x_mm']
 return rows


class WavefolderBuilder(Builder):
 def __init__(self):super().__init__('FOLDER_CORE:${SHEETNAME}')
 def panel_attributes(self,t):
  return ({'PanelUid':t.replace('{}','${SHEETNAME}')},{i:PLACEMENTS[t.format(i)]['ref'] for i in INSTANCES}) if t else ({'PanelUid':''},{})
 def cell(self,id,tag,nets,*,panel=None,led=False):
  for p in cell_parts(id,(panel or 'J:{}.IN').format('W2'),nets,ordinal_start=1,instance_tag=tag):
   attrs={**p.attributes,'PanelUid':'','Island':'FOLDER_LEDS:${SHEETNAME}' if led else self.island};refs={}
   if panel and (p.prefix=='RV' or (led and p.symbol.endswith('0603Whitelight_C2290'))):
    a,refs=self.panel_attributes(panel);attrs.update(a)
    if not led:attrs['Island']=''
   self.parts.append(replace(p,attributes=attrs,panel_refs=refs))
 def complete(self):
  led=[p for p in self.parts if p.attributes.get('Island')=='FOLDER_LEDS:${SHEETNAME}'];core=[p for p in self.parts if p not in led];compiled=[]
  for tag,parts in [('CORE',core),('LED',led)]:
   b=Builder();b.parts=parts
   for p in b.finish('wavefolder',globals=RAILS).parts:
    attrs={**p.attributes,'Role':p.attributes.get('Role','').replace('oscillator:','wavefolder:')}
    if p.key.startswith('C_DEC_'):attrs['Island']='FOLDER_'+('LEDS' if tag=='LED' else 'CORE')+':${SHEETNAME}'
    compiled.append(replace(p,key=tag+'_'+p.key,attributes=attrs))
  counts=defaultdict(int);assigned={};out=[]
  for p in compiled:
   prefix='R' if p.prefix=='RB' else p.prefix;key=(prefix,p.key.rsplit('.',1)[0])
   if key not in assigned:counts[prefix]+=1;assigned[key]=counts[prefix]
   n=assigned[key];pos=len(out)
   out.append(replace(p,prefix=prefix if n<=99 else prefix+'B',ordinal=(n-1)%99+1,x=45.72+(pos%17)*63.5,y=66.04+(pos//17)*38.1))
  return Family('wavefolder',tuple(out),global_nets=RAILS,sensitive_nets=SENSITIVE,paper='A0')


def family():
 panel_bindings();b=WavefolderBuilder()
 b.cell('reference_generator','LOCAL',{'REF_5V':'REF5','REF_N5V':'REFN5'})
 for k in ('IN','FOLD','BIAS'):
  b.device('WQP518MA','J_'+k,'J',{'T':k+'_TIP','S':'AGND','TN':None},panel='J:{}.{}'.format('{}',k),island='')
  b.cell('input_fault_switch',k,{'JACK':k+'_TIP','PROTECTED':k+'_PROTECTED'})
  b.cell('high_impedance_input',k,{'PROTECTED':k+'_PROTECTED','BUFFERED':k+'_BUFFER'})
  b.cell('magnitude_indicator',k,{'MONITOR':k+'_BUFFER'},panel='L:{}.{}.mag'.format('{}',k),led=True)
 b.cell('dc_control_source','FOLD',{'REF_LOW':'AGND','REF_HIGH':'REF5','OUT':'FOLD_MANUAL'},panel='C:{}.FOLD')
 b.cell('dc_control_source','BIAS',{'REF_LOW':'REFN5','REF_HIGH':'REF5','OUT':'BIAS_MANUAL'},panel='C:{}.BIAS')
 b.cell('remote_buffer','FOLD',{'SIGNAL':'FOLD_BUFFER','REMOTE':'FOLD_REMOTE'})
 b.cell('bipolar_attenuverter','FOLD',{'REMOTE_INPUT':'FOLD_REMOTE','BUFFERED_INPUT':'FOLD_BUFFER','OUT':'FOLD_DEPTH'},panel='C:{}.FOLD±')
 # Linear control current servo. The soft clamp can exceed nominal0..5V by Vf.
 b.amp('CONTROL_SUM','cv','AGND','CONTROL_SUM','CONTROL_NEG')
 for tag in ('MANUAL','DEPTH'):b.r('CONTROL_'+tag,'100 kΩ','FOLD_'+tag,'CONTROL_SUM')
 b.r('CONTROL_FB','100 kΩ','CONTROL_NEG','CONTROL_SUM')
 b.amp('CONTROL_INVERT','cv','AGND','CONTROL_INV','CONTROL_RAW');b.r('CONTROL_INV_IN','100 kΩ','CONTROL_NEG','CONTROL_INV');b.r('CONTROL_INV_FB','100 kΩ','CONTROL_RAW','CONTROL_INV')
 b.r('CONTROL_LIMIT','10 kΩ','CONTROL_RAW','CONTROL_CLAMP');b.device('BAT54S_215','CONTROL_CLAMP','D',{'1':'AGND','3':'CONTROL_CLAMP','2':'REF5'})
 b.amp('CONTROL_BUFFER','cv','CONTROL_CLAMP','COMMAND','COMMAND')
 b.r('REF25_TOP','100 kΩ','REF5','REF25');b.r('REF25_BOTTOM','100 kΩ','REF25','AGND')
 b.amp('EMITTER_TARGET','cv','REF25','TARGET_SUM','TARGET');b.r('TARGET_IN','100 kΩ','COMMAND','TARGET_SUM');b.r('TARGET_FB','100 kΩ','TARGET','TARGET_SUM')
 b.amp('CURRENT_SERVO','cv','TARGET','EMITTER','BASE_DRIVE');b.r('BIAS_SENSE','12.4 kΩ','REF5','EMITTER');b.r('BASE_LIMIT','10 kΩ','BASE_DRIVE','BASE')
 b.device('MMBT3906_215','BIAS_PNP','Q',{'1':'BASE','2':'EMITTER','3':'CURRENT_SOURCE'})
 b.device(CATALOG[SHORTLIST['signal_diode']['mpn']],'BIAS_REVERSE_BE','D',{'2':'BASE','1':'EMITTER'})
 b.c('SERVO_COMP','100 pF','BASE_DRIVE','EMITTER');b.r('IABC_LIMIT','22 kΩ','CURRENT_SOURCE','IABC')
 # One active OTA; whole dual package retained, unused section unbiased.
 b.r('INPUT_ATTEN_TOP','100 kΩ','IN_BUFFER','OTA_SIGNAL');b.r('INPUT_ATTEN_BOTTOM','200 Ω','OTA_SIGNAL','AGND')
 b.trim('OTA_OFFSET','10 kΩ','REFN5','OFFSET_TRIM','REF5');b.r('OFFSET_FEED','470 kΩ','OFFSET_TRIM','OTA_OFFSET');b.r('OFFSET_RETURN','1 kΩ','OTA_OFFSET','AGND')
 b.r('UNUSED_BIAS','100 kΩ','UNUSED_IABC','-12V')
 b.device('LM13700M_NOPB','OTA','U',{'1':'IABC','2':None,'3':'OTA_OFFSET','4':'OTA_SIGNAL','5':'PRE_GAIN_SUM','6':'-12V','7':'AGND','8':None,'9':None,'10':'AGND','11':'+12V','12':None,'13':'AGND','14':'AGND','15':None,'16':'UNUSED_IABC'})
 b.amp('PRE_GAIN','audio','AGND','PRE_GAIN_SUM','PRE_GAIN');b.r('PRE_GAIN_FIXED','49.9 kΩ','PRE_GAIN','PRE_GAIN_TRIM');b.trim('PRE_GAIN_MAX','10 kΩ','PRE_GAIN_TRIM','PRE_GAIN_SUM')
 # Fixed bias0.1 replaces planning unity so normal summed drive fits four cells.
 b.amp('DRIVE_SUM','audio','AGND','FOLDER_SUM','FOLDER_NEG')
 b.r('DRIVE_SIGNAL','100 kΩ','PRE_GAIN','FOLDER_SUM')
 for k in ('MANUAL','BUFFER'):b.r('DRIVE_BIAS_'+k,'1 MΩ','BIAS_'+k,'FOLDER_SUM')
 b.r('DRIVE_FB','100 kΩ','FOLDER_NEG','FOLDER_SUM')
 b.amp('DRIVE_INVERT','audio','AGND','DRIVE_INV_SUM','FOLDER_DRIVE');b.r('DRIVE_INV_IN','100 kΩ','FOLDER_NEG','DRIVE_INV_SUM');b.r('DRIVE_INV_FB','100 kΩ','FOLDER_DRIVE','DRIVE_INV_SUM')
 # f(x)=2*c(x)-x, where c is the passive antiparallel diode clamp.
 previous='FOLDER_DRIVE'
 for i in range(1,5):
  k=f'F{i}';b.r(k+'_CLIP_FEED','10 kΩ',previous,k+'_CLIP')
  b.device(CATALOG[SHORTLIST['signal_diode']['mpn']],k+'_D_POS','D',{'2':k+'_CLIP','1':'AGND'})
  b.device(CATALOG[SHORTLIST['signal_diode']['mpn']],k+'_D_NEG','D',{'2':'AGND','1':k+'_CLIP'})
  b.amp(k,'audio',k+'_CLIP',k+'_SUM',k+'_OUT')
  b.r(k+'_INPUT','100 kΩ',previous,k+'_SUM');b.r(k+'_FEEDBACK','100 kΩ',k+'_OUT',k+'_SUM')
  previous=k+'_OUT'
 b.amp('OUTPUT_SCALE','audio','F4_OUT','OUTPUT_FB','PRE_AC');b.r('OUTPUT_RF','70 kΩ','PRE_AC','OUTPUT_FB');b.r('OUTPUT_RG','10 kΩ','OUTPUT_FB','AGND')
 # Ten exact100nF C0G parts yield1uF nominal without inventing a film MPN.
 for i in range(10):b.device(CATALOG[SHORTLIST['c_slew']['mpn']],f'AC_BANK{i}','C',{'1':'PRE_AC','2':'AC_NODE'},value='100 nF C0G')
 b.r('AC_RETURN','100 kΩ','AC_NODE','AGND');b.amp('AC_BUFFER','audio','AC_NODE','AC_BUFFER','AC_BUFFER')
 b.cell('remote_buffer','LEVEL',{'SIGNAL':'AC_BUFFER','REMOTE':'LEVEL_REMOTE'})
 b.cell('level_attenuator','LEVEL',{'REMOTE_INPUT':'LEVEL_REMOTE','OUT':'LEVEL_OUT'},panel='C:{}.LEVEL')
 b.cell('general_output','OUT',{'SIGNAL':'LEVEL_OUT','JACK':'OUT_TIP'})
 b.device('WQP518MA','J_OUT','J',{'T':'OUT_TIP','S':'AGND','TN':None},panel='J:{}.OUT',island='')
 return b.complete()


def specification():return (family(),),tuple(Instance('wavefolder',n,51+i) for i,n in enumerate(INSTANCES))
