"""Conditional EXT inlet sheet; electrical protection remains unimplemented.

The two abstract symbols have no footprint or BOM entry. The boundary's
power_out pins satisfy schematic ERC only; they do not represent a physical
source, a conducting path, or completed protection. Issue #59 owns the circuit.
"""
from __future__ import annotations

import re
from scripts.schgen.core import Family, Instance, Part
from design.spec.cells._builder import load_symbol

RAILS = ('+12V', '-12V', '+5V')
RAW = ('+12V_IN', '-12V_IN', '+5V_IN')
GLOBAL_NETS = (*RAILS, *RAW, 'AGND')
IDENTITIES = {
    'OSC_EXT_INLET_R1': ('CN', 'Logical eight-contact inlet, NOT SELECTED'),
    'OSC_EXT_BOUNDARY_R1': ('XB', 'Unimplemented source/protection requirement'),
    'GRM188R71H104KA93D': ('C', 'Local 100 nF rail bypass'),
    'CL10A105KB8NNNC': ('C', 'Local 1 uF rail reservoir'),
    'RC0603FR-072K2L': ('R', 'Rail discharge bleeder'),
    'TestPoint': ('TP', 'Bare copper rail probe pad'),
}


def family() -> Family:
    parts: list[Part] = []
    counters: dict[str, int] = {}

    def add(name: str, key: str, pins: dict[str, str | None], x: float, y: float,
            *, value: str = '', island: str = 'POWER_ENTRY', abstract: bool = False) -> None:
        symbol = load_symbol(name)
        allpins = {pin.number for unit in symbol.units.values() for pin in unit}
        if set(pins) != allpins:
            raise ValueError(f'{name}/{key}: pins {set(pins)} differ from {allpins}')
        units = [number for number, unit in symbol.units.items() if unit]
        if len(units) != 1:
            raise ValueError(f'{name}: expected one unit')
        prefix, role = IDENTITIES[name]
        counters[prefix] = counters.get(prefix, 0) + 1
        props = dict(re.findall(r'\(property\s+"([^\"]+)"\s+"([^\"]*)"', symbol.body))
        attrs = {
            'Role': 'power:' + role,
            'MPN': '' if abstract else props.get('MPN', ''),
            'Manufacturer': '' if abstract else props.get('Manufacturer', ''),
            'LCSC': '' if abstract else props.get('LCSC', ''),
            'Island': island,
            'Implementation': 'REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE' if abstract else 'Unvalidated physical draft',
        }
        # KiCad omits on_board=no symbols from native netlists. Keep these
        # no-footprint abstract symbols in the export for pin/net auditing;
        # in_bom=no and no footprint prohibit placement and ordering.
        parts.append(Part(key, symbol.lib_id, prefix, counters[prefix], units[0],
                          x, y, pins, value=value or props.get('Value', name),
                          footprint='' if abstract else props.get('Footprint', ''),
                          attributes=attrs, in_bom=not abstract, on_board=True,
                          abstract=abstract))

    add('OSC_EXT_INLET_R1', 'INLET', {
        '1': '+12V_IN', '2': '-12V_IN', '3': '+5V_IN', '4': None,
        '5': 'AGND', '6': 'AGND', '7': 'AGND', '8': 'AGND',
    }, 50.8, 76.2, value='OSC-EXT-PWR-8-R1 / REQUIREMENT ONLY', abstract=True)
    add('OSC_EXT_BOUNDARY_R1', 'BOUNDARY', {
        '1': '+12V_IN', '2': '-12V_IN', '3': '+5V_IN',
        '4': '+12V', '5': '-12V', '6': '+5V',
        '7': 'AGND',
    }, 127.0, 76.2, value='UNIMPLEMENTED EXT PROTECTION / NOT ENERGIZABLE', abstract=True)
    for key, rail, y in (('P12', '+12V', 127.0), ('N12', '-12V', 177.8), ('P5', '+5V', 228.6)):
        add('GRM188R71H104KA93D', 'C100N_' + key,
            {'1': rail, '2': 'AGND'}, 50.8, y, value='100 nF')
        add('CL10A105KB8NNNC', 'C1U_' + key,
            {'1': rail, '2': 'AGND'}, 101.6, y, value='1 uF')
        add('RC0603FR-072K2L', 'BLEED_' + key,
            {'1': rail, '2': 'AGND'}, 152.4, y, value='2.2 kohm')
        add('TestPoint', 'TP_' + key, {'1': rail}, 203.2, y,
            value=rail, island='POWER_PROBE')
    add('TestPoint', 'TP_GND', {'1': 'AGND'}, 50.8, 279.4,
        value='AGND', island='POWER_PROBE')
    return Family('01_power_interfaces', tuple(parts), global_nets=GLOBAL_NETS)


def specification():
    return (family(),), (Instance('01_power_interfaces', 'POWER', 3),)
