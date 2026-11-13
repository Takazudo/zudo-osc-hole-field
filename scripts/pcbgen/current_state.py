#!/usr/bin/env python3
"""Record the current native state of an adopted OSC PCB from an isolated copy.

The adopted board stays the original: it is copied into a disposable workspace,
the copy alone is refilled and saved by native DRC, and the original is never
replaced. The record binds the input bytes, the refilled output bytes, the
project/rule hashes, the pinned KiCad version, the raw DRC report and the native
connectivity (open edges, AGND islands, rails) to one source. Warning
completeness is reported, not assumed: KiCad 10.0.6 lists at most 199 warnings
per type, so a capped type is INCOMPLETE until a source-bound audit completes it.
Draft only: routing is incomplete and electrical/physical qualification is NOT RUN.
"""
from __future__ import annotations
import argparse,collections,datetime,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import scripts.pcbgen.route_jack_grid as driver
from scripts.pcbgen.complete_native_warnings import CAP,capped_types

BOARDS=('osc-core','osc-jack-left','osc-jack-right')
SCHEMA='osc-current-native-state-1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_sha(folder):
    """One digest over every file below folder, keyed by relative path."""
    h=hashlib.sha256()
    for p in sorted(Path(folder).rglob('*')):
        if p.is_file():h.update(f'{p.relative_to(folder)}\0{sha(p)}\n'.encode())
    return h.hexdigest()


def kicad_version():
    done=subprocess.run(['bash','scripts/kicad/run.sh','kicad-cli','version'],cwd=ROOT,text=True,capture_output=True,check=True)
    return done.stdout.strip()


def pinned_image():
    for line in (ROOT/'scripts/kicad/pin.env').read_text().splitlines():
        if line.startswith('KICAD_IMAGE='):return line.split('=',1)[1].strip("'\"")
    raise ValueError('KICAD_IMAGE missing from pin.env')


def metadata_successor(board_id,source_sha):
    """The verified metadata-only successor receipt naming these bytes, or None (scripts/checks/metadata_successor.py)."""
    from scripts.checks.metadata_successor import successor_for
    return successor_for(f'boards/{board_id}/{board_id}.kicad_pcb',source_sha,ROOT)


def latest_receipt(board_id,source_sha):
    """The adopted stage receipt whose candidate hash is the current board, if any.

    A metadata-only successor resolves to the receipt of its adopted bytes, and only after
    the successor receipt has re-derived the property-only difference from Git."""
    direct=adopted_receipt(board_id,source_sha)
    if direct is not None:return direct
    successor=metadata_successor(board_id,source_sha)
    return None if successor is None else adopted_receipt(board_id,successor['adopted']['sha256'])


def adopted_receipt(board_id,source_sha):
    found=[]
    for path in sorted((ROOT/'boards'/board_id/'reports'/'grid-routing').glob('*.json')):
        if path.name.endswith('-copper.json'):continue
        try:r=json.loads(path.read_text())
        except ValueError:continue
        if not isinstance(r,dict):continue
        gate=receipt_gate(r)
        if r.get('adopted') and gate.get('adopted') and gate.get('candidate_board_sha256')==source_sha:found.append((path,r))
    if len(found)!=1:return None
    path,r=found[0]
    gate=receipt_gate(r)
    # osc3 chain receipts (osc3-k-chain-1) keep only total open edges; their AGND count is unknown, not zero.
    if gate is not r:agnd=r['after'].get('agnd_open_edges') if isinstance(r.get('after'),dict) else None
    else:agnd=r.get('open_by_net_after',{}).get('AGND')
    return {'path':str(path.relative_to(ROOT)),'sha256':sha(path),'stage':gate.get('stage'),
            'open_edges_after':gate.get('open_edges_after'),'agnd_open_edges_after':agnd}


def receipt_gate(r):
    """Stage receipts keep the gate at top level; osc3 chain receipts keep it under final_gate."""
    if 'candidate_board_sha256' not in r and isinstance(r.get('final_gate'),dict):return r['final_gate']
    return r


