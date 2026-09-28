"""Shared panel binding and input/indicator capture for the two mixer families.

All circuits are OSC-ES-1 proposals; panel coordinates come only from the lock.
"""
from dataclasses import replace
from collections import defaultdict
from scripts.schgen.core import Family
from design.spec.modules.oscillator import Builder, PLACEMENTS, RAILS
from design.spec.cells._builder import cell_parts


class MixerBuilder(Builder):
    def __init__(self, name, instances):
        super().__init__(name.upper()+'_CORE:${SHEETNAME}')
        self.name=name
        self.instances=instances

    def panel_attributes(self, template):
        if template is None:
            return {'PanelUid':''}, {}
        return ({'PanelUid':template.replace('{}','${SHEETNAME}')},
                {i:PLACEMENTS[template.format(i)]['ref'] for i in self.instances})

    def cell(self, id, tag, nets, *, panel=None, indicator=False):
        uid=(panel or 'J:{}.1').format(self.instances[0])
        for part in cell_parts(id,uid,nets,instance_tag=tag):
            attrs={**part.attributes,'PanelUid':'',
                   'Island':self.name.upper()+('_LEDS' if indicator else '_CORE')+':${SHEETNAME}'}
            refs={}
            panel_part=part.prefix=='RV' or (indicator and part.attributes.get('Role','').endswith(':LED'))
            if panel and panel_part:
                binding,refs=self.panel_attributes(panel)
                attrs.update(binding)
                attrs['Island']=''
            self.parts.append(replace(part,attributes=attrs,panel_refs=refs))

    def finish_mixer(self, sensitive=()):
        # Pack each physical island separately, then assign unique schematic
        # package ordinals across the whole family.
        groups=defaultdict(list)
        for part in self.parts:
            groups[part.attributes.get('Island','')].append(part)
        compiled=[]
        for number,(island,parts) in enumerate(sorted(groups.items())):
            sub=Builder(island);sub.parts=parts
            result=sub.finish(self.name,globals=RAILS)
            for part in result.parts:
                attrs={**part.attributes,'Role':part.attributes.get('Role','').replace('oscillator:',self.name+':')}
                if part.key.startswith('C_DEC_'):attrs['Island']=island
                compiled.append(replace(part,key=f'G{number}_'+part.key,attributes=attrs))
        assigned={};counts=defaultdict(int);out=[]
        for part in compiled:
            stem=part.key.rsplit('.',1)[0];group=(part.prefix,stem)
            if group not in assigned:
                counts[part.prefix]+=1;assigned[group]=counts[part.prefix]
            n=assigned[group];prefix=part.prefix if n<=99 else part.prefix+'B'
            i=len(out)
            out.append(replace(part,prefix=prefix,ordinal=(n-1)%99+1,
                               x=45.72+(i%17)*63.5,y=66.04+(i//17)*38.1))
        return Family(self.name,tuple(out),global_nets=RAILS,
                      sensitive_nets=sensitive,paper='A0')


def bindings(instances, templates):
    rows=[]
    for instance in instances:
        for template in templates:
            uid=template.format(instance)
            if uid not in PLACEMENTS:
                raise ValueError('missing fixed panel UID '+uid)
            p=PLACEMENTS[uid]
            rows.append({'instance':instance,'uid':uid,'ref':p['ref'],
                         'x_mm':p['x_mm'],'y_mm':p['y_mm']})
    if len(rows)!=len({r['uid'] for r in rows}):
        raise ValueError('duplicate mixer panel binding')
    return rows


def input_channel(b, number):
    key=str(number)
    b.device('WQP518MA','J_'+key,'J',{'T':key+'_TIP','S':'AGND','TN':None},
             panel='J:{}.{}'.format('{}',key),island='')
    b.cell('input_fault_switch',key,{'JACK':key+'_TIP','PROTECTED':key+'_PROTECTED'})
    b.cell('high_impedance_input',key,{'PROTECTED':key+'_PROTECTED','BUFFERED':key+'_BUFFER'})
    b.cell('remote_buffer',key,{'SIGNAL':key+'_BUFFER','REMOTE':key+'_REMOTE'})
    b.cell('bipolar_attenuverter',key,
           {'REMOTE_INPUT':key+'_REMOTE','BUFFERED_INPUT':key+'_BUFFER','OUT':key+'_GAIN'},
           panel='C:{}.{}±'.format('{}',key))
    b.cell('magnitude_indicator',key,{'MONITOR':key+'_GAIN'},
           panel='L:{}.{}.mag'.format('{}',key),indicator=True)


def output_channel(b, signal):
    b.cell('general_output','SUM',{'SIGNAL':signal,'JACK':'SUM_TIP'})
    b.device('WQP518MA','J_SUM','J',{'T':'SUM_TIP','S':'AGND','TN':None},
             panel='J:{}.SUM',island='')
    b.cell('magnitude_indicator','SUM',{'MONITOR':signal},
           panel='L:{}.SUM.mag',indicator=True)
    b.cell('clip_detector','SUM',
           {'MONITOR':'SUM_PRELEVEL','REF_5V':'REF5','REF_N5V':'REFN5'},
           panel='L:{}.SUM.clip',indicator=True)
