"""Fail-closed full-board audit before promoting deterministic local copper."""
from __future__ import annotations
import argparse,collections,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE,REF_RE

TRACK_NET_RE=re.compile(r'\(net\s+"([^"]+)"\)')

def blocks(path):
    text=path.read_text();found=collections.defaultdict(dict);found['non_copper']=collections.Counter()
    for a,b in top_level_spans(text):
        block=text[a:b];kind=re.match(r'\(([A-Za-z0-9_]+)',block)
        if not kind:continue
        kind=kind[1]
        if kind not in ('segment','via','arc'):found['non_copper'][block]+=1
        if kind in ('footprint','zone','segment','via','arc'):
            key=REF_RE.search(block)[1] if kind=='footprint' and REF_RE.search(block) else UUID_RE.search(block)[1] if UUID_RE.search(block) else None
            if not key or key in found[kind]:raise ValueError(f'{kind}: missing/duplicate identity')
            found[kind][key]=block
    return found

def verify(source,candidate,receipt_path,before_ratsnest,after_ratsnest,drc_path,expected_sha):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=expected_sha:raise ValueError('source board changed since pilot')
    receipt=json.loads(receipt_path.read_text());before=blocks(source);after=blocks(candidate)
    if before['non_copper']!=after['non_copper']:
        raise ValueError('non-copper board outline/config/net/graphic/footprint/zone block changed')
    for kind in ('footprint','zone'):
        if before[kind]!=after[kind]:raise ValueError(f'{kind} geometry/identity changed')
    for kind in ('segment','via','arc'):
        if any(after[kind].get(key)!=block for key,block in before[kind].items()):raise ValueError(f'prior {kind} copper changed')
    added={key:block for kind in ('segment','via','arc') for key,block in after[kind].items() if key not in before[kind]}
    expected={row['track_uuid']:row['net'] for row in receipt['tracks_added']}
    if set(added)!=set(expected):raise ValueError('new copper UUID set differs from receipt')
    for key,block in added.items():
        match=TRACK_NET_RE.search(block)
        if not match or match[1]!=expected[key]:raise ValueError('new copper net differs from exact target')
    old=json.loads(before_ratsnest.read_text())['native_unconnected_edges'];new=json.loads(after_ratsnest.read_text())['native_unconnected_edges']
    if new>=old or old-new!=len(expected):raise ValueError('target local links did not all close in native ratsnest')
    drc=json.loads(drc_path.read_text())
    errors=[v for v in drc['violations'] if v['severity']=='error']
    if drc['kicad_version']!='10.0.6' or errors or drc['schematic_parity']:raise ValueError('native KiCad DRC/parity failed')
    return {'status':'PASS - unvalidated draft local copper only','source_sha256':expected_sha,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'new_exact_signal_tracks':len(expected),'native_unconnected_edges_before':old,'native_unconnected_edges_after':new,'native_edge_reduction':old-new,'rule_errors':0,'schematic_parity_issues':0,'prior_footprints_preserved':len(before['footprint']),'prior_zones_preserved':len(before['zone']),'prior_copper_preserved':sum(len(before[k]) for k in ('segment','via','arc'))}

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);p.add_argument('receipt',type=Path);p.add_argument('before_ratsnest',type=Path);p.add_argument('after_ratsnest',type=Path);p.add_argument('drc',type=Path);p.add_argument('expected_sha');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report=verify(a.source,a.candidate,a.receipt,a.before_ratsnest,a.after_ratsnest,a.drc,a.expected_sha)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,sort_keys=True))
if __name__=='__main__':main()
