"""Full-package native field projection fixture, with no plane/routing claim."""
import json
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.sync import sync
from scripts.pcbgen.core_package_fields import native_field_projection,apply_native_fields


def run(output,cache):
    if output.exists():raise ValueError('fresh metadata fixture required')
    cache.mkdir(parents=True,exist_ok=False)
    source=ROOT/'schematic/boards/osc-core.net';projected=native_field_projection(source)
    paths=[source,Path(__file__),ROOT/'scripts/pcbgen/core_package_fields.py',ROOT/'scripts/pcbgen/sync.py',
        ROOT/'scripts/pcbgen/footprint_attributes.py']+[Path(p) for p in projected['source_sheet_sha256']]
    digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    hashes={str(p):digest(p) for p in paths}
    sync('osc-core',output,source);board=pcbnew.LoadBoard(str(output))
    # This fixture checks metadata only. Reservations are tested independently;
    # their known own-pad exception cannot obscure field-parity evidence here.
    for zone in list(board.Zones()):board.Remove(zone)
    apply_native_fields(board,projected);pcbnew.SaveBoard(str(output),board)
    for suffix in ('.kicad_sch','.kicad_pro'):
        original=ROOT/'boards/osc-core'/('osc-core'+suffix);hashes[str(original)]=digest(original)
        shutil.copyfile(original,output.with_suffix(suffix))
    # KiCad resolves Sheetfile paths relative to the copied root schematic.
    # Retain the complete hierarchy, including pages without fitted packages.
    sheet_copies={}
    schematic_root=ROOT/'boards/osc-core'
    for original in sorted((schematic_root/'sheets').rglob('*.kicad_sch')):
        expected=digest(original);hashes[str(original)]=expected
        destination=output.parent/original.relative_to(schematic_root)
        if destination.resolve()!=original.resolve():
            destination.parent.mkdir(parents=True,exist_ok=True)
            if destination.exists():raise ValueError('fresh fixture sheet mirror required')
            shutil.copyfile(original,destination)
        sheet_copies[str(destination)]=expected
    output.with_suffix('.kicad_dru').write_text('(version 1)\n')
    def check(label):
        report=cache/(label+'.json')
        subprocess.run(['kicad-cli','pcb','drc','--schematic-parity','--format','json','--severity-all','-o',str(report),str(output)],check=True)
        result=json.loads(report.read_text())
        if result['kicad_version']!='10.0.6':raise ValueError('wrong oracle')
        return result
    positive=check('positive')
    if positive['schematic_parity']:raise ValueError('complete native fields projection did not close parity')
    fp=next(f for f in board.GetFootprints() if f.GetReference()=='U4209')
    fp.SetField('LogicalCellKey','INTENTIONAL WRONG AGGREGATED FIELD');pcbnew.SaveBoard(str(output),board)
    negative=check('negative')
    if not any(r['type']=='footprint_symbol_field_mismatch' and any(i['description']=='Footprint U4209' for i in r['items']) for r in negative['schematic_parity']):
        raise ValueError('native parity failed to reject changed mixed-unit aggregate')
    if any(digest(p)!=expected for p,expected in hashes.items()):raise ValueError('native fields fixture source changed')
    if any(digest(p)!=expected for p,expected in sheet_copies.items()):raise ValueError('native fields fixture sheet copy changed')
    (cache/'receipt.json').write_text(json.dumps({'status':'PASS metadata-only exact native projection; no board geometry or electrical acceptance',
        'source_sha256':hashes,'packages':len(projected['packages']),'all_original_source_units':len(projected['all_original_source_units']),
        'positive_parity_count':0,'negative_parity_count':len(negative['schematic_parity']),
        'native_artifacts':{str(cache/(n+'.json')):digest(cache/(n+'.json')) for n in ('positive','negative')},
        'schematic_sheet_copies_sha256':sheet_copies,'projection':projected},indent=2,sort_keys=True)+'\n')
    print('PASS all',len(projected['packages']),'native package fields; changed mixed-unit aggregate rejected',flush=True)


if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
