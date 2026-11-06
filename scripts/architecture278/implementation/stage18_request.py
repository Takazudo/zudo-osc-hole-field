"""Emit an exact proposal from committed bytes. Never launch a native process."""
import argparse
import hashlib
import json
import subprocess

import stage18_compat as s

IMAGE='kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'


def request(commit):
    actual=subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=s.ROOT,text=True).strip()
    s.need(actual==commit,'request requires full exact commit SHA')
    report=s.report()
    s.need((s.OUT/'compatibility-report.json').read_text()==s.json_text(report),'stale source report')
    bound=dict(report['source_sha256'])
    bound.update({str((s.GENERATED/name).relative_to(s.ROOT)):sha for name,sha in report['generated_sha256'].items()})
    bound[str((s.OUT/'compatibility-report.json').relative_to(s.ROOT))]=s.digest(s.OUT/'compatibility-report.json')
    for path,sha in bound.items():
        blob=subprocess.check_output(['git','show',commit+':'+path],cwd=s.ROOT)
        s.need(hashlib.sha256(blob).hexdigest()==sha==s.digest(s.ROOT/path),'commit/input mismatch '+path)
    inputs={path.removeprefix('design/architecture-278/implementation/'):sha for path,sha in bound.items()
        if path.startswith(('design/architecture-278/implementation/stage17/generated/',
                            'design/architecture-278/implementation/stage18/generated/'))}
    return {'status':'PROPOSAL ONLY; fresh owner approval and live independent admission REQUIRED',
        'admission_granted':False,'native_executed':False,'commit':commit,'image':IMAGE,
        'preferred_host':'Codex Cloud; X0X only if Cloud cannot prove required existing native capabilities',
        'version_argv':['kicad-cli','version'], 'required_version_stdout':'10.0.6',
        'export_argv':['kicad-cli','sch','export','netlist','--format','kicadxml','-o','/output/netlist.xml','/inputs/stage18/generated/a01.kicad_sch'],
        'one_export_opportunity':True,'automatic_retry':False,
        'input_mount':{'repository_relative_source':'design/architecture-278/implementation', 'container_target':'/inputs','read_only':True,'required_files_sha256':inputs},
        'output_path':'/output/netlist.xml', 'fresh_run_id':'osc-stage18-native-001',
        'resources':{'cpus':2,'memory_bytes':4294967296,'swap_bytes':0,'whole_run_timeout_seconds':600,
            'network':'none','root_filesystem':'read-only','live_tmpfs_bytes':262144000,
            'retained_stream_bytes':262144000,'host_metadata_bytes':12582912,'total_writable_budget_bytes':536870912},
        'requirements':['Use the shared heavy guard and prove actual cgroup/mount/network/timeout controls before admission.',
            'Use fresh absent run/output paths; retain exact argv, version/export stdout/stderr/exit/time/resource receipts.',
            'Bind actual checkout, scripts, input inventory, output destination, limits and owner approval in fresh independently reviewed admission.',
            'Review an adapted supervisor for the stage18 layout and XML output before executing; old stage17 host/container wrappers are not compatible and must not be invoked.',
            'Use verified bounded streaming retention before cleanup; compare required file inventory, byte counts and SHA256 independently.',
            'Stop on version/resource/hash mismatch; no install, native ERC/DRC/PCB/simulation, or reuse of run001/run002 admission.'],
        'source_and_verifier_sha256':dict(sorted(bound.items())),
        'post_retention_comparison_argv':['python3','scripts/architecture278/implementation/stage18_observation.py',
            '--netlist','<fresh-run>/retained/netlist.xml','--output','<fresh-run>/xml-parity.json'],
        'acceptance_contract':{'references':118,'pins_including_NC':561,'unit_UUIDs':154,
            'annotations_remain_excluded':22,'hardware_acceptance':False},
        'historical_status':{'run001':'UNKNOWN','run002_export':'PASS','run002_full_parity':'FAIL'}}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True);args=parser.parse_args()
    print(s.json_text(request(args.commit)),end='')
