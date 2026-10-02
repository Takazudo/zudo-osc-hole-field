"""Source pose directives, independent of pcbnew and existing board state."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class SourcePose:
    side: str | None
    orientation: float | None
    force_lock: bool


def source_pose(fields: dict, fixed_rotation: float | None = None) -> SourcePose:
    side = fields.get('BoardSide', '')
    if side not in ('', 'F.Cu', 'B.Cu'):
        raise ValueError('invalid BoardSide')
    raw = fields.get('KiCadOrientationDeg', '')
    orientation = None
    if raw != '':
        try:
            orientation = float(raw)
        except (TypeError, ValueError) as error:
            raise ValueError('invalid KiCadOrientationDeg') from error
        if isinstance(raw, bool) or not math.isfinite(orientation):
            raise ValueError('invalid KiCadOrientationDeg')
    if fixed_rotation is not None:
        if not math.isfinite(fixed_rotation):
            raise ValueError('invalid lockfile rotation')
        if side == 'B.Cu':
            raise ValueError('panel hardware must face F.Cu')
        if orientation is not None and orientation % 360 != fixed_rotation % 360:
            raise ValueError('KiCadOrientationDeg conflicts with lockfile rotation')
        return SourcePose('F.Cu', fixed_rotation, True)
    return SourcePose(side or None, orientation,
                      bool(fields.get('FootprintOriginMm') and not fields.get('BoardRegion')))
