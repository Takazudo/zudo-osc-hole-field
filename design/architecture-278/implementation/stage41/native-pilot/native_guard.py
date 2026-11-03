"""Compare native in-memory identities to raw input before connectivity/save."""
from collections import Counter
import pcbnew
from identity_guard import inventory


def copper_identity(board, t):
    point = lambda p: (p.x, p.y)
    if t.Type() == pcbnew.PCB_TRACE_T:
        kind = 'segment'
        shape = (point(t.GetStart()), point(t.GetEnd()), (t.GetWidth(),), board.GetLayerName(t.GetLayer()))
    elif t.Type() == pcbnew.PCB_VIA_T:
        kind = 'via'
        shape = (point(t.GetPosition()), (t.GetWidth(pcbnew.F_Cu),), (t.GetDrillValue(),),
                 (board.GetLayerName(t.TopLayer()), board.GetLayerName(t.BottomLayer())))
    else:
        raise ValueError('unsupported native copper type')
    return kind, t.m_Uuid.AsString(), shape, t.GetNetname()


def check_native(board, raw_text):
    if pcbnew.GetBuildVersion() != '10.0.6':
        raise ValueError('exact KiCad 10.0.6 required')
    expected = inventory(raw_text)
    copper = Counter()
    for t in board.GetTracks():
        copper[copper_identity(board, t)] += 1
    pads = Counter((f.m_Uuid.AsString(), f.GetReference(), p.m_Uuid.AsString(), p.GetNumber(), p.GetNetname())
                   for f in board.GetFootprints() for p in f.Pads())
    zones = Counter((z.m_Uuid.AsString(), z.GetNetname()) for z in board.Zones())
    expected_zones = Counter()
    for (uid, net, _), count in expected['zones'].items():
        expected_zones[(uid, net)] += count
    checks = {'copper': copper == expected['native_contract'], 'pads': pads == expected['pads'],
              'zones': zones == expected_zones}
    if not all(checks.values()):
        missing = list((expected['native_contract'] - copper).elements())[:10]
        extra = list((copper - expected['native_contract']).elements())[:10]
        raise ValueError(f'native identity changed: {checks}; missing={missing}; extra={extra}')
    return checks
