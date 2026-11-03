"""Synthetic XML and negative source tests; never a native receipt."""
import copy
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import stage18_observation as n
import stage18_compat as s

EXPECTED=n.expected_from_source()


def fixture():
    root=ET.Element('export',version='E')
    ET.SubElement(ET.SubElement(root,'design'),'tool').text='Eeschema 10.0.6'
    comps=ET.SubElement(root,'components');libs=ET.SubElement(root,'libparts');nets=ET.SubElement(root,'nets')
    by_net={}
    names=n.net_names(net for w in EXPECTED.values() for net in w['pins'].values() if net is not None)
    for ref,w in EXPECTED.items():
        c=ET.SubElement(comps,'comp',ref=ref)
        for key in ('value','footprint','datasheet','description'):ET.SubElement(c,key).text=w[key]
        ET.SubElement(c,'libsource',lib=w['library'],part=w['part'])
        for key,value in w['properties'].items():ET.SubElement(c,'property',name=key,value=value)
        fields=ET.SubElement(c,'fields')
        for key,value in w['field_candidates'][0]['fields'].items():ET.SubElement(fields,'field',name=key).text=value
        ET.SubElement(c,'tstamps').text=' '.join(w['tstamps'])
        ET.SubElement(c,'sheetpath',**w['sheetpath'])
        units=ET.SubElement(c,'units')
        for name,pins in w['units'].items():
            dest=ET.SubElement(ET.SubElement(units,'unit',name=name),'pins')
            for pin in pins:ET.SubElement(dest,'pin',num=pin)
        lib=ET.SubElement(libs,'libpart',lib=w['library'],part=w['part'])
        lp=ET.SubElement(lib,'pins')
        for pin,net in w['pins'].items():
            ET.SubElement(lp,'pin',num=pin)
            name=names['source_to_xml'][net] if net is not None else f'unconnected-({ref}-Pad{pin})'
            if name not in by_net:by_net[name]=ET.SubElement(nets,'net',name=name,code=str(len(by_net)+1))
            ET.SubElement(by_net[name],'node',ref=ref,pin=pin,pintype='passive'+('+no_connect' if net is None else ''))
    return root


