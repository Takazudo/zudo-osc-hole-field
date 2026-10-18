import cadquery as cq,json,sys
from pathlib import Path
out={}
for n in [8,10,14]:
 stem=f'612{n:03d}';folder=Path('.circuit-cache/sources/practical-idc-layout' if n==14 else '.circuit-cache/sources/hybrid-service-layout')
 hs=cq.importers.importStep(str(folder/(stem+'21621.stp'))).val().Solids(); ss=cq.importers.importStep(str(folder/(stem+'23021.stp'))).val().Solids();h=max(hs,key=lambda s:s.Volume());s=ss[0]
 turns={}
 for axis in [(1,0,0),(0,1,0)]:
  q=s.rotate((0,0,0),axis,180).translate((0,0,4.925));turns[str(axis)]=round(h.intersect(q).Volume(),8)
 # Rejected inference preserved: Closed cap drawing6.9: from matingface nativez7 -> capouterz.1, suppliedcapzmin-3.7 =>shift+3.8.
 cap=ss[1].translate((0,0,3.8));posed=[t.rotate((0,0,0),(0,1,0),180).translate((0,0,4.925)) for t in [s,cap]]
 out[str(n)]={'native_header_seat_z':-4.675,'native_header_floor_z':-2.075,'native_socket_face_z':7,'native_key_fit_plastic_intersection_mm3':turns,'REJECTED_naive_cap_translation_native_z':3.8,'REJECTED_naive_closed_height_mm':round(max(q.BoundingBox().zmax for q in posed)+4.675,8),'closed_body_cap_intersection_mm3':round(s.intersect(cap).Volume(),8),'closure_status':'UNRESOLVED_NAIVE_TRANSLATION_INTERSECTS_BODY','supplied_open_mated_envelope_mm':18.3,'nominal_mated_socket_body_height_mm':9.6,'relief_closed_transform':None,'relief_installed_height':None,'socket_raw_solids':[[round(v,5) for v in [q.BoundingBox().xmin,q.BoundingBox().ymin,q.BoundingBox().zmin,q.BoundingBox().xmax,q.BoundingBox().ymax,q.BoundingBox().zmax]] for q in ss[:3]]}
print(json.dumps(out,indent=2))
dest=Path(__file__).with_name('cad-report.json');payload=json.dumps(out,indent=2)+'\n'
if '--check' in sys.argv:
 if dest.read_text()!=payload:raise SystemExit('STALE cad-report')
else:dest.write_text(payload)
