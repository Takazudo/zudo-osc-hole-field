"""Render the authored standard-cell reference from the proposal authority."""
from pathlib import Path
import json
from ._builder import ROOT,STANDARD,CELLS
DOC=ROOT/'doc/src/content/docs/architecture/osc-standard-cells.mdx'
SPICE=ROOT/'design/reports/spice/cells.json'
CURRENT=ROOT/'design/reports/current/cells.json'
PATHS={
'input_fault_switch':['JACK','ADG5412F','PROTECTED'],
'high_impedance_input':['PROTECTED','10k limiter + BAT54S','CV buffer','BUFFERED'],
'summing_node_input':['PROTECTED','100k input + clamp','SUM'],
'general_output':['SIGNAL','local feedback buffer','499Ω + 499Ω','JACK'],
'precision_output':['SIGNAL','precision buffer','499Ω + 499Ω','JACK','100Ω DC feedback + 1nF local feedback'],
'remote_buffer':['SIGNAL','local buffer','100Ω isolation','REMOTE'],
'bipolar_attenuverter':['BUFFERED_INPUT','10k panel pot','wiper buffer + summer','OUT'],
'dc_control_source':['buffered ±5V refs','100k panel pot','CV follower','OUT'],
'level_attenuator':['REMOTE_INPUT','10k panel pot','audio follower','OUT'],
'reference_generator':['+12V','REF5050','buffered ±5V and gate refs'],
'octave_reference':['buffered endpoints','five 10k resistors','six buffered octave taps'],
'gate_trigger_input':['BUFFERED','biased comparator','Schmitt inverter','GATE_HIGH'],
'magnitude_indicator':['MONITOR','bridge driver','4-diode rectifier','white LED'],
'clip_detector':['MONITOR','divide by two','±5V window comparators','red LED'],
'stage_indicator':['ENV_BUFFERED','divider + stage mute','current sink','white LED'],
'switch_button_input':['CONTACT','pull-up + RC','Schmitt inverter','ACTIVE'],
'decoupling_bulk':['rail','100nF local + 4.7µF bulk','analog return'],
'trimmer':['LIMITED_LOW','10k strapped trimmer','100k limiter','CAL_SUM'],
'slew_island':['HELD_BUFFERED','precision pre-buffer','2.2k + 500k rheostat','five 100nF caps','precision post-buffer'],
}

