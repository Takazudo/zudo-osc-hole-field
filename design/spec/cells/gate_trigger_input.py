"""OSC-ES-1 gate trigger input proposal cell."""
from ._builder import cell_parts

def build(panel_uid, nets=None, *, ordinal_start=1, instance_tag=''):
    return cell_parts('gate_trigger_input', panel_uid, nets, ordinal_start=ordinal_start, instance_tag=instance_tag)
