"""Rebuild the unrouted P layout in disposable storage and compare every byte.

Native checks cover current placement, annotation and rules, not connected
copper or physical qualification. No routing or fabrication export is run.
"""
import hashlib
import json
import copy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.generate_control_ground_feasibility import generate
from scripts.pcbgen.build_control_ground_bare import build
from scripts.pcbgen.control_reference_layout import apply
from scripts.pcbgen.control_project_source import derive
from scripts.pcbgen.octave_project import expected_configuration, TEMPLATE
from scripts.pcbgen.ratsnest import inspect
from scripts.pcbgen.control_bypass_geometry import audit as audit_bypasses, reject_displaced_capacitor

FOLDER = ROOT/'boards/osc-control'
SOURCE = ROOT/'design/partition/control-layout'
PROPOSAL = ROOT/'design/partition/control-ground-feasibility/proposal.json'
STEM = 'osc-control-layout'


@contextmanager
def workspace():
    (ROOT/'.circuit-cache').mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix='control-layout-', dir=ROOT/'.circuit-cache'))
    try:
        yield path
    except Exception:
        print('Failed native evidence retained at', path, flush=True)
        raise
    else:
        shutil.rmtree(path)


def project_bytes(bare, definition):
    raw, _ = derive(bare, definition, STEM+'.kicad_pro')
    project = json.loads(raw)
    project['board']['design_settings']['rules']['min_track_width'] = json.loads(definition)['routing']['min_track_width_mm']
    design, nets = expected_configuration((ROOT/TEMPLATE).read_bytes(), json.loads(definition)['routing'])
    nets['classes'].sort(key=lambda row: row['name'])
    if project['board']['design_settings'] != design or project['net_settings'] != nets:
        raise ValueError('Control project differs from the pinned complete rules/classes baseline')
    return (json.dumps(project, indent=2, sort_keys=True)+'\n').encode()


def negative_controls(bare, work):
    original = json.loads((SOURCE/'reference-positions.json').read_bytes())
    cases = []
    bad = copy.deepcopy(original)
    bad['references'].pop('C107')
    cases.append(('missing-reference', bad, bare, '418'))
    bad = copy.deepcopy(original)
    bad['references']['C107']['x_mm'] = float('nan')
    cases.append(('nonfinite', bad, bare, 'Finite'))
    bad = copy.deepcopy(original)
    bad['references']['C107'] = {'x_mm': 128, 'y_mm': 274, 'rotation_deg': 0}
    cases.append(('over-component', bad, bare, 'intersects'))
    changed = work/'changed-bare.kicad_pcb'
    changed.write_bytes(bare.read_bytes()+b'\n')
    cases.append(('changed-input', original, changed, 'Bare board differs'))
    for name, policy, board, expected in cases:
        path = work/(name+'.json')
        path.write_text(json.dumps(policy))
        output = work/(name+'.kicad_pcb')
        try:
            apply(board, path, output)
        except ValueError as error:
            if expected not in str(error):
                raise AssertionError('Wrong rejection for '+name) from error
        else:
            raise AssertionError('Invalid reference layout accepted: '+name)
        if output.exists():
            raise AssertionError('Rejected annotation wrote an output: '+name)
    print('PASS: four native reference rejection controls; rejected outputs absent', flush=True)


