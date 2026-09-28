"""Native exact IC/bypass, GH-return and load-terminal continuity audit."""
from __future__ import annotations
import argparse,hashlib,json,re,sys,math
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
ROOT=Path(__file__).resolve().parents[2]

def audit(source,output):
    board=pcbnew.LoadBoard(str(source));conn=board.GetConnectivity();conn.RecalculateRatsnest();fps={f.GetReference():f for f in board.GetFootprints()};packages=json.loads((ROOT/'design/reports/io-partition.json').read_text())['physical_packages'];cache={}
    def members(pad):
        key=pad.m_Uuid.AsString()
        if key not in cache:
            group={m.m_Uuid.AsString() for m in conn.GetConnectedItems(pad) if m.Type()!=pcbnew.PCB_ZONE_T};group.add(key)
            for uid in group:cache[uid]=group
        return cache[key]
    lands=[(ref,p) for ref,f in fps.items() if str(f.GetFPID().GetLibItemName())=='LoadWireTerminal_4x4mm' for p in f.Pads()];ground=next(p for _,p in lands if p.GetNetname()=='AGND');main=members(ground);rail_main={p.GetNetname():members(p) for _,p in lands if p.GetNetname()!='AGND'};bypasses=[]
    for row in packages:
        ref,ic=row['ref'],row['decouples_ref']
        if not ic or ref not in fps:continue
        if ic not in fps:raise ValueError('bypass IC absent from same native board '+ref)
        for pad in fps[ref].Pads():
            net=pad.GetNetname()
            if net not in ('+12V','-12V','+5V'):continue
            pins=[p for p in fps[ic].Pads() if p.GetNetname()==net]
            if not pins:raise ValueError('exact bypass IC has no matching native supply pad')
            a=pad.GetPosition();pin=min(pins,key=lambda p:math.hypot(a.x-p.GetPosition().x,a.y-p.GetPosition().y));b=pin.GetPosition()
            ground_pads=[p for p in fps[ref].Pads() if p.GetNetname()=='AGND'];ground_ok=bool(ground_pads) and all(p.m_Uuid.AsString() in main for p in ground_pads)
            bypasses.append({'capacitor_ref':ref,'capacitor_pad':pad.GetNumber(),'IC_ref':ic,'IC_pad':pin.GetNumber(),'net':net,'same_face':fps[ref].GetLayer()==fps[ic].GetLayer(),'pad_distance_mm':round(pcbnew.ToMM(math.hypot(a.x-b.x,a.y-b.y)),6),'rail_connected':pin.m_Uuid.AsString() in members(pad),'rail_feed_connected_to_load_land':pad.m_Uuid.AsString() in rail_main[net],'AGND_return_connected':ground_ok,'capacitor_pad_uuid':pad.m_Uuid.AsString(),'IC_pad_uuid':pin.m_Uuid.AsString()})
    open_ground=[];contacts=[]
    for ref,f in fps.items():
        for p in f.Pads():
            if p.GetNetname()!='AGND':continue
            connected=p.m_Uuid.AsString() in main
            if not connected:open_ground.append({'ref':ref,'pad':p.GetNumber(),'uuid':p.m_Uuid.AsString(),'x_mm':pcbnew.ToMM(p.GetPosition().x),'y_mm':pcbnew.ToMM(p.GetPosition().y)})
            if re.fullmatch(r'J9\d{5}',ref):contacts.append({'ref':ref,'pad':p.GetNumber(),'connected_to_main_returns':connected})
    fitted={row['ref'] for row in packages if not row['dnp']};fitted_rail_pads=[]
    for ref,fp in sorted(fps.items()):
        if ref not in fitted:continue
        for pad in fp.Pads():
            net=pad.GetNetname()
            if net not in ('+12V','-12V','+5V'):continue
            fitted_rail_pads.append({'ref':ref,'pad':pad.GetNumber(),'net':net,'uuid':pad.m_Uuid.AsString(),'x_mm':pcbnew.ToMM(pad.GetPosition().x),'y_mm':pcbnew.ToMM(pad.GetPosition().y),'connected_to_load_land':pad.m_Uuid.AsString() in rail_main[net]})
    terminal_rows=[]
    for ref,p in lands:
        group=conn.GetConnectedItems(p);terminal_rows.append({'ref':ref,'net':p.GetNetname(),'connected_to_same_net_filled_plane':any(m.Type()==pcbnew.PCB_ZONE_T and m.GetNetname()==p.GetNetname() for m in group),'native_connected_items':len(group),'connected_to_main_AGND_component':p.m_Uuid.AsString() in main if p.GetNetname()=='AGND' else None})
    report={'board_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bypasses':bypasses,'fitted_rail_pad_feeds':fitted_rail_pads,'fitted_rail_pad_count':len(fitted_rail_pads),'fitted_rail_pads_connected_to_load_land':sum(r['connected_to_load_land'] for r in fitted_rail_pads),'rail_feed_scope':'All fitted master-package native rail pads; exact source DNP exclusion. Factory load lands are separately listed. Electrical feeding is unresolved unless this native topology and per-path resistance/current gates pass.','bypass_count':len(bypasses),'rail_loops_connected':sum(r['rail_connected'] for r in bypasses),'bypass_AGND_returns_connected':sum(r['AGND_return_connected'] for r in bypasses),'rail_feeds_connected':sum(r['rail_feed_connected_to_load_land'] for r in bypasses),'all_same_face':all(r['same_face'] for r in bypasses),'maximum_pad_distance_mm':max(r['pad_distance_mm'] for r in bypasses),'open_AGND_pad_identities':open_ground,'GH_return_contacts':contacts,'load_terminals':terminal_rows,'scope':'Native electrical continuity and exact source DecouplesRef relation only; short-loop copper geometry/stability and hot physical qualification remain separate.'}
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(f'{source}: bypass rails {report["rail_loops_connected"]}/{len(bypasses)}, returns {report["bypass_AGND_returns_connected"]}/{len(bypasses)}; open AGND pads {len(open_ground)}')

def main():
    p=argparse.ArgumentParser();p.add_argument('board',type=Path);p.add_argument('output',type=Path);a=p.parse_args();audit(a.board,a.output)
if __name__=='__main__':main()
