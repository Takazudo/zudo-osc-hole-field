"""Complete B2 source/native identity gate, with explicit retirement/proposal proofs."""
from pathlib import Path
from collections import Counter
import argparse,json,sys,re
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import inventory,compare,digest,structure_matches,top_level_spans,kind,value
from acceptance import connectivity_gate
BASE=ROOT/'.circuit-cache/stage42-full-b1-fresh/osc-jack-left.kicad_pcb'
REVIEWED_BRANCH_PROOF_SHA256='54c9b325e66215704d65d4732dfcfb553414ff7aad63496617d6d2f8aed10066'
BASE_HASH='975cd15d5ba69b9695e8d32a575a289306a27f1ea17d6b5f7a5819071dc5505b'

def reviewed_proof(raw):
    if digest(raw)!=REVIEWED_BRANCH_PROOF_SHA256:raise ValueError('unreviewed branch proof')
    return json.loads(raw)

def check_auxiliary(candidate,baseline):
    def inventory(folder):
        items=[*folder.glob('sheets/**/*'),folder/'fp-lib-table',folder/'sym-lib-table']
        return {str(p.relative_to(folder)):p.read_bytes() for p in items if p.is_file()}
    if inventory(candidate)!=inventory(baseline):raise ValueError('recursive schematic/library-table change')
    return True

def contract(r):
    if r['kind']=='segment':shape=(tuple(r['start_nm']),tuple(r['end_nm']),(r['width_nm'],),r['layer'])
    elif r['kind']=='via':shape=(tuple(r['at_nm']),(r['diameter_nm'],),(r['drill_nm'],),tuple(r['layers']))
    else:raise ValueError('unsupported copper')
    return r['kind'],r['uuid'],shape,r['net']

def bound_retirements(receipt,raw,proof):
    if digest(raw)!=BASE_HASH or receipt['baseline_sha256']!=BASE_HASH or proof['baseline_sha256']!=BASE_HASH:raise ValueError('baseline binding')
    if receipt['retired_local_supply_copper']!=proof['screened_retirements']:raise ValueError('shared retirement differs from proof')
    plan=json.loads((ROOT/'design/architecture-278/implementation/stage40/mult-copper-plan/plan.json').read_text())
    refs={v['B2_ref'] for v in plan['candidate_B1'].values()};moved=refs-{'J309','J409','J310','J410','D309'}
    if set(receipt['moved'])!=moved or set(proof['scope_refs'])!=moved:raise ValueError('B2 scope')
    moves=[m for m in plan['moves'] if m['ref'] in moved]
    nets={p['net'] for m in moves for p in m['old']['pads']}-{'AGND','+12V','-12V','+5V',None,''}-{p['native_net'] for p in plan['NC_equivalence']}
    expected=[r for r in plan['private_net_retire_copper'] if r['net'] in nets]
    if receipt['retired_private_copper']!=expected or set(receipt['private_net_owners'])!=nets:raise ValueError('private scope/retirement')
    rows=receipt['retired_private_copper']+receipt['retired_local_supply_copper'];by={}
    for index,(a,z) in enumerate(top_level_spans(raw)):
        p=raw[a:z]
        if kind(p) in ('segment','via'):by.setdefault(digest(p),[]).append((index,kind(p),value(p,'uuid'),value(p,'net')))
    # Stage40 indices refer to canonical order, which changes in accepted B1.
    # Exact raw hash/UUID/kind/net binds those private occurrences; local proof
    # indices refer directly to this accepted Stage42 baseline.
    for r in rows:
        matches=by.get(r['sha256'],[])
        if len(matches)!=1 or matches[0][1:]!=(r['kind'],r['uuid'],r['net']):raise ValueError('ambiguous retirement occurrence')
        if r in receipt['retired_local_supply_copper'] and matches[0][0]!=r['index']:raise ValueError('local retirement index')
    if len({r['sha256'] for r in rows})!=len(rows) or Counter(receipt['retired_hashes'])!=Counter(r['sha256'] for r in rows):raise ValueError('retirement hash multiset')
    return rows

def audit(path,receipt_path,proof_path,proposals):
    import pcbnew
    from native_guard import check_native
    raw0,raw=BASE.read_text(),path.read_text();receipt=json.loads(receipt_path.read_text());proof=reviewed_proof(proof_path.read_text())
    if receipt['branch_proof_sha256']!=digest(proof_path.read_text()) or digest(proof_path.read_text())!=REVIEWED_BRANCH_PROOF_SHA256:raise ValueError('reviewed branch proof binding')
    retired=bound_retirements(receipt,raw0,proof)
    before,after=inventory(raw0),inventory(raw);rows=[]
    for p in proposals:
        d=json.loads(p.read_text())
        if d['removed_uuids']:raise ValueError('additive route required')
        rows.extend(d['copper'])
    ids=[r['uuid'] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate new UUID')
    allowed=set(receipt['private_net_owners'])|{'AGND','+12V','-12V','+5V'}
    if any(r['net'] not in allowed for r in rows):raise ValueError('new copper outside B2 nets')
    actual=Counter({k:n for k,n in after['native_contract'].items() if k[1] in ids})
    if actual!=Counter(contract(r) for r in rows):raise ValueError('proposal geometry/net mismatch')
    new=[k for k,n in after['copper'].items() if k[1] in ids for _ in range(n)]
    result=compare(before,after,[r['sha256'] for r in retired],new)
    if not result['accepted'] or not structure_matches(before,after,receipt['prepared_footprint_hashes']):raise ValueError('source identity gate: '+json.dumps(result))
    if any(after['footprints'][r]!=h for r,h in before['footprints'].items() if r not in receipt['moved']):raise ValueError('foreign/fixed footprint changed')
    for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru'):
        if path.with_suffix(suffix).read_bytes()!=BASE.with_suffix(suffix).read_bytes():raise ValueError('project/rules/schematic changed')
    check_auxiliary(path.parent,BASE.parent)
    def properties(text):
        result={}
        for a,z in top_level_spans(text):
            part=text[a:z]
            if kind(part)!='footprint':continue
            fields=re.findall(r'\(property\s+("(?:[^"\\]|\\.)*")\s+("(?:[^"\\]|\\.)*")',part)
            values={json.loads(k):json.loads(v) for k,v in fields}
            result[values['Reference']]=values
        return result
    if properties(raw0)!=properties(raw):raise ValueError('BOM/reference property change')
    b=pcbnew.LoadBoard(str(path));check_native(b,raw);b.GetConnectivity().RecalculateRatsnest();check_native(b,raw)
    from packages import verify
    package_hashes=verify(BASE,b,receipt['moved']);check_native(b,raw)
    output={'pose_only_packages':package_hashes,'accepted_identity_only':True,'raw_sha256':digest(raw),'baseline_sha256':BASE_HASH,'receipt_sha256':digest(receipt_path.read_text()),'branch_proof_sha256':digest(proof_path.read_text()),'proposal_sha256':[digest(p.read_text()) for p in proposals],'new_objects':len(rows),'retired_objects':len(retired),'checks':result['checks'],'foreign_fixed_footprints_byte_equal':True,'all_footprint_properties_unchanged':True,'recursive_schematics_and_library_tables_unchanged':True,'native_open_edges':b.GetConnectivity().GetUnconnectedCount(False)}
    path.with_name('identity-audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n');print(json.dumps(output))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('board','receipt','proof'):p.add_argument(n,type=Path)
    p.add_argument('--proposal',type=Path,action='append',default=[]);a=p.parse_args();audit(a.board,a.receipt,a.proof,a.proposal)
