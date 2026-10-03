"""Fresh native verification of the partial control-board copper checkpoint."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
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


def check():
    check_base()
    import pcbnew
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
    digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    before = {str(p):digest(p) for p in paths}
    (ROOT/'.circuit-cache').mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='control-copper-',dir=ROOT/'.circuit-cache'))
    try:
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
        print(json.dumps(result,indent=2),flush=True)
    except Exception:
        print('Failed partial copper evidence retained at',work,flush=True)
        raise
    else:
        shutil.rmtree(work)


if __name__ == '__main__':
    check()
