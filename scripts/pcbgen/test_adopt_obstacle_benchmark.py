"""Fail closed before native work when a candidate or its canonical input changed."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen.adopt_obstacle_benchmark import sha,validate_inputs


class AdoptionInputTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.folder=self.root/'artifact';name='osc-jack-left.kicad_pcb'
        self.board=self.root/'boards/osc-jack-left'/name
        self.saved=self.folder/'input'/name;self.candidate=self.folder/'new/native'/name
        for file,text in ((self.board,'canonical'),(self.saved,'settled'),(self.candidate,'candidate')):
            file.parent.mkdir(parents=True,exist_ok=True);file.write_text(text)
        self.report={'status':'COMPLETE','board':'osc-jack-left',
            'input_hashes':{str(self.board.relative_to(self.root)):sha(self.board)},
            'saved_input_sha256':sha(self.saved),
            'variants':{'new':{'eligible_for_promotion':True,'candidate_sha256':sha(self.candidate)}}}

    def test_current_inputs_resolve_to_exact_candidate(self):
        self.assertEqual(validate_inputs(self.report,self.folder,self.root),('osc-jack-left',self.board,self.candidate))

    def test_changed_canonical_copper_is_never_overwritten(self):
        self.board.write_text('another session adopted copper')
        with self.assertRaisesRegex(ValueError,'stale input'):validate_inputs(self.report,self.folder,self.root)

    def test_changed_saved_or_candidate_board_is_rejected(self):
        for path in (self.saved,self.candidate):
            old=path.read_text();path.write_text('changed')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):validate_inputs(self.report,self.folder,self.root)
            path.write_text(old)

    def test_incomplete_or_rejected_benchmark_cannot_be_promoted(self):
        for field in ('status','eligible'):
            report=copy.deepcopy(self.report)
            if field=='status':report['status']='RUNNING'
            else:report['variants']['new']['eligible_for_promotion']=False
            with self.assertRaises(ValueError):validate_inputs(report,self.folder,self.root)


class CachePublicationTests(unittest.TestCase):
    def test_compaction_requires_native_equivalence(self):
        from scripts.pcbgen import adopt_obstacle_benchmark as adopt
        for change in ('none','connectivity','warning','geometry'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);checked=root/'osc-core.kicad_pcb'
                checked.write_text('(kicad_pcb (zone (net "A") (filled_polygon (pts '+('(xy 1 1)'*100)+'))))')
                dump={'open_edges':1,'islands':{'A':[['p'],['q']]},'pads':[{'uuid':'p','xy':[0,0]}],'tracks':[],'vias':[]}
                after=copy.deepcopy(dump);drc={'violations':[],'schematic_parity':[]};after_drc=copy.deepcopy(drc)
                if change=='connectivity':after['islands']={'A':[['p','q'],['r']]}
                if change=='warning':after_drc['violations']=[{'type':'clearance','severity':'warning','items':[]}]
                if change=='geometry':after['pads'][0]['xy']=[1,0]
                def workspace(*args):
                    folder=root/'compact';folder.mkdir();return folder
                with patch.object(adopt.driver,'workspace',side_effect=workspace),patch.object(adopt,'checked_copy',return_value=(checked,after_drc,after)) as native:
                    if change=='none':
                        published,receipt=adopt.publication_copy('osc-core',checked,drc,dump,limit=100)
                        self.assertLess(published.stat().st_size,100)
                        self.assertEqual(receipt['derived_zone_cache_fields_removed'],1)
                    else:
                        with self.assertRaises(adopt.driver.StageRejected):adopt.publication_copy('osc-core',checked,drc,dump,limit=100)
                    native.assert_called_once()
