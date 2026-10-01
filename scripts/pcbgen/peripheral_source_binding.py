"""Immutable prerequisite input authorities and fresh native output lifecycle."""
import hashlib
from pathlib import Path


def retain_sources(root, paths, authorities):
    root=Path(root).resolve();retained={}
    def key(path):
        path=Path(path)
        resolved=path.resolve() if path.is_absolute() else (root/path).resolve()
        if not resolved.is_relative_to(root):raise ValueError('peripheral source escapes worktree')
        return str(resolved.relative_to(root))
    for authority in authorities:
        for name,value in authority.items():
            name=key(name)
            if name in retained and retained[name]!=value:raise ValueError('conflicting retained peripheral source')
            retained[name]=value
    names=set(retained)|{key(p) for p in paths}
    for name in sorted(names):
        actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
        if name in retained and retained[name]!=actual:
            raise ValueError('peripheral source changed before native entry: '+name)
        retained.setdefault(name,actual)
    return retained


def require_fresh_outputs(output,cache):
    output=Path(output);cache=Path(cache)
    paths=[output,cache]+[output.with_suffix(suffix) for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru')]
    if any(path.exists() or path.is_symlink() for path in paths):
        raise ValueError('fresh native stem and cache required; existing PCB/companion bytes must remain unchanged')