def check():
    digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    paths = [Path(__file__), ROOT/'scripts/pcbgen/control_reference_layout.py',
             ROOT/'scripts/pcbgen/control_bypass_geometry.py', ROOT/'design/reports/io-partition.json',
             ROOT/'scripts/pcbgen/control_project_source.py', SOURCE/'reference-positions.json',
             ROOT/'scripts/pcbgen/octave_project.py', ROOT/TEMPLATE]
    paths += [FOLDER/(STEM+suffix) for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch', '.kicad_dru')]
    paths += [SOURCE/('osc-control'+suffix) for suffix in ('.json', '.receipt.json', '.kicad_dru')]
    paths += list((FOLDER/'sheets').rglob('*.kicad_sch'))
    tables = [FOLDER/name for name in ('fp-lib-table', 'sym-lib-table') if (FOLDER/name).exists()]
    paths += tables
    before = {str(path): digest(path) for path in paths}
    with workspace() as work:
        definition = work/'definition/osc-control.json'
        generate(PROPOSAL, definition)
        for suffix in ('.json', '.receipt.json', '.kicad_dru'):
            if definition.with_suffix(suffix).read_bytes() != (SOURCE/('osc-control'+suffix)).read_bytes():
                raise ValueError('Control layout definition or source receipt drift: '+suffix)
        # Sheetfile paths are relative to each root schematic. The entire
        # generated hierarchy is needed for native parity, not just used pages.
        shutil.copytree(FOLDER/'sheets', work/'sheets')
        for table in tables:
            shutil.copyfile(table, work/table.name)
        bare = work/'osc-control-layout-bare.kicad_pcb'
        build(PROPOSAL, definition, bare, work/'bare-evidence')
        dependencies = json.loads((work/'bare-evidence/bare-native-receipt.json').read_bytes())['source_sha256']
        output = work/(STEM+'.kicad_pcb')
        annotation = apply(bare, SOURCE/'reference-positions.json', output)
        negative_controls(bare, work)
        output.with_suffix('.kicad_pro').write_bytes(project_bytes(
            bare.with_suffix('.kicad_pro').read_bytes(), definition.read_bytes()))
        for suffix in ('.kicad_sch', '.kicad_dru'):
            shutil.copyfile(bare.with_suffix(suffix), output.with_suffix(suffix))
        for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch', '.kicad_dru'):
            if output.with_suffix(suffix).read_bytes() != (FOLDER/(STEM+suffix)).read_bytes():
                raise ValueError('Control layout differs from exact source regeneration: '+suffix)
        native_paths = [output.with_suffix(s) for s in ('.kicad_pcb', '.kicad_pro', '.kicad_sch', '.kicad_dru')]
        native_paths += list((work/'sheets').glob('*.kicad_sch'))
        native_paths += [work/table.name for table in tables]
        native_before = {str(path): digest(path) for path in native_paths}
        report = work/'final-drc.json'
        subprocess.run(['kicad-cli', 'pcb', 'drc', '--schematic-parity', '--format', 'json',
                        '--severity-all', '-o', str(report), str(output)], check=True)
        drc = json.loads(report.read_bytes())
        if drc['kicad_version'] != '10.0.6' or drc['source'] != output.name:
            raise ValueError('Wrong native oracle or source')
        if drc['violations'] or drc['schematic_parity']:
            print(json.dumps((drc['violations']+drc['schematic_parity'])[:5], indent=2), flush=True)
            raise ValueError('Control layout has native rule or parity findings')
        import pcbnew
        native_board = pcbnew.LoadBoard(str(output))
        io = json.loads((ROOT/'design/reports/io-partition.json').read_bytes())
        bypass_geometry = audit_bypasses(native_board, io)
        reject_displaced_capacitor(native_board, io)
        ratsnest = inspect(output)
        if ratsnest['native_unconnected_edges'] != 872 or ratsnest['multi_pad_candidate_net_count'] != 348:
            raise ValueError('Unrouted control connectivity inventory changed')
        if any(digest(p) != value for p, value in native_before.items()):
            raise ValueError('Native control check changed its input')
        if any(digest(p) != value for p, value in before.items()):
            raise ValueError('Control layout source/artifact changed during verification')
        if any(digest(p) != value for p, value in dependencies.items()):
            raise ValueError('Bare-layout source changed after construction')
        print(json.dumps({'status': 'PASS UNROUTED DRAFT ONLY', **annotation,
                          'native_violations': 0, 'native_parity_findings': 0,
                          'native_open_edges': 872, 'routing_complete': False,
                          'native_bypass_geometry': bypass_geometry,
                          'physical_qualification': 'NOT RUN'}, indent=2), flush=True)


if __name__ == '__main__':
    check()