class ObservationTests(unittest.TestCase):
    def setUp(self):self.xml=fixture()
    def comp(self,ref='U7102'):return self.xml.find(f'components/comp[@ref="{ref}"]')
    def reject(self):
        with self.assertRaises((ValueError,KeyError,ET.ParseError)):
            n.compare(n.parse_xml(ET.tostring(self.xml,encoding='unicode')),EXPECTED)
    def test_complete_synthetic_xml(self):
        r=n.compare(n.parse_xml(ET.tostring(self.xml,encoding='unicode')),EXPECTED)
        self.assertEqual((r['references'],r['physical_pins'],r['unit_UUIDs'],r['native_net_nodes']),(118,561,154,561))
        self.assertEqual(len(r['explicit_singleton_NCs']),196)
    def test_missing_annotation(self):self.xml.find('components').remove(self.comp('TP17901'));self.reject()
    def test_extra_component(self):self.xml.find('components').append(ET.Element('comp',ref='FAKE'));self.reject()
    def test_duplicate_component(self):self.xml.find('components').append(copy.deepcopy(self.comp()));self.reject()
    def test_missing_connected_endpoint(self):
        net=next(x for x in self.xml.findall('nets/net') if not x.get('name').startswith('unconnected-'))
        net.remove(net[0]);self.reject()
    def test_missing_nc_endpoint(self):
        net=next(x for x in self.xml.findall('nets/net') if x.get('name').startswith('unconnected-'))
        self.xml.find('nets').remove(net);self.reject()
    def test_missing_annotation_endpoint(self):
        node=self.xml.find('nets/net/node[@ref="TP17901"]')
        net=next(x for x in self.xml.findall('nets/net') if node in list(x))
        net.remove(node);self.reject()
    def test_extra_endpoint(self):
        ET.SubElement(self.xml.find('nets/net'),'node',ref='U7102',pin='999',pintype='passive');self.reject()
    def test_duplicate_endpoint(self):
        net=self.xml.find('nets/net');net.append(copy.deepcopy(net[0]));self.reject()
    def test_rewire(self):self.xml.find('nets/net').set('name','WRONG');self.reject()
    def test_ep_ground_rewired(self):
        node=self.xml.find('nets/net/node[@ref="RN7102"][@pin="9"]')
        old=next(x for x in self.xml.findall('nets/net') if node in list(x));old.remove(node)
        self.xml.find('nets/net').append(node);self.reject()
    def test_nc_short_to_signal(self):
        nc=next(x for x in self.xml.findall('nets/net') if x.get('name').startswith('unconnected-'))
        target=next(x for x in self.xml.findall('nets/net') if not x.get('name').startswith('unconnected-'))
        target.append(nc[0]);self.xml.find('nets').remove(nc);self.reject()
    def test_nc_short_to_nc(self):
        a,b=[x for x in self.xml.findall('nets/net') if x.get('name').startswith('unconnected-')][:2]
        a.append(b[0]);self.xml.find('nets').remove(b);self.reject()
    def test_missing_nc_marker(self):
        net=next(x for x in self.xml.findall('nets/net') if x.get('name').startswith('unconnected-'))
        net[0].set('pintype','passive');self.reject()
    def test_missing_unit_uuid(self):self.comp().find('tstamps').text=' '.join(EXPECTED['U7102']['tstamps'][:-1]);self.reject()
    def test_duplicate_unit_uuid(self):self.comp().find('tstamps').text+=' '+EXPECTED['U7102']['tstamps'][0];self.reject()
    def test_wrong_unit_uuid(self):self.comp().find('tstamps').text=self.comp().find('tstamps').text.replace(EXPECTED['U7102']['tstamps'][0],'wrong');self.reject()
    def test_missing_unit_slot(self):self.comp().find('units').remove(self.comp().find('units/unit'));self.reject()
    def test_unit_pin_swap(self):self.comp().find('units/unit/pins/pin').set('num','999');self.reject()
    def test_missing_library_pin(self):
        pins=self.xml.find('libparts/libpart/pins');pins.remove(pins[0]);self.reject()
    def test_wrong_mpn(self):self.comp().find('property[@name="MPN"]').set('value','substitute');self.reject()
    def test_wrong_field_mpn(self):self.comp().find('fields/field[@name="MPN"]').text='substitute';self.reject()
    def test_wrong_manufacturer(self):self.comp().find('property[@name="Manufacturer"]').set('value','substitute');self.reject()
    def test_wrong_value(self):self.comp().find('value').text='substitute';self.reject()
    def test_wrong_footprint(self):self.comp().find('footprint').text='substitute';self.reject()
    def test_wrong_library(self):self.comp().find('libsource').set('part','substitute');self.reject()
    def test_property_unit_substitution(self):
        c=self.comp('U7104');props=EXPECTED['U7104']['properties'];others=EXPECTED['U7104']['unit_metadata'].values()
        alt=next(r['properties']['Role'] for r in others if r['properties']['Role']!=props['Role'])
        c.find('property[@name="Role"]').set('value',alt);self.reject()
    def test_aggregate_metadata_substitution(self):self.comp().find('fields/field[@name="Role"]').text='invented';self.reject()
    def test_duplicate_property(self):self.comp().append(copy.deepcopy(self.comp().find('property')));self.reject()
    def test_duplicate_field(self):self.comp().find('fields').append(copy.deepcopy(self.comp().find('fields/field')));self.reject()
    def test_annotation_fitted(self):
        c=self.comp('TP17901');c.remove(c.find('property[@name="exclude_from_board"]'));self.reject()
    def test_annotation_bom_flag(self):
        c=self.comp('TP17901');c.remove(c.find('property[@name="exclude_from_bom"]'));self.reject()
    def test_fitted_part_excluded(self):ET.SubElement(self.comp(),'property',name='exclude_from_board');self.reject()
    def test_wrong_sheet(self):self.comp().find('sheetpath').set('tstamps','/wrong/');self.reject()
    def test_wrong_version(self):self.xml.find('design/tool').text='Eeschema 10.0.7';self.reject()
    def test_duplicate_net_name(self):self.xml.find('nets').append(copy.deepcopy(self.xml.find('nets/net')));self.reject()
    def test_duplicate_net_code(self):self.xml.findall('nets/net')[1].set('code',self.xml.find('nets/net').get('code'));self.reject()
    def test_dtd_rejected(self):
        with self.assertRaisesRegex(ValueError,'declarations'):n.parse_xml('<!DOCTYPE export><export version="E"/>')


