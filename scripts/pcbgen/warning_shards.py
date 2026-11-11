"""Plan, run and assemble a sharded complete-warning audit; host-only, never imports pcbnew.

The silk sub-audit is split into fixed fixture ranges of `audit_added_mask.py --fixture-range`;
holes-before, holes-after and zones run whole through their unchanged scripts. `run-unit`
wraps one native unit through `scripts/kicad/run.sh` and writes a host receipt beside it.
`assemble` rebuilds the `native-audits/` layout that `audit_current_reports` writes, after
rejecting any gap, overlap, foreign input, mixed tool/oracle identity, tampered file or
incomplete unit. It never writes `proof.json`: only `audit_current_reports` or the unchanged
`complete_reports` (the `verify` command) decide anything. An assembled tree is evidence to be
re-verified, not an adoption; every board remains an unvalidated draft.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import resource
import shutil
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.audit_added_mask import (PROBE_BATCH, SHARD_STATUS, added_copper_scope, check_fixture_range, new_silk_identities,
                                             ordered_scope_sha256, parse_fixture_range, read_stage_removals, removal_source,
                                             reviewed_copper_removals, stage_removed_uuids, unchanged_nonrouting, write_stage_removals,
                                             StageRemovals)
from scripts.pcbgen.uuid_tools import top_level_spans, UUID_RE

# Every file a native unit executes, plus this wrapper; a receipt binds their bytes.
TOOL_FILES=('scripts/pcbgen/audit_added_mask.py','scripts/pcbgen/audit_hole_pairs.py','scripts/pcbgen/audit_zone_silk_scope.py',
            'scripts/pcbgen/zone_batch_evidence.py','scripts/pcbgen/zone_batch_resume.py','scripts/pcbgen/uuid_tools.py',
            'scripts/pcbgen/copper_identity.py','scripts/pcbgen/complete_native_warnings.py','scripts/pcbgen/warning_shards.py',
            'scripts/kicad/run.sh','scripts/kicad/pin.env')
WHOLE_UNITS=('holes-before','holes-after','zones')
ZONE_BATCH_SIZE=16  # route_jack_grid.py's complete-gate default
RECEIPT='unit-receipt.json';STARTED='unit-started.json'
UNIT_STATUS='UNIT RECEIPT; NOT COMPLETE EVIDENCE'
ASSEMBLY_STATUS='ASSEMBLED FROM SHARDS; RE-VERIFY WITH complete_reports; NOT AN ADOPTION'
MONOLITH_STATUS='READ-ONLY NATIVE ADDED-MASK EVIDENCE; PROMOTION GATE UNCHANGED'
HOLE_STATUS='READ-ONLY NATIVE FIXTURE EVIDENCE; NOT FULL-BOARD ACCEPTANCE'
ZONE_STATUS='READ-ONLY NATIVE ZONE SHAPE EVIDENCE; NO PROMOTION'
SHARED_RECEIPT_KEYS=('tool_commit','tool_files','kicad_image','inspected_image_digest','oracle_mode','version','before_sha256',
                     'after_sha256','project_sha256','rules_sha256','removal_scope_sha256')
SHARED_SHARD_KEYS=('ordered_scope_sha256','added_copper_source_scope','unchanged_nonrouting_objects','added_unmasked_tracks','fixture_total')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n')
def utc():return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def identity(v):return (v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items'])))
def normalized(rows):return {(a,b,tuple(c)) for a,b,c in rows}


def parse_unit(text):
    if text in WHOLE_UNITS:return text,None
    match=re.fullmatch(r'silk:(\d+:\d+)',text or '')
    if not match:raise ValueError('unit must be silk:START:END, holes-before, holes-after or zones')
    return 'silk',parse_fixture_range(match[1])


def removal_scope(cuts):
    """sha256 of the removal source and its sorted UUIDs, or None; the same scope hashes the same however it was supplied."""
    return hashlib.sha256(json.dumps([removal_source(cuts),sorted(cuts)]).encode()).hexdigest() if cuts else None


def load_cuts(before, after, reviewed=(), stage_scope=None, from_delta=False):
    """from_delta derives StageRemovals from the boards themselves, as route_jack_grid.complete_gate does."""
    if sum(map(bool,(reviewed,stage_scope,from_delta)))>1:raise ValueError('use one removal scope source')
    if from_delta:return stage_removed_uuids(Path(before).read_text(),Path(after).read_text())
    return read_stage_removals(stage_scope,before,after) if stage_scope else list(reviewed)


def source_context(before, after, cuts=()):
    """Host recomputation of everything a unit must agree with; text only."""
    before,after=Path(before),Path(after);bt,at=before.read_text(),after.read_text()
    for suffix in ('.kicad_pro','.kicad_dru'):
        if before.with_suffix(suffix).read_bytes()!=after.with_suffix(suffix).read_bytes():raise ValueError('project/rules changed')
    count=unchanged_nonrouting(bt,at,cuts)
    scope=added_copper_scope(bt,at,reviewed_removed_uuids=cuts)
    cut_scope=reviewed_copper_removals(bt,at,cuts)
    return dict(before_sha256=sha(before),after_sha256=sha(after),project_sha256=sha(before.with_suffix('.kicad_pro')),
                rules_sha256=sha(before.with_suffix('.kicad_dru')),added_copper_source_scope=scope,ordered_scope_sha256=ordered_scope_sha256(scope),
                fixture_total=len(scope),expected_vias=sum(k=='via' for k in scope.values()),unchanged_nonrouting_objects=count,
                added_unmasked_tracks=sum(k=='segment' for k in scope.values()),reviewed_copper_removals=cut_scope,
                copper_removal_source=removal_source(cuts) if cut_scope else None,removal_scope_sha256=removal_scope(cuts))


def pinned_image(root=ROOT):
    match=re.search(r"^KICAD_IMAGE='([^']+@sha256:[0-9a-f]{64})'$",(Path(root)/'scripts/kicad/pin.env').read_text(),re.M)
    if not match:raise ValueError('pin.env has no digest-pinned KICAD_IMAGE')
    return match[1]


def tool_files(root=ROOT):return {name:sha(Path(root)/name) for name in TOOL_FILES}


def tool_identity(root=ROOT):
    """The committed tool bytes a unit executes; uncommitted tool edits are refused."""
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('tool commit is not a 40-hex commit')
    dirty=subprocess.run(['git','status','--porcelain','--',*TOOL_FILES],cwd=root,check=True,capture_output=True,text=True).stdout
    if dirty.strip():raise ValueError('tool files differ from the tool commit')
    return dict(tool_commit=commit,tool_files=tool_files(root))


def oracle_identity(root=ROOT):
    """Mirror run.sh's selection: KICAD_CLI_BIN or a missing docker would select another oracle."""
    image=pinned_image(root)
    if os.environ.get('KICAD_CLI_BIN'):raise ValueError('KICAD_CLI_BIN selects a native oracle; units require the pinned Docker image')
    docker=shutil.which('docker')
    if not docker:raise ValueError('docker missing; units require the pinned Docker image')
    digests=json.loads(subprocess.run([docker,'image','inspect','--format','{{json .RepoDigests}}',image],check=True,capture_output=True,text=True).stdout)
    want=image.split('@',1)[1];found=[d.split('@',1)[1] for d in digests or [] if '@' in d and d.split('@',1)[1]==want]
    if not found:raise ValueError('inspected image digest differs from pin.env')
    return dict(oracle_mode='docker',kicad_image=image,inspected_image_digest=found[0])


