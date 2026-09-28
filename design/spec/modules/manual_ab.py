"""X1/X2 maintained buffered A/B selectors; contact mapping remains a bench gate."""
from collections import defaultdict
from dataclasses import replace

from scripts.schgen.core import Family, Instance
from design.spec.cells._builder import ROOT, SHORTLIST, CATALOG, cell_parts, load_symbol, STANDARD
from design.spec.modules.oscillator import Builder, PLACEMENTS, RAILS
from design.spec.modules.sample_hold import footprint

INSTANCES = ('X1', 'X2')
INPUTS = ('A', 'B')
PANEL = tuple(f'J:{{}}.IN-{key}' for key in INPUTS) + ('J:{}.OUT', 'C:{}.SELECT') + tuple(
    f'L:{{}}.IN-{key}.mag' for key in INPUTS) + ('L:{}.OUT.mag',)
SENSITIVE = ('A_PROTECTED', 'A_SENSE', 'B_PROTECTED', 'B_SENSE',
             'SELECT_A_CONTACT', 'SELECT_B_CONTACT', 'SELECTOR_COMMON')


def panel_bindings():
    rows = []
    for instance in INSTANCES:
        for template in PANEL:
            uid = template.format(instance)
            if uid not in PLACEMENTS:
                raise ValueError('missing locked panel UID ' + uid)
            placement = PLACEMENTS[uid]
            rows.append({'instance': instance, 'uid': uid, 'ref': placement['ref'],
                         'x_mm': placement['x_mm'], 'y_mm': placement['y_mm']})
    if len(rows) != 14 or len({row['uid'] for row in rows}) != 14:
        raise ValueError('manual A/B panel binding count/uniqueness drift')
    return rows


class ManualABBuilder(Builder):
    def __init__(self):
        super().__init__('AB_CORE:${SHEETNAME}')
        self.led_island = 'AB_LEDS:${SHEETNAME}'

    def panel_attributes(self, template):
        return ({'PanelUid': template.replace('{}', '${SHEETNAME}')},
                {instance: PLACEMENTS[template.format(instance)]['ref'] for instance in INSTANCES}) if template else ({'PanelUid': ''}, {})

    def cell(self, cell_id, tag, nets, *, panel=None, role=None, led=False):
        uid = (panel or 'J:{}.IN-A').format(INSTANCES[0])
        for part in cell_parts(cell_id, uid, nets, ordinal_start=1, instance_tag=tag):
            attrs = {**part.attributes, 'PanelUid': '',
                     'Island': self.led_island if led else self.island}
            refs = {}
            if panel and part.symbol.endswith('0603Whitelight_C2290'):
                panel_attrs, refs = self.panel_attributes(panel)
                attrs.update(panel_attrs)
            if role and part.symbol.split(':')[-1].startswith('OPA'):
                record = SHORTLIST[STANDARD['roles'][role]['part_id']]
                symbol = load_symbol(CATALOG[record['mpn']])
                attrs.update(MPN=record['mpn'], Manufacturer=record['manufacturer'], LCSC=record.get('lcsc', ''))
                part = replace(part, symbol=symbol.lib_id, footprint=footprint(symbol), value=record['mpn'])
            self.parts.append(replace(part, attributes=attrs, panel_refs=refs))

    def complete(self):
        compiled = []
        for tag, island in (('CORE', self.island), ('LED', self.led_island)):
            selected = [p for p in self.parts if (p.attributes.get('Island') == self.led_island) == (tag == 'LED')]
            if not selected:
                continue
            builder = Builder(island)
            builder.parts = selected
            finished = builder.finish('manual_ab', globals=RAILS)
            for part in finished.parts:
                attrs = {**part.attributes,
                         'Role': part.attributes.get('Role', '').replace('oscillator:', 'manual_ab:')}
                if part.key.startswith('C_DEC_'):
                    attrs['Island'] = island
                compiled.append(replace(part, key=tag + '_' + part.key, attributes=attrs))

        assigned = {}
        counts = defaultdict(int)
        output = []
        for part in compiled:
            prefix = 'R' if part.prefix == 'RB' else part.prefix
            package = part.key.rsplit('.', 1)[0]
            group = (prefix, package)
            if group not in assigned:
                counts[prefix] += 1
                assigned[group] = counts[prefix]
            number = assigned[group]
            final_prefix = prefix if number <= 99 else prefix + 'B'
            ordinal = (number - 1) % 99 + 1
            output.append(replace(part, prefix=final_prefix, ordinal=ordinal,
                                  x=45.72 + (len(output) % 17) * 63.5,
                                  y=66.04 + (len(output) // 17) * 38.1))
        return Family('manual_ab', tuple(output), global_nets=RAILS,
                      sensitive_nets=SENSITIVE, paper='A0')


def family():
    panel_bindings()
    builder = ManualABBuilder()
    for source in INPUTS:
        source_key = source
        tip = source_key + '_TIP'
        protected = source_key + '_PROTECTED'
        buffered = source_key + '_BUFFER'
        builder.device('WQP518MA', 'J_IN_' + source, 'J',
                       {'T': tip, 'S': 'AGND', 'TN': None},
                       panel='J:{}.IN-' + source, island='')
        builder.cell('input_fault_switch', source, {'JACK': tip, 'PROTECTED': protected})
        builder.cell('high_impedance_input', source,
                     {'PROTECTED': protected, 'SENSE': source + '_SENSE',
                      'BUFFERED': buffered}, role='precision')
        builder.cell('magnitude_indicator', source, {'MONITOR': buffered},
                     panel='L:{}.IN-' + source + '.mag', led=True)

    # The 2.2 kΩ resistors limit current if the maintained switch momentarily
    # bridges both contacts. Contact side assignment is provisional pending a
    # continuity coupon because the retained exact-part source does not confirm
    # lever orientation.
    builder.r('SELECT_A_SERIES', '2.2 kΩ', 'A_BUFFER', 'SELECT_A_CONTACT')
    builder.r('SELECT_B_SERIES', '2.2 kΩ', 'B_BUFFER', 'SELECT_B_CONTACT')
    builder.device('2MS1T1B1M2QES-5', 'SELECT', 'SW',
                   {'1': 'SELECT_B_CONTACT', '2': 'SELECTOR_COMMON', '3': 'SELECT_A_CONTACT'},
                   panel='C:{}.SELECT', island=builder.island)
    builder.r('SELECT_COMMON_BIAS', '10 MΩ', 'SELECTOR_COMMON', 'AGND')

    builder.cell('precision_output', 'OUT',
                 {'SIGNAL': 'SELECTOR_COMMON', 'DRIVE': 'OUT_BUFFERED', 'JACK': 'OUT_TIP'})
    builder.device('WQP518MA', 'J_OUT', 'J', {'T': 'OUT_TIP', 'S': 'AGND', 'TN': None},
                   panel='J:{}.OUT', island='')
    builder.cell('magnitude_indicator', 'OUT', {'MONITOR': 'OUT_BUFFERED'},
                 panel='L:{}.OUT.mag', led=True)
    return builder.complete()


def specification():
    return (family(),), tuple(Instance('manual_ab', name, 33 + i) for i, name in enumerate(INSTANCES))