class EncodingAndAggregationTests(unittest.TestCase):
    def test_all_tokens(self):
        for token,value in n.TOKENS.items():self.assertEqual(n.unescape('{'+token+'}'),value)
    def test_nested_and_protected(self):
        for prefix in '$~^_':self.assertEqual(n.unescape(prefix+'{slash}'),prefix+'{slash}')
        self.assertEqual(n.unescape('{outer{slash}}'),'{outer/}')
        self.assertEqual(n.unescape('{outer{slash}'),'{outer/')
        self.assertEqual(n.unescape('{brace}slash}'),'{slash}')
    def test_roundtrip(self):
        m=n.net_names(['A/B','C{lt}D','AGND'])
        for original,xml in m['source_to_xml'].items():self.assertEqual(m['xml_to_source'][xml],original)
        self.assertEqual(m['source_to_internal']['A/B'],'A{slash}B')
    def test_slash_collision(self):
        with self.assertRaisesRegex(ValueError,'collision'):n.net_names(['A/B','A{slash}B'])
    def test_newline_collision(self):
        with self.assertRaisesRegex(ValueError,'collision'):n.net_names(['AB','A\nB'])
    def test_other_token_collision(self):
        with self.assertRaisesRegex(ValueError,'collision'):n.net_names(['A<B','A{lt}B'])
    def test_algorithm_does_not_allow_independent_field_mix(self):
        units=[{'unit':1},{'unit':2}];props=[{'Role':'low','Island':'low'},{'Role':'high','Island':'high'}]
        results=[x['fields'] for x in n.aggregate_fields(units,props,1)]
        self.assertEqual({(x['Role'],x['Island']) for x in results},{('low','low'),('high','high')})
        self.assertNotIn({'Role':'low','Island':'high','Footprint':'','Datasheet':'','Description':''},results)
    def test_running_minimum_not_lowest_nonblank(self):
        units=[{'unit':1},{'unit':2}];props=[{'Role':''},{'Role':'high'}]
        results=n.aggregate_fields(units,props,2)
        self.assertEqual({x['fields']['Role'] for x in results},{''})
    def test_representative_differs_from_aggregate(self):
        self.assertTrue(any(any(c['fields'].get('Role')!=w['properties'].get('Role') for c in w['field_candidates']) for w in EXPECTED.values()))


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        s.old.write_files(s.build_files(),self.root)
    def tearDown(self):self.tmp.cleanup()
    def mutate(self,transform):
        path=next(x for x in (self.root/'sheets').glob('*.kicad_sch') if '"U7102"' in x.read_text())
        path.write_text(transform(path.read_text()))
        with self.assertRaises(ValueError):s.source_check(self.root/'a01.kicad_sch')
    def test_deterministic(self):self.assertEqual(s.build_files(),s.build_files())
    def test_whole_package_single_sheet(self):
        _,rows=s.source_check(self.root/'a01.kicad_sch')
        for ref in EXPECTED:self.assertEqual(len({r['sheet'] for r in rows if r['ref']==ref}),1)
    def test_source_identity_change(self):self.mutate(lambda t:t.replace('"U7102"','"U7999"'))
    def test_source_metadata_change(self):self.mutate(lambda t:t.replace('UNVALIDATED SOURCE CANDIDATE','ALTERED'))
    def test_source_missing_unit(self):self.mutate(lambda t:t.replace('(unit 5)','(unit 4)',1))
    def test_source_uuid_change(self):self.mutate(lambda t:t.replace(EXPECTED['U7102']['tstamps'][0],'00000000-0000-0000-0000-000000000000'))
    def test_source_rewire(self):self.mutate(lambda t:t.replace('(global_label "AGND"','(global_label "WRONG"',1))
    def test_preserve_original_uuid_roster(self):
        old={s.p.one(r['symbol'],'uuid')[1] for r in s.original_units()}
        new={u for w in EXPECTED.values() for u in w['tstamps']}
        self.assertEqual(old,new);self.assertEqual(len(new),154)


if __name__=='__main__':unittest.main()