def unit_command(kind, rng, before, after, out, context, cuts, stage_scope, root=ROOT):
    rel=lambda p:str(Path(p).resolve().relative_to(Path(root).resolve()))
    if kind=='holes-before':command=['scripts/pcbgen/audit_hole_pairs.py',rel(before),rel(out)]
    elif kind=='holes-after':command=['scripts/pcbgen/audit_hole_pairs.py',rel(after),rel(out)]
    elif kind=='zones':command=['scripts/pcbgen/audit_zone_silk_scope.py',rel(before),rel(after),rel(out),'--classify','--batch-size',str(ZONE_BATCH_SIZE)]
    else:command=['scripts/pcbgen/audit_added_mask.py',rel(before),rel(after),rel(out),'--expected-copper',str(context['fixture_total']),
                  '--expected-vias',str(context['expected_vias']),'--fixture-range',f'{rng[0]}:{rng[1]}']
    if kind in ('silk','zones') and cuts:
        command+=['--stage-removal-scope',rel(stage_scope)] if stage_scope else [a for u in sorted(cuts) for a in ('--reviewed-cut-uuid',u)]
    return ['bash','scripts/kicad/run.sh','python3',*command]


def native_runner(argv, root):subprocess.run(argv,cwd=root,check=True)


class MemoryPeak:
    """Host used-memory peak (MemTotal-MemAvailable) while the unit runs; it includes the container."""
    def __init__(self):self.peak=None;self.stop=threading.Event();self.thread=threading.Thread(target=self.sample,daemon=True)
    def sample(self):
        while True:
            try:
                info=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
                used=int(info['MemTotal'].split()[0])-int(info['MemAvailable'].split()[0]);self.peak=max(self.peak or 0,used)
            except (OSError,KeyError,ValueError):return
            if self.stop.wait(5):return
    def __enter__(self):self.thread.start();return self
    def __exit__(self,*exc):self.stop.set();self.thread.join()


