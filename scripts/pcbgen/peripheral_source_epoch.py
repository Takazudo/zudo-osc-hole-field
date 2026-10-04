"""Prove named source-only transitions without rebinding native/model evidence."""
import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from scripts.libgen.gen_ic_package_envelopes import owned_model_span
from scripts.pcbgen.generate_peripheral_ground import generate
from scripts.checks.io_partition60 import power_requirements, repacking_metadata
from scripts.pcbgen.netlist import TOKEN, many, one, parse, read_netlist

BASE = Path('design/partition/peripheral-ground-feasibility')
PRIOR = Path('design/partition/peripheral-source-epoch-20261001.json')
DISPLAY_EPOCH = Path('design/partition/peripheral-source-epoch-20261002.json')
POWER_EPOCH = Path('design/partition/peripheral-source-epoch-20261002-power-metadata.json')
ROUTING_EPOCH = Path('design/partition/peripheral-source-epoch-20261002-octave-routing.json')
IDENTITY_EPOCH = Path('design/partition/peripheral-source-epoch-20261002-feedback-identities.json')
CONNECTOR_EPOCH = Path('design/partition/peripheral-source-epoch-20261002-connector-locality.json')
OUTPUT = Path('design/partition/peripheral-source-epoch-20261003-stage-optical-layout.json')
CONNECTOR_BASE = '141b508e89030e8465bf750147d529426c60b91f'
CONNECTOR_SOURCE = Path('design/partition/control-connector-locality.json')
JACK_BASE = 'eecfdaf60db38d5f42b85ffb3d3fdd07403fc27f'
CORE_BASE = 'bb82340375312fee50af5735116ab7871061b4cf'
PARTITION = 'design/partition/partition.json'
IDENTITY_BASE = '8d2940ac7f6fde3d2a466e4e21c45d4f232fdad1'
IDENTITIES = Path('design/standard/precision-feedback-bindings.json')
ROUTING_BASE = 'b8795bfbceaeb13e8e3f6d29d9ef57729299fd68'
ROUTING = 'design/partition/octave-routing.json'
STAGE_LAYOUT_BASE = '34de88e3c2bac915bbdfbb5458194328be167e62'
STAGE_ROUTING = 'design/partition/stage-optical-routing.json'
COMMIT = 'fa11636b860ef80c01cb42bc7450551db556c72e'
METADATA_BASE = '38153f8d51db8852ab87e00aa94039f7981dc937'
IO = 'design/reports/io-partition.json'
FP = 'footprints/kicad/zudo-osc-hole-field.pretty/DIP-8_W7.62mm.kicad_mod'
MODEL = 'IC_DIP-8_W7.62mm.wrl'
CONTRACT = 'design/power/supply-architecture-input.json'
SUPPLY = 'design/power/supply-architecture.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def historical(path, commit=COMMIT):
    return subprocess.check_output(['git', 'show', f'{commit}:{path}'])


def prove_display_only(old_io, new_io, old_fp, new_fp):
    """Require byte-identical 2D footprint and a single report hash substitution."""
    geometries = []
    for raw in (old_fp, new_fp):
        text = raw.decode()
        start, end = owned_model_span(text, MODEL)
        geometries.append(text[:start] + text[end:])
    if geometries[0] != geometries[1]:
        raise ValueError('2D footprint geometry changed')
    old, new = json.loads(old_io), json.loads(new_io)
    expected = copy.deepcopy(old)
    matches = [r for r in expected['physical_packages'] if r['ref'] == 'U6101']
    if len(matches) != 1:
        raise ValueError('expected exactly one U6101 package')
    row = matches[0]
    if row['mpn'] != 'NOISE2' or row['footprint'] != 'zudo-osc-hole-field:DIP-8_W7.62mm':
        raise ValueError('unexpected U6101 identity')
    if row['courtyard']['footprint_sha256'] != sha(old_fp):
        raise ValueError('historical footprint hash mismatch')
    row['courtyard']['footprint_sha256'] = sha(new_fp)
    if expected != new:
        raise ValueError('IO report changed beyond the U6101 display footprint hash')


