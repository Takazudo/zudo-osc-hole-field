"""Source-level I/O allocation and equivalent-channel package packing for #60.

Regions are candidate electrical ownership, not PCB outlines or fit claims. No
new circuit topology is inferred. Existing channel nets and exact IC identities
are preserved; surplus fitted sections remain grounded followers.
"""
from collections import defaultdict
from dataclasses import replace
from functools import wraps

JACK_CELLS = {'input_fault_switch', 'high_impedance_input', 'general_output',
              'precision_output', 'magnitude_indicator', 'clip_detector'}
CONTROL_CELLS = {'switch_button_input', 'stage_indicator', 'slew_island'}
AMP_MAPS = (('1','2','3'), ('7','6','5'), ('8','9','10'), ('14','13','12'))
SCHMITT_MAPS = (('2','1'), ('4','3'), ('6','5'), ('8','9'), ('10','11'), ('12','13'))


def region(part, family):
    uid = part.attributes.get('PanelUid', '')
    if uid.startswith('J:') or uid.startswith('L:') and '.stage' not in uid:
        return 'jack'
    if uid.startswith('C:') or '.stage' in uid:
        return 'selector' if uid.endswith('.OCT') else 'control'
    full_role = part.attributes.get('Role', '')
    if family == 'offset' and (full_role == 'offset:RESTORE' or full_role.startswith('offset:R_RESTORE_')):
        return 'jack'
    role = full_role.split(':')[0]
    if role in JACK_CELLS:
        return 'jack'
    if role in CONTROL_CELLS or family == 'manual_ab':
        return 'control'
    return 'core'


def spare(part):
    if part.symbol.endswith(('OPA4196IDR', 'OPA4197IPWR', 'OPA4197IDR')) and part.unit in range(1,5):
        out, minus, plus = AMP_MAPS[part.unit-1]
        return part.pins[out] == part.pins[minus] and part.pins[plus] == 'AGND'
    if part.symbol.endswith('SN74HC14DR') and part.unit in range(1,7):
        out, inp = SCHMITT_MAPS[part.unit-1]
        return part.pins[out] is None and part.pins[inp] == 'AGND'
    return False