def manifest(folder):
    folder=Path(folder);files={}
    for path in sorted(folder.rglob('*')):
        if path.is_symlink():raise ValueError('unit directory holds a symlink: '+str(path))
        if path.is_file() and path.relative_to(folder).as_posix()!=RECEIPT:files[path.relative_to(folder).as_posix()]=sha(path)
    return files


def run_unit(before, after, out, unit, reviewed=(), stage_scope=None, from_delta=False, provenance=None, root=ROOT,
             runner=native_runner, oracle=oracle_identity, tool=tool_identity):
    kind,rng=parse_unit(unit);before,after,out=Path(before).resolve(),Path(after).resolve(),Path(out).resolve()
    for path in (before,after,out,*([Path(stage_scope).resolve()] if stage_scope else [])):
        path.relative_to(Path(root).resolve())  # run.sh mounts only the checkout at /work
    if out.exists():raise ValueError('unit output must be a new directory')
    cuts=load_cuts(before,after,reviewed,stage_scope,from_delta);context=source_context(before,after,cuts)
    if rng:check_fixture_range(rng,context['fixture_total'])
    if from_delta and cuts:
        # A stage scope travels to the container as a hash-bound file, as in audit_current_reports; kept outside the unit directory.
        out.parent.mkdir(parents=True,exist_ok=True)
        stage_scope=write_stage_removals(out.parent/(out.name+'.stage-removal-scope.json'),before,after,cuts)
    tool_id=tool(root);oracle_id=oracle(root)
    argv=unit_command(kind,rng,before,after,out,context,cuts,stage_scope,root)
    out.mkdir(parents=True);start=utc();write(out/STARTED,dict(status='STARTED; NO UNIT RECEIPT',unit=unit,argv=argv,started_utc=start))
    began=time.monotonic()
    with MemoryPeak() as memory:runner(argv,root)
    wall=round(time.monotonic()-began,3)
    result_file='shard-result.json' if kind=='silk' else 'result.json'
    if not (out/result_file).is_file() or (kind=='silk' and (out/'result.json').exists()):raise ValueError('unit wrote no terminal result')
    result=read(out/result_file)
    env=os.environ.get
    receipt=dict(status=UNIT_STATUS,unit=unit,argv=argv,**tool_id,**oracle_id,version=result.get('version'),
                 **{k:context[k] for k in ('before_sha256','after_sha256','project_sha256','rules_sha256','removal_scope_sha256')},
                 **{k:(provenance or {}).get(k) for k in ('before_commit','before_dir','after_commit','after_dir')},
                 result_file=result_file,result_sha256=sha(out/result_file),files=manifest(out),
                 github_run_id=env('GITHUB_RUN_ID'),run_attempt=env('GITHUB_RUN_ATTEMPT'),job=env('GITHUB_JOB'),
                 started_utc=start,ended_utc=utc(),wall_seconds=wall,host_used_memory_peak_kib=memory.peak,
                 host_children_maxrss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                 runner_image=' '.join(filter(None,[env('ImageOS'),env('ImageVersion')])) or platform.platform())
    write(out/RECEIPT,receipt)
    return receipt


