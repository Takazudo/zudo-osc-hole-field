"""Current publication preserves source changes and unknown-load boundaries."""
import copy
import json
import unittest

from scripts.schgen.build_schematic_status import REPORT, OSCILLATOR_REPORT, sections, oscillator_current
from scripts.schgen.build_supply_documentation import render


class SchematicStatus(unittest.TestCase):
    def setUp(self):
        self.report = json.loads(REPORT.read_text())

    def test_oscillator_population_and_totals_follow_current_source(self):
        report = json.loads(OSCILLATOR_REPORT.read_text())
        body = oscillator_current(report)
        self.assertIn('4 `OPA4197IPWR`', body)
        self.assertIn('339.500 / 335.000 / 30.000', body)
        self.assertIn('NOT ESTABLISHED / NOT ESTABLISHED / NOT ESTABLISHED', body)
        report['sheets'][0]['fitted_IC_packages_per_instance']['OPA4197IPWR'] += 1
        report['planning_upper_total_mA']['+12V'] += 6
        body = oscillator_current(report)
        self.assertIn('5 `OPA4197IPWR`', body)
        self.assertIn('345.500 / 335.000 / 30.000', body)

    def test_oscillator_population_cannot_omit_or_duplicate_a_sheet(self):
        report = json.loads(OSCILLATOR_REPORT.read_text())
        for rows in (report['sheets'][:1], [report['sheets'][0]] * 2):
            with self.subTest(count=len(rows)), self.assertRaises(ValueError):
                oscillator_current({**report, 'sheets': rows})
        report['sheets'][0]['fitted_IC_packages_per_instance']['OPA4197IPWR'] = -1
        with self.assertRaisesRegex(ValueError, 'population'):
            oscillator_current(report)

    def test_current_mixer_totals_and_partial_scope(self):
        body = sections(self.report)['schematic-family-current']
        self.assertIn('`mix5` | M5A, M5B | 79.200 / 73.200 / 1.000', body)
        self.assertIn('`mix4_vca` | M4A, M4B | 93.200 / 87.200 / 1.000', body)
        sh = next(line for line in body.splitlines() if '`sample_hold`' in line)
        self.assertIn('109.700 / 105.300 / 0.000', sh)
        self.assertIn('Partial known subtotal', sh)
        self.assertIn('NOT ESTABLISHED / NOT ESTABLISHED / NOT ESTABLISHED', sh)
        # Each instance is represented exactly once, including the shared reference.
        instance_cells = [line.split('|')[2].strip() for line in body.splitlines() if line.startswith('| `')]
        published = [name for cell in instance_cells for name in cell.split(', ')]
        self.assertCountEqual(published, [row['instance'] for row in self.report['instances']])

    def test_changed_source_value_changes_display_without_promoting_maximum(self):
        row = next(row for row in self.report['instances'] if row['instance'] == 'M5A')
        row['planning_upper_subtotal_mA']['+12V'] += 1.25
        body = sections(self.report)['schematic-family-current']
        line = next(line for line in body.splitlines() if '`mix5`' in line)
        self.assertIn('80.450 / 73.200 / 1.000', line)
        self.assertIn('NOT ESTABLISHED', line)

    def test_known_maximum_is_separate_and_one_unknown_keeps_family_unknown(self):
        for row in self.report['instances']:
            if row['family'] == 'mix5':
                row['guaranteed_maximum_mA']['+12V'] = 50
        body = sections(self.report)['schematic-family-current']
        line = next(line for line in body.splitlines() if '`mix5`' in line)
        self.assertIn('| 100.000 / NOT ESTABLISHED / NOT ESTABLISHED |', line)
        next(row for row in self.report['instances'] if row['instance'] == 'M5A')['guaranteed_maximum_mA']['+12V'] = None
        line = next(line for line in sections(self.report)['schematic-family-current'].splitlines() if '`mix5`' in line)
        self.assertIn('| NOT ESTABLISHED / NOT ESTABLISHED / NOT ESTABLISHED |', line)

    def test_missing_duplicate_rail_and_nonfinite_fail(self):
        mutations = []
        missing = copy.deepcopy(self.report); missing['instances'].pop(); mutations.append(missing)
        duplicate = copy.deepcopy(self.report); duplicate['instances'][1] = duplicate['instances'][0]; mutations.append(duplicate)
        rail = copy.deepcopy(self.report); del rail['instances'][0]['planning_upper_subtotal_mA']['+5V']; mutations.append(rail)
        nonfinite = copy.deepcopy(self.report); nonfinite['instances'][0]['planning_upper_subtotal_mA']['+12V'] = float('nan'); mutations.append(nonfinite)
        maximum = copy.deepcopy(self.report); maximum['instances'][0]['guaranteed_maximum_mA']['+12V'] = float('inf'); mutations.append(maximum)
        for report in mutations:
            with self.subTest(report=report['instances'][0]['instance']), self.assertRaises((ValueError, KeyError)):
                sections(report)

    def test_only_marked_sections_change_and_missing_markers_fail(self):
        text = 'Authored model limits\n{/* schematic-rail-current:start */}\nstale\n{/* schematic-rail-current:end */}\nPhysical gates remain open'
        new = render(text, 'schematic-rail-current', sections(self.report)['schematic-rail-current'], True)
        self.assertTrue(new.startswith('Authored model limits\n'))
        self.assertTrue(new.endswith('\nPhysical gates remain open'))
        with self.assertRaises(ValueError):
            render('no markers', 'schematic-rail-current', '', True)


if __name__ == '__main__':
    unittest.main()
