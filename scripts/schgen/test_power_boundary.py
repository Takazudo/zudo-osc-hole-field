"""Fault injections against the native requirement-only power boundary audit."""
import unittest
from scripts.schgen.check_power_boundary import build


def component(ref, part):
    return f'''(comp (ref "{ref}")
      (libsource (lib "zudo-osc-hole-field") (part "{part}"))
      (property (name "Implementation") (value "REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE"))
      (property (name "AbstractBoundary") (value "true"))
      (property (name "Footprint")) (property (name "MPN")))'''


def net(name, *nodes):
    return '(net (name "'+name+'") '+' '.join(f'(node (ref "{ref}") (pin "{pin}"))' for ref,pin in nodes)+')'


def fixture():
    rails=[('+12V_IN','+12V','1','4','R1'),('-12V_IN','-12V','2','5','R2'),('+5V_IN','+5V','3','6','R3')]
    nets=[]
    for raw,load,ip,op,ref in rails:
        nets.append(net(raw,('CN301',ip),('XB301',ip)))
        nets.append(net(load,('XB301',op),(ref,'1')))
    nets.append(net('AGND',*(('CN301',str(i)) for i in range(5,9)),('XB301','7')))
    nets.append(net('unconnected-(CN301-Pin_4)',('CN301','4')))
    return '(export (components '+component('CN301','OSC_EXT_INLET_R1')+component('XB301','OSC_EXT_BOUNDARY_R1')+') (nets '+' '.join(nets)+'))'


class PowerBoundaryTests(unittest.TestCase):
    def test_native_contract_and_fault_injection(self):
        native=fixture()
        self.assertFalse(build(native, 'R1,R2,R3')['protection_implemented'])
        with self.assertRaisesRegex(ValueError,'raw inlet net'):
            build(native.replace('(node (ref "CN301") (pin "1"))','(node (ref "CN301") (pin "2"))',1))
        with self.assertRaisesRegex(ValueError,'inlet directly joined|raw inlet net'):
            build(native.replace('(node (ref "R1") (pin "1"))','(node (ref "CN301") (pin "1"))',1))
        with self.assertRaisesRegex(ValueError,'leaked into KiCad BOM'):
            build(native, 'CN301,R1,R2,R3')
        with self.assertRaisesRegex(ValueError,'non-orderable status'):
            build(native.replace('(value "true")','(value "false")',1))

if __name__=='__main__':unittest.main()
