"""Independent X1 source conservation/composition guard; never native execution."""
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'design/architecture-278/implementation/stage7'

def need(ok,message):
    if not ok:raise ValueError(message)

def verify_source(packages,ledger,locked,old_overlay):
    source={p['ref']:p for p in ledger['packages'] if p['instance']=='X1'}
    need(set(packages)==set(source) and len(source)==56,'complete56package X1 scope')
    expected={ref:{} for ref in source};units={ref:[] for ref in source}
    for u in ledger['package_units']:
        if u['ref']not in source:continue
        units[u['ref']].append(u['unit'])
        for pin,net in u['pins'].items():
            need(pin not in expected[u['ref']],'duplicate physical source pin')
            expected[u['ref']][pin]=net
    need(sum(len(p)for p in expected.values())==182,'all physical pins includingNC')
    for ref,p in packages.items():
        need(p['pins']==expected[ref],'source net/NC identity changed '+ref)
        need(Counter(p['units'])==Counter(units[ref]),'whole package units changed '+ref)
    fixed=[p for p in locked['placements']if p['block']=='X1']
    need(len(fixed)==7 and len(locked['placements'])==438,'fixed panel scope')
    for p in fixed:
        q=packages[p['ref']]
        need(q['origin_mm']==[p['x_mm'],p['y_mm']] and q['quarter_turn']==p['rot_deg']//90,'fixed panel device moved')
    bypass=[(p['ref'],p['decouples_ref'])for p in source.values()if p['decouples_ref']]
    need(len(bypass)==10,'bypass scope')
    for ref,target in bypass:need(packages[ref]['board']==packages[target]['board'],'bypass split across hosts')
    for ref,p in packages.items():
        need(p['board']==('X1-control' if source[ref]['regions']==['control'] else 'X1-jack'),'source owner/host changed '+ref)
    need(len(old_overlay)==5904 and set(old_overlay)=={p['ref']for p in ledger['packages']},'whole instrument ownership omitted')
    overlay=dict(old_overlay)
    for ref,p in packages.items():overlay[ref]='stage7-'+p['board']
    return {'packages':56,'units':sum(len(p['units'])for p in packages.values()),'physical_pins_including_NC':182,'bypasses':10,'fixed_X1_devices':7,'instrument_packages':len(overlay),'instrument_functions':len(ledger['functions']),'fixed_instrument_centres':438},overlay


def verify_transport(report):
    headers=report['headers'];links=report['links'];need(len(headers)==8 and len(links)==4,'complete physical transport')
    wires=[];seen=set()
    for link in links:
        active={pin:net for pin,net in link['pins'].items() if net is not None}
        need({w['pin']:w['net']for w in link['conductors']}==active,'wire/pin inventory changed')
        for w in link['conductors']:
            key=(link['id'],w['pin']);need(key not in seen,'duplicate physical wire');seen.add(key)
            for side in ('front','middle'):
                h=headers[link[side+'_header']]
                need(h['pins'][w['pin']]==w['net'],'cross-net physical conductor')
                need(w[side+'_pad_xyz_mm']==h['pads_xyz_mm'][w['pin']][0],'wire endpoint detached from actual header pad')
            wires.append(w)
    counts=Counter('AGND' if w['net']=='AGND' else 'signal' if w['net'].startswith('/X1/') else 'rail' for w in wires)
    need(counts=={'AGND':4,'signal':6,'rail':5},'physical conductor role coverage')
    need(all(w['net']!='+5V' for l in links if l['id'].startswith('C-')for w in l['conductors']),'+5V illegally on control host')
    for edge in report['middle_trace_edges']:
        for side in ('from','to'):
            e=edge[side];h=headers[e['ref']]
            need(h['pins'][e['pin']]==edge['net'] and h['pads_xyz_mm'][e['pin']][0]==e['pad_xyz_mm'],'middle edge is not bound to same-net actual pads')
    need(Counter(e['net']for e in report['middle_trace_edges'])=={'/X1/A_BUFFER':1,'/X1/B_BUFFER':1,'/X1/SELECTOR_REMOTE':1,'+12V':1,'-12V':1,'AGND':3},'middle net graph changed')
    expected_edges=[('/X1/'+net,'J-SIG',str(pin),'C-SIG',str(pin)) for pin,net in enumerate(('A_BUFFER','B_BUFFER','SELECTOR_REMOTE'),1)]
    expected_edges += [('+12V','J-PWR','1','C-PWR','1'),('-12V','J-PWR','3','C-PWR','2')]
    expected_edges += [('AGND','J-PWR','7',target,pin) for target,pin in [('J-SIG','4'),('C-SIG','4'),('C-PWR','3')]]
    actual=Counter((e['net'],e['from']['ref'],e['from']['pin'],e['to']['ref'],e['to']['pin']) for e in report['middle_trace_edges'])
    expected=Counter((net,'X1:'+a+':middle',ap,'X1:'+b+':middle',bp) for net,a,ap,b,bp in expected_edges)
    need(actual==expected,'middle graph connectivity changed')
    pinjoints=sum(sum(not p.startswith('MP')for p in h['pins'])for h in headers.values());mpjoints=sum(sum(p.startswith('MP')for p in h['pins'])for h in headers.values())
    need((pinjoints,mpjoints)==(36,16),'populated/NC/mechanical header joint count')
    bom=report['transport_BOM']
    need(bom['physical_wire_conductors']==len(wires) and bom['crimp_contacts']==2*len(wires),'termination accounting')
    need(bom['total_header_solder_joints']==pinjoints+mpjoints,'NC solder joints omitted')
    # Identical-size signal connections share a pin map; power must not share it.
    bysize={}
    for l in links:
        n=headers[l['front_header']]['positions'];mapping=l['pins']
        if n in bysize:need(mapping==bysize[n],'same-size incompatible pinmap remains')
        bysize[n]=mapping
    return {'harnesses':4,'headers':8,'housings':bom['added_housings'],'conductors':len(wires),'roles':dict(counts),'crimps':2*len(wires),'header_pin_solder_joints_including_NC':pinjoints,'mechanical_solder_joints':mpjoints,'middle_copper_edges':len(report['middle_trace_edges']),'mis_mating_boundary':'No exact same-size conflicting pinmap in candidate; partial insertion and mechanical coding/assembly proof remain OPEN'}

def build():
    files={'interfaces':OUT/'interfaces-report.json','mechanical':OUT/'mechanical-report.json','electrical':OUT/'electrical-report.json','ledger':ROOT/'design/architecture-278/source-ledger.json','locked':ROOT/'design/grid/placements.lock.json','prior':ROOT/'design/architecture-278/implementation/stage6/hosting-report.json','OSC':ROOT/'design/architecture-278/implementation/stage6/candidate-report.json','scope':OUT/'scope.json'}
    r={k:json.loads(p.read_text())for k,p in files.items()}
    transport=verify_transport(r['interfaces'])
    counts,overlay=verify_source(r['interfaces']['source_packages'],r['ledger'],r['locked'],r['prior']['whole_instrument_host_overlay'])
    need(hashlib.sha256(files['OSC'].read_bytes()).hexdigest()=='2a7eb6d0c9095d864854209cf7280a6e1f8719b06ec5f1142ad2694c855431f7','Stage6 OSC baseline mutated')
    need(len(r['OSC']['candidate']['paths'])==225 and len(r['OSC']['candidate']['returns'])==240,'OSC baseline scope')
    # Hash binding guards cross-stage consistency; no source report promotes qualification.
    for name in ('interfaces','mechanical','electrical'):
        for p,h in r[name]['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'stale dependent source '+name+':'+p)
    paths=list(files.values())+[Path(__file__),Path(__file__).with_name('test_stage7_demonstrator.py')]
    return {'status':'CONDITIONAL X1 SOURCE DEMONSTRATOR; ENGINEERING CONSTRAINTS REMAIN','counts':counts,'transport_inventory':transport,'whole_instrument_host_overlay':overlay,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths},'OSC_baseline':{'sha256':hashlib.sha256(files['OSC'].read_bytes()).hexdigest(),'paths':225,'returns':240,'geometry_changed':False},'review_boundary':'Source conservation and current-input composition, not native ERC/DRC or assembled fit. Read mechanical/interface/electrical reports for exact quantitative constraints. No unknown neighboring geometry is free space.','hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();data=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n';out=OUT/'demonstrator-report.json'
    if args.check:need(out.read_text()==data,'stale demonstrator report')
    else:out.write_text(data)
    print('X1 complete source preservation PASS; conditionaldemonstrator only; physicalacceptance OPEN')
if __name__=='__main__':main()