def plan(before, after, shard_size, reviewed=(), stage_scope=None, from_delta=False, pilot_ranges=None):
    if type(shard_size) is not int or shard_size<=0 or shard_size%PROBE_BATCH:raise ValueError(f'shard size must be a positive multiple of {PROBE_BATCH}')
    cuts=load_cuts(before,after,reviewed,stage_scope,from_delta);context=source_context(before,after,cuts);total=context['fixture_total']
    ranges=[(a,min(a+shard_size,total)) for a in range(0,total,shard_size)]
    if pilot_ranges is not None:
        ranges=[check_fixture_range(parse_fixture_range(r),total) for r in pilot_ranges]
        if not ranges or len(set(ranges))!=len(ranges):raise ValueError('pilot ranges must be distinct and nonempty')
    units=[f'silk:{a}:{b}' for a,b in ranges]+([] if pilot_ranges is not None else list(WHOLE_UNITS))
    return dict(status='PILOT TIMING; NOT EVIDENCE' if pilot_ranges is not None else 'PLAN; NO NATIVE RESULT',shard_size=shard_size,units=units,
                **{k:context[k] for k in ('before_sha256','after_sha256','project_sha256','rules_sha256','removal_scope_sha256',
                                          'fixture_total','expected_vias','ordered_scope_sha256')})


def fixture_board_check(text, uid, after_blocks):
    copper=[]
    for a,b in top_level_spans(text):
        block=text[a:b];kind=block[1:].split(None,1)[0].rstrip(')')
        if kind=='zone':raise ValueError('fixture board contains a zone')
        if kind=='footprint' and any(block[x+1:y].split(None,1)[0].rstrip(')')=='pad' for x,y in top_level_spans(block)):
            raise ValueError('fixture board retains a pad')
        if kind in ('segment','via','arc'):copper.append(block)
    if copper!=[after_blocks[uid]]:raise ValueError('fixture copper differs from the after-board block of its copper_uuid')


def hole_context(before):
    import math
    context={'project_sha256':sha(Path(before).with_suffix('.kicad_pro')),'rules_sha256':sha(Path(before).with_suffix('.kicad_dru'))}
    context['clearance_nm']=math.ceil(read(Path(before).with_suffix('.kicad_pro'))['board']['design_settings']['rules']['min_hole_to_hole']*1e6)
    return context


