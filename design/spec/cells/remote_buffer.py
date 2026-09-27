"""OSC-ES-1 remote buffer proposal cell."""
from ._builder import cell_parts

def build(panel_uid, nets=None, *, ordinal_start=1, instance_tag=''):
    return cell_parts('remote_buffer', panel_uid, nets, ordinal_start=ordinal_start, instance_tag=instance_tag)
