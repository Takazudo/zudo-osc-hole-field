"""Dated JLC candidate sourcing; never apply selections or authorize assembly."""
import argparse
import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
REL = 'design/architecture-278/implementation/'
OUT = ROOT / REL / 'stage23'
BASE = '12a48ff5f7c771a1011c789c42d5e4dcb450c07d'
CODES = {
    'RT0603BRD0710KL': 'C95204', 'RT0603BRD0722KL': 'C469656',
    'RT0603BRD071KL': 'C110776', 'RT0603BRD07100RL': 'C122970',
    'RC0603FR-0710ML': 'C114606', 'RT0603BRD075K6L': 'C179095',
    'RT0603BRD0722K1L': 'C723484', 'C0603C100J5GACTU': 'C2167326',
    'C0603C103J5RACTU': 'C5360746',
}
KEYS = ('componentModelEn', 'componentCode', 'componentBrandEn',
        'componentSpecificationEn', 'componentLibraryType', 'assemblyComponentFlag',
        'assemblyMode', 'componentProductType', 'overseasStockCount',
        'canPresaleNumber', 'preMinPurchaseNum', 'encapsulationNumber',
        'lossNumber', 'leastPatchNumber', 'needAuditFlag', 'manufacturerBlackFlag')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def dump(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Visible(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def flight_frames(decoded):
    # Flight T records carry a UTF-8 byte length and need no trailing newline.
    data = decoded.encode('utf-8')
    frames = {}
    offset = 0
    while offset < len(data):
        match = re.match(rb'([0-9a-f]+):', data[offset:])
        need(match is not None, 'invalid flight record boundary')
        key = match[1].decode()
        offset += match.end()
        need(key not in frames, 'missing or duplicate product reference')
        text = re.match(rb'T([0-9a-f]+),', data[offset:])
        if text:
            offset += text.end()
            length = int(text[1], 16)
            need(offset+length <= len(data), 'truncated flight text')
            data[offset:offset+length].decode('utf-8')
            frames[key] = ''
            offset += length
        else:
            end = data.find(b'\n', offset)
            if end < 0:
                end = len(data)
            frames[key] = data[offset:end].decode('utf-8')
            offset = end+1
    return frames


def parse_jlc(html, mpn, code):
    # Next flight contains related products too: only componentInfo is authoritative here.
    blocks = re.findall(r'self\.__next_f\.push\((\[1,.*?\])\)</script>', html)
    decoded = ''.join(json.loads(block)[1] for block in blocks)
    decoder = json.JSONDecoder()
    frames = flight_frames(decoded)
    records = [decoder.raw_decode(body[m.end():].lstrip())[0]
               for body in frames.values() for m in re.finditer(r'"componentInfo":', body)]
    need(records, 'missing exact product observation; search zero is inconclusive')
    merged = {}
    for row in records:
        if isinstance(row, str):
            need(re.fullmatch(r'\$[0-9a-f]+', row), 'unsupported product reference')
            need(row[1:] in frames, 'missing or duplicate product reference')
            row = decoder.raw_decode(frames[row[1:]].lstrip())[0]
        need(isinstance(row, dict), 'product record must be object')
        need(row.get('componentModelEn') == mpn and row.get('componentCode') == code,
             'exact product identity mismatch')
        for key in KEYS:
            if key in row and row[key] != '$undefined':
                need(key not in merged or merged[key] == row[key], 'conflicting product '+key)
                merged[key] = row[key]
    p = Visible(); p.feed(html)
    # Bind visible service declarations to the main exact-product table, before specifications.
    tokens = p.parts
    starts = [i for i,t in enumerate(tokens) if t == 'MFR.Part #' and i+1 < len(tokens) and tokens[i+1] == mpn]
    need(starts, 'missing visible exact product table')
    labels = {}
    for start in starts:
        end = next((i for i in range(start, len(tokens)) if tokens[i] == 'Specifications' or (i > start and tokens[i] == 'MFR.Part #')), len(tokens))
        table = tokens[start:end]
        need('JLCPCB Part #' in table and table[table.index('JLCPCB Part #')+1] == code,
             'visible code mismatch')
        for label in ('Assembly Type', 'PCBA Type'):
            positions = [i for i,t in enumerate(table) if t == label]
            need(positions, 'missing explicit service '+label)
            values = {table[i+1] for i in positions if i+1 < len(table)}
            need(len(values) == 1, 'conflicting visible service')
            value = values.pop()
            need(label not in labels or labels[label] == value, 'conflicting visible product tables')
            labels[label] = value
    merged['visible_service'] = labels
    validate_observation(merged, mpn, code)
    return merged


def validate_observation(row, mpn, code):
    need(row['componentModelEn'] == mpn and row['componentCode'] == code, 'exact identity')
    need(row['componentBrandEn'] == ('KEMET' if mpn.startswith('C') else 'YAGEO')
         and row['componentSpecificationEn'] == '0603', 'manufacturer/package mismatch')
    for key in ('overseasStockCount', 'canPresaleNumber', 'preMinPurchaseNum',
                'encapsulationNumber', 'lossNumber', 'leastPatchNumber'):
        value = row.get(key)
        need(value is None or (type(value) is int and value >= 0), 'invalid count '+key)
    need(type(row.get('componentProductType')) is int and row['componentProductType'] in (0,1,2), 'unknown PCBA service')
    service = {0:'Economic and Standard', 1:'Economic Only', 2:'Standard Only'}[row['componentProductType']]
    need(row.get('assemblyMode') == 'smtWeld'
         and row['visible_service'] == {'Assembly Type':'SMT Assembly','PCBA Type':service}, 'service mismatch')
    need(type(row.get('assemblyComponentFlag')) is bool, 'opaque flag type')


def classify(row):
    stock = row.get('overseasStockCount')
    return {
        'identity_verdict':'CONFIRMED - distributor identity only',
        'catalog_assembly_declaration':row['visible_service'],
        'stock_status': 'UNKNOWN' if stock is None else ('OBSERVED_POSITIVE' if stock > 0 else 'OBSERVED_ZERO'),
        'stock_quantity':stock,
        'stock_scope':'Dated exact-product overseasStockCount; not reserved or guaranteed order inventory.',
        'order_assembly_eligibility':'UNCONFIRMED_REQUIRES_PROJECT_BOM_CPL_AND_SERVICE_REVIEW',
        'allocation_confirmed':False, 'purchase_authorized':False,
        'assemblyComponentFlag_scope':'Mechanical-assembly badge discriminator, not SMT eligibility; retain raw value.',
    }


def compare_candidate(old, proposed):
    fields = ('kind','value_SI','tolerance_fraction','body_nominal_mm','body_tolerance_mm')
    need(all(k in proposed for k in fields), 'incomplete replacement ratings')
    need(proposed['kind'] == old['kind'] and proposed['value_SI'] == old['value_SI'], 'nominal value/kind substitution')
    need(proposed['tolerance_fraction'] <= old['tolerance_fraction'], 'tolerance degraded')
    need(proposed['body_nominal_mm'] == old['body_nominal_mm'] and proposed['body_tolerance_mm'] == old['body_tolerance_mm'], 'dimensions require mounting review')
    if old['kind'] == 'C':
        need(proposed.get('dielectric') == old['dielectric'], 'dielectric requires separate review')
        need(proposed.get('rated_voltage_V',0) >= old['rated_voltage_V'], 'voltage degraded')
    else:
        need(proposed.get('power_W_at_70C',0) >= old['power_W_at_70C']
             and proposed.get('maximum_continuous_voltage_V',0) >= old['maximum_continuous_voltage_V'], 'power/voltage degraded')
        need(proposed.get('TCR_ppm_per_C',float('inf')) <= old['TCR_ppm_per_C'], 'TCR degraded')
    need(proposed['temperature_range_C'][0] <= old['temperature_range_C'][0]
         and proposed['temperature_range_C'][1] >= old['temperature_range_C'][1], 'temperature range degraded')
    return 'NO_RATING_OR_DIMENSION_CHANGE; application qualification remains open'


def propose(prior, packages, requirements, evidence):
    need(evidence['owner_choice'] == 'JLC_SUPPORTED_SOURCING_AND_ASSEMBLY'
         and evidence['manual_population_required'] is False, 'owner sourcing route')
    need(evidence['adopted'] is False and evidence['electrical_acceptance'] is False, 'candidate promotion')
    need(set(evidence['candidates']) == set(CODES), 'complete nine-candidate roster')
    need(len(prior['selections']) == 19 and set(requirements['references']) == set(prior['selections']), 'complete 19-reference roster')
    need(requirements['assumptions']['owner_approved'] is False and not requirements['electrical_acceptance'], 'no new performance approval')
    operations = []
    for ref, selection in sorted(prior['selections'].items()):
        package = packages[ref]
        need(package == selection['captured_source'], 'source pin/net/unit/placement/metadata drift '+ref)
        need(package['selected_mpn'] is None and package['selected_manufacturer'] is None and package['supplier_order_code'] is None, 'selection already changed')
        mpn = selection['candidate_mpn']; c = evidence['candidates'][mpn]
        need(c['code'] == CODES[mpn] and c['mpn'] == mpn, 'exact code mapping')
        validate_observation(c['observation'], mpn, c['code'])
        old = prior['sources'][mpn]['ratings']
        need(c['ratings'] == old, 'retained primary rating substitution')
        comparison = compare_candidate(old, c['ratings'])
        need(c['manufacturer_source_sha256'] == prior['sources'][mpn]['sha256'], 'manufacturer source substitution')
        need(c['source_id'] == c['code'], 'supplier source binding')
        sourcing = classify(c['observation'])
        blockers = [requirements['references'][ref]['remaining'],
                    'Exact land pattern and installed reflow/thermal qualification remain open.',
                    'Order-time BOM/CPL matching, project service eligibility, quantities/attrition and allocation remain unconfirmed.']
        operations.append({
            'ref':ref, 'operation':'PROPOSE_ONLY_NOT_APPLIED',
            'source_package_sha256':hashlib.sha256(dump(package).encode()).hexdigest(),
            'test':{'selected_manufacturer':None,'selected_mpn':None,'supplier_order_code':None},
            'proposed':{'selected_manufacturer':c['observation']['componentBrandEn'],'selected_mpn':mpn,'supplier_order_code':c['code']},
            'unchanged_unit_records':package['unit_records'], 'unchanged_pins':package['pins'],
            'comparison':comparison, 'sourcing':sourcing, 'unresolved':blockers,
            'ready_to_apply':False,
        })
    return {'status':'REVIEWED_CANDIDATE_PROPOSAL_NOT_APPLIED', 'operations':operations,
            'counts':{'references':19,'exact_candidates':9,'substitutions':0},
            'native_request':'NONE', 'candidate_adoption':False,'electrical_acceptance':False,
            'owner_choices_not_made':['AC center-null bandwidth','manual-control settling','wiring serviceability'],
            'next_bounded_step':'Close source error/thermal/filter budgets and prepare exact reflow land-pattern proposal; retain JLC codes, then independently review before any source/CAD adoption. No native work in this step.'}


def protected():
    changed = subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed) <= {REL+'WORK.md'}, 'protected historical bytes changed')
    additions = subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    additions += subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    allowed = {'scripts/architecture278/implementation/'+p for p in ('stage23_jlc.py','test_stage23_jlc.py')}
    need(all(p.startswith(REL+'stage23/') or p in allowed for p in additions), 'out-of-scope addition')
    return {'baseline_commit':BASE,'preexisting_bytes_preserved_except':[REL+'WORK.md']}


