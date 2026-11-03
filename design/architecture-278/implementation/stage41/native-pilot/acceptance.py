"""Pure complete-connectivity acceptance gate; no net/UUID collapsing."""
from collections import Counter


def connectivity_gate(before, after, retired=(), added=(), target_nets=()):
    retired, added = set(retired), set(added)
    original, current = set(before['objects']), set(after['objects'])
    if not retired <= original or added & original or not added <= current:
        raise ValueError('invalid explicit object delta')
    identity_set_equal = original - retired | added == current
    retained = original - retired
    def partitions(snapshot):
        result = {}
        seen = set()
        if any(not groups or any(not g for g in groups) for groups in snapshot['groups'].values()):
            raise ValueError('empty connectivity component')
        if snapshot['native_open_edges'] != sum(len(groups)-1 for groups in snapshot['groups'].values()):
            raise ValueError('declared open count differs from complete membership')
        for net, groups in snapshot['groups'].items():
            normalized = []
            for group in groups:
                members = set(group)
                if len(members) != len(group) or seen & members:
                    raise ValueError('duplicate/overlapping membership')
                if not members <= snapshot['objects'].keys():
                    raise ValueError('unknown component member')
                if any(snapshot['objects'][k]['net'] != net for k in members):
                    raise ValueError('cross-net component')
                seen |= members
                kept = sorted(members & retained)
                if kept: normalized.append(kept)
            if normalized: result[net] = sorted(normalized)
        if seen != set(snapshot['objects']):
            raise ValueError('incomplete component inventory')
        return result
    old, new = partitions(before), partitions(after)
    changed = sorted(n for n in old.keys() | new.keys() if old.get(n) != new.get(n))
    closed = {n: len(after['groups'].get(n, [])) == 1 for n in target_nets}
    new_only_islands = [{'net':n,'members':g} for n, groups in after['groups'].items() for g in groups if set(g) <= added]
    checks = {'exact_object_delta': identity_set_equal,
              'retained_object_net_names': all(before['objects'][k]['net'] == after['objects'].get(k, {}).get('net') for k in retained),
              'complete_retained_partitions_equal': not changed,
              'all_disturbed_nets_closed': all(closed.values()),
              'no_new_only_islands': not new_only_islands,
              'baseline_open_edge_count_equal': before['native_open_edges'] == after['native_open_edges']}
    return {'accepted_connectivity_only': all(checks.values()), 'checks': checks,
            'changed_retained_nets': changed, 'target_net_closed': closed,
            'new_only_islands': new_only_islands,
            'open_edges_before': before['native_open_edges'], 'open_edges_after': after['native_open_edges']}
