"""Reproduce the exact white-pad jack draft and check fresh native authority.

This admits only a geometrical/native prerequisite. Old electrical matrices
stay tied to the old board and are not rebound by this receipt.
"""
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

from scripts.pcbgen.generate_power_candidate import generate
from scripts.pcbgen.refresh_white_land import refresh
from scripts.pcbgen.source_contact_inventory import expected_contacts, reconcile_native
from scripts.pcbgen.netlist import TOKEN, parse, many, read_netlist

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def schematic_tree(root, allowed):
    result=[];seen=set();pending=[root]
    while pending:
        path=pending.pop()
        if path in seen:raise ValueError('duplicate or cyclic jack schematic sheet')
        seen.add(path);result.append(path)
        tokens=TOKEN.findall(path.read_text())
        node,end=parse(tokens)
        if end!=len(tokens) or node[0]!='kicad_sch':
            raise ValueError('malformed jack schematic sheet')
        for sheet in many(node,'sheet'):
            props=[p[2] for p in many(sheet,'property') if p[1]=='Sheetfile']
            if len(props)!=1:raise ValueError('jack schematic child lacks one Sheetfile')
            child=Path(os.path.normpath(str(path.parent/props[0])))
            if not child.is_relative_to(allowed):
                raise ValueError('jack schematic child escapes owner directory')
            pending.append(child)
    return result


