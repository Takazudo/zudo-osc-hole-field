"""Class-only DSN pilot rejects format and membership drift."""
import unittest
from scripts.pcbgen.selective_dsn import transform

SOURCE='''(pcb "pilot"
  (parser (string_quote ") (space_in_quoted_tokens on))
  (resolution um 10)
  (unit um)
  (structure (boundary (rect pcb 0 0 1000 1000)))
  (placement (component U1))
  (library (image U1))
  (network
    (net A (pins U1-1 U1-2))
    (net B (pins U1-3 U1-4))
    (net AGND (pins U1-5 U1-6))
    (net +12V (pins U1-7 U1-8))
    (class kicad_default A B (circuit (use_via V)) (rule (width 200)))
    (class Ground AGND (circuit (use_via V)) (rule (width 500)))
    (class Rails +12V (circuit (use_via V)) (rule (width 400)))
  )
  (wiring (wire (path F.Cu 200 0 0 1000 1000) (net AGND)))
)'''

class SelectiveDsnTests(unittest.TestCase):
    def test_only_class_membership_changes(self):
        result,receipt=transform(SOURCE,['A'])
        self.assertIn('(class Pilot A',result)
        self.assertIn('(class kicad_default B',result)
        self.assertIn('(wiring (wire (path F.Cu 200 0 0 1000 1000) (net AGND)))',result)
        self.assertEqual(receipt['unchanged_net_descriptors'],4)
    def test_unknown_or_unsafe_input_fails_closed(self):
        cases=(SOURCE.replace('(net A','(pair A B)(net A'),
               SOURCE.replace('(net A','(net Z (pins U1-1 U1-2))(net A'),
               SOURCE.replace('(class Ground AGND','(class Ground B AGND'),
               SOURCE.replace('(wiring','(mystery foo)(wiring'))
        for case in cases:
            with self.subTest(case=case[-80:]),self.assertRaises(ValueError):transform(case,['A'])
        for chosen in (['AGND'],['+12V'],['missing'],['A','A']):
            with self.subTest(chosen=chosen),self.assertRaises(ValueError):transform(SOURCE,chosen)

if __name__=='__main__':unittest.main()
