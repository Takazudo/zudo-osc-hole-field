#!/usr/bin/env python3
"""Write issue-15 CAD receipts and capture-grade pin maps from retained inputs."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/libgen'))
from gen_courtyards import parse,walk,node_name
SOURCE=ROOT/'circuit/sources/ic-library'
LIB='zudo-osc-hole-field'
FP=ROOT/'footprints/kicad'/f'{LIB}.pretty'
PINMAP=ROOT/'design/standard/pin-maps';PINMAP.mkdir(parents=True,exist_ok=True)
RECEIPTS=ROOT/'circuit/cad-receipts'
SHORTLIST={p['id']:p for p in json.loads((ROOT/'design/standard/parts-shortlist.json').read_text())['parts']}
PARTS={
'op_audio':('OPA4196IDR','OPA4196',3,'4'),
'op_precision':('OPA4197IPWR','OPA4197',3,'4'),
'fault_switch':('ADG5412FBRUZ','ADG5412F',12,'13'),
'comparator':('LM393BIDR','LM393B',2,'3'),
'schmitt':('SN74HC14DR','SN74HC14',2,'3'),
'flipflop':('SN74HC74DR','SN74HC74',2,'3'),
'nand':('SN74HC00DR','SN74HC00',2,'3'),
'one_shot':('CD74HC221M96','CD74HC221',0,'1'),
'ota':('LM13700M_NOPB','LM13700',2,'3'),
'sample_hold':('LF398M_NOPB','LF398',2,'3'),
'vco':('AS3340D',None,None,None),
'noise':('NOISE2','NOISE2',1,'2'),
'reference':('REF5050AIDR','REF5050',3,'4'),
'regulator_3v3':('TLV75533PDBVR','TLV755P',2,'3'),
'clamp_diode':('BAT54S_215','BAT54S',0,'1'),
'npn':('MMBT3904_215','MMBT3904',0,'1'),
'pnp':('MMBT3906_215','MMBT3906',0,'1'),
'mosfet':('2N7002_215','2N7002',0,'1'),
'matched_npn':('BCM847BS_115','BCM847BS',1,'2'),
 'trim_102':('TC33X-2-102E','TC33X',0,'unlabeled'),
 'trim_103':('TC33X-2-103E','TC33X',0,'unlabeled'),
 'r_general':('RC0603FR-07100KL','RC0603FR',0,'unlabeled'),
 'r_precision':('RT0603BRD07100KL','RT0603BRD',0,'unlabeled'),
 'r_ladder':('TNPW080510K0BEEA','TNPW0805',0,'1'),
 'r_power':('RC1210FR-07499RL','RC1210FR',0,'unlabeled'),
 'c_bypass':('GRM188R71H104KA93D',None,None,None),
 'c_bulk':('GRM21BR61E475KA12L',None,None,None),
 'c_small':('C0603C101J5GACTU','C0603C101',0,'unlabeled'),
 'c_hold':('C0805C103J5GACTU','C0805C103',0,'unlabeled'),
 'c_slew':('1206CG104J500NT','1206CG104J500NT',0,'unlabeled'),
}
URLS={
 'OPA4196':'https://www.ti.com/lit/ds/symlink/opa4196.pdf','OPA4197':'https://www.ti.com/lit/ds/symlink/opa4197.pdf',
 'ADG5412F':'https://www.analog.com/media/en/technical-documentation/data-sheets/adg5412f_5413f.pdf',
 'LM393B':'https://www.ti.com/lit/ds/symlink/lm393b.pdf','SN74HC14':'https://www.ti.com/lit/ds/symlink/sn74hc14.pdf',
 'SN74HC74':'https://www.ti.com/lit/ds/symlink/sn74hc74.pdf','SN74HC00':'https://www.ti.com/lit/ds/symlink/sn74hc00.pdf',
 'CD74HC221':'https://www.ti.com/lit/ds/symlink/cd74hc221.pdf','LM13700':'https://www.ti.com/lit/ds/symlink/lm13700.pdf',
 'LF398':'https://www.ti.com/lit/ds/symlink/lf398-n.pdf','NOISE2':'https://electricdruid.net/datasheets/NOISE2Datasheet.pdf',
 'REF5050':'https://www.ti.com/lit/ds/symlink/ref50.pdf','TLV755P':'https://www.ti.com/lit/ds/symlink/tlv755p.pdf',
 'BAT54S':'https://assets.nexperia.com/documents/data-sheet/BAT54S.pdf','MMBT3904':'https://assets.nexperia.com/documents/data-sheet/MMBT3904.pdf',
 'MMBT3906':'https://assets.nexperia.com/documents/data-sheet/MMBT3906.pdf','2N7002':'https://assets.nexperia.com/documents/data-sheet/2N7002.pdf',
 'BCM847BS':'https://assets.nexperia.com/documents/data-sheet/BCM847BS.pdf',
 'TC33X':'https://www.bourns.com/docs/product-datasheets/tc33.pdf',
 'RC0603FR':'https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-07100KL',
 'RT0603BRD':'https://www.yageogroup.com/component-documentation/download/specsheet/RT0603BRD07100KL',
 'RC1210FR':'https://www.yageogroup.com/component-documentation/download/specsheet/RC1210FR-07499RL',
 'TNPW0805':'https://www.vishay.com/docs/28758/tnpw_e3.pdf',
 'C0603C101':'https://search.kemet.com/download/specsheet/C0603C101J5GACTU',
 'C0805C103':'https://search.kemet.com/download/specsheet/C0805C103J5GACTU',
 '1206CG104J500NT':'https://web-static.partgenie.ai/component/docs/24814d3406042d9d5b5483a096d4df41_2304140030_FH--Guangdong-Fenghua-Advanced-Tech-1206CG104J500NT_C46348.pdf',
}
FUNCTION_OVERRIDES={
'op_audio':dict(zip(map(str,range(1,15)),['OUT A','IN- A','IN+ A','V+','IN+ B','IN- B','OUT B','OUT C','IN- C','IN+ C','V-','IN+ D','IN- D','OUT D'])),
'op_precision':dict(zip(map(str,range(1,15)),['OUT A','IN- A','IN+ A','V+','IN+ B','IN- B','OUT B','OUT C','IN- C','IN+ C','V-','IN+ D','IN- D','OUT D'])),
'fault_switch':dict(zip(map(str,range(1,17)),['IN1 logic','D1 drain','S1 protected source','VSS negative supply','GND reference','S4 protected source','D4 drain','IN4 logic','IN3 logic','D3 drain','S3 protected source','FF fault flag, high normal/low fault','VDD positive supply','S2 protected source','D2 drain','IN2 logic'])),
'comparator':dict(zip(map(str,range(1,9)),['1OUT open collector','1IN-','1IN+','GND','2IN+','2IN-','2OUT open collector','VCC'])),
'schmitt':dict(zip(map(str,range(1,15)),['1A input','1Y output','2A input','2Y output','3A input','3Y output','GND','4Y output','4A input','5Y output','5A input','6Y output','6A input','VCC'])),
'flipflop':dict(zip(map(str,range(1,15)),['1CLR active low','1D data','1CLK rising edge','1PRE active low','1Q','1Q inverted','GND','2Q inverted','2Q','2PRE active low','2CLK rising edge','2D data','2CLR active low','VCC'])),
'nand':dict(zip(map(str,range(1,15)),['1A input','1B input','1Y NAND output','2A input','2B input','2Y NAND output','GND','3Y NAND output','3A input','3B input','4Y NAND output','4A input','4B input','VCC'])),
'ota':dict(zip(map(str,range(1,17)),['amplifier 1 bias','diode 1 bias','input 1+','input 1-','unbuffered output 1','V-','buffer input 1','buffer output 1','buffer output 2','buffer input 2','V+','unbuffered output 2','input 2-','input 2+','diode 2 bias','amplifier 2 bias'])),
'sample_hold':dict(zip(map(str,range(1,15)),['analog input','NC','V-','NC','NC','NC','output','hold capacitor','NC','logic reference','logic input','V+','NC','offset adjust'])),
'one_shot':dict(zip(map(str,range(1,17)),['1A trailing-edge trigger','1B leading-edge trigger','1R active-low reset','1Q','2Q inverted','2CX timing capacitor','2RXCX timing resistor/capacitor','GND','2A trailing-edge trigger','2B leading-edge trigger','2R active-low reset','2Q','1Q inverted','1CX timing capacitor','1RXCX timing resistor/capacitor','VCC'])),
'noise':dict(zip(map(str,range(1,9)),['+5V supply','unused digital input','white digital output','unused digital input','unused digital input','unused digital input','pink analog output','0V supply'])),
'clamp_diode':{'1':'A1 anode diode 1','2':'K2 cathode diode 2','3':'K1/A2 series common'},
}
ZERO='0'*64
def rel(p):return p.relative_to(ROOT).as_posix()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def child(node,name):return next((x for x in node if isinstance(x,list) and node_name(x)==name),None)
def prop(tree,name):
 for x in tree:
  if isinstance(x,list) and node_name(x)=='property' and x[1]==name:return x[2]
 raise ValueError((tree[1],name))
def symbol_info(path):
 tree=parse(path.read_text());sym=child(tree,'symbol');pins={}
 for u in sym:
  if not isinstance(u,list) or node_name(u)!='symbol':continue
  for x in walk(u):
   if node_name(x)=='pin':
    n=child(x,'number')[1];nm=child(x,'name')[1]
    if n not in pins or (not pins[n] and nm):pins[n]=nm
 return sym,pins
def footprint_pads(path):return {x[1] for x in walk(parse(path.read_text())) if node_name(x)=='pad'}
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
for id,(name,source_name,page,label) in PARTS.items():
 part=SHORTLIST[id];sym_path=ROOT/'symbols/src'/(name+'.kicad_sym');sym,pins=symbol_info(sym_path)
 footprint=prop(sym,'Footprint').split(':',1)[1];fp_path=FP/(footprint+'.kicad_mod');pads=footprint_pads(fp_path)
 if set(pins)!=pads:raise ValueError(f'{id}: symbol {set(pins)} differs from pads {pads}')
 source_path=SOURCE/(source_name+'.pdf') if source_name else None
 source_available=bool(source_path and source_path.is_file())
 source_status='AVAILABLE' if source_available else 'SOURCE UNAVAILABLE'
 if id=='c_slew':source_status='FAMILY SOURCE ONLY - exact MPN not located in PDF'
 if id=='vco':source_url='http://www.alfarzpp.lv/ (manufacturer PDF location not recovered; mirrors do not establish primary bytes)'
 elif id=='c_bulk':source_url='https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM21BR61E475KA12-01A.pdf (HTTP 404 during retrieval)'
 elif id=='c_bypass':source_url='https://www.murata.com/ (exact manufacturer PDF not retrieved)'
 else:source_url=URLS[source_name]
 source={'availability':source_status,'authority':'MANUFACTURER_PRIMARY' if source_available and id!='c_slew' else 'UNVERIFIED','url':source_url,'retained_path':rel(source_path) if source_available else None,'sha256':sha(source_path) if source_available else ZERO,'physical_pdf_page_index':page if source_available else None,'printed_page_label':label if source_available else None,'locator':'Pin configuration/function table' if id not in ('trim_102','trim_103','r_general','r_precision','r_ladder','r_power','c_bypass','c_bulk','c_small','c_hold','c_slew') else 'Package/terminal drawing or exact-part specsheet'}
 if id=='c_slew':source['note']='Retained Fenghua high-voltage MLCC family PDF does not name 1206CG104J500NT; exact-part facts remain UNSOURCED.'
 rows=[]
 for n in sorted(pins,key=lambda x:int(x) if x.isdigit() else 999):
  function=FUNCTION_OVERRIDES.get(id,{}).get(n) or pins[n] or ('unpolarized terminal' if id.startswith(('r_','c_')) else 'output or passive terminal per manufacturer pin diagram')
  rows.append({'datasheet_pin':n,'function':function,'symbol_pin':n,'footprint_pad':n,'source_locator':f"{source.get('retained_path') or source_url}, physical PDF p.{page}, printed p.{label}, {source['locator']}" if source_available else 'SOURCE UNAVAILABLE; no manufacturer page locator','verdict':'UNSOURCED' if source_status!='AVAILABLE' else 'DRAFT - source-backed pin identity; board net unassigned'})
 pinmap={'schema_version':1,'role_id':id,'identity':{'manufacturer':part['manufacturer'],'mpn':part['mpn'],'lcsc':part.get('lcsc',''),'status':'draft selected part'},'cad':{'symbol':f'{LIB}:{name}','footprint':f'{LIB}:{footprint}'},'source':source,'pins':rows,'nets':'Unassigned; no schematic or placement binding is claimed.'}
 write(PINMAP/(id+'.json'),pinmap)
 # One receipt per new symbol. Sources are retained stock expressions and manufacturer PDF where available.
 stock=SOURCE/'cad'/(name+'.stock.kicad_sympart');parent=SOURCE/'cad'/(name+'.parent.kicad_sympart')
 inputs=[p for p in (stock,parent,source_path) if p and p.is_file()]
 if not inputs:inputs=[ROOT/'scripts/libgen/fixtures'/('build_passive_symbols.py' if id.startswith(('r_','c_','trim_')) else 'build_ic_custom.py')]
 hashes={rel(p):sha(p) for p in inputs}
 provider='KiCad 10 stock symbol and retained manufacturer/creator document' if stock and source_available else 'KiCad 10 stock symbol; manufacturer document unavailable' if stock else 'Issue 15 symbol generator and retained source' if source_available else 'Issue 15 symbol generator; exact manufacturer document unavailable'
 receipt={'receipt_version':1,'identity':{'asset_id':'ic15-'+id,'record_id':None,'manufacturer':part['manufacturer'],'mpn':part['mpn'],'package':part['package'],'variant_notes':source_status},'acquisition':{'provider':provider,'source_url':source_url,'acquired_on':'2026-09-28','original_filenames':[p.name for p in inputs],'sha256':hashes},'representation':{'files':[rel(sym_path)],'formats':['kicad_sym'],'units':'KiCad schematic units','original_paths':list(hashes)},'fidelity':{'class':'derived','reason':'Stock pin graphics or custom unit layout normalized for the exact draft identity; unsupported manufacturer facts remain UNSOURCED.' if not source_available else 'Source pin functions audited against the retained document; KiCad stock or custom graphics normalized for this draft identity.','evidence':[source_status,source_url]},'derivation':{'derived':True,'input_sha256':hashes,'tool':'scripts/libgen/fixtures/build_ic_assets.py, build_ic_custom.py, or build_passive_symbols.py','tool_version':'1','parameters':{'normalization':'exact MPN/manufacturer/LCSC fields, local footprint reference; alias parent units expanded where required'},'output_sha256':{rel(sym_path):sha(sym_path)}},'cad_use':{'symbol':f'{LIB}:{name}','footprint':f'{LIB}:{footprint}','model_path':None,'transform':{'offset':None,'rotation':None,'scale':None},'seating_plane':None},'checks':{'performed':['Issue-15 all-unit KiCad 10 ERC fixture and project library checker'],'remaining_physical_checks':['Confirm exact package drawing/lot, actual circuit net mapping, electrical suitability and procurement before board release.']},'publication':{'preview_selected':False,'download_published':False,'permitted_scope':None}}
 write(RECEIPTS/('ic15-'+id+'.receipt.json'),receipt)
 print('pinmap/receipt',id,len(rows),source_status)
# Footprint receipts for each newly imported generic package.
for stock in sorted((SOURCE/'cad').glob('*.stock.kicad_mod')):
 name=stock.name.removesuffix('.stock.kicad_mod');out=FP/(name+'.kicad_mod')
 orig=rel(stock);dest=rel(out);h={orig:sha(stock)}
 receipt={'receipt_version':1,'identity':{'asset_id':'ic15-footprint-'+name.lower().replace('_','-'),'record_id':None,'manufacturer':None,'mpn':None,'package':name,'variant_notes':'Generic KiCad 10 package footprint, not exact vendor land-pattern qualification.'},'acquisition':{'provider':'KiCad 10.0.6 stock library','source_url':'KiCad 10.0.6 pinned oracle, scripts/kicad/run.sh','acquired_on':'2026-09-28','original_filenames':[stock.name],'sha256':h},'representation':{'files':[dest],'formats':['kicad_mod'],'units':'mm','original_paths':[orig]},'fidelity':{'class':'family','reason':'Generic package source; device-specific package dimensions and reflow rules require checking against the exact manufacturer drawing.','evidence':['KiCad 10.0.6 pinned stock library source retained with SHA-256.']},'derivation':{'derived':True,'input_sha256':h,'tool':'scripts/libgen/fixtures/import_ic_stock.py and build_ic_assets.py; scripts/libgen/gen_courtyards.py','tool_version':'1','parameters':{'operations':['set project footprint name','remove stock 3D model reference','generate project courtyard']},'output_sha256':{dest:sha(out)}},'cad_use':{'symbol':None,'footprint':f'{LIB}:{name}','model_path':None,'transform':{'offset':None,'rotation':None,'scale':None},'seating_plane':None},'checks':{'performed':['Project library and courtyard checks'],'remaining_physical_checks':['Audit against exact package drawing before fabrication.']},'publication':{'preview_selected':False,'download_published':False,'permitted_scope':None}}
 write(RECEIPTS/(receipt['identity']['asset_id']+'.receipt.json'),receipt)
 print('footprint receipt',name)
