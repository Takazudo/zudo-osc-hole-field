"""Disposable source-defined load-land to AGND plane via arrays."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.definition import load_definition
from scripts.pcbgen.uuid_tools import stable_uuid
ROOT=Path(__file__).resolve().parents[2]

def route(board_id,source,output,receipt,net):
    definition=load_definition(ROOT/'design/boards'/f'{board_id}.json')
    spec=definition.routing['load_terminal_transfer'];board=pcbnew.LoadBoard(str(source))
    planes=[z for z in board.Zones() if z.GetNetname()==net and z.IsOnLayer(pcbnew.In1_Cu if net=='AGND' else pcbnew.In2_Cu) and not z.GetIsRuleArea()]
    if len(planes)!=1 or not planes[0].HasFilledPolysForLayer(pcbnew.In1_Cu if net=='AGND' else pcbnew.In2_Cu):raise ValueError('one filled AGND plane required')
    lands=[(f.GetReference(),p) for f in board.GetFootprints() if str(f.GetFPID().GetLibItemName())=='LoadWireTerminal_4x4mm' for p in f.Pads() if p.GetNetname()==net]
    if len(lands)!=(3 if net=='AGND' else 1):raise ValueError('incorrect exact load land count')
    existing={t.m_Uuid.AsString() for t in board.GetTracks()};added=[]
    for ref,pad in sorted(lands):
        if pad.GetSize().x!=pcbnew.FromMM(4) or pad.GetSize().y!=pcbnew.FromMM(4):raise ValueError('load land changed from exact 4x4 mm copper')
        row={'ref':ref,'pad_uuid':pad.m_Uuid.AsString(),'net':net,'via_uuids':[]}
        for ix in range(spec['array_columns']):
            for iy in range(spec['array_rows']):
                dx=(ix-(spec['array_columns']-1)/2)*spec['array_pitch_mm'];dy=(iy-(spec['array_rows']-1)/2)*spec['array_pitch_mm']
                if max(abs(dx),abs(dy))+spec['via_diameter_mm']/2>2-spec['pad_edge_copper_margin_mm']+1e-8:raise ValueError('array exceeds land edge margin')
                at=pcbnew.VECTOR2I(pad.GetPosition().x+pcbnew.FromMM(dx),pad.GetPosition().y+pcbnew.FromMM(dy))
                if not planes[0].HitTestFilledArea(pcbnew.In1_Cu if net=='AGND' else pcbnew.In2_Cu,at,0):raise ValueError('array point not inside actual filled same-net plane')
                uid=stable_uuid(board_id,'load-array:'+net,ref+':'+str(ix)+':'+str(iy))
                if uid in existing:raise ValueError('terminal already has this array; do not add duplicates')
                via=pcbnew.PCB_VIA(board);via.SetViaType(pcbnew.VIATYPE_THROUGH);via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);via.SetPosition(at);via.SetWidth(pcbnew.FromMM(spec['via_diameter_mm']));via.SetDrill(pcbnew.FromMM(spec['via_drill_mm']));via.SetNetCode(pad.GetNetCode());via.SetUuid(pcbnew.KIID(uid));board.Add(via);row['via_uuids'].append(uid)
        added.append(row)
    pcbnew.SaveBoard(str(output),board)
    report={'status':'DISPOSABLE DRAFT; full native geometry/parity/connectivity and hot resistance gates pending','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'board_id':board_id,'net':net,'source_requirement':spec,'added':added,'new_via_count':sum(len(r['via_uuids']) for r in added),'process_qualification':'NOT RUN #65; explicit factory filled/capped or qualified anti-wicking solder process required'}
    receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(f'{board_id}: disposable {report["new_via_count"]} {net} terminal array vias')

def main():
    p=argparse.ArgumentParser();p.add_argument('board_id');p.add_argument('--board',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--net',choices=('AGND','+12V','-12V','+5V'),default='AGND');a=p.parse_args()
    if a.board.resolve()==a.output.resolve():raise ValueError('require disposable output')
    route(a.board_id,a.board,a.output,a.receipt,a.net)
if __name__=='__main__':main()
