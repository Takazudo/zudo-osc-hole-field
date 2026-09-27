"""OSC-ES-1 stage indicator proposal cell."""
from ._builder import cell_parts

def build(panel_uid, nets=None, *, ordinal_start=1, instance_tag=''):
    return cell_parts('stage_indicator', panel_uid, nets, ordinal_start=ordinal_start, instance_tag=instance_tag)
