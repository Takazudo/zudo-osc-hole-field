"""Quota-bound transport shared by E16 source fixtures and admitted operation.

Pickle is trusted-code input: only independently bound original bytes may reach
this decoder. Streaming bounds decoded bytes, not the pickle memo/object graph;
those allocations additionally require the worker's enforced memory cgroup.
"""
import gzip
import hashlib
import io
import json
import os
import pickle
import time
from pathlib import Path

from resistance_attribution import need

OUTPUT_MAX = 64*1024**2
RECEIPT_RESERVE = 65536


class Budget:
    def __init__(self, seconds=180., output_bytes=OUTPUT_MAX, clock=time.monotonic):
        need(0 < seconds <= 180 and RECEIPT_RESERVE < output_bytes <= OUTPUT_MAX, 'invalid fixed budget')
        self.clock = clock
        self.started = clock()
        self.deadline = self.started + seconds
        self.limit = output_bytes
        self.used = 0
        self.cancelled = False
        self.phase = 'entry'

    def check(self):
        need(not self.cancelled, 'CANCELLED')
        need(self.clock() < self.deadline, 'TIMEOUT')

    def charge(self, size, terminal=False):
        if not terminal:
            self.check()
        need(size >= 0 and self.used + size <= self.limit-(0 if terminal else RECEIPT_RESERVE), 'aggregate output quota exhausted')
        self.used += size


class LimitedReader(io.RawIOBase):
    def __init__(self, stream, limit, budget):
        self.stream, self.limit, self.budget = stream, limit, budget
        self.count = 0
        self.hash = hashlib.sha256()

    def readable(self):
        return True

    def readinto(self, buffer):
        self.budget.check()
        # At most 64 KiB is requested from gzip even when pickle requests a huge
        # frame. The BufferedReader may allocate its requested frame: cgrouped.
        data = self.stream.read(min(len(buffer),65536,self.limit-self.count+1))
        self.count += len(data)
        need(self.count <= self.limit, 'decoded payload limit exceeded')
        self.hash.update(data)
        buffer[:len(data)] = data
        return len(data)


def sha_stream(stream, budget):
    h = hashlib.sha256()
    while True:
        budget.check()
        chunk = stream.read(65536)
        if not chunk:
            return h.hexdigest()
        h.update(chunk)


def decode(binding, budget):
    """Verify same descriptor before interpretation, drain and rehash afterwards.

    Caller must have validated binding against the independent original request
    or artifact index inside the guard. Compressed and decoded hashes are distinct.
    No compressed-byte/decompressed-byte/object triple is materialized.
    """
    budget.check()
    path = Path(binding['path'])
    need(0 < binding['decoded_limit'] <= 512*1024**2, 'invalid decoded limit')
    with path.open('rb') as raw:
        before = os.fstat(raw.fileno())
        need(before.st_size == binding['bytes'], 'artifact size changed')
        need(sha_stream(raw,budget) == binding['sha256'], 'artifact hash changed')
        raw.seek(0)
        with gzip.GzipFile(fileobj=raw) if binding.get('gzip',True) else _Borrowed(raw) as compressed:
            limited = LimitedReader(compressed,binding['decoded_limit'],budget)
            with io.BufferedReader(limited,buffer_size=65536) as stream:
                if binding['format'] == 'pickle':
                    value = pickle.load(stream)
                    need(stream.read(1) == b'', 'trailing pickle content')
                elif binding['format'] == 'json':
                    # JSON parser and text/object copies are explicitly included
                    # in the decoded/object allowance; never claimed zero-copy.
                    value = json.load(stream)
                else:
                    raise ValueError('unsupported artifact encoding')
                need(stream.read(1) == b'', 'unexhausted artifact')
                if binding.get('decoded_sha256'):
                    need(limited.hash.hexdigest() == binding['decoded_sha256'], 'decoded identity changed')
        after = os.fstat(raw.fileno())
        need((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns) ==
             (after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns), 'artifact changed during decoding')
        raw.seek(0)
        need(sha_stream(raw,budget) == binding['sha256'], 'artifact changed during interpretation')
    return value


class _Borrowed:
    def __init__(self, stream):
        self.stream = stream
    def __enter__(self):
        return self.stream
    def __exit__(self,*args):
        pass


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


class Output:
    """Only terminal receipt can commit a fully exhausted result stream.

    A .partial file never counts as complete, even if its last line parses.
    The receipt binds final stream bytes; absent/negative receipt forbids use.
    Output root must be fresh. Failed identity/output cannot be resumed.
    """
    def __init__(self, root, budget):
        self.root, self.budget = Path(root), budget
        need(self.root.is_absolute() and self.root.resolve() == self.root, 'canonical output path required')
        self.failure_record = None
        self.root.mkdir(parents=False,exist_ok=False)
        self.path = self.root/'components.partial'
        self.stream = self.path.open('xb')
        self.hash = hashlib.sha256()
        self.rows = 0
        self.closed = False

    def row(self,value):
        data = canonical(value)
        self.budget.charge(len(data))
        self.stream.write(data)
        self.hash.update(data)
        self.rows += 1

    def finish(self, summary):
        self.budget.check()
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.stream.close()
        self.closed = True
        record = {'schema':'e16-attribution-terminal-v1','status':'COMPLETE',
                  'components_sha256':self.hash.hexdigest(),'component_rows':self.rows,
                  'summary':summary,'electrical_acceptance':False,
                  'whole_board_acceptance':False,'adopted':False}
        data = canonical(record)
        # Success finalization also obeys deadline; failures reserve a receipt.
        self.budget.check()
        self.budget.charge(len(data))
        with (self.root/'terminal.pending').open('xb') as out:
            out.write(data); out.flush(); os.fsync(out.fileno())
        self.budget.check()
        self.path.rename(self.root/'components.jsonl')
        need(not (self.root/'terminal.json').exists() and not (self.root/'terminal.json').is_symlink(), 'terminal destination already exists')
        (self.root/'terminal.pending').rename(self.root/'terminal.json')
        return record

    def fail(self, error):
        if self.failure_record is not None:
            return self.failure_record
        close_error = None
        if not self.closed:
            try:
                self.stream.close()
            except OSError as exc:
                close_error = str(exc)[:512]
            self.closed = True
        # Even if success committed before a later cleanup error, revoke it.
        # Unlinking a symlink never follows its target; fresh-root ownership is
        # required by the constructor. No retry or failed-identity resume exists.
        for name in ('terminal.pending','terminal.json'):
            (self.root/name).unlink(missing_ok=True)
        complete = self.root/'components.jsonl'
        if complete.exists() or complete.is_symlink():
            need(not self.path.exists() and not self.path.is_symlink(), 'conflicting partial output')
            complete.rename(self.path)
        record = {'schema':'e16-attribution-terminal-v1','status':'INCOMPLETE',
                  'phase':str(self.budget.phase)[:256],'reason':str(error)[:2048],
                  'component_rows':self.rows,'partial_sha256':self.hash.hexdigest(),
                  'close_error':close_error,
                  'electrical_acceptance':False,'whole_board_acceptance':False,'adopted':False}
        data = canonical(record)
        need(len(data) <= RECEIPT_RESERVE, 'failure receipt reserve exceeded')
        self.budget.charge(len(data),terminal=True)
        fd = os.open(self.root/'terminal.pending',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as out:
            out.write(data); out.flush(); os.fsync(out.fileno())
        (self.root/'terminal.pending').rename(self.root/'terminal.json')
        self.failure_record = record
        return record
