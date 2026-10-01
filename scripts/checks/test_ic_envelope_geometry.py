import math
import unittest
from scripts.libgen import gen_ic_package_envelopes as model
from scripts.libgen import vrml_geometry as vrml
from scripts.libgen.gen_courtyards import parse,node_name

MESH='Coordinate { point [ -1 -2 -3, 1 -2 -3, 1 2 -3, -1 2 -3, -1 -2 3, 1 -2 3, 1 2 3, -1 2 3 ] }'


def body(text):
    root=parse(text);points=[]
    for item in root[1:]:
        if not isinstance(item,list):continue
        fields={node_name(n):n for n in item[1:] if isinstance(n,list)}
        if fields.get('layer',[None,None])[1]!='F.Fab':continue
        kind=node_name(item)
        if kind in ('fp_line','fp_rect'):
            points.extend(tuple(map(float,fields[key][1:3])) for key in ('start','end'))
        elif kind=='fp_poly':
            points.extend(tuple(map(float,n[1:3])) for n in fields['pts'][1:] if node_name(n)=='xy')
    return [(min(p[i] for p in points),max(p[i] for p in points)) for i in range(2)]


class ICEnvelopeGenerationTests(unittest.TestCase):
    def test_axes_and_centres_follow_independent_footprint_bodies(self):
        for name,row in model.MODELS.items():
            with self.subTest(name=name):
                bounds=body((model.FOOTPRINTS/(name+'.kicad_mod')).read_text())
                width,height=(b-a for a,b in bounds)
                self.assertGreater((row['dims'][0]-row['dims'][1])*(width-height),0)
                offset=row.get('offset_mm',(0,0,0))
                self.assertAlmostEqual(offset[0],sum(bounds[0])/2)
                self.assertAlmostEqual(-offset[1],sum(bounds[1])/2)

    def test_owned_model_generation_is_idempotent(self):
        for name,row in model.MODELS.items():
            text=(model.FOOTPRINTS/(name+'.kicad_mod')).read_text()
            once=model.footprint_with_model(text,row['file'],row.get('offset_mm',(0,0,0)))
            self.assertEqual(once,text)
            self.assertEqual(model.footprint_with_model(once,row['file'],row.get('offset_mm',(0,0,0))),once)

    def test_stale_transform_is_rebuilt_without_2d_changes(self):
        row=model.MODELS['DIP-8_W7.62mm'];name=row['file']
        original=(model.FOOTPRINTS/'DIP-8_W7.62mm.kicad_mod').read_text()
        start,end=model.owned_model_span(original,name)
        stale=original[:start]+original[start:end].replace('3.81 -3.81 0','0 0 0').replace('(rotate (xyz 0 0 0))','(rotate (xyz 0 0 90))')+original[end:]
        fixed=model.footprint_with_model(stale,name,row['offset_mm'])
        self.assertNotEqual(stale,fixed)
        self.assertEqual(fixed,original)
        a,b=model.owned_model_span(fixed,name);c,d=model.owned_model_span(stale,name)
        self.assertEqual(fixed[:a]+fixed[b:],stale[:c]+stale[d:])

    def test_foreign_and_duplicate_models_are_rejected(self):
        text=(model.FOOTPRINTS/'SOT-23-5.kicad_mod').read_text();name='IC_SOT-23-5.wrl'
        start,end=model.owned_model_span(text,name)
        for changed in (text.replace(name,'foreign.wrl'),text[:end]+text[start:end]+text[end:]):
            with self.assertRaises(ValueError):model.footprint_with_model(changed,name)

    def test_model_keyword_whitespace_cannot_add_a_second_model(self):
        text=(model.FOOTPRINTS/'SOT-23-5.kicad_mod').read_text();name='IC_SOT-23-5.wrl'
        changed=text.replace('(model ','(model\n')
        self.assertEqual(model.footprint_with_model(changed,name),text)

    def test_invalid_offsets_are_rejected(self):
        for offset in ((float('nan'),0,0),(0,float('inf'),0),(True,0,0),(0,0)):
            with self.assertRaises(ValueError):model.footprint_with_model('(footprint "x")','x.wrl',offset)


class NativeVRMLTransformTests(unittest.TestCase):
    def assertVector(self,got,want):
        for a,b in zip(got,want):self.assertAlmostEqual(a,b,places=10)

    def test_nested_rotation_translation_and_closed_sibling(self):
        text=('Transform { scale 100 100 100 children [] } '
              'Transform { scale 2 2 2 children [ Transform { '
              'translation 1 2 3 rotation 0 0 1 '+str(math.pi/2)+' children ['+MESH+'] } ] }')
        result=vrml.first_coordinate_geometry(text)
        self.assertVector(result['size'],(8,4,12))
        self.assertVector(result['mesh_axis_sizes'],(4,8,12))
        self.assertVector(result['center'],(2,4,6))
        self.assertEqual(result['transform_count'],2)

    def test_scale_orientation_and_nonzero_centre(self):
        text='Transform { center 1 2 0 scale 2 1 1 scaleOrientation 0 0 1 '+str(math.pi/2)+' children ['+MESH+'] }'
        result=vrml.first_coordinate_geometry(text)
        self.assertVector(result['size'],(2,8,6))
        self.assertVector(result['center'],(0,-2,0))

    def test_transform_fields_after_children_are_applied(self):
        result=vrml.first_coordinate_geometry('Transform { children ['+MESH+'] translation 1 2 3 }')
        self.assertVector(result['center'],(1,2,3))

    def test_reflection_preserves_positive_extents(self):
        result=vrml.first_coordinate_geometry('Transform { translation 1 2 -3 scale -2 3 -1 children ['+MESH+'] }')
        self.assertVector(result['size'],(4,12,6))
        self.assertVector(result['center'],(1,2,-3))

    def test_malformed_or_unsupported_scenes_fail_closed(self):
        scenes=[MESH[:-1],MESH.replace('-1 -2 -3','NaN NaN NaN'),
                MESH.replace('-1 -2 -3','1e999 -2 -3'),
                'Transform { mystery 3 children ['+MESH+'] }',
                'Transform { scale 1 1 1 scale 2 2 2 children ['+MESH+'] }',
                'Billboard { children ['+MESH+'] }',
                'Transform { rotation 0 0 0 1 children ['+MESH+'] }']
        for text in scenes:
            with self.subTest(text=text[:60]):
                with self.assertRaises(ValueError):vrml.first_coordinate_geometry(text)
