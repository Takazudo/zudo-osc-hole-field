#!/usr/bin/env bash
set -euo pipefail
native=design/architecture-278/implementation/stage36/gh4-coupon-native
out="$native/review-only"
mkdir -p "$out"
cli() { bash scripts/kicad/run.sh kicad-cli "$@"; }
cli sch export netlist --format kicadxml --output "$out/netlist.xml" "$native/gh4-coupon.kicad_sch"
cli sch export svg --output "$out/schematic/" "$native/gh4-coupon.kicad_sch"
cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts,Dwgs.User --output "$out/gerbers/" "$native/gh4-coupon.kicad_pcb"
cli pcb export drill --format excellon --excellon-units mm --drill-origin absolute --excellon-separate-th --generate-map --map-format svg --generate-report --report-path "$out/drill-report.txt" --output "$out/drill/" "$native/gh4-coupon.kicad_pcb"
cli pcb export pos --format csv --units mm --side front --output "$out/placement-native.csv" "$native/gh4-coupon.kicad_pcb"
cli pcb export svg --layers F.Cu,F.Silkscreen,Edge.Cuts,Dwgs.User --mode-single --fit-page-to-board --exclude-drawing-sheet --output "$out/board-top.svg" "$native/gh4-coupon.kicad_pcb"
cli pcb export svg --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts,Dwgs.User --mode-multi --fit-page-to-board --exclude-drawing-sheet --output "$out/layers/" "$native/gh4-coupon.kicad_pcb"
