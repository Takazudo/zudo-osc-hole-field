#!/usr/bin/env python3
"""Upper bound on translated full-module copper replay for osc-jack."""
from __future__ import annotations
import argparse,collections,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def build(board_id):
    manifest=json.loads((ROOT/'design/partition/partition.json').read_text())
    board_key=next(b['board_key'] for b in manifest['boards'] if b['id']==board_id)
    physical=json.loads((ROOT/'design/reports/io-partition.json').read_text())['physical_packages']
    locations={p['ref']:p for p in json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text())['placements']}
    families=collections.defaultdict(lambda:collections.defaultdict(list))
    for part in physical:
        point=locations[part['ref']]
        if point['board']==board_key and not part['panel_uid']:
            families[part['family']][part['instance']].append((part['footprint'],point['side'],round(point['x_mm'],4),round(point['y_mm'],4)))
    comparisons=[]
    for family,instances in sorted(families.items()):
        if len(instances)<2:continue
        source=sorted(instances)[0]
        for target in sorted(instances)[1:]:
            shifts=collections.Counter()
            for af,aside,ax,ay in instances[source]:
                for bf,bside,bx,by in instances[target]:
                    if af==bf and aside==bside:shifts[(round(bx-ax,4),round(by-ay,4))]+=1
            (shift,count)=shifts.most_common(1)[0] if shifts else ((0,0),0)
            comparisons.append({'family':family,'source':source,'target':target,'source_free_packages':len(instances[source]),
                'target_free_packages':len(instances[target]),'best_translation_mm':list(shift),
                'matching_footprint_face_centres_upper_bound':count,'whole_module_translation_possible':count==len(instances[source])==len(instances[target])})
    return {'schema_version':1,'board_id':board_id,'method':'For every same-footprint, same-face source/target pair, count coincident centres under each translation. The maximum is an upper bound on full-module pad-identical copper replication.',
        'comparisons':comparisons,'whole_module_translation_pairs':sum(x['whole_module_translation_possible'] for x in comparisons),
        'status':'Measured source-geometry incompatibility with whole-module translation; local subcluster replay would need independent pad/net/DRC proof.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('board_id');args=parser.parse_args()
    report=build(args.board_id);path=ROOT/'boards'/args.board_id/'reports/replication-feasibility.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(f"{len(report['comparisons'])} repeated-module comparisons; {report['whole_module_translation_pairs']} full translations")
