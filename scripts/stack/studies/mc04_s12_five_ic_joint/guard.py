"""Memory and time guard for the S12 study steps (brief "Run bounds").

Runs one command, samples the RSS of its whole process tree every 5 s and the
system MemAvailable, and kills the tree when the tree RSS exceeds the budget or
MemAvailable drops below the floor. The floor exists because an oracle container
runs under dockerd, outside the tree (admission note 1 of the S12 reviewer).
Writes a JSON summary with the peak tree RSS, the minimum MemAvailable and the
peak docker container memory seen.
"""
import json
import os
import signal
import subprocess
import sys
import time

BUDGET = 8 * 1024 ** 3
FLOOR = 7 * 1024 ** 3
PERIOD = 5.0


def mem_available():
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    return 0


def tree_rss(root):
    children = {}
    rss = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/stat") as f:
                parts = f.read().rsplit(")", 1)[1].split()
            ppid = int(parts[1])
            rss[int(pid)] = int(parts[21]) * os.sysconf("SC_PAGE_SIZE")
            children.setdefault(ppid, []).append(int(pid))
        except (OSError, IndexError, ValueError):
            continue
    total, stack = 0, [root]
    while stack:
        p = stack.pop()
        total += rss.get(p, 0)
        stack.extend(children.get(p, []))
    return total


def docker_mem():
    try:
        out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}"],
                             capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return None
    total = 0.0
    units = {"B": 1, "KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3, "kB": 1e3, "MB": 1e6, "GB": 1e9}
    for line in out.splitlines():
        used = line.split("/")[0].strip()
        for u in sorted(units, key=len, reverse=True):
            if used.endswith(u):
                try:
                    total += float(used[: -len(u)]) * units[u]
                except ValueError:
                    pass
                break
    return int(total)


def main():
    summary_path = sys.argv[1]
    cmd = sys.argv[2:]
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    t0 = time.time()
    proc = subprocess.Popen(cmd, start_new_session=True)
    peak, min_avail, peak_docker, reason = 0, mem_available(), 0, None
    last_docker = 0.0
    while proc.poll() is None:
        r = tree_rss(proc.pid)
        a = mem_available()
        peak, min_avail = max(peak, r), min(min_avail, a)
        if time.time() - last_docker > 30:
            d = docker_mem()
            if d:
                peak_docker = max(peak_docker, d)
            last_docker = time.time()
        if r > BUDGET:
            reason = f"tree RSS {r} > budget {BUDGET}"
        elif a < FLOOR:
            reason = f"MemAvailable {a} < floor {FLOOR}"
        if reason:
            os.killpg(proc.pid, signal.SIGKILL)
            break
        time.sleep(PERIOD)
    rc = proc.wait()
    out = {"command": cmd, "returncode": rc, "wall_s": round(time.time() - t0, 1),
           "peak_tree_rss_bytes": peak, "peak_tree_rss_mib": round(peak / 2 ** 20, 1),
           "min_mem_available_mib": round(min_avail / 2 ** 20, 1),
           "peak_docker_container_mem_mib": round(peak_docker / 2 ** 20, 1),
           "watchdog_fired": reason, "budget_bytes": BUDGET, "mem_available_floor_bytes": FLOOR,
           "measure": "tree RSS sampled every 5 s plus system MemAvailable floor; docker stats every 30 s"}
    with open(summary_path, "w") as f:
        json.dump(out, f, indent=1)
    sys.exit(rc if reason is None else 137)


if __name__ == "__main__":
    main()
