"""Bounded terminal-extension inventory; no full routing or electrical acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'design/architecture-278/implementation/stage9'

def need(ok,message):
    if not ok:raise ValueError(message)

def analyze(support,baseline):
    packages=baseline['packages']
    refs=('J809','J909','J1009','D809','D909','D1009','SW608')
    expected={(ref,pin):net for ref in refs for pin,net in packages[ref]['pins'].items() if net is not None}
    extensions=support['terminal_extensions']
    lands={(r['ref'],r['pin']):r for r in support['terminal_lands']}
    need(len(support['terminal_lands'])==15 and set(lands)==set(expected),'complete target land inventory')
    need(support['added_mating_interfaces']==0,'no added terminal mating interfaces')
    nc=support['retained_NC_terminals']
    need(len(nc)==3 and {(r['ref'],r['pin'],r['net'])for r in nc}=={(ref,'TN',None)for ref in ('J809','J909','J1009')},'retained jack NC inventory')
    led_lands={(r['ref'],r['pin']):r for r in support['LED_wire_lands']}
    need(len(support['LED_wire_lands'])==6 and set(led_lands)=={k for k in expected if k[0].startswith('D')},'LED local wire land inventory')
    need(len(extensions)==15 and {(r['ref'],r['pin']):r['net']for r in extensions}==expected,'complete exact terminal pin/net inventory')
    rows=[]
    for row in extensions:
        ref,pin=row['ref'],row['pin'];source=packages[ref]
        need(all(len(row[k])==3 and all(isinstance(v,(int,float))and math.isfinite(v)for v in row[k])for k in ('source_terminal_xyz_mm','from_xyz_mm','to_xyz_mm')),'finite terminal XYZ')
        need(all(isinstance(row[k],(int,float))and math.isfinite(row[k])and row[k]>=0 for k in ('wire_nominal_mm','wire_tolerance_mm','minimum_geometric_slack_mm')),'finite nonnegative wire values')
        need(source['pads_xyz_mm'][pin]==[row['source_terminal_xyz_mm']],'extension detached from retained source datum')
        need(row['to_xyz_mm'][2]==35,'unreviewed core terminal plane')
        need(lands[ref,pin]['xyz_mm']==row['to_xyz_mm'] and lands[ref,pin]['net']==row['net'],'terminal wire target detached from land')
        if not ref.startswith('D'):need(row['from_xyz_mm']==row['source_terminal_xyz_mm'] and row['local_terminal_copper_mm']==0,'direct tail datum/allocation drift')
        else:
            a,b=row['source_terminal_xyz_mm'],row['from_xyz_mm']
            need(led_lands[ref,pin]['xyz_mm']==b and led_lands[ref,pin]['net']==row['net'],'LED wire detached from local land')
            need(b[2]==21.6 and math.isclose(row['local_terminal_copper_mm'],abs(a[0]-b[0])+abs(a[1]-b[1])+1.6,abs_tol=1e-9),'LED local copper/barrel allocation drift')
        nominal,tolerance=row['wire_nominal_mm'],row['wire_tolerance_mm']
        need(nominal==35 and tolerance==3,'unreviewed terminal wire allocation')
        distance=math.dist(row['from_xyz_mm'],row['to_xyz_mm']);slack=nominal-tolerance-distance
        points=row['proposed_wire_points_xyz_mm']
        need(len(points)>=2 and points[0]==row['from_xyz_mm']and points[-1]==row['to_xyz_mm']and all(len(p)==3 and all(isinstance(v,(int,float))and math.isfinite(v)for v in p)for p in points),'proposed wire polyline endpoint/finite geometry')
        developed=sum(math.dist(a,b)for a,b in zip(points,points[1:]))
        need(math.isclose(developed,row['proposed_developed_wire_mm'],abs_tol=1e-9)and math.isclose(nominal-tolerance-developed,row['minimum_proposed_route_slack_mm'],abs_tol=1e-9)and nominal-tolerance-developed>=10,'proposed route length/slack')
        need(slack>=10 and math.isclose(slack,row['minimum_geometric_slack_mm'],abs_tol=1e-8),'terminal allocation/slack below proposed10mm or mismatch')
        if ref.startswith('J'):
            role='external sleeve return; sharing with local/middle AGND unknown' if pin=='S' else ('output load AND remote feedback common branch' if ref=='J1009' else 'external input before ADG5412F protection')
        elif ref.startswith('D'):role='LED bridge current; retain A/K polarity, neither conductor is AGND'
        else:role='selector common; high impedance when open' if pin=='2' else 'selector A/B contact after 2.2kohm resistor'
        rows.append({**row,'maximum_wire_cut_mm':nominal+tolerance,'local_plus_wire_allocation_mm':nominal+tolerance+row['local_terminal_copper_mm'],'geometric_distance_mm':distance,'electrical_role':role,'owner':'X1-jack'if ref!='SW608'else'X1-control'})
    return {'status':'TERMINAL INTERCONNECT DELTA ONLY; NOT ASSEMBLED ACCEPTANCE','terminal_extensions':rows,
      'counts':{'fixed_packages':7,'extended_active_terminals':15,'jack_tip_wires':3,'jack_sleeve_AGND_wires':3,'LED_bridge_wires':6,'selector_wires':3,'retained_jack_TN_NC':3,'added_mating_interfaces':0,'added_mated_contacts':0,'added_crimps':0,'new_wire_end_terminations':30,'existing_transport_wires':15,'total_candidate_physical_wires':30},
      'termination_interpretation':'30 wire ends:9 jack/switch direct tails,6 LED-support board lands,15 elevated-board lands. Not automatically30 additional solder joints versus Stage8: direct tails replace former directPCB joints; exact process and NC mechanical retention remain OPEN. Six LED device pads remain on three local support PCBs.',
      'return_interpretation':'Three new sleeve conductors preserve AGND but add unknown series impedance and external patch return paths. LED conductors retain signed bridge paths, not substitute ground returns. Existing four service-harness AGND conductors remain electrically joined; no equal sharing/cancellation credit.',
      'budget_delta_scope':'Each new physical terminal wire has38mm maximum cut allocation,570mm sum over15 distinct wires. Sum is inventory, not one signal path. Existing transport endpoint Z, front J-PWR XY and middle C-PWR position change, so Stage8 length/slack/return budgets cannot be carried forward as actual Stage9 values. Output-tip extension is shared by load/remote-feedback paths; do not double-count it as two wires. Source XY/Z are nominal retained datums, not measured factory tails.',
      'required_later_inputs':['actual terminal/land/strain geometry and accepted factory termination process','whole path cable/copper length and aggregate capacitance for every affected net','actual wire/copper/contact R and external return division','output remote-feedback loop parasitics and assembled stability','selector open-state leakage/capacitance and transition response','LED extension loop parasitics, source headroom and local-board support'],
      'service_boundary':'Two separate permanent factory subassemblies, jack and control; each disconnects its two existing service ports for routine replacement. Individual terminal repair requires factory process, not home soldering. No new GH3/GH7 interface reproduces the rejected power/signal mis-mate.',
      'slack_scope':'Straight endpoint distance and proposed polyline allocation only; positive numerical slack is not proof of installed routing, bend radius, insulation clearance, termination reach or physical fit.',
      'source_counts_scope':'56 original X1 packages and76 units remain required; new terminal lands/support substrates are transport/mechanical items, not replacements for original devices.',
      'hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}

def build():
    support=OUT/'support-report.json';baseline=OUT.parent/'stage8/interfaces-report.json'
    r=analyze(json.loads(support.read_text()),json.loads(baseline.read_text()))
    paths=[support,baseline,Path(__file__),Path(__file__).with_name('test_stage9_electrical.py')]
    r['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}
    return r

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data=json.dumps(build(),indent=2,sort_keys=True)+'\n';target=OUT/'electrical-delta-report.json'
    if args.check:need(target.read_text()==data,'stale electrical terminal delta')
    else:target.write_text(data)
    print('Stage9 terminal delta:15 permanent wires,30 wire ends,zero added mating interfaces; electrical acceptance OPEN')
if __name__=='__main__':main()
