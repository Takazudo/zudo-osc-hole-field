"""Adversarial tests of independently derived schematic connectivity."""
import copy
import json
import shutil
from pathlib import Path
import tempfile
import unittest
import stage17_parity as p

LIB = '(symbol "X:part" (symbol "part_1_1" (pin passive line (at -5 0 0) (number "1")) (pin passive line (at 5 0 180) (number "2"))))'
SYM = '(symbol (lib_id "X:part") (at 20 20 0) (unit 1) (property "Reference" "R1") (pin "1") (pin "2"))'

def doc(extra):
    return p.parse('(kicad_sch (lib_symbols '+LIB+') '+SYM+' '+extra+')')


class Connectivity(unittest.TestCase):
    def audit(self, text):
        return p.audit_documents([('sheet',doc(text))])[0]['resolved']

    def test_wire_connectivity_is_derived_from_pin_geometry(self):
        r=self.audit('(wire (pts (xy 15 20) (xy 5 20))) (global_label "A" (at 5 20 0)) (no_connect (at 25 20))')
        self.assertEqual(r,{'1':'A','2':None})

    def test_shifted_wire_is_disconnected(self):
        with self.assertRaisesRegex(ValueError,'disconnected'):
            self.audit('(wire (pts (xy 14 20) (xy 5 20))) (global_label "A" (at 5 20 0)) (no_connect (at 25 20))')

    def test_distinct_net_short_rejected(self):
        with self.assertRaisesRegex(ValueError,'shorted'):
            self.audit('(wire (pts (xy 15 20) (xy 25 20))) (global_label "A" (at 15 20 0)) (global_label "B" (at 25 20 0))')

    def test_nc_cannot_hide_connected_pin(self):
        with self.assertRaisesRegex(ValueError,'NC marker connected'):
            self.audit('(global_label "A" (at 15 20 0)) (no_connect (at 15 20)) (no_connect (at 25 20))')

    def test_orphan_nc_rejected(self):
        with self.assertRaisesRegex(ValueError,'orphan NC'):
            self.audit('(global_label "A" (at 15 20 0)) (no_connect (at 24 20))')

    def test_missing_instance_pin_rejected(self):
        d=doc('(global_label "A" (at 15 20 0)) (no_connect (at 25 20))')
        sym=p.children(d,'symbol')[0];sym.remove(p.children(sym,'pin')[0])
        with self.assertRaisesRegex(ValueError,'pin UUID inventory'):p.audit_documents([('x',d)])

    def test_rotation_uses_library_y_inversion(self):
        symbol=p.parse('(symbol (at 20 30 90))')
        self.assertEqual(p.world((5,2),symbol),(18,25))

    def test_transport_reads_actual_wire_end_labels(self):
        graph={'nodes':{'a':{'net':'N'},'b':{'net':'N'}},'edges':[{'from':'a','to':'b'}]}
        text='(kicad_sch (lib_symbols) (wire (pts (xy 0 0) (xy 5 0))) (global_label "a" (at 0 0)) (global_label "b" (at 5 0)))'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'transport-graph.kicad_sch';path.write_text(text)
            (Path(tmp)/'transport-source.json').write_text(json.dumps(graph))
            self.assertEqual(p.check_transport(path,{'transport_contract':graph})['edge_diagram_segments'],1)
            path.write_text(text.replace('"b"','"c"'))
            with self.assertRaisesRegex(ValueError,'topology'):p.check_transport(path,{'transport_contract':graph})

    def test_transport_orphan_label_rejected(self):
        graph={'nodes':{},'edges':[]}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'transport-graph.kicad_sch';path.write_text('(kicad_sch (lib_symbols) (global_label "a" (at 0 0)))')
            with self.assertRaisesRegex(ValueError,'orphan label'):p.check_transport(path,{'transport_contract':graph})


def emit(node):
    return '('+' '.join(emit(x) if isinstance(x,list) else json.dumps(x) for x in node)+')'


class GeneratedParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated=p.ROOT/'design/architecture-278/implementation/stage17/generated'
        cls.inputs=json.loads((p.ROOT/'design/architecture-278/implementation/stage16/inputs-report.json').read_text())

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'generated';shutil.copytree(self.generated,self.root)

    def check(self):
        return p.check(self.root/'a01.kicad_sch',self.inputs,self.root)

    def mutate_sheet(self,mutator):
        for path in sorted((self.root/'sheets').glob('*.kicad_sch')):
            tree=p.parse(path.read_text())
            if mutator(tree):path.write_text(emit(tree));return
        self.fail('mutation target not found')

    def test_generated_circuit_and_transport(self):
        self.assertEqual(self.check()['physical_pins'],561)
        self.assertEqual(p.check_transport(self.root/'transport-graph.kicad_sch',self.inputs)['edge_diagram_segments'],320)

    def test_wrong_actual_pin_label_rejected(self):
        def mutate(tree):p.children(tree,'global_label')[0][1]='WRONG';return True
        self.mutate_sheet(mutate)
        with self.assertRaises(ValueError):self.check()

    def test_displaced_label_rejected(self):
        def mutate(tree):p.one(p.children(tree,'global_label')[0],'at')[1]='999';return True
        self.mutate_sheet(mutate)
        with self.assertRaises(ValueError):self.check()

    def test_orphan_extra_label_rejected(self):
        def mutate(tree):tree.append(p.parse('(global_label "EXTRA" (at 999 999 0))'));return True
        self.mutate_sheet(mutate)
        with self.assertRaisesRegex(ValueError,'orphan circuit label'):self.check()

    def test_duplicate_uuid_rejected(self):
        def mutate(tree):
            nodes=p.children(tree,'global_label');p.one(nodes[1],'uuid')[1]=p.one(nodes[0],'uuid')[1];return True
        self.mutate_sheet(mutate)
        with self.assertRaisesRegex(ValueError,'duplicate schematic UUID'):self.check()

    def test_missing_nc_marker_rejected(self):
        def mutate(tree):
            nodes=p.children(tree,'no_connect')
            if nodes:tree.remove(nodes[0]);return True
        self.mutate_sheet(mutate)
        with self.assertRaises(ValueError):self.check()

    def test_removed_network_ep_unit_rejected(self):
        def mutate(tree):
            for sym in p.children(tree,'symbol'):
                if p.properties(sym)['Reference']=='RN7101' and p.one(sym,'unit')[1]=='5':tree.remove(sym);return True
        self.mutate_sheet(mutate)
        with self.assertRaises(ValueError):self.check()

    def test_unselected_mpn_cannot_be_invented(self):
        def mutate(tree):
            for sym in p.children(tree,'symbol'):
                if p.properties(sym)['Reference']=='R7101':
                    next(x for x in p.children(sym,'property') if x[1]=='MPN')[2]='INVENTED';return True
        self.mutate_sheet(mutate)
        with self.assertRaisesRegex(ValueError,'MPN mismatch'):self.check()

    def test_embedded_external_library_mismatch(self):
        path=self.root/'A01Candidate.kicad_sym';tree=p.parse(path.read_text())
        definition=p.children(tree,'symbol')[0];definition.append(['property','Extra','drift'])
        path.write_text(emit(tree))
        with self.assertRaisesRegex(ValueError,'embedded/external'):self.check()

    def test_footprint_pad_geometry_drift(self):
        path=self.root/'A01Candidate.pretty/KEMET_T491C475K050AT.kicad_mod'
        tree=p.parse(path.read_text());p.one(p.children(tree,'pad')[0],'at')[1]='99';path.write_text(emit(tree))
        with self.assertRaisesRegex(ValueError,'pad position drift'):self.check()

    def test_wrong_unit_value_rejected(self):
        def mutate(tree):
            sym=p.children(tree,'symbol')[0];next(x for x in p.children(sym,'property') if x[1]=='Value')[2]='wrong';return True
        self.mutate_sheet(mutate)
        with self.assertRaisesRegex(ValueError,'unit value mismatch'):self.check()

    def test_population_and_instance_mutations(self):
        for key in ('dnp','reference','path'):
            with self.subTest(key=key):
                def mutate(tree):
                    sym=p.children(tree,'symbol')[0]
                    if key=='dnp':p.one(sym,key)[1]='yes'
                    else:
                        instance=p.one(p.one(p.one(sym,'instances'),'project'),'path')
                        if key=='path':instance[1]='/wrong'
                        else:p.one(instance,'reference')[1]='GHOST'
                    return True
                self.mutate_sheet(mutate)
                with self.assertRaises(ValueError):self.check()
                shutil.rmtree(self.root);shutil.copytree(self.generated,self.root)

    def mutate_coherent_library(self,mutator):
        path=self.root/'A01Candidate.kicad_sym';tree=p.parse(path.read_text())
        definition=next(x for x in p.children(tree,'symbol') if x[1]=='A01_R7101');mutator(definition);path.write_text(emit(tree))
        for path in (self.root/'sheets').glob('*.kicad_sch'):
            tree=p.parse(path.read_text())
            for definition in p.children(p.one(tree,'lib_symbols'),'symbol'):
                if definition[1]=='A01Candidate:A01_R7101':mutator(definition)
            path.write_text(emit(tree))

    def test_coherent_library_default_identity_rejected(self):
        def mutate(definition):next(x for x in p.children(definition,'property') if x[1]=='MPN')[2]='INVENTED'
        self.mutate_coherent_library(mutate)
        with self.assertRaisesRegex(ValueError,'library default identity'):self.check()

    def test_coherent_retained_pin_type_drift_rejected(self):
        def mutate(definition):
            for sub in p.children(definition,'symbol'):
                for pin in p.children(sub,'pin'):pin[1]='power_out'
        self.mutate_coherent_library(mutate)
        with self.assertRaisesRegex(ValueError,'pin specification drift'):self.check()

    def test_transport_pin_net_mutation(self):
        def mutate(tree):
            for sym in p.children(tree,'symbol'):
                if p.properties(sym)['Reference']=='J17901':
                    libid=p.one(sym,'lib_id')[1];definition=next(x for x in p.children(p.one(tree,'lib_symbols'),'symbol') if x[1]==libid)
                    point=p.world(p.pins(definition,1)['1'],sym)
                    label=next(x for x in p.children(tree,'global_label') if p.xy(x)==point);label[1]='WRONG';return True
        self.mutate_sheet(mutate)
        with self.assertRaises(ValueError):self.check()

    def test_transport_nc_pin_marker_removed(self):
        def mutate(tree):
            for sym in p.children(tree,'symbol'):
                if p.properties(sym)['Reference']=='J17909':
                    libid=p.one(sym,'lib_id')[1];definition=next(x for x in p.children(p.one(tree,'lib_symbols'),'symbol') if x[1]==libid)
                    point=p.world(p.pins(definition,1)['a1'],sym)
                    nc=next(x for x in p.children(tree,'no_connect') if p.xy(x)==point);tree.remove(nc);return True
        self.mutate_sheet(mutate)
        with self.assertRaises(ValueError):self.check()

    def test_transport_mpn_or_source_endpoint_cannot_change(self):
        for key in ('MPN','SourceGraphNodes'):
            with self.subTest(key=key):
                def mutate(tree):
                    for sym in p.children(tree,'symbol'):
                        if p.properties(sym)['Reference']=='J17909':
                            next(x for x in p.children(sym,'property') if x[1]==key)[2]='WRONG' if key=='MPN' else '{}';return True
                self.mutate_sheet(mutate)
                with self.assertRaises(ValueError):self.check()
                shutil.rmtree(self.root);shutil.copytree(self.generated,self.root)

    def test_unbound_din_footprint_cannot_be_invented(self):
        def mutate(tree):
            for sym in p.children(tree,'symbol'):
                if p.properties(sym)['Reference']=='J17909':
                    next(x for x in p.children(sym,'property') if x[1]=='Footprint')[2]='A01Candidate:R0603';return True
        self.mutate_sheet(mutate)
        with self.assertRaises(ValueError):self.check()


if __name__=='__main__':unittest.main()
