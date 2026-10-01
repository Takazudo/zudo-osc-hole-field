"""Exact primitive envelope and retained native nanometre regression."""
import json
import math
from pathlib import Path
import unittest
import numpy as np
import shapely
from shapely.geometry import Point,Polygon
from scripts.pcbgen.copper_envelope import primitive_envelopes
from scripts.pcbgen.propose_rail_transfers import geometry
from scripts.pcbgen.ground_volume_geometry import computational_envelopes,fixed_load_patch
from scripts.pcbgen.sheet_mesh import Sheet,make_cells
from scripts.pcbgen.sheet_flux import FluxSheet


class CopperEnvelopeTests(unittest.TestCase):
    def test_computational_domains_bound_native_sliver_and_keep_finite_rim_profile(self):
        # Native In1 near-coincident vertices from the failed complete solve.
        native=Polygon([(266,140),(267,140),(267,142),(266,142),
            (266.188207218,140.463371908),(266.188207211,140.463371894)])
        self.assertTrue(native.is_valid)
        inner,outer,audit=computational_envelopes(native,native)
        self.assertTrue(native.covers(inner));self.assertTrue(outer.covers(native))
        self.assertTrue(audit['strict_boolean_inclusion'])
        rim=Point(0,0).buffer(.875,quad_segs=32).difference(Point(0,0).buffer(.71,quad_segs=32))
        patch=fixed_load_patch(rim)
        self.assertTrue(rim.covers(patch));self.assertGreater(patch.area,.02)
        for part in shapely.get_parts(patch):
            self.assertEqual(part.area,part.envelope.area)

    def test_translated_multisquare_profile_has_no_binary_ghost_overlap(self):
        centre=Point(267.410002,72.455002)
        rim=centre.buffer(1.,quad_segs=16).difference(centre.buffer(.71,quad_segs=16))
        patch=fixed_load_patch(rim)
        sheet=Sheet(rim,make_cells(rim.bounds,.5,.25),.001,source_patches=[patch])
        source=FluxSheet(sheet,.001).area_current(patch,1.)
        self.assertAlmostEqual(float(source.sum()),1.,places=10)

    def test_native_roundrect_missing_strip_is_covered_by_analytic_outer(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/native-rounded-pad.json').read_text())
        pad=fixture['native_pad'];self.assertEqual(pad['uuid'],'5eac5a5d-048f-5231-8914-d8c181a64ecb')
        old_inner=geometry(pad['copper_inside']['B.Cu']);old_outer=geometry(pad['copper']['B.Cu'])
        self.assertGreater(old_inner.difference(old_outer).area,1e-6)
        inner,outer=primitive_envelopes(fixture['analytic_primitive'])
        self.assertTrue(outer.covers(inner));self.assertTrue(outer.covers(old_inner))
        for x in np.linspace(260.345,261.62,101):
            self.assertTrue(outer.covers(Point(x,181.779999)))

    def test_circle_secant_envelopes_and_native_coordinate_translation(self):
        for centre in ([0,0],[999000001,-998000003]):
            primitive={'kind':'circle','centre_nm':centre,'half_size_nm':[350000,350000],
                       'quarter_turns':0,'corner_radius_nm':0}
            inner,outer=primitive_envelopes(primitive)
            xy=np.array(centre)/1e6
            boundary=shapely.points(xy+np.column_stack((np.cos(np.arange(1024)*math.pi/512),
                                                      np.sin(np.arange(1024)*math.pi/512)))*.35)
            self.assertTrue(np.all(shapely.covers(outer,boundary)))
            self.assertLess(max(np.linalg.norm(p-xy) for p in np.array(inner.exterior.coords)),.35)
            self.assertTrue(outer.covers(inner))

    def test_actual_supported_classes_and_explicit_unsupported_failure(self):
        for kind in ('rectangle','oval','roundrect'):
            for angle in range(4):
                inner,outer=primitive_envelopes({'kind':kind,'centre_nm':[123400000,98765000],
                    'half_size_nm':[600000,200000],'quarter_turns':angle,'corner_radius_nm':100000})
                self.assertTrue(outer.covers(inner));self.assertGreater(inner.area,0)
        inner,outer=primitive_envelopes({'kind':'segment','start_nm':[110000001,87000003],
                                        'end_nm':[112000000,91000000],'radius_nm':100000})
        self.assertTrue(outer.covers(inner))
        with self.assertRaisesRegex(ValueError,'unsupported'):
            primitive_envelopes({'kind':'custom','centre_nm':[0,0],'half_size_nm':[1,1],
                                 'quarter_turns':0,'corner_radius_nm':0})


if __name__=='__main__':unittest.main()
