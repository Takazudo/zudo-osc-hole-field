"""Tiny native negative-control fixture through existing exact local admission.

Preparation/source tests never import pcbnew. Worker and native phases both
recheck the request/approval; native startup also verifies the existing guard's
read-only acknowledgement and actual resource caps before importing pcbnew.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path
import re

LAYERS = ('F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu')
DEFAULT = 'e16a0000-0000-4000-8000-000000000001'
CUSTOM = 'e16a0000-0000-4000-8000-000000000002'
IDS = {f'e16a0000-0000-4000-8000-{i:012d}' for i in range(1, 7)}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def characterize(pcbnew, fixture, fresh_output):
    """For a future admitted worker ONLY; snapshots must match after native reload.

The custom .35 mm land is a NEGATIVE CONTROL, never accepted as omitted annulus.
No zone fill, DRC completeness, production candidate or fabrication output here.
"""
    need(re.match(r'^10\.0\.6(?:$|[^0-9])', str(pcbnew.GetBuildVersion())),
         'exact KiCad 10.0.6 required')
    fixture, fresh_output = Path(fixture), Path(fresh_output)
    need(not fresh_output.exists(), 'fresh native output required')
    before = fixture.read_bytes()
    need({x.decode() for x in re.findall(rb'\(uuid\s+"([^"]+)"\)', before)} == IDS,
         'unexpected input identities')
    need(not any(x in before for x in (b'remove_unused_layers', b'keep_end_layers',
                                     b'zone_layer_connections', b'start_end_only')),
         'global removal or transient override is not the exact policy')

    def snapshot_inner(board):
        need(board is not None, 'native load failed')
        board.GetConnectivity().RecalculateRatsnest()
        tracks = list(board.GetTracks())
        need(len(tracks) == 5, 'fixture track/via inventory changed')
        vias = {v.m_Uuid.AsString(): v for v in tracks if v.Type() == pcbnew.PCB_VIA_T}
        need(set(vias) == {DEFAULT, CUSTOM}, 'native via UUIDs changed')
        rows = {}
        for ident, via in vias.items():
            need(hasattr(via, 'FlashLayer'), 'UNSUPPORTED_NATIVE_API: FlashLayer unavailable')
            need(via.GetDrillValue() == 300000, 'native through drill changed')
            need(via.GetNetname() == 'AGND', 'native net changed')
            need(via.TopLayer() == board.GetLayerID('F.Cu')
                 and via.BottomLayer() == board.GetLayerID('B.Cu'), 'through span changed')
            sizes, flashed = {}, {}
            for name in LAYERS:
                layer = board.GetLayerID(name)
                need(layer >= 0, 'fixture layer unavailable')
                sizes[name] = via.GetWidth(layer)
                flashed[name] = bool(via.FlashLayer(layer))
                expected = 350000 if ident == CUSTOM and name == 'In3.Cu' else 600000
                need(sizes[name] == expected, 'native diameter changed')
                need(flashed[name], 'unexpected no-flash: negative control changed semantics')
            position = via.GetPosition()
            xy = [position.x, position.y]
            need(xy == ([5000000, 5000000] if ident == DEFAULT else [10000000, 5000000]),
                 'native center changed')
            rows[ident] = {'width_nm': sizes, 'flashed': flashed, 'drill_nm': 300000,
                           'net': 'AGND', 'center_nm': xy}
        segments = {}
        for item in tracks:
            ident = item.m_Uuid.AsString()
            if ident in vias:
                continue
            a, b = item.GetStart(), item.GetEnd()
            segments[ident] = {'start_nm': [a.x, a.y], 'end_nm': [b.x, b.y],
                               'width_nm': item.GetWidth(), 'layer': board.GetLayerName(item.GetLayer()),
                               'net': item.GetNetname()}
        expected_segments = {f'e16a0000-0000-4000-8000-{i:012d}': {
            'start_nm': [5000000, 5000000], 'end_nm': [10000000, 5000000],
            'width_nm': 250000, 'layer': layer, 'net': 'AGND'}
            for i, layer in zip((3, 4, 5), ('F.Cu', 'In1.Cu', 'B.Cu'))}
        need(segments == expected_segments, 'native functional track geometry/net/layer changed')
        drawings = list(board.GetDrawings())
        need(len(drawings) == 1, 'native owner artwork inventory changed')
        drawing = drawings[0]
        a, b = drawing.GetStart(), drawing.GetEnd()
        artwork = {'uuid': drawing.m_Uuid.AsString(), 'start_nm': [a.x, a.y],
                   'end_nm': [b.x, b.y], 'width_nm': drawing.GetWidth(),
                   'layer': board.GetLayerName(drawing.GetLayer()), 'shape': int(drawing.GetShape())}
        need(artwork['uuid'] == 'e16a0000-0000-4000-8000-000000000006'
             and artwork['start_nm'] == [0, 0] and artwork['end_nm'] == [15000000, 10000000]
             and artwork['width_nm'] == 50000 and artwork['layer'] == 'Edge.Cuts',
             'native owner artwork geometry changed')
        return {'vias': rows, 'functional_tracks': segments, 'owner_artwork': artwork}

    def snapshot(board):
        try:
            return snapshot_inner(board)
        except (AttributeError, TypeError) as error:
            raise ValueError('UNSUPPORTED_NATIVE_API: pinned fixture binding unavailable: ' + str(error)) from error

    board = pcbnew.LoadBoard(str(fixture))
    initial = snapshot(board)
    pcbnew.SaveBoard(str(fresh_output), board)
    need(fresh_output.is_file(), 'native serialization produced no output')
    saved = fresh_output.read_bytes()
    need({x.decode() for x in re.findall(rb'\(uuid\s+"([^"]+)"\)', saved)} == IDS,
         'roundtrip object identities changed')
    need(fixture.read_bytes() == before, 'native changed immutable input')
    reloaded = snapshot(pcbnew.LoadBoard(str(fresh_output)))
    need(initial == reloaded, 'native reload changed via semantics')
    return {'schema': 'e16-annulus-native-negative-control-v1',
            'input_sha256': hashlib.sha256(before).hexdigest(),
            'output_sha256': hashlib.sha256(saved).hexdigest(), 'snapshots': reloaded,
            'characterization': 'CUSTOM_DIAMETER_REMAINS_FLASHED; NOT_EXACT_ANNULUS_REMOVAL',
            'native_acceptance': 'NOT_ESTABLISHED', 'adopted': False,
            'drc': 'NOT RUN', 'refill': 'NOT RUN: fixture has no zones'}


ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'circuit/WORKFLOW.md').is_file())
SCRIPT = str(Path(__file__).resolve().relative_to(ROOT))
FIXTURE = Path(__file__).with_name('native-negative-control.kicad_pcb')
GUARD_KEYS = ('EPIC242_NATIVE_WORKER', 'EPIC242_NATIVE_SLICE', 'EPIC242_NATIVE_DEADLINE')


def local_admission():
    spec = importlib.util.spec_from_file_location('annulus_local_admission',
                                                ROOT / 'scripts/kicad/local_native_admission.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def context(env, output, *, host):
    local = local_admission()
    request = local.authority(ROOT, env, host=host)
    need(request['kind'] == 'annulus-fixture' and request['target'] == 'annulus',
         'exact annulus fixture authority required')
    need(request['seconds'] == 60, 'exact fixture deadline required')
    expected = request['evidence'] + '.annulus'
    need(output == expected, 'fixture output differs from request')
    destination = local.local_path(ROOT, output, cache=True)
    need(request['command'] == ['python3', SCRIPT, 'worker', '--output', output],
         'fixture command binding differs')
    worker = request['worker']
    need(env.get('EPIC242_NATIVE_WORKER') == worker and
         env.get('EPIC242_NATIVE_SLICE') == 'epic242-w' + worker.encode().hex() + '.slice',
         'fixture worker/slice differs')
    deadline = env.get('EPIC242_NATIVE_DEADLINE', '')
    need(re.fullmatch(r'[0-9]{10}', deadline) and 0 < int(deadline) - time.time() <= 60,
         'fixture deadline expired or exceeds request')
    return local, request, destination


def native_command(env, local, output):
    return ['env'] + [key + '=' + env[key] for key in (*GUARD_KEYS, *local.AUTHORITY_KEYS)] + [
        'python3', SCRIPT, 'native', '--output', output]


def verify_host_resources(env, proc=Path('/proc/self/cgroup'), cgroup=Path('/sys/fs/cgroup')):
    worker, slice_name = env['EPIC242_NATIVE_WORKER'], env['EPIC242_NATIVE_SLICE']
    need(proc.read_text().strip() == '0::/epic242.slice/' + slice_name +
         '/epic242-' + worker + '-checks.service', 'fixture outside actual host checks service')
    for path, cap in ((cgroup / 'epic242.slice', 12884901888),
                      (cgroup / 'epic242.slice' / slice_name, 6442450944)):
        need((path / 'memory.max').read_text().strip() == str(cap) and
             (path / 'memory.swap.max').read_text().strip() == '0', 'fixture host caps differ')


def verify_native_gate(env, expected, gate=Path('/epic242-gate'),
                       mountinfo=Path('/proc/self/mountinfo'), cgroup=Path('/sys/fs/cgroup')):
    mounts = {parts[4]: parts[5].split(',') for line in mountinfo.read_text().splitlines()
              if len(parts := line.split()) > 5}
    need(all('ro' in mounts.get(path, []) for path in ('/epic242-gate', '/epic242-start.sh')),
         'fixture requires actual read-only startup gate')
    record = json.loads((gate / 'request.json').read_text())
    cid = (gate / 'container-id').read_text().strip()
    token = record.get('token', '')
    need(re.fullmatch(r'[0-9a-f]{64}', cid) and re.fullmatch(r'gate\.[a-zA-Z0-9]{12}', token),
         'fixture native gate identity invalid')
    need((gate / 'ack').read_text() == token + ':' + cid + '\n', 'fixture guard acknowledgement differs')
    image = re.search(r"^KICAD_IMAGE='([^']+)'$", (ROOT / 'scripts/kicad/pin.env').read_text(), re.M)
    need(image is not None and record.get('image') == image.group(1), 'fixture gate image differs')
    need(record.get('container_id') == cid and record.get('worker') == env['EPIC242_NATIVE_WORKER']
         and record.get('deadline') == int(env['EPIC242_NATIVE_DEADLINE']), 'fixture gate worker/deadline differs')
    need(record.get('command') == expected, 'fixture gate exact command differs')
    need((cgroup / 'memory.max').read_text().strip() == '6442450944' and
         (cgroup / 'memory.swap.max').read_text().strip() == '0', 'fixture native caps differ')


def worker(env, output):
    local, unused, destination = context(env, output, host=True)
    verify_host_resources(env)
    destination.mkdir(exist_ok=False)
    result = subprocess.run(['bash', 'scripts/kicad/run.sh', *native_command(env, local, output)],
                            cwd=ROOT, env=env, check=False)
    local.authority(ROOT, env, host=True)
    return result.returncode


def native(env, output):
    local, request, destination = context(env, output, host=False)
    verify_native_gate(env, native_command(env, local, output))
    need(destination.is_dir() and not list(destination.iterdir()), 'fresh empty fixture output required')
    import pcbnew  # Exact authority and real read-only guard proof precede native import.
    result = characterize(pcbnew, FIXTURE, destination / 'roundtrip.kicad_pcb')
    local.authority(ROOT, env, host=False)
    result.update(request_sha256=local.sha(local.local_path(ROOT, request['request_path'], cache=True)),
                  worker=request['worker'], status='CHARACTERIZATION COMPLETE; NOT NATIVE ACCEPTANCE')
    with (destination / 'characterization.json').open('x') as stream:
        stream.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('worker', 'native'))
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        return (worker if args.phase == 'worker' else native)(dict(os.environ), args.output)
    except (ValueError, KeyError, OSError) as error:
        print('ANNULUS FIXTURE REFUSED: ' + str(error))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
