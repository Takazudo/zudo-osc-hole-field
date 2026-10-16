"""Synthetic comparator mutation tests; fixtures are never native evidence."""
import copy
import sys
import unittest
from pathlib import Path
import native_parity as n

REPO=Path(__file__).parent/'osc-validation'
EXPECTED,P=n.expected_from_source(REPO)


def fixture():
    comps=['components']; libs=['libparts']; nets={}
    for ref,w in EXPECTED.items():
        props=[['property',['name','MPN'],['value',w['mpn']]],
               ['property',['name','Manufacturer'],['value',w['manufacturer']]]]
        if not w['fitted']:
            props += [['property',['name',k]] for k in ('exclude_from_bom','exclude_from_board')]
        comps.append(['comp',['ref',ref],['value',w['value']],['footprint',w['footprint']],
            ['libsource',['lib',w['library']],['part',w['part']]],['tstamps',*w['tstamps']],*props])
        libs.append(['libpart',['lib',w['library']],['part',w['part']],
            ['pins',*[['pin',['num',pin]] for pin in w['pins']]]])
        for pin,net in w['pins'].items():
            if net is not None:
                nets.setdefault(net,[]).append(['node',['ref',ref],['pin',pin]])
    return ['export',comps,libs,['nets',*[['net',['name',name],*nodes] for name,nodes in nets.items()]]]


class Mutations(unittest.TestCase):
    def setUp(self): self.tree=fixture()
    def reject(self):
        with self.assertRaises(ValueError): n.compare(self.tree,EXPECTED,P)
    def test_baseline_explicit_nc_omission(self):
        result=n.compare(self.tree,EXPECTED,P)
        self.assertEqual((result['references'],result['physical_pins'],result['units']),(118,561,154))
        self.assertIn('RN7102:3',result['explicit_source_NC_omitted_from_native_nets'])
    def test_missing_source_land_fails(self):
        self.tree[1]=[x for x in self.tree[1] if not isinstance(x,list) or P.one(x,'ref')[1]!='TP17901']; self.reject()
    def test_wrong_net(self): self.tree[3][1][1][1]='WRONG'; self.reject()
    def test_duplicate_endpoint(self): self.tree[3][1].append(copy.deepcopy(self.tree[3][1][2])); self.reject()
    def test_missing_connected_endpoint(self): self.tree[3][1].pop(); self.reject()
    def test_missing_library_nc_pin(self):
        for lib in self.tree[2][1:]:
            if P.one(lib,'part')[1]=='A01_RN7102':
                pins=P.one(lib,'pins'); pins[:]=[x for x in pins if not isinstance(x,list) or P.one(x,'num')[1]!='3']
        self.reject()
    def test_missing_unit(self): P.one(self.tree[1][1],'tstamps').pop(); self.reject()
    def test_wrong_mpn(self): P.children(self.tree[1][1],'property')[0][2][1]='fabricated'; self.reject()
    def test_wrong_footprint(self): P.one(self.tree[1][1],'footprint')[1]='fabricated'; self.reject()
    def test_nc_connected_to_named_net(self): self.tree[3][1].append(['node',['ref','RN7102'],['pin','3']]); self.reject()
    def test_nc_singleton_allowed(self):
        self.tree[3].append(['net',['name','unconnected-(RN7102-Pad3)'],['node',['ref','RN7102'],['pin','3']]])
        n.compare(self.tree,EXPECTED,P)
    def test_missing_source_land_flags(self):
        for comp in self.tree[1][1:]:
            if P.one(comp,'ref')[1]=='TP17901':
                comp[:]=[x for x in comp if not isinstance(x,list) or x[0]!='property']
        self.reject()


if __name__=='__main__': unittest.main()
