"""Restore only the observed hidden-field default serialization on P.

KiCad 10.0.6 inserts an explicit 0.15 mm font thickness in three hidden
LogicalCellKey properties on another save. Restore the complete original
footprint block, after proving that this is its only difference. No physical
or visible style change is permitted by this helper.
"""
import hashlib
import re
from scripts.pcbgen.uuid_tools import top_level_spans, REF_RE, UUID_RE

ALLOWED_REFS = {'U3303', 'U3403', 'U4611'}


def restore(candidate_text, original_footprints):
    edits, receipts, seen = [], [], set()
    sha = lambda value: hashlib.sha256(value.encode()).hexdigest()
    for start, end in top_level_spans(candidate_text):
        block = candidate_text[start:end]
        if not block.startswith('(footprint '):
            continue
        match = REF_RE.search(block)
        if match is None or match[1] in seen or match[1] not in original_footprints:
            raise ValueError('Unexpected or duplicate P footprint during preservation')
        ref = match[1]
        seen.add(ref)
        original = original_footprints[ref]
        if block == original:
            continue
        if ref not in ALLOWED_REFS:
            raise ValueError('Unapproved P footprint serialization change: '+ref)
        def field_span(text):
            result = [(a, b) for a, b in top_level_spans(text)
                      if text[a:b].startswith('(property "LogicalCellKey" ')]
            if len(result) != 1:
                raise ValueError('One exact LogicalCellKey field required')
            return result[0]
        a, b = field_span(block)
        c, d = field_span(original)
        new_field, old_field = block[a:b], original[c:d]
        old_children = [old_field[x:y] for x, y in top_level_spans(old_field)]
        if '(hide yes)' not in old_children or '(thickness ' in old_field:
            raise ValueError('Only the original hidden implicit-font field may be restored')
        stripped, count = re.subn(r'\n[ \t]*\(thickness 0\.15\)', '', new_field)
        if count != 1 or stripped != old_field or block[:a]+old_field+block[b:] != original:
            raise ValueError('P footprint delta is not solely the observed hidden default thickness')
        edits.append((start, end, original))
        receipts.append({'ref': ref, 'property': 'LogicalCellKey',
            'property_uuid': UUID_RE.search(old_field)[1],
            'original_footprint_sha256': sha(original), 'native_serialized_footprint_sha256': sha(block),
            'original_field_sha256': sha(old_field), 'native_serialized_field_sha256': sha(new_field),
            'restored': 'Exact original full footprint block; sole native insertion was hidden font thickness 0.15 mm'})
    if seen != set(original_footprints):
        raise ValueError('P footprint set changed during preservation')
    for start, end, original in reversed(edits):
        candidate_text = candidate_text[:start]+original+candidate_text[end:]
    return candidate_text, receipts
