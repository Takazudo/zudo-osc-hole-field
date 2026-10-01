"""Integrated disjoint copper/3D barrel/collar/source fixtures."""
import unittest
import numpy as np
import shapely
from shapely.geometry import box,Polygon
from scripts.pcbgen.barrel_volume import BarrelVolume
from scripts.pcbgen.sheet_mesh import Sheet,make_cells
from scripts.pcbgen.sheet_volume import SheetVolume

RHO=1.7241e-5*(1+.003947*50)
THICKNESS=[.07,.14,.07,.07]
BANDS=[(0,.07),(1.2,1.34),(1.4,1.47),(1.53,1.6)]


def assembly(centres,bounds,source,sink,refinement,origin=(0,0)):
    barrel=BarrelVolume(.15,.025,.275,1.6,BANDS,RHO,polygon_sides=8,
        angular_subdivisions=refinement,radial_steps=refinement,band_steps=refinement,gap_steps=2*refinement)
    copper=box(*bounds).difference(shapely.union_all([Polygon(barrel.interface_polygon(c)) for c in centres]))
    cells=make_cells(copper.bounds,.5,.125/refinement,source.union(sink).buffer(.2),origin)
    sheets=[Sheet(copper,cells,RHO/t,source_patches=[source,sink],
                  interfaces=[{'relative':barrel.interface_polygon(),'centre':c} for c in centres]) for t in THICKNESS]
    return SheetVolume(sheets,[RHO/t for t in THICKNESS],[(barrel,c) for c in centres])