def check_silk_unit(folder, rng, context, ordered, after_name, after_blocks):
    start,end=rng
    if (folder/'result.json').exists():raise ValueError('silk shard directory holds result.json')
    res=read(folder/'shard-result.json')
    if 'added_copper_scope_complete' in res:raise ValueError('silk shard receipt claims added_copper_scope_complete')
    if res.get('status')!=SHARD_STATUS or res.get('fixture_range')!=[start,end]:raise ValueError('silk shard status or range differs from its unit')
    for key in ('before_sha256','after_sha256','project_sha256','rules_sha256',*SHARED_SHARD_KEYS):
        if res.get(key)!=context[key]:raise ValueError('silk shard differs from host recomputation: '+key)
    cuts=context['reviewed_copper_removals']
    if res.get('reviewed_copper_removals',{})!=cuts or (cuts and res.get('copper_removal_source')!=context['copper_removal_source']):
        raise ValueError('silk shard removal scope differs from host recomputation')
    folders={p.name for p in folder.iterdir() if p.name.startswith('fixture-')}
    if folders!={f'fixture-{i:03d}' for i in range(start,end)} or len(res['fixtures'])!=end-start:raise ValueError('silk shard fixtures differ from its range')
    found=set()
    for i,f in enumerate(res['fixtures'],start):
        uid=ordered[i];fixture=folder/f'fixture-{i:03d}'
        if f['copper_uuid']!=uid or f['kind']!=context['added_copper_source_scope'][uid]:raise ValueError('silk fixture copper_uuid/kind differs from sorted scope')
        if sha(fixture/'drc.json')!=f['report_sha256']:raise ValueError('silk fixture report hash mismatch')
        board=fixture/after_name
        if sha(board)!=f.get('fixture_sha256'):raise ValueError('silk fixture board bytes differ from fixture_sha256')
        for suffix,key in (('.kicad_pro','project_sha256'),('.kicad_dru','rules_sha256')):
            if sha(board.with_suffix(suffix))!=context[key]:raise ValueError('silk fixture context changed')
        fixture_board_check(board.read_text(),uid,after_blocks)
        rows=new_silk_identities(read(fixture/'drc.json'),uid)
        if rows!=f['violations']:raise ValueError('silk receipt differs from raw native report')
        found.update(identity(v) for v in rows)
    if found!=normalized(res['new_mask_identities']):raise ValueError('silk shard identity union incomplete')
    return res,found


