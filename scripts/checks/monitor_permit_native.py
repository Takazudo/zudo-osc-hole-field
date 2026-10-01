#!/usr/bin/env python3
"""Fresh pinned-oracle ERC and exact pin/identity checks for an isolated draft."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.schgen import generate_monitor_permit as generator
from scripts.schgen.core import children, designator, parse, tokens
from scripts.schgen.verify_netlist import verify, expected_pin_nets
from scripts.libgen import build_monitor_candidate_assets, build_symbol_lib

REPORT = ROOT/'design/power/monitor-permit-native-report.json'
ERC = ROOT/'schematic/candidates/monitor-permit/native-erc.json'
NETLIST = ROOT/'schematic/candidates/monitor-permit/native.net'


def inputs():
    families, instances, _ = generator.specification()
    paths = {generator.SPEC,ROOT/'design/power/monitor-permit-parts.json',Path(__file__).resolve(),
             ROOT/'scripts/schgen/generate_monitor_permit.py',ROOT/'scripts/schgen/core.py',
             ROOT/'scripts/schgen/verify_netlist.py',ROOT/'design/spec/cells/_builder.py',
             ROOT/'scripts/libgen/build_symbol_lib.py',ROOT/'symbols/zudo-osc-hole-field.kicad_sym',
             ROOT/'scripts/libgen/build_monitor_candidate_assets.py',ROOT/'symbols/src/RT0603BRD07100KL.kicad_sym',
             ROOT/'.claude/skills/component-spec-audit/references/inventory.json',
             ROOT/'scripts/kicad/run.sh',ROOT/'scripts/kicad/pin.env'}
    paths.update(generator.OUTPUT/name for name in generator.generated_files())
    paths.update((ROOT/'circuit/sources/monitor-permit-cad').glob('*.kicad_mod'))
    for family in families:
        for part in family.parts:
            if part.symbol.startswith('zudo-osc-hole-field:'):
                paths.add(ROOT/'symbols/src'/(part.symbol.split(':')[1]+'.kicad_sym'))
            if part.footprint:
                paths.add(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(part.footprint.split(':')[1]+'.kicad_mod'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def inspect(erc, netlist):
    families, instances, _ = generator.specification()
    # KiCad omits the nonphysical, off-board ideal supply declaration from
    # board netlist exports. It is an ERC test assumption, not an inlet.
    families = tuple(replace(f,parts=tuple(p for p in f.parts if not p.abstract)) for f in families)
    if erc.get('kicad_version') != '10.0.6' or set(erc.get('included_severities',[])) != {'error','warning'}:
        raise ValueError('required KiCad version/severity scope missing')
    if erc.get('source') != 'monitor-permit-candidate.kicad_sch':
        raise ValueError('ERC source differs from the candidate')
    expected_paths = {'/'}
    for inst in instances:
        family = next(f for f in families if f.name==inst.family)
        expected_paths.update('/'+inst.name+('' if page==1 else '-P'+str(page))+'/'
                              for page in {p.page for p in family.parts})
    if (len(erc['sheets']) != len(expected_paths)
            or {s['path'] for s in erc['sheets']} != expected_paths):
        raise ValueError('ERC sheet coverage incomplete')
    allowed_ignored = {'single_global_label','four_way_junction','simulation_model_issue','footprint_filter'}
    if {c['key'] for c in erc['ignored_checks']} != allowed_ignored:
        raise ValueError('unexpected native ERC check suppression')
    violations = [v for sheet in erc['sheets'] for v in sheet['violations']]
    if violations:
        raise ValueError('native candidate ERC violations remain')
    differences = verify(families, instances, netlist)
    if differences:
        raise ValueError('native candidate pin mismatch: '+'; '.join(differences[:8]))
    tree, _ = parse(tokens(netlist))
    if children(children(tree,'design')[0],'tool')[0][1] != 'Eeschema 10.0.6':
        raise ValueError('netlist oracle version differs')
    actual = {}
    for component in children(children(tree,'components')[0],'comp'):
        ref = children(component,'ref')[0][1]
        fields = {children(f,'name')[0][1]:f[-1] if isinstance(f[-1],str) else ''
                  for f in children(children(component,'fields')[0],'field')}
        footprint = children(component,'footprint')
        actual[ref] = (children(component,'value')[0][1], footprint[0][1] if footprint else '',
                       fields.get('MPN',''),fields.get('Manufacturer',''))
    expected = {}
    for inst in instances:
        family = next(f for f in families if f.name==inst.family)
        for p in family.parts:
            expected[designator(p,inst)] = (p.value or p.symbol.split(':')[-1],p.footprint,
                                          p.attributes.get('MPN',''),p.attributes.get('Manufacturer',''))
    if actual != expected:
        raise ValueError('native candidate value/footprint/MPN mismatch')
    return {'physical_candidate_components':len(expected),'ideal_test_source_symbols':1,
            'test_source_export_scope':'Nonphysical supply declaration omitted by KiCad; no source hardware implementation inferred.',
            'checked_physical_and_test_pins':len(expected_pin_nets(families,instances)),
            'erc_errors':0,'erc_warnings':0,'ignored_native_checks':erc['ignored_checks']}


def run(check=False):
    build_monitor_candidate_assets.generate(check=True)
    if build_symbol_lib.assemble() != (ROOT/'symbols/zudo-osc-hole-field.kicad_sym').read_bytes():
        raise ValueError('assembled symbol library is stale')
    generator.run(check=True)
    before = inputs()
    cache = ROOT/'.circuit-cache'; cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='monitor-permit-oracle-',dir=cache) as directory:
        directory = Path(directory); erc_path=directory/'erc.json'; net_path=directory/'export.net'
        source = generator.OUTPUT/'monitor-permit-candidate.kicad_sch'
        base = ['bash',str(ROOT/'scripts/kicad/run.sh'),'kicad-cli','sch']
        subprocess.run(base+['erc','--format','json','--output',str(erc_path.relative_to(ROOT)),
                            str(source.relative_to(ROOT))],cwd=ROOT,check=True)
        subprocess.run(base+['export','netlist','--format','kicadsexpr','--output',str(net_path.relative_to(ROOT)),
                            str(source.relative_to(ROOT))],cwd=ROOT,check=True)
        erc=json.loads(erc_path.read_text()); netlist=net_path.read_text()
        result=inspect(erc,netlist)
    if before != inputs():
        raise ValueError('candidate inputs changed during native checks')
    # Only volatile creation timestamps are omitted; all ERC findings and
    # exported electrical identities/connectivity remain in the snapshots.
    erc.pop('date',None)
    netlist=re.sub(r'\(date "\d{4}-\d{2}-\d{2}T[^"\n]+"\)', '(date "")',netlist,count=1)
    for prefix in ('/work/',str(ROOT)+'/'):
        netlist=netlist.replace('(source "'+prefix,'(source "')
    erc_text=json.dumps(erc,indent=2)+'\n'
    result.update(status='UNSELECTED NATIVE DRAFT; connectivity/ERC only',
        oracle='KiCad10.0.6 through scripts/kicad/run.sh',
        candidate_circuit_captured=True,canonical_protection_implemented=False,qualification_accepted=False,
        input_sha256=before,normalization='Creation timestamps omitted and known workspace source prefix made relative; fresh temporary outputs generated on every check.',
        normalized_native_sha256={'erc':hashlib.sha256(erc_text.encode()).hexdigest(),
                                  'netlist':hashlib.sha256(netlist.encode()).hexdigest()},
        physical_dynamic_qualification='NOT RUN by this native check; no circuit-performance or physical acceptance')
    outputs={ERC:erc_text,NETLIST:netlist,REPORT:json.dumps(result,indent=2)+'\n'}
    for path,text in outputs.items():
        if check:
            if not path.exists() or path.read_text()!=text:
                raise ValueError('native candidate snapshot drift: '+str(path.relative_to(ROOT)))
        else:
            path.write_text(text)
    print('PASS: fresh native ERC and all candidate pin/value/MPN checks; qualification OPEN')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    run(parser.parse_args().check)
