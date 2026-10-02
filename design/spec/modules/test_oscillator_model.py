"""Keep excluded reference fanout out of the bounded sine fixture."""
from dataclasses import replace
import unittest
from unittest.mock import patch
from design.spec.modules.oscillator import family
from design.spec.modules.oscillator_sine_projection import sine_parts, SINE_ROLES
from design.spec.modules import run_oscillator_spice as runner


def disconnected_nodes(deck):
    """Connectivity diagnostic for this fixture's R/V/E/Q syntax, not a rank proof."""
    graph = {}
    widths = {'R': 2, 'V': 2, 'E': 4, 'Q': 3}
    for line in deck.splitlines()[1:]:
        fields = line.split()
        if not fields or fields[0].startswith(('.', '*')):
            continue
        kind = fields[0][0]
        if kind not in widths:
            raise AssertionError(f'unsupported fixture element: {line}')
        nodes = fields[1:1 + widths[kind]]
        for node in nodes:
            graph.setdefault(node, set()).update(nodes)
    reached = set(); pending = ['0']
    while pending:
        node = pending.pop()
        if node not in reached:
            reached.add(node); pending.extend(graph.get(node, set()) - reached)
    return set(graph) - reached


class OscillatorModelSourceTests(unittest.TestCase):
    def setUp(self):
        self.family = family()

    def test_complete_declared_membership_and_no_disconnected_fragments(self):
        selected = sine_parts(self.family.parts)
        self.assertCountEqual([p.attributes['Role'] for p in selected], SINE_ROLES)
        self.assertEqual(len(selected), 14)
        body = runner.decks()['oscillator-sine-generic.cir']
        self.assertFalse(disconnected_nodes(body))
        self.assertNotIn('SINE_REF', body)
        # The historical prefix selection admitted these isolated chains. This
        # demonstrates the graph defect without asserting a native solve failed.
        old = body.replace('.tran ', 'Rold1 SINE_REF5_DRIVE SINE_REF5 100\n'
                           'Rold2 SINE_REF5 SINE_REF5_FB 100\n'
                           'Rold3 SINE_REFN5_DRIVE SINE_REFN5 100\n'
                           'Rold4 SINE_REFN5 SINE_REFN5_FB 100\n.tran ')
        self.assertEqual(disconnected_nodes(old), {'SINE_REF5_DRIVE', 'SINE_REF5', 'SINE_REF5_FB',
                                                   'SINE_REFN5_DRIVE', 'SINE_REFN5', 'SINE_REFN5_FB'})

    def test_excluded_fanout_changes_do_not_enter_ideal_boundary(self):
        before = runner.decks()['oscillator-sine-generic.cir']
        parts = tuple(replace(p, value='250 Ω') if p.attributes.get('Role', '').startswith('oscillator:R_SINE_REF')
                      else p for p in self.family.parts)
        with patch.object(runner, 'family', return_value=replace(self.family, parts=parts)):
            self.assertEqual(runner.decks()['oscillator-sine-generic.cir'], before)

    def test_modeled_resistor_still_comes_from_source(self):
        parts = tuple(replace(p, value='69 kΩ') if p.attributes.get('Role') == 'oscillator:R_SINE_ATTEN'
                      else p for p in self.family.parts)
        with patch.object(runner, 'family', return_value=replace(self.family, parts=parts)):
            self.assertIn('TRI_SCALED SINE_BASE 69000', runner.decks()['oscillator-sine-generic.cir'])

    def test_missing_duplicate_dnp_and_unsupported_members_fail(self):
        p = next(p for p in self.family.parts if p.attributes.get('Role') == 'oscillator:R_SINE_ATTEN')
        variants = [tuple(q for q in self.family.parts if q is not p),
                    self.family.parts + (replace(p, key='duplicate'),)]
        for changes in ({'dnp': True}, {'prefix': 'C'}, {'unit': 1},
                        {'symbol': 'zudo-osc-hole-field:C0603C101J5GACTU'}):
            variants.append(tuple(replace(q, **changes) if q is p else q for q in self.family.parts))
        for parts in variants:
            with self.subTest(count=len(parts)), self.assertRaises(ValueError):
                sine_parts(parts)

    def test_missing_amp_fails_before_oracle_or_deck_write(self):
        parts = tuple(p for p in self.family.parts if p.attributes.get('Role') != 'oscillator:SINE_GAIN')
        with patch.object(runner, 'family', return_value=replace(self.family, parts=parts)), \
                patch.object(runner.subprocess, 'run') as run, patch.object(runner.Path, 'write_text') as write:
            with self.assertRaisesRegex(ValueError, 'one fitted'):
                runner.main()
            run.assert_not_called(); write.assert_not_called()


if __name__ == '__main__':
    unittest.main()
