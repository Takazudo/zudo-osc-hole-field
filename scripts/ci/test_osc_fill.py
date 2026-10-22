"""Pure fixtures only; no pcbnew import or native subprocess execution."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import osc_frozen_fill as f


class FillTests(unittest.TestCase):
    def semantic(self,text):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a';p.write_text(text);return f.semantic_hash(p)

    def test_only_direct_zone_fill_is_ignored(self):
        a='(kicad_pcb (zone (net "AGND") (polygon (pts (xy 1 2)))))'
        b='(kicad_pcb (zone (net "AGND") (polygon (pts (xy 1 2))) (filled_polygon (layer "F.Cu") (pts (xy 4 5)))))'
        self.assertEqual(self.semantic(a),self.semantic(b))
        self.assertNotEqual(self.semantic(a),self.semantic(a.replace('AGND','+12V')))
        self.assertNotEqual(self.semantic(a),self.semantic(a[:-1]+' (filled_polygon (x 1)))'))

    def test_zone_settings_and_geometry_not_ignored(self):
        a='(kicad_pcb (zone (connect_pads yes) (fill yes)))'
        for b in [a.replace('yes','no'), a.replace('(fill yes)','(fill yes (thermal_gap 9))')]:
            self.assertNotEqual(self.semantic(a),self.semantic(b))

    def test_malformed_semantics_fail(self):
        for text in ['(x','(x))','((x))','(x "line\nbreak")']:
            with self.assertRaises(ValueError): self.semantic(text)

    def test_pin_mismatch_and_symlink_reject(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with self.assertRaises(ValueError):f.verify_inputs(root)
            (root/'osc-core.kicad_pcb').write_text('wrong')
            with self.assertRaises(ValueError):f.verify_inputs(root)

    def test_drc_identity_multiplicity_and_delta(self):
        row={'type':'unconnected_items','severity':'error','description':'gap','items':[{'uuid':'a'},{'uuid':'b'}]}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'drc.json'; p.write_text(json.dumps({'kicad_version':'10.0.6','violations':[],'unconnected_items':[row,row],'schematic_parity':[]}))
            counts,ids=f.drc_summary(p);self.assertEqual(sum(ids.values()),2)
            delta=f.delta(ids,ids+ids);self.assertEqual(delta['added']['count'],2);self.assertEqual(delta['removed']['count'],0)
            row['items']=[{}];p.write_text(json.dumps({'kicad_version':'10.0.6','violations':[row],'unconnected_items':[],'schematic_parity':[]}))
            with self.assertRaises(ValueError):f.drc_summary(p)

    def test_report_bound_before_parse(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'d';p.write_text('12345')
            with patch.object(f,'REPORT_LIMIT',4),self.assertRaisesRegex(ValueError,'bound'):f.drc_summary(p)

    def test_delta_samples_are_explicitly_incomplete(self):
        import collections
        d=f.delta(collections.Counter(),collections.Counter({str(i):1 for i in range(40)}))
        self.assertFalse(d['added']['sample_complete']);self.assertEqual(len(d['added']['sample']),32)

    def test_expired_budget_never_starts_process(self):
        with patch.object(f.time,'monotonic',return_value=10),patch.object(f.subprocess,'Popen') as launch:
            with self.assertRaises(TimeoutError):f.bounded([],Path('.'),9,Path('unused'))
            launch.assert_not_called()

    def test_success_validator_fail_closed(self):
        import copy,collections
        h='a'*64
        native={'membership':{n:{'count':0,'uuid_sha256':h,'selected_members':[]} for n in set(f.topology.EXPECTED)|set(f.VIAS)},'zones':[{'uuid':u,'net':'AGND','rule_area':False,'counts':{'F.Cu':0}} for u in f.topology.ZONES],'entry_terminal':None,'entry_terminal_status':'UNRESOLVED'}
        drc={'before':{},'after':{},'before_identity_sha256':h,'after_identity_sha256':h,'delta':f.delta(collections.Counter(),collections.Counter())}
        r={'status':f.STATUS,'board_acceptance':False,'source_hashes':{'before':f.PINS,'after':f.PINS},'nonfill_input':h,'nonfill_before':h,'nonfill_after':h,'commands':[{'exit_code':0}]*4,'elapsed_seconds':99,'native_before':native,'native_after':native,'drc':drc,'scratch_hashes':{'input':f.PINS['osc-core.kicad_pcb'],'before':h,'after':h}}
        f.validate_result(r)
        for key,value in [('board_acceptance',True),('elapsed_seconds',101),('nonfill_after','b'),('failure',{}),('native_before',{}),('native_after',{}),('drc',{}),('scratch_hashes',{})]:
            altered=dict(r);altered[key]=value
            with self.assertRaises(ValueError):f.validate_result(altered)
        # Normalization and fill agreeing with each other cannot excuse a mutation
        # from the exact input's semantics.
        altered=copy.deepcopy(r);altered['nonfill_input']='b'*64
        with self.assertRaisesRegex(ValueError,'semantics'):f.validate_result(altered)
        for field,bad in [('membership',{}),('zones',[])]:
            altered=copy.deepcopy(r);altered['native_before'][field]=bad
            with self.assertRaises(ValueError):f.validate_result(altered)

    def test_membership_bound_during_iteration(self):
        visited=[]
        def items():
            for n in range(100): visited.append(n);yield str(n)
        with patch.object(f,'MEMBER_LIMIT',3),patch.object(f.topology,'uid',side_effect=lambda x:x):
            with self.assertRaisesRegex(ValueError,'bound'):f.bounded_members(items())
        self.assertEqual(visited,[0,1,2,3])

    def test_pcb_output_monitor_kills_on_growth(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);board=root/'board';board.write_bytes(b'12345')
            proc=unittest.mock.Mock();proc.poll.return_value=None;proc.pid=123
            with patch.object(f.subprocess,'Popen',return_value=proc),patch.object(f.os,'killpg',create=True) as kill,patch.object(f.signal,'SIGKILL',9,create=True):
                with self.assertRaisesRegex(ValueError,'file size bound'):
                    f.bounded(['fake'],root,f.time.monotonic()+2,root/'log',((board,4),))
                kill.assert_called_once_with(123,f.signal.SIGKILL);proc.wait.assert_called_once_with(timeout=2)

    def test_no_refill_cli_or_original_save(self):
        source=Path(f.__file__).read_text()
        self.assertNotIn('--refill-zones',source);self.assertNotIn('--save-board',source)
        self.assertEqual(source.count('ZONE_FILLER(board).Fill(board.Zones())'),1)
        self.assertIn("path=scratch/'after'/'osc-core.kicad_pcb'",source)


if __name__=='__main__':unittest.main()
