import copy
import json
import unittest
import stage16_inputs as m


class Inputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        b = m.packages.OUT.parent
        cls.args = [json.loads((b/p).read_text()) for p in (
            'stage10/inventory-report.json', 'stage15/package-report.json', 'stage15/interfaces-report.json',
            'stage13/capacitor-input.json', 'stage15/package-input.json')]
        cls.args += [m.schematic_symbols((m.ROOT/m.SCHEMATIC).read_text()), {}]

    def test_population_and_ep_outside_units(self):
        r = m.analyze(*self.args)
        self.assertEqual((r['counts']['packages'], r['counts']['physical_pins_including_NC'], r['counts']['unit_records']), (86, 291, 120))
        self.assertEqual((r['counts']['connected_pins'], r['counts']['NC_pins'], r['counts']['power_return_endpoints']), (271, 20, 108))
        self.assertEqual(r['packages']['RN7102']['extra_package_pins_outside_element_units'], {'9': 'AGND'})
        self.assertTrue({'RN7102:3', 'RN7102:4', 'RN7102:5', 'RN7102:6'} <= set(r['NC_endpoints']))

    def test_old_cap_footprint_never_promoted(self):
        r = m.analyze(*self.args)
        for ref in ('C7101', 'C7102'):
            p = r['packages'][ref]
            self.assertIsNone(p['footprint']['path'])
            self.assertTrue(p['footprint']['captured_path'].endswith('C0603.kicad_mod'))
            self.assertEqual(p['symbol']['paths'], [])
            self.assertFalse(p['footprint']['native_ready'])
        self.assertEqual(r['packages']['C7101']['selected_mpn'], 'T491C475K050AT')
        self.assertEqual(r['packages']['C7101']['canonical']['mpn'], 'GRM188R71H104KA93D')

    def test_unselected_resistor_is_not_inferred(self):
        r = m.analyze(*self.args)
        self.assertIsNone(r['packages']['R7101']['selected_mpn'])
        self.assertIn('EXACT_MPN_UNSELECTED', r['packages']['R7101']['gaps'])

    def test_graph_pin_or_geometry_drift_rejected(self):
        for key, value in [('net', 'AGND'), ('pad_xyz_mm', [0, 0, 0])]:
            args = copy.deepcopy(self.args); args[2]['nodes']['RN7101:1'][key] = value
            with self.assertRaises(ValueError): m.analyze(*args)

    def test_wrong_network_alias_rejected(self):
        args = copy.deepcopy(self.args)
        args[1]['endpoint_aliases']['R7121:1'] = 'RN7101:2'
        with self.assertRaises(ValueError): m.analyze(*args)

    def test_duplicate_board_reference_rejected(self):
        block = '\t(footprint "x"\n\t\t(property "Reference" "R1")\n\t)\n'
        with self.assertRaises(ValueError): m.board_packages(block*2, {'R1'})

    def test_board_parser_preserves_raw_nc_and_multiple_pads(self):
        text = '\t(footprint "x"\n\t\t(property "Reference" "R1")\n\t\t(pad "1" smd rect (at 0 0) (net "AGND"))\n\t\t(pad "2" smd rect (at 1 0) (net "unconnected-(R1-Pad2)"))\n\t)\n'
        r = m.board_packages(text, {'R1'})['R1']
        self.assertEqual(r['pads']['1'][0]['normalized_net'], 'AGND')
        self.assertIsNone(r['pads']['2'][0]['normalized_net'])
        self.assertIn('unconnected', r['pads']['2'][0]['raw_net'])

    def test_missing_native_observation_cannot_imply_readiness(self):
        r = m.analyze(*self.args)
        self.assertFalse(r['native_ready']); self.assertFalse(r['hardware_acceptance'])
        self.assertIsNone(r['native_comparison']['U7101']['observed_native_footprint'])
        self.assertEqual(r['native_comparison']['RN7101']['status'], 'CANDIDATE_NEW_NOT_IN_CANONICAL')
        self.assertEqual(r['native_comparison']['R7121']['status'], 'REMOVED_IN_CANDIDATE')

    def test_transport_graph_complete_and_separate(self):
        r = m.analyze(*self.args)
        t = r['transport_contract']
        for key in ('headers', 'DIN_pinmap', 'terminal_wires', 'upstream_power_boundaries', 'wires', 'edges', 'nodes'):
            self.assertEqual(t[key], self.args[2][key])
        self.assertEqual(len(r['packages']), 86)
        self.assertFalse(t['native_ready'])
        self.assertIn({'ref': 'TRANSPORT_ASSEMBLY', 'reason': 'CONNECTOR_HARNESS_NATIVE_MATERIALIZATION_UNBOUND'}, r['gaps'])


if __name__ == '__main__': unittest.main()
