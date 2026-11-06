"""Resume of the OSC3 K signal chain (circuit/reviews/osc3-k-signals/chain.py) from its progress file."""
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import scripts.pcbgen.route_jack_grid as driver

CHAIN=Path(__file__).resolve().parents[2]/'circuit/reviews/osc3-k-signals/chain.py'
spec=importlib.util.spec_from_file_location('osc3_k_chain',CHAIN);chain=importlib.util.module_from_spec(spec);spec.loader.exec_module(chain)
CLEAN={'violations':[],'schematic_parity':[]}


class ChainResumeTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,self.root)
        self.here=self.root/'reviews';self.here.mkdir()
        self.board=self.root/'boards/osc-core/osc-core.kicad_pcb';self.board.parent.mkdir(parents=True);self.board.write_text('adopted')
        (self.root/'design/boards').mkdir(parents=True);(self.root/'design/boards/osc-core.json').write_text('{}')
        for name,value in (('ROOT',self.root),('HERE',self.here)):
            patch=unittest.mock.patch.object(chain,name,value);patch.start();self.addCleanup(patch.stop)
        self.start=self.put('osc3-t-start','adopted',10)
        self.gates=[]
        def gate(board_id,current,candidate,receipt,spec,resume=False,**kw):
            self.gates.append((current,candidate,resume));return {**receipt,'adopted':self.adopt,'split_pad_groups':[],'rejection_reason':None if self.adopt else 'fixture'}
        self.adopt=False
        for name,value in (('complete_gate',gate),('run',lambda *a:'10.0.6\n')):
            patch=unittest.mock.patch.object(driver,name,value);patch.start();self.addCleanup(patch.stop)

    def put(self,name,text,open_edges):
        path=chain.cache(name)/'osc-core.kicad_pcb';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        path.with_name('dump.json').write_text(json.dumps({'open_edges':open_edges,'pads':[],'islands':{}}))
        path.with_name('drc.json').write_text(json.dumps(CLEAN))
        return path

    def progress(self,current,steps,**extra):
        (self.here/'t-progress.json').write_text(json.dumps({'steps':steps,'current':str(current.relative_to(self.root)),**extra}))

    def kept(self,name,candidate):return {'step':name,'raw_gate_adopted':True,'candidate_sha256':chain.sha(candidate)}

    def stitched_progress(self):
        self.put('rrr-02-verify','unstitched',9)
        stitched=self.put('rrr-02-stitch-verify','stitched',7)
        self.progress(stitched,[{'step':'rrr-01','result':'nothing to do'},self.kept('rrr-02',stitched)])
        return stitched

    def main(self,*args):
        with unittest.mock.patch.object(sys,'argv',['chain.py','t',*args]):chain.main()
        return json.loads((self.here/'t.json').read_text())

    def test_gate_only_continuation_gates_the_stitched_kept_candidate(self):
        stitched=self.stitched_progress()
        with unittest.mock.patch.object(driver,'run_stage',side_effect=AssertionError('no stage may run')):
            out=self.main('rrr-01','rrr-02','--resume-from','rrr-02','--promote')
        self.assertEqual(self.gates,[(self.start,stitched,True)])
        self.assertEqual(out['steps'][-1]['candidate'],str(stitched.relative_to(self.root)))
        self.assertEqual((out['adopted'],out['promoted'],out['open_edges_after']),(False,False,7))
        self.assertEqual(self.board.read_text(),'adopted')

    def test_adopted_final_gate_without_promote_leaves_the_board(self):
        stitched=self.stitched_progress();self.adopt=True
        with unittest.mock.patch.object(chain,'delta',return_value={'base_sha256':chain.sha(self.board)}):
            out=self.main('rrr-01','rrr-02','--resume-from','rrr-02')
        self.assertTrue(out['adopted']);self.assertFalse(out['promoted']);self.assertEqual(self.board.read_text(),'adopted')
        self.assertEqual(out['final_gate']['candidate_board_sha256'],chain.sha(stitched))

    def test_unstitched_predecessor_is_never_substituted(self):
        stitched=self.stitched_progress()
        self.progress(chain.cache('rrr-02-verify')/'osc-core.kicad_pcb',[{'step':'rrr-01','result':'nothing to do'},self.kept('rrr-02',stitched)])
        with self.assertRaisesRegex(RuntimeError,'stale'):self.main('rrr-01','rrr-02','--resume-from','rrr-02')
        self.assertEqual(self.gates,[])

    def test_progress_must_point_at_the_last_kept_stage_workspace(self):
        stitched=self.stitched_progress();other=self.put('rrr-01-verify','stitched',7)
        self.progress(other,[{'step':'rrr-01','result':'nothing to do'},self.kept('rrr-02',stitched)])
        with self.assertRaisesRegex(RuntimeError,'not the kept candidate of rrr-02'):self.main('rrr-01','rrr-02','--resume-from','rrr-02')

    def test_stale_start_copy_fails_closed(self):
        self.stitched_progress();self.start.write_text('older')
        with self.assertRaisesRegex(RuntimeError,'start copy is not the adopted board'):self.main('rrr-01','rrr-02','--resume-from','rrr-02')

    def test_stale_or_missing_candidate_fails_closed(self):
        stitched=self.stitched_progress();stitched.write_text('edited')
        with self.assertRaisesRegex(RuntimeError,'stale'):self.main('rrr-01','rrr-02','--resume-from','rrr-02')
        stitched.unlink()
        with self.assertRaisesRegex(RuntimeError,'cannot resume t: FileNotFoundError'):self.main('rrr-01','rrr-02','--resume-from','rrr-02')
        self.stitched_progress()
        (self.here/'t-progress.json').write_text(json.dumps({'steps':[],'current':'x','current_sha256':'0'*64}))
        with self.assertRaisesRegex(RuntimeError,'not the stages through rrr-02'):self.main('rrr-01','rrr-02','--resume-from','rrr-02')
        stitched=self.stitched_progress()
        self.progress(stitched,[{'step':'rrr-01','result':'nothing to do'},self.kept('rrr-02',stitched)],current_sha256='0'*64)
        with self.assertRaisesRegex(RuntimeError,'stale'):self.main('rrr-01','rrr-02','--resume-from','rrr-02')
        (self.here/'t-progress.json').unlink()
        with self.assertRaisesRegex(RuntimeError,'cannot resume t: FileNotFoundError'):self.main('rrr-01','rrr-02','--resume-from','rrr-02')
        self.assertEqual(self.gates,[])

    def test_missing_dump_or_drc_evidence_fails_closed(self):
        for missing in ('stitched','start'):
            for name in ('dump.json','drc.json'):
                stitched=self.stitched_progress();self.put('osc3-t-start','adopted',10)
                {'stitched':stitched,'start':self.start}[missing].with_name(name).unlink()
                with self.assertRaisesRegex(RuntimeError,'cannot resume t: FileNotFoundError'):self.main('rrr-01','rrr-02','--resume-from','rrr-02')
        self.assertEqual(self.gates,[])

    def test_candidate_failing_the_raw_gate_against_the_start_fails_closed(self):
        stitched=self.put('rrr-02-stitch-verify','stitched',10)
        self.progress(stitched,[{'step':'rrr-01','result':'nothing to do'},self.kept('rrr-02',stitched)])
        with self.assertRaisesRegex(RuntimeError,'fails the raw gate'):self.main('rrr-01','rrr-02','--resume-from','rrr-02')
        self.assertEqual(self.gates,[])

    def test_later_stages_run_from_the_bound_candidate_and_a_second_resume_still_binds(self):
        stitched=self.stitched_progress();seen=[]
        def run_stage(board_id,current,spec,definition,log):seen.append(current);return None,None
        with unittest.mock.patch.object(driver,'run_stage',run_stage):
            self.main('rrr-01','rrr-02','rrr-03','--resume-from','rrr-02')
        self.assertEqual(seen,[stitched])
        progress=json.loads((self.here/'t-progress.json').read_text())
        self.assertEqual([s['step'] for s in progress['steps']],['rrr-01','rrr-02','resumed:rrr-01,rrr-02','rrr-03'])
        self.assertEqual(progress['current_sha256'],chain.sha(stitched))
        out=self.main('rrr-01','rrr-02','rrr-03','--resume-from','rrr-03')
        self.assertEqual(self.gates[-1],(self.start,stitched,True));self.assertFalse(out['adopted'])

    def test_resume_with_no_kept_stage_reports_no_gain_without_a_gate(self):
        self.progress(self.start,[{'step':'rrr-01','result':'nothing to do'}])
        out=self.main('rrr-01','--resume-from','rrr-01')
        self.assertEqual(out['rejection_reason'],'no step passed its raw gate');self.assertEqual(self.gates,[])


if __name__=='__main__':unittest.main()
