"""Run DRC/refill/save and bind its report to the actual inputs and saved board."""
from pathlib import Path
import hashlib,json,subprocess,sys

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dependencies(board):
    paths=[board.with_suffix(s) for s in ('.kicad_pro','.kicad_sch','.kicad_dru')]
    paths += [*board.parent.glob('sheets/**/*'),board.parent/'fp-lib-table',board.parent/'sym-lib-table']
    return {str(p.relative_to(board.parent)):sha(p) for p in paths if p.is_file()}

def validate(report,execution,board_hash,dependency_hashes):
    if execution['returncode']!=0 or execution['saved_board_sha256']!=board_hash or execution['report_sha256']!=sha(report):raise ValueError('DRC execution/report/board binding')
    if execution['dependencies_before']!=execution['dependencies_after'] or execution['dependencies_after']!=dependency_hashes:raise ValueError('DRC dependency binding')
    expected=['kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--save-board','--format','json','--severity-all','-o',execution['report'],execution['board']]
    if execution['command']!=expected or execution['report']!=str(report):raise ValueError('DRC command/report binding')
    return True

def run(board,report):
    if report.exists() or Path(str(report)+'.execution.json').exists():raise ValueError('do not overwrite native evidence')
    before=sha(board);deps=dependencies(board)
    command=['kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--save-board','--format','json','--severity-all','-o',str(report),str(board)]
    process=subprocess.run(command,check=False)
    result={'command':command,'board':str(board),'report':str(report),'input_board_sha256':before,'saved_board_sha256':sha(board),'report_sha256':sha(report) if report.is_file() else None,'dependencies_before':deps,'dependencies_after':dependencies(board),'returncode':process.returncode}
    Path(str(report)+'.execution.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if process.returncode:raise SystemExit(process.returncode)
    validate(report,result,sha(board),dependencies(board))
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
