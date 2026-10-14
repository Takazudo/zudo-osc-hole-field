import ctypes,errno,fcntl,json,os,pathlib,resource,select,signal,subprocess,tempfile,time
resource.setrlimit(resource.RLIMIT_AS,(64*1024**2,64*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(2,2));resource.setrlimit(resource.RLIMIT_FSIZE,(8192,8192))
libc=ctypes.CDLL(None,use_errno=True);libc.syscall.restype=ctypes.c_long
assert os.uname().machine=='x86_64'
with tempfile.TemporaryDirectory(prefix='e16-pidfd-fixture-') as d:
 path=pathlib.Path(d)/'lock';path.touch();ready_r,ready_w=os.pipe();done_r,done_w=os.pipe()
 pid=os.fork()
 if pid==0:
  os.close(ready_r);os.close(done_w)
  fd=os.open(path,os.O_RDWR);os.dup2(fd,200);os.close(fd);fcntl.flock(200,fcntl.LOCK_EX)
  os.write(ready_w,b'1');os.close(ready_w)
  select.select([done_r],[],[],5);os.close(done_r);os._exit(0)
 os.close(ready_w);os.close(done_r);pidfd=None;duplicate=None
 try:
  assert select.select([ready_r],[],[],3)[0];assert os.read(ready_r,1)==b'1'
  pidfd=os.pidfd_open(pid,0)
  ctypes.set_errno(0);result=libc.syscall(438,pidfd,200,0);err=ctypes.get_errno()
  print(json.dumps({'stage':'pidfd_getfd','parent':os.getpid(),'owned_direct_child':pid,'target_fd':200,'pidfd_open':'PASS','syscall':438,'return':result,'errno':err,'error':os.strerror(err),'uid':os.getuid(),'parent_caps':[x for x in pathlib.Path('/proc/self/status').read_text().splitlines() if x.startswith(('CapEff:','Seccomp:','NoNewPrivs:'))],'ptrace_scope':pathlib.Path('/proc/sys/kernel/yama/ptrace_scope').read_text().strip()}),flush=True)
  if result>=0:
   duplicate=result
   os.write(done_w,b'x');os.waitpid(pid,0);pid=None
   check=os.open(path,os.O_RDWR)
   try:
    try:fcntl.flock(check,fcntl.LOCK_EX|fcntl.LOCK_NB);locked=False
    except BlockingIOError:locked=True
   finally:os.close(check)
   print(json.dumps({'stage':'after_child_exit','exact_lock_remains_held':locked}),flush=True)
  else:
   assert err in (errno.EPERM,errno.EACCES,errno.ENOSYS),err
 finally:
  if pid is not None:os.write(done_w,b'x');os.waitpid(pid,0)
  for fd in (ready_r,done_w,pidfd,duplicate):
   if fd is not None:os.close(fd)
  check=os.open(path,os.O_RDWR);fcntl.flock(check,fcntl.LOCK_EX|fcntl.LOCK_NB);os.close(check)
  print(json.dumps({'stage':'cleanup','child_reaped':True,'lock_released':True,'temporary_directory_removed_on_exit':True}),flush=True)
