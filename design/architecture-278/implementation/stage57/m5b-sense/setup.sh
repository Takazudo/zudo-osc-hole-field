#!/bin/bash
# Stage57 disposable copies: two empty project folders beside the Stage53 baseline.
# Writes only under .circuit-cache/. Fails if the baseline board or snapshot drifted.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
C=.circuit-cache; B=$C/stage53-fresh
ck(){ [[ $(sha256sum "$1" | cut -d' ' -f1) == "$2" ]] || { echo "FAIL hash $1"; exit 3; }; }
ck $B/osc-jack-left.kicad_pcb 27d2214492f9dd88483be014df4197fdb936cbbc7c445f17c8178cce97126560
ck $B/connectivity-passfresh.json 21e305061046e7bdf79baa67cd7ddfa31adc2e2db6d00c7a6203173911a3a6e0
for d in stage57-pass1 stage57-fresh; do
  [[ -e $C/$d ]] && { echo "FAIL $C/$d exists; remove it first"; exit 4; }
  python3 - "$B" "$C/$d" <<'PY'
import shutil,sys
from pathlib import Path
s,d=Path(sys.argv[1]),Path(sys.argv[2]);d.mkdir()
for p in s.iterdir():
    if p.name=='sheets':shutil.copytree(p,d/p.name)
    elif p.suffix in ('.kicad_pro','.kicad_sch','.kicad_dru') or p.name in ('receipt.json','prepare-receipt.json','fp-lib-table','sym-lib-table'):shutil.copy2(p,d/p.name)
PY
  echo "READY $C/$d"
done
