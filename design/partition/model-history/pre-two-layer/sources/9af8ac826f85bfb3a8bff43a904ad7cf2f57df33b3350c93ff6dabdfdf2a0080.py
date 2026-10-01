"""Source-field projection for a named disposable prerequisite board.

The historical K implementation stays byte-stable for its retained native
authority. This parameterized successor uses immutable netlist bytes and an
explicit sheet root, while preserving the two metadata namespaces.
"""
import hashlib
from pathlib import Path
import tempfile
from scripts.pcbgen.netlist import TOKEN,parse,many,one,read_netlist
from scripts.pcbgen.core_package_fields import apply_native_fields


def project(netlist,sheet_root):
    netlist=Path(netlist);sheet_root=Path(sheet_root).resolve();data=netlist.read_bytes()
    root,end=parse(TOKEN.findall(data.decode()))
    with tempfile.TemporaryDirectory(prefix='prerequisite-netlist-') as directory:
        snapshot=Path(directory)/'source.net';snapshot.write_bytes(data)
        components,_=read_netlist(snapshot)
    by_ref={c.ref:c for c in components};rows=[]
    for component in many(one(root,'components'),'comp'):
        ref=one(component,'ref')[1]
        if ref not in by_ref:continue
        fields={}
        for field in many(one(component,'fields'),'field'):
            name=one(field,'name')[1]
            if name in fields or len(field) not in (2,3) or (len(field)==3 and not isinstance(field[2],str)):
                raise ValueError('malformed or duplicate native component field')
            fields[name]=field[2] if len(field)==3 else ''
        properties=dict(by_ref[ref].fields)
        for name in ('BoardSide','FootprintOriginMm','KiCadOrientationDeg','BoardAssignment','BoardRegion'):
            if name in fields and fields[name]!=properties.get(name):
                raise ValueError('native field projection changes physical source metadata: '+ref+':'+name)
        rows.append({'ref':ref,'native_fields':fields,'source_properties':properties})
    if len(rows)!=len(by_ref) or len({r['ref'] for r in rows})!=len(rows):
        raise ValueError('complete native field package inventory required')
    units=[];hashes={}
    for sheet in sorted({dict(c.fields)['Sheetfile'] for c in components}):
        path=(sheet_root/sheet).resolve()
        if not path.is_relative_to(sheet_root):raise ValueError('source sheet escapes its explicit board root')
        raw=path.read_bytes();hashes[str(path)]=hashlib.sha256(raw).hexdigest()
        schematic,_=parse(TOKEN.findall(raw.decode()))
        for symbol in many(schematic,'symbol'):
            fields={p[1]:p[2] for p in many(symbol,'property')};ref=fields.get('Reference')
            if ref not in by_ref:continue
            sheetname=by_ref[ref].sheetname.rstrip('/').rsplit('/',1)[-1]
            units.append({'ref':ref,'unit':one(symbol,'unit')[1],'uuid':one(symbol,'uuid')[1],
                'source':str(path),'original_fields':fields,
                'resolved_fields':{k:v.replace('${SHEETNAME}',sheetname) for k,v in fields.items()}})
    for row in rows:
        matches=[u for u in units if u['ref']==row['ref']]
        if not matches:raise ValueError('native field package lacks original schematic units')
        for name in ('Role','LogicalCellKey','Island'):
            if name in row['native_fields'] and not any(u['resolved_fields'].get(name)==row['native_fields'][name] for u in matches):
                raise ValueError('native field lacks original per-unit source support: '+row['ref']+':'+name)
    if netlist.read_bytes()!=data or any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):
        raise ValueError('prerequisite metadata source changed during projection')
    return {'netlist_sha256':hashlib.sha256(data).hexdigest(),'packages':rows,
        'all_original_source_units':units,'source_sheet_sha256':hashes,
        'scope':'Exact native fields for parity, independent original properties/markers and all per-unit source semantics retained; no layout/pin/net rewrite.'}
