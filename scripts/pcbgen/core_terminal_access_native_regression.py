"""Pinned native positive/negative own-land via rule fixture; run under guard."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.core_terminal_access import apply,rules,source_entries
from scripts.pcbgen.uuid_tools import stable_uuid


def run(folder):
    folder.mkdir(parents=True,exist_ok=False);path=folder/'fixture.kicad_pcb'
    definition={'keepouts':[{'id':'POWER-'+str(i),'layers':['F.Cu'],
        'polygon':[[x-3,-3],[x+3,-3],[x+3,3],[x-3,3]]} for i,x in enumerate((0,12))]}
    entries=source_entries(definition,[{'reference':'TP1','net':'AGND','center_mm':[0,0]}])
    board=pcbnew.BOARD();board.SetCopperLayerCount(4)
    def vec(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x+100),pcbnew.FromMM(y+50))
    nets={}
    for name in ('AGND','FOREIGN'):
        nets[name]=pcbnew.NETINFO_ITEM(board,name);board.Add(nets[name])
    for row in definition['keepouts']:
        zone=pcbnew.ZONE(board);zone.SetLayer(pcbnew.F_Cu);zone.SetIsRuleArea(True)
        zone.SetZoneName('pcbgen:osc-core:keepout:'+row['id']+':F.Cu')
        for method in ('SetDoNotAllowTracks','SetDoNotAllowVias','SetDoNotAllowPads','SetDoNotAllowZoneFills','SetDoNotAllowFootprints'):
            getattr(zone,method)(True)
        poly=zone.Outline();index=poly.NewOutline()
        for x,y in row['polygon']:poly.Append(vec(x,y),index)
        board.Add(zone)
    cases={}
    owner=pcbnew.FootprintLoad(str(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'),'LoadWireTerminal_4x4mm')
    owner.SetReference('TP1');owner.SetPosition(vec(0,0));owner.SetUuid(pcbnew.KIID(stable_uuid('osc-core','footprint:TP1','root')))
    for pad in owner.Pads():pad.SetNet(nets['AGND']);cases['own_pad']=pad.m_Uuid.AsString()
    board.Add(owner);cases['own_footprint']=owner.m_Uuid.AsString()
    for ref,net,x,y in [('FOREIGN_SAME_NET','AGND',-1,1),('FOREIGN_NET','FOREIGN',1,1),('UNRELATED','AGND',12,0)]:
        fp=pcbnew.FootprintLoad(str(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'),'LoadWireTerminal_4x4mm')
        fp.SetReference(ref);fp.SetPosition(vec(x,y));pad=list(fp.Pads())[0];pad.SetNet(nets[net]);board.Add(fp)
        cases[ref+'_pad']=pad.m_Uuid.AsString();cases[ref+'_footprint']=fp.m_Uuid.AsString()
    retained_owner_uuid=owner.m_Uuid.AsString();owner.SetUuid(pcbnew.KIID())
    try:apply(board,entries)
    except ValueError as error:
        if 'UUID' not in str(error):raise
    else:raise ValueError('wrong owning source UUID was accepted')
    owner.SetUuid(pcbnew.KIID(retained_owner_uuid))
    own_pad=list(owner.Pads())[0];own_pad.SetNet(nets['FOREIGN'])
    try:apply(board,entries)
    except ValueError as error:
        if 'net changed' not in str(error):raise
    else:raise ValueError('wrong owning source pad net was accepted')
    own_pad.SetNet(nets['AGND']);receipt=apply(board,entries)
    for name,net,x,y in [('own_inside','AGND',0,0),('foreign_inside','FOREIGN',0,1),
        ('own_straddles','AGND',1.8,0),('own_outside','AGND',2.6,1),('unrelated_land','AGND',12,0)]:
        via=pcbnew.PCB_VIA(board);via.SetViaType(pcbnew.VIATYPE_THROUGH);via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
        via.SetPosition(vec(x,y));via.SetWidth(pcbnew.FromMM(.7));via.SetDrill(pcbnew.FromMM(.3));via.SetNet(nets[net]);board.Add(via)
        cases[name]=via.m_Uuid.AsString()
    track=pcbnew.PCB_TRACK(board);track.SetLayer(pcbnew.F_Cu);track.SetWidth(pcbnew.FromMM(.2));track.SetNet(nets['AGND'])
    track.SetStart(vec(-1,-1));track.SetEnd(vec(-.5,-1));board.Add(track);cases['own_track']=track.m_Uuid.AsString()
    corners=[(-10,-10),(25,-10),(25,10),(-10,10)]
    for a,b in zip(corners,corners[1:]+corners[:1]):
        edge=pcbnew.PCB_SHAPE(board);edge.SetShape(pcbnew.SHAPE_T_SEGMENT);edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetStart(vec(*a));edge.SetEnd(vec(*b));edge.SetWidth(pcbnew.FromMM(.05));board.Add(edge)
    pcbnew.SaveBoard(str(path),board)
    shutil.copyfile(ROOT/'boards/osc-core/osc-core.kicad_pro',path.with_suffix('.kicad_pro'))
    path.with_suffix('.kicad_dru').write_text(rules(entries))
    report=folder/'drc.json'
    subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','-o',str(report),str(path)],check=True)
    drc=json.loads(report.read_text())
    if drc['kicad_version']!='10.0.6':raise ValueError('wrong oracle')
    forbidden={i['uuid'] for row in drc['violations'] if row['type']=='items_not_allowed' for i in row['items']}
    permitted={'own_inside','own_pad','own_footprint'}
    if any(cases[name] in forbidden for name in permitted):raise ValueError('legal own-land native object rejected')
    for name,uid in cases.items():
        if name not in permitted and uid not in forbidden:raise ValueError('native keepout did not reject '+name)
    for zone in board.Zones():
        if zone.GetZoneName()==entries[0]['keepout_name']:
            if not all((zone.GetDoNotAllowTracks(),zone.GetDoNotAllowZoneFills())):
                raise ValueError('track/zone prohibition changed')
    owner.SetPosition(vec(2,0));pcbnew.SaveBoard(str(path),board)
    negative_path=folder/'negative-drc.json'
    subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','-o',str(negative_path),str(path)],check=True)
    negative=json.loads(negative_path.read_text())
    negative_forbidden={i['uuid'] for row in negative['violations'] if row['type']=='items_not_allowed' for i in row['items']}
    if cases['own_pad'] not in negative_forbidden or cases['own_footprint'] not in negative_forbidden:
        raise ValueError('straddling own pad or footprint escaped native prohibition')
    (folder/'receipt.json').write_text(json.dumps({'status':'PASS pinned own-land via rule fixture; not board acceptance',
        'cases':cases,'native_forbidden_uuids':sorted(forbidden),'shifted_owner_forbidden_uuids':sorted(negative_forbidden),'source_entries':receipt,
        'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (Path(__file__),ROOT/'scripts/pcbgen/core_terminal_access.py',path.with_suffix('.kicad_dru'))}},indent=2)+'\n')
    print('PASS: exact own land/footprint and finite via allowed; foreign pads/footprints, straddling/outside/unrelated vias, shifted own land and track rejected')


if __name__=='__main__':run(Path(sys.argv[1]))
