"""Reconcile a SHA-verified disposable native pilot; never adopt its result."""
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups
from scripts.pcbgen.route_jack_grid import connectivity_signature, promotion_gate
from scripts.pcbgen.uuid_tools import top_level_spans
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata

HERE = Path(__file__).resolve().parent
ROOT = Path('.circuit-cache/issue189-downloaded/jr-rb4413-edge-bridge')
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def physical(text):
    rows = []
    for a, b in top_level_spans(text):
        block = text[a:b]
        if block.startswith(('(segment', '(via', '(zone')):
            continue
        if block.startswith('(footprint') and re.search(r'\(property "Reference" "RB4413"', block):
            # Only the reviewed footprint's absolute origin may differ.
            block = re.sub(r'\(at [^)]*\)', '(at REVIEWED_ORIGIN)', block, count=1)
        rows.append(block)
    return collections.Counter(rows)


def main():
    meta = read(HERE / 'download.json')
    assert sha(Path(meta['zip_path'])) == meta['zip_sha256']
    plan = read(HERE / 'plan.json')
    cache = ROOT / '.circuit-cache' if (ROOT / '.circuit-cache').is_dir() else ROOT
    pilot = read(cache / 'issue189-rb4413-move/result.json')
    assert pilot['plan_sha256'] == sha(HERE / 'plan.json')
    assert pilot['adopted'] is False and pilot['source_regenerated'] is False
    paths = {s: cache / ('osc-jack-right-grid-189-jr-rb4413-' + s)
             for s in ('base', 'candidate', 'fresh')}
    dumps = {s: read(p / 'dump.json') for s, p in paths.items()}
    drc = {s: read(p / 'drc.json') for s, p in paths.items()}
    texts = {s: (p / 'osc-jack-right.kicad_pcb').read_text() for s, p in paths.items()}
    copper = {s: collections.Counter(b for rows in copper_block_groups(t).values() for b in rows)
              for s, t in texts.items()}
    expected_pads = copy.deepcopy(dumps['base']['pads'])
    for pad in expected_pads:
        if pad['ref'] == plan['ref']:
            pad['xy'] = [a+b for a, b in zip(pad['xy'], plan['translation_nm'])]
            pad['poly'] = [[a+b for a, b in zip(v, plan['translation_nm'])] for v in pad['poly']]
    assert sha(paths['candidate'] / 'osc-jack-right.kicad_pcb') == pilot['candidate_sha256']
    assert sha(paths['fresh'] / 'osc-jack-right.kicad_pcb') == pilot['fresh_sha256']
    assert sha(cache / 'issue189-rb4413-move/moved-copper.json') == pilot['proposal_sha256']
    gates = {}
    for stage in ('candidate', 'fresh'):
        assert dumps[stage]['pads'] == expected_pads
        for key in ('edges', 'keepouts', 'layers'):
            assert dumps[stage][key] == dumps['base'][key]
        assert physical(texts[stage]) == physical(texts['base'])
        assert zone_metadata(texts[stage]) == zone_metadata(texts['base'])
        assert not copper['base'] - copper[stage]
        assert sum(copper['base'].values()) == 51177
        assert sum((copper[stage] - copper['base']).values()) == 8
        gates[stage] = promotion_gate(dumps['base'], dumps[stage], drc['base'], drc[stage])
    assert copper['candidate'] == copper['fresh']
    for suffix in ('.kicad_pro', '.kicad_dru'):
        assert len({(p / ('osc-jack-right' + suffix)).read_bytes() for p in paths.values()}) == 1
    receipt = dict(status='DISPOSABLE NATIVE EVIDENCE RECONCILED; NOT ADOPTED',
                   source_regenerated=False, adopted=False, download=meta,
                   board_sha256={s: sha(p / 'osc-jack-right.kicad_pcb') for s, p in paths.items()},
                   open_edges={s: d['open_edges'] for s, d in dumps.items()}, gates=gates,
                   retained_original_objects=51177, added_objects=8, removed_objects=0,
                   reviewed_translation_nm=plan['translation_nm'], other_physical_geometry_unchanged=True,
                   fresh_agreement=connectivity_signature(dumps['candidate']) == connectivity_signature(dumps['fresh']),
                   drc_errors={s: sum(v['severity']=='error' for v in d['violations']) for s, d in drc.items()},
                   parity={s: len(d['schematic_parity']) for s, d in drc.items()})
    (HERE / 'native-result.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
