"""Source-verified representative footprint fields; original units stay intact."""
import hashlib
from pathlib import Path
from scripts.pcbgen.netlist import TOKEN,parse,many,one,read_netlist


def native_field_projection(netlist):
    """Keep native `(fields ...)` separate from exporter `(property ...)`.

    KiCad parity compares COMPONENT.GetFields(), while DNP/BOM uses properties.
    The existing shared reader and layout/current metadata meanings are intact.
    """
    content=Path(netlist).read_bytes();root,_=parse(TOKEN.findall(content.decode()))
    components,_=read_netlist(Path(netlist));by_ref={c.ref:c for c in components};rows=[]
    for component in many(one(root,'components'),'comp'):
        ref=one(component,'ref')[1]
        if ref not in by_ref:continue
        fields={}
        for entry in many(one(component,'fields'),'field'):
            name=one(entry,'name')[1]
            if name in fields or len(entry) not in (2,3) or (len(entry)==3 and not isinstance(entry[2],str)):
                raise ValueError('malformed or duplicate native component field')
            fields[name]=entry[2] if len(entry)==3 else ''
        properties=dict(by_ref[ref].fields)
        for name in ('BoardSide','FootprintOriginMm','KiCadOrientationDeg','BoardAssignment','BoardRegion'):
            if name in fields and fields[name]!=properties.get(name):
                raise ValueError('native field projection changes physical source metadata: '+ref+':'+name)
        rows.append({'ref':ref,'native_fields':fields,'source_properties':properties})
    if len(rows)!=len(by_ref) or len({r['ref'] for r in rows})!=len(rows):raise ValueError('native field projection package inventory mismatch')
    all_units=[];sheet_hashes={}
    sheets={dict(c.fields)['Sheetfile'] for c in components}
    for sheet in sorted(sheets):
        path=Path('boards/osc-core')/sheet;data=path.read_bytes()
        sheet_hashes[str(path)]=hashlib.sha256(data).hexdigest()
        schematic,_=parse(TOKEN.findall(data.decode()))
        for symbol in many(schematic,'symbol'):
            fields={p[1]:p[2] for p in many(symbol,'property')};ref=fields.get('Reference')
            if ref not in by_ref:continue
            sheetname=by_ref[ref].sheetname.rstrip('/').rsplit('/',1)[-1]
            all_units.append({'ref':ref,'unit':one(symbol,'unit')[1],'uuid':one(symbol,'uuid')[1],'source':str(path),
                'original_fields':fields,'resolved_fields':{k:v.replace('${SHEETNAME}',sheetname) for k,v in fields.items()}})
    for row in rows:
        matches=[u for u in all_units if u['ref']==row['ref']]
        if not matches:raise ValueError('native field package lacks original schematic units')
        for name in ('Role','LogicalCellKey','Island'):
            if name in row['native_fields'] and not any(u['resolved_fields'].get(name)==row['native_fields'][name] for u in matches):
                raise ValueError('native representative field lacks an original source unit: '+row['ref']+':'+name)
    return {'netlist_sha256':hashlib.sha256(content).hexdigest(),'packages':rows,'all_original_source_units':all_units,
        'source_sheet_sha256':sheet_hashes,
        'scope':'Pinned exported native fields authority for PCB parity only; separate properties and all per-unit original fields retained. Absent and explicitly empty fields remain distinct.'}


def apply_native_fields(board,projected):
    footprints=list(board.GetFootprints());by_ref={f.GetReference():f for f in footprints}
    if len(footprints)!=len(by_ref):raise ValueError('duplicate native footprint reference')
    for row in projected['packages']:
        fp=by_ref[row['ref']]
        for name,value in row['native_fields'].items():
            if name in ('Reference','Value','Footprint','Component Class'):continue
            fp.SetField(name,value);fp.GetField(name).SetVisible(False)


def projection(audit,netlist):
    if hashlib.sha256(Path(netlist).read_bytes()).hexdigest()!=audit['netlist_sha256']:
        raise ValueError('K package field netlist is stale')
    components,_=read_netlist(Path(netlist));packages={p.ref:p for p in components}
    records=[r for r in audit['parity_records'] if 'field' in r]
    refs={r['ref'] for r in records};units={};retained=[]
    for name,expected in audit['source_sheet_sha256'].items():
        content=Path(name).read_bytes()
        if hashlib.sha256(content).hexdigest()!=expected:raise ValueError('K package field source sheet changed')
        root,_=parse(TOKEN.findall(content.decode()))
        for symbol in many(root,'symbol'):
            fields={p[1]:p[2] for p in many(symbol,'property')};ref=fields.get('Reference')
            if ref not in refs:continue
            unit=one(symbol,'unit')[1];uid=one(symbol,'uuid')[1]
            sheetname=packages[ref].sheetname.rstrip('/').rsplit('/',1)[-1]
            values={k:v.replace('${SHEETNAME}',sheetname) for k,v in fields.items()}
            row={'ref':ref,'unit':unit,'uuid':uid,'source':name,
                 'original_fields':fields,'resolved_fields':values}
            units[name,uid]=row;retained.append(row)
    selected=[]
    for row in records:
        if row['field'] not in ('Role','LogicalCellKey','Island'):raise ValueError('unexpected K representative field')
        matches=[]
        for identity in row['matching_source_units']:
            unit=units[identity['source'],identity['uuid']]
            if unit['ref']!=row['ref'] or unit['unit']!=identity['unit'] or unit['resolved_fields'].get(row['field'])!=row['expected_source_value']:
                raise ValueError('representative value does not match exact source unit')
            matches.append(identity)
        if not matches:raise ValueError('representative field lacks source unit')
        selected.append({k:row[k] for k in ('ref','field','pcb_value','expected_source_value','footprint_uuid')})
    if len({(r['ref'],r['field']) for r in selected})!=len(selected):raise ValueError('duplicate K representative field')
    return {'representatives':selected,'all_original_source_units':retained,
        'scope':'Native footprint representative metadata only. Every original schematic unit and its electrical pins/nets is unchanged; complete unit metadata retained here.'}
