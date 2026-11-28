"""Memory and time guard for the S13 study steps (brief "Run bounds").

Copied from `mc04_s12_five_ic_joint/guard.py` (the S12 file is not edited) and changed to the S13 numbers:
a 4 GiB budget enforced on the sum of the process-tree RSS and the oracle container memory from `docker stats`
(both sampled every 5 s; the container runs under dockerd, outside the tree), and a MemAvailable floor of 8 GiB
as the backstop. On an abort it kills the tree and then every container of the pinned image, and records whether
the container list is empty afterwards. Writes a JSON summary with the peaks.
"""
import json
import os
import signal
import subprocess
import sys
import time

BUDGET = 4 * 1024 ** 3
FLOOR = 8 * 1024 ** 3
PERIOD = 5.0
IMAGE = "kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec"


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


def pinned_containers():
    out = subprocess.run(["docker", "ps", "-q", "--filter", f"ancestor={IMAGE}"],
                         capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(f"docker ps failed: {out.stderr.strip()}")
    return out.stdout.split()


def kill_pinned_containers():
    """Kill every container of the pinned image; return the ids that survive (must be empty)."""
    ids = pinned_containers()
    if ids:
        subprocess.run(["docker", "kill", *ids], capture_output=True, text=True, timeout=60)
        time.sleep(1.0)
    return pinned_containers()


def docker_mem():
    try:
        ids = pinned_containers()
        if not ids:
            return 0
        out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", *ids],
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
    peak, peak_sum, min_avail, peak_docker, reason = 0, 0, mem_available(), 0, None
    samples = 0
    while proc.poll() is None:
        r = tree_rss(proc.pid)
        d = docker_mem() or 0
        a = mem_available()
        samples += 1
        peak, peak_docker, min_avail = max(peak, r), max(peak_docker, d), min(min_avail, a)
        peak_sum = max(peak_sum, r + d)
        if r + d > BUDGET:
            reason = f"tree RSS {r} + container {d} > budget {BUDGET}"
        elif a < FLOOR:
            reason = f"MemAvailable {a} < floor {FLOOR}"
        if reason:
            os.killpg(proc.pid, signal.SIGKILL)
            break
        time.sleep(PERIOD)
    rc = proc.wait()
    survivors = kill_pinned_containers() if reason else pinned_containers()
    out = {"command": cmd, "returncode": rc, "wall_s": round(time.time() - t0, 1),
           "peak_tree_rss_bytes": peak, "peak_tree_rss_mib": round(peak / 2 ** 20, 1),
           "peak_docker_container_mem_mib": round(peak_docker / 2 ** 20, 1),
           "peak_tree_plus_container_mib": round(peak_sum / 2 ** 20, 1),
           "min_mem_available_mib": round(min_avail / 2 ** 20, 1),
           "samples": samples,
           "watchdog_fired": reason, "budget_bytes": BUDGET, "mem_available_floor_bytes": FLOOR,
           "pinned_containers_after": survivors,
           "measure": "tree RSS plus docker stats of pinned-image containers, both every 5 s, enforced; "
                      "MemAvailable floor as backstop"}
    with open(summary_path, "w") as f:
        json.dump(out, f, indent=1)
    if survivors:
        sys.exit(70)
    sys.exit(rc if reason is None else 137)


if __name__ == "__main__":
    main()
