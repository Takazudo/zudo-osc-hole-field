"""Launcher configuration and bounded cleanup, without starting a browser."""
import io
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import check_browser as launcher


class BrowserLauncherTests(unittest.TestCase):
    def test_explicit_missing_executable_does_not_fall_back(self):
        with patch.dict(os.environ, {'CHROME_BIN': '/also/missing'}):
            with self.assertRaisesRegex(ValueError, 'Browser discovery failed'):
                launcher.discover_browser('/missing/chrome')

    def test_configured_executable_with_spaces(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'Chrome With Spaces'
            executable.write_text('#!/bin/sh\nexit 0\n')
            executable.chmod(0o700)
            with patch.dict(os.environ, {'CHROME_BIN': str(executable)}):
                self.assertEqual(launcher.discover_browser(), str(executable))
            executable.chmod(0o600)
            with self.assertRaises(ValueError):
                launcher.discover_browser(str(executable))

    def test_mac_discovery(self):
        expected = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        with patch.dict(os.environ, {}, clear=True), patch.object(launcher.shutil, 'which', side_effect=lambda p: p if p == expected else None):
            self.assertEqual(launcher.discover_browser(), expected)

    def test_platform_flags_and_path_arguments(self):
        for platform in ['darwin', 'linux']:
            command = launcher.browser_command('/Chrome With Spaces', '/profile with spaces', '/output with spaces.png', 'file:///test.html', platform)
            self.assertEqual(command[0], '/Chrome With Spaces')
            self.assertNotIn('--no-sandbox', command)
            self.assertNotIn('--disable-gpu', command)
            self.assertEqual('--disable-dev-shm-usage' in command, platform == 'linux')
            self.assertIn('--user-data-dir=/profile with spaces', command)
            self.assertIn('--screenshot=/output with spaces.png', command)

    def test_timeout_cleans_up_process_group(self):
        with patch.object(launcher.subprocess, 'Popen') as popen, patch.object(launcher.os, 'killpg') as killpg:
            process = popen.return_value
            process.pid = 123
            process.wait.side_effect = [subprocess.TimeoutExpired('browser', 60), 0, 0]
            with self.assertRaises(subprocess.TimeoutExpired):
                launcher.bounded_run(['browser'], io.StringIO(), io.StringIO())
            self.assertTrue(popen.call_args.kwargs['start_new_session'])
            self.assertEqual(killpg.call_args_list[0].args, (123, signal.SIGTERM))
            self.assertEqual(killpg.call_args_list[1].args, (123, signal.SIGKILL))

    def test_nonzero_exit_is_preserved_and_descendants_cleaned(self):
        with patch.object(launcher.subprocess, 'Popen') as popen, patch.object(launcher.os, 'killpg') as killpg:
            popen.return_value.wait.return_value = 23
            self.assertEqual(launcher.bounded_run(['browser'], io.StringIO(), io.StringIO()), 23)
            self.assertEqual(killpg.call_count, 2)


if __name__ == '__main__':
    unittest.main()
