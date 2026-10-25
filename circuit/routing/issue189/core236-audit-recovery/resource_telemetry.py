"""Observe this audit runner; no inference of an exit cause."""
import json,pathlib,shutil,subprocess,sys,time
output=pathlib.Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True)
while True:
    row={'utc_epoch':time.time(),'disk':shutil.disk_usage('.')._asdict()}
    for name in ('/proc/meminfo','/sys/fs/cgroup/memory.current','/sys/fs/cgroup/memory.max','/sys/fs/cgroup/memory.events','/sys/fs/cgroup/memory.peak'):
        try:row[name]=pathlib.Path(name).read_text()
        except OSError:pass
    ps=subprocess.run(['ps','-eo','pid,ppid,comm,rss,vsz','--sort=-rss'],capture_output=True,text=True)
    row['largest_processes']=ps.stdout.splitlines()[:21]
    with output.open('a') as f:f.write(json.dumps(row)+'\n')
    time.sleep(10)
