"""Export disposable/canonical schematics read-only and compare complete pin graphs.
No ERC, DRC, PCB generation or hardware acceptance is implied.
"""
from pathlib import Path
import json,subprocess,sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from proposal import ROOT,PROJECT,specification,prepare,sha,sig,require,write,run as proposal_run
from scripts.schgen.verify_netlist import expected_pin_nets,exported_pin_nets

def compare(before,after,expected_before,expected_after,removed_refs):
 require(before==expected_before,'canonical native/spec pin mismatch')
 require(after==expected_after,'candidate native/spec pin mismatch')
 require(after=={k:v for k,v in before.items() if k[0] not in removed_refs},'native retained pin/net loss')
 return True

def export(folder,output):
 command=['kicad-cli','sch','export','netlist','--format','kicadsexpr','-o',str(output.relative_to(ROOT)),str((folder/(PROJECT+'.kicad_sch')).relative_to(ROOT))]
 require(not output.exists(),'refuse overwrite native export')
 inputs={str(p.relative_to(ROOT)):sha(p) for p in sorted(folder.rglob('*.kicad_sch'))}
 result=subprocess.run(command,cwd=ROOT,check=False,capture_output=True,text=True)
 require({p:sha(ROOT/p) for p in inputs}==inputs,'schematic mutation during export')
 receipt={'command':command,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'input_schematic_sha256':inputs,'output_sha256':sha(output) if output.exists() else None}
 write(HERE/'evidence'/(output.stem+'.execution.json'),receipt)
 require(result.returncode==0,'native export failed; receipt retained')
 return receipt

def run(check=False):
 proposal_run(None,True)
 families,instances=specification();new,proposal=prepare(families,instances)
 stored=json.loads((HERE/'proposal.json').read_text())
 require(all(stored[k]==v for k,v in proposal.items()),'proposal drift')
 cache=ROOT/'.circuit-cache/stage54';candidate=ROOT/'.circuit-cache/stage54-candidate';paths=[cache/'canonical-native.net',cache/'candidate-native.net']
 version=subprocess.check_output(['kicad-cli','version'],text=True).strip();require(version=='10.0.6','oracle version')
 for folder,path in zip([ROOT/'schematic',candidate],paths):
  hashes=stored['canonical_schematic_sha256' if folder==ROOT/'schematic' else 'candidate_schematic_sha256']
  require(all(sha(folder/name)==value for name,value in hashes.items()),'rendered schematic byte binding')
  if not check:export(folder,path)
  receipt=json.loads((HERE/'evidence'/(path.stem+'.execution.json')).read_text())
  expected=['kicad-cli','sch','export','netlist','--format','kicadsexpr','-o',str(path.relative_to(ROOT)),str((folder/(PROJECT+'.kicad_sch')).relative_to(ROOT))]
  require(receipt['command']==expected and receipt['returncode']==0 and receipt['output_sha256']==sha(path),'export receipt binding')
  require(receipt['input_schematic_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sorted(folder.rglob('*.kicad_sch'))},'complete source roster binding')
 before,after=[exported_pin_nets(p.read_text()) for p in paths];old_expected=expected_pin_nets(families,instances);new_expected=expected_pin_nets(new,instances)
 compare(before,after,old_expected,new_expected,set(proposal['removed_refs']))
 selected={r:sorted([pin,net] for (ref,pin),net in before.items() if ref==r) for r in proposal['removed_refs']}
 result={'status':'PASS native exported pin connectivity only; unadopted removal proposal','oracle':version,'complete_baseline_spec_parity':True,'complete_candidate_spec_parity':True,'all_surviving_native_pin_nets_unchanged':True,'before_pin_count':len(before),'after_pin_count':len(after),'removed_pin_count':len(before)-len(after),'retained_pin_net_sha256':sig(sorted((r,p,n) for (r,p),n in after.items())),'removed_native_pin_nets':selected,'export_sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths},'limits':'No native ERC/DRC or physical test run for proposal. Canonical schematic/PCB remains unchanged. Signal function equivalence is connectivity-level, not analog qualification.'}
 require(result['retained_pin_net_sha256']==proposal['retained_pin_net_sha256'],'source/native comparison signature')
 if check:require(json.loads((HERE/'native-audit.json').read_text())==result,'native audit replay drift')
 else:write(HERE/'native-audit.json',result)
 print('PASS native complete retained-pin graph; only12idle quads+24owned bypasses removed')
if __name__=='__main__':run('--check' in sys.argv)
