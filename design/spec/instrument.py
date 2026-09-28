"""Instrument assembly entry point; H1/H2 are the first captured draft family."""
from design.spec.modules.sample_hold import specification as sample_hold_specification
from design.spec.modules.oscillator import specification as oscillator_specification
from design.spec.modules.filter import specification as filter_specification
from scripts.schgen.core import Family, Instance, Part

def specification():
    families,instances=sample_hold_specification()
    osc_families,osc_instances=oscillator_specification()
    families=(*families,*osc_families)
    instances=(*instances,*osc_instances)
    filter_families,filter_instances=filter_specification()
    families=(*families,*filter_families)
    instances=(*instances,*filter_instances)
    # Filter family F1..F3 reserves component indices 21..23.
    # Reserved index allocation: pilot H1/H2=1/2, power=3; O1..O5=11..15, shared octave=16.
    rails=('+12V','-12V','+5V','AGND')
    flags=tuple(Part(f'RAIL_{i}','Fixture:PWR_FLAG','#FLG',i,0,50.8+i*25.4,50.8,{'1':net},value='HARNESS_SUPPLY') for i,net in enumerate(rails,1))
    return (*families,Family('pilot_power',flags,global_nets=rails)),(*instances,Instance('pilot_power','PILOT_POWER',3))
