#!/usr/bin/env python3
"""Check proposed support/pad/body reservations without claiming seated fit."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks.partition35_json import dumps
from scripts.partition.model import JACK_BOARDS
from scripts.checks.connector_packing35 import board_for,rect_collision,pads
from scripts.checks.partition35_diagnostic import footprint_geometry
from scripts.checks.partition35_floorplan import transformed
OUT=ROOT/'design/partition/mechanical-candidate.json'


def build():
    src=json.loads((ROOT/'design/partition/partition-input.json').read_text());io=json.loads((ROOT/'design/reports/io-partition.json').read_text());ports=json.loads((ROOT/'design/partition/connector-packing-candidate.json').read_text());optical=json.loads((ROOT/'design/partition/stage-optical-candidate.json').read_text());lock={p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
    errors=[];supports=[];parts=io['physical_packages']
    for b,s in src['boards'].items():
        points=list(s['supports_mm'])
        if b in ('EL','P'):points +=[h['center_mm'] for h in optical['support_posts'] if b=='EL' or h['center_mm'][1]>=176]
        for x,y in points:
            box=[x-1.6,y-1.6,x+1.6,y+1.6]
            # Carrier collars are real reserved volumes; compare against complete
            # fixed hardware courtyards (already include their solder margin).
            for p in parts:
                if board_for(p)!=b or not p['panel_uid']:continue
                geometry=footprint_geometry(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(p['footprint'].split(':')[1]+'.kicad_mod'))['courtyard_bbox_mm'];q=transformed(geometry,lock[p['panel_uid']])
                if rect_collision(box,q,0):errors.append('support/fixed hardware '+b+' '+str([x,y])+' '+p['ref'])
            for h in ports['headers']:
                if h['board']!=b:continue
                # EL collar is on the front; rear header only sees the Ø2 post.
                r=1 if b=='EL' else 1.6
                if rect_collision([x-r,y-r,x+r,y+r],h['land_courtyard_mm'],0):errors.append('support/header '+b+' '+h['id'])
            # All main outlines are orthogonal; corners/notches remain excluded.
            polygon=s['outline'];xs=[p[0] for p in polygon];ys=[p[1] for p in polygon]
            if not(min(xs)<=box[0] and box[2]<=max(xs) and min(ys)<=box[1] and box[3]<=max(ys)):errors.append('support outside outline '+b)
            if not(-2<=box[0] and box[2]<=320 and -2<=box[1] and box[3]<=300):errors.append('support outside enclosure')
            supports.append({'board':b,'center_mm':[x,y],'collar_diameter_mm':3.2,'hole_diameter_mm':2.2,'post_diameter_mm':2,'status':'PROPOSAL, strength/thread engagement NOT RUN #65'})
    # Load-side factory solder pads must avoid every existing plated hardware pad.
    d=src['load_distribution'];powerpads=[]
    for destination,branch in d['branches'].items():
        for index,(x,net) in enumerate(zip(branch['x_mm'],d['net_order'])):
            for b,y in [(destination,branch['pad_y_mm']),('K',branch['core_pad_y_mm'][index])]:
                box=[x-2.5,y-2.5,x+2.5,y+2.5]
                for p in parts:
                    if board_for(p)==b and p['panel_uid']:
                        for ref,q in pads(p,lock):
                            if rect_collision(box,q,.25):errors.append('load power pad overlaps '+ref)
                for h in ports['headers']:
                    if h['board']==b and rect_collision(box,h['land_courtyard_mm'],.25):errors.append('load pad/header '+h['id'])
                for h in supports:
                    if h['board']==b:
                        X,Y=h['center_mm']
                        if rect_collision(box,[X-1.6,Y-1.6,X+1.6,Y+1.6],.25):errors.append('load pad/support '+b)
                if b=='K':
                    for h in ports['K_service_apertures']:
                        if rect_collision(box,h['box_mm'],.25):errors.append('load pad/service '+h['header_id'])
                for reserve in src['boards'][b].get('board_bulk_reserve',[]):
                    if rect_collision(box,reserve['rect'],.25):errors.append('load pad/bulk '+b)
                powerpads.append({'board':b,'net':net,'center_mm':[x,y],'size_mm':[4,4],'courtyard_mm':box,'status':'PROPOSAL factory solder land; exact construction/current/strain-relief qualification #65'})
    for b,bs in src['boards'].items():
        for reserve in bs.get('board_bulk_reserve',[]):
            box=reserve['rect']
            for p in parts:
                if board_for(p)!=b or not p['panel_uid']:continue
                for ref,q in pads(p,lock):
                    if rect_collision(box,q,.25):errors.append('bulk reservation overlaps hardware pad '+b+' '+ref)
            for h in ports['headers']:
                if h['board']==b and h['side']==reserve['side'] and rect_collision(box,h['land_courtyard_mm'],.25):errors.append('bulk reservation overlaps header '+h['id'])
            if b=='K':
                for h in ports['K_service_apertures']:
                    if rect_collision(box,h['box_mm'],.25):errors.append('bulk reservation overlaps service hole '+h['header_id'])
    carrier=src['jack_split']['carrier']
    for p in parts:
        if board_for(p) not in JACK_BOARDS or not p['panel_uid']:continue
        shape=footprint_geometry(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(p['footprint'].split(':')[1]+'.kicad_mod'))['courtyard_bbox_mm']
        if rect_collision(carrier['front_lip_rect_mm'],transformed(shape,lock[p['panel_uid']]),.25):errors.append('seam lip/fixed courtyard '+p['ref'])
        for ref,box in pads(p,lock):
            if rect_collision(carrier['rear_rect_mm'],box,.25):errors.append('seam carrier/TH pad '+ref)
    for h in ports['headers']:
        if h['board'] in JACK_BOARDS and rect_collision(carrier['rear_rect_mm'],h['native_cached_courtyard_envelope_mm'],.25):errors.append('seam carrier/header '+h['id'])
    datum=[
      {'family':'WQP518MA jack','source':'design/mechanical/facts/jack.json','pcb_face_z_mm':-10,'required_board_to_panel_rear_shoulder_mm':8,'panel_method':'nut/bushing clamps directly to 2 mm flat panel','sourced_status':'seated shoulder, thread and clamp range UNSOURCED','verdict':'CONDITIONAL requirement only; installed reach NOT RUN #65'},
      {'family':'Bourns PTV09A-4020F pot family','source':'design/mechanical/facts/pot.json','pcb_face_z_mm':-11.8,'shaft_L_mm':20,'shaft_L_tolerance_mm':.5,'panel_aperture_mm':6.3,'body_front_requirement_z_mm':-5,'sourced_status':'L is SOURCED but not PCB-to-tip datum; actual seated body height UNSOURCED','support':'custom insulating body carrier captures sides; knob torque bypasses solder mounting legs','verdict':'CONDITIONAL body/shaft reach and capless-use coupon NOT RUN #65'},
      {'family':'Dailywell 2MS1 / 2MS3','source':'design/mechanical/facts/toggle.json','pcb_face_z_mm':-11.8,'body_height_candidate_mm':8.64,'bushing_candidate_mm':5.59,'derived_bushing_tip_z_mm':2.43,'nut_candidate_mm':1.19,'washer_candidate_mm':.46,'remaining_nominal_thread_mm':.78,'sourced_status':'retained drawing candidate dimensions; exact unsuffixed seating/applicability remains UNSOURCED','verdict':'CONDITIONAL nut clamp and lever/tolerance coupon NOT RUN #65'},
      {'family':'Omron B3F-1020','source':'design/mechanical/facts/button.json','pcb_face_z_mm':-11.8,'component_height_mm':5,'derived_actuator_top_z_mm':-6.8,'custom_plunger_nominal_length_mm':7.8,'custom_plunger_diameter_mm':4.5,'panel_aperture_mm':5,'support':'guided captive insulating plungers and rigid body carrier, positive travel stop; all factory assembly','verdict':'PROPOSAL actuator interface; stroke/overtravel/lateral fit NOT RUN #65'},
      {'family':'Alps SRBV160803','source':'design/mechanical/selector-assembly.json','pcb_face_z_mm':[-16,-29],'population_by_plane':[3,2],'body_tail_z_mm':[[-20,-8.5],[-33,-21.5]],'sourced_main_body_from_mount_face_mm':[0,7.5],'sourced_rear_terminal_reach_from_mount_face_mm':[-4,0],'source_locator':'Alps Drawing No.7, physical PDF page3, PC board mounting face side-view datum','GH7_main_body_from_mount_face_mm':[-5.65,-1.6],'front_body_to_GH7_body_nominal_gap_mm':1.6,'rear_terminal_and_mount_land_check':'Every retained TH pad projection versus full GH7 courtyard checked by connector_packing35; minimum mounting-copper gap0.35mm. Rear tail/solder must remain in the reserved footprint projection; unknown solid-leg/tail tolerance is NOT inferred from bore diameter.','support':'source-selected stepped M9 carrier, five indexed knobs and two keyed extensions','verdict':'Existing conditional nominal envelope retained; installed fit NOT RUN #55'},
      {'family':'Complete stage optical board','source':'design/partition/stage-optical-candidate.json','pcb_face_z_mm':-4.2,'thickness_mm':.4,'front_component_height_max_mm':1.75,'nominal_panel_gap_mm':.45,'nonpassing_pot_body_front_requirement_z_mm':-5,'nominal_rear_gap_mm':.4,'passages':{'switch':18,'button':6,'pot':18},'verdict':'Nominal proposal only; tolerance/stiffness NOT RUN #65 and optical #64'},
      {'family':'JST GH top-entry harness','source':'design/connectors/jst-gh.json','mated_reference_height_mm':7.3,'sourced_status':'SOURCED reference only; no manufacturer tolerance','verdict':'Local-plane geometry/ribbon proposal; installed mating/tool/loom NOT RUN #65'}]
    return {'schema_version':1,'status':'FAIL' if errors else 'PASS - nominal reservation checks; hardware seating/tolerances NOT RUN','errors':errors,'supports':supports,'jack_seam_carrier':carrier,'factory_load_power_pads':powerpads,'datum_table':datum,
            'panel':{'thickness_mm':2,'front_support_drill_count':0,'method':'PROPOSAL segmented perimeter clips within the 0..3 mm border only where clear of hardware and internal support collars; no continuous solid lip or selected clip profile. Side fasteners enter the enclosure. No internal 35-post holes in front artwork. #37 checks projected border conflicts; installed clip fit remains NOT RUN #65.'},
            'K_rear':{'face_z_mm':-100,'back_face_z_mm':-101.6,'component_height_ceiling_mm':5,'enclosure_inside_depth_mm':120,'nominal_back_component_clearance_mm':13.4,'status':'PROPOSAL, actual sourced component solids/case coupon NOT RUN #65'},
            'load_cases':{'jack_insertion_N':30,'knob_lateral_N':10,'knob_torque_Nm':.2,'button_press_N':5,'harness_pull_N':5,'transport_acceleration_g':10,'status':'PROPOSAL test requirements; no strength PASS'},
            'load_paths':['J bushings and exact nuts react plug insertion into the panel; proposed segmented enclosure clips capture the panel only at clear perimeter positions. Edge board posts support PCB mass only.','P insulating body carrier captures bushingless pots and B3F bodies; toggle bushings react operation into panel. Side rails transfer carrier loads to enclosure, not PCB solder.','EL 35 front collars/Ø2 posts terminate in the P/body carrier; 30 internal P clearance holes, five top posts outside P outline. Factory local backing supports GH mating.','K eight edge M2 posts fasten to enclosure rear/side frame; service hooks through 191 Ø2.2 apertures before K removal.','All wire combs/strain relief anchored to the enclosure carrier, never to connector latch/solder pads.'],
            'open':['#65 all main support stiffness, seating, tolerances, threaded engagement, exact fastener order codes and factory service tools','#55 selector assembly coupon','#57 source inlet and delivered-current realization','#59 return integrity/partial power/powered-off signal protection','#64 optical hot qualification','#37 panel perimeter artwork/hole review']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();r=build();text=dumps(r)+'\n'
    if a.check:
        if not OUT.exists() or OUT.read_text()!=text:raise SystemExit('mechanical report drift')
    else:OUT.write_text(text)
    print(r['status'],len(r['supports']),'support/pass-through locations')
    if r['errors']:raise SystemExit('\n'.join(r['errors']))

if __name__=='__main__':main()
