#!/usr/bin/env python3
"""Fixture setup: seed one routed instance's local tracks onto a six-instance board."""
import sys
import pcbnew
source=pcbnew.LoadBoard(sys.argv[1]);target=pcbnew.LoadBoard(sys.argv[2]);count=0
for item in source.GetTracks():
    name=item.GetNetname()
    if not (name.startswith('/S') or name.startswith('/C')):continue
    net=target.FindNet(name)
    if net is None:raise ValueError(name)
    clone=item.Duplicate();clone.SetParent(target);clone.SetNet(net);clone.SetLocked(True);target.Add(clone);count+=1
pcbnew.SaveBoard(sys.argv[2],target)
print(f'seeded {count} source-local tracks/vias')
