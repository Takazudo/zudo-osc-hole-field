"""Instrument assembly entry point for captured draft families."""
from design.spec.modules.sample_hold import specification as sample_hold_specification
from design.spec.modules.oscillator import specification as oscillator_specification
from design.spec.modules.filter import specification as filter_specification
from design.spec.modules.power import specification as power_specification
from design.spec.modules.envelope import specification as envelope_specification
from design.spec.modules.mix5 import specification as mix5_specification
from design.spec.modules.mix4_vca import specification as mix4_vca_specification


def specification():
    families, instances = sample_hold_specification()
    osc_families, osc_instances = oscillator_specification()
    filter_families, filter_instances = filter_specification()
    power_families, power_instances = power_specification()
    # Reserved indices: H1/H2=1/2, power=3, O1..O5=11..15,
    # octave reference=16, F1..F3=21..23.
    # Envelope E1..E6 reserves component indices 41..46.
    env_families,env_instances=envelope_specification()
    mix5_families,mix5_instances=mix5_specification()
    mix4_families,mix4_instances=mix4_vca_specification()
    families=(*families,*env_families,*mix5_families,*mix4_families)
    instances=(*instances,*env_instances,*mix5_instances,*mix4_instances)
    return (
        (*families, *osc_families, *filter_families, *power_families),
        (*instances, *osc_instances, *filter_instances, *power_instances),
    )
