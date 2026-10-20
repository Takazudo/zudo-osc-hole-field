"""Stage55: render the Stage54 idle-quad removal onto a disposable osc-core board schematic.

Host-side source step. It reuses the Stage54 `prepare()` transform unchanged, projects
the candidate families through the canonical board projector with a filtered
assignment/floorplan, and writes only under `.circuit-cache/stage55/`. Canonical
schematic, partition, PCB and BOM files are never written.
"""
from pathlib import Path
import hashlib, importlib.util, json, re, shutil, sys, tempfile
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from scripts.schgen import project_boards as pb
from scripts.schgen.core import Family, Instance, LibrarySymbol, Part, render
from design.spec.cells._builder import load_symbol

BOARD = 'osc-core'
SHORT = 'K'
CACHE = ROOT/'.circuit-cache/stage55'


def load_stage54():
    path = ROOT/'design/architecture-278/implementation/stage54/power-cleanup/proposal.py'
    spec = importlib.util.spec_from_file_location('stage54_proposal', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok, msg):
    if not ok: raise ValueError(msg)


def filtered_partition(removed):
    partition = json.loads((ROOT/'design/partition/partition.json').read_text())
    floorplan = json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text())
    before = {x['ref'] for x in partition['assignment']['components']}
    require(removed <= before, 'removed reference missing from canonical assignment')
    require({x['board'] for x in partition['assignment']['components'] if x['ref'] in removed} == {SHORT}, 'removed refs not all on osc-core')
    partition['assignment']['components'] = [x for x in partition['assignment']['components'] if x['ref'] not in removed]
    floorplan['placements'] = [x for x in floorplan['placements'] if x['ref'] not in removed]
    return partition, floorplan


