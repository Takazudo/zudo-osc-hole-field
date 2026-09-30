"""Adversarial electrical-boundary and physical-package allocation checks."""
from collections import defaultdict
from dataclasses import replace
import unittest
from design.spec.instrument import specification
from design.spec.modules.io_partition import refine, channel_signatures
from design.spec.modules.envelope import family as envelope
from scripts.checks.io_partition60 import build, source_data, assignment_errors, crossing_kind


class BoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families,cls.instances=specification()
        cls.packages,cls.nets,cls.sensitive,cls.units=source_data(cls.families,cls.instances)
        cls.assignments=[{'ref':ref,'region':p['regions'][0]} for ref,p in cls.packages.items()]

    def test_no_raw_or_sensitive_crossings_and_exact_panel_roster(self):
        report=build(self.families,self.instances)
        self.assertEqual(report['errors'],[])
        self.assertEqual(report['forbidden_crossings'],[])
        self.assertEqual(report['module_count'],33)
        self.assertEqual(report['fixed_uid_count'],438)
        self.assertEqual(len([r for r in report['local_raw_sensitive_nets'] if r['net'].endswith('_TIP')]),180)
        jack=next(r for r in report['area_lower_bounds'] if r['region']=='jack')
        self.assertLess(jack['courtyard_sum_mm2'],jack['gross_face_area_mm2'])
        self.assertIsNone(jack['usable_area_mm2'])
        self.assertFalse(report['complete_cut_accepted'])

    def test_missing_duplicate_and_unknown_assignments_rejected(self):
        self.assertEqual(assignment_errors(self.packages,self.assignments),[])
        for rows in (self.assignments[:-1],self.assignments+[self.assignments[0]],self.assignments+[{'ref':'FICTION','region':'jack'}]):
            self.assertTrue(assignment_errors(self.packages,rows))

    def test_reference_isolator_requires_real_upstream_driver(self):
        name='/O1/LOCAL_REF5';members=self.nets[name]
        self.assertEqual(crossing_kind(name,members,self.sensitive,self.nets)[0],'compensated oscillator reference')
        stripped={n:[m for m in rows if m['role']!='oscillator:LOCAL_REF5'] for n,rows in self.nets.items()}
        self.assertIsNone(crossing_kind(name,members,self.sensitive,stripped)[0])

    def test_raw_tip_cannot_be_relabelled_as_buffered(self):
        name='/O1/1V_TIP';rows=self.nets[name]
        self.assertIsNone(crossing_kind(name,rows,self.sensitive)[0])
        switch=next(m['ref'] for m in rows if m['ref'].startswith('U'))
        moved=[{**r,'region':'core'} if r['ref']==switch else r for r in self.assignments]
        report=build(self.families,self.instances,moved)
        self.assertIn(name,{x['net'] for x in report['forbidden_crossings']})
        self.assertTrue(report['errors'])

    def test_sensitive_island_split_is_rejected(self):
        storage='/H1/SLEW_STORAGE';member=next(m['ref'] for m in self.nets[storage] if m['ref'].startswith('C'))
        moved=[{**r,'region':'jack'} if r['ref']==member else r for r in self.assignments]
        report=build(self.families,self.instances,moved)
        self.assertIn(storage,{x['net'] for x in report['forbidden_crossings']})
        self.assertTrue(any('split island' in x for x in report['errors']))

    def test_repacking_preserves_every_active_channel(self):
        raw=envelope.__wrapped__();packed=refine(raw)
        self.assertEqual(channel_signatures(raw),channel_signatures(packed))
        live=next(p for p in packed.parts if p.attributes.get('Role')=='stage_indicator:A')
        # Swap plus and minus pins within an actual physical unit. Functional
        # channel equivalence must catch this even when package count is intact.
        from design.spec.modules.io_partition import AMP_MAPS
        out,minus,plus=AMP_MAPS[live.unit-1]
        bad=replace(live,pins={**live.pins,plus:live.pins[minus],minus:live.pins[plus]})
        altered=replace(packed,parts=tuple(bad if p is live else p for p in packed.parts))
        self.assertNotEqual(channel_signatures(raw),channel_signatures(altered))

    def test_impossibly_small_candidate_fails_area_gate(self):
        report=build(self.families,self.instances,capacities={'jack':{'width_mm':10,'height_mm':10,'faces':2}})
        self.assertFalse(report['source_cut_accepted'])
        self.assertTrue(any('area lower bound' in e for e in report['errors']))

    def test_missing_and_duplicate_physical_unit_rejected(self):
        f=next(f for f in self.families if f.name=='envelope')
        unit=next(p for p in f.parts if p.prefix=='U' and p.unit==5)
        for parts in (tuple(p for p in f.parts if p is not unit),f.parts+(unit,)):
            altered=replace(f,parts=parts)
            report=build(tuple(altered if q is f else q for q in self.families),self.instances)
            self.assertTrue(any('package unit coverage' in e for e in report['errors']))

    def test_swapped_units_between_regions_are_rejected(self):
        f=next(f for f in self.families if f.name=='envelope')
        stage=next(p for p in f.parts if p.attributes.get('Role')=='stage_indicator:A')
        mag=next(p for p in f.parts if p.attributes.get('Role')=='magnitude_indicator:A' and p.unit==stage.unit)
        moved=replace(stage,ordinal=mag.ordinal,key=mag.key)
        counterpart=replace(mag,ordinal=stage.ordinal,key=stage.key)
        altered=replace(f,parts=tuple(moved if p is stage else counterpart if p is mag else p for p in f.parts))
        report=build(tuple(altered if q is f else q for q in self.families),self.instances)
        self.assertTrue(any('split/swapped package' in e for e in report['errors']))

    def test_historical_capture_survives_live_warning_repacking(self):
        from scripts.checks.prepartition54 import check_report
        check_report()

    def test_env_package_units_never_mix_stage_and_magnitude(self):
        groups=defaultdict(list)
        for u in self.units:
            if u['ref'].startswith('U41'):groups[u['ref']].append(u)
        stage=[rows for rows in groups.values() if any(r['role']=='stage_indicator:A' for r in rows)]
        self.assertEqual(len(stage),1)
        self.assertEqual(sum(r['role']=='stage_indicator:A' for r in stage[0]),2)
        self.assertTrue(all(r['region']=='stage_optical' for r in stage[0]))
        self.assertFalse(any(r['role']=='magnitude_indicator:A' for r in stage[0]))

    def test_stage_optical_package_retains_its_bypasses(self):
        stage = [p for p in self.packages.values() if p['instance']=='E1' and p['regions']==['stage_optical']]
        self.assertEqual(len(stage), 23)
        amp = next(p for p in stage if p['symbol']=='OPA4196IDR')
        bypasses = [p for p in stage if p['decouples_ref']==amp['ref']]
        self.assertEqual(len(bypasses), 2)
        self.assertEqual({p['mpn'] for p in bypasses}, {'GRM188R71H104KA93D'})

if __name__=='__main__':unittest.main()
