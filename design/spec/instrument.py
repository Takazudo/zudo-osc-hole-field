"""Instrument assembly entry point; H1/H2 are the first captured draft family."""
from design.spec.modules.sample_hold import specification as sample_hold_specification
from scripts.schgen.core import Family, Instance, Part

def specification():
    families,instances=sample_hold_specification()
    rails=('+12V','-12V','+5V','AGND')
    flags=tuple(Part(f'RAIL_{i}','Fixture:PWR_FLAG','#FLG',i,0,50.8+i*25.4,50.8,{'1':net},value='HARNESS_SUPPLY') for i,net in enumerate(rails,1))
    return (*families,Family('pilot_power',flags,global_nets=rails)),(*instances,Instance('pilot_power','PILOT_POWER',3))
