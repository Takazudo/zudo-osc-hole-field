"""Exact KiCad netlist population/BOM marker projection, independent of library defaults."""
import hashlib
from pathlib import Path


def source_attribute_bits(current,fields,dnp_bit,exclude_bom_bit):
    result=current & ~(dnp_bit|exclude_bom_bit)
    for name,bit in (('dnp',dnp_bit),('exclude_from_bom',exclude_bom_bit)):
        if name in fields:
            if fields[name]!='':raise ValueError('unexpected native netlist attribute marker: '+name)
            result|=bit
    return result


def source_rotation_degrees(fields,native_template_after_face=None):
    """Match sync's explicit angle or actual native library initialization.

    A missing angle is not a zero-angle claim. The caller must obtain the
    library footprint's actual orientation after applying the source face.
    """
    value=fields.get('KiCadOrientationDeg')
    if value not in (None,''):return float(value)
    if native_template_after_face is None:raise ValueError('missing native source template orientation')
    return float(native_template_after_face)


def capture_template_digests(paths):
    return {str(Path(p)):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in set(map(Path,paths))}


def verify_template_digest(path,retained):
    key=str(Path(path))
    if key not in retained or hashlib.sha256(Path(path).read_bytes()).hexdigest()!=retained[key]:
        raise ValueError('native orientation source template changed')
