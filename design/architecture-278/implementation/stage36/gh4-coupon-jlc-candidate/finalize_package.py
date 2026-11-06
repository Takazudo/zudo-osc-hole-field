from pathlib import Path
import hashlib, zipfile

O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fab=O/'GH4-fabrication-candidate.zip'
with zipfile.ZipFile(fab,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted((O/'fabrication').iterdir()):z.write(p,p.name)
    z.write(O/'fabrication-drawing.pdf','fabrication-drawing.pdf')
    z.write(O/'FABRICATION-NOTES.txt','FABRICATION-NOTES.txt')
with zipfile.ZipFile(fab) as z:
    assert z.testzip() is None and len(z.namelist())==14
    for p in (O/'fabrication').iterdir():assert z.read(p.name)==p.read_bytes()
files=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt' and '__pycache__' not in p.parts)
(O/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(O).as_posix()+'\n' for p in files),encoding='ascii')
out=O.parents[5]/'GH4-JLC-submission-candidate-537ab6a.zip'
# The delivery is outside the repository, in the task workspace.
assert out.parent.name=='task-4',out
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files+[O/'SHA256SUMS.txt']:z.write(p,p.relative_to(O).as_posix())
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for line in z.read('SHA256SUMS.txt').decode().splitlines():
        h,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==h
out.with_suffix('.zip.sha256').write_text(sha(out)+'  '+out.name+'\n',encoding='ascii')
print('Verified inner ZIP: '+str(fab))
print('Verified delivery: '+str(out))
print('SHA256 '+sha(out))
