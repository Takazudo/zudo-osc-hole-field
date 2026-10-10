"""Keep declared JR replay choices executable through the strict dispatch allowlist."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RoutingWorkflowDispatchTests(unittest.TestCase):
    def setUp(self):
        source = (ROOT / '.github/workflows/routing-benchmark.yml').read_text()
        choices = re.search(r'jr_replay:\s*\n(?:(?!      \w).+\n)*?        options: \[([^\]]+)\]', source)
        self.assertIsNotNone(choices)
        self.choices = [choice.strip() for choice in choices[1].split(',')]
        allowlist = re.search(r'case "\$JR_REPLAY" in\n.*?\besac', source, re.DOTALL)
        self.assertIsNotNone(allowlist)
        self.allowlist = allowlist[0]

    def dispatch(self, choice):
        return subprocess.run(['bash', '-c', self.allowlist], env={**os.environ, 'JR_REPLAY': choice}, capture_output=True).returncode

    def test_every_declared_jr_replay_passes_dispatch(self):
        for choice in self.choices:
            with self.subTest(choice=choice):
                self.assertEqual(self.dispatch(choice), 0)

    def test_joint_replay_requires_complete_audits_without_changing_legacy_replays(self):
        source=(ROOT/'.github/workflows/routing-benchmark.yml').read_text()
        step=source.split('      - name: Replay reviewed JR copper through the native gate\n',1)[1].split('      - name:',1)[0]
        body=textwrap.dedent(step.split('        run: |\n',1)[1])
        for choice,limit,complete in [('d7604-return-joint','120m',True),('in3-two-whole','120m',True),('c7413-endpoints','80m',False)]:
            with self.subTest(choice=choice), tempfile.TemporaryDirectory() as directory:
                prefix='python() { printf "%s\\n" "$@" > prepare-args; }; timeout() { printf "%s\\n" "$@" > native-args; };\n'
                result=subprocess.run(['bash','-c',prefix+body],cwd=directory,
                    env={**os.environ,'JR_REPLAY':choice},capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                args=(Path(directory)/'native-args').read_text().splitlines()
                self.assertIn(limit,args)
                self.assertEqual('--complete-native-warnings' in args,complete)
                self.assertEqual('--native-zone-batch-size' in args,complete)
                if complete:
                    self.assertEqual(args[args.index('--native-zone-batch-size')+1],'16')
                    directory_name = 'jr-layer-escape' if choice == 'in3-two-whole' else 'jr-neighbour-return-repair'
                    self.assertEqual((Path(directory)/'prepare-args').read_text().splitlines(),
                        ['circuit/routing/issue189/' + directory_name + '/prepare_adoption.py'])

    def test_unknown_jr_replay_is_rejected(self):
        self.assertNotEqual(self.dispatch('unknown-replay'), 0)

    def test_reviewed_jl_cut_cannot_dispatch_without_complete_bound_audit(self):
        source=(ROOT/'.github/workflows/routing-benchmark.yml').read_text()
        step=source.split('      - name: Replay reviewed JL copper through full native gates\n',1)[1].split('      - name:',1)[0]
        body=textwrap.dedent(step.split('        run: |\n',1)[1])
        for choice,complete in [('r8127-via-branch',True),('r8276-joint',False)]:
            with self.subTest(choice=choice),tempfile.TemporaryDirectory() as directory:
                prefix='python() { printf "%s\\n" "$@" > prepare-args; }; timeout() { printf "%s\\n" "$@" > native-args; };\n'
                result=subprocess.run(['bash','-c',prefix+body],cwd=directory,env={**os.environ,'JL_REPLAY':choice},capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                args=(Path(directory)/'native-args').read_text().splitlines()
                for flag in ('--complete-native-warnings','--native-zone-batch-size','--reviewed-cut-plan'):
                    self.assertEqual(flag in args,complete)
                self.assertIn('120m' if complete else '80m',args)
                if complete:
                    self.assertEqual(args[args.index('--native-zone-batch-size')+1],'16')
                    self.assertEqual(args[args.index('--reviewed-cut-plan')+1],'circuit/routing/issue189/jl118-r8127-via-branch/plan.json')


if __name__ == '__main__':
    unittest.main()