class SheetVolumeTests(unittest.TestCase):
    def test_translated_shared_trace_uses_one_telescoping_parameter_measure(self):
        x,y=250.017,100.031
        source=box(*(round(v,9) for v in (x+.4,y+.4,x+.65,y+.65)))
        sink=box(*(round(v,9) for v in (x-.7,y-.5,x-.45,y-.25)))
        conductor=assembly([(x,y)],(x-1,y-1,x+1,y+1),source,sink,2,(.013,.027))
        barrel=conductor.barrels[0][0]
        for layer,sheet in enumerate(conductor.sheets):
            for (_,sector),pieces in sheet.interface_faces.items():
                intervals=sorted((min(p['parameters']),max(p['parameters'])) for p in pieces)
                self.assertEqual(intervals[0][0],0);self.assertEqual(intervals[-1][1],1)
                self.assertTrue(all(a[1]==b[0] for a,b in zip(intervals,intervals[1:])))
                for p in pieces:
                    a,b=p['vertices'];fraction=abs(p['parameters'][1]-p['parameters'][0])
                    length=np.linalg.norm(sheet.metric_xy[b]-sheet.metric_xy[a])
                    self.assertLess(abs(length/barrel.interface_chord_mm-fraction),2e-12)
                    self.assertEqual(conductor.face_maps[layer][p['face']][1],fraction)
            self.assertLess(sheet.maximum_interface_projection_mm,2e-9)
        receipt,_,_=conductor.area_pair(3,source,1,sink,RHO,THICKNESS)
        self.assertLess(receipt['maximum_volume_sheet_divergence_A'],1e-8)
        # Actual translated triangle 868 has almost orthogonal normals. Its
        # C[0,1] cancels although the two normal products are individually large.
        # Exercise every local unit trace and a signed source, including the
        # forced third-face propagation, against a long-double factor witness.
        indices,C,_,_=conductor.hybrid_cells[0]
        field=np.zeros((conductor.hybrid_matrix.shape[0],4))
        for k in range(3):field[indices[868,k],k]=1
        sources=np.zeros((len(indices),4));sources[868,3]=.123456789
        observed=conductor.hybrid_current(0,field,sources)
        enclosure=conductor.hybrid_current_error(0,field,sources,observed)
        ld=np.longdouble
        values=field[indices].astype(ld);normal=conductor.hybrid_normals[0].astype(ld)
        denominator=(ld(conductor.trials[0].sheet_ohm)*
            conductor.sheets[0].metric_factors.astype(ld)*conductor.sheets[0].areas.astype(ld))
        constant=-np.einsum('tik,tid->tdk',values[:,:2]-values[:,2:3],normal[:,:2])/denominator[:,None,None]
        reference=np.einsum('tid,tdk->tik',normal,constant)+sources.astype(ld)[:,None,:]/3
        reference[:,2]=sources.astype(ld)-reference[:,0]-reference[:,1]
        discrepancy=abs(observed.astype(ld)-reference)
        old_bound=64*np.finfo(float).eps*abs(C[868,0,1])
        self.assertGreater(discrepancy[868,0,1],1000*old_bound)
        self.assertTrue(np.all(discrepancy<=enclosure))
        self.assertTrue(np.all(enclosure[:,2]>=enclosure[:,0]+enclosure[:,1]))

    def test_asymmetric_four_layers_collar_and_patch_refine_same_physical_domain(self):
        source=box(.4,.4,.65,.65);sink=box(-.7,-.5,-.45,-.25)
        results=[]
        for refinement,origin in ((1,(0,0)),(2,(0,0)),(2,(.017,.031))):
            conductor=assembly([(0,0)],(-1,-1,1,1),source,sink,refinement,origin)
            result,voltage,flux=conductor.area_pair(3,source,1,sink,RHO,THICKNESS)
            self.assertLess(result['maximum_volume_sheet_divergence_A'],1e-8)
            self.assertGreater(result['upper_ohm'],result['lower_ohm'])
            # Constant potential is a physical null mode despite the different
            # sheet, collar and cylinder parameterizations.
            matrix=conductor.potential_matrix
            self.assertLess(np.max(abs(matrix@np.ones(matrix.shape[0]))),1e-7)
            results.append(result)
        self.assertLess(results[1]['upper_ohm']-results[1]['lower_ohm'],
                        results[0]['upper_ohm']-results[0]['lower_ohm'])
        self.assertLess(abs(results[1]['lower_ohm']-results[2]['lower_ohm']),
                        results[1]['upper_ohm']-results[1]['lower_ohm'])
        profiles=[[(3,source,1.),(1,sink,-1.)],[(0,source,1.),(1,sink,-1.)]]
        matrices=conductor.area_profile_matrices(profiles,RHO,THICKNESS)
        direct,_,_=conductor.area_pair(3,source,0,source,RHO,THICKNESS)
        difference=np.array([1.,-1.])
        self.assertAlmostEqual(difference@matrices['lower']@difference,direct['lower_ohm'],places=10)
        self.assertAlmostEqual(difference@matrices['upper']@difference,direct['upper_ohm'],places=10)
        self.assertGreaterEqual(np.linalg.eigvalsh(matrices['upper']-matrices['lower'])[0],-1e-10)
        for mode,key in (('current','upper'),('potential','lower')):
            conductor.certificate_mode=mode
            batched=conductor.area_profile_matrix_batched(profiles,RHO,THICKNESS,batch_size=1)
            # Batched residual-work intervals enclose the direct field Gram.
            # They need not equal its stationary shortcut.
            difference=(batched['energy']-matrices[key])*(1 if key=='upper' else -1)
            self.assertGreaterEqual(np.linalg.eigvalsh(difference).min(),-1e-12)
            self.assertLess(np.max(abs(difference)),max(1e-12,4*batched['maximum_residual_work_allowance_ohm']))

    def test_actual_4mm_land_25_barrels_keeps_every_shared_barrel(self):
        centres=[(.7*i,.7*j) for i in range(-2,3) for j in range(-2,3)]
        source=box(.225,.225,.475,.475);sink=box(-1.95,-1.95,-1.70,-1.70)
        conductor=assembly(centres,(-2,-2,2,2),source,sink,1)
        result,_,_=conductor.area_pair(3,source,1,sink,RHO,THICKNESS)
        self.assertEqual(result['barrel_count'],25)
        self.assertGreater(result['upper_ohm'],result['lower_ohm'])
        self.assertLess(result['upper_ohm'],.001)


if __name__=='__main__':unittest.main()
