"""Incomplete FH12 recommended-land fixtures, only in a fresh ignored directory."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SOURCE=Path(__file__).with_name('source.json')
COUNTS=(8,14,26,40)
LABEL='INCOMPLETE_NOT_FOR_LAYOUT; NO_ADOPTION'
DESCRIPTION=LABEL+'; recommended lands only; no body, courtyard, 3D or endpoint binding'
PDF_SHA='c3257beed2331e5c95e176bc28441b04b804301a44c11b462e486fb5cc649d07'


def verify_source(root=ROOT):
    source=json.loads(SOURCE.read_text())
    if source['pdf_sha256']!=PDF_SHA or source['status']!=LABEL:
        raise ValueError('source identity/scope changed')
    for path,pin in source['sha256'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=pin:raise ValueError('source pin changed: '+path)
    if source['dimensions']!={'pitch':'0.5','pad_width':'0.3','pad_length':'1.3','pad_tab_gap':'1.5','tab_length':'2.2'}:
        raise ValueError('nominal recommended land dimensions changed')
    return source


def footprint_name(count):
    if count not in COUNTS:raise ValueError('exact selected contact count required')
    return f'INCOMPLETE_FH12_{count}S_0_5SH55_LAND_ONLY'


def pads(count):
    footprint_name(count)
    D=Decimal;A=D('.5')*(count-1);F=A+2;G=A+D('5.6')
    output=[{'number':str(i+1),'xy_mm':[str(-A/2+D('.5')*i),'0'],
             'size_mm':['0.3','1.3'],'role':'signal_land'} for i in range(count)]
    tab_width=(G-F)/2;tab_x=(G+F)/4;tab_y=D('1.3')/2+D('1.5')+D('2.2')/2
    for sign in (-1,1):output.append({'number':'','xy_mm':[str(sign*tab_x),str(tab_y)],
                                    'size_mm':[str(tab_width),'2.2'],'role':'unnumbered_mounting_land'})
    return output


def render(count):
    name=footprint_name(count)
    lines=[f'(footprint "{name}"','  (version 20241229)','  (generator "mc02_fh12_land_fixture")',
           '  (layer "F.Cu")',f'  (descr "{DESCRIPTION}")',
           '  (attr smd exclude_from_pos_files exclude_from_bom)']
    for pad in pads(count):
        x,y=pad['xy_mm'];w,h=pad['size_mm'];number=pad['number']
        lines.append(f'  (pad "{number}" smd rect (at {x} {y}) (size {w} {h}) (layers "F.Cu"))')
    return '\n'.join(lines+[')'])+'\n'


def safe_target(target,root=ROOT):
    target=Path(target);cache=root/'.circuit-cache'
    if cache.is_symlink() or not target.resolve().is_relative_to(cache.resolve()):
        raise ValueError('fixture must be inside the real ignored cache')
    if target.exists() or target.is_symlink():raise ValueError('fixture output must be fresh')
    return target


def generate(target,root=ROOT):
    source=verify_source(root)
    target=safe_target(target,root)
    target.mkdir(parents=True,exist_ok=False)  # exclusive ownership before output
    library=target/'INCOMPLETE_LAND_ONLY.pretty';library.mkdir()
    records=[]
    for count in COUNTS:
        path=library/(footprint_name(count)+'.kicad_mod');text=render(count);path.write_text(text)
        records.append({'contacts':count,'name':footprint_name(count),'path':str(path.relative_to(target)),
                        'sha256':hashlib.sha256(text.encode()).hexdigest(),'pads':pads(count)})
    receipt={'status':LABEL,'source':source,'source_spec_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'native_checker_sha256':hashlib.sha256(Path(__file__).with_name('native_check.py').read_bytes()).hexdigest(),
             'library':'INCOMPLETE_LAND_ONLY.pretty','footprints':records,
             'native_validation':'NOT_RUN','actual_project_registration':None,'endpoint_bindings':[]}
    (target/'fixture.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def verify_fixture(target,root=ROOT):
    target=Path(target);cache=root/'.circuit-cache'
    if cache.is_symlink() or not target.resolve().is_relative_to(cache.resolve()):raise ValueError('not an ignored fixture')
    source=verify_source(root);receipt=json.loads((target/'fixture.json').read_text())
    if receipt['source']!=source or receipt['source_spec_sha256']!=hashlib.sha256(SOURCE.read_bytes()).hexdigest():
        raise ValueError('fixture provenance changed')
    if (receipt['generator_sha256']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            or receipt['native_checker_sha256']!=hashlib.sha256(Path(__file__).with_name('native_check.py').read_bytes()).hexdigest()):
        raise ValueError('fixture generator/checker provenance changed')
    if receipt['status']!=LABEL or receipt['native_validation']!='NOT_RUN' or receipt['endpoint_bindings'] or receipt['actual_project_registration'] is not None:
        raise ValueError('fixture was promoted or bound to project endpoints')
    if receipt['library']!='INCOMPLETE_LAND_ONLY.pretty' or len(receipt['footprints'])!=4:
        raise ValueError('fixture inventory changed')
    for count,record in zip(COUNTS,receipt['footprints']):
        expected_path='INCOMPLETE_LAND_ONLY.pretty/'+footprint_name(count)+'.kicad_mod'
        if record['contacts']!=count or record['name']!=footprint_name(count) or record['path']!=expected_path or record['pads']!=pads(count):
            raise ValueError('fixture geometry/identity changed')
        expected=render(count).encode();path=target/expected_path
        if path.is_symlink() or path.read_bytes()!=expected or record['sha256']!=hashlib.sha256(expected).hexdigest():
            raise ValueError('fixture bytes changed')
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    print(json.dumps(generate(args.output_dir),indent=2))


if __name__=='__main__':main()
