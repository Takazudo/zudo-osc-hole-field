"""Emit diffs only. Never modifies input alternatives or adopts an output tree."""
import argparse,csv,difflib,hashlib,io,json,re,sys
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('repository',type=Path);ap.add_argument('after',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
sys.dont_write_bytecode=True;sys.path.insert(0,str(a.repository))
from scripts.schgen.core import parse,tokens,children
sha=lambda b:hashlib.sha256(b).hexdigest()
results=[]
for v in ['UNI_ROYAL/BA1','UNI_ROYAL/RevP','YAGEO/BA1','YAGEO/RevP']:
 base=a.after/v;rel='candidate/rendered/variant/sheets/sample_hold.kicad_sch';s=(base/rel).read_text();tree=parse(tokens(s))[0];libs=children(tree,'lib_symbols')[0]
 def pin_geometry(name):
  lib=next(x for x in children(libs,'symbol') if x[1]=='zudo-osc-hole-field:'+name);result=[]
  for unit in children(lib,'symbol'):
   suffix=unit[1].rsplit('_',2)[-2:]
   for pin in children(unit,'pin'):
    result.append((suffix,children(pin,'number')[0][1],children(pin,'at'),children(pin,'length'),pin[1:3]))
  return sorted(result,key=str)
 assert pin_geometry('TL074HIDR')==pin_geometry('OPA4196IDR'),'cached symbol pin geometry mismatch'
 pattern=r'^  \(symbol \(lib_id "zudo-osc-hole-field:TL074HIDR"\).*?(?=^  \(|\Z)'
 matches=list(re.finditer(pattern,s,re.M|re.S));assert len(matches)==5
 new=s
 for m in reversed(matches):
  b=m.group();assert '(property "Reference" "U110"' in b
  refs=re.findall(r'\(reference "([^"]+)"\)',b);assert set(refs)=={'U110','U210'},refs
  changed=b.replace('zudo-osc-hole-field:TL074HIDR','zudo-osc-hole-field:OPA4196IDR').replace('"TL074HIDR"','"OPA4196IDR"').replace('"C2878713"','"C2057385"').replace('https://www.ti.com/lit/ds/symlink/tl074.pdf','https://www.ti.com/lit/ds/symlink/opa4196.pdf').replace('"variant-substitution-v1"','"PROPOSED-OPA4196-COMPACT-UNADOPTED"')
  assert changed.replace('zudo-osc-hole-field:OPA4196IDR','zudo-osc-hole-field:TL074HIDR').replace('"OPA4196IDR"','"TL074HIDR"').replace('"C2057385"','"C2878713"').replace('https://www.ti.com/lit/ds/symlink/opa4196.pdf','https://www.ti.com/lit/ds/symlink/tl074.pdf').replace('"PROPOSED-OPA4196-COMPACT-UNADOPTED"','"variant-substitution-v1"')==b
  new=new[:m.start()]+changed+new[m.end():]
 changes={rel:(s,new)}
 for rel in ['candidate/source-records/candidate-bom.csv','candidate/source-records/candidate-pin-map.csv','views/source-facts.csv','views/unadopted-procurement-candidate.csv']:
  old=(base/rel).read_text();lines=old.splitlines(True);fields=next(csv.reader([lines[0]]));output=[lines[0]];hits=0
  for line in lines[1:]:
   values=next(csv.reader([line]));row=dict(zip(fields,values))
   if row['ref'] in ('U110','U210'):
    assert row['mpn']=='TL074HIDR';hits+=1
    for k,val in [('mpn','OPA4196IDR'),('value','OPA4196IDR'),('lib_id','zudo-osc-hole-field:OPA4196IDR'),('lcsc','C2057385')]:
     if k in fields:values[fields.index(k)]=val
    buf=io.StringIO();csv.writer(buf,quoting=csv.QUOTE_ALL,lineterminator='\n').writerow(values);output.append(buf.getvalue())
   else:output.append(line)
  assert hits==(28 if 'pin-map' in rel else 2),(rel,hits)
  modified=''.join(output)
  before=list(csv.DictReader(io.StringIO(old)));after=list(csv.DictReader(io.StringIO(modified)))
  for x,y in zip(before,after):
   allowed={'mpn','value','lib_id','lcsc'} if x['ref'] in ('U110','U210') else set()
   assert {k for k in x if x[k]!=y[k]}<=allowed
  assert len(before)==len(after)
  changes[rel]=(old,modified)
 patch='';record={'variant':v,'status':'PROPOSAL ONLY; input unchanged','files':{},'checks':'cached pin geometry equal;5shared units affect exactlyU110/U210;CSV pin/net fields invariant;roundtrip symbol edit;row counts invariant'}
 for rel,(old,new) in changes.items():
  patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
  record['files'][rel]={'before_sha256':sha(old.encode()),'proposed_sha256':sha(new.encode())}
  assert (base/rel).read_text()==old
 (a.output/(v.replace('/','-')+'.patch')).write_text(patch);results.append(record)
(a.output/'checks.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS:four independent proposal patches;five files each;no input mutation')
