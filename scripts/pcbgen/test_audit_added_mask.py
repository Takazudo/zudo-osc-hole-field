import unittest
from scripts.pcbgen.audit_added_mask import added_copper_scope


def item(i, kind='segment', width=1):
    return f'({kind} (width {width}) (uuid "00000000-0000-4000-8000-{i:012d}"))'


def board(*items):
    return '(kicad_pcb (version 20260101) ' + ' '.join(items) + ')'


class AddedCopperScopeTests(unittest.TestCase):
    def test_core_and_jr_exact_scopes(self):
        for count, vias in ((382, 38), (79, 5)):
            added=[item(i, 'via' if i<=vias else 'segment') for i in range(1,count+1)]
            scope=added_copper_scope(board(item(0),item(0)),board(item(0),item(0),*added),count,vias)
            self.assertEqual(len(scope),count)
            self.assertEqual(list(scope.values()).count('via'),vias)
            with self.assertRaisesRegex(ValueError,'count'):
                added_copper_scope(board(item(0)),board(item(0),*added),count+1,vias)
            with self.assertRaisesRegex(ValueError,'count'):
                added_copper_scope(board(item(0)),board(item(0),*added),count,vias+1)

    def test_old_copper_cannot_change_or_disappear(self):
        for after in (board(item(1)),board(item(0,width=2),item(1))):
            with self.assertRaisesRegex(ValueError,'additive'):
                added_copper_scope(board(item(0)),after)

    def test_new_uuid_must_be_unique_and_not_reused(self):
        for additions in ((item(0),),(item(0,width=2),),(item(1),item(1))):
            with self.assertRaisesRegex(ValueError,'UUID'):
                added_copper_scope(board(item(0)),board(item(0),*additions))

    def test_empty_or_invalid_counts_rejected(self):
        with self.assertRaises(ValueError):added_copper_scope(board(),board())
        for count,vias in ((True,0),(1,True),(0,0),(1,-1),(1,2)):
            with self.assertRaises(ValueError):added_copper_scope(board(),board(item(1)),count,vias)
