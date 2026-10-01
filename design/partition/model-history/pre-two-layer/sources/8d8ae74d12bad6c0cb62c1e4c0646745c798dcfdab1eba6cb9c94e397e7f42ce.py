"""Apply only the explicitly named P source-owned outline/reserve revision."""
from scripts.pcbgen.uuid_tools import stable_uuid


def apply(board, original, revised, change):
    import pcbnew

    board_id = 'osc-control'
    if original['board_id'] != board_id or revised['board_id'] != board_id:
        raise ValueError('P board required')
    def vector(point):
        return pcbnew.VECTOR2I(pcbnew.FromMM(point[0] + 100), pcbnew.FromMM(point[1] + 50))
    def nm(point):
        return [point.x, point.y]

    existing = {item.m_Uuid.AsString(): item for item in board.GetDrawings()}
    old_edges = []
    for index, start in enumerate(original['outline']):
        uid = stable_uuid(board_id, 'outline', str(index))
        item = existing.get(uid)
        end = original['outline'][(index + 1) % len(original['outline'])]
        if item is None or item.GetLayer() != pcbnew.Edge_Cuts or item.GetShape() != pcbnew.SHAPE_T_SEGMENT:
            raise ValueError('Original owned edge identity/type changed')
        if nm(item.GetStart()) != nm(vector(start)) or nm(item.GetEnd()) != nm(vector(end)):
            raise ValueError('Original owned edge geometry changed')
        old_edges.append(item)
    managed_ids = {stable_uuid(board_id, 'outline', str(index)) for index in range(1024)}
    if set(existing).intersection(managed_ids) != {item.m_Uuid.AsString() for item in old_edges}:
        raise ValueError('Unexpected additional managed P edge')
    for item in old_edges:
        board.Remove(item)
    added_edges = []
    for index, start in enumerate(revised['outline']):
        item = pcbnew.PCB_SHAPE(board)
        item.SetLayer(pcbnew.Edge_Cuts)
        item.SetWidth(pcbnew.FromMM(0.05))
        item.SetShape(pcbnew.SHAPE_T_SEGMENT)
        item.SetStart(vector(start))
        item.SetEnd(vector(revised['outline'][(index + 1) % len(revised['outline'])]))
        item.SetUuid(pcbnew.KIID(stable_uuid(board_id, 'outline', str(index))))
        board.Add(item)
        added_edges.append(item.m_Uuid.AsString())
    zones = {zone.GetZoneName(): zone for zone in board.Zones()}
    removed = []
    for source in change['removed_keepouts']:
        for layer in source['layers']:
            key = source['id'] + ':' + layer
            name = 'pcbgen:' + board_id + ':keepout:' + key
            zone = zones[name]
            outline = zone.Outline()
            if zone.m_Uuid.AsString() != stable_uuid(board_id, 'keepout', key) or not zone.GetIsRuleArea():
                raise ValueError('Original reserve is not generator owned')
            actual = [nm(outline.COutline(0).CPoint(i)) for i in range(outline.COutline(0).PointCount())]
            expected = [nm(vector(point)) for point in source['polygon']]
            if outline.OutlineCount() != 1 or outline.HoleCount(0) or actual != expected or zone.GetLayer() != board.GetLayerID(layer):
                raise ValueError('Original reserve shape/face changed')
            if not all((zone.GetDoNotAllowTracks(), zone.GetDoNotAllowVias(), zone.GetDoNotAllowPads(), zone.GetDoNotAllowZoneFills(), zone.GetDoNotAllowFootprints())):
                raise ValueError('Original reserve prohibitions changed')
            removed.append(zone.m_Uuid.AsString())
            board.Remove(zone)
    added = []
    for source in change['added_keepouts']:
        for layer in source['layers']:
            key = source['id'] + ':' + layer
            name = 'pcbgen:' + board_id + ':keepout:' + key
            if name in zones:
                raise ValueError('New individual reserve conflicts with an existing owner')
            zone = pcbnew.ZONE(board)
            zone.SetZoneName(name)
            zone.SetLayer(board.GetLayerID(layer))
            zone.SetIsRuleArea(True)
            for method in ('SetDoNotAllowTracks', 'SetDoNotAllowVias', 'SetDoNotAllowPads', 'SetDoNotAllowZoneFills', 'SetDoNotAllowFootprints'):
                getattr(zone, method)(True)
            outline = zone.Outline()
            index = outline.NewOutline()
            for point in source['polygon']:
                outline.Append(vector(point), index)
            zone.SetUuid(pcbnew.KIID(stable_uuid(board_id, 'keepout', key)))
            board.Add(zone)
            added.append(zone.m_Uuid.AsString())
    return {'old_edge_uuids': [stable_uuid(board_id, 'outline', str(i)) for i in range(len(old_edges))],
            'new_edge_uuids': added_edges, 'removed_reservation_uuids': removed,
            'added_reservation_uuids': added, 'source_change': change}
