"""Bounded additive routing: 24 B1 private nets and three baseline-closed rails."""
from pathlib import Path
import argparse
import json
import sys
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.grid_router import route, copper_rows


def propose(dump_path, receipt_path, output, resolution=.075, priority_net=None):
    dump = json.loads(dump_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    # Baseline rail partitions are complete. Only moved B1 pads may add opens;
    # full native partition comparison must prove every foreign member stays.
    nets = set(receipt['private_net_owners']) | {'+12V', '-12V', '+5V'}
    # Short local links first, then complete paths to retained package/jack pads.
    def span(net):
        points = [p['xy'] for p in dump['pads'] if p['net'] == net]
        return sum(max(p[i] for p in points)-min(p[i] for p in points) for i in (0, 1))
    nets = sorted(nets, key=lambda n: (span(n), n))
    if priority_net:
        if priority_net not in nets: raise ValueError('priority net outside explicit scope')
        nets.remove(priority_net); nets.insert(0, priority_net)
    results, removed = route(
        dump, nets, res=resolution, signal_width=.2, clearance=.25,
        allowed_layers=['F.Cu', 'In2.Cu', 'B.Cu'], rail_nets=['+12V', '-12V', '+5V'],
        grow={'+12V': .05, '-12V': .05, '+5V': .05}, via_diameter=.7, via_drill=.3,
        max_expansions=1000000, bounds_mm=[106.5, 168, 139, 213.5], window_mm=12,
        fill_guards={'-12V': 'In3.Cu'}, log=lambda s: print(s, flush=True))
    if removed:
        raise ValueError('additive pilot unexpectedly ripped copper')
    rows, links = copper_rows(results, 'osc-jack-left', 'stage42-full-b1')
    proposal = {'board_sha256': dump['board_sha256'], 'removed_uuids': [], 'copper': rows}
    output.write_text(json.dumps(proposal, indent=2) + '\n')
    result = {'scope_nets': nets, 'priority_net': priority_net, 'resolution_mm': resolution, 'bounds_mm': [106.5, 168, 139, 213.5],
              'allowed_layers': ['F.Cu', 'In2.Cu', 'B.Cu'], 'results': results, 'links': links,
              'new_objects': len(rows), 'failed_links': sum(not r['path'] for r in results),
              'status': 'ROUTE PROPOSAL ONLY; native gates mandatory'}
    output.with_name(output.stem + '-search.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'objects': len(rows), 'links': len(results), 'failed': result['failed_links']}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('dump', type=Path); p.add_argument('receipt', type=Path)
    p.add_argument('output', type=Path); p.add_argument('--resolution', type=float, default=.075)
    p.add_argument('--priority-net')
    a = p.parse_args(); propose(a.dump, a.receipt, a.output, a.resolution, a.priority_net)
