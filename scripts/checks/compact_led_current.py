#!/usr/bin/env python3
"""Conditional current arithmetic for exact compact LED draft; no hardware sign-off."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
source=R/'design/standard/electrical-standard.json'
cells={x['id']:x for x in json.loads(source.read_text())['cells']}
def value(cell,ref):return next(x['value'] for x in cells[cell]['parts'] if x['ref']==ref)
assert value('stage_indicator','R_LED_LIMIT')==1200
assert value('stage_indicator','R_SENSE')==1000
assert value('magnitude_indicator','R_SENSE')==5600
assert value('clip_detector','R_LED')==22100
assumptions={'rail_plus_5_upper_V':5.5,'rail_plus_12_upper_V':13.2,'rail_minus_12_lower_V':-13.2,'resistor_minimum_fraction':0.99,'operating_ambient_upper_C':50}
stage_current=5.5/(1200*.99)*1000
stage_resistor_power=5.5**2/(1200*.99)*1000
magnitude_current=26.4/(5600*.99)*1000
red_current=26.4/(22100*.99)*1000
assert stage_current<5 and magnitude_current<5 and red_current<25
x={'schema_version':1,'status':'CONDITIONAL DRAFT; assumed rail and resistor tolerances, no measured thermal or optical validation',
   'source':'design/standard/electrical-standard.json','assumptions':assumptions,
   'white_primary':'Kingbright APHHS1005QWF/D; DSAK0125 / 1203009228 V.10B pages 2-3',
   'red_primary':'Kingbright APG1005SEC/E-T; DSAM9600 / 1203013767 V.10A page 2',
   'white_25C_dc_absolute_max_mA':30,'white_85C_derating_conservative_read_mA':5,
   'red_25C_dc_absolute_max_mA':25,
   'branches':{
      'stage_white':{'count':12,'resistor_nominal_ohm':1200,'resistor_exact_identity':'UNSELECTED','worst_zero_diode_drop_mA':round(stage_current,3),'worst_resistor_mW':round(stage_resistor_power,3),'nominal_0_5mA_resistor_drop_V':0.6,'verdict':'CONDITIONAL: assumed +5 V <=5.5 V; manufacturer graph near 5 mA at 85 C; exact resistor derating, supply tolerance, fault response and light output open'},
      'magnitude_white':{'count':92,'sense_resistor_nominal_ohm':5600,'supply_bound_V':26.4,'worst_zero_diode_drop_mA':round(magnitude_current,3),'verdict':'CONDITIONAL: assumed +/-12 V rails <= +/-13.2 V; magnitude fault/loop behavior, exact resistor sourcing and installed ambient remain open'},
      'clip_red':{'count':10,'series_resistor_nominal_ohm':22100,'supply_bound_V':26.4,'worst_zero_diode_drop_mA':round(red_current,3),'verdict':'CONDITIONAL: assumed +/-12 V rails <= +/-13.2 V; exact resistor/fault response open'}},
   'rail_worksheet':'Nominal LED load allocations remain unchanged; 1.2 kohm stage resistor is series with LED, not an added independent rail load. At high VF, driver headroom may reduce actual LED current. Existing rail budgets are planning values, not maxima.',
   'not_run':['ambient and installed LED thermal measurements','light output at actual current','panel-window coupling','assembled fit','rail tolerance and startup/fault oscilloscope measurements']}
p=R/'design/reports/current/compact-led-61.json';p.write_text(json.dumps(x,indent=2)+'\n')
print(f'PASS: conditional worst stage {stage_current:.3f} mA/{stage_resistor_power:.1f} mW, magnitude {magnitude_current:.3f} mA, red {red_current:.3f} mA')
