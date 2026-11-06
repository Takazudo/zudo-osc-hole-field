"""Independent retention tests using synthetic bytes only; no CAD invocation."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import stage17_retain as r


def manifest(files):
    return [{'path':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
            for name,data in sorted(files.items())]


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dest=Path(self.temp.name)/'retained'
        self.files={'command-0.stdout':b'10.0.6\n','netlist.net':b'\x00\xff\x80 synthetic\n',
                    'config/nested.bin':bytes(range(256)), 'empty.log':b''}
        self.rows=manifest(self.files)

    def runner(self,argv,limit,deadline,sink):
        if argv[-1]==r.MANIFEST_CODE:
            data=json.dumps(self.rows).encode()
        else:
            self.assertEqual(argv[-2],r.FILE_CODE)
            data=self.files[argv[-1]]
        total=0
        for start in range(0,len(data),7):
            chunk=data[start:start+7]
            if total+len(chunk)>limit:
                raise ValueError('test stream exceeds cap')
            sink(chunk); total+=len(chunk)
        return total

    def retain(self,**kwargs):
        return r.retain('synthetic-only',self.dest,['command-0.stdout','netlist.net'],
                        runner=self.runner,**kwargs)

    def assert_unpublished(self):
        self.assertFalse(self.dest.exists())

    def test_binary_roundtrip_and_nested_paths(self):
        result=self.retain()
        self.assertTrue(result['cleanup_permitted'])
        self.assertEqual(result['bytes'],sum(map(len,self.files.values())))
        for name,data in self.files.items(): self.assertEqual((self.dest/name).read_bytes(),data)
        self.assertFalse(self.dest.with_name('retained.partial').exists())

    def test_exact_total_limit(self):
        self.retain(limit=sum(map(len,self.files.values())))

    def test_total_excess_rejected_before_staging(self):
        with self.assertRaises(ValueError): self.retain(limit=sum(map(len,self.files.values()))-1)
        self.assert_unpublished()
        self.assertFalse(self.dest.with_name('retained.partial').exists())

    def test_missing_required_file(self):
        self.rows=[x for x in self.rows if x['path']!='netlist.net']
        with self.assertRaises(ValueError): self.retain()
        self.assert_unpublished()

    def test_empty_manifest(self):
        self.rows=[]
        with self.assertRaises(ValueError): self.retain()
        self.assert_unpublished()

    def test_hash_mismatch_never_publishes(self):
        self.rows[0]['sha256']='0'*64
        with self.assertRaises(ValueError): self.retain()
        self.assert_unpublished()

    def test_truncated_file_never_publishes(self):
        self.files['netlist.net']=self.files['netlist.net'][:-1]
        with self.assertRaises(ValueError): self.retain()
        self.assert_unpublished()

    def test_extra_file_bytes_never_publishes(self):
        self.files['netlist.net']+=b'extra'
        with self.assertRaises(ValueError): self.retain()
        self.assert_unpublished()

    def test_manifest_paths(self):
        for name in ('../escape','/absolute','a/../b','a\\b','C:drive','a//b','a/./b','','.','bad\x00name'):
            with self.subTest(name=name):
                rows=copy.deepcopy(self.rows); rows[0]['path']=name
                with self.assertRaises(ValueError): r.validate_manifest(rows,[],10000)

    def test_duplicate_manifest_path(self):
        with self.assertRaises(ValueError): r.validate_manifest(self.rows+[self.rows[0]],[],10000)

    def test_invalid_sizes_and_hashes(self):
        for size in (-1,1.5,True,'2'):
            rows=copy.deepcopy(self.rows); rows[0]['size']=size
            with self.assertRaises(ValueError): r.validate_manifest(rows,[],10000)
        for digest in ('f'*63,'g'*64,'A'*64, None):
            rows=copy.deepcopy(self.rows); rows[0]['sha256']=digest
            with self.assertRaises(ValueError): r.validate_manifest(rows,[],10000)

    def test_excessive_manifest_count(self):
        with self.assertRaises(ValueError): r.validate_manifest([self.rows[0]]*4097,[],10000)

    def test_existing_destination_or_staging(self):
        for path in (self.dest,self.dest.with_name('retained.partial')):
            path.mkdir()
            with self.assertRaises(ValueError): self.retain()
            path.rmdir()

    def test_fsync_error_never_publishes(self):
        with patch.object(r.os,'fsync',side_effect=OSError('synthetic fsync failure')):
            with self.assertRaises(OSError): self.retain()
        self.assert_unpublished()

    def test_stream_failure_after_partial_output(self):
        original=self.runner
        def failing(argv,limit,deadline,sink):
            if argv[-1]=='netlist.net':
                sink(b'partial'); raise ValueError('synthetic command failure')
            return original(argv,limit,deadline,sink)
        with self.assertRaises(ValueError):
            r.retain('synthetic-only',self.dest,['netlist.net'],runner=failing)
        self.assert_unpublished()

    def test_invalid_manifest_json(self):
        def broken(argv,limit,deadline,sink): sink(b'not json'); return 8
        with self.assertRaises(ValueError):
            r.retain('synthetic-only',self.dest,[],runner=broken)
        self.assert_unpublished()

    def test_source_inventory_changes_before_publication(self):
        original=self.runner
        calls=0
        def changing(argv,limit,deadline,sink):
            nonlocal calls
            if argv[-1]==r.MANIFEST_CODE:
                calls+=1
                if calls==2:
                    self.rows.append({'path':'late','size':0,'sha256':hashlib.sha256(b'').hexdigest()})
            return original(argv,limit,deadline,sink)
        with self.assertRaises(ValueError):
            r.retain('synthetic-only',self.dest,['netlist.net'],runner=changing)
        self.assert_unpublished()


class RealPipeTests(unittest.TestCase):
    """Exercise the actual bounded pipe reader with Python synthetic writers."""
    def run_stream(self,code,limit=100,seconds=3):
        chunks=[]
        result=r.stream([sys.executable,'-c',code],limit,time.monotonic()+seconds,chunks.append)
        return result,b''.join(chunks)

    def test_exact_pipe_limit(self):
        self.assertEqual(self.run_stream("import sys;sys.stdout.buffer.write(bytes(range(100)))"),
                         (100,bytes(range(100))))

    def test_oversized_pipe_never_writes_excess(self):
        chunks=[]
        with self.assertRaises(ValueError):
            r.stream([sys.executable,'-c',"import sys;sys.stdout.buffer.write(b'x'*101)"],
                     100,time.monotonic()+3,chunks.append)
        self.assertLessEqual(sum(map(len,chunks)),100)

    def test_pipe_exit_failure(self):
        with self.assertRaises(ValueError): self.run_stream("print('partial');raise SystemExit(2)")

    def test_pipe_deadline(self):
        with self.assertRaises(TimeoutError): self.run_stream('import time;time.sleep(1)',seconds=.05)

    def test_manifest_pipe_cap(self):
        with self.assertRaises(ValueError):
            self.run_stream("import sys;sys.stdout.buffer.write(b'x'*1048577)",limit=r.MANIFEST_LIMIT)


class ManifestScannerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def scan(self):
        # Only substitute the isolated test root; execute the production scanner.
        code=r.MANIFEST_CODE.replace("pathlib.Path('/output')",'pathlib.Path('+repr(str(self.root))+')')
        return subprocess.run([sys.executable,'-c',code],capture_output=True,timeout=3)

    def test_symlink_file_rejected(self):
        (self.root/'data').write_bytes(b'synthetic')
        (self.root/'link').symlink_to(self.root/'data')
        self.assertNotEqual(self.scan().returncode,0)

    def test_symlink_directory_rejected(self):
        (self.root/'sub').mkdir()
        (self.root/'link').symlink_to(self.root/'sub',target_is_directory=True)
        self.assertNotEqual(self.scan().returncode,0)

    @unittest.skipUnless(hasattr(os,'mkfifo'),'POSIX synthetic FIFO test')
    def test_special_file_rejected_without_blocking(self):
        os.mkfifo(self.root/'fifo')
        self.assertNotEqual(self.scan().returncode,0)

    def test_scanner_binary_hash_and_empty_file(self):
        files={'data':b'\x00\xff\x80','empty':b''}
        for name,data in files.items(): (self.root/name).write_bytes(data)
        result=self.scan()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout),manifest(files))


if __name__=='__main__': unittest.main()
