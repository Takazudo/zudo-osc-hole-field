"""Retire only UUID-verified generated pour blocks before native loading.

Filtering the source serialization avoids KiCad 10 SWIG lifetime corruption
when removing populated zone objects before refill. Owner zones are untouched.
"""
import re
from scripts.pcbgen.uuid_tools import stable_uuid, top_level_spans, UUID_RE


def retire(text, board_id, routing):
    desired = {f"pcbgen:{board_id}:pour:{spec['name']}:{layer}"
               for spec in routing['zones'] for layer in spec['layers']}
    prefix = f'pcbgen:{board_id}:pour:'
    removals = []; retired = set()
    for start, end in top_level_spans(text):
        block = text[start:end]
        if not block.startswith('(zone'):
            continue
        match = re.search(r'\(name\s+"([^"\n]+)"\)', block)
        if not match or not match[1].startswith(prefix) or match[1] in desired:
            continue
        expected = stable_uuid(board_id, 'pour', match[1][len(prefix):])
        identity = UUID_RE.search(block)
        if not identity or identity[1] != expected:
            raise ValueError('refusing retirement of a zone without exact source UUID')
        removals.append((start, end)); retired.add(expected)
    for start, end in reversed(removals):
        text = text[:start]+text[end:]
    return text, retired
