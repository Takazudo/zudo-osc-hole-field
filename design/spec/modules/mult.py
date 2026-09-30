"""B1/B2 precision buffered one-to-three multiples; capture remains unvalidated."""
from design.spec.modules.io_partition import refined
from collections import defaultdict
from dataclasses import replace

from scripts.schgen.core import Family, Instance
from design.spec.cells._builder import ROOT, SHORTLIST, CATALOG, cell_parts, load_symbol, STANDARD
from design.spec.modules.oscillator import Builder, PLACEMENTS, RAILS
from design.spec.modules.sample_hold import footprint

INSTANCES = ('B1', 'B2')
OUTPUTS = ('1', '2', '3')
PANEL = tuple(f'J:{{}}.{key}' for key in ('IN', *OUTPUTS)) + ('L:{}.IN.mag',)


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
    if len(rows) != 10 or len({row['uid'] for row in rows}) != 10:
        raise ValueError('MULT panel binding count/uniqueness drift')
    return rows


class MultBuilder(Builder):
    def __init__(self):
        super().__init__('MULT_CORE:${SHEETNAME}')
        self.led_island = 'MULT_LEDS:${SHEETNAME}'

    def panel_attributes(self, template):
        return ({'PanelUid': template.replace('{}', '${SHEETNAME}')},
                {instance: PLACEMENTS[template.format(instance)]['ref'] for instance in INSTANCES}) if template else ({'PanelUid': ''}, {})

    def cell(self, cell_id, tag, nets, *, panel=None, role=None, led=False):
        # Cell-private pins are namespaced by the exact locked UID and tag. Only
        # the LED receives the physical panel binding; its driver stays local.
        uid = (panel or 'J:{}.IN').format(INSTANCES[0])
        for part in cell_parts(cell_id, uid, nets, ordinal_start=1, instance_tag=tag):
            attrs = {**part.attributes, 'PanelUid': '',
                     'Island': self.led_island if led else self.island}
            refs = {}
            if panel and part.symbol.endswith('Kingbright_White_0402'):
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
            finished = builder.finish('mult', globals=RAILS)
            for part in finished.parts:
                attrs = {**part.attributes,
                         'Role': part.attributes.get('Role', '').replace('oscillator:', 'mult:')}
                if part.key.startswith('C_DEC_'):
                    attrs['Island'] = island
                compiled.append(replace(part, key=tag + '_' + part.key, attributes=attrs))

        # CORE and LED are compiled independently to keep indicator drivers next
        # to their panel LEDs; allocate one collision-free ref space afterward.
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
        return Family('mult', tuple(output), global_nets=RAILS,
                      sensitive_nets=('IN_PROTECTED', 'IN_SENSE'), paper='A0')


@refined
def family():
    panel_bindings()
    builder = MultBuilder()
    builder.device('WQP518MA', 'J_IN', 'J', {'T': 'IN_TIP', 'S': 'AGND', 'TN': None},
                   panel='J:{}.IN', island='')
    builder.cell('input_fault_switch', 'IN', {'JACK': 'IN_TIP', 'PROTECTED': 'IN_PROTECTED'})
    builder.cell('high_impedance_input', 'IN',
                 {'PROTECTED': 'IN_PROTECTED', 'SENSE': 'IN_SENSE',
                  'BUFFERED': 'IN_BUFFER'}, role='precision')
    builder.cell('magnitude_indicator', 'IN', {'MONITOR': 'IN_BUFFER'},
                 panel='L:{}.IN.mag', led=True)
    for output in OUTPUTS:
        builder.cell('precision_output', 'OUT_' + output,
                     {'SIGNAL': 'IN_BUFFER', 'JACK': 'OUT_' + output + '_TIP'})
        builder.device('WQP518MA', 'J_OUT_' + output, 'J',
                       {'T': 'OUT_' + output + '_TIP', 'S': 'AGND', 'TN': None},
                       panel='J:{}.' + output, island='')
    return builder.complete()


def specification():
    return (family(),), tuple(Instance('mult', name, 31 + i) for i, name in enumerate(INSTANCES))
