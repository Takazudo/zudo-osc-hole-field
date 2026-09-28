"""M4A/M4B four-input DC-coupled mixer with LM13700 VCA proposal.

The OTA design is an unvalidated 25 °C planning calculation. A 100k/100Ω
input divider limits the differential signal to about ±10 mV at ±10 V
summer output. A 0..5 V command requests 0..500 µA bias through 10k;
100k plus 10k feedback trim targets unity gain at +5 V. The Schottky
clamp has a forward-drop margin, so 0..5 V is a requested control range,
not a hard bound. Distortion,
feedthrough, current limiting and temperature behavior need vendor-model
and bench qualification.
"""
from scripts.schgen.core import Instance
from design.spec.modules.mixer_common import MixerBuilder, bindings, input_channel, output_channel
from design.spec.cells._builder import CATALOG, SHORTLIST

INSTANCES=('M4A','M4B')
PANEL=tuple(f'J:{{}}.{k}' for k in ('1','2','3','4','ATTEN','SUM'))+tuple(f'C:{{}}.{k}' for k in ('1±','2±','3±','4±','CV±','LEVEL'))+tuple(f'L:{{}}.{k}.mag' for k in ('1','2','3','4','ATTEN','SUM'))+('L:{}.SUM.clip',)


def panel_bindings():
    rows=bindings(INSTANCES,PANEL)
    if len(rows)!=38:raise ValueError('MIX4 panel binding count drift')
    return rows


