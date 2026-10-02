"""Native exit zero is insufficient: traces must be fresh and errors absent."""
from contextlib import ExitStack, redirect_stdout
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from design.spec.modules import run_envelope_spice as envelope
from design.spec.modules import run_filter_spice as filter_model
from design.spec.modules import run_noise_spice as noise

ENVELOPE = (Path(__file__).with_name('fixtures') / 'envelope-ar-trace-control.txt').read_text()
# Synthetic AC controls exercise runner I/O acceptance, not physical response.
WHITE = 'frequency gain\n' + ''.join(f'{10**(i/40):.12g} 0\n' for i in range(201))


def filter_trace(stem):
    frequency = int(stem.split('-')[1])
    output = 0 if stem.endswith('gain1') else -40
    return ('frequency LP BP HP OUT\n'
            f'{frequency/10} 0 -20 -40 {output}\n'
            f'{frequency} -3 3 -3 {output}\n'
            f'{frequency*10} -40 -20 0 {output}\n')


class SpiceTraceFreshness(unittest.TestCase):
    def exercise(self, model, behavior):
        with TemporaryDirectory(prefix='spice-output-test-') as directory, ExitStack() as stack:
            root = Path(directory)
            decks = root / 'decks'; decks.mkdir()
            cache = root / ('.circuit-cache/filter-spice' if model is filter_model else 'cache')
            cache.mkdir(parents=True)
            stack.enter_context(patch.object(model, 'ROOT', root))
            stack.enter_context(patch.object(model, 'DIR', decks))
            stack.enter_context(patch.object(model, 'SCRATCH' if model is filter_model else 'CACHE', cache))
            stack.enter_context(patch.object(model, 'OUT', root / 'report.json'))
            if model is noise:
                stack.enter_context(patch.object(model, 'CASES', {'WHITE': noise.CASES['WHITE']}))
                traces = {'white': WHITE}
            elif model is envelope:
                traces = {'envelope-ar-linear-normal': ENVELOPE}
            else:
                stems = [f'filter-{fc}-{res}-gain1' for fc in (100, 1000, 10000) for res in ('low', 'high')]
                stems += [f'filter-1000-{res}-gain0' for res in ('low', 'high')]
                traces = {stem: filter_trace(stem) for stem in stems}
            for stem, body in traces.items():
                (cache / (stem + '.txt')).write_text(body)
            calls = []

            def oracle(args, **kwargs):
                stem = Path(args[-1]).stem
                trace_key = 'white' if model is noise else stem
                trace = cache / (trace_key + '.txt') if trace_key in traces else None
                calls.append(stem)
                if trace is not None:
                    self.assertFalse(trace.exists(), 'previous trace survived until oracle execution')
                    if behavior not in ('missing', 'empty'):
                        trace.write_text(traces[trace_key])
                    elif behavior == 'empty':
                        trace.write_text('')
                stdout = 'bp_max = 3\nbp_min = -3\nlp_max = 3\nlp_min = -3\n'
                stderr = ''
                if behavior == 'error':
                    stderr = 'Error: no such vector NO_SUCH_NODE\n'
                if behavior == 'stdout_error':
                    stdout += 'Error: control command failed\n'
                if behavior == 'aborted':
                    stderr = 'run simulation(s) aborted\n'
                if behavior == 'warning':
                    stderr = 'Warning: synthetic advisory; completed control trace\n'
                return SimpleNamespace(returncode=1 if behavior == 'nonzero' else 0,
                                       stdout=stdout, stderr=stderr)

            stack.enter_context(patch.object(model.subprocess, 'run', side_effect=oracle))
            with redirect_stdout(io.StringIO()):
                if behavior in ('success', 'warning'):
                    result = model.run('AR', False) if model is envelope else model.main()
                    if model is envelope:
                        self.assertTrue(result['status'].startswith('PASS'))
                    else:
                        self.assertTrue((root / 'report.json').exists())
                    self.assertEqual(len(calls), 9 if model is filter_model else 1)
                else:
                    with self.assertRaisesRegex(RuntimeError, 'ngspice'):
                        model.run('AR', False) if model is envelope else model.main()
                    self.assertEqual(len(calls), 1, 'a failed run reached subsequent cases')
                    self.assertFalse((root / 'report.json').exists())

    def test_cached_trace_cannot_replace_missing_or_empty_new_output(self):
        for model in (envelope, noise, filter_model):
            for behavior in ('missing', 'empty'):
                with self.subTest(model=model.__name__, behavior=behavior):
                    self.exercise(model, behavior)

    def test_zero_exit_errors_or_aborts_reject_even_fresh_numeric_data(self):
        for model in (envelope, noise, filter_model):
            for behavior in ('error', 'stdout_error', 'aborted'):
                with self.subTest(model=model.__name__, behavior=behavior):
                    self.exercise(model, behavior)

    def test_nonzero_exit_rejects_fresh_numeric_data(self):
        for model in (envelope, noise, filter_model):
            with self.subTest(model=model.__name__):
                self.exercise(model, 'nonzero')

    def test_successful_fresh_runs_and_advisory_warnings_remain_accepted(self):
        for model in (envelope, noise, filter_model):
            for behavior in ('success', 'warning'):
                with self.subTest(model=model.__name__, behavior=behavior):
                    self.exercise(model, behavior)


if __name__ == '__main__':
    unittest.main()
