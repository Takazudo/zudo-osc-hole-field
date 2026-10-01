"""Expected fitted contacts derived independently of native geometry exports."""


def expected_contacts(board_id, partition, io, nets):
    boards = [b for b in partition['boards'] if b['id'] == board_id]
    if len(boards) != 1:
        raise ValueError('native board lacks one exact source board identity')
    key = boards[0]['board_key']
    assignments = partition['assignment']['components']
    if len({r['ref'] for r in assignments}) != len(assignments):
        raise ValueError('duplicate source package assignment')
    fitted = {p['ref'] for p in io['physical_packages'] if not p['dnp']}
    refs = {r['ref'] for r in assignments if r['board'] == key and r['fitted']}
    if not refs <= fitted:
        raise ValueError('assigned fitted package is absent from source physical packages')
    expected = {}
    for crossing in io['allowed_crossings']:
        if crossing['net'] not in nets:
            continue
        for member in crossing['members']:
            if member['ref'] in refs:
                identity = (member['ref'], member['pin'], crossing['net'])
                expected.setdefault(identity, []).append(member)
    if not expected:
        raise ValueError('empty board-specific expected source contact inventory')
    return expected


def reconcile_native(native, expected, fitted_refs, nets):
    rows = [i for i in native['items'] if i['net'] in nets and i.get('ref') in fitted_refs]
    identities = [(r['ref'], r['pad'], r['net']) for r in rows]
    if len(set(identities)) != len(rows):
        raise ValueError('duplicate native fitted contact identity')
    if len({r['uuid'] for r in rows}) != len(rows):
        raise ValueError('duplicate native fitted contact UUID')
    if set(identities) != set(expected):
        missing = sorted(set(expected) - set(identities))
        extra = sorted(set(identities) - set(expected))
        raise ValueError(f'native/source fitted contact mismatch: missing={missing}, extra={extra}')
    return dict(zip(identities, rows))