def family():
    panel_bindings();b=MixerBuilder('mix4_vca',INSTANCES)
    b.cell('reference_generator','LOCAL',{'REF_5V':'REF5','REF_N5V':'REFN5'})
    for n in range(1,5):input_channel(b,n)
    b.amp('SUMMER','audio','AGND','SUM_NODE','SUM_PRELEVEL')
    for n in range(1,5):b.r('SUM_IN_'+str(n),'100 kΩ',str(n)+'_GAIN','SUM_NODE')
    b.r('SUM_FEEDBACK','50 kΩ','SUM_PRELEVEL','SUM_NODE')
    # ATTEN is a CV jack and never enters the four-input audio sum.
    b.device('WQP518MA','J_ATTEN','J',{'T':'ATTEN_TIP','S':'AGND','TN':None},panel='J:{}.ATTEN',island='')
    b.cell('input_fault_switch','ATTEN',{'JACK':'ATTEN_TIP','PROTECTED':'ATTEN_PROTECTED'})
    b.cell('high_impedance_input','ATTEN',{'PROTECTED':'ATTEN_PROTECTED','BUFFERED':'ATTEN_BUFFER'})
    b.cell('remote_buffer','ATTEN',{'SIGNAL':'ATTEN_BUFFER','REMOTE':'ATTEN_REMOTE'})
    b.cell('bipolar_attenuverter','CV',{'REMOTE_INPUT':'ATTEN_REMOTE','BUFFERED_INPUT':'ATTEN_BUFFER','OUT':'CV_DEPTH'},panel='C:{}.CV±')
    b.cell('magnitude_indicator','ATTEN',{'MONITOR':'ATTEN_BUFFER'},panel='L:{}.ATTEN.mag',indicator=True)
    b.cell('dc_control_source','LEVEL',{'REF_LOW':'AGND','REF_HIGH':'REF5','OUT':'LEVEL_MANUAL'},panel='C:{}.LEVEL')
    # Schottky-limited command targets [0, REF5]; diode drop permits margin.
    # Negative CV drives the PNP off rather than reversing signal gain.
    b.amp('COMMAND_SUM','cv','AGND','COMMAND_SUM','COMMAND_NEG')
    b.r('COMMAND_MANUAL','100 kΩ','LEVEL_MANUAL','COMMAND_SUM')
    b.r('COMMAND_CV','100 kΩ','CV_DEPTH','COMMAND_SUM')
    b.r('COMMAND_SUM_FB','100 kΩ','COMMAND_NEG','COMMAND_SUM')
    b.amp('COMMAND_INVERT','cv','AGND','COMMAND_INVERT_SUM','COMMAND_RAW')
    b.r('COMMAND_INVERT_IN','100 kΩ','COMMAND_NEG','COMMAND_INVERT_SUM')
    b.r('COMMAND_INVERT_FB','100 kΩ','COMMAND_RAW','COMMAND_INVERT_SUM')
    b.r('COMMAND_LIMIT','10 kΩ','COMMAND_RAW','COMMAND_CLAMP')
    b.device('BAT54S_215','COMMAND_CLAMP','D',{'1':'AGND','3':'COMMAND_CLAMP','2':'REF5'})
    b.amp('COMMAND_BUFFER','cv','COMMAND_CLAMP','COMMAND','COMMAND')
    # PNP emitter current servo: emitter target = REF5 - COMMAND.
    b.r('REF25_TOP','100 kΩ','REF5','REF25');b.r('REF25_BOT','100 kΩ','REF25','AGND')
    b.amp('EMITTER_TARGET','cv','REF25','TARGET_SUM','EMITTER_TARGET')
    b.r('TARGET_IN','100 kΩ','COMMAND','TARGET_SUM')
    b.r('TARGET_FB','100 kΩ','EMITTER_TARGET','TARGET_SUM')
    b.amp('CURRENT_SERVO','cv','EMITTER_TARGET','EMITTER','BASE_DRIVE')
    b.r('CURRENT_SENSE','10 kΩ','REF5','EMITTER')
    b.r('BASE_DRIVE','10 kΩ','BASE_DRIVE','BASE')
    b.device('MMBT3906_215','CURRENT_PNP','Q',{'1':'BASE','2':'EMITTER','3':'CURRENT_SOURCE'})
    b.device(CATALOG[SHORTLIST['signal_diode']['mpn']],'REVERSE_BE','D',{'2':'BASE','1':'EMITTER'})
    b.c('SERVO_COMP','100 pF','BASE_DRIVE','EMITTER')
    b.r('IABC_LIMIT','10 kΩ','CURRENT_SOURCE','IABC1')
    # No linearizing diode bias. The small differential input is bounded by
    # the divider; a local offset trimmer is reserved for bench feedthrough.
    b.r('OTA_ATTEN_TOP','100 kΩ','SUM_PRELEVEL','OTA_SIGNAL')
    b.r('OTA_ATTEN_BOTTOM','100 Ω','OTA_SIGNAL','AGND')
    b.trim('FEEDTHROUGH','10 kΩ','REFN5','OFFSET_W','REF5')
    b.r('OFFSET_FEED','1 MΩ','OFFSET_W','OTA_OFFSET')
    b.r('OFFSET_RETURN','1 kΩ','OTA_OFFSET','AGND')
    b.r('UNUSED_BIAS_OFF','100 kΩ','IABC2','-12V')
    b.device('LM13700M_NOPB','VCA_OTA','U',{
        '1':'IABC1','2':None,'3':'OTA_SIGNAL','4':'OTA_OFFSET','5':'OTA_CURRENT',
        '6':'-12V','7':'AGND','8':None,'9':None,'10':'AGND','11':'+12V',
        '12':None,'13':'AGND','14':'AGND','15':None,'16':'IABC2'})
    b.amp('CURRENT_TO_VOLTAGE','audio','AGND','OTA_CURRENT','SUM_POSTVCA')
    b.r('TIA_FIXED','100 kΩ','SUM_POSTVCA','TIA_TRIM')
    b.trim('TIA_CAL','10 kΩ','TIA_TRIM','OTA_CURRENT')
    output_channel(b,'SUM_POSTVCA')
    return b.finish_mixer(sensitive=('SUM_NODE','OTA_SIGNAL','OTA_CURRENT','IABC1','EMITTER'))


def specification():
    return (family(),),tuple(Instance('mix4_vca',name,83+i) for i,name in enumerate(INSTANCES))
