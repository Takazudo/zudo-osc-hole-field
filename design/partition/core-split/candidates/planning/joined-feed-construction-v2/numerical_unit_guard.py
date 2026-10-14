"""Per-unit shared-guard scheduling for explicitly admitted Linux numerical batches.

The lightweight parent never holds a heavy slot. Each solver unit queues normally,
then this helper proves the owning shared guard before entering the existing timeout
and finite_solve user-systemd scope. This is resource scheduling, not run admission.
"""
import fcntl
import hashlib
import os
from pathlib import Path
import pwd
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
DEFAULTS = {'slots': 1, 'wait_seconds': 0, 'max_run_seconds': 1800,
            'min_mem_mb': 2048, 'low_mem_mb': 512}


def need(ok, message):
    if not ok:
        raise SystemExit('numerical unit guard: ' + message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prove_inherited_lock(descriptor, lock):
    """Prove this actual OFD holds the kernel flock, without ancestor proc access.

    Custody is transferred by SCM_RIGHTS/inheritance, never by reopening a lock.
    The acquisition PID can belong to an exited flock utility, so it is not the
    guard identity. Guard/controller ancestry is separately checked by callers.
    """
    need(type(descriptor) is int and descriptor>=3,'invalid inherited lock descriptor')
    actual=os.fstat(descriptor);expected=Path(lock).stat()
    need((actual.st_dev,actual.st_ino)==(expected.st_dev,expected.st_ino),
         'inherited lock descriptor identity differs')
    info=Path(f'/proc/self/fdinfo/{descriptor}').read_text()
    locks=re.findall(r'^lock:\s+\d+:\s+FLOCK\s+ADVISORY\s+WRITE\s+-?\d+\s+([0-9a-fA-F]+):([0-9a-fA-F]+):(\d+) 0 EOF$',info,re.M)
    need(any((int(major,16),int(minor,16),int(inode))==
             (os.major(actual.st_dev),os.minor(actual.st_dev),actual.st_ino)
             for major,minor,inode in locks),'descriptor does not carry the actual exclusive flock')


class UnitGuard:
    def __init__(self, expected_sha256):
        need(bool(re.fullmatch(r'[0-9a-f]{64}', expected_sha256)), 'expected guard SHA-256 required')
        self.expected = expected_sha256
        self.home = Path(pwd.getpwuid(os.getuid()).pw_dir)
        self.path = self.home / '.codex/scripts/heavy-guard.sh'
        self.directory = self.home / '.agent-guard/heavy'

    def check(self, inside=False):
        need(os.getuid() == os.geteuid(), 'real/effective UID differs')
        need(Path(os.environ.get('HOME', '')).resolve() == self.home.resolve(), 'account HOME differs')
        allowed = {'HEAVY_GUARD_HELD'} if inside else set()
        need(not (set(k for k in os.environ if k.startswith('HEAVY_GUARD_')) - allowed),
             'guard environment override or nested guard refused')
        need(not inside or os.environ.get('HEAVY_GUARD_HELD') == '1', 'guard marker absent')
        need('E16_SOLVE_SCOPE' not in os.environ, 'inherited solver scope marker refused')
        need(sha(self.path) == self.expected, 'shared guard bytes changed')
        for tool in ('bash', 'flock', 'setsid', 'timeout', 'systemd-run'):
            need(shutil.which(tool) is not None, 'missing prerequisite: ' + tool)
        need(self.directory.is_dir() and os.access(self.directory, os.R_OK | os.W_OK | os.X_OK),
             'existing shared guard directory must be accessible; no fallback allowed')
        need(re.search(r'^MemAvailable:\s+[1-9][0-9]*\s+kB$', Path('/proc/meminfo').read_text(), re.M),
             'Linux available-memory measurement absent')

    def binding(self):
        self.check()
        return {'guard': str(self.path), 'sha256': self.expected,
                'helper_sha256': sha(__file__), 'directory': str(self.directory),
                'defaults': DEFAULTS, 'queue_outside_unit_timeout': True}

    def command(self, python, workload):
        self.check()
        return ['bash', str(self.path), '--', python, str(Path(__file__).resolve()),
                '--inside', self.expected, '--', *workload]

    def prove_owner(self, inherited_fd=None):
        self.check(inside=True)
        info = (self.directory / 'slot-0.info').read_text()
        match = re.match(r'pid=([1-9][0-9]*) ', info)
        need(match is not None, 'shared slot owner absent')
        owner = int(match.group(1))
        pid = os.getppid()
        while pid > 1 and pid != owner:
            status = Path(f'/proc/{pid}/status').read_text()
            pid = int(re.search(r'^PPid:\s+(\d+)$', status, re.M).group(1))
        need(pid == owner, 'shared slot owner is not an ancestor')
        args = Path(f'/proc/{owner}/cmdline').read_bytes().split(b'\0')
        need(str(self.path).encode() in args, 'ancestor is not the requested guard')
        lock = self.directory / 'slot-0.lock'
        if inherited_fd is None:
            need(os.path.samefile(f'/proc/{owner}/fd/200', lock), 'guard does not hold the shared slot descriptor')
        else:prove_inherited_lock(inherited_fd,lock)
        with lock.open('rb') as stream:
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                need(False, 'shared slot is not locked')

    @staticmethod
    def verdict(stderr, process_exit):
        matches = re.findall(r'^heavy-guard: verdict=(PASS|FAIL|ENV_SUSPECT) exit=(-?\d+) secs=(\d+) min_mem_mb=(\d+|\?) reason=(\S+)$', stderr, re.M)
        if len(matches) != 1:
            return {'passed': False, 'reason': 'missing or ambiguous shared guard verdict'}
        verdict, code, seconds, memory, reason = matches[0]
        passed = verdict == 'PASS' and int(code) == process_exit == 0 and memory != '?'
        return {'passed': passed, 'verdict': verdict, 'exit': int(code),
                'seconds': int(seconds), 'min_mem_mb': memory, 'reason': reason}


if __name__ == '__main__':
    need(len(sys.argv) >= 7 and sys.argv[1] == '--inside' and sys.argv[3] == '--', 'invalid inside invocation')
    guard = UnitGuard(sys.argv[2])
    guard.prove_owner()
    os.execvp(sys.argv[4], sys.argv[4:])