def assemble(before, after, units_dir, output, reviewed=(), stage_scope=None, from_delta=False, root=ROOT):
    before,after,units_dir,output=Path(before),Path(after),Path(units_dir),Path(output)
    if output.exists():raise ValueError('assembly output must be a new directory')
    cuts=load_cuts(before,after,reviewed,stage_scope,from_delta);context=source_context(before,after,cuts)
    image=pinned_image(root);host_tools=tool_files(root);total=context['fixture_total']
    units={}
    for folder in sorted(p for p in units_dir.iterdir()):
        if not folder.is_dir() or folder.is_symlink():raise ValueError('unexpected entry in units directory: '+folder.name)
        if not (folder/RECEIPT).is_file():raise ValueError(f'unit {folder.name} has no terminal receipt')
        receipt=read(folder/RECEIPT);name=receipt.get('unit')
        if receipt.get('status')!=UNIT_STATUS:raise ValueError('not a unit receipt: '+folder.name)
        parse_unit(name)
        if name in units:raise ValueError('second receipt for unit '+name)
        if manifest(folder)!=receipt.get('files'):raise ValueError(f'unit {name} file manifest does not verify')
        if receipt['result_file'] not in receipt['files'] or sha(folder/receipt['result_file'])!=receipt['result_sha256']:
            raise ValueError(f'unit {name} result hash mismatch')
        units[name]=(folder,receipt)
    if not units:raise ValueError('no units')
    first=next(iter(units.values()))[1]
    for key in SHARED_RECEIPT_KEYS:
        if any(r.get(key)!=first.get(key) for _,r in units.values()):raise ValueError('units differ in '+key)
    expected=dict(tool_files=host_tools,kicad_image=image,inspected_image_digest=image.split('@',1)[1],oracle_mode='docker',version='10.0.6',
                  **{k:context[k] for k in ('before_sha256','after_sha256','project_sha256','rules_sha256','removal_scope_sha256')})
    for key,value in expected.items():
        if first.get(key)!=value:raise ValueError('unit '+key+' differs from host recomputation')
    if not re.fullmatch('[0-9a-f]{40}',str(first.get('tool_commit'))):raise ValueError('unit tool_commit is not a 40-hex commit')
    for name in WHOLE_UNITS:
        if name not in units:raise ValueError('missing unit '+name)
    ranges=sorted(parse_unit(n)[1] for n in units if n.startswith('silk:'))
    cursor=0
    for a,b in ranges:
        if a%PROBE_BATCH or a>=b or b>total:raise ValueError(f'unaligned or out-of-scope silk range {a}:{b} for {total} fixtures')
        if a!=cursor:raise ValueError(f'silk ranges do not tile 0..{total-1} exactly once at {cursor}')
        cursor=b
    if cursor!=total:raise ValueError(f'silk ranges do not tile 0..{total-1} exactly once at {cursor}')
    holes=hole_context(before)
    from scripts.pcbgen.complete_native_warnings import hole_evidence
    for name,board in (('holes-before',before),('holes-after',after)):
        folder=units[name][0];res=read(folder/'result.json')
        if (res.get('status')!=HOLE_STATUS or res.get('version')!='10.0.6' or res.get('source_sha256')!=sha(board) or 'fixtures' not in res
                or res.get('project_sha256')!=context['project_sha256'] or res.get('rules_sha256')!=context['rules_sha256']):
            raise ValueError(name+' is not the unmodified script\'s complete result for these hashes')
        hole_evidence(folder,board,{'violations':[]},holes)
    zone=read(units['zones'][0]/'result.json')
    if (zone.get('status')!=ZONE_STATUS or zone.get('version')!='10.0.6' or zone.get('zone_silk_scope_complete') is not True
            or zone.get('before_sha256')!=context['before_sha256'] or zone.get('after_sha256')!=context['after_sha256']):
        raise ValueError('zones is not the unmodified script\'s complete result for these hashes')
    ordered=sorted(context['added_copper_source_scope']);text=after.read_text();after_blocks={}
    for a,b in top_level_spans(text):
        block=text[a:b]
        if block[1:].split(None,1)[0].rstrip(')') in ('segment','via'):
            uid=UUID_RE.search(block)[1]
            if uid in context['added_copper_source_scope']:after_blocks[uid]=block
    shards=[];identities=set();started=set()
    for a,b in ranges:
        folder=units[f'silk:{a}:{b}'][0];res,found=check_silk_unit(folder,(a,b),context,ordered,after.name,after_blocks)
        shards.append((folder,res));identities|=found;started.add((folder/'started.json').read_bytes())
    if len(started)!=1:raise ValueError('silk shards started on different sources')
    output.mkdir(parents=True)
    write(output/'added-copper-scope.json',dict(before_sha256=context['before_sha256'],after_sha256=context['after_sha256'],copper=context['added_copper_source_scope'],
          **({'reviewed_copper_removals':context['reviewed_copper_removals'],'copper_removal_source':context['copper_removal_source']} if context['reviewed_copper_removals'] else {})))
    for name in WHOLE_UNITS:shutil.copytree(units[name][0],output/name,ignore=shutil.ignore_patterns(RECEIPT,STARTED))
    silk=output/'silk';silk.mkdir();(silk/'started.json').write_bytes(started.pop());fixtures=[]
    for folder,res in shards:
        for i in range(*res['fixture_range']):shutil.copytree(folder/f'fixture-{i:03d}',silk/f'fixture-{i:03d}')
        fixtures.extend(res['fixtures'])
    result=dict(status=MONOLITH_STATUS,version='10.0.6',before_sha256=context['before_sha256'],after_sha256=context['after_sha256'],
                unchanged_nonrouting_objects=context['unchanged_nonrouting_objects'],added_unmasked_tracks=context['added_unmasked_tracks'],
                added_copper_scope_complete=True,added_copper_source_scope=context['added_copper_source_scope'],
                new_mask_identities=sorted(identities),fixtures=fixtures)
    if cuts:result.update(reviewed_copper_removals=context['reviewed_copper_removals'],copper_removal_source=context['copper_removal_source'])
    write(silk/'result.json',result)
    write(output/'assembly-receipt.json',dict(status=ASSEMBLY_STATUS,tool_commit=first['tool_commit'],tool_files=host_tools,kicad_image=image,
          inspected_image_digest=first['inspected_image_digest'],before_sha256=context['before_sha256'],after_sha256=context['after_sha256'],
          fixture_total=total,ordered_scope_sha256=context['ordered_scope_sha256'],silk_tiling=[list(r) for r in ranges],
          units={name:dict(receipt_sha256=sha(folder/RECEIPT),result_sha256=r['result_sha256'],github_run_id=r.get('github_run_id'),
                            run_attempt=r.get('run_attempt'),wall_seconds=r.get('wall_seconds')) for name,(folder,r) in sorted(units.items())},
          silk_result_sha256=sha(silk/'result.json')))
    return output