def board_render(families_override, partition, floorplan, transform=None):
    """Run the canonical projector for one board with injected inputs.

    `transform`, if given, maps the projected board families before rendering (Stage56).
    """
    original_spec, original_root = pb.specification, pb.ROOT
    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp); (fake/'design/partition').mkdir(parents=True)
        (fake/'design/partition/floorplan-candidate.json').write_text(json.dumps(floorplan))
        try:
            if families_override is not None:
                pb.specification = lambda: families_override
            pb.ROOT = fake
            partition, _, _, short_to_id, families, instances, canon = pb.project(partition)
        finally:
            pb.specification, pb.ROOT = original_spec, original_root
    # Mirrors scripts/schgen/project_boards.py main() for the one board, without writes.
    symbols = {}
    for fs in families.values():
        for f in fs:
            for p in f.parts:
                if p.symbol in symbols: continue
                key = p.symbol.split(':', 1)[1]
                symbols[p.symbol] = (LibrarySymbol.from_fixture(p.symbol, ROOT/'scripts/schgen/fixtures'/f'{key}.kicad_sympart')
                                     if key in pb.FIXTURES else load_symbol(key))
    for key in ('JST_GH3_BM', 'JST_GH7_BM', 'JST_GH8_BM', 'TestPoint'):
        symbols[f'zudo-osc-hole-field:{key}'] = load_symbol(key)
    symbols['Fixture:PWR_FLAG'] = LibrarySymbol.from_fixture('Fixture:PWR_FLAG', ROOT/'scripts/schgen/fixtures/PWR_FLAG.kicad_sympart')
    board_id = short_to_id[SHORT]; require(board_id == BOARD, 'board id')
    board_families = list(families[board_id]) if transform is None else list(transform(families[board_id]))
    fs = [*board_families, pb.interface_family(SHORT, partition, canon)]
    ins = [*instances[board_id], Instance(fs[-1].name, f'INTERFACES_{SHORT}', 999)]
    power_nets = set()
    for family in fs:
        for part in family.parts:
            for pin in symbols[part.symbol].units[part.unit]:
                if pin.electrical == 'power_in' and part.pins.get(pin.number):
                    power_nets.add(part.pins[pin.number])
    flags = [Part(key=f'PWR{i}', symbol='Fixture:PWR_FLAG', prefix='PWR', ordinal=i, unit=0,
                  x=35+(i % 3)*65, y=40+((i//3) % 8)*30, page=1+i//24, pins={'1': net},
                  panel_ref=f'#PWR{i}', in_bom=False, on_board=False)
             for i, net in enumerate(sorted(power_nets), 1)]
    if flags:
        ff = Family(f'board_power_flags_{SHORT}', tuple(flags), tuple(sorted(power_nets)), (), 'A0')
        fs.append(ff); ins.append(Instance(ff.name, f'POWER_FLAGS_{SHORT}', 998))
    return render(tuple(fs), tuple(ins), symbols, board_id), canon


UNIT_FIELDS = ('Role', 'LogicalCellKey', 'Island')


def unit_field_conflicts(tree):
    """{field: {ref: unit values}} for placed symbols whose units disagree on a unit-specific field."""
    values = {}
    for body in tree.values():
        for block in body.split('\n  (symbol (lib_id')[1:]:
            ref = re.search(r'"Reference" "([^"]+)"', block)
            if not ref:
                continue
            for field in UNIT_FIELDS:
                m = re.search(rf'"{field}" "([^"]*)"', block)
                values.setdefault((field, ref.group(1)), set()).add(m.group(1) if m else '')
    out = {}
    for (field, ref), seen in values.items():
        if len(seen) > 1:
            out.setdefault(field, {})[ref] = sorted(seen)
    return {f: dict(sorted(r.items())) for f, r in sorted(out.items())}


def write_tree(target, generated):
    target.mkdir(parents=True)
    for name, body in generated.items():
        p = target/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(body)
    src = ROOT/'boards'/BOARD
    for name in ('sym-lib-table', 'fp-lib-table'):
        (target/name).write_text((src/name).read_text().replace('${KIPRJMOD}/../../', '${KIPRJMOD}/../../../../'))
    for name in (f'{BOARD}.kicad_pro', f'{BOARD}.kicad_dru'):
        shutil.copyfile(src/name, target/name)


def compute():
    """Return (baseline, candidate, receipt) in memory; raises on any binding failure."""
    s54 = load_stage54()
    families, instances = s54.specification()
    new_families, proposal = s54.prepare(families, instances)
    removed = set(proposal['removed_refs']); require(len(removed) == 36, 'removed roster')
    partition = json.loads((ROOT/'design/partition/partition.json').read_text())
    floorplan = json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text())
    baseline, canon = board_render(None, partition, floorplan)
    # The unfiltered projector must reproduce every committed board schematic byte.
    for name, body in baseline.items():
        require((ROOT/'boards'/BOARD/name).read_text() == body, 'canonical board generator drift '+name)
    fpart, ffloor = filtered_partition(removed)
    candidate, canon_after = board_render((new_families, instances), fpart, ffloor)
    require(set(candidate) == set(baseline), 'board schematic file roster changed')
    changed = sorted(n for n in baseline if baseline[n] != candidate[n])
    removed_tokens = sorted(set(canon) - set(canon_after))
    refs_in = lambda tree: {r for r in removed if any(f'"Reference" "{r}"' in body for body in tree.values())}
    require(refs_in(baseline) == removed and not refs_in(candidate), 'removed references not exactly dropped')
    require(len(removed_tokens) == 48, 'removed board-net roster')
    receipt = {
        'multi_unit_field_conflicts': {'baseline': unit_field_conflicts(baseline), 'candidate': unit_field_conflicts(candidate),
                                       'meaning': ('References whose symbol units carry different values of a field. KiCad '
                                                   'parity compares a footprint with one unit, so these are ambiguous.')},
        'status': 'DISPOSABLE candidate board schematic only; canonical files unchanged',
        'stage54_proposal_sha256': sha(ROOT/'design/architecture-278/implementation/stage54/power-cleanup/proposal.json'),
        'removed_refs': sorted(removed),
        'removed_board_net_tokens': removed_tokens,
        'changed_board_schematic_files': changed,
        'baseline_matches_committed_board_schematic': True,
        'candidate_schematic_sha256': {n: hashlib.sha256(b.encode()).hexdigest() for n, b in sorted(candidate.items()) if n in changed},
    }
    return baseline, candidate, receipt


def run():
    require(not CACHE.exists(), 'fresh .circuit-cache/stage55 required')
    baseline, candidate, receipt = compute()
    write_tree(CACHE/'baseline'/BOARD, baseline)
    write_tree(CACHE/'candidate'/BOARD, candidate)
    (CACHE/'schematic-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(f"PASS candidate osc-core board schematic: {len(receipt['changed_board_schematic_files'])} sheet(s) changed, "
          f"{len(receipt['removed_board_net_tokens'])} board nets removed")
    return receipt


if __name__ == '__main__':
    run()
