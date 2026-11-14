"""Fresh native verification of the partial control-board copper checkpoint."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.control_oracle_policy import configuration, runtime
from scripts.pcbgen.control_copper_draft import build, require_connected_ground_copper
from scripts.pcbgen.control_bypass_geometry import audit as audit_bypasses
from scripts.pcbgen.control_ground_inventory import audit
from scripts.pcbgen.extract_power_geometry import extract
from scripts.pcbgen.ratsnest import inspect
from scripts.pcbgen.check_control_layout import check as check_base
from scripts.pcbgen.verify_local_links import blocks
from scripts.pcbgen.uuid_tools import top_level_spans, replace_spans, UUID_RE


def independent_refill(board, definition, output):
    """Refill a fresh native load, preserving all non-zone source bytes."""
    import pcbnew
    from scripts.pcbgen.route_kicad import apply_classes
    from scripts.schgen.core import parse, tokens
    native = pcbnew.LoadBoard(str(board))
    apply_classes(native, json.loads(definition.read_bytes())['routing'])
    if not pcbnew.ZONE_FILLER(native).Fill(native.Zones()):
        raise ValueError('Independent native refill failed')
    serialized = output.with_suffix('.native.kicad_pcb')
    pcbnew.SaveBoard(str(serialized),native)
    before, after = blocks(board), blocks(serialized)
    def metadata(block):
        tree,_ = parse(tokens(block))
        return [x for x in tree if not isinstance(x,list) or x[0] not in ('filled_polygon','fill_segments')]
    if {k:metadata(v) for k,v in before['zone'].items()} != {k:metadata(v) for k,v in after['zone'].items()}:
        raise ValueError('Independent refill changed zone configuration')
    text = board.read_text()
    edits = [(a,b,after['zone'][UUID_RE.search(text[a:b])[1]])
             for a,b in top_level_spans(text) if text[a:b].startswith('(zone ')]
    output.write_text(replace_spans(text,edits))
    for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru'):
        shutil.copyfile(board.with_suffix(suffix),output.with_suffix(suffix))


def retained_workspace(root, requested):
    """Create a new evidence directory; never reuse or remove existing evidence."""
    cache = (root / '.circuit-cache').resolve()
    target = Path(requested)
    if not target.is_absolute():
        target = root / target
    target = target.resolve()
    if target == cache or not target.is_relative_to(cache):
        raise ValueError('Retained evidence must be a new directory inside .circuit-cache')
    # Board lib tables use ${KIPRJMOD}/../../footprints; only depth one resolves to the repository.
    if target.parent != cache:
        raise ValueError('Retained evidence must be a direct child of .circuit-cache')
    if (cache / (target.name + '-layout')).exists():
        raise FileExistsError('Retained layout evidence already exists for this id')
    target.mkdir(parents=True, exist_ok=False)
    return target


def layout_workspace_path(work):
    """Sibling of the copper evidence, at the same .circuit-cache depth."""
    return work.parent / (work.name + '-layout')


def retain_receipt(root, work, source_hashes, result, oracle_identity=None, layout_work=None):
    """Index real completed native outputs; this function does not run a gate."""
    digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    layout = (work / 'layout-check') if layout_work is None else Path(layout_work).resolve()
    nested = layout.is_relative_to(work)
    if not nested and layout.parent != work.parent:
        raise ValueError('Layout evidence must be inside or a sibling of the copper evidence')
    if any(digest(path) != expected for path, expected in source_hashes.items()):
        raise ValueError('Source changed before evidence retention')
    required = ('drc.json', 'ratsnest.json', 'geometry.json', 'base-geometry.json',
                'refilled.kicad_pcb', 'refilled-ratsnest.json', 'refilled-geometry.json')
    required_layout = ('layout-check-receipt.json', 'bare-evidence/bare-native-receipt.json')
    if (any(not (work / name).is_file() for name in required) or
            any(not (layout / name).is_file() for name in required_layout)):
        raise ValueError('Incomplete native evidence cannot receive a receipt')
    sources, snapshots = {}, {}
    for name, expected in source_hashes.items():
        path = Path(name).resolve()
        # Generated base-check inputs are already preserved and indexed as outputs.
        if path.is_relative_to(work) or path.is_relative_to(layout):
            continue
        key = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        relative = (Path('source-inputs/repository') / path.relative_to(root)
                    if path.is_relative_to(root) else
                    Path('source-inputs/oracle') / path.relative_to(path.anchor))
        destination = work / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        if digest(destination) != expected:
            raise ValueError('Source changed while copying retained inputs')
        sources[key], snapshots[key] = expected, str(relative)
    if any(digest(path) != expected for path, expected in source_hashes.items()):
        raise ValueError('Source changed during evidence retention')
    (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    outputs = {str(path.relative_to(work)): digest(path)
               for path in sorted(work.rglob('*')) if path.is_file()}
    layout_outputs = {} if nested else {str(path.relative_to(layout)): digest(path)
                                        for path in sorted(layout.rglob('*')) if path.is_file()}
    receipt = {'schema_version': 1, 'board_id': 'osc-control', 'oracle_identity': oracle_identity,
               'scope': 'Native routed-draft verification only; not electrical or manufacturing acceptance',
               'model_entry_eligible': False,
               'source_closure_complete': False,
               'source_closure_review': 'PENDING independent review and native execution',
               'base_check_detail': (str((layout / 'layout-check-receipt.json').relative_to(work)) if nested
                                     else str(Path('..') / layout.name / 'layout-check-receipt.json')),
               'layout_evidence_dir': None if nested else layout.name,
               'layout_artifact_sha256': layout_outputs,
               'source_snapshot_paths': snapshots,
               'source_sha256': sources, 'artifact_sha256': outputs, 'result': result}
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


def check(evidence_dir=None):
    configuration(ROOT)
    import pcbnew
    oracle_identity = runtime(ROOT, pcbnew.GetBuildVersion(), subprocess.check_output(['kicad-cli', 'version'], text=True))
    source = ROOT/'design/partition/control-copper/copper.json'
    retained_ratsnest = source.parent/'ratsnest.json'
    spec = json.loads(source.read_bytes())
    base = ROOT/spec['base_board']
    published = ROOT/'boards/osc-control/osc-control-routed-draft.kicad_pcb'
    folder = published.parent
    paths = [source, retained_ratsnest, base, ROOT/spec['definition'], Path(__file__),
             ROOT/'scripts/pcbgen/control_copper_draft.py',
             ROOT/'scripts/pcbgen/control_bypass_geometry.py',
             ROOT/'scripts/pcbgen/extract_power_geometry.py',
             ROOT/'scripts/pcbgen/control_ground_inventory.py',
             ROOT/'design/partition/control-layout/osc-control.receipt.json',
             ROOT/'design/partition/partition.json', ROOT/'design/reports/io-partition.json']
    for board in (base,published):
        paths += [board.with_suffix(s) for s in ('.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_dru')]
    paths += list((folder/'sheets').glob('*.kicad_sch'))
    paths += [folder/'fp-lib-table', folder/'sym-lib-table']
    paths += [ROOT/'scripts/kicad/pin.env', ROOT/'scripts/kicad/run.sh', ROOT/'scripts/pcbgen/check_control_layout.py',
              ROOT/'scripts/pcbgen/ratsnest.py', ROOT/'scripts/pcbgen/route_kicad.py',
              ROOT/'scripts/pcbgen/verify_local_links.py', ROOT/'scripts/pcbgen/uuid_tools.py',
              ROOT/'scripts/schgen/core.py']
    paths += sorted((ROOT/'scripts').rglob('*.py'))
    digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    before = {str(p):digest(p) for p in paths}
    (ROOT/'.circuit-cache').mkdir(exist_ok=True)
    work = (retained_workspace(ROOT, evidence_dir) if evidence_dir is not None else
            Path(tempfile.mkdtemp(prefix='control-copper-',dir=ROOT/'.circuit-cache')))
    try:
        layout_work = layout_workspace_path(work) if evidence_dir is not None else None
        base_receipt = check_base(layout_work)
        if evidence_dir is not None:
            for name, expected in base_receipt['source_sha256'].items():
                if name in before and before[name] != expected:
                    raise ValueError('Conflicting routed/base-check source hashes')
                before[name] = expected
        board = work/published.name
        shutil.copytree(folder/'sheets',work/'sheets')
        for name in ('fp-lib-table','sym-lib-table'):
            shutil.copyfile(folder/name,work/name)
        build(source,board)
        for suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_dru'):
            if board.with_suffix(suffix).read_bytes() != published.with_suffix(suffix).read_bytes():
                raise ValueError('Partial copper differs from source replay: '+suffix)
        native_inputs = {str(p):digest(p) for p in work.rglob('*') if p.is_file()}
        drc_path = work/'drc.json'
        subprocess.run(['kicad-cli','pcb','drc','--schematic-parity','--refill-zones',
                        '--format','json','--severity-all','-o',str(drc_path),str(board)],check=True)
        drc = json.loads(drc_path.read_bytes())
        if (drc['kicad_version']!='10.0.6' or drc['source']!=board.name or drc['violations'] or
                drc['schematic_parity'] or set(drc['included_severities'])!={'error','warning','exclusion'}):
            raise ValueError('Partial copper failed native DRC/parity scope')
        io = json.loads((ROOT/'design/reports/io-partition.json').read_bytes())
        bypasses = audit_bypasses(pcbnew.LoadBoard(str(board)), io, require_connected=True)
        rats = inspect(board)
        (work/'ratsnest.json').write_text(json.dumps(rats,indent=2)+'\n')
        retained = json.loads(retained_ratsnest.read_bytes())
        if {k:v for k,v in retained.items() if k!='board'} != {k:v for k,v in rats.items() if k!='board'}:
            raise ValueError('Retained complete connectivity report differs from fresh native result')
        geom_path = work/'geometry.json'
        base_geom_path = work/'base-geometry.json'
        definition = ROOT/spec['definition']
        extract('osc-control',base,base_geom_path,definition)
        extract('osc-control',board,geom_path,definition)
        old = json.loads(base_geom_path.read_bytes())
        geom = json.loads(geom_path.read_bytes())
        ground_copper_count = require_connected_ground_copper(spec, geom)
        pads = lambda g: {r['uuid']:r for r in g['items'] if 'ref' in r}
        if pads(old)!=pads(geom):
            raise ValueError('Partial copper moved or changed a source pad')
        holes = {r['uuid']:r for r in geom['holes']}
        if any(holes.get(r['uuid'])!=r for r in old['holes']):
            raise ValueError('Partial copper changed an existing drill')
        via_ids = {r['uuid'] for r in spec['copper'] if r['kind']=='via'}
        if set(holes)-{r['uuid'] for r in old['holes']} != via_ids or len(via_ids)!=527:
            raise ValueError('Partial copper drill inventory differs from source')
        for array in spec['main_arrays']:
            if not set(array['via_uuids']) <= set(geom['main_rail_members'][array['net']]):
                raise ValueError('Main-terminal array is disconnected')
        inventory = audit(geom,json.loads((ROOT/'design/partition/control-layout/osc-control.receipt.json').read_bytes()),
                          json.loads((ROOT/'design/partition/partition.json').read_bytes()),
                          json.loads((ROOT/'design/reports/io-partition.json').read_bytes()))
        if rats['native_unconnected_edges'] != 0:
            raise ValueError('Partial-copper connectivity changed: '+str(rats['native_unconnected_edges']))
        refilled = work/'refilled.kicad_pcb'
        independent_refill(board,definition,refilled)
        audit_bypasses(pcbnew.LoadBoard(str(refilled)), io, require_connected=True)
        refill_rats = inspect(refilled)
        (work/'refilled-ratsnest.json').write_text(json.dumps(refill_rats,indent=2)+'\n')
        if refill_rats['native_open_edges_by_net'] != rats['native_open_edges_by_net']:
            raise ValueError('Independent reload/refill changed per-net connectivity')
        if refill_rats['native_unconnected_edges'] != 0:
            raise ValueError('Independent reload/refill changed connectivity')
        refill_geometry_path = work/'refilled-geometry.json'
        extract('osc-control',refilled,refill_geometry_path,definition)
        refill_geometry = json.loads(refill_geometry_path.read_bytes())
        require_connected_ground_copper(spec, refill_geometry)
        if pads(refill_geometry)!=pads(geom) or refill_geometry['holes']!=geom['holes']:
            raise ValueError('Independent reload/refill changed pad/drill geometry')
        audit(refill_geometry,json.loads((ROOT/'design/partition/control-layout/osc-control.receipt.json').read_bytes()),
              json.loads((ROOT/'design/partition/partition.json').read_bytes()),
              json.loads((ROOT/'design/reports/io-partition.json').read_bytes()))
        if any(digest(p)!=value for p,value in {**before,**native_inputs}.items()):
            raise ValueError('Input changed during native copper verification')
        result = {'status':'PASS ROUTED UNVALIDATED DRAFT ONLY','native_open_edges':0,
                  'native_rule_errors':0,'native_parity_findings':0,
                  'native_warnings':sum(v['severity']=='warning' for v in drc['violations']),
                  'ground_contacts_connected':inventory['connected_count'],
                  'ground_copper_objects_connected':ground_copper_count,
                  'local_bypass_rail_pairs_connected':bypasses['rail_pairs_connected'],'source_vias':527,
                  'source_tracks':sum(r['kind']=='segment' for r in spec['copper']),
                  'independent_reload_refill':'PASS: 0 open edges and all 344 ground contacts retained',
                  'board_sha256':digest(published),'routing_complete':True,
                  'electrical_current_resistance_acceptance':'NOT RUN','physical_qualification':'NOT RUN'}
        if evidence_dir is not None:
            retain_receipt(ROOT, work, before, result, oracle_identity, layout_work)
        print(json.dumps(result,indent=2),flush=True)
    except Exception:
        print('Failed partial copper evidence retained at',work,flush=True)
        raise
    else:
        if evidence_dir is None:
            shutil.rmtree(work)
        else:
            print('Completed native evidence retained at', work, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', help='New directory inside .circuit-cache; retain native outputs and exact input snapshots')
    check(parser.parse_args().evidence_dir)
