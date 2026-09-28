"""Synth-side power inlet, OSC-ES-1 unvalidated proposal.

The rail names are the instrument's global rails. Protection components are
source-backed candidates; no reverse/offset-cable or startup qualification is
claimed by this connectivity capture.
"""
from __future__ import annotations

from dataclasses import replace
import re

from scripts.schgen.core import Family, Instance, Part
from design.spec.cells._builder import load_symbol

RAILS = ('+12V', '-12V', '+5V', 'AGND')
IDENTITIES = {
    'DW254P-2X8-L0': ('CN', 'Power ribbon inlet'),
    'mSMD110-33V': ('F', 'Synth-side resettable overcurrent limiter'),
    'SMAJ15A_C571368': ('D', '12 V rail shunt transient limiter'),
    'SMAJ6.5A_C87267': ('D', '5 V rail shunt transient limiter'),
    'GRM188R71H104KA93D': ('C', 'Local 100 nF rail bypass'),
    'CL10A105KB8NNNC': ('C', 'Local 1 uF rail reservoir'),
    'RC0603FR-072K2L': ('R', 'Rail discharge bleeder'),
    'TestPoint': ('TP', 'Bare copper rail probe pad'),
    'PWR_FLAG': ('#FLG', 'Power input declaration for ERC'),
}


def family() -> Family:
    parts: list[Part] = []
    counters: dict[str, int] = {}

    def add(name: str, key: str, pins: dict[str, str | None], *, value: str = '',
            island: str = 'POWER_ENTRY') -> None:
        symbol = load_symbol(name)
        allpins = {pin.number for unit in symbol.units.values() for pin in unit}
        if set(pins) != allpins:
            raise ValueError(f'{name}/{key}: pins {set(pins)} differ from {allpins}')
        units = [number for number, unit in symbol.units.items() if unit]
        if len(units) != 1:
            raise ValueError(f'{name}: expected one unit')
        prefix, role = IDENTITIES[name]
        counters[prefix] = counters.get(prefix, 0) + 1
        ordinal = counters[prefix]
        props = dict(re.findall(r'\(property\s+"([^\"]+)"\s+"([^\"]*)"', symbol.body))
        attrs = {
            'Role': 'power:' + role,
            'MPN': props.get('MPN', ''),
            'Manufacturer': props.get('Manufacturer', ''),
            'LCSC': props.get('LCSC', ''),
            'Island': island,
        }
        parts.append(Part(key, symbol.lib_id, prefix, ordinal, units[0],
                          50.8 + (len(parts) % 5) * 50.8,
                          50.8 + (len(parts) // 5) * 30.48,
                          pins, value=value or props.get('Value', name),
                          footprint=props.get('Footprint', ''), attributes=attrs))

    add('DW254P-2X8-L0', 'INLET', {
        '1': 'IN_N12', '2': 'IN_N12',
        **{str(n): 'AGND' for n in range(3, 9)},
        '9': 'IN_P12', '10': 'IN_P12',
        '11': 'IN_P5', '12': 'IN_P5',
        **{str(n): None for n in range(13, 17)},
    })
    for key, incoming, rail, tvs in (
        ('P12', 'IN_P12', '+12V', 'SMAJ15A_C571368'),
        ('N12', 'IN_N12', '-12V', 'SMAJ15A_C571368'),
        ('P5', 'IN_P5', '+5V', 'SMAJ6.5A_C87267'),
    ):
        add('mSMD110-33V', 'PTC_' + key, {'1': incoming, '2': rail})
        # Unidirectional TVS: pin 1 is cathode, pin 2 is anode.
        add(tvs, 'TVS_' + key,
            {'1': rail, '2': 'AGND'} if key != 'N12'
            else {'1': 'AGND', '2': rail})
        add('GRM188R71H104KA93D', 'C100N_' + key, {'1': rail, '2': 'AGND'}, value='100 nF')
        add('CL10A105KB8NNNC', 'C1U_' + key, {'1': rail, '2': 'AGND'}, value='1 uF')
        add('RC0603FR-072K2L', 'BLEED_' + key, {'1': rail, '2': 'AGND'}, value='2.2 kohm')
        add('TestPoint', 'TP_' + key, {'1': rail}, value=rail, island='POWER_PROBE')
        add('PWR_FLAG', 'FLAG_' + key, {'1': rail}, island='')
    add('TestPoint', 'TP_GND', {'1': 'AGND'}, value='AGND', island='POWER_PROBE')
    add('PWR_FLAG', 'FLAG_GND', {'1': 'AGND'}, island='')
    # Keep each rail's protection path in one horizontal row in the rendered
    # sheet. This is presentation only; connectivity comes from explicit nets.
    positions = {'INLET': (50.8, 50.8),
                 'TP_GND': (50.8, 254.0), 'FLAG_GND': (101.6, 254.0)}
    for key, y in (('P12', 101.6), ('N12', 152.4), ('P5', 203.2)):
        for stem, x in (('PTC_', 76.2), ('TVS_', 127.0),
                        ('C100N_', 177.8), ('C1U_', 228.6),
                        ('BLEED_', 279.4), ('TP_', 330.2),
                        ('FLAG_', 381.0)):
            positions[stem + key] = (x, y)
    return Family('01_power_interfaces', tuple(replace(p, x=positions[p.key][0],
                                       y=positions[p.key][1]) for p in parts),
                  global_nets=RAILS)


def specification():
    return (family(),), (Instance('01_power_interfaces', 'POWER', 3),)
