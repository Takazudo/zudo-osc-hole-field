#!/usr/bin/env python3
"""Check custom minimum-box persistence with the pinned native KiCad oracle."""
import re
import sys
import tempfile
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.checks.test_courtyard_minimum import fixture
from scripts.libgen.gen_courtyards import parse, walk, node_name, rewrite


def main():
    if not re.match(r'^10\.0\.6(?:[-+ ]|$)', pcbnew.GetBuildVersion()):
        raise RuntimeError('KiCad 10.0.6 required')
    cache = ROOT/'.circuit-cache/fixtures'
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='courtyard-minimum-', dir=cache) as temp:
        directory = Path(temp)
        (directory/'MinimumBoxFixture.kicad_mod').write_text(
            rewrite(fixture('-2.001 -1.009 2.009 1.001')))
        footprint = pcbnew.FootprintLoad(str(directory), 'MinimumBoxFixture')
        if footprint is None:
            raise RuntimeError('native load failed')
        board = pcbnew.BOARD()
        board.Add(footprint)
        output = directory/'roundtrip.kicad_pcb'
        pcbnew.SaveBoard(str(output), board)
        props = [node for node in walk(parse(output.read_text()))
                 if node_name(node) == 'property' and len(node) > 2
                 and node[1] == 'ProjectCourtyardMinimumBox']
        if len(props) != 1 or props[0][2] != '-2.001 -1.009 2.009 1.001':
            raise AssertionError('native roundtrip lost the source minimum')
        restored = pcbnew.LoadBoard(str(output))
        items = list(restored.GetFootprints())
        if len(items) != 1:
            raise AssertionError('roundtrip footprint count changed')
        points = []
        for graphic in items[0].GraphicalItems():
            if graphic.GetLayer() != pcbnew.F_CrtYd:
                continue
            points.extend((graphic.GetStart(), graphic.GetEnd()))
        actual = (min(pcbnew.ToMM(p.x) for p in points), min(pcbnew.ToMM(p.y) for p in points),
                  max(pcbnew.ToMM(p.x) for p in points), max(pcbnew.ToMM(p.y) for p in points))
        if actual != (-2.01, -1.01, 2.01, 1.01):
            raise AssertionError('native courtyard differs: '+repr(actual))
    print('PASS: native minimum-box property and outward courtyard survive save/reload; physical fit NOT RUN')


if __name__ == '__main__':
    main()
