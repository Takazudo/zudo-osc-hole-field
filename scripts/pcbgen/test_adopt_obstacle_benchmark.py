"""Fail closed before native work when a candidate or its canonical input changed."""
import copy,tempfile,unittest
from pathlib import Path
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
