"""MC04-S16b control K3: a no-op child that appends one heartbeat line per second for 5 minutes, then exits."""
import sys
import time

path = sys.argv[1]
end = time.time() + 300
while time.time() < end:
    with open(path, 'a') as f:
        f.write('%.1f\n' % time.time())
    time.sleep(1.0)
