"""Inventory planar copper lengths; these are not electrical loop lengths."""
from pathlib import Path
import argparse
import json
import math
from collections import defaultdict
from identity_guard import digest, kind, copper_contract, top_level_spans


def extract(path, nets):
    raw=path.read_text();totals={n:{'segment_centerline_mm':0.,'segments':0,'vias':0,'by_layer_mm':defaultdict(float)} for n in nets}
    for a,b in top_level_spans(raw):
        part=raw[a:b]
        if kind(part)=='arc':raise ValueError('arc length extraction is unsupported')
        if kind(part) not in ('segment','via'):continue
        k,uid,shape,net=copper_contract(part)
        if net not in totals:continue
        row=totals[net]
        if k=='via':row['vias']+=1
        else:
            length=math.dist(shape[0],shape[1])/1000000
            row['segments']+=1;row['segment_centerline_mm']+=length;row['by_layer_mm'][shape[-1]]+=length
    return {'board_sha256':digest(raw),'nets':totals}


def metrics(baseline,candidate,receipt_path,output):
    receipt=json.loads(receipt_path.read_text());nets=receipt['private_net_owners']
    before,after=extract(baseline,nets),extract(candidate,nets)
    if before['board_sha256']!=receipt['canonical_sha256']:raise ValueError('baseline binding')
    feedback={}
    for pin in ('6','9','13'):
        matches=[p['net'] for pose in receipt['poses'] if pose['ref']=='U3102' for p in pose['pads'] if p['pin']==pin]
        # Exact audited pad net names, never inferred schematic aliases.
        if len(matches)!=1:raise ValueError('feedback owner identity missing/ambiguous')
        net=matches[0]
        if net not in nets:raise ValueError('feedback outside disturbed net scope')
        feedback[pin]={'net':net,'before':before['nets'][net],'after':after['nets'][net]}
    result={'baseline':before,'candidate':after,'U3102_feedback_nets_by_pin':feedback,
            'limits':'Sum of planar segment centerlines per net, including branches/overlaps. Excludes pad internal paths, via vertical distance and plane spread; not closed-loop length, loop area, inductance, impedance or stability qualification.'}
    output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('baseline','candidate','receipt','output'):p.add_argument(n,type=Path)
    a=p.parse_args();metrics(a.baseline,a.candidate,a.receipt,a.output)
