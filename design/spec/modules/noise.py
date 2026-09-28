"""N1 four-colour noise draft: two NOISE2 outputs, four buffered paths.

All filter poles and level trims are proposals, not measured transfer functions.
"""
from dataclasses import replace
import json
from scripts.schgen.core import Family, Instance, Part
from design.spec.modules.oscillator import Builder, PLACEMENTS, RAILS

OUTPUTS = ('WHITE', 'PINK', 'BLUE', 'BROWN')
PANEL = tuple(f'J:N1.{name}' for name in OUTPUTS)


def panel_bindings():
    rows = []
    for uid in PANEL:
        p = PLACEMENTS[uid]
        rows.append({'instance': 'N1', 'uid': uid, 'ref': p['ref'],
                     'x_mm': p['x_mm'], 'y_mm': p['y_mm']})
    assert len(rows) == len({r['uid'] for r in rows}) == 4
    return rows


class NoiseBuilder(Builder):
    def __init__(self):
        super().__init__('NOISE_ANALOG')

    def panel_attributes(self, template):
        if not template:
            return {'PanelUid': ''}, {}
        uid = template.format('N1')
        return {'PanelUid': template.replace('{}', '${SHEETNAME}')}, {'N1': PLACEMENTS[uid]['ref']}

    def cell(self, id, tag, nets):
        from design.spec.cells._builder import cell_parts
        for p in cell_parts(id, 'J:N1.WHITE', nets, ordinal_start=1, instance_tag=tag):
            self.parts.append(replace(p, attributes={**p.attributes, 'Block': 'noise',
                                                     'PanelUid': '', 'Island': self.island}, panel_refs={}))

    def finish_noise(self):
        family = super().finish('noise', globals=RAILS,
                                sensitive=('NOISE_VDD', 'WHITE_RAW', 'PINK_RAW',
                                           'WHITE_AC', 'PINK_AC', 'BLUE_SHAPE',
                                           'BROWN_SHAPE'))
        parts = tuple(replace(p, attributes={**p.attributes, 'Block': 'noise',
                                            'Role': p.attributes.get('Role', '').replace('oscillator:', 'noise:')})
                      for p in family.parts)
        return replace(family, parts=parts)


def family():
    panel_bindings()
    b = NoiseBuilder()
    # The manufacturer's output rate is about 100 kHz; this local RC supply
    # branch isolates its fast switching from the analogue +5 V distribution.
    b.r('DIGITAL_FEED', '22 Ω', '+5V', 'NOISE_VDD')
    b.c('DIGITAL_BULK', '4.7 µF', 'NOISE_VDD', 'AGND')
    b.c('DIGITAL_FAST', '100 nF', 'NOISE_VDD', 'AGND')
    b.device('NOISE2', 'SOURCE', 'U', {
        '1': 'NOISE_VDD', '2': 'AGND', '3': 'WHITE_RAW', '4': 'AGND',
        '5': 'AGND', '6': 'AGND', '7': 'PINK_RAW', '8': 'AGND',
    }, island='NOISE_DIGITAL')
    # ERC power declaration is local to the filtered rail, after the feed R.
    b.parts.append(Part('DIGITAL_POWER_FLAG', 'Fixture:PWR_FLAG', '#FLG', 1, 0,
                        50.8, 50.8, {'1': 'NOISE_VDD'}, value='FILTERED_5V',
                        attributes={'Block': 'noise', 'Role': 'noise:local filtered supply',
                                    'MPN': '', 'Manufacturer': '', 'LCSC': '',
                                    'PanelUid': '', 'Island': 'NOISE_DIGITAL'}))
    # WHITE is a two-level digital waveform; reconstruct before AC coupling.
    b.r('WHITE_RECON', '1 kΩ', 'WHITE_RAW', 'WHITE_LP')
    b.c('WHITE_RECON', '10 nF', 'WHITE_LP', 'AGND')
    b.c('WHITE_AC', '100 nF', 'WHITE_LP', 'WHITE_AC')
    b.r('WHITE_BLEED', '100 kΩ', 'WHITE_AC', 'AGND')
    b.amp('WHITE_INPUT', 'audio', 'WHITE_AC', 'WHITE_SIGNAL', 'WHITE_SIGNAL')
    # PINK is a low-drive DAC output; buffer it before the same finite band.
    b.amp('PINK_SOURCE', 'audio', 'PINK_RAW', 'PINK_SOURCE', 'PINK_SOURCE')
    b.r('PINK_RECON', '1 kΩ', 'PINK_SOURCE', 'PINK_LP')
    b.c('PINK_RECON', '10 nF', 'PINK_LP', 'AGND')
    b.c('PINK_AC', '100 nF', 'PINK_LP', 'PINK_AC')
    b.r('PINK_BLEED', '100 kΩ', 'PINK_AC', 'AGND')
    b.amp('PINK_INPUT', 'audio', 'PINK_AC', 'PINK_SIGNAL', 'PINK_SIGNAL')
    # Leaky inverting integrator: 1 MΩ || 10 nF gives 15.9 Hz lower knee.
    b.amp('BROWN_LEAK', 'audio', 'AGND', 'BROWN_SUM', 'BROWN_SHAPE')
    b.r('BROWN_IN', '100 kΩ', 'WHITE_SIGNAL', 'BROWN_SUM')
    b.r('BROWN_LEAK', '1 MΩ', 'BROWN_SHAPE', 'BROWN_SUM')
    b.c('BROWN_LEAK', '10 nF', 'BROWN_SHAPE', 'BROWN_SUM')
    # Inverting differentiator with finite low and high knees, from PINK.
    b.c('BLUE_INPUT', '100 pF', 'PINK_SIGNAL', 'BLUE_SERIES')
    b.r('BLUE_INPUT', '100 kΩ', 'BLUE_SERIES', 'BLUE_SUM')
    b.amp('BLUE_DIFF', 'audio', 'AGND', 'BLUE_SUM', 'BLUE_SHAPE')
    b.r('BLUE_FEEDBACK', '100 kΩ', 'BLUE_SHAPE', 'BLUE_SUM')
    b.c('BLUE_FEEDBACK', '33 pF', 'BLUE_SHAPE', 'BLUE_SUM')
    for name, source in [('WHITE', 'WHITE_SIGNAL'), ('PINK', 'PINK_SIGNAL'),
                         ('BLUE', 'BLUE_SHAPE'), ('BROWN', 'BROWN_SHAPE')]:
        # Four separately isolated output channels. The 10 kΩ feedback trims
        # offer only a small range; equal-RMS matching remains a bench gate.
        b.amp(name + '_LEVEL', 'audio', 'AGND', name + '_LEVEL_SUM', name + '_LEVEL')
        b.r(name + '_LEVEL_IN', '10 kΩ' if name == 'BLUE' else '20 kΩ' if name == 'BROWN' else '100 kΩ',
            source, name + '_LEVEL_SUM')
        b.r(name + '_LEVEL_FIXED', '100 kΩ', name + '_LEVEL', name + '_TRIM')
        b.trim(name + '_LEVEL_TRIM', '10 kΩ', name + '_TRIM', name + '_LEVEL_SUM')
        b.cell('general_output', name, {'SIGNAL': name + '_LEVEL',
                                        'JACK': name + '_TIP'})
        b.device('WQP518MA', 'J_' + name, 'J',
                 {'T': name + '_TIP', 'S': 'AGND', 'TN': None},
                 panel='J:{}.{}'.format('{}', name), island='')
    return b.finish_noise()


def specification():
    return (family(),), (Instance('noise', 'N1', 61),)
