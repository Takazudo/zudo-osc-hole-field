"""One conditional C29534 50 -> 51 mm paper-model experiment; no substitution."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name('manifest.json')
GATE = 'design/stack/geometry/links/link-gate.json'
RATIOS = 'design/stack/link-electrical/link-ratios.json'
INPUTS = 'design/stack/link-electrical/inputs.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def verify_pins(root, manifest):
    for path, expected in manifest['sha256'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest() != expected:
            raise ValueError('source/model pin changed: '+path)


def override_lengths(links, identifiers):
    if len(identifiers) != len(set(identifiers)) or len(identifiers) != 28:
        raise ValueError('exactly 28 unique length overrides required')
    actual = {r['id'] for r in links if r['cable'] == 'C29534'}
    if actual != set(identifiers):
        raise ValueError('override set is not exactly selected C29534 links')
    changed = copy.deepcopy(links)
    for row in changed:
        if row['id'] in actual:
            if row['cable_length_mm'] != 50:
                raise ValueError('selected baseline length differs from 50 mm')
            row['cable_length_mm'] = 51.0
    check = copy.deepcopy(changed)
    for row in check:
        if row['id'] in actual:
            row['cable_length_mm'] = 50.0
    if check != links:
        raise ValueError('nonlength field changed')
    return changed


def pair_summary(kernel, inp, link, base):
    pairs, missing = kernel.link_pairs(inp, link, base)
    if missing:
        raise ValueError('missing pair reference: '+link['id'])
    largest = max(pairs, key=lambda r:r['ratio']) if pairs else None
    return {'id': link['id'], 'ratio': largest['ratio'] if largest else None,
            'largest_pair': largest, 'pairs_evaluated': len(pairs), 'pairs_without_reference': missing}


def check_baseline(kernel, rows, ground, retained, expected_nulls):
    expected = [{key:r[key] for key in ('id','ratio','largest_pair','pairs_evaluated','pairs_without_reference')}
                for r in retained['links']]
    if kernel.le.rnd(rows) != expected or kernel.le.rnd(ground) != retained['ground_share']:
        raise ValueError('baseline reproduction mismatch; variation forbidden')
    nulls = sorted(r['id'] for r in rows if r['ratio'] is None)
    if nulls != expected_nulls or len(nulls) != 5:
        raise ValueError('five intentional null links changed')


def experiment(kernel, inp, links, base, retained, manifest):
    original = digest(links)
    model = digest(inp)
    if len(links) != 61 or len({r['id'] for r in links}) != 61:
        raise ValueError('61 unique links required')
    baseline = [pair_summary(kernel, inp, link, base) for link in links]
    # All branches are recomputed over all 61 original links, not one link alone.
    ground_before = kernel.ground_share(inp, links)
    check_baseline(kernel, baseline, ground_before, retained, manifest['intentional_nulls'])
    variant = override_lengths(links, manifest['overrides'])
    changes = set(manifest['overrides'])
    rows = [pair_summary(kernel, inp, link, base) if link['id'] in changes else copy.deepcopy(old)
            for link, old in zip(variant, baseline)]
    # A changed path affects the alternative conductance seen by unchanged paths.
    ground_after = kernel.ground_share(inp, variant)
    if sorted(r['id'] for r in rows if r['ratio'] is None) != manifest['intentional_nulls']:
        raise ValueError('variation changed intentional null classification')
    if digest(inp) != model or digest(links) != original:
        raise ValueError('kernel mutated frozen input')
    return {'baseline_reproduction': 'MATCH', 'baseline_compared_fields':
            ['all61 directed-pair maxima, witness pairs and counts', 'mixed branch ground shares in all three post cases', 'five intentional nulls'],
            'overrides': [{'id': ident,'from_mm':50,'to_mm':51} for ident in manifest['overrides']],
            'baseline': {'links':baseline,'ground_share':ground_before},
            'length_51_only': {'links':rows,'ground_share':ground_after},
            'numeric_ratio_count':sum(r['ratio'] is not None for r in rows),
            'intentional_nulls':manifest['intentional_nulls'],
            'above_one': [r['id'] for r in rows if r['ratio'] is not None and r['ratio']>1],
            'maximum_ratio':max(r['ratio'] for r in rows if r['ratio'] is not None),
            'scope':'Conditional length-only paper sensitivity, same retained material/end/drive/impedance parameters; not a Molex or other cable qualification, routing, placement, hardware adoption, DRC/fill or manufacturing acceptance.'}


def run():
    manifest=json.loads(MANIFEST.read_text())
    verify_pins(ROOT,manifest)
    sys.path.insert(0,str(ROOT/'scripts/stack/link_electrical'))
    import link_ratios as kernel
    inp=kernel.le.load_inputs(ROOT/INPUTS)
    links=[r for r in json.loads((ROOT/GATE).read_text())['links'] if not r.get('gone')]
    if kernel.projection_sha256(links) != inp['link_record']['projection_sha256']:
        raise ValueError('retained model projection mismatch')
    # Exact existing adapter-aware baseline function; no new reference or table search.
    patterns=kernel.hb.harness_patterns(copy.deepcopy(inp)|{'classes':{'rules':kernel.d62.adapter_rules(inp)}},ROOT)
    base,_=kernel.hb.baseline(inp,patterns)
    result=experiment(kernel,inp,links,base,json.loads((ROOT/RATIOS).read_text()),manifest)
    verify_pins(ROOT,manifest)
    result['inputs_sha256']=manifest['sha256']
    result['engineering_commit']=manifest['engineering_commit']
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not args.output.resolve().is_relative_to((ROOT/'.circuit-cache').resolve()):
        parser.error('output must be in this worktree ignored cache')
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists; refusing to consume an attempt')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:
        try:result=run()
        except Exception as exc:
            json.dump({'status':'FAILED','error':str(exc)},stream)
            stream.write('\n')
            raise
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print('baseline matched; conditional experiment complete')


if __name__=='__main__':main()
