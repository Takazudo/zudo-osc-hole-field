"""A01--A06 precision attenuverter / manual-offset proposal.

Nominal transfer: OUT_INTERNAL = gain*IN + manual_offset + OFFSET_CV.
The ±15 V mathematical sum is deliberately beyond available output headroom;
clip reporting and bench-defined overload behaviour are part of this draft.
"""
from collections import defaultdict
from dataclasses import replace
from scripts.schgen.core import Family, Instance
from design.spec.modules.oscillator import Builder, PLACEMENTS, RAILS
from design.spec.cells._builder import ROOT, STANDARD, SHORTLIST, CATALOG, cell_parts, load_symbol
from design.spec.modules.sample_hold import footprint

INSTANCES = tuple(f'A{i:02d}' for i in range(1, 7))
INPUTS = ('IN', 'OFFSET')
LEDS = ('IN.mag', 'OFFSET.mag', 'OUT.mag', 'OUT.clip')
PANEL = (tuple('J:{}.{}'.format('{}', key) for key in ('IN', 'OFFSET', 'OUT'))
         + tuple('C:{}.{}'.format('{}', key) for key in ('ATTEN', 'OFFSET'))
         + tuple('L:{}.{}'.format('{}', key) for key in LEDS))


def panel_bindings():
    rows = []
    for instance in INSTANCES:
        for template in PANEL:
            uid = template.format(instance)
            p = PLACEMENTS[uid]
            rows.append({'instance': instance, 'uid': uid, 'ref': p['ref'],
                         'x_mm': p['x_mm'], 'y_mm': p['y_mm']})
    assert len(rows) == len({row['uid'] for row in rows}) == 54
    return rows


