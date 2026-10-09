"""Restore one archived evidence root; never overwrite differing existing bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / '.circuit-cache/issue189-downloaded'
ORIGINAL = Path('/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence_root', help='Exact manifest root, e.g. core-short19')
    args = parser.parse_args()
    rows = json.loads(Path(__file__).with_name('extracted-archive-retention.json').read_text())['files']
    rows = [r for r in rows if Path(r['path']).relative_to(ORIGINAL).parts[0] == args.evidence_root]
    if not rows:
        raise ValueError('No archived PCB files for this evidence root')
    archives = {}
    for row in rows:
        archive = Path(row['archive'])
        if archive not in archives:
            if digest(archive) != row['archive_sha256']:
                raise ValueError('Archive hash mismatch: ' + str(archive))
            archives[archive] = zipfile.ZipFile(archive)
        data = archives[archive].read(row['member'])
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Archive member hash mismatch')
        target = CACHE / Path(row['path']).relative_to(ORIGINAL)
        if target.exists():
            if digest(target) != row['sha256']:
                raise ValueError('Existing evidence differs; refusing overwrite: ' + str(target))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print('Verified/restored', len(rows), 'PCB files in', args.evidence_root)


if __name__ == '__main__':
    main()
