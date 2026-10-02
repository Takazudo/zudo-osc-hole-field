#!/usr/bin/env python3
"""Require an explicit publication decision for every manual inventory record."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def keyed(rows, key):
    result = {}
    for row in rows:
        identity = row[key]
        if identity in result:
            raise ValueError(f'duplicate {key}: {identity}')
        result[identity] = row
    return result


def check_publication(lines, records, selection, decisions, sources, facts, renderer_version):
    inventory = keyed(lines, 'line_id')
    by_line = keyed(records, 'line_id')
    expected = {by_line[line]['record_id'] for line in inventory if line in by_line}
    if len(expected) != len(inventory):
        raise ValueError('inventory line has no unique exact owner record')
    selected = selection['recordIds']
    if len(set(selected)) != len(selected):
        raise ValueError('duplicate selected record')
    selected = set(selected)
    blocked = keyed(decisions['blocked_records'], 'record_id')
    excluded = keyed(decisions['intentional_exclusions'], 'record_id')
    if decisions['schema_version'] != 1:
        raise ValueError('unsupported publication decision schema')
    if blocked and renderer_version != decisions['renderer']['version']:
        raise ValueError('renderer changed: re-review every publication blocker')
    for kind, rows in (('blocked', blocked), ('excluded', excluded)):
        for identity, row in rows.items():
            if not isinstance(row.get('reason'), str) or not row['reason'].strip():
                raise ValueError(f'{identity}: {kind} decision needs an explicit reason')
            if kind == 'blocked' and (not row.get('blockers') or not row.get('unblock')):
                raise ValueError(f'{identity}: blocker needs its condition and resolution')
    if selected & blocked.keys() or selected & excluded.keys() or blocked.keys() & excluded.keys():
        raise ValueError('record has conflicting publication decisions')
    decided = selected | blocked.keys() | excluded.keys()
    if decided != expected:
        raise ValueError(f'publication coverage differs: missing={sorted(expected-decided)}, stale={sorted(decided-expected)}')
    documents = keyed(selection['documentSelections'], 'recordId')
    record_by_id = keyed(records, 'record_id')
    for constraint in decisions['document_constraints']:
        identity = constraint['record_id']
        if identity not in expected:
            raise ValueError('document constraint references an absent inventory record')
        if identity not in selected:
            continue
        document = documents[identity]
        source = sources[constraint['source_id']]
        fact = facts[constraint['applicability_fact_id']]
        line = inventory[record_by_id[identity]['line_id']]
        if (document['sourceId'] != constraint['source_id'] or
                document['documentKind'] != constraint['document_kind'] or
                source['document_title'] != constraint['source_title'] or
                source['authority_class'] != constraint['authority_class']):
            raise ValueError(f'{identity}: family document was mislabelled or its source metadata changed')
        if fact['verdict'] != constraint['applicability_verdict']:
            raise ValueError(f'{identity}: unresolved exact applicability was promoted')
        if any(term not in line['function'] or term not in fact['conditions']
               for term in constraint['required_record_terms']):
            raise ValueError(f'{identity}: prominent family/applicability warning is missing')
    return {'inventory': len(expected), 'published': len(selected),
            'blocked': len(blocked), 'excluded': len(excluded)}


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    lines = read('.claude/skills/component-spec-audit/references/inventory.json')['lines']
    records = []; sources = []; facts = []
    for owner in sorted({line['owner_skill'] for line in lines}):
        directory = f'.claude/skills/{owner}'
        records += read(f'{directory}/manifest.json')['records']
        sources += read(f'{directory}/sources.json')['sources']
        facts += read(f'{directory}/facts.json')['facts']
    result = check_publication(lines, records, read('circuit/publication/selection.json'),
                               read('design/standard/catalogue-publication.json'),
                               keyed(sources, 'source_id'), keyed(facts, 'fact_id'),
                               read('node_modules/@takazudo/zudo-circuit-doc/package.json')['version'])
    print('PASS: explicit catalogue decisions:', result)
    if result['blocked']:
        print('SCOPE: catalogue completion remains OPEN; renderer blockers are explicit, not waived. Physical qualification NOT RUN.')


if __name__ == '__main__':
    main()
