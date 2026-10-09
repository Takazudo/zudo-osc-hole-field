"""Compare native fixture identities; produce evidence, never authorize adoption."""
import json
from pathlib import Path
import sys


def identities(rows):
    return {(kind,severity,tuple(ids)) for kind,severity,ids in rows}


def compare(before, after, before_drc, after_drc):
    for key in ('version','project_sha256','rules_sha256','clearance_nm'):
        if before[key] != after[key]:
            raise ValueError('audit contexts differ: '+key)
    old, new = identities(before['identities']), identities(after['identities'])
    for audit, drc in [(old,before_drc),(new,after_drc)]:
        reported={(v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items'])))
                  for v in drc['violations'] if v['type'] in ('hole_to_hole','holes_co_located')}
        if not reported <= audit:
            raise ValueError('fixture audit omitted original native report identities: '+repr(reported-audit))
    old_objects,new_objects=identities(before['object_identities']),identities(after['object_identities'])
    return dict(new_object_identities=sorted(new_objects-old_objects),removed_object_identities=sorted(old_objects-new_objects),before_object_identity_count=len(old_objects),after_object_identity_count=len(new_objects),status='NATIVE FIXTURE COMPARISON ONLY; PROMOTION GATE UNCHANGED',
                before_count=len(old),after_count=len(new),new_identities=sorted(new-old),
                removed_identities=sorted(old-new),full_board_report_identities_covered=True,
                before_source_sha256=before['source_sha256'],after_source_sha256=after['source_sha256'])


if __name__=='__main__':
    result=compare(*(json.loads(Path(p).read_text()) for p in sys.argv[1:5]))
    Path(sys.argv[5]).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
