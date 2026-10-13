"""Terminal/auth lifecycle units; sudo and workload launches are mocked."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

try:
    from . import operator_terminal as t
except ImportError:
    import operator_terminal as t


class OperatorTerminal(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.log=Path(self.tmp.name)/'driver.log'
        checked=patch.object(t,'check_operator_terminal');checked.start();self.addCleanup(checked.stop)

    def test_auth_failure_never_launches_or_logs_workload(self):
        with patch.object(t.subprocess,'run',return_value=subprocess.CompletedProcess([],1)),patch.object(t.subprocess,'Popen') as launch:
            self.assertEqual(t.run_in_terminal(['fixture'],self.log),1)
        launch.assert_not_called();self.assertFalse(self.log.exists())

    def test_auth_output_is_not_captured_and_workload_exit_is_preserved(self):
        process=Mock();process.wait.return_value=7;process.poll.return_value=7
        def launch(command,**kwargs):
            kwargs['stdout'].write('workload only\n');return process
        with patch.object(t.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as auth,patch.object(t.subprocess,'Popen',side_effect=launch):
            self.assertEqual(t.run_in_terminal(['fixture'],self.log),7)
        self.assertEqual(auth.call_count,2)
        for call in auth.call_args_list:
            self.assertNotIn('stdout',call.kwargs);self.assertNotIn('stdin',call.kwargs)
            self.assertNotIn('input',call.kwargs)
        self.assertEqual(self.log.read_text(),'workload only\n')

    def test_ticket_refresh_is_noninteractive_and_ends_with_workload(self):
        process=Mock();process.wait.side_effect=[subprocess.TimeoutExpired('fixture',30),0];process.poll.return_value=0
        with patch.object(t.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as auth,patch.object(t.subprocess,'Popen',return_value=process):
            self.assertEqual(t.run_in_terminal(['fixture'],self.log),0)
        self.assertEqual(auth.call_count,3)
        self.assertEqual(auth.call_args.args[0],['sudo','-n','-v'])
        self.assertEqual(auth.call_args.kwargs['timeout'],5)
        process.terminate.assert_not_called()

    def test_refresh_failure_stops_workload_and_cannot_pass(self):
        process=Mock();process.wait.side_effect=[subprocess.TimeoutExpired('fixture',30),0];process.poll.side_effect=[None,0]
        with patch.object(t.subprocess,'run',side_effect=[subprocess.CompletedProcess([],0),subprocess.CompletedProcess([],0),subprocess.CompletedProcess([],1)]),patch.object(t.subprocess,'Popen',return_value=process):
            self.assertEqual(t.run_in_terminal(['fixture'],self.log),1)
        process.terminate.assert_called_once()


class TerminalRequirement(unittest.TestCase):
    def test_no_terminal_fails_without_sudo(self):
        with patch.object(t.os,'isatty',return_value=False),patch.object(t.subprocess,'run') as auth,self.assertRaises(ValueError):
            t.check_operator_terminal()
        auth.assert_not_called()

    def test_sets_id_fd_tty_alone_is_not_controlling_tty(self):
        with patch.object(t.os,'isatty',return_value=True),patch.object(t.os,'open',side_effect=OSError('no controlling terminal')),self.assertRaises(OSError):
            t.check_operator_terminal()


if __name__=='__main__':unittest.main()
