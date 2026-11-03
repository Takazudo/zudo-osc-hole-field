"""Published process applicability, not a fabrication quote or acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'design/architecture-278/implementation/stage9'

def check(ok, message):
    if not ok:raise ValueError(message)

def analyze(evidence, mechanical):
    requested=evidence['present_process'];rows={r['id']:r for r in evidence['sources']}
    check(set(rows)=={'euro-mechanical','euro-current-tolerances','jlc-capabilities','pcbway-capabilities'},'published source inventory')
    check(all(not r['supplier_acceptance_of_X1'] for r in rows.values()),'general capability cannot imply X1 acceptance')
    check(all(r['authority']=='MANUFACTURER_PRIMARY'and r['availability']=='AVAILABLE'and len(r['sha256'])==64 and r['sha256']!='0'*64 for r in rows.values()),'source identity/availability')
    euro=rows['euro-current-tolerances']['facts'];jlc=rows['jlc-capabilities']['facts'];pcb=rows['pcbway-capabilities']['facts']
    check(euro['profile_dimension_plusminus_mm']==.2 and euro['profile_cutout_to_hole_position_plusminus_mm']==.2,'reviewed separate profile bounds')
    check(jlc['precision_outline_plusminus_mm']==.1 and jlc['NPTH_slot_size_plusminus_mm']==.2 and jlc['precision_minimum_dimensions_mm']==[50,50],'reviewed outline and slot applicability')
    check(pcb['shape_below_0p10_mm_column']=='Unable to make','PCBWay source table column alignment')
    current=mechanical['requested_precision_process']
    check(current['dimension_tolerance_plusminus_mm']==requested['requested_dimension_plusminus_mm'] and current['position_tolerance_plusminus_mm']==requested['requested_position_plusminus_mm'],'separate requested bounds disagree')
    t=current['dimension_tolerance_plusminus_mm']+current['position_tolerance_plusminus_mm']
    original_gap=min(p['minimum_cut_boundary_gap_mm'] for p in mechanical['actual_pad_cut_margins'])+2*t
    limit=(original_gap-requested['required_outer_land_edge_mm'])/2
    check(math.isclose(limit,requested['maximum_combined_boundary_allowance_mm'],abs_tol=1e-9),'combined contour limit no longer follows actual land gap')
    check(requested['requested_dimension_plusminus_mm']==.05 and requested['requested_position_plusminus_mm']==.05,'unreviewed requested process')
    dimensions={name:[b['outline_mm'][2]-b['outline_mm'][0],b['outline_mm'][3]-b['outline_mm'][1]]for name,b in mechanical['boards'].items()}
    standard_t=euro['profile_dimension_plusminus_mm']+euro['profile_cutout_to_hole_position_plusminus_mm']
    return {'construction':evidence['construction'],'derived_limits':{'pre_tolerance_minimum_land_gap_mm':original_gap,'maximum_combined_allowance_mm':limit,'requested_combined_allowance_mm':t,'requested_worst_land_gap_mm':original_gap-2*t,'euro_standard_combined_allowance_mm':standard_t,'euro_standard_worst_land_gap_mm':original_gap-2*standard_t,'interpretation':'Conservative additive dimensional+registration convention from Stage8; nominal outward compensation protects inward cut and twice allowance screens outward cut. Not statistical tolerance combination.'},
            'JLC_precision_size_screen':{name:{'bare_board_dimensions_mm':xy,'meets_minimum_size_only':all(v>=50 for v in xy),'precision_acceptance':False,'missing':'actual profile/cutout positional bound and tooling/panel applicability'}for name,xy in dimensions.items()},
            'published_precision_cutout_acceptance':False,'comparison_scope':'No reviewed source supplies both requested contour limits for this construction. Hole tolerances are not contour tolerances; minimum slot width is not profile accuracy. No assertion that no other supplier could do it.',
            'smallest_external_evidence_for_present':'A construction-specific supplier statement covering contour-to-land/registration datums, every cutout/notch, tool radius, FR4 thickness/layers and the combined allowance. No outreach performed.',
            'alternative_policy':'Remove precision-dependent foreign-pin passages by separating the circuit substrate from the fixed terminal plane; ordinary outline capability still requires actual data review, but is not used as proof of tight cutout clearance.',
            'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN','supplier_contacted':False,'hardware_acceptance':False}

def build():
    evidence=OUT/'process-evidence.json';mechanical=OUT.parent/'stage8/mechanical-report.json'
    r=analyze(json.loads(evidence.read_text()),json.loads(mechanical.read_text()))
    paths=[evidence,mechanical,Path(__file__),Path(__file__).with_name('test_stage9_process.py')]
    r['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}
    return r

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();body=json.dumps(build(),indent=2,sort_keys=True)+'\n';p=OUT/'process-report.json'
    if args.check:check(p.read_text()==body,'stale Stage9 process report')
    else:p.write_text(body)
    print('Stage9 published process applicability reproduced; specific precision cutout acceptance absent')
if __name__=='__main__':main()
