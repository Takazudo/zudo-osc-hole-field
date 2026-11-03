"""Bounded live-container evidence retention; never invokes a CAD executable."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import selectors
import subprocess
import time

LIMIT = 250 * 1024 * 1024
MANIFEST_LIMIT = 1024 * 1024
MANIFEST_CODE = r'''
import hashlib,json,os,pathlib,stat
root=pathlib.Path('/output'); rows=[]
for directory,dirs,files in os.walk(root,followlinks=False):
 for name in dirs+files:
  p=pathlib.Path(directory)/name; s=p.lstat()
  assert not stat.S_ISLNK(s.st_mode)
  if stat.S_ISDIR(s.st_mode): continue
  assert stat.S_ISREG(s.st_mode)
  h=hashlib.sha256()
  with p.open('rb') as f:
   while b:=f.read(65536): h.update(b)
  rows.append({'path':str(p.relative_to(root)),'size':s.st_size,'sha256':h.hexdigest()})
assert len(rows)<=4096
print(json.dumps(sorted(rows,key=lambda x:x['path']),separators=(',',':')))
'''
FILE_CODE = r'''
import os,pathlib,stat,sys
root=pathlib.Path('/output'); p=root/sys.argv[1]
assert p.resolve().is_relative_to(root)
for q in [p,*p.parents]:
 if q==root: break
 assert not q.is_symlink()
fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
assert stat.S_ISREG(os.fstat(fd).st_mode)
with os.fdopen(fd,'rb') as f:
 while b:=f.read(65536): sys.stdout.buffer.write(b)
'''


def stream(argv, limit, deadline, sink):
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    total = 0
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('retention deadline')
            if not selector.select(min(remaining, 1)):
                continue
            chunk = os.read(process.stdout.fileno(), 65536)
            if not chunk:
                break
            if total + len(chunk) > limit:
                raise ValueError('stream exceeds byte limit')
            sink(chunk)
            total += len(chunk)
        if process.wait(timeout=max(.01, deadline-time.monotonic())) != 0:
            raise ValueError('stream command failed')
        return total
    finally:
        selector.close()
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdout.close()


def validate_manifest(rows, required, limit=LIMIT):
    if not isinstance(rows, list) or not rows or len(rows) > 4096:
        raise ValueError('empty or excessive file manifest')
    names = set()
    total = 0
    for row in rows:
        name = row['path']
        path = PurePosixPath(name)
        if not name or name == '.' or '\x00' in name or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name or str(path) != name or name in names:
            raise ValueError('unsafe or duplicate manifest path')
        if type(row['size']) is not int or row['size'] < 0:
            raise ValueError('invalid size')
        digest = row['sha256']
        if not isinstance(digest,str) or len(digest)!=64 or any(x not in '0123456789abcdef' for x in digest):
            raise ValueError('invalid digest')
        names.add(name)
        total += row['size']
    if total > limit or not set(required) <= names:
        raise ValueError('missing required evidence or total byte quota exceeded')
    return total


def retain(container, destination, required, *, seconds=60, limit=LIMIT, runner=stream):
    destination = Path(destination)
    staging = destination.with_name(destination.name+'.partial')
    if destination.exists() or staging.exists():
        raise ValueError('fresh destination required')
    deadline = time.monotonic()+seconds
    chunks = []
    runner(['docker','exec',container,'python3','-c',MANIFEST_CODE], MANIFEST_LIMIT, deadline, chunks.append)
    rows = json.loads(b''.join(chunks))
    total = validate_manifest(rows,required,limit)
    staging.mkdir(parents=False)
    for row in rows:
        path = staging / row['path']
        path.parent.mkdir(parents=True,exist_ok=True)
        digest = hashlib.sha256()
        with path.open('xb') as output:
            def write(chunk):
                output.write(chunk)
                digest.update(chunk)
            size = runner(['docker','exec',container,'python3','-c',FILE_CODE,row['path']],row['size'],deadline,write)
            output.flush()
            os.fsync(output.fileno())
        if size != row['size'] or digest.hexdigest() != row['sha256']:
            raise ValueError('retained size/hash mismatch: '+row['path'])
    if {str(p.relative_to(staging)) for p in staging.rglob('*') if p.is_file()} != {r['path'] for r in rows}:
        raise ValueError('retained membership mismatch')
    after = []
    runner(['docker','exec',container,'python3','-c',MANIFEST_CODE], MANIFEST_LIMIT, deadline, after.append)
    if json.loads(b''.join(after)) != rows:
        raise ValueError('source inventory changed during retention')
    # Renaming this one directory adds no second archive/extraction copy.
    staging.rename(destination)
    return {'status':'VERIFIED_HASHED_COPY','bytes':total,'files':rows,'cleanup_permitted':True}