class OffsetBuilder(Builder):
    def __init__(self):
        super().__init__('AO_CORE:${SHEETNAME}')

    def panel_attributes(self, template):
        if not template:
            return {'PanelUid': ''}, {}
        return ({'PanelUid': template.replace('{}', '${SHEETNAME}')},
                {i: PLACEMENTS[template.format(i)]['ref'] for i in INSTANCES})

    def cell(self, id, tag, nets, *, panel=None, role=None, indicator=False):
        uid=(panel or 'J:{}.IN').format('A01')
        for p in cell_parts(id, uid, nets, ordinal_start=1, instance_tag=tag):
            attrs={**p.attributes,'Block':'offset','PanelUid':'',
                   'Island':'AO_INDICATORS:${SHEETNAME}' if indicator else self.island}
            refs={}
            if panel and (p.prefix=='RV' or (indicator and p.attributes.get('Role')==id+':LED')):
                panelattrs,refs=self.panel_attributes(panel)
                attrs.update(panelattrs)
                if p.prefix=='RV': attrs['Island']=''
            if role and p.symbol.rsplit(':',1)[-1].startswith('OPA'):
                record=SHORTLIST[STANDARD['roles'][role]['part_id']]
                symbol=load_symbol(CATALOG[record['mpn']])
                p=replace(p,symbol=symbol.lib_id,footprint=footprint(symbol),value=record['mpn'])
                attrs.update(MPN=record['mpn'],Manufacturer=record['manufacturer'],LCSC=record['lcsc'])
            self.parts.append(replace(p,attributes=attrs,panel_refs=refs))

    def finish_offset(self):
        # Pack core and LED channels independently to preserve physical islands.
        core=[p for p in self.parts if p.attributes.get('Island')!='AO_INDICATORS:${SHEETNAME}']
        indicators=[p for p in self.parts if p.attributes.get('Island')=='AO_INDICATORS:${SHEETNAME}']
        out=[]
        for label,parts in [('CORE',core),('IND',indicators)]:
            b=Builder();b.parts=parts
            family=b.finish('offset',globals=RAILS)
            out.extend(replace(p,key=label+'_'+p.key,
                               attributes={**p.attributes,'Block':'offset',
                                           'Role':p.attributes.get('Role','').replace('oscillator:','offset:')})
                       for p in family.parts)
        allocated={};counts=defaultdict(int);normal=[]
        for p in out:
            group=(p.prefix,p.key.rsplit('.',1)[0])
            if group not in allocated:
                counts[p.prefix]+=1;allocated[group]=counts[p.prefix]
            index=allocated[group]
            prefix=p.prefix if index<=99 else p.prefix+'B'
            ordinal=(index-1)%99+1
            n=len(normal)
            normal.append(replace(p,prefix=prefix,ordinal=ordinal,
                                  x=45.72+(n%17)*63.5,y=66.04+(n//17)*38.1))
        return Family('offset',tuple(normal),global_nets=RAILS,paper='A0',
                      sensitive_nets=('ATTEN_SUM','SUM_NODE','RESTORE_NODE',
                                      'OUT_INTERNAL','CLIP_HALF'))


def family():
    panel_bindings();b=OffsetBuilder()
    b.cell('reference_generator','LOCAL',{'REF_5V':'REF5','REF_N5V':'REFN5'})
    for key in INPUTS:
        b.device('WQP518MA','J_'+key,'J',{'T':key+'_TIP','S':'AGND','TN':None},
                 panel='J:{}.{}'.format('{}',key),island='')
        b.cell('input_fault_switch',key,{'JACK':key+'_TIP','PROTECTED':key+'_PROTECTED'})
        b.cell('high_impedance_input',key,
               {'PROTECTED':key+'_PROTECTED','BUFFERED':key+'_BUFFER'},role='precision')
        b.cell('magnitude_indicator',key,{'MONITOR':key+'_BUFFER'},
               panel='L:{}.{}.mag'.format('{}',key),indicator=True)
    b.cell('remote_buffer','IN',{'SIGNAL':'IN_BUFFER','REMOTE':'IN_REMOTE'},role='precision')
    b.cell('bipolar_attenuverter','IN',
           {'REMOTE_INPUT':'IN_REMOTE','BUFFERED_INPUT':'IN_BUFFER',
            'OUT':'ATTEN_OUT','SUM':'ATTEN_SUM'},
           panel='C:{}.ATTEN',role='precision')
    b.cell('dc_control_source','OFFSET',
           {'REF_LOW':'REFN5','REF_HIGH':'REF5','OUT':'MANUAL_OFFSET'},
           panel='C:{}.OFFSET',role='precision')
    # A 100 kΩ matched-resistor inverting summer and unity inverter preserve
    # the handoff sign; ±5 V + ±5 V + ±5 V can overdrive ±12 V rails.
    b.amp('SUM','precision','AGND','SUM_NODE','SUM_NEG')
    for key,net in [('ATTEN','ATTEN_OUT'),('MANUAL','MANUAL_OFFSET'),
                    ('CV','OFFSET_BUFFER')]:
        b.r('SUM_'+key,'100 kΩ',net,'SUM_NODE')
    b.r('SUM_FB','100 kΩ','SUM_NEG','SUM_NODE')
    b.amp('RESTORE','precision','AGND','RESTORE_NODE','OUT_INTERNAL')
    b.r('RESTORE_IN','100 kΩ','SUM_NEG','RESTORE_NODE')
    b.r('RESTORE_FB','100 kΩ','OUT_INTERNAL','RESTORE_NODE')
    b.cell('precision_output','OUT',{'SIGNAL':'OUT_INTERNAL','JACK':'OUT_TIP'})
    b.device('WQP518MA','J_OUT','J',{'T':'OUT_TIP','S':'AGND','TN':None},
             panel='J:{}.OUT',island='')
    b.cell('magnitude_indicator','OUT',{'MONITOR':'OUT_INTERNAL'},
           panel='L:{}.OUT.mag',indicator=True)
    b.cell('clip_detector','OUT',
           {'MONITOR':'OUT_INTERNAL','REF_5V':'REF5','REF_N5V':'REFN5',
            'HALF':'CLIP_HALF'},
           panel='L:{}.OUT.clip',indicator=True)
    return b.finish_offset()


def specification():
    return (family(),),tuple(Instance('offset',name,71+i) for i,name in enumerate(INSTANCES))
