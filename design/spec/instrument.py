"""Instrument assembly entry point for captured draft families."""
from design.spec.modules.sample_hold import specification as sample_hold_specification
from design.spec.modules.oscillator import specification as oscillator_specification
from design.spec.modules.filter import specification as filter_specification
from design.spec.modules.power import specification as power_specification
from design.spec.modules.noise import specification as noise_specification
from design.spec.modules.envelope import specification as envelope_specification
from design.spec.modules.mult import specification as mult_specification
from design.spec.modules.manual_ab import specification as manual_ab_specification
from design.spec.modules.mix5 import specification as mix5_specification
from design.spec.modules.mix4_vca import specification as mix4_vca_specification
from design.spec.modules.wavefolder import specification as wavefolder_specification


def specification():
    specs = (
        sample_hold_specification(), oscillator_specification(),
        filter_specification(), power_specification(), noise_specification(),
        envelope_specification(), mult_specification(), manual_ab_specification(),
        mix5_specification(), mix4_vca_specification(), wavefolder_specification(),
    )
    # H1/H2=1/2, power=3, O1..O5=11..15, octave ref=16,
    # F1..F3=21..23, B1/B2=31/32, X1/X2=33/34, E1..E6=41..46,
    # W2/W1=51/52, N1=61, M5A/B=81/82, M4A/B=83/84.
    return (tuple(f for families, _ in specs for f in families),
            tuple(i for _, instances in specs for i in instances))
