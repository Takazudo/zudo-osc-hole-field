"""Exact retained non-OSC occupied/service inventory; no33-function redesign."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'design/architecture-278/implementation/stage4'

def build():
    names=['design/architecture-278/source-ledger.json','design/partition/floorplan-candidate.json','design/reports/io-partition.json','design/partition/mechanical-candidate.json','design/architecture-278/implementation/assembly-report.json','design/architecture-278/implementation/stage4/mechanical-input.json']
    raw={n:(ROOT/n).read_bytes()for n in names};ledger,floor,partition,mechanical,assembly,config=[json.loads(raw[n])for n in names]
    others={f['id']for f in ledger['functions']if f['family']!='OSC'};assert len(others)==28
    parts={p['ref']:p for p in ledger['packages']};poses={p['ref']:p for p in floor['placements']};physical={p['ref']:p for p in partition['physical_packages']}
    units=defaultdict(list)
    for i,u in enumerate(ledger['package_units']):units[u['ref']].append((i,u))
    shared={p['ref']:p for p in assembly['shared_middle_placements']};dx,dy=config['shared_group_translation_mm']
    rows=[]
    for ref,p in parts.items():
        if p['instance']not in others|{'POWER','OCTAVE_REF'}:continue
        group='other28' if p['instance']in others else p['instance']
        pos=poses[ref];pp=physical[ref]
        assert set(p['units'])=={u['unit']for _,u in units[ref]},'lost wholepackage units '+ref
        assert pos['board']==p['current_board'],'retainedboard mismatch '+ref
        target=p['decouples_ref'];assert target is None or target in parts,'missing bypass target '+ref
        proposed=None
        if group=='OCTAVE_REF':
            q=shared[ref];proposed={'board':'candidate-shared-middle','side':q['side'],'depth_mm':50,'origin_mm':[q['origin_mm'][0]+dx,q['origin_mm'][1]+dy],
                'box_mm':[q['box_mm'][0]+dx,q['box_mm'][1]+dy,q['box_mm'][2]+dx,q['box_mm'][3]+dy],
                'pads_mm':{pin:[[x+dx,y+dy]for x,y in xy]for pin,xy in q['pads_mm'].items()},'status':'CONDITIONAL rigidgroup sourceproposal; body heights/board/support/routing not qualified'}
        rows.append({'ref':ref,'population_group':group,'function_or_service':p['instance'],'mpn':p['mpn'],'footprint':pp['footprint'],'dnp':p['dnp'],
            'units':p['units'],'unit_pin_record_indices':[i for i,_ in units[ref]],'bypass_target':target,
            'historical_placement':{'board':pos['board'],'side':pos['side'],'origin_mm':[pos['x_mm'],pos['y_mm']],'rotation_deg':pos['rotation_deg'],'courtyard_mm':pos['courtyard_mm'],'footprint_sha256':pp['courtyard']['footprint_sha256']},
            'new_candidate_placement':proposed,'new_candidate_occupied_solid':None})
    counts=Counter(p['population_group']for p in rows);assert counts=={'other28':4766,'POWER':13,'OCTAVE_REF':30},counts
    other_k=[p for p in rows if p['population_group']=='other28'and p['historical_placement']['board']=='K'];assert len(other_k)==2572
    hashes={n:hashlib.sha256(b).hexdigest()for n,b in raw.items()};hashes[str(Path(__file__).relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {'status':'EXACT RETAINED PACKAGE INVENTORY; candidate occupied solids UNKNOWN','source_sha256':hashes,'counts':dict(counts),'package_count':len(rows),'unit_count':sum(len(p['unit_pin_record_indices'])for p in rows),'DNP_count':sum(p['dnp']for p in rows),
        'unit_pin_record_source':'source_sha256-bound design/architecture-278/source-ledger.json package_units zero-based indices; complete pins/nets/NC and unit ownership retained by reference','row_interpretation':'Source exact XY and whole package retained. Historical position is not a new-stack solid. DNP is explicitly not a fitted-body claim.','rows':rows,'retained_board_geometry_and_reserves':ledger['boards'],'retained_support_and_load_paths':mechanical,
        'scenario_distinction':{'canonical_source':'Unchanged under both physicalscenarios; keepingfiles is not a physicalassembly decision.',
            'old_K_physically_retained':{'source_depth_mm':[100,101.6],'rear_allowance_end_mm':106.6,'candidate_cover_mm':105,'effect':'Conflicts with allfive proposed directcard withdrawal sweeps and extends beyond105cover allowance; cannot claim candidatecores rear-most.'},
            'old_K_physically_replaced':{'other_function_K_packages_to_rehost':2572,'POWER_packages_to_rehost':13,'shared_reference_packages_translated_as_group':30,'effect':'Must assign wholepackages/units/bypass/rails/returns to newboards or conservativevolumes, preserve supportandservicepaths. Noassignedvolume for2585other/POWERpackages exists in this task.'}},
        'dependency_boundary':['No redesign of33functions performed. This is a4809package retained-coordinate inventory, not an areamultiplier or a newpartition.',
            'Reusingphysicaloldfrontboards also needs an explicitpopulation/partition/interface plan: oldJL/JR/P contain OSC andotherfunctionparts; newOSCfrontcopies cannot implyduplicatefixedhardware.',
            'Newstackother28/POWERsolidpositions remainnull; unplaced doesnotmeanfree. Current exacthistoricalXY remainsavailableforconservativeexclusions and dependency review.',
            'Complete shared30translation is reversible candidate sourceonly; sourceboardoutlines, mounting, heat, routing andnative/physicalfit remainOPEN.'],
        'native':'NOT RUN','physical':'NOT RUN'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();data=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n';p=OUT/'occupied-report.json'
    if args.check:assert p.read_text()==data,'stale occupied inventory'
    else:p.write_text(data)
    print('4809wholepackages',r['unit_count'],'unitrecords;4766other+13POWER+30shared;newoccupiedsolidsUNKNOWN')
if __name__=='__main__':main()
