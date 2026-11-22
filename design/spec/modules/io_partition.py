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


# An instance-scoped retention entry maps its package from OPA4197IDR (the default) or, when it names
# from_mpn "OPA4196IDR" (MC04-S5 input-buffer swap, owner 2026-11-21), from OPA4196IDR to the
# op_precision record (OPA4197IPWR, TSSOP-14). Family-level entries keep the OPA4197IDR meaning only.
TSSOP_FROM_MPN_DEFAULT = 'OPA4197IDR'
TSSOP_FROM_MPNS = ('OPA4197IDR', 'OPA4196IDR')


def validate_retention(packages):
    for r in packages:
        if r.get('from_mpn', TSSOP_FROM_MPN_DEFAULT) not in TSSOP_FROM_MPNS:
            raise ValueError(f"{r['family']} {r['package_key']}: unsupported from_mpn {r['from_mpn']!r}")
        if 'from_mpn' in r and 'instances' not in r:
            raise ValueError(f"{r['family']} {r['package_key']}: from_mpn needs an instance-scoped entry")


def _tssop_retention():
    import json
    from pathlib import Path
    data = json.loads((Path(__file__).resolve().parents[3] / 'design/partition/precision-tssop-retention.json').read_text())
    validate_retention(data['packages'])
    return ({(r['family'], r['package_key'], r['board_region']) for r in data['packages'] if 'instances' not in r},
            [r for r in data['packages'] if 'instances' in r])


TSSOP_RETENTION, TSSOP_INSTANCE_RETENTION = _tssop_retention()
TSSOP_SPLIT_SUFFIX = '_tssop'


KMOVE_SPLIT_SUFFIX = '_kmove'


def base_family(name):
    """Source family of a TSSOP instance split (see split_tssop_instances) or a K block relocation clone
    (see relocate_instances)."""
    for suffix in (TSSOP_SPLIT_SUFFIX, KMOVE_SPLIT_SUFFIX):
        if suffix in name:
            name = name.split(suffix, 1)[0]
    return name


def _k_relocation():
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[3] / 'design/partition/k-block-relocation.json'
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    validate_relocation(data['blocks'])
    return data['blocks']


def validate_relocation(blocks):
    seen = set()
    for b in blocks:
        missing = {'instance', 'family', 'ic', 'package_key', 'members'} - set(b)
        if missing:
            raise ValueError(f"K relocation {b.get('ic')}: missing {sorted(missing)}")
        if b['ic'] not in b['members']:
            raise ValueError(f"K relocation {b['ic']}: the IC is not among its members")
        if 'k_poses' in b and set(b['k_poses']) != set(b['members']):
            raise ValueError(f"K relocation {b['ic']}: k_poses do not name exactly the members")
        for ref in b['members']:
            if (b['instance'], ref) in seen:
                raise ValueError(f"K relocation: {b['instance']} {ref} named twice")
            seen.add((b['instance'], ref))


K_RELOCATION = _k_relocation()


def relocated_part(part):
    """One moved part: core region; FILTER_LEDS parts take the K-side FILTER_LEDS_K island, others IO_CORE."""
    island = part.attributes.get('Island', '')
    island = 'FILTER_LEDS_K:${SHEETNAME}' if island.startswith('FILTER_LEDS:') else 'IO_CORE:${SHEETNAME}'
    return replace(part, attributes={**part.attributes, 'BoardRegion': 'core', 'Island': island})


def relocate_instances(families, instances, blocks=None):
    """MC04-S7: move the function blocks of design/partition/k-block-relocation.json to the core region (board K)
    for their instance only. A family used by one instance is changed in place; a shared family is cloned for the
    instance (name + _kmove_<instance>), as the TSSOP retention does. Every named key must exist and render to the
    named reference, and the block must be exactly its named members, or the build fails."""
    from scripts.schgen.core import designator
    blocks = K_RELOCATION if blocks is None else blocks
    if not blocks:
        return tuple(families), tuple(instances)
    by_inst = defaultdict(list)
    for b in blocks:
        by_inst[b['instance']].append(b)
    known = {i.name for i in instances}
    if set(by_inst) - known:
        raise ValueError(f'K relocation: unknown instances {sorted(set(by_inst) - known)}')
    byname = {f.name: f for f in families}
    users = defaultdict(list)
    for i in instances:
        users[i.family].append(i.name)
    replaced, added, out_instances = {}, defaultdict(list), []
    for inst in instances:
        entries = by_inst.get(inst.name)
        if not entries:
            out_instances.append(inst)
            continue
        fam = byname[inst.family]
        keys = set()
        for b in entries:
            if base_family(fam.name) != b['family']:
                raise ValueError(f"K relocation {b['ic']}: {inst.name} renders {fam.name}, not {b['family']}")
            want = {k for ks in b['members'].values() for k in ks}
            parts = [p for p in fam.parts if p.key in want]
            if {p.key for p in parts} != want:
                raise ValueError(f"K relocation {b['ic']}: keys not in {fam.name}: {sorted(want - {p.key for p in parts})}")
            for ref, ks in b['members'].items():
                got = {designator(p, inst) for p in parts if p.key in ks}
                if got != {ref}:
                    raise ValueError(f"K relocation {b['ic']}: {ks} render {sorted(got)} in {inst.name}, not {ref}")
            stem = b['package_key']
            package = {p.key for p in fam.parts if p.key.rsplit('.', 1)[0] == stem}
            if not package or not package <= want:
                raise ValueError(f"K relocation {b['ic']}: package {stem} is not wholly among the members")
            bypass = {p.key for p in fam.parts if p.attributes.get('Decouples') == stem}
            if not bypass <= want:
                raise ValueError(f"K relocation {b['ic']}: bypass {sorted(bypass - want)} left behind")
            keys |= want
        parts = tuple(relocated_part(p) if p.key in keys else p for p in fam.parts)
        if len(users[fam.name]) == 1:
            replaced[fam.name] = replace(fam, parts=parts)
            out_instances.append(inst)
        else:
            name = f'{fam.name}{KMOVE_SPLIT_SUFFIX}_{inst.name.lower()}'
            added[fam.name].append(replace(fam, name=name, parts=parts))
            out_instances.append(replace(inst, family=name))
    out_families = []
    for f in families:
        out_families.append(replaced.get(f.name, f))
        out_families.extend(added.get(f.name, ()))
    return tuple(out_families), tuple(out_instances)


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
        # Only the entries that name these instances: two entries may share a package key for
        # different instances (MC04-S5 O4 and O5 both retain IO_EXTRA_18).
        out[name] = (sorted(insts), [e for e in entries if set(insts) & set(e['instances'])])
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
                source = entry.get('from_mpn', TSSOP_FROM_MPN_DEFAULT)
                parts = [replace(p, symbol=symbol.lib_id, footprint=footprint,
                                 value=record['mpn'] if p.value == source else p.value,
                                 attributes={**p.attributes, 'MPN': record['mpn'], 'Manufacturer': record['manufacturer'],
                                             'LCSC': record.get('lcsc', '')})
                         if (p.symbol.endswith(source) and p.key.rsplit('.', 1)[0] == entry['package_key']
                             and p.attributes.get('BoardRegion') == entry['board_region']) else p for p in parts]
                if parts == before:
                    raise ValueError(f"{entry['family']}: no {source} {entry['package_key']} in {entry['board_region']}")
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
