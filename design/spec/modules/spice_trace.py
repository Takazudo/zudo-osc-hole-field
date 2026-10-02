"""Accept native output only after the caller removes any previous trace."""
import re


def check_oracle_result(result, trace=None):
    """ngspice can exit zero after a control-command or simulation error."""
    output = result.stdout + '\n' + result.stderr
    failed = re.search(r'(?im)^\s*(?:error|fatal error)\s*:|simulation\(s\)\s+aborted', output)
    if result.returncode or failed:
        raise RuntimeError('ngspice run failed:\n' + output)
    if trace is not None and (not trace.is_file() or trace.stat().st_size == 0):
        raise RuntimeError(f'ngspice produced no fresh nonempty trace: {trace}\n{output}')
