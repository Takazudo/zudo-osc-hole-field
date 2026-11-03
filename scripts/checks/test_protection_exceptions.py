"""A protection-locality exception is bound to the exact diode, nets, anchor and pose."""
import copy
import json
from pathlib import Path
import unittest
from scripts.checks.partition35_floorplan import protection_exception_errors
ROOT=Path(__file__).resolve().parents[2]


class ProtectionExceptionBindingTests(unittest.TestCase):
    def setUp(self):
        self.exceptions=[{'board':'K','ref':'D4233','adoption_state':'PROVISIONAL','binding':{
            'mpn':'BAT54S,215','nets':['/E2/FALL_CURVE','/E2/SLOPE_SELECT_SEL4'],'anchor_refs':['U4206'],'anchor_mpns':['TMUX6112PWR'],
            'anchor_mm':[242.48,261.57],'placed_mm':[242.81,289.18],'side':'F.Cu','distance_mm':27.61,'radius_mm':24.0,
            'position_tolerance_mm':0.05,'distance_tolerance_mm':0.01}}]
        self.far={'K':{'D4233':{'mpn':'BAT54S,215','nets':['/E2/FALL_CURVE','/E2/SLOPE_SELECT_SEL4'],'anchor_refs':['U4206']}}}
        self.placed={'D4233':{'ref':'D4233','board':'K','x_mm':242.81,'y_mm':289.18,'side':'F.Cu'},
                     'U4206':{'ref':'U4206','board':'K','x_mm':242.48,'y_mm':261.57,'side':'F.Cu'}}
        self.parts={'D4233':{'mpn':'BAT54S,215'},'U4206':{'mpn':'TMUX6112PWR'}}

    def errors(self,exceptions=None,far=None,placed=None,parts=None):
        return protection_exception_errors(self.exceptions if exceptions is None else exceptions,self.far if far is None else far,
                                           self.placed if placed is None else placed,self.parts if parts is None else parts)

    def test_current_binding_passes(self):
        self.assertEqual(self.errors(),[])

    def test_each_bound_property_change_fails(self):
        def moved(ref,dx=0.0,dy=0.0,**fields):
            placed=copy.deepcopy(self.placed);placed[ref]['x_mm']+=dx;placed[ref]['y_mm']+=dy;placed[ref].update(fields);return placed
        far_other_net=copy.deepcopy(self.far);far_other_net['K']['D4233']['nets']=['/E2/RISE_CURVE','/E2/SLOPE_SELECT_SEL2']
        far_other_anchor=copy.deepcopy(self.far);far_other_anchor['K']['D4233']['anchor_refs']=['U4207']
        placed_other_anchor=copy.deepcopy(self.placed);placed_other_anchor['U4207']={**self.placed['U4206'],'ref':'U4207'}
        cases={
            'diode moved beyond tolerance':dict(placed=moved('D4233',dy=0.2)),
            'diode moved further from the anchor':dict(placed=moved('D4233',dy=3.0)),
            'anchor moved':dict(placed=moved('U4206',dx=0.1)),
            'diode on the other face':dict(placed=moved('D4233',side='B.Cu')),
            'diode on another board':dict(placed=moved('D4233',board='JL')),
            'mpn changed':dict(parts={**self.parts,'D4233':{'mpn':'BAV199,215'}}),
            'anchor mpn changed':dict(parts={**self.parts,'U4206':{'mpn':'ADG5412FBRUZ'}}),
            'nets changed':dict(far=far_other_net),
            'anchor changed':dict(far=far_other_anchor,placed=placed_other_anchor),
        }
        for name,kwargs in cases.items():
            with self.subTest(name):self.assertTrue(self.errors(**kwargs))

    def test_stale_missing_and_duplicate_records_fail(self):
        self.assertTrue(any('stale' in e for e in self.errors(far={'K':{}})))
        self.assertTrue(any('without a recorded exception' in e for e in self.errors(exceptions=[])))
        self.assertTrue(any('duplicate' in e for e in self.errors(exceptions=self.exceptions*2)))

    def test_unbound_or_loose_records_fail(self):
        for name,mutate in {
            'no binding':lambda e:e.pop('binding'),
            'board/ref only':lambda e:e.update(binding={}),
            'loose tolerance':lambda e:e['binding'].update(position_tolerance_mm=5),
            'no distance tolerance':lambda e:e['binding'].pop('distance_tolerance_mm'),
            'other radius':lambda e:e['binding'].update(radius_mm=30.0),
            'unknown state':lambda e:e.update(adoption_state='ACCEPTED'),
            'approved without approval':lambda e:e.update(adoption_state='APPROVED'),
        }.items():
            exceptions=copy.deepcopy(self.exceptions);mutate(exceptions[0])
            with self.subTest(name):self.assertTrue(self.errors(exceptions=exceptions))
        approved=copy.deepcopy(self.exceptions);approved[0].update(adoption_state='APPROVED',approval={'decision':'E99','by':'owner'})
        self.assertEqual(self.errors(exceptions=approved),[])

    def test_committed_record_is_provisional_and_bound(self):
        record=json.loads((ROOT/'design/partition/protection-locality-exceptions.json').read_text())['exceptions']
        self.assertEqual([(e['board'],e['ref'],e['adoption_state']) for e in record],[('K','D4233','PROVISIONAL')])
        self.assertEqual(record[0]['binding'],self.exceptions[0]['binding'])


if __name__=='__main__':unittest.main()
