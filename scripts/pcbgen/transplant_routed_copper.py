"""Recover new SES copper without importing prepared-board owner changes.

Writes a disposable candidate only. Native DRC/parity, warning comparison,
and a strict complete native ratsnest reduction are separate promotion gates.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.verify_local_links import blocks,TRACK_NET_RE

def transplant(source,prepared,routed,output,receipt):
    if output.resolve() in (source.resolve(),prepared.resolve(),routed.resolve()):
        raise ValueError('candidate must be a separate disposable file')
    original=blocks(source);before=blocks(prepared);after=blocks(routed)
    # Import must retain the complete prepared owner state and every prior
    # copper block. Filled plane polygons may change during native refill;
    # none of those polygons will be copied into the candidate.
    if before['footprint']!=after['footprint']:
        raise ValueError('SES changed prepared footprints')
    if set(before['zone'])!=set(after['zone']):
        raise ValueError('SES changed prepared zone identities')
    for kind in ('segment','via','arc'):
        if any(after[kind].get(key)!=value for key,value in before[kind].items()):
            raise ValueError(f'SES changed existing prepared {kind}')
        if set(original[kind])!=set(before[kind]):
            raise ValueError(f'prepare changed existing {kind} identities')
        for key,value in original[kind].items():
            normalized=lambda text: re.sub(r'\n\s*\(locked yes\)','',text)
            if normalized(value)!=normalized(before[kind][key]):
                raise ValueError(f'prepare changed existing {kind} geometry/net')
    net_names=set(re.findall(r'\(net\s+"([^"\n]+)"\)',source.read_text()))
    new=[];identities=set().union(*(set(original[k]) for k in ('footprint','zone','segment','via','arc')))
    for kind in ('segment','via','arc'):
        for key,value in sorted(after[kind].items()):
            if key in before[kind]:continue
            if key in identities:raise ValueError('new copper UUID collision')
            match=TRACK_NET_RE.search(value)
            if not match or match[1] not in net_names:raise ValueError('new copper net absent from canonical board')
            identities.add(key);new.append((kind,key,match[1],value))
    if not new:raise ValueError('SES produced no new copper')
    text=source.read_text();end=text.rfind(')')
    if end<0 or text[end+1:].strip():raise ValueError('unexpected board terminator')
    output.write_text(text[:end]+''.join('\t'+value+'\n' for _,_,_,value in new)+text[end:])
    candidate=blocks(output)
    if candidate['non_copper']!=original['non_copper']:
        raise ValueError('transplant changed canonical owner blocks')
    for kind in ('segment','via','arc'):
        if any(candidate[kind].get(k)!=v for k,v in original[kind].items()):
            raise ValueError('transplant changed canonical prior copper')
    report={'status':'DISPOSABLE DRAFT; native promotion gates pending',
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'prepared_sha256':hashlib.sha256(prepared.read_bytes()).hexdigest(),
            'routed_sha256':hashlib.sha256(routed.read_bytes()).hexdigest(),
            'candidate_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'all_canonical_non_copper_blocks_preserved':True,
            'all_canonical_prior_copper_blocks_preserved':True,
            'added':[{'kind':kind,'uuid':key,'net':net} for kind,key,net,_ in new]}
    receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('prepared',type=Path);p.add_argument('routed',type=Path);p.add_argument('output',type=Path);p.add_argument('receipt',type=Path);a=p.parse_args()
    report=transplant(a.source,a.prepared,a.routed,a.output,a.receipt)
    print(f'Disposable copper transplant: {len(report["added"])} new items; native gates pending')

if __name__=='__main__':main()
