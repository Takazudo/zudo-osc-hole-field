"""H1/H2 sample-and-hold pilot, OSC-ES-1 unvalidated proposal.

The family contains the same source sheet for H1 and H2. Panel references are
instance-specific; local net labels are scoped by KiCad's sheet instance path.
"""
from dataclasses import replace
from pathlib import Path
import json,re
from scripts.schgen.core import Family,Instance,Part
from design.spec.cells._builder import ROOT,SHORTLIST,CATALOG,CELLS,cell_parts,load_symbol

PLACEMENTS={p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
INSTANCES=('H1','H2')
RAILS=('+12V','-12V','+5V','AGND')
PANEL_ROLES=('J:{}.TRIGGER','J:{}.IN','J:{}.OUT','C:{}.SAMPLE','C:{}.SLEW','L:{}.TRIGGER.mag','L:{}.IN.mag','L:{}.OUT.mag')

def panel_bindings():
 rows=[]
 for instance in INSTANCES:
  for template in PANEL_ROLES:
   uid=template.format(instance)
   if uid not in PLACEMENTS:raise ValueError('missing locked panel UID '+uid)
   row=PLACEMENTS[uid]
   rows.append({'instance':instance,'uid':uid,'ref':row['ref'],'kind':row['kind'],'x_mm':row['x_mm'],'y_mm':row['y_mm']})
 if len(rows)!=16 or len({r['uid'] for r in rows})!=16:raise ValueError('panel binding count/uniqueness drift')
 return rows

def panel_refs(template):
 return {instance:PLACEMENTS[template.format(instance)]['ref'] for instance in INSTANCES}

def footprint(symbol):
 match=re.search(r'\(property "Footprint" "([^\"]+)"',symbol.body)
 if not match:raise ValueError(symbol.lib_id+' missing footprint')
 return match[1]

def part(id,key,prefix,ordinal,pins,page,*,value=None,mpn=None,panel=None,island='',dnp=False):
 if id in ('jack','button'):
  name={'jack':'WQP518MA','button':'B3F-1020'}[id];sym=load_symbol(name)
  def prop(field):
   match=re.search(r'\(property "'+field+r'" "([^\"]*)"',sym.body)
   return match[1] if match else ''
  record={'mpn':prop('MPN'),'manufacturer':prop('Manufacturer'),'lcsc':prop('LCSC')}
 else:
  record=SHORTLIST[id];sym=load_symbol(CATALOG[record['mpn']])
 unit=next(u for u,p in sym.units.items() if p)
 expected={p.number for p in sym.units[unit]}
 if set(pins)!=expected:raise ValueError(f'{key}: expected {expected}, got {set(pins)}')
 attrs={'Role':'sample_hold:'+key,'MPN':record['mpn'] if mpn is None else mpn,'Manufacturer':record['manufacturer'] if mpn is None or mpn else '', 'LCSC':record.get('lcsc','') if mpn is None or mpn else '', 'PanelUid':panel.replace('{}','${SHEETNAME}') if panel else '', 'Island':island}
 return Part(key,sym.lib_id,prefix,ordinal,unit,50.8,50.8,pins,value=value or record['mpn'],footprint=footprint(sym),attributes=attrs,page=page,panel_refs=panel_refs(panel) if panel else {},dnp=dnp)

def family():
 panel_bindings();parts=[];ordinal=1
 def add(id,uid,nets,page,*,island='',panel_part=None):
  nonlocal ordinal
  cell=cell_parts(id,uid,nets,ordinal_start=ordinal)
  ordinal+=len(CELLS[id]['parts'])
  for p in cell:
   attrs={**p.attributes,'PanelUid':'','Island':island}
   refs={}
   if panel_part and p.symbol.endswith(panel_part[0]):
    attrs['PanelUid']=panel_part[1].replace('{}','${SHEETNAME}')
    refs=panel_refs(panel_part[1])
   parts.append(replace(p,page=page,attributes=attrs,panel_refs=refs))
 def manual(id,key,prefix,pins,page,**kwargs):
  nonlocal ordinal
  parts.append(part(id,key,prefix,ordinal,pins,page,**kwargs));ordinal+=1
 # Capture group: input protection, trigger/manual conditioning, acquisition and hold.
 manual('jack','J_TRIGGER','J',{'T':'TRIGGER_TIP','S':'AGND','TN':None},1,panel='J:{}.TRIGGER')
 manual('jack','J_IN','J',{'T':'IN_TIP','S':'AGND','TN':None},1,panel='J:{}.IN')
 manual('button','SW_SAMPLE','SW',{'4':'CONTACT','3':'CONTACT','2':'AGND','1':'AGND'},1,panel='C:{}.SAMPLE')
 add('reference_generator','J:H1.TRIGGER',{'REF_5V':'REF_5V','REF_N5V':'REF_N5V','GATE_REF':'GATE_REF'},1)
 add('input_fault_switch','J:H1.TRIGGER',{'JACK':'TRIGGER_TIP','PROTECTED':'TRIGGER_PROTECTED'},1)
 add('high_impedance_input','J:H1.TRIGGER',{'PROTECTED':'TRIGGER_PROTECTED','BUFFERED':'TRIGGER_BUFFERED'},1)
 add('gate_trigger_input','J:H1.TRIGGER',{'BUFFERED':'TRIGGER_BUFFERED','REF_5V':'REF_5V','GATE_REF':'GATE_REF','GATE_HIGH':'TRIGGER_GATE'},1)
 add('input_fault_switch','J:H1.IN',{'JACK':'IN_TIP','PROTECTED':'IN_PROTECTED'},1)
 add('high_impedance_input','J:H1.IN',{'PROTECTED':'IN_PROTECTED','BUFFERED':'IN_BUFFERED'},1)
 add('switch_button_input','C:H1.SAMPLE',{'CONTACT':'CONTACT','ACTIVE':'BUTTON_ACTIVE'},1)
 add('magnitude_indicator','L:H1.TRIGGER.mag',{'MONITOR':'TRIGGER_BUFFERED'},1,island='L:${SHEETNAME}.TRIGGER.mag',panel_part=('0603Whitelight_C2290','L:{}.TRIGGER.mag'))
 add('magnitude_indicator','L:H1.IN.mag',{'MONITOR':'IN_BUFFERED'},1,island='L:${SHEETNAME}.IN.mag',panel_part=('0603Whitelight_C2290','L:{}.IN.mag'))
 manual('signal_diode','D_TRIGGER_OR','D',{'2':'TRIGGER_GATE','1':'TRIGGER_OR'},1)
 manual('signal_diode','D_BUTTON_OR','D',{'2':'BUTTON_ACTIVE','1':'TRIGGER_OR'},1)
 manual('r_general','R_OR_PD','R',{'1':'TRIGGER_OR','2':'AGND'},1,value='100 kΩ')
 # CD74HC221: B1 rising edge, A1 low, reset high. Channel 2 is disabled.
 shot=load_symbol(CATALOG[SHORTLIST['one_shot']['mpn']]);shot_pins={
  1:{'1':'AGND','2':'TRIGGER_OR','3':'+5V','14':'TIMING_C','15':'TIMING_RCX','4':'SAMPLE_PULSE','13':None},
  2:{'9':'AGND','10':'AGND','11':'AGND','6':None,'7':None,'12':None,'5':None},
  3:{'16':'+5V','8':'AGND'},
 }
 for unit in (1,2,3):
  parts.append(Part(f'ONE_SHOT.{unit}',shot.lib_id,'U',ordinal,unit,50.8,50.8,shot_pins[unit],value=SHORTLIST['one_shot']['mpn'],footprint=footprint(shot),attributes={'Role':'sample_hold:acquisition pulse','MPN':SHORTLIST['one_shot']['mpn'],'Manufacturer':'Texas Instruments','LCSC':SHORTLIST['one_shot'].get('lcsc',''),'PanelUid':'','Island':'TIMING_LOCAL'},page=1))
 ordinal+=1
 manual('r_general','R_TIMING','R',{'1':'+5V','2':'TIMING_RCX'},1,value='10 kΩ',mpn='',island='TIMING_LOCAL')
 manual('c_hold','C_TIMING','C',{'1':'TIMING_RCX','2':'TIMING_C'},1,value='10 nF',island='TIMING_LOCAL')
 lf=load_symbol(CATALOG[SHORTLIST['sample_hold']['mpn']]);lfpins={'1':'IN_BUFFERED','2':None,'3':'-12V','4':None,'5':None,'6':None,'7':'RAW_HELD','8':'HOLD_CAP','9':None,'10':'AGND','11':'SAMPLE_PULSE','12':'+12V','13':None,'14':None}
 parts.append(Part('LF398.1',lf.lib_id,'U',ordinal,1,50.8,50.8,lfpins,value=SHORTLIST['sample_hold']['mpn'],footprint=footprint(lf),attributes={'Role':'sample_hold:hold core','MPN':SHORTLIST['sample_hold']['mpn'],'Manufacturer':'Texas Instruments','LCSC':SHORTLIST['sample_hold'].get('lcsc',''),'PanelUid':'','Island':'HOLD_LOCAL'},page=1));ordinal+=1
 manual('c_hold','C_HOLD','C',{'1':'HOLD_CAP','2':'AGND'},1,value='10 nF',island='HOLD_LOCAL')
 manual('c_hold','C_HOLD_ALT','C',{'1':'HOLD_CAP','2':'AGND'},1,value='100 nF ALT',mpn='',island='HOLD_LOCAL',dnp=True)
 # Post-hold group: every lag-storage component stays in one panel-pot island.
 add('slew_island','C:H1.SLEW',{'HELD_BUFFERED':'RAW_HELD','STORAGE':'SLEW_STORAGE','POT_IN':'SLEW_POT_IN','SLEW_OUT':'SLEW_BUFFERED'},2,island='C:${SHEETNAME}.SLEW',panel_part=('PTV09A-4020F-B504','C:{}.SLEW'))
 add('precision_output','J:H1.OUT',{'SIGNAL':'SLEW_BUFFERED','JACK':'OUT_TIP'},2,island='OUT_LOCAL')
 manual('jack','J_OUT','J',{'T':'OUT_TIP','S':'AGND','TN':None},2,panel='J:{}.OUT')
 add('magnitude_indicator','L:H1.OUT.mag',{'MONITOR':'SLEW_BUFFERED'},2,island='L:${SHEETNAME}.OUT.mag',panel_part=('0603Whitelight_C2290','L:{}.OUT.mag'))
 # OSC-ES-1 calls for 100 nF at each IC supply pin. These are local to each
 # package; board-rail bulk remains a DNP reservation until partitioning.
 packages={p.key.rsplit('.',1)[0]:p.symbol.split(':')[-1] for p in parts if p.prefix=='U'}
 for package,symbol in packages.items():
  if symbol in ('SN74HC14DR','CD74HC221M96'):rails=('+5V',)
  elif symbol in ('LM393BIDR','REF5050AIDR'):rails=('+12V',)
  else:rails=('+12V','-12V')
  for rail in rails:
   key='C_DEC_'+str(len([p for p in parts if p.key.startswith('C_DEC_')])+1)
   parts.append(part('c_bypass',key,'C',1,{'1':rail,'2':'AGND'},1,value='100 nF',island='DECOUP:'+package))
 for rail in RAILS[:3]:
  key='C_BULK_'+rail.replace('+','P').replace('-','N')
  parts.append(part('c_bulk',key,'C',1,{'1':rail,'2':'AGND'},1,value='4.7 µF bulk reservation',island='BULK_TBD',dnp=True))
 # Reference ordinals are unique per prefix, not across unlike device classes.
 # This allows many local decouplers while preserving the generator's 1..99 range.
 allocated={};normalized=[];counters={}
 for p in parts:
  package=p.key.rsplit('.',1)[0];group=(p.prefix,package)
  if group not in allocated:
   counters[p.prefix]=counters.get(p.prefix,0)+1
   if counters[p.prefix]>99:raise ValueError(f'{p.prefix} ordinal capacity exceeded')
   allocated[group]=counters[p.prefix]
  normalized.append(replace(p,ordinal=allocated[group]))
 # One shared sheet keeps RAW_HELD local to each KiCad sheet instance. Global
 # labels would short H1 and H2 outputs if used merely to span handoff pages.
 # The upper/lower circuit groups still implement handoff sections 62 and 63.
 ordered=[]
 for p in normalized:
  n=len(ordered)
  ordered.append(replace(p,page=1,x=50.8+(n%12)*60.96,y=50.8+(n//12)*30.48))
 return Family('sample_hold',tuple(ordered),global_nets=RAILS,sensitive_nets=('HOLD_CAP','SLEW_STORAGE','SLEW_POT_IN','TIMING_C','TIMING_RCX'),paper='A1')

def specification():
 return (family(),),(Instance('sample_hold','H1',1),Instance('sample_hold','H2',2))
