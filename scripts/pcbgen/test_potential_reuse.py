"""A changed physical source support cannot reuse a prior current certificate."""
import unittest
import shapely
from shapely.geometry import box
from scripts.pcbgen.recompute_ground_potential import validate_profiles


class PotentialReuseTests(unittest.TestCase):
    def test_support_and_identity_order_are_checked(self):
        load={'ref':'U1','pad':'1','kind':'load','layer':3,'patch':box(0,0,.25,.25)}
        main={'ref':'TP1','pad':'1','kind':'main','layer':3,'patch':box(1,1,1.25,1.25)}
        expected=[{**{k:p[k] for k in ('ref','pad','kind','layer')},
                   'patch_geojson':shapely.geometry.mapping(p['patch'])} for p in (load,main)]
        validate_profiles(expected,[load],main)
        for changed in (dict(load,pad='2'),dict(load,patch=box(0,0,.26,.25))):
            with self.assertRaisesRegex(ValueError,'cannot be reused'):
                validate_profiles(expected,[changed],main)


if __name__=='__main__':unittest.main()
