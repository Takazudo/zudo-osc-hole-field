"""Instrument assembly entry point for captured draft families."""
from design.spec.modules.sample_hold import specification as sample_hold_specification
from design.spec.modules.oscillator import specification as oscillator_specification
from design.spec.modules.filter import specification as filter_specification
from design.spec.modules.power import specification as power_specification
from design.spec.modules.noise import specification as noise_specification
from design.spec.modules.envelope import specification as envelope_specification


def specification():
    families, instances = sample_hold_specification()
    osc_families, osc_instances = oscillator_specification()
    filter_families, filter_instances = filter_specification()
    power_families, power_instances = power_specification()
    noise_families, noise_instances = noise_specification()
    # Reserved indices: H1/H2=1/2, power=3, O1..O5=11..15,
    # octave reference=16, F1..F3=21..23.
    # Envelope E1..E6 reserves component indices 41..46.
    env_families,env_instances=envelope_specification()
    families=(*families,*env_families)
    instances=(*instances,*env_instances)
    return (
        (*families, *osc_families, *filter_families, *power_families, *noise_families),
        (*instances, *osc_instances, *filter_instances, *power_instances, *noise_instances),
    )
