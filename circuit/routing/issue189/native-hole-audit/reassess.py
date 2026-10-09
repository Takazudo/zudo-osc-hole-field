"""Reassess saved core candidate using complete native observations; never promote."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.complete_native_warnings import complete_reports
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
native=Path('.circuit-cache/issue189-downloaded/core-finer-ground-batch/.circuit-cache');holes=Path('.circuit-cache/issue189-downloaded/native-hole-context');masks=Path('.circuit-cache/issue189-downloaded/native-all-copper-silk');zones=Path('.circuit-cache/issue189-downloaded/native-zone-classification');out=Path(__file__).parent
before=native/'osc-core-grid-shards-start';after=native/'osc-core-grid-shards-merge';fresh=native/'osc-core-grid-shards-fresh'
read=lambda p:json.loads(p.read_text())
a,b=read(before/'dump.json'),read(after/'dump.json');bd,ad=read(before/'drc.json'),read(after/'drc.json')
raw=promotion_gate(a,b,bd,ad);assert not raw['adopted']
full_before,full_after,proof=complete_reports(before/'osc-core.kicad_pcb',after/'osc-core.kicad_pcb',bd,ad,holes/'hole-audit-start',holes/'hole-audit-merge',masks,zones)
gate=promotion_gate(a,b,full_before,full_after);agreement=connectivity_signature(b)==connectivity_signature(read(fresh/'dump.json'));assert agreement and gate['adopted'];assert hashlib.sha256((fresh/'osc-core.kicad_pcb').read_bytes()).hexdigest()==b['board_sha256']
result=dict(status='ELIGIBLE WITH COMPLETE NATIVE EVIDENCE; CANONICAL BOARD NOT CHANGED',raw_gate=raw,complete_gate=gate,evidence=proof,native_edges_before=a['open_edges'],native_edges_after=b['open_edges'],fresh_native_agreement=agreement)
(out/'reassessment.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
