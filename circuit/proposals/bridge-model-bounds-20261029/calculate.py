"""Conditional 25C monotonic-I/V screen. Not a guaranteed circuit limit."""
from decimal import Decimal as D
import json
led=D('4.0')+D('.1');diode=D('.715');drop=led+2*diode
print(json.dumps({'assumptions':['25C only','Nondecreasing forward I/V from actual <=1mA to published1mA diode/20mA LED test points','LED4.0V maximum expanded by stated0.1V measurement tolerance','Diode pulsed test limit used only as a conditional DC-screen bound; no temperature extrapolation','No opamp output-headroom guarantee inferred'], 'conditional_bridge_drop_V':str(drop),'at_5V_command_required_drive_magnitude_V':str(5+drop),'nominal12V_remaining_for_opamp_headroom_V':str(12-5-drop),'illustrative10_8V_remaining_for_opamp_headroom_V':str(D('10.8')-5-drop),'reused_5V_Rmin_current_mA':str(D(5)/D(5544)*1000),'result':'Positive conditional headroom budget; not a qualified worst-case margin or transient result'},indent=2))