def build():
 sim={x['id']:x for x in json.loads(SPICE.read_text())['cells']}
 current={x['id']:x for x in json.loads(CURRENT.read_text())['cells']}
 lines=['---','title: "OSC-ES-1 reusable standard cells"','description: "Nineteen proposed circuit cells, terminal nets, current worksheet, and isolated KiCad checks."','sidebar_position: 31','---','',
 'These 19 cells implement **OSC-ES-1, PROPOSAL (planning, owner-delegated)**. Every schematic is an **unvalidated draft**. `design/standard/electrical-standard.json` supplies values, roles and topology. `design/spec/cells/*.py` exposes `build(panel_uid, nets)`; the UID comes from the fixed placement lockfile and `nets` maps standard port names to module nets. Each complete IC package, including unused sections and its power unit, is represented in the returned Parts.','',
 'The generated harness under `schematic/cells/` has zero KiCad 10 ERC errors and six documented LED pin-type warnings; `schematic/reports/cells-erc-notes.md` explains them. Its exported netlist matches the spec at every pin. Test-only port sources and loads are not module design parts. These checks establish connectivity consistency, not correct analog behavior or physical safety.','',
 'The proposed signal diode is **Nexperia BAS16GW-QX**, replacing an unsupported `1N4148W,115` identity. Nexperia’s [exact OPN record](https://www.nexperia.com/chemical-content/BAS16GW-Q.html?identifier=BAS16GW-Q) names BAS16GW-QX in SOD123; the retained BAS16GW-Q datasheet gives pin 1 cathode and pin 2 anode. Bridge brightness and physical qualification remain open.','',
 'The historical OSC-ES-1 preliminary worksheet estimated **712.655 mA on −12 V against its then-proposed 640 mA ceiling**. Those figures describe the superseded supply study, not the current EXT requirement contract. See the [current supply architecture](../decisions/osc-supply-architecture.mdx) and its generated `design/power/rail-ledger.json` and `design/power/supply-architecture.json` for present allocations. Current figures below remain partial planning allocations, not cell maxima or a passing instrument budget. Exact value-specific passive sourcing, package sharing, output loads and rail startup remain open; #57 retains physical source qualification and #59 retains protection implementation.','']
 for cell in CELLS.values():
  id=cell['id'];lines += [f'## {id.replace("_"," ").title()} (`{id}`)','',f'Status: **{cell["verification_status"]}**. Model check: **{sim[id]["status"]}**.','',
   '```mermaid','flowchart LR']
  path=PATHS[id]
  for n,label in enumerate(path):lines.append(f'  N{n}["{label}"]')
  for n in range(len(path)-1):lines.append(f'  N{n} --> N{n+1}')
  lines+=['```','','| Ref | Selected role | Value | Terminal → cell net |','| --- | --- | --- | --- |']
  for part in cell['parts']:
   ident=part.get('part_id') or 'opamp role: '+part['opamp_role']
   value=part.get('value');unit=part.get('unit','')
   value_text=(f'{value:g} {unit}' if value is not None else 'per selected part')
   terms=', '.join(f'`{pin}`→`{net}`' for pin,net in part['terminals'].items())
   lines.append(f'| `{part["ref"]}` | `{ident}` | {value_text} | {terms} |')
  amps=current[id]['known_planning_mA']
  lines+=['',f'**Known planning allocation:** +12 V {amps["+12V"]:g} mA; −12 V {amps["-12V"]:g} mA; +5 V {amps["+5V"]:g} mA. This is incomplete where device, signal and load currents are unquantified.','']
  if current[id]['unquantified']:lines.append('**Unquantified:** '+', '.join(current[id]['unquantified'])+'.');lines.append('')
  if id in ('bipolar_attenuverter','magnitude_indicator','gate_trigger_input','clip_detector','stage_indicator'):
   results=', '.join(f'{name} = {m["value"]:.6g}' for name,m in sim[id]['measurements'].items())
   lines += [f'**Ideal ngspice result:** {results}. This tests only the named ideal topology and generic device models; no vendor or hardware behavior is qualified.','']
  elif 'reason' in sim[id]:lines+=['**Full-cell simulation: NOT RUN** — '+sim[id]['reason'],'']
  else:lines+=['**Full-cell simulation:** '+sim[id]['status']+' — '+sim[id]['limit'],'']
  if id=='precision_output':
   vendor=json.loads((ROOT/'design/reports/spice/precision-output-vendor.json').read_text())
   worst=max(vendor['cases'],key=lambda case:case['overshoot_percent'])
   lines += [f'**TI OPAx197 Final 1.3 model sweep:** {vendor["pass_count"]} of {len(vendor["cases"])} cases pass overshoot, settling and late-ripple checks. Worst overshoot is {worst["overshoot_percent"]:g}% at {worst["load"]} load and {worst["cable_capacitance"]} cable capacitance. The fixed proposal uses 100 Ω jack-sense feedback and 1 nF local feedback. The prior 10 kΩ/100 pF ideal diagnostic remains retained with six of twelve failures; it was a different circuit and an ideal source, so its results do not predict this TI model. Value-specific 100 Ω and 1 nF orderable identities are still open. Physical cable, PCB parasitics, temperature and tolerance checks are **NOT RUN**.','']
  for note in cell.get('notes',[])[:3]:lines += ['- '+note.replace('<','less than ').replace('>','greater than ')]
  lines.append('')
 lines += ['## Verification limits','','The TI OPAx197 model includes OPA4197 and models output impedance, slew rate, settling and capacitive-load response. Its sweep is a model result for the stated fixed network, not a measurement or a guarantee across part and layout variation. Physical OPA4197 cable stability is **NOT RUN** pending a populated board/cable coupon; temperature, component tolerances, output-current and thermal checks are also open. The remote driver cable stability check is **NOT RUN** for its separate model/harness gap. Resistor-chain fault power is an arithmetic planning check, not thermal qualification. The sample-and-hold slew and reference outputs require measured calibration and hot/cold data. No cell is released for fabrication.','']
 return '\n'.join(lines)

def main(check=False):
 body=build()
 if check:
  if not DOC.is_file() or DOC.read_text()!=body:raise SystemExit('cell doc drift')
 else:DOC.write_text(body)
 print(f'{"Checked" if check else "Generated"} 19 cell documentation entries')
if __name__=='__main__':
 import sys
 main('--check' in sys.argv)
