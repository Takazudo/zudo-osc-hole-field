"""Small synthetic geometry/graph tests; no router or native execution."""
import collections
import unittest
import numpy as np
from analyze import components, boundary_screen


class GraphTests(unittest.TestCase):
    def test_diagonal_corner_is_not_connected(self):
        a=np.array([[[1,0],[0,1]]],bool);z=np.zeros_like(a)
        labels=components(a,z[0],z,z)
        self.assertNotEqual(labels[0,0,0],labels[0,1,1])

    def test_via_switch_requires_passability_both_layers(self):
        a=np.array([[[1,1,0]],[[0,1,1]]],bool);s=np.zeros_like(a);g=s.copy();v=np.zeros((1,3),bool)
        without=components(a,v,s,g);self.assertNotEqual(without[0,0,0],without[1,0,2])
        v[0,1]=True;with_via=components(a,v,s,g);self.assertEqual(with_via[0,0,0],with_via[1,0,2])
        v[0,1]=False;v[0,0]=True;blocked=components(a,v,s,g);self.assertNotEqual(blocked[0,0,0],blocked[1,0,2])

    def test_through_terminal_enables_switch_without_new_via(self):
        a=np.ones((2,1,1),bool);v=np.zeros((1,1),bool);s=a.copy();g=np.zeros_like(a)
        self.assertEqual(len(np.unique(components(a,v,s,g))),1)

    def test_components_match_independent_eight_neighbor_no_cornercut_graph(self):
        rng=np.random.default_rng(253)
        for _ in range(30):
            a=rng.random((3,5,6))>.4;s=(rng.random(a.shape)>.94)&a;g=(rng.random(a.shape)>.94)&a;v=rng.random((5,6))>.7
            labels=components(a,v,s,g);switch=v|s.all(0)|g.all(0)
            unseen={tuple(map(int,x)) for x in np.argwhere(a)}
            while unseen:
                start=next(iter(unseen));seen={start};queue=collections.deque([start])
                while queue:
                    l,y,x=queue.popleft();neighbors=[]
                    for dy in (-1,0,1):
                        for dx in (-1,0,1):
                            ny,nx=y+dy,x+dx
                            if not(dx or dy) or not(0<=ny<5 and 0<=nx<6) or not a[l,ny,nx]:continue
                            if dy and dx and not(a[l,y,nx] and a[l,ny,x]):continue
                            neighbors.append((l,ny,nx))
                    if switch[y,x]:neighbors.extend((ll,y,x) for ll in range(3) if a[ll,y,x])
                    for n in neighbors:
                        if n not in seen:seen.add(n);queue.append(n)
                root=labels[start];self.assertEqual(seen,{tuple(map(int,x)) for x in np.argwhere(labels==root)})
                unseen-=seen


class GeometryTests(unittest.TestCase):
    def screen(self,**extra):
        dump={'layers':['F.Cu'],'edges':[[0,0,10000000,0],[10000000,0,10000000,10000000],[10000000,10000000,0,10000000],[0,10000000,0,0]],'pads':[],'tracks':[],'vias':[],'keepouts':[],**extra}
        terminal=np.zeros((1,3,3),bool);terminal[0,1,1]=True
        labels=terminal.astype(np.int32)
        return boundary_screen(dump,{'net':'own'},labels,terminal,terminal,[4,4],1,.2,.2)['layers'][0]

    def test_foreign_via_is_complete_obstacle(self):
        baseline=self.screen();self.assertEqual(baseline['exact_clearance_legal_centers'],4)
        blocked=self.screen(vias=[{'net':'other','xy':[5000000,4000000],'diameter':1000000,'uuid':'via'}])
        self.assertEqual(blocked['exact_clearance_legal_centers'],3)

    def test_nonplated_hole_and_track_keepout_are_not_omitted(self):
        hole=self.screen(pads=[{'net':'','layers':[],'poly':[],'npth':True,'drill':1000000,'xy':[5000000,4000000],'ref':'H','pad':''}])
        self.assertEqual(hole['exact_clearance_legal_centers'],3)
        keep=self.screen(keepouts=[{'name':'guard','tracks':True,'layers':['F.Cu'],'poly':[[4500000,3500000],[5500000,3500000],[5500000,4500000],[4500000,4500000]]}])
        self.assertEqual(keep['exact_clearance_legal_centers'],3)

if __name__=='__main__':unittest.main()
