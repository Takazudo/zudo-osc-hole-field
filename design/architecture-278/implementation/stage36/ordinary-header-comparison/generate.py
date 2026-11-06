"""Planning evidence/sketch using existing Stage36 SVG primitives, no native CAD."""
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'scripts/architecture278/implementation'))
from stage36_interface_cassette import svg_start, text, rect


def outputs():
    i=json.loads((ROOT/'design/architecture-278/implementation/stage10/interface-input.json').read_text())
    old=json.loads((ROOT/'design/architecture-278/implementation/stage10/interfaces-report.json').read_text())
    inputs=['design/architecture-278/implementation/stage10/interface-input.json',
            'design/architecture-278/implementation/stage10/interfaces-report.json',
            'design/architecture-278/implementation/stage36/whole-layout-review/view-data.json',
            'design/architecture-278/implementation/stage36/practical-idc-layout/cad-report.json',
            'design/architecture-278/implementation/stage36/practical-idc-layout/sources.json',
            'design/architecture-278/implementation/stage36/standard-idc-comparison/sources.json',
            'scripts/architecture278/implementation/stage36_interface_cassette.py']
    sig={str(2*n-1):old['DIN_pinmap']['c'+str(n)] for n in range(1,9)}
    sig.update({str(2*n):old['DIN_pinmap']['b'+str(n)] for n in range(1,9)})
    maps={q['id']:{'boards':[q['local']['board'],q['middle']['board']],
                    'pins':q['pins'],'proposed_mode':'direct8' if q['id']=='K-PWR' else 'IDC'} for q in i['links']}
    maps['rear_signal']={'boards':['A01-middle','A01-core'],'pins':sig,'proposed_mode':'direct16'}
    a={'status':'UNADOPTED_PLANNING_ONLY','hardware_fit_established':False,
       'input_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs},
       'maps':maps,'retained_tail_wires':old['counts']['permanent_terminal_wires'],
       'direct':{'male_body_mm':[2.39,2.69],'male_pin_mm':[5.8,6.2], 'socket_height_mm':[8.3,8.7],
                 'assumed_separation_mm':[11.9,12.1], 'penetration_mm':[4.39,5.69],
                 'axial_screen_nominal_spacing_open_interval_mm':[11.73,13.99],
                 'qualified_insertion_interval':None,'body_gap_min_mm':.51,
                 'electrical_strip_max_length_mm':round(21.12+6+10.96+4,2),
                 'strip_proposal_mm':[43,10],'component_fit':None,'support_fit':None},
       'IDC':{'supplied_open_cap_height_mm':18.3,'closed_height_mm':None,
              'assumed_bend_radius_mm':10,'assumed_placement_bow_mm':2,
              'planning_depth_mm':32,'open_access_column_mm':36,'cut_lengths_mm':None},
       'service':{'axial_pin_clearance_screen_mm':5.69,'historical_core_reservation_mm':40,
                  'new_full_sweep_clear':None,'load_support_qualified':False},
       'procurement':{'ordered':False,'stock_verified':False,'exact_spacer':None,'long_pin_variant':None}}
    s=svg_start('Ordinary direct stack or IDC — dimensioned planning comparison',
                'Unadopted source study. All dimensions mm. Unknown board population remains occupied/unknown. No manufacturing outputs.')
    s += [text(30,40,'A01 / ordinary headers + spacers, or ribbon IDC',25),
          text(30,72,'Dimensions in mm • proposals • existing fixed front hardware untouched • not a populated fit drawing',17),
          text(40,112,'A / Direct rear pair — 12 mm face gap',21),
          text(650,112,'B / IDC — accessible edge bay',21)]
    # Direct section, upward means rearward. Board surfaces are exact labeled z proposals.
    s += [rect(65,400,390,19.2,'#376E61','#dbe8df'),text(70,445,'Middle: z48.4–50 retained study',16),
          rect(65,236.8,390,19.2,'#376E61','#dbe8df'),text(70,217,'Core: z62–63.6 PROPOSED (was69.2–70.8)',16),
          rect(180,369.52,70,30.48,'#253235','#b6c2bd'),
          rect(180,256,70,102,'#253235','#d3d8d2'),
          rect(209,297.52,12,72,'#aa7744','#ddba78'),
          text(270,285,'Socket 8.5±0.2',16),text(270,321,'Pin 6.0±0.2',16),text(270,374,'Body 2.54±0.15',16),
          rect(90,256,32,144,'#a65e42','none',True),text(70,475,'Spacer sketch: exact SKU / screws / bow OPEN',15),
          '<path d="M475 256h18m-9 0v144m-9 0h18" fill="none" stroke="#253235"/>',
          text(496,318,'S=12',18),text(496,343,'±0.10*',15),
          '<path d="M570 230v-65m-7 10l7-10 7 10" fill="none" stroke="#376E61"/>',
          text(65,155,'Axial first: >5.69 pin clearance screen',16),
          text(65,178,'Then retained40 removal reservation; full sweep UNKNOWN',15)]
    s += [rect(680,400,360,10,'#376E61','#dbe8df'),
          rect(745,290.2,100,109.8,'#253235','#d3d8d2'),
          '<path d="M795 290 Q795 230 855 230 H1010" fill="none" stroke="#aa7744" stroke-width="5"/>',
          text(870,280,'R10 assumed',16),text(855,325,'18.3 supplied',16),text(855,347,'open-cap CAD',16),
          text(855,369,'closed height UNKNOWN',15),
          '<path d="M1060 208h18m-9 0v192m-9 0h18" fill="none" stroke="#253235"/>',
          text(1090,292,'32',20),text(1090,315,'proposal',12),
          rect(680,208,360,192,'#a65e42','none',True),
          text(665,155,'36 mm open access column proposed',16),
          text(665,178,'Unplug + park before core moves40 mm',16),
          text(665,445,'32 >19.2 existing gap: no hidden bay-fit claim',16),
          text(665,475,'Grip / cable path / neighbors / cover remain OPEN',15)]
    s += [text(40,525,'Electrical strip only — excludes screws / tool access',18),
          rect(65,555,344,80,'#376E61','none',True),
          rect(81,574,168.96,41.84,'#253235','#d3d8d2'),
          rect(297.96,574,87.68,41.84,'#253235','#d3d8d2'),
          text(90,600,'2×8 signals+returns',14),text(305,600,'2×4 PWR',13),
          text(65,660,'43×10 allocation; 42.08×9.23 body + chosen gaps',15),
          text(650,525,'IDC strip: 14-signal +8-internal power',18),
          text(650,555,'Max header lengths25.64 +18.02 mm',16),
          text(650,581,'+12 grip gap +8 ends =63.66 →64×30 bay*',16),
          text(650,609,'Front links:3 cables /6 presses; rear direct:0 cable',16),
          text(650,637,'All-IDC rear alternative: +2 cables /4 presses',16),
          text(30,708,'* Engineering allowances, not maker guarantees. All untallied components/supports remain UNKNOWN.',16,'#a65e42'),
          text(30,738,'Source: exact WR-PHD/BHD drawings + retained A01 study. No geometry adoption, order or physical result.',15),
          '</g></svg>']
    return {'analysis.json':json.dumps(a,indent=2,sort_keys=True)+'\n','comparison.svg':'\n'.join(s)+'\n'}

if __name__=='__main__':
    for name,data in outputs().items():
        p=HERE/name
        if '--check' in sys.argv:
            if not p.exists() or p.read_text()!=data:raise SystemExit('STALE '+name)
        else:p.write_text(data)
    print('PASS deterministic planning outputs' if '--check' in sys.argv else 'Wrote planning outputs')
