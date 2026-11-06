"""Propose real-control verification after owner intended-use decision; preserve historical evidence."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import stage15_procedure as previous
import stage11_assessment as common
ROOT=common.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage15-detent'
BASE='c142e1120da1cfe66e809b83fbcb6698c204a341'
need=common.need

def preserve():
    scope=json.loads((OUT/'scope.json').read_text())
    names=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,*common.PREFIXES],cwd=ROOT,text=True).splitlines())-common.MUTABLE
    need(scope['baseline_commit']==BASE and set(scope['preserved_prior_source_sha256'])==names,'historical inventory')
    for name,sha in scope['preserved_prior_source_sha256'].items():
        need(common.digest(ROOT/name)==sha==hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest(),'preserved '+name)
    return len(names)

def predecessor():
    preserve()
    need((previous.OUT/'procedure-report.json').read_text()==json.dumps(previous.build(),sort_keys=True,indent=2,allow_nan=False)+'\n','historical interpretation report')
    for role in ('root','code','electrical'):
        r=json.loads((previous.OUT/('review-'+role+'.json')).read_text())
        need(r.get('independent_review') and r.get('authorship_exclusion'),'historical review authorship')
        for name,sha in r['source_sha256'].items():
            actual=hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest() if name in common.MUTABLE else common.digest(ROOT/name)
            need(actual==sha,'historical review binding '+name)

def analyze(standard,shortlist,inventory,evidence):
    binding=next(p for p in standard['pot_bindings'] if p['panel_uid']=='C:A01.OFFSET')
    part=next(p for p in shortlist['parts'] if p['id']==binding['part_id'])
    package=inventory['packages']['RV1308']
    need(part['manufacturer']=='Bourns' and part['mpn']=='PTV09A-4020F-B104','exact selected OFFSET part')
    need(package['attributes']['MPN']==part['mpn'] and package['attributes']['PanelUid']=='C:A01.OFFSET','captured OFFSET BOM binding')
    fields=part['mpn'].split('-');configuration=fields[1]
    need(configuration=='4020F' and configuration[1]=='0','selected no-detent ordering option')
    need(evidence['option_definitions']=={'0':'No Detent','2':'Center'},'manufacturer order option meanings')
    need(evidence['document_sha256']=='411cdb6a62e61f9c5bc2df76ed64ee21d7bcfbee035c1ba36beff08c43f28558','exact inspected primary bytes')
    need(evidence['physical_pdf_page_index']==0 and evidence['visual_ordering_field_verified'],'primary ordering locator')
    need(evidence['required_centre_detent'] is False,'owner no-centre-click requirement')
    return {'manufacturer':part['manufacturer'],'selected_mpn':part['mpn'],'reference':'RV1308','panel_uid':binding['panel_uid'],
        'ordering_decode':{'terminal_configuration':configuration[0],'detent_option':configuration[1],'shaft_length_mm':int(configuration[2:4]),'shaft_style':configuration[4],'resistance_code':fields[2][1:]},
        'detent':'NONE','disposition':'RETAIN selected part; no alternative/substitution required',
        'owner_requirement':'Normal continuous rotary manual OFFSET with no centre detent/click.',
        'contract_addendum':{'manual_control':'Continuous rotation over normal potentiometer travel, no centre detent. End stops remain normal; not an endless encoder.',
            'centre_definition':'Centre in procedure means nominal angle/electrical test position, never tactile click or guaranteed zero. Establish desired baseline by ear/meter as intended use permits.',
            'factory_setup':'Keep prior declared Btarget/meter procedure. Do not locate zero by click or assume midpoint voltage. Record actual setting and approach direction.',
            'physical_receipt':'Future incoming/assembled inspection may confirm correct supplied option and smooth travel/no centre click; NOT RUN here, not a new component or electrical qualification.',
            'criteria':'Unchanged2mV postfactory static-path and1mV same-settingload; no knob-position voltageaccuracy requirement.'},
        'source_evidence':evidence,'component_geometry_changed':False,'hardware_acceptance':False,'native':'NOT RUN','CAD':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}

def build():
    count=preserve()
    files=[ROOT/'design/standard/electrical-standard.json',ROOT/'design/standard/parts-shortlist.json',ROOT/'design/architecture-278/implementation/stage10/inventory-report.json',OUT/'primary-evidence.json']
    r=analyze(*[json.loads(p.read_text()) for p in files])
    files += [OUT/'scope.json',ROOT/'.claude/skills/component-bourns-ptv09a-4020f-b104/manifest.json',ROOT/'.claude/skills/component-bourns-ptv09a-4020f-b104/sources.json',Path(__file__),Path(__file__).with_name('test_stage15_detent.py'),ROOT/'design/architecture-278/implementation/STAGE15-DETENT.md']
    r.update(baseline_commit=BASE,preserved_predecessor_files=count,source_sha256={str(p.relative_to(ROOT)):common.digest(p) for p in files})
    return r

def reviews():
    for role in ('code','electrical'):
        r=json.loads((OUT/('review-'+role+'.json')).read_text())
        need(r.get('independent_review') and r.get('authorship_exclusion'),'review authorship')
        common.bindings(r)
        need({'scripts/architecture278/implementation/stage15_detent.py','design/architecture-278/implementation/STAGE15-DETENT.md'}<=set(r['source_sha256']),'review coverage')

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--check-predecessor',action='store_true');args=p.parse_args()
    if args.check_predecessor:predecessor();print('PASS frozen procedure evidence; no-detent requirement recorded separately');return
    r=build();common.finite(r);common.acceptance(r);text=json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n';dest=OUT/'detent-report.json'
    if args.check:need(dest.read_text()==text,'stale detent report');reviews()
    else:dest.write_text(text)
    print('PASS exact manual OFFSET ordering option0: no detent; part retained')
if __name__=='__main__':main()
