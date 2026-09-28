"""Regression: a pad plus its own zone is not a main-return connection.

Run through scripts/kicad/run.sh; the fixture is entirely in memory.
"""
import unittest
import pcbnew

def vec(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))

class MainGroundComponentTests(unittest.TestCase):
    def test_zone_membership_does_not_prove_main_network(self):
        board=pcbnew.BOARD();net=pcbnew.NETINFO_ITEM(board,'AGND',1);board.Add(net)
        for a,b in (((0,0),(10,0)),((10,0),(10,8)),((10,8),(0,8)),((0,8),(0,0))):
            edge=pcbnew.PCB_SHAPE(board);edge.SetShape(pcbnew.SHAPE_T_SEGMENT);edge.SetStart(vec(*a));edge.SetEnd(vec(*b));edge.SetLayer(pcbnew.Edge_Cuts);edge.SetWidth(pcbnew.FromMM(.05));board.Add(edge)
        pads=[]
        for x,ref in ((2,'MAIN'),(7,'CONTACT')):
            fp=pcbnew.FOOTPRINT(board);fp.SetReference(ref);board.Add(fp)
            copper=pcbnew.LSET();copper.AddLayer(pcbnew.F_Cu)
            pad=pcbnew.PAD(fp);pad.SetNumber('1');pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD);pad.SetShape(pcbnew.PAD_SHAPE_RECT);pad.SetSize(vec(1,1));pad.SetLayerSet(copper);pad.SetPosition(vec(x,2));pad.SetNet(net);fp.Add(pad);pads.append(pad)
            zone=pcbnew.ZONE(board);zone.SetLayer(pcbnew.F_Cu);zone.SetNet(net);zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);zone.SetLocalClearance(pcbnew.FromMM(.2));zone.SetMinThickness(pcbnew.FromMM(.15));poly=zone.Outline();i=poly.NewOutline()
            for px,py in ((x-1,1),(x+1,1),(x+1,3),(x-1,3)):poly.Append(vec(px,py),i)
            board.Add(zone)
        board.GetConnectivity().Build(board)
        self.assertTrue(pcbnew.ZONE_FILLER(board).Fill(board.Zones()));conn=board.GetConnectivity();conn.Build(board);conn.RecalculateRatsnest()
        first=conn.GetConnectedItems(pads[0]);self.assertTrue(any(m.Type()==pcbnew.PCB_ZONE_T for m in first))
        # This is the exact false-positive shape found in the J power lands.
        self.assertNotIn(pads[1].m_Uuid.AsString(),{m.m_Uuid.AsString() for m in first})
        self.assertEqual(conn.GetUnconnectedCount(False),1)
        track=pcbnew.PCB_TRACK(board);track.SetStart(pads[0].GetPosition());track.SetEnd(pads[1].GetPosition());track.SetLayer(pcbnew.F_Cu);track.SetWidth(pcbnew.FromMM(.5));track.SetNet(net);board.Add(track);conn.Build(board);conn.RecalculateRatsnest()
        self.assertIn(pads[1].m_Uuid.AsString(),{m.m_Uuid.AsString() for m in conn.GetConnectedItems(pads[0])});self.assertEqual(conn.GetUnconnectedCount(False),0)

if __name__=='__main__':unittest.main()
