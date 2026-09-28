"""Instrument assembly entry point for captured draft families."""
from design.spec.modules.sample_hold import specification as sample_hold_specification
from design.spec.modules.oscillator import specification as oscillator_specification
from design.spec.modules.filter import specification as filter_specification
from design.spec.modules.power import specification as power_specification
from design.spec.modules.noise import specification as noise_specification
from design.spec.modules.envelope import specification as envelope_specification
from design.spec.modules.mult import specification as mult_specification
from design.spec.modules.manual_ab import specification as manual_ab_specification


def specification():
    families, instances = sample_hold_specification()
    osc_families, osc_instances = oscillator_specification()
    filter_families, filter_instances = filter_specification()
    power_families, power_instances = power_specification()
    noise_families, noise_instances = noise_specification()
    env_families, env_instances = envelope_specification()
    mult_families, mult_instances = mult_specification()
    manual_ab_families, manual_ab_instances = manual_ab_specification()
    # H1/H2=1/2, power=3, O1..O5=11..15, octave reference=16,
    # F1..F3=21..23, B1/B2=31/32, X1/X2=33/34, E1..E6=41..46,
    # N1=61. Each family keeps a separate physical reference block.
    return (
        (*families, *osc_families, *filter_families, *power_families,
         *noise_families, *env_families, *mult_families, *manual_ab_families),
        (*instances, *osc_instances, *filter_instances, *power_instances,
         *noise_instances, *env_instances, *mult_instances, *manual_ab_instances),
    )