def prove_power_metadata_only(old_io, new_io, contract, supply):
    """Require the exact source-driven metadata replacement; compare all else."""
    expected = json.loads(old_io)
    expected.pop('added_fitted_quads')
    expected.pop('rail_change')
    expected.update(repacking_metadata(
        {r['ref']: r for r in expected['physical_packages']}, expected['package_units']))
    power = power_requirements(contract, supply)
    for row in expected['allowed_crossings']:
        if row['net'] not in power:
            continue
        fields = power[row['net']]
        if row['capacitance_F']['whole_domain_nominal_ceiling'] != fields['capacitance_F']:
            raise ValueError('capacitance contract changed beyond metadata scope')
        row['current_mA'] = fields['current_mA']
        row['capacitance_F']['status'] = 'board count and fitted/bulk totals are owned by the current partition report'
    if expected != json.loads(new_io):
        raise ValueError('IO report changed beyond the exact power/package metadata replacement')


def prove_octave_routing_only(old_bytes, new_bytes, routing):
    old,new=json.loads(old_bytes),json.loads(new_bytes)
    if old.get('routing') is not None or old['board_id'] not in {f'osc-octave-{n}' for n in range(1,6)}:
        raise ValueError('unexpected octave routing transition base')
    if new != {**old,'routing':routing}:
        raise ValueError('octave definition changed beyond declared routing')


STAGE_LAYOUT_FIELDS = ('FootprintOriginMm', 'KiCadOrientationDeg')


def _netlist(raw):
    with tempfile.TemporaryDirectory(prefix='stage-layout-') as folder:
        path = Path(folder) / 'source.net'
        path.write_bytes(raw)
        return read_netlist(path)


def _set_layout_fields(root, changes):
    for comp in many(one(root, 'components'), 'comp'):
        fields = changes.get(one(comp, 'ref')[1], {})
        for entry in many(one(comp, 'fields'), 'field'):
            name = one(entry, 'name')[1]
            if name in fields:
                entry[2] = fields[name]['current']
        for prop in many(comp, 'property'):
            name = one(prop, 'name')[1]
            if name in fields:
                one(prop, 'value')[1] = fields[name]['current']
    return root


def prove_stage_optical_layout(old_definition, new_definition, old_net, new_net, routing):
    """Return the free-part layout field changes after proving nothing else moved."""
    old, new = json.loads(old_definition), json.loads(new_definition)
    if old.get('routing') is not None or old['board_id'] != 'osc-stage-optical':
        raise ValueError('unexpected stage-optical layout transition base')
    if {k: v for k, v in new.items() if k != 'regions'} != {**{k: v for k, v in old.items() if k != 'regions'}, 'routing': routing}:
        raise ValueError('stage-optical definition changed beyond declared routing and regions')
    shape = lambda rows: [{k: v for k, v in r.items() if k != 'rect'} for r in rows]
    if shape(old['regions']) != shape(new['regions']):
        raise ValueError('stage-optical regions changed beyond rectangles')
    old_parts, old_pins = _netlist(old_net)
    new_parts, new_pins = _netlist(new_net)
    if old_pins != new_pins:
        raise ValueError('stage-optical netlist connectivity changed')
    olds, news = {c.ref: c for c in old_parts}, {c.ref: c for c in new_parts}
    if set(olds) != set(news):
        raise ValueError('stage-optical netlist package set changed')
    changes = {}
    for ref in sorted(olds):
        a, b = olds[ref], news[ref]
        fa, fb = dict(a.fields), dict(b.fields)
        if (a.value, a.footprint, a.sheetname, a.sheet_ts, a.symbol_ts) != (b.value, b.footprint, b.sheetname, b.sheet_ts, b.symbol_ts) or set(fa) != set(fb):
            raise ValueError('stage-optical netlist identity changed: ' + ref)
        diff = {k: {'historical': fa[k], 'current': fb[k]} for k in sorted(fa) if fa[k] != fb[k]}
        if not diff:
            continue
        if set(diff) - set(STAGE_LAYOUT_FIELDS) or fa.get('PanelUid'):
            raise ValueError('stage-optical netlist changed beyond free-part layout fields: ' + ref)
        changes[ref] = diff
    if not changes:
        raise ValueError('stage-optical layout transition declares no change')
    old_root, _ = parse(TOKEN.findall(old_net.decode()))
    new_root, _ = parse(TOKEN.findall(new_net.decode()))
    _set_layout_fields(old_root, changes)
    # Routing may also declare the KiCad net class of rail and ground nets.
    classes = {net: spec['name'] for spec in routing['net_classes'] for net in spec['nets']}
    for net in many(one(new_root, 'nets'), 'net'):
        if one(net, 'class')[1] not in ('Default', classes.get(one(net, 'name')[1], 'Default')):
            raise ValueError('stage-optical netlist net class differs from declared routing')
    for old_entry, new_entry in zip(many(one(old_root, 'nets'), 'net'), many(one(new_root, 'nets'), 'net')):
        one(old_entry, 'class')[1] = one(new_entry, 'class')[1]
    if old_root != new_root:
        raise ValueError('stage-optical netlist text changed beyond free-part layout fields')
    return changes


