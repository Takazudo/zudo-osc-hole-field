"""Conditional source-level screens, not analog qualification."""
from decimal import Decimal as D
import json
r=D(5600);t=D('.01');v=D(5)
out={'conditions':'Nominal +/-12V rails; +/-5V MONITOR; 1% resistor envelope conditional on selected resistor specification; closed-loop DC equation only','current_mA_nominal':str(v/r*1000),'current_mA_Rmin':str(v/(r*(1-t))*1000),'current_mA_Rmax':str(v/(r*(1+t))*1000),'TL_recommended_input_min_V':-8,'TL_negative_margin_at_minus5_V':3,'TL_positive_margin_at_plus5_V':7.1,'bridge_drop_plus_output_headroom_budget_at_abs5_V':7,'TL4mV_offset_current_uA_at_Rmin':str(D('.004')/(r*(1-t))*1000000),'TL_typical_quad_Iq_mA':str(D('.9375')*4),'OPA_typical_quad_Iq_mA':str(D('.140')*4),'two_packages_typical_Iq_increment_mA':str((D('.9375')-D('.140'))*8),'warning':'Iq comparison uses datasheet typicals and is not actual24V measured power; output swing/max current at unrelated conditions not used as guarantee'}
print(json.dumps(out,indent=2))
