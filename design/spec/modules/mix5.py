"""M5A/M5B five-input DC-coupled attenuverting mixer proposal.

Each 100k input and 40k feedback resistor makes ±5 V on all five
inputs approximately ±10 V at the pre-level summer. This is not an
implicit five-way average. The post-level inverter restores polarity.
"""
from scripts.schgen.core import Instance
from design.spec.modules.mixer_common import MixerBuilder, bindings, input_channel, output_channel

INSTANCES=('M5A','M5B')
PANEL=tuple(f'J:{{}}.{k}' for k in ('1','2','3','4','5','SUM'))+tuple(f'C:{{}}.{k}' for k in ('1±','2±','3±','4±','5±','LEVEL'))+tuple(f'L:{{}}.{k}.mag' for k in ('1','2','3','4','5','SUM'))+('L:{}.SUM.clip',)


def panel_bindings():
    rows=bindings(INSTANCES,PANEL)
    if len(rows)!=38:raise ValueError('MIX5 panel binding count drift')
    return rows


def family():
    panel_bindings();b=MixerBuilder('mix5',INSTANCES)
    b.cell('reference_generator','LOCAL',{'REF_5V':'REF5','REF_N5V':'REFN5'})
    for n in range(1,6):input_channel(b,n)
    b.amp('SUMMER','audio','AGND','SUM_NODE','SUM_PRELEVEL')
    for n in range(1,6):b.r('SUM_IN_'+str(n),'100 kΩ',str(n)+'_GAIN','SUM_NODE')
    b.r('SUM_FEEDBACK','40 kΩ','SUM_PRELEVEL','SUM_NODE')
    b.cell('remote_buffer','LEVEL',{'SIGNAL':'SUM_PRELEVEL','REMOTE':'LEVEL_REMOTE'})
    b.cell('level_attenuator','LEVEL',{'REMOTE_INPUT':'LEVEL_REMOTE','OUT':'LEVEL_BUFFERED'},panel='C:{}.LEVEL')
    b.amp('POLARITY_RESTORE','audio','AGND','RESTORE_SUM','SUM_POSTLEVEL')
    b.r('RESTORE_IN','100 kΩ','LEVEL_BUFFERED','RESTORE_SUM')
    b.r('RESTORE_FB','100 kΩ','SUM_POSTLEVEL','RESTORE_SUM')
    output_channel(b,'SUM_POSTLEVEL')
    return b.finish_mixer(sensitive=('SUM_NODE',))


def specification():
    return (family(),),tuple(Instance('mix5',name,61+i) for i,name in enumerate(INSTANCES))
