#!/usr/bin/env python3
"""Insert deliberately unowned copper and silk into a fixture board."""
import sys,json
from pathlib import Path
import pcbnew
p=Path(sys.argv[1]);b=pcbnew.LoadBoard(str(p))
track=pcbnew.PCB_TRACK(b)
track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(125),pcbnew.FromMM(80)))
track.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(130),pcbnew.FromMM(80)))
track.SetWidth(pcbnew.FromMM(0.25));track.SetLayer(pcbnew.F_Cu);b.Add(track)
text=pcbnew.PCB_TEXT(b);text.SetText('OWNER SILK');text.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(130),pcbnew.FromMM(85)));text.SetLayer(pcbnew.F_SilkS);b.Add(text)
via=pcbnew.PCB_VIA(b);via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(128),pcbnew.FromMM(90)))
via.SetWidth(pcbnew.FromMM(0.9));via.SetDrill(pcbnew.FromMM(0.4));via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(via)
graphic=pcbnew.PCB_SHAPE(b);graphic.SetShape(pcbnew.SHAPE_T_SEGMENT)
graphic.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(126),pcbnew.FromMM(95)))
graphic.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(132),pcbnew.FromMM(95)))
graphic.SetLayer(pcbnew.F_SilkS);graphic.SetWidth(pcbnew.FromMM(0.15));b.Add(graphic)
zone=pcbnew.ZONE(b);zone.SetZoneName('OWNER ZONE');zone.SetLayer(pcbnew.B_Cu)
poly=zone.Outline();i=poly.NewOutline()
for x,y in [(125,100),(132,100),(132,108),(125,108)]:poly.Append(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)),i)
b.Add(zone)
pcbnew.SaveBoard(str(p),b)
ids={name:item.m_Uuid.AsString() for name,item in [('track',track),('silk',text),('via',via),('graphic',graphic),('zone',zone)]}
(p.parent/'owner-ids.json').write_text(json.dumps(ids,indent=2)+'\n')
print('owner items:',ids)
