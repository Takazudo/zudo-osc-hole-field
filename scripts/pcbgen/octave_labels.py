"""Place an untouched adapter reference on its tongue; preserve edited labels."""
import pcbnew
from scripts.geometry.panel_frame import to_kicad


def place_default_reference(footprint, hardware):
    # The SRBV library reference is at local (0,-12). The rear selector rotates
    # that default below the board. Both source outlines have their tongue at
    # panel y = shaft_y - 12; only the unedited library pose is migrated.
    if str(footprint.GetFPID().GetLibItemName()) != 'SRBV160803':
        raise ValueError('unexpected octave selector footprint')
    rotation = hardware['rot_deg'] % 360
    if rotation not in (0, 180):
        raise ValueError('unsupported octave reference rotation')
    reference = footprint.Reference()
    center = to_kicad(hardware['x_mm'], hardware['y_mm'])
    default_y = center[1] + (12 if rotation == 180 else -12)
    position = reference.GetPosition()
    if (abs(pcbnew.ToMM(position.x) - center[0]) > 1e-6
            or abs(pcbnew.ToMM(position.y) - default_y) > 1e-6
            or reference.GetLayer() != pcbnew.F_SilkS
            or abs((reference.GetTextAngle().AsDegrees()-rotation+180) % 360-180) > 1e-6):
        return False
    reference.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(center[0]),
                                         pcbnew.FromMM(center[1]-12)))
    reference.SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
    return rotation == 180