def validate_guidance(evidence, receipts):
    expected = {
        'sourcing': ('sourcing', 'https://jlcpcb.com/help/article/pcba-parts-sourcing-instruction'),
        'global_sourcing': ('global-sourcing', 'https://jlcpcb.com/help/article/how-to-use-jlcpcb-global-sourcing-parts-service'),
        'matching': ('matching', 'https://jlcpcb.com/help/article/component-matching-guidelines-for-pcba-orders'),
        'frontend': ('frontend', 'https://assets.jlcpcb.com/web-resources/component-platform-static/CanaryLane/latest/_next/static/chunks/app/%5Blocale%5D/partdetail/%5B...urlSuffix%5D/page-5d49ca895ef509da.js'),
    }
    need(set(evidence['service_guidance']) == set(expected), 'complete service guidance')
    for key, (sid, url) in expected.items():
        need(evidence['service_guidance'][key]['source_id'] == sid and sid in receipts,
             'guidance source binding')
        need(receipts[sid]['url'] == url, 'guidance official URL binding')
    need(receipts['frontend']['sha256'] == '776243a15b5fdf3cefb44b0cfca77dd2fc087e8c8850399715b73a51558d9461',
         'reviewed frontend interpretation binding')


def build(check_cache=False):
    prior_path=ROOT/REL/'stage21/inventory-input.json'; source_path=ROOT/REL/'stage16/inputs-report.json'
    requirements_path=ROOT/REL/'stage22/requirements-report.json'
    prior,source,requirements = map(read,(prior_path,source_path,requirements_path))
    evidence = read(OUT/'inventory-input.json'); receipts=read(OUT/'retrieval.json')
    validate_guidance(evidence, receipts)
    need(set(CODES.values()) <= set(receipts), 'all exact receipts required')
    for sid, receipt in receipts.items():
        need(re.fullmatch('[0-9a-f]{64}',receipt['sha256']) and receipt['sha256'] != '0'*64, 'receipt digest')
        need(receipt['bytes'] > 0 and datetime.datetime.fromisoformat(receipt['retrieved_at']).tzinfo is not None, 'dated receipt')
        need(receipt['url'].startswith('https://jlcpcb.com/') or receipt['url'].startswith('https://assets.jlcpcb.com/'), 'official supplier receipt URL')
        if sid.startswith('C'):
            need(receipt['url'] == 'https://jlcpcb.com/partdetail/'+sid, 'receipt code URL')
        if check_cache:
            p=ROOT/receipt['raw_cache'];need(p.is_file() and sha(p)==receipt['sha256'] and p.stat().st_size==receipt['bytes'], 'cache mismatch '+sid)
    for mpn,candidate in evidence['candidates'].items():
        need(candidate['supplier_sha256'] == receipts[candidate['source_id']]['sha256'], 'supplier digest binding')
        if check_cache:
            html=(ROOT/receipts[candidate['source_id']]['raw_cache']).read_text()
            need(parse_jlc(html,mpn,candidate['code']) == candidate['observation'], 'supplier parser replay drift')
    result=propose(prior,source['packages'],requirements,evidence)
    result['preservation']=protected()
    result['candidates']=evidence['candidates']; result['service_guidance']=evidence['service_guidance']
    paths=[prior_path,source_path,requirements_path,OUT/'inventory-input.json',OUT/'retrieval.json',OUT/'README.md',Path(__file__),Path(__file__).with_name('test_stage23_jlc.py')]
    result['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in paths}
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--check-cache',action='store_true');args=parser.parse_args()
    body=dump(build(args.check_cache));path=OUT/'candidate-selection.patch.json'
    if args.check:need(path.read_text()==body,'deterministic candidate patch drift')
    else:path.write_text(body)
    print('PASS Stage23: 9 exact JLC candidates / 19 references; proposal NOT APPLIED; allocation and electrical acceptance UNCONFIRMED')


if __name__=='__main__':main()