def verify(before, after, tree, before_drc, after_drc, reviewed=(), stage_scope=None, from_delta=False):
    """The unchanged complete_reports on an assembled tree; writes nothing into the tree."""
    from scripts.pcbgen.complete_native_warnings import complete_reports
    cuts=load_cuts(before,after,reviewed,stage_scope,from_delta);tree=Path(tree)
    kwargs={'reviewed_removed_uuids':cuts if isinstance(cuts,StageRemovals) else sorted(cuts)} if cuts else {}
    return complete_reports(before,after,read(before_drc),read(after_drc),tree/'holes-before',tree/'holes-after',tree/'silk',tree/'zones',**kwargs)[2]


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    def common(p):
        p.add_argument('before',type=Path);p.add_argument('after',type=Path)
        p.add_argument('--reviewed-cut-uuid',action='append',default=[]);p.add_argument('--stage-removal-scope',type=Path)
        p.add_argument('--stage-removals-from-delta',action='store_true',help='derive the stage removal scope from the board delta, as complete_gate does')
    p=sub.add_parser('plan');common(p);p.add_argument('--shard-size',type=int,required=True)
    p.add_argument('--pilot-ranges',help='comma-separated START:END; pilot timing only, no holes/zones units');p.add_argument('--output',type=Path)
    p=sub.add_parser('run-unit');common(p);p.add_argument('output',type=Path);p.add_argument('--unit',required=True)
    for name in ('before-commit','before-dir','after-commit','after-dir'):p.add_argument('--'+name)
    p=sub.add_parser('assemble');common(p);p.add_argument('units',type=Path);p.add_argument('output',type=Path)
    p=sub.add_parser('verify');common(p);p.add_argument('tree',type=Path)
    p.add_argument('--before-drc',type=Path,required=True);p.add_argument('--after-drc',type=Path,required=True)
    args=parser.parse_args(argv);removal=dict(reviewed=args.reviewed_cut_uuid,stage_scope=args.stage_removal_scope,from_delta=args.stage_removals_from_delta)
    if args.command=='plan':
        value=plan(args.before,args.after,args.shard_size,pilot_ranges=args.pilot_ranges.split(',') if args.pilot_ranges else None,**removal)
        if args.output:write(args.output,value)
        print(json.dumps(value,indent=2))
    elif args.command=='run-unit':
        provenance=dict(before_commit=args.before_commit,before_dir=args.before_dir,after_commit=args.after_commit,after_dir=args.after_dir)
        receipt=run_unit(args.before,args.after,args.output,args.unit,provenance=provenance,**removal)
        print(json.dumps({k:receipt[k] for k in ('unit','result_sha256','wall_seconds','tool_commit','inspected_image_digest')},indent=2))
    elif args.command=='assemble':
        print(assemble(args.before,args.after,args.units,args.output,**removal))
    else:
        print(json.dumps(verify(args.before,args.after,args.tree,args.before_drc,args.after_drc,**removal),indent=2))


if __name__=='__main__':main()
