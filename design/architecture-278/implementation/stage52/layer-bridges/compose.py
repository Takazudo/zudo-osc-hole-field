"""Compose the two explicit local F/In2/B bridges against the Stage49 baseline."""
from pathlib import Path
import json,sys,uuid,copy
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
NET='XED7C19D453619667580D'
def segment(name,a,b):return {'kind':'segment','uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'stage52/compose/'+name)),'net':NET,'layer':'In3.Cu','start_nm':[round(v*1e6) for v in a],'end_nm':[round(v*1e6) for v in b],'width_nm':200000}
def run(lower,upper):
 p=json.loads((ROOT/'design/architecture-278/implementation/stage51/f3-sense/proposal.json').read_text());old=p['copper'];lo=json.loads(lower.read_text());up=json.loads(upper.read_text())
 if lo['board_sha256']!=p['board_sha256'] or up['board_sha256']!=p['board_sha256'] or lo['removed_uuids'] or up['removed_uuids']:raise ValueError('baseline/rip')
 if not any(r['kind']=='segment' for r in lo['copper']) or not any(r['kind']=='segment' for r in up['copper']):raise ValueError('failed bridge')
 rows=old[:11]+[segment('lower-approach',[229.1,109.1],[227.948045,109.1]),segment('lower-spoke',[227.948045,109.1],[227.948045,109.291186])]+lo['copper']+[segment('middle',[234.888909,104.511091],[235.4,104])]+old[23:25]+[segment('upper-spoke',[236,102.7],[234.885993,102.753381])]+up['copper']+[segment('upper-return',[235.122861,99.590073],[236,99.590073]),segment('upper-tail',[236,99.590073],[236,96.4])]+old[26:]
 if len({r['uuid'] for r in rows})!=len(rows):raise ValueError('duplicate additions')
 return {**p,'copper':rows}
if __name__=='__main__':Path(sys.argv[3]).write_text(json.dumps(run(Path(sys.argv[1]),Path(sys.argv[2])),indent=2,sort_keys=True)+'\n')
