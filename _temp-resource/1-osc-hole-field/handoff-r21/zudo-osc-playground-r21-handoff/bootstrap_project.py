#!/usr/bin/env python3
"""Print, or explicitly run, the official initializer. No homebrew scaffold."""
import argparse,json,subprocess,shlex
from pathlib import Path

def command(a):
    dst=a.destination.absolute()
    if dst.exists() and (not dst.is_dir() or any(dst.iterdir())):raise ValueError('Destination must be nonexistent or empty. For an existing host use install_resources.py only.')
    if a.initializer_script:
        script=a.initializer_script.resolve(strict=True);cmd=['node',str(script)]
    else:cmd=['npx','--yes','--package=create-zudo-circuit-doc@'+a.version,'create-zudo-circuit-doc']
    cmd += [str(dst),'--name','zudo-osc-playground','--title','zudo-osc-playground','--library','zudo_osc_playground','--agent','both','--yes','--no-git','--no-install']
    if a.runtime_tarball:cmd+=['--runtime-spec','file:'+str(a.runtime_tarball.resolve(strict=True))]
    return cmd

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--version',default='0.1.0');p.add_argument('--initializer-script',type=Path);p.add_argument('--runtime-tarball',type=Path);p.add_argument('--run',action='store_true');a=p.parse_args()
    try:cmd=command(a)
    except (ValueError,OSError) as e:raise SystemExit(str(e))
    print(shlex.join(cmd))
    if not a.run:print('Dry run. --run executes this official create-only initializer; it does not install the payload.');return
    try:v=subprocess.check_output(['node','-p','process.versions.node'],text=True).strip();parts=tuple(int(x) for x in v.split('.')[:3])
    except (OSError,ValueError,subprocess.CalledProcessError):raise SystemExit('A working Node >=22.18.0 is required')
    if parts<(22,18,0):raise SystemExit(f'Node {v} is below the reviewed upstream minimum 22.18.0; update locally first')
    subprocess.run(cmd,check=True)
    print('Initializer finished. Inspect the generated workflow, then run install_resources.py dry run and --apply.')
if __name__=='__main__':main()