def prove_octave_netclass_only(old_bytes, new_bytes):
    old_class = b'(name "AGND")\n\t\t\t(class "Default")'
    new_class = b'(name "AGND")\n\t\t\t(class "Ground")'
    if old_bytes.count(old_class) != 1 or new_bytes != old_bytes.replace(old_class, new_class, 1):
        raise ValueError('octave netlist changed beyond the AGND class declaration')


def prove_feedback_identity_only(old_bytes, new_bytes, contract):
    """Compare the entire IO report after 32 explicitly named substitutions."""
    if contract['schema_version'] != 1 or contract['base_commit'] != IDENTITY_BASE:
        raise ValueError('Unexpected feedback identity transition base')
    expected, current = json.loads(old_bytes), json.loads(new_bytes)
    if expected['native_netlist']['sha256'] != contract['old_native_netlist_sha256']:
        raise ValueError('Feedback identity base netlist hash differs')
    expected['native_netlist']['sha256'] = contract['new_native_netlist_sha256']
    packages = {row['ref']:row for row in expected['physical_packages']}
    if len(packages) != len(expected['physical_packages']):
        raise ValueError('Duplicate source package identity')
    changes = contract['packages']
    if len(changes) != 32 or len({row['ref'] for row in changes}) != 32:
        raise ValueError('Exactly 32 unique feedback package substitutions required')
    allowed = {'RC0603FR-07100KL':'RC0603FR-07100RL',
               'C0603C101J5GACTU':'C0603C102J5GACTU'}
    counts = {key:0 for key in allowed}
    for change in changes:
        old = change['old_symbol']
        if old not in allowed or change['new_symbol'] != allowed[old] or change['new_mpn'] != allowed[old]:
            raise ValueError('Unexpected exact feedback substitution')
        row = packages[change['ref']]
        if (row['instance'] != change['instance'] or row['symbol'] != old or
                row['mpn'] != '' or row['dnp']):
            raise ValueError('Feedback substitution does not match its original fitted package')
        row['symbol'] = change['new_symbol']
        row['mpn'] = change['new_mpn']
        counts[old] += 1
    if set(counts.values()) != {16} or expected != current:
        raise ValueError('IO report changed beyond the exact feedback identities/netlist hash')


