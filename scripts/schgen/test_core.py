"""Pure-Python generator contract tests."""
from dataclasses import replace
from pathlib import Path
import unittest
from design.spec.modules.synthetic import example
from scripts.schgen.core import LibrarySymbol, Part, Family, Instance, designator, render, uid, validate_family
from scripts.schgen.verify_netlist import verify

FIX = Path(__file__).parent/'fixtures'
LIB = {f'Fixture:{name}': LibrarySymbol.from_fixture(f'Fixture:{name}', FIX/f'{name}.kicad_sympart')
       for name in ('LM2902','LM2903','R','Conn_01x02','PWR_FLAG','GND','VCC')}

class GeneratorTests(unittest.TestCase):
    def test_uuid_derivation(self):
        self.assertEqual(uid('sheet:SYN1'), uid('sheet:SYN1'))
        self.assertNotEqual(uid('sheet:SYN1'), uid('sheet:SYN2'))

    def test_designators_and_panel_lock(self):
        family, instances = example()
        self.assertEqual(designator(family[0].parts[0], instances[2]), 'U301')
        self.assertEqual(designator(replace(family[0].parts[0], panel_ref='J101'), instances[0]), 'J101')
        with self.assertRaisesRegex(ValueError, 'collision'):
            p=replace(next(x for x in family[0].parts if x.key=='R1'), panel_ref='J101')
            q=replace(next(x for x in family[0].parts if x.key=='R2'), panel_ref='J101')
            render((Family('bad',(p,q)),), (Instance('bad','BAD',1),), LIB)

    def test_multiunit_assignment_requires_every_unit(self):
        families,_=example()
        validate_family(families[0], LIB)
        bad=replace(families[0],parts=tuple(p for p in families[0].parts if p.key!='U1.4'))
        with self.assertRaisesRegex(ValueError, 'all symbol units'):
            validate_family(bad,LIB)
        p=families[0].parts[0]
        with self.assertRaisesRegex(ValueError, 'pin map'):
            validate_family(replace(families[0],parts=(replace(p,pins={'1':'X'}),*families[0].parts[1:])),LIB)

    def test_paging_and_local_net_scope(self):
        families, instances = example()
        f = families[0]
        moved = tuple(replace(p, page=2) if p.key == 'J1' else p for p in f.parts)
        with self.assertRaisesRegex(ValueError, 'spans pages'):
            validate_family(replace(f, parts=moved), LIB)
        isolated = replace(next(p for p in f.parts if p.key == 'R2'), page=2, pins={'1':'P2_A','2':'P2_B'})
        rest = tuple(p for p in f.parts if p.key != 'R2')
        changed = replace(f, parts=(*rest, isolated))
        generated = render((changed,), instances[:3], LIB)
        self.assertIn('sheets/synthetic-p2.kicad_sch', generated)
        self.assertIn('(reference \"R102\")', generated['sheets/synthetic-p2.kicad_sch'])
        self.assertIn('SYN1-P2', generated['zudo-osc-hole-field.kicad_sch'])

    def test_attributes_and_instance_paths(self):
        families, instances=example()
        generated=render(families,instances,LIB)
        sheet=generated['sheets/synthetic.kicad_sch']
        for name in ('MPN','Manufacturer','LCSC','Block','Role','PanelUid','Island','Sensitive'):
            self.assertIn(f'(property "{name}"',sheet)
        for inst in instances[:3]:
            self.assertIn(f'(reference "U{inst.index}01")',sheet)
        self.assertIn('(no_connect',sheet)
        self.assertEqual(generated, render(families,instances,LIB))


if __name__=='__main__': unittest.main()
