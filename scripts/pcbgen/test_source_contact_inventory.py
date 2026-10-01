"""A contact missing from all native lists still exists in the source ledger."""
import unittest
from scripts.pcbgen.source_contact_inventory import expected_contacts, reconcile_native


class SourceInventoryTests(unittest.TestCase):
    def test_source_assignment_is_independent_of_native_presence(self):
        partition = {'boards': [{'id': 'left', 'board_key': 'JL'}],
            'assignment': {'components': [
                {'ref': 'U1', 'board': 'JL', 'fitted': True},
                {'ref': 'U2', 'board': 'JL', 'fitted': True},
                {'ref': 'U3', 'board': 'JR', 'fitted': True}]}}
        io = {'physical_packages': [{'ref': r, 'dnp': False} for r in ('U1', 'U2', 'U3')],
              'allowed_crossings': [{'net': '+5V', 'members': [
                  {'ref': r, 'pin': '1'} for r in ('U1', 'U2', 'U3')]}]}
        expected = expected_contacts('left', partition, io, ('+5V',))
        self.assertEqual(set(expected), {('U1', '1', '+5V'), ('U2', '1', '+5V')})
        native = {'items': [{'ref': 'U1', 'pad': '1', 'net': '+5V', 'uuid': 'one'}]}
        with self.assertRaisesRegex(ValueError, 'missing=.*U2'):
            reconcile_native(native, expected, {'U1', 'U2', 'U3'}, ('+5V',))
        native['items'].append({'ref': 'U2', 'pad': '1', 'net': '+5V', 'uuid': 'two'})
        self.assertEqual(set(reconcile_native(native, expected, {'U1', 'U2', 'U3'}, ('+5V',))), set(expected))


if __name__ == '__main__': unittest.main()
