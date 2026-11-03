import copy
import json
import unittest
import stage17_assets as m


class Assets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inp=json.loads((m.previous.OUT/'inputs-report.json').read_text())
        cls.files,cls.bindings=m.build_assets(cls.inp)

    def test_complete_pin_and_unit_coverage(self):
        self.assertEqual(len(self.bindings),86)
        self.assertEqual(sum(len(b['pins']) for b in self.bindings.values()),291)
        self.assertEqual(sum(len(b['symbol_units']) for b in self.bindings.values()),122)
        for ref,b in self.bindings.items():self.assertEqual(set(b['pins']),set(self.inp['packages'][ref]['pins']))

    def test_ep_not_resistor_common_and_unused_retained(self):
        for ref in ('RN7101','RN7102'):
            b=self.bindings[ref]
            self.assertEqual(b['pin_to_unit'],{'1':1,'8':1,'2':2,'7':2,'3':3,'6':3,'4':4,'5':4,'9':5})
            self.assertEqual(b['pins']['9']['name'],'EP_SHIELD')
        self.assertTrue(all(self.inp['packages']['RN7102']['pins'][p] is None for p in ('3','4','5','6')))

    def test_cap_polarity_and_frozen_land_geometry(self):
        for ref in ('C7101','C7102'):
            b=self.bindings[ref]; name=b['footprint_lib_id'].split(':')[1]
            fp=m.sexpr(self.files[m.LIB+'.pretty/'+name+'.kicad_mod'])
            pads={p[1]:p for p in fp if isinstance(p,list) and p and p[0]=='pad'}
            g=self.inp['capacitor_overrides'][ref]['geometry']
            for number,p in pads.items():
                self.assertEqual(list(map(float,m.field(p,'at'))),g['pads_mm'][number])
                self.assertEqual(list(map(float,m.field(p,'size'))),g['pad_sizes_mm'][number])
            self.assertEqual(b['pins']['1']['name'],'+')
            self.assertEqual(b['pins']['2']['name'],'-')
            self.assertEqual(self.inp['packages'][ref]['pins']['2'],'AGND')
            self.assertEqual(b['models'],[])

    def test_unresolved_default_mpn_is_not_template_identity(self):
        lib=m.sexpr(self.files[m.LIB+'.kicad_sym'])
        symbols={n[1]:n for n in lib if isinstance(n,list) and n and n[0]=='symbol'}
        missing=0
        for ref,row in self.inp['packages'].items():
            properties=m.previous.props(symbols['A01_'+ref])
            self.assertEqual(properties['MPN'],row['selected_mpn'] or '')
            self.assertEqual(properties['LCSC'],row['supplier_order_code'] or '')
            if row['selected_mpn'] is None:missing+=1
        self.assertEqual(missing,19)

    def test_retained_footprint_geometry_unchanged_after_model_localization(self):
        for ref,b in self.bindings.items():
            if not b['source_footprint_path']:continue
            original=m.sexpr((m.ROOT/b['source_footprint_path']).read_text())
            name=b['footprint_lib_id'].split(':')[1]
            isolated=m.sexpr(self.files[m.LIB+'.pretty/'+name+'.kicad_mod'])
            remove_models=lambda nodes:[n for n in nodes if not(isinstance(n,list) and n and n[0]=='model')]
            self.assertEqual(remove_models(original),remove_models(isolated),ref)

    def test_model_files_retained_and_paths_local(self):
        for b in self.bindings.values():
            for model in b['models']:
                self.assertEqual(self.files[model['isolated_path']],(m.ROOT/model['source']).read_text())
        for name,text in self.files.items():
            if name.endswith('.kicad_mod'):self.assertNotIn('${KIPRJMOD}/../../',text)

    def test_source_pin_loss_rejected(self):
        inp=copy.deepcopy(self.inp);del inp['packages']['RN7102']['pins']['9']
        with self.assertRaises(ValueError):m.build_assets(inp)

    def test_all_retained_transport_headers_copied_without_reselection(self):
        transport=json.loads(self.files['transport-asset-bindings.json'])
        self.assertEqual(set(transport),set(self.inp['transport_contract']['headers']))
        for row in transport.values():
            name=row['footprint_lib_id'].split(':')[1]
            original=m.sexpr((m.ROOT/row['source']).read_text())
            isolated=m.sexpr(self.files[m.LIB+'.pretty/'+name+'.kicad_mod'])
            remove_models=lambda nodes:[n for n in nodes if not(isinstance(n,list) and n and n[0]=='model')]
            self.assertEqual(remove_models(original),remove_models(isolated))
            self.assertFalse(row['native_validated'])


if __name__=='__main__':unittest.main()