def derive():
    from scripts.checks.control_connector_locality import prove_partition_transition
    from scripts.checks.jack_locality import prove_jack_locality_transition
    from scripts.checks.core_locality import prove_core_locality_transition,without_core_locality
    identity_epoch = IDENTITY_EPOCH.read_bytes()
    if identity_epoch != historical(str(IDENTITY_EPOCH), CONNECTOR_BASE):
        raise ValueError('Historical feedback identity epoch was modified')
    connector_source = CONNECTOR_SOURCE.read_bytes()
    old_partition = historical(PARTITION, CONNECTOR_BASE)
    jack_base_partition = historical(PARTITION, JACK_BASE)
    core_base_partition = historical(PARTITION, CORE_BASE)
    new_partition = Path(PARTITION).read_bytes()
    prove_partition_transition(json.loads(old_partition), json.loads(jack_base_partition),
                               json.loads(connector_source))
    pre_core = without_core_locality(json.loads(new_partition), json.loads(core_base_partition))
    pre_core_partition = (json.dumps(pre_core, indent=2) + '\n').encode()
    prove_jack_locality_transition(json.loads(jack_base_partition), pre_core)
    prove_core_locality_transition(pre_core, json.loads(new_partition))
    routing_epoch = ROUTING_EPOCH.read_bytes()
    if routing_epoch != historical(str(ROUTING_EPOCH), IDENTITY_BASE):
        raise ValueError('Historical routing epoch was modified')
    identity_bytes = IDENTITIES.read_bytes()
    power_bytes=POWER_EPOCH.read_bytes()
    if power_bytes != historical(str(POWER_EPOCH),ROUTING_BASE):
        raise ValueError('historical power metadata epoch was modified')
    routing_bytes=Path(ROUTING).read_bytes()
    prior_bytes = PRIOR.read_bytes()
    if prior_bytes != historical(str(PRIOR)):
        raise ValueError('historical epoch was modified')
    display_bytes = DISPLAY_EPOCH.read_bytes()
    if display_bytes != historical(str(DISPLAY_EPOCH), METADATA_BASE):
        raise ValueError('historical display epoch was modified')
    display = json.loads(display_bytes)
    if display['prior_epoch'] != {'path': str(PRIOR), 'sha256': sha(prior_bytes)}:
        raise ValueError('display epoch prior binding changed')
    old_io, display_io, new_io = historical(IO), historical(IO, METADATA_BASE), Path(IO).read_bytes()
    old_fp, display_fp, new_fp = historical(FP), historical(FP, METADATA_BASE), Path(FP).read_bytes()
    prove_display_only(old_io, display_io, old_fp, display_fp)
    if new_fp != display_fp:
        raise ValueError('footprint changed after the display epoch')
    inputs = {p: Path(p).read_bytes() for p in (CONTRACT, SUPPLY)}
    if any(raw != historical(p, METADATA_BASE) for p, raw in inputs.items()):
        raise ValueError('supply source changed beyond this metadata-only transition')
    identity_base_io = historical(IO, IDENTITY_BASE)
    prove_power_metadata_only(display_io, identity_base_io, json.loads(inputs[CONTRACT]), json.loads(inputs[SUPPLY]))
    prove_feedback_identity_only(identity_base_io, new_io, json.loads(identity_bytes))
    result = copy.deepcopy(display)
    result['scope'] = ('Exact source projection equivalence through the retained power metadata epoch '
        'plus declared routing-only additions, AGND net-class declarations, and 32 exact feedback '
        'package identity substitutions on the jack boards. '
        'Their geometry, stack proposal and source pins are unchanged. The disposable ground '
        'generator replaces routing, so its output definition remains identical. '
        'The later K/P pair permutation changes no EL or octave source geometry or contacts. '
        'Historical native/model prerequisites remain stale; actual octave PCB checks are separate.')
    # The connector-locality epoch stays byte-stable; other proofs bind its hash.
    connector_epoch = CONNECTOR_EPOCH.read_bytes()
    if connector_epoch != historical(str(CONNECTOR_EPOCH), STAGE_LAYOUT_BASE):
        raise ValueError('Historical connector-locality epoch was modified')
    result['prior_epoch'] = {'path': str(CONNECTOR_EPOCH), 'sha256': sha(connector_epoch)}
    result['connector_locality_transition'] = {'base_commit':CONNECTOR_BASE,
        'proposal':str(CONNECTOR_SOURCE),'proposal_sha256':sha(connector_source),
        'historical_partition_sha256':sha(old_partition),'current_partition_sha256':sha(jack_base_partition),
        'scope':'Whole partition equality after only the declared K/P header-pair and service-aperture permutation. EL and octave source geometry/contacts unchanged. No native/model rebinding.'}
    result['jack_locality_transition'] = {'base_commit':JACK_BASE,
        'base_partition_sha256':sha(jack_base_partition),'current_partition_sha256':sha(pre_core_partition),
        'scope':'Whole partition equality except jack-half package faces, jack bypass distances and the six-layer jack stack (owner decision 2026-10-03). EL and octave source geometry/contacts unchanged. No native/model rebinding.'}
    result['core_locality_transition'] = {'base_commit':CORE_BASE,
        'base_partition_sha256':sha(pre_core_partition),'current_partition_sha256':sha(new_partition),
        'base':'current partition with core package faces and layer stack restored from base_commit',
        'scope':'Whole partition equality except core package faces and the core layer stack (#43). EL and octave source geometry/contacts unchanged. No native/model rebinding.'}
    result['feedback_identity_transition'] = {'base_commit':IDENTITY_BASE,
        'contract':str(IDENTITIES),'sha256':sha(identity_bytes),'package_count':32,
        'scope':'Complete IO report equality except the 32 named symbol/MPN pairs and bound native-netlist hash; no native/model rebinding'}
    result['routing_transition']={'base_commit':ROUTING_BASE,'source':ROUTING,'sha256':sha(routing_bytes),
        'scope':'Canonical routing-only proposal; no native/model evidence rebinding'}
    stage_routing_bytes=Path(STAGE_ROUTING).read_bytes()
    result['stage_optical_layout_transition']={'base_commit':STAGE_LAYOUT_BASE,'routing_source':STAGE_ROUTING,
        'routing_sha256':sha(stage_routing_bytes),
        'scope':('Draft routing classes and AGND pours plus moved free (non-panel) stage-optical part origins and angles. '
                 'Panel hardware, connectivity, identities and all other source geometry are unchanged; '
                 'no native/model evidence rebinding')}
    result['metadata_comparison'] = {'commit': METADATA_BASE, 'report': IO,
        'historical_report_sha256': sha(display_io), 'current_report_sha256': sha(new_io),
        'unchanged_supply_sources': {p: sha(raw) for p, raw in inputs.items()}}
    with tempfile.TemporaryDirectory() as folder:
        for row in result['boards']:
            bid = row['board_id']
            raw = (BASE / (bid + '.receipt.json')).read_bytes()
            if sha(raw) != row['historical_receipt_sha256']:
                raise ValueError(f'{bid}: historical receipt changed')
            expected = json.loads(raw)
            if expected['source_sha256'][IO] != sha(old_io):
                raise ValueError(f'{bid}: historical IO report mismatch')
            if row['source_changes'][IO] != {'historical': sha(old_io), 'current': sha(display_io)}:
                raise ValueError(f'{bid}: display epoch IO binding changed')
            row['source_changes'][IO] = {'historical': sha(old_io), 'current': sha(new_io)}
            if bid.startswith('osc-octave-'):
                path=f'design/boards/{bid}.json'
                old_definition=historical(path,ROUTING_BASE)
                new_definition=Path(path).read_bytes()
                prove_octave_routing_only(old_definition,new_definition,json.loads(routing_bytes))
                row['source_changes'][path]={'historical':sha(old_definition),'current':sha(new_definition)}
                net_path=f'schematic/boards/{bid}.net'
                old_net=historical(net_path,ROUTING_BASE)
                new_net=Path(net_path).read_bytes()
                prove_octave_netclass_only(old_net,new_net)
                row['source_changes'][net_path]={'historical':sha(old_net),'current':sha(new_net)}
            if bid == 'osc-stage-optical':
                path=f'design/boards/{bid}.json'
                net_path=f'schematic/boards/{bid}.net'
                old_definition=historical(path,STAGE_LAYOUT_BASE)
                new_definition=Path(path).read_bytes()
                old_net=historical(net_path,STAGE_LAYOUT_BASE)
                new_net=Path(net_path).read_bytes()
                layout=prove_stage_optical_layout(old_definition,new_definition,old_net,new_net,json.loads(stage_routing_bytes))
                row['source_changes'][path]={'historical':sha(old_definition),'current':sha(new_definition)}
                row['source_changes'][net_path]={'historical':sha(old_net),'current':sha(new_net)}
                row['layout_field_changes']=layout
                for package in expected['source_packages']:
                    for field,change in layout.get(package['ref'],{}).items():
                        if package['source_fields'][field]!=change['historical']:
                            raise ValueError(f'{bid}: historical layout field mismatch')
                        package['source_fields'][field]=change['current']
            if row['source_changes'][PARTITION]['current'] != sha(old_partition):
                raise ValueError(f'{bid}: connector transition partition base differs')
            row['source_changes'][PARTITION]['current'] = sha(new_partition)
            for path, change in row['source_changes'].items():
                if expected['source_sha256'][path] != change['historical'] or sha(Path(path).read_bytes()) != change['current']:
                    raise ValueError(f'{bid}: source hash mismatch: {path}')
                expected['source_sha256'][path] = change['current']
            target = Path(folder) / (bid + '.json')
            actual = generate(BASE / 'proposal.json', bid, target)
            if bid == 'osc-stage-optical':
                # The generated definition may differ from the historical one only by regions.
                generated=json.loads(target.read_bytes());generated['regions']=json.loads(old_definition)['regions']
                if sha((json.dumps(generated,indent=2,sort_keys=True)+'\n').encode()) != row['unchanged_definition_sha256']:
                    raise ValueError(f'{bid}: generated definition changed beyond regions')
                expected['definition_sha256']=row['current_definition_sha256']=actual['definition_sha256']
            if actual != expected or actual['model_entry_allowed']:
                raise ValueError(f'{bid}: source projection differs or model admitted')
            if actual['definition_sha256'] != row.get('current_definition_sha256',row['unchanged_definition_sha256']):
                raise ValueError(f'{bid}: definition changed')
            row['current_source_receipt_sha256'] = sha(target.with_suffix('.receipt.json').read_bytes())
    result['latest_source_audit'] = ('Source projection only; exact historical receipt equality '
        'except the explicitly named metadata, canonical routing and K/P-only partition source hashes. '
        'No native/model receipt rebind or electrical acceptance.')
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = (json.dumps(derive(), indent=2) + '\n').encode()
    if args.check:
        if OUTPUT.read_bytes() != data:
            raise SystemExit('FAIL: stale peripheral source equivalence epoch')
    else:
        OUTPUT.write_bytes(data)
