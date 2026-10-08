"""Copper evidence must not collapse pre-existing duplicate UUIDs."""
import collections,json


def reject_new_uuid_collisions(existing,rows):
    seen=set(existing)
    for row in rows:
        uid=row['uuid']
        if uid in seen:raise ValueError('new copper UUID collides with surviving geometry: '+uid)
        seen.add(uid)


def retention(before,after):
    old=[i for kind in ('tracks','vias') for i in before[kind]]
    new=[i for kind in ('tracks','vias') for i in after[kind]]
    def geometry(items):return collections.Counter(json.dumps(i,sort_keys=True,separators=(',',':')) for i in items)
    a,b=geometry(old),geometry(new)
    old_ids=collections.Counter(i['uuid'] for i in old);new_ids=collections.Counter(i['uuid'] for i in new)
    old_groups=collections.defaultdict(list);new_groups=collections.defaultdict(list)
    for i in old:old_groups[i['uuid']].append(i)
    for i in new:new_groups[i['uuid']].append(i)
    return {'counting':'multiset of full object geometry and UUID; duplicate IDs are not collapsed',
        'before':len(old),'after':len(new),'identical':sum((a&b).values()),
        'removed_objects':sum((a-b).values()),'added_objects':sum((b-a).values()),
        'before_unique_uuids':len(old_ids),'after_unique_uuids':len(new_ids),
        'duplicate_uuids_before':{u:n for u,n in old_ids.items() if n>1},
        'duplicate_uuids_after':{u:n for u,n in new_ids.items() if n>1},
        'removed_uuids':sorted(old_ids.keys()-new_ids.keys()),'added_uuids':sorted(new_ids.keys()-old_ids.keys()),
        'changed_existing_uuids':sorted(u for u in old_ids.keys()&new_ids.keys() if geometry(old_groups[u])!=geometry(new_groups[u]))}
