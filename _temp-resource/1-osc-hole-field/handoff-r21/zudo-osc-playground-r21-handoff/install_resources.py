#!/usr/bin/env python3
"""Safe, create-only content overlay for an officially initialized circuit-doc host.
Default is dry run. No package, workflow, inventory or generator-owned files are modified.
Existing identical payloads are skipped; a differing file or symlink aborts before writes.
"""
from __future__ import annotations
import argparse,hashlib,json,os,tempfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
BEGIN='<!-- osc-playground-r21-handoff:start -->';END='<!-- osc-playground-r21-handoff:end -->'
def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def contained(root:Path,path:Path)->None:
    try:path.resolve().relative_to(root.resolve())
    except ValueError:raise ValueError(f'Path escapes project: {path}')
    cur=path
    while cur!=root:
        if cur.is_symlink():raise ValueError(f'Symlink not accepted: {cur}')
        if cur==cur.parent:break
        cur=cur.parent

def atomic(path:Path,data:bytes)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def plan(target:Path,payload:Path)->dict:
    if target.is_symlink():raise ValueError('Target itself must not be a symlink')
    target=target.resolve()
    for rel in ['circuit.config.ts','circuit/WORKFLOW.md','package.json','circuit/publication/assets.json','doc/src/content/docs/project/index.mdx','doc/src/content/docs/project/next-actions.mdx']:
        p=target/rel;contained(target,p)
        if not p.is_file():raise ValueError(f'Not a complete initialized circuit-doc host: missing {rel}')
    manifest=json.loads((target/'package.json').read_text())
    deps={**manifest.get('dependencies',{}),**manifest.get('devDependencies',{})}
    if '@takazudo/zudo-circuit-doc' not in deps:raise ValueError('Official runtime dependency absent; refusing to treat an arbitrary folder as a host')
    if not payload.is_dir():raise ValueError(f'Missing payload {payload}')
    writes=[];skipped=[]
    for src in sorted(payload.rglob('*')):
        if src.is_symlink():raise ValueError(f'Symlink in payload {src}')
        if not src.is_file():continue
        rel=src.relative_to(payload).as_posix()
        if rel.startswith(('doc/src/content/docs/components/','doc/public/assets/component-previews/','.claude/','node_modules/','circuit/generated/')):raise ValueError(f'Generator/evidence-owned path in overlay: {rel}')
        out=target/rel;contained(target,out);data=src.read_bytes()
        if out.exists():
            if not out.is_file() or out.read_bytes()!=data:raise ValueError(f'Collision; existing file preserved: {rel}')
            skipped.append(rel)
        else:writes.append({'path':rel,'new':data,'old':None})
    for rel,link,title in [
        ('doc/src/content/docs/project/index.mdx','./osc-overview.mdx','Oscillator playground R21 project brief'),
        ('doc/src/content/docs/project/next-actions.mdx','./osc-next-actions.mdx','Oscillator playground local next actions')]:
        p=target/rel;old=p.read_bytes();text=old.decode('utf-8')
        insertion=f'{BEGIN}\n\n## zudo-osc-playground handoff\n\n[{title}]({link}). Read this project-specific handoff after the canonical circuit workflow.\n\n{END}'
        if BEGIN in text:
            if insertion not in text:raise ValueError(f'Managed link block changed; reconcile manually: {rel}')
        else:writes.append({'path':rel,'new':(text.rstrip()+'\n\n'+insertion+'\n').encode(),'old':old})
    rel='circuit/publication/assets.json';p=target/rel;old=p.read_bytes();a=json.loads(old)
    if a.get('schema_version')!=1 or not isinstance(a.get('assets'),list):raise ValueError('Unknown publication allowlist schema; not upgraded automatically')
    entries={x.get('path') for x in a['assets']};changed=False
    for src in sorted((payload/'doc/public').rglob('*')):
        if not src.is_file():continue
        name=src.relative_to(payload/'doc/public').as_posix()
        if name not in entries:a['assets'].append({'path':name,'reason':'R21 authored oscillator-playground preview / diagram / print proof. Not approved component CAD or manufacturing evidence.'});changed=True
    if changed:writes.append({'path':rel,'new':(json.dumps(a,ensure_ascii=False,indent=2)+'\n').encode(),'old':old})
    for w in writes:contained(target,target/w['path'])
    return {'target':target,'writes':writes,'skipped':skipped}

def apply(p:dict)->None:
    target=p['target'];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');log=target/'project/osc-playground-import-log'/stamp
    # Recheck ALL observed files before making the first change.
    for w in p['writes']:
        dst=target/w['path'];contained(target,dst)
        actual=dst.read_bytes() if dst.is_file() else None
        if actual!=w['old'] or (dst.exists() and not dst.is_file()):raise ValueError(f'Concurrent change: {w["path"]}')
    done=[]
    try:
        for w in p['writes']:
            dst=target/w['path']
            if w['old'] is not None:atomic(log/'before'/w['path'],w['old'])
            atomic(dst,w['new']);done.append(w)
        if done:atomic(log/'receipt.json',(json.dumps({'scope':'Content overlay only, not official runtime or hardware validation','files':[{'path':w['path'],'sha256':digest(w['new']),'replaced_authored_entry':w['old'] is not None} for w in done]},indent=2)+'\n').encode())
    except Exception:
        for w in reversed(done):
            dst=target/w['path']
            if w['old'] is None:dst.unlink(missing_ok=True)
            else:atomic(dst,w['old'])
        raise

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('target',type=Path);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    try:p=plan(args.target,ROOT/'payload')
    except (ValueError,OSError,json.JSONDecodeError) as e:raise SystemExit(str(e))
    print('Target:',p['target']);print('Identical files skipped:',len(p['skipped']));print('Files to create/update:',len(p['writes']))
    for w in p['writes']:print(('LINK/ALLOWLIST ' if w['old'] is not None else 'CREATE ')+w['path'])
    if args.apply:apply(p);print('Imported. Run canonical circuit checks locally; no runtime or hardware validation is implied.')
    else:print('Dry run only. Add --apply after reviewing the plan.')
if __name__=='__main__':main()