def summarize(board_id,source,input_sha,output_sha,drc,dump,context):
    warnings=collections.Counter(v['type'] for v in drc['violations'] if v['severity']=='warning')
    errors=collections.Counter(v['type'] for v in drc['violations'] if v['severity']=='error')
    capped=sorted(capped_types(drc))
    open_by_net={n:len(g)-1 for n,g in dump['islands'].items() if len(g)>1}
    rails={n:open_by_net.get(n,0) for n in driver.RAILS}
    agnd=open_by_net.get('AGND',0)
    signature=hashlib.sha256(json.dumps(driver.connectivity_signature(dump),sort_keys=True).encode()).hexdigest()
    receipt=latest_receipt(board_id,input_sha)
    successor=metadata_successor(board_id,input_sha)
    return {
        'schema':SCHEMA,'board_id':board_id,'board':str(source.relative_to(ROOT)),
        'status':'NATIVE CHECKED UNVALIDATED DRAFT; ROUTING INCOMPLETE' if dump['open_edges'] else 'NATIVE CHECKED UNVALIDATED DRAFT',
        'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'tool':{'kicad_cli_version':context['version'],'image':context['image'],'wrapper':'scripts/kicad/run.sh'},
        'source':{'input_board_sha256':input_sha,'project_sha256':context['project_sha256'],'rules_sha256':context['rules_sha256'],
                  'schematic_sha256':context['schematic_sha256'],'sheets_tree_sha256':context['sheets_tree_sha256']},
        'method':{'command':'kicad-cli pcb drc --schematic-parity --refill-zones --save-board --format json --severity-all',
                  'connectivity':'scripts/pcbgen/grid_dump.py on the refilled copy',
                  'settled_refill':'route_jack_grid.check(): three equal island signatures, at most six refills',
                  'isolation':'disposable copy under .circuit-cache; the adopted original is read only and not replaced'},
        'refilled_copy':{'output_board_sha256':output_sha,'differs_from_input':output_sha!=input_sha,
                         'adopted':False,'note':'Refill output is a check artifact; it never replaces the adopted board'},
        'raw':{'drc_report':f'boards/{board_id}/reports/drc.json'},
        'native':{'open_edges':dump['open_edges'],'agnd_open_edges':agnd,'agnd_islands':len(dump['islands'].get('AGND',[None])),
                  'rail_open_edges':rails,'other_signal_open_edges':dump['open_edges']-agnd-sum(rails.values()),
                  'open_nets':len(open_by_net),'island_signature_sha256':signature,
                  'drc_errors':sum(errors.values()),'drc_errors_by_type':dict(sorted(errors.items())),
                  'drc_warnings_listed':sum(warnings.values()),'drc_warnings_by_type':dict(sorted(warnings.items())),
                  'drc_unconnected_items_listed':len(drc.get('unconnected_items',[])),
                  'schematic_parity':len(drc.get('schematic_parity',[]))},
        'warning_completeness':{
            'cap_per_type':CAP,'capped_types':capped,
            'status':('INCOMPLETE: native report capped; complete evidence NOT RUN for this standalone state' if capped
                      else 'COMPLETE: no warning type reached the native cap'),
            'gate_rule':'route_jack_grid.warning_complete_gate requires source-bound complete evidence before any capped promotion'},
        'latest_adopted_receipt':receipt,
        'metadata_successor':None if successor is None else {
            'path':successor['path'],'sha256':successor['receipt_sha256'],
            'adopted_board_sha256':successor['adopted']['sha256'],'adopted_label':successor['adopted']['label']},
        'receipt_agreement':None if receipt is None else {
            'open_edges':receipt['open_edges_after']==dump['open_edges'],
            'agnd_open_edges':None if receipt['agnd_open_edges_after'] is None else receipt['agnd_open_edges_after']==agnd},
        'fabrication_outputs':'NOT CREATED','qualification':'NOT RUN: electrical, thermal and physical qualification',
    }


def record(board_id):
    source=ROOT/'boards'/board_id/f'{board_id}.kicad_pcb'
    input_sha=sha(source)
    work=driver.workspace(board_id,'current-state');copy=work/source.name;shutil.copyfile(source,copy)
    if sha(copy)!=input_sha:raise RuntimeError('isolated copy differs from the adopted board')
    context={'version':kicad_version(),'image':pinned_image(),
             'project_sha256':sha(source.with_suffix('.kicad_pro')),
             'rules_sha256':sha(source.with_suffix('.kicad_dru')) if source.with_suffix('.kicad_dru').exists() else None,
             'schematic_sha256':sha(source.with_suffix('.kicad_sch')),'sheets_tree_sha256':tree_sha(source.parent/'sheets')}
    if context['version']!='10.0.6':raise RuntimeError('KiCad 10.0.6 oracle required, got '+context['version'])
    drc,dump=driver.check(copy)
    if sha(source)!=input_sha:raise RuntimeError('adopted board changed during the native check')
    output_sha=sha(copy)
    reports=source.parent/'reports'
    shutil.copyfile(copy.with_name('drc.json'),reports/'drc.json')
    state=summarize(board_id,source,input_sha,output_sha,drc,dump,context)
    (reports/'routing.json').write_text(json.dumps(state,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'board':board_id,'open_edges':state['native']['open_edges'],'agnd':state['native']['agnd_open_edges'],
                      'capped':state['warning_completeness']['capped_types'],'errors':state['native']['drc_errors'],
                      'parity':state['native']['schematic_parity'],'input':input_sha[:12],'output':output_sha[:12]}),flush=True)
    return state


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('boards',nargs='*',choices=BOARDS,default=list(BOARDS))
    for board_id in p.parse_args().boards:record(board_id)


if __name__=='__main__':main()
