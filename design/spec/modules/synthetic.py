"""Synthetic generator fixture; no claim that this is a usable circuit."""
from scripts.schgen.core import Family, Instance, Part


def example():
    parts = []
    amp_nets = [
        {'1':'AOUT', '2':'AIN-', '3':'AIN+'},
        {'5':None, '6':None, '7':None},
        {'8':None, '9':None, '10':None},
        {'12':None, '13':None, '14':None},
        {'4':'VCC', '11':'GND'},
    ]
    for n, pins in enumerate(amp_nets, 1):
        parts.append(Part(f'U1.{n}', 'Fixture:LM2902', 'U', 1, n, 55.88+(n-1)*30.48, 55.88, pins,
                          value='LM2902', attributes={'Role':'synthetic amplifier'}))
    comp_nets = [
        {'1':'COUT', '2':'AOUT', '3':'AIN+'},
        {'5':None, '6':None, '7':None},
        {'4':'GND', '8':'VCC'},
    ]
    for n, pins in enumerate(comp_nets, 1):
        parts.append(Part(f'U2.{n}', 'Fixture:LM2903', 'U', 2, n, 55.88+(n-1)*30.48, 96.52, pins,
                          value='LM2903', attributes={'Role':'synthetic comparator'}))
    parts += [
        Part('R1', 'Fixture:R', 'R', 1, 1, 55.88, 129.54, {'1':'VCC','2':'COUT'}, value='10k', attributes={'Role':'pull-up'}),
        Part('R2', 'Fixture:R', 'R', 2, 1, 86.36, 129.54, {'1':'AIN+','2':'GND'}, value='10k', attributes={'Role':'bias'}),
        Part('J1', 'Fixture:Conn_01x02', 'J', 1, 1, 121.92, 129.54, {'1':'AIN+','2':'GND'}, value='Conn_01x02', attributes={'Role':'input', 'PanelUid':'J:${SHEETNAME}.IN', 'Island':'J:${SHEETNAME}.IN'}),
        Part('R3', 'Fixture:R', 'R', 3, 1, 152.4, 129.54, {'1':'AOUT','2':'AIN-'}, value='10k', rotation=90, attributes={'Role':'feedback'}),
    ]
    power = [
        Part('P1', 'Fixture:PWR_FLAG', '#FLG', 1, 0, 175.26, 129.54, {'1':'VCC'}, value='PWR_FLAG'),
        Part('P2', 'Fixture:PWR_FLAG', '#FLG', 2, 0, 190.5, 129.54, {'1':'GND'}, value='PWR_FLAG'),
        Part('P3', 'Fixture:VCC', '#PWR', 3, 1, 175.26, 139.7, {'1':'VCC'}, value='VCC'),
        Part('P4', 'Fixture:GND', '#PWR', 4, 1, 190.5, 139.7, {'1':'GND'}, value='GND'),
    ]
    return (Family('synthetic', tuple(parts), global_nets=('VCC','GND'), sensitive_nets=('AIN-',)), Family('power', tuple(power), global_nets=('VCC','GND'))), tuple([Instance('synthetic',f'SYN{n}',n) for n in range(1,4)] + [Instance('power','POWER',4)])
