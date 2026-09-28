"""Instrument assembly entry point for captured draft families."""
from design.spec.modules.sample_hold import specification as sample_hold_specification
from design.spec.modules.oscillator import specification as oscillator_specification
from design.spec.modules.power import specification as power_specification

def specification():
    families,instances=sample_hold_specification()
    osc_families,osc_instances=oscillator_specification()
    power_families,power_instances=power_specification()
    # Reserved index allocation: H1/H2=1/2, power=3; O1..O5=11..15, octave=16.
    return (*families,*osc_families,*power_families),(*instances,*osc_instances,*power_instances)
