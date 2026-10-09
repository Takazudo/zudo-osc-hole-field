"""Hold whole signal cases away from observed split regions; native test still required."""
import hashlib,json
from pathlib import Path
here=Path(__file__).parent;prior=here.parent/'core-short-no-via'
source=prior/'proposal.json';data=json.loads(source.read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()=='c3d1a8691b41b374690dcbb21d35f612c9275783a1fcd390c1daadbf26ae5ef2'
assert not data['removed_uuids'] and len(data['copper'])==19
proximity=json.loads((prior/'split-proximity.json').read_text())
excluded={p['nearest_three_transactions'][0]['net'] for p in proximity['split_pads']}
assert excluded=={'X0C6D5F78E32943DCB854','X069AA41BCE4A36C26FB2','XEB3ADF3D5A9AB1D27287'}
rows=[r for r in data['copper'] if r['net'] not in excluded]
assert len(rows)==13 and len({r['net'] for r in rows})==8
assert all(r['kind']=='segment' and r['layer'] in ('F.Cu','B.Cu') for r in rows)
selection=json.loads((prior/'selection.json').read_text())['selected']
assert len({r['net'] for r in selection})==11
proposal={**data,'copper':rows}
(here/'proposal-original.json').write_text(json.dumps(proposal,indent=2)+'\n')
(here/'selection.json').write_text(json.dumps(dict(status='HELD HYPOTHESIS ONLY; NO NATIVE RUN OR ACCEPTANCE; REBASE AFTER CURRENT GROUND WORK',source_proposal_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_board_sha256=data['board_sha256'],proposal_sha256=hashlib.sha256((here/'proposal-original.json').read_bytes()).hexdigest(),retained_whole_cases=[r for r in selection if r['net'] not in excluded],excluded_whole_cases=[r for r in selection if r['net'] in excluded],basis='Omit the unique closest new signal transaction to each observed split region. Proximity is not causality. All nearest gaps exceed3mm, so the prior3mm heuristic would miss these splits.',removed_accepted_copper=0,added_segments=13,added_vias=0),indent=2)+'\n')
print('Held8whole signal cases/13segments; no native run or adoption')