def verify(side):
    if side not in ('left', 'right'):
        raise ValueError('one exact jack half required')
    bid = 'osc-jack-' + side
    owner = ROOT/'boards'/bid
    old_stem = bid + '-parallel-feeds'
    new_stem = bid + '-white-current-v1'
    old = owner/(old_stem+'.kicad_pcb')
    new = owner/(new_stem+'.kicad_pcb')
    cache = ROOT/'.circuit-cache/issue38-recovery/white-current-boards'/bid
    old_cache = ROOT/'.circuit-cache/issue38-recovery'/('surface140' if side=='left' else 'right-surface140')
    prior = old_cache/'parallel-native-receipt.json'
    proposal = ROOT/'design/partition/rail-plane-proposals.json'
    definition = ROOT/'design/partition/jack-white-current'/(bid+'.json')
    historical_definition=old_cache/'source-replay-definition'/(bid+'.json')
    historical_rule=historical_definition.with_suffix('.kicad_dru')
    historical_geometry=old_cache/'parallel-geometry.json'
    partition = ROOT/'design/partition/partition.json'
    io_path = ROOT/'design/reports/io-partition.json'
    spec_path = ROOT/'design/mechanical/kingbright-white-land.json'
    canonical = ROOT/'design/boards'/(bid+'.json')
    canonical_data=canonical.read_bytes()
    source = json.loads(canonical_data)
    source_root = ROOT/source['schematic']
    netlist = ROOT/source['netlist']
    if source_root != ROOT/'schematic/boards'/(bid+'.kicad_sch') or netlist != ROOT/'schematic/boards'/(bid+'.net'):
        raise ValueError('canonical jack schematic/netlist source differs')
    components,_ = read_netlist(netlist)
    canonical_tree=schematic_tree(source_root,owner)
    owner_tree=schematic_tree(new.with_suffix('.kicad_sch'),owner)
    sheets=sorted(set(canonical_tree[1:]))
    if set(owner_tree[1:])!=set(sheets):
        raise ValueError('current jack companion schematic child hierarchy differs')
    relocated=source_root.read_text().replace('../../boards/'+bid+'/sheets/','sheets/')
    if relocated!=new.with_suffix('.kicad_sch').read_text():
        raise ValueError('current jack schematic root differs from exact source relocation')
    net_sheets={owner/dict(component.fields)['Sheetfile'] for component in components}
    if not net_sheets.issubset(set(sheets)):
        raise ValueError('jack netlist references a sheet outside canonical hierarchy')
    schematic_manifest=ROOT/'design/partition/jack-white-current/schematic-source-sha256.json'
    pinned_data=schematic_manifest.read_bytes()
    pinned=json.loads(pinned_data)
    expected_schematic={str(path.relative_to(ROOT)):sha(path) for path in (source_root,netlist,*sheets)}
    if pinned.get(bid)!=expected_schematic:
        raise ValueError('canonical jack schematic/netlist source differs from frozen source manifest')
    drc_path = cache/'native-drc.json'
    geometry_path=cache/'native-geometry.json'
    inputs=[old,old.with_suffix('.kicad_pro'),old.with_suffix('.kicad_sch'),old.with_suffix('.kicad_dru'),prior,
            historical_definition,historical_rule,historical_geometry,
            new,new.with_suffix('.kicad_pro'),new.with_suffix('.kicad_sch'),new.with_suffix('.kicad_dru'),
            proposal,canonical,definition,definition.with_suffix('.kicad_dru'),partition,io_path,spec_path,
            ROOT/'footprints/kicad/zudo-osc-hole-field.pretty/LED0402-Kingbright-White.kicad_mod',
            ROOT/'scripts/pcbgen/refresh_white_land.py',ROOT/'scripts/libgen/gen_kingbright_land.py',
            ROOT/'scripts/pcbgen/generate_power_candidate.py',ROOT/'scripts/pcbgen/source_contact_inventory.py',
            ROOT/'scripts/pcbgen/extract_power_geometry.py',ROOT/'scripts/pcbgen/jack_white_current_binding.py',
            ROOT/'scripts/pcbgen/netlist.py',schematic_manifest,source_root,netlist,*sheets,drc_path,geometry_path]
    spec_data=spec_path.read_bytes()
    spec = json.loads(spec_data)
    original = ROOT/spec['original_footprint']
    inputs.append(original)
    initial={str(path.relative_to(ROOT)):sha(path) for path in inputs}
    if initial[str(canonical.relative_to(ROOT))]!=hashlib.sha256(canonical_data).hexdigest():
        raise ValueError('canonical jack board source changed during verification')
    if (initial[str(schematic_manifest.relative_to(ROOT))]!=hashlib.sha256(pinned_data).hexdigest()
        or initial[str(spec_path.relative_to(ROOT))]!=hashlib.sha256(spec_data).hexdigest()):
        raise ValueError('jack source manifest/spec changed during verification')
    prior_report = json.loads(prior.read_bytes())
    for name in prior_report['artifact_sha256']:
        path=ROOT/name.removeprefix('/work/')
        initial[str(path.relative_to(ROOT))]=sha(path)
    if (prior_report['board_id'] != bid or prior_report['board_sha256'] != sha(old)
        or not prior_report['status'].startswith('PASS')
        or prior_report['rule_errors'] or prior_report['parity_issues']
        or prior_report['open_AGND_pads'] or not prior_report['all_prior_copper_and_owner_state_preserved']):
        raise ValueError('historical parallel-feed source board differs')
    if any(sha(ROOT/name.removeprefix('/work/')) != want for name,want in prior_report['artifact_sha256'].items()):
        raise ValueError('historical parallel-feed native artifacts differ')
    with tempfile.TemporaryDirectory(prefix='jack-white-definition-') as folder:
        generated = Path(folder)/(bid+'.json')
        generate(bid,proposal,'surface-rails-140um-ground',generated)
        if generated.read_bytes()!=definition.read_bytes() or generated.with_suffix('.kicad_dru').read_bytes()!=definition.with_suffix('.kicad_dru').read_bytes():
            raise ValueError('portable source definition/rules differ from regeneration')
    if (sha(definition)!=prior_report['input_source_sha256'][str(historical_definition.relative_to(ROOT))]
        or sha(historical_definition)!=sha(definition)
        or sha(historical_rule)!=sha(definition.with_suffix('.kicad_dru'))):
        raise ValueError('portable source definition differs from historical native epoch')
    older=json.loads(historical_geometry.read_bytes())
    if (older['board_sha256']!=sha(old) or older['definition_sha256']!=sha(definition)
        or older['project_sha256']!=sha(old.with_suffix('.kicad_pro'))):
        raise ValueError('historical native geometry/source binding differs')
    part = json.loads(partition.read_bytes())
    io = json.loads(io_path.read_bytes())
    expected_text, pad_receipt = refresh(old.read_text(),bid,part,io,spec,original.read_bytes())
    if new.read_text()!=expected_text or pad_receipt['after_sha256']!=sha(new):
        raise ValueError('current white native board differs from exact source pad revision')
    companions={}
    for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru'):
        previous = owner/(old_stem+suffix)
        current = owner/(new_stem+suffix)
        expected=previous.read_bytes()
        if suffix=='.kicad_pro':
            project=json.loads(expected)
            if project['meta']['filename']!=old_stem+suffix:raise ValueError('historical project name differs')
            project['meta']['filename']=new_stem+suffix
            expected=(json.dumps(project,indent=2)+'\n').encode()
        if current.read_bytes()!=expected:raise ValueError('white current companion differs from source')
        companions[str(current.relative_to(ROOT))]=sha(current)
    drc=json.loads(drc_path.read_bytes())
    if drc['source']!=new.name or drc['kicad_version']!='10.0.6' or drc['schematic_parity'] or any(v['severity']=='error' for v in drc['violations']):
        raise ValueError('fresh white board native DRC/parity differs')
    native=json.loads(geometry_path.read_bytes())
    if native.get('extractor_sha256') != sha(ROOT/'scripts/pcbgen/extract_power_geometry.py'):
        raise ValueError('fresh white native geometry exporter differs')
    if native['board_id']!=bid or native['kicad_version']!='10.0.6' or native['board_sha256']!=sha(new) or native['definition_sha256']!=sha(definition) or native['project_sha256']!=sha(new.with_suffix('.kicad_pro')):
        raise ValueError('fresh white native geometry/source binding differs')
    board=next(b for b in part['boards'] if b['id']==bid)
    fitted={row['ref'] for row in part['assignment']['components'] if row['board']==board['board_key'] and row['fitted']}
    expected=expected_contacts(bid,part,io,{'AGND'})
    actual=reconcile_native(native,expected,fitted,{'AGND'})
    selected=set(native['main_rail_members']['AGND'])
    all_ground=[row for row in native['items'] if row.get('ref') and row['net']=='AGND']
    if (len(actual)!=(1070 if side=='left' else 896)
        or len(all_ground)!=(1177 if side=='left' else 1005)
        or any(row['uuid'] not in selected for row in all_ground)):
        raise ValueError('fresh white native fitted AGND component incomplete')
    for name,want in initial.items():
        if sha(ROOT/name)!=want:
            raise ValueError('jack source/native input changed during verification: '+name)
    for name,want in pinned[bid].items():
        if sha(ROOT/name)!=want:
            raise ValueError('canonical jack schematic/netlist changed from frozen source manifest: '+name)
    if relocated!=new.with_suffix('.kicad_sch').read_text():
        raise ValueError('current jack schematic root changed after source relocation check')
    hashes=initial
    return {'status':'PASS current native jack geometry prerequisite only; electrical/contact/material/common acceptance OPEN',
            'board_id':bid,'board_sha256':sha(new),'native_export_sha256':sha(geometry_path),
            'source_white_pad_revision':pad_receipt,'source_sha256':hashes,
            'companion_sha256':companions,'rule_error_count':0,'schematic_parity_count':0,
            'own_AGND_connected_count':len(actual),'all_source_AGND_connected_count':len(all_ground),
            'native_warning_count':sum(v['severity']=='warning' for v in drc['violations']),
            'scope':'Historical native/model receipts remain historical. This exact source-derived white-pad board requires new numerical and full physical proof.'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('side',choices=('left','right'))
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('fresh receipt path required')
    report=verify(args.side)
    with args.output.open('x') as handle:json.dump(report,handle,indent=2,sort_keys=True);handle.write('\n')
    print(report['board_id'],report['all_source_AGND_connected_count'],report['status'])
