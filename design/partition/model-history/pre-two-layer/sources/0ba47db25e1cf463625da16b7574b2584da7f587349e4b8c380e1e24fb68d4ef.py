"""Resolve the physical external foil for a single-face SMD interface.

This selects a native foil, not a physical contact-density class. Through-hole
terminals require a separately defined interface and are deliberately rejected.
"""


def external_smd_face(shapes, identity):
    layers=set(shapes)
    if layers=={'F.Cu'}:
        return 0
    if layers=={'B.Cu'}:
        return 3
    raise ValueError('terminal requires exactly one external native foil: '+identity)


def main_land_face(shapes):
    """Recognize the existing 4 x 4 mm single-foil main-land geometry."""
    if set(shapes) not in ({'F.Cu'},{'B.Cu'}):
        return None
    layer=0 if 'F.Cu' in shapes else 3
    shape=shapes['F.Cu' if layer==0 else 'B.Cu']
    x0,y0,x1,y1=shape.bounds
    if abs(shape.area-16)<1e-4 and abs(x1-x0-4)<1e-4 and abs(y1-y0-4)<1e-4:
        return layer
    return None