def refined(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        return refine(function(*args, **kwargs))
    return wrapped


def refine(family):
    parts = list(family.parts)
    # Old bypass keys encode their owner package except the H pilot, which has
    # an explicit DECOUP: owner attribute. Rebuild bypass ownership below.
    bypass = [p for p in parts if 'C_DEC_' in p.key]
    parts = [p for p in parts if p not in bypass]
    result = []
    groups = defaultdict(list)
    for p in parts:
        reg = region(p, family.name)
        attrs = {**p.attributes, 'BoardRegion': reg}
        if reg != 'core':
            old = attrs.get('Island', '')
            # Retain already local optical and S&H slew identities.
            keep = (old.startswith(('FILTER_LEDS:', 'FOLDER_LEDS:', 'L:', 'C:'))
                    or family.name == 'sample_hold' and p.attributes.get('Role','').startswith('slew_island:'))
            attrs['Island'] = old if keep else f'IO_{reg.upper()}:${{SHEETNAME}}'
        elif not attrs.get('Island'):
            attrs['Island'] = f'IO_CORE:${{SHEETNAME}}'
        p = replace(p, attributes=attrs)
        if p.symbol.endswith(('OPA4196IDR','OPA4197IPWR','OPA4197IDR','SN74HC14DR')):
            groups[p.symbol].append(p)
        else:
            result.append(p)
    extra_ordinal = max((p.ordinal for p in family.parts if p.prefix == 'U'), default=0)
    for symbol, entries in groups.items():
        is_amp = symbol.endswith(('OPA4196IDR','OPA4197IPWR','OPA4197IDR'))
        maps = AMP_MAPS if is_amp else SCHMITT_MAPS
        power_unit = len(maps)+1
        package_templates = [p for p in entries if p.unit == power_unit]
        channels = defaultdict(list)
        for p in entries:
            if p.unit != power_unit and not spare(p):
                channels[p.attributes['BoardRegion']].append(p)
        # Keep original package count when there is spare capacity. Any added
        # package is real, with all units and two bypasses, and enters worksheets.
        batches = [(reg, rows[n:n+len(maps)]) for reg, rows in sorted(channels.items())
                   for n in range(0, len(rows), len(maps))]
        while len(batches) < len(package_templates):
            batches.append(('core', []))
        for number, (reg, batch) in enumerate(batches):
            if number < len(package_templates):
                template = package_templates[number]
            else:
                extra_ordinal += 1
                if extra_ordinal > 99:
                    raise ValueError('I/O package ordinal capacity exceeded')
                template = replace(package_templates[0], key=f'IO_EXTRA_{extra_ordinal}.{power_unit}', ordinal=extra_ordinal)
            stem = template.key.rsplit('.',1)[0]
            attrs = {**template.attributes, 'BoardRegion': reg,
                     'Island': f'IO_{reg.upper()}:${{SHEETNAME}}'}
            for unit, target in enumerate(maps, 1):
                if unit <= len(batch):
                    channel = batch[unit-1]
                    pins = dict(zip(target, (channel.pins[x] for x in maps[channel.unit-1])))
                    channel_attrs = {**channel.attributes, 'LogicalCellKey': channel.attributes.get('LogicalCellKey') or channel.key}
                else:
                    channel = template
                    net = f'{stem}_IO_UNUSED{unit}'
                    pins = dict(zip(target, (net,net,'AGND') if is_amp else (None,'AGND')))
                    channel_attrs = {**attrs, 'Role': f'{family.name}:unused grounded follower' if is_amp else f'{family.name}:unused grounded Schmitt', 'LogicalCellKey': ''}
                result.append(replace(channel, key=f'{stem}.{unit}', prefix=template.prefix,
                                      ordinal=template.ordinal, unit=unit, pins=pins,
                                      attributes=channel_attrs, x=template.x, y=template.y))
            result.append(replace(template, attributes=attrs))
    # Whole non-repacked packages must also have one electrical region. Their
    # supply units inherit the live unit's region (no separate power island).
    packages = defaultdict(list)
    for p in result:
        if p.prefix == 'U':
            packages[p.key.rsplit('.',1)[0]].append(p)
    for stem, rows in packages.items():
        regions = {p.attributes['BoardRegion'] for p in rows}
        if len(regions) != 1:
            raise ValueError(f'{family.name}: split fitted package {stem}: {regions}')
    # Retain every original bypass reference and value. Package supplies specify
    # local derived rails such as VEE5/NOISE_VDD, so reuse existing rail nets.
    pools = defaultdict(list)
    for p in bypass:
        rail = next(n for n in p.pins.values() if n != 'AGND')
        pools[rail].append(p)
    consumed = set()
    for stem, rows in packages.items():
        p = rows[-1]
        supply = {pin: net for q in rows for pin, net in q.pins.items()}
        sym = p.symbol.split(':')[-1]
        rail_pins = {'OPA4196IDR':('4','11'),'OPA4197IPWR':('4','11'),'OPA4197IDR':('4','11'),
                     'SN74HC14DR':('14',),'SN74HC00DR':('14',),'SN74HC74DR':('14',),
                     'CD74HC221M96':('16',),'REF5050AIDR':('2',),'LM393BIDR':('8','4'),
                     'ADG5412FBRUZ':('13','4'),'TMUX7412FRRPR':('11','2'),'TMUX6112PWR':('13','4'),'LM13700M_NOPB':('11','6'),
                     'AS3340D':('16','3'),'NOISE2':('1',),'LF398M_NOPB':('12','3')}[sym]
        for pin in rail_pins:
            rail = supply[pin]
            if rail == 'AGND':
                continue
            if pools[rail]:
                cap = pools[rail].pop(0)
            else:
                # New exact 100 nF bypass copied from the retained selected part.
                cap = next(c for c in bypass if set(c.pins.values()) == {rail,'AGND'})
                ordinal = max([q.ordinal for q in family.parts if q.prefix == 'C'] + [q.ordinal for q in result if q.prefix == 'C'] + [0])+1
                cap = replace(cap, key=f'C_DEC_IO_EXTRA_{ordinal}', prefix='C', ordinal=ordinal)
            consumed.add(cap.key)
            result.append(replace(cap, attributes={**cap.attributes, 'BoardRegion':p.attributes['BoardRegion'],
                                                 'Island':p.attributes['Island'], 'Decouples':stem}, pins={'1':rail,'2':'AGND'}))
    if any(pools.values()):
        raise ValueError(f'{family.name}: orphaned bypass capacitors')
    # Preserve drawing ordering for unchanged keys. Reassigned units receive the
    # original slot positions; extra units go to the existing page grid tail.
    original = {p.key:p for p in family.parts}
    result.sort(key=lambda p: next((n for n,q in enumerate(family.parts) if q.key==p.key),len(family.parts)))
    positioned=[]
    for n,p in enumerate(result):
        old=original.get(p.key)
        positioned.append(replace(p,x=old.x if old else 45.72+(n%17)*63.5,
                                  y=old.y if old else 66.04+(n//17)*38.1))
    result_family = replace(family, parts=tuple(positioned))
    if channel_signatures(family) != channel_signatures(result_family):
        raise ValueError(f'{family.name}: channel function changed during I/O packing')
    # The fixed stage emitters overlap pot mounting holes on a common PCB.
    # Their already dedicated complete amplifier package and bypasses therefore
    # follow the whole stage circuit onto a distinct front optical plane.
    stage_packages = {p.key.rsplit('.', 1)[0] for p in result_family.parts
                      if p.prefix == 'U' and p.attributes.get('Role', '').startswith('stage_indicator:')}
    optical = []
    for p in result_family.parts:
        stage = (p.attributes.get('Role', '').startswith('stage_indicator:')
                 or p.prefix == 'U' and p.key.rsplit('.', 1)[0] in stage_packages
                 or p.attributes.get('Decouples') in stage_packages)
        if stage:
            p = replace(p, attributes={**p.attributes, 'BoardRegion': 'stage_optical',
                                      'Island': 'IO_STAGE_OPTICAL:${SHEETNAME}'})
        optical.append(p)
    result_family = replace(result_family, parts=tuple(optical))
    return replace(result_family, parts=tuple(precision_package(p, result_family.name) for p in result_family.parts))


def _tssop_retention():
    import json
    from pathlib import Path
    data = json.loads((Path(__file__).resolve().parents[3] / 'design/partition/precision-tssop-retention.json').read_text())
    return ({(r['family'], r['package_key'], r['board_region']) for r in data['packages'] if 'instances' not in r},
            [r for r in data['packages'] if 'instances' in r])


TSSOP_RETENTION, TSSOP_INSTANCE_RETENTION = _tssop_retention()
TSSOP_SPLIT_SUFFIX = '_tssop'


def base_family(name):
    """Source family of a TSSOP instance split (see split_tssop_instances)."""
    return name.split(TSSOP_SPLIT_SUFFIX, 1)[0] if TSSOP_SPLIT_SUFFIX in name else name


def tssop_groups(family_name):
    """Instance groups of one family that share the same retained packages: {clone name: (instances, entries)}."""
    entries = [e for e in TSSOP_INSTANCE_RETENTION if e['family'] == family_name]
    keys = defaultdict(list)
    for e in entries:
        for i in e['instances']:
            keys[i].append(e)
    groups = defaultdict(list)
    for i, es in keys.items():
        groups[tuple(sorted((e['package_key'], e['board_region']) for e in es))].append(i)
    out = {}
    for sig, insts in sorted(groups.items(), key=lambda kv: sorted(kv[1])):
        name = family_name + TSSOP_SPLIT_SUFFIX + ('' if len(groups) == 1 else '_' + '_'.join(sorted(insts)).lower())
        out[name] = (sorted(insts), [e for e in entries if (e['package_key'], e['board_region']) in sig])
    return out


def split_tssop_instances(families, instances, strict=True):
    # A shared hierarchical sheet carries one footprint per symbol for every
    # instance, so an instance-scoped OPA4197IPWR retention becomes a cloned
    # family (own master sheet) used only by the instances that retain the same packages.
    from design.spec.cells._builder import SHORTLIST, CATALOG, load_symbol
    record = SHORTLIST['op_precision']
    symbol = load_symbol(CATALOG[record['mpn']])
    footprint = symbol.body.split('(property "Footprint" "', 1)[1].split('"', 1)[0]
    clones = defaultdict(list)
    target = {}
    for base in families:
        for name, (insts, entries) in tssop_groups(base.name).items():
            parts = list(base.parts)
            for entry in entries:
                before = list(parts)
                parts = [replace(p, symbol=symbol.lib_id, footprint=footprint,
                                 value=record['mpn'] if p.value == 'OPA4197IDR' else p.value,
                                 attributes={**p.attributes, 'MPN': record['mpn'], 'Manufacturer': record['manufacturer'],
                                             'LCSC': record.get('lcsc', '')})
                         if (p.symbol.endswith('OPA4197IDR') and p.key.rsplit('.', 1)[0] == entry['package_key']
                             and p.attributes.get('BoardRegion') == entry['board_region']) else p for p in parts]
                if parts == before:
                    raise ValueError(f"{entry['family']}: no OPA4197IDR {entry['package_key']} in {entry['board_region']}")
            clones[base.name].append(replace(base, name=name, parts=tuple(parts)))
            target.update({i: name for i in insts})
    known = {i.name for i in instances}
    if strict and set(target) - known:
        raise ValueError(f'unknown retained instances: {sorted(set(target) - known)}')
    out_families = []
    for f in families:
        out_families.append(f)
        out_families.extend(clones.get(f.name, ()))
    out_instances = tuple(replace(i, family=target[i.name]) if i.name in target else i for i in instances)
    return tuple(out_families), out_instances


def instance_package_counts(family, instance_name):
    """Whole fitted IC packages of one instance, after any TSSOP split."""
    from collections import Counter
    g = instance_family(family, instance_name)
    return dict(sorted(Counter({p.key.rsplit('.', 1)[0]: p.symbol.split(':')[-1]
                                for p in g.parts if p.prefix == 'U' and not p.dnp}.values()).items()))


def instance_family(family, instance_name):
    """The family (base or TSSOP split) that one instance of a source family renders."""
    from scripts.schgen.core import Instance
    fs, ins = split_tssop_instances((family,), (Instance(family.name, instance_name, 1),), strict=False)
    return next(f for f in fs if f.name == ins[0].family)


def precision_package(part, family=None):
    # Adopted control-board option B (E15): precision packages outside the control
    # region move to the pin-identical SOIC-14 OPA4197IDR; the four control-board
    # packages keep TSSOP-14 OPA4197IPWR, as do the jack-board packages listed in
    # design/partition/precision-tssop-retention.json (minimal-move locality).
    if not part.symbol.endswith('OPA4197IPWR') or part.attributes.get('BoardRegion') == 'control':
        return part
    if (family, part.key.rsplit('.', 1)[0], part.attributes.get('BoardRegion')) in TSSOP_RETENTION:
        return part
    from design.spec.cells._builder import SHORTLIST, CATALOG, load_symbol
    record = SHORTLIST['op_precision_d']
    symbol = load_symbol(CATALOG[record['mpn']])
    footprint = symbol.body.split('(property "Footprint" "', 1)[1].split('"', 1)[0]
    attrs = {**part.attributes, 'MPN': record['mpn'], 'Manufacturer': record['manufacturer'],
             'LCSC': record.get('lcsc', '')}
    return replace(part, symbol=symbol.lib_id, footprint=footprint,
                   value=record['mpn'] if part.value == 'OPA4197IPWR' else part.value, attributes=attrs)


def channel_signatures(family):
    """Electrical identity independent of physical channel pin allocation."""
    signatures=[]
    for p in family.parts:
        maps=AMP_MAPS if p.symbol.endswith(('OPA4196IDR','OPA4197IPWR','OPA4197IDR')) else SCHMITT_MAPS if p.symbol.endswith('SN74HC14DR') else ()
        if not maps or p.unit>len(maps) or spare(p):continue
        # The option-B SOIC-14 OPA4197IDR is pin-identical to OPA4197IPWR.
        signatures.append((p.symbol.replace('OPA4197IDR','OPA4197IPWR'),p.attributes.get('LogicalCellKey') or p.key,
                           p.attributes.get('Role',''),tuple(p.pins[k] for k in maps[p.unit-1])))
    return sorted(signatures)
