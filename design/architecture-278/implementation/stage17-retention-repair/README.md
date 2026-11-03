# Retention repair: synthetic verification only

The original X0X attempt remains **native outcome UNKNOWN / native parity
NOT RUN**. Its failure record is unchanged in `../stage17-native-x0x-001/`.
No additional KiCad command was executed during this repair.

`stage17_retain.py` replaces Docker copy with bounded `docker exec` reads from
the live process's filesystem. It rejects unsafe paths, symlinks, special
files, empty manifests, missing required files and quota excess. It streams
regular files into one fresh partial directory, checks sizes and SHA256,
fsyncs file contents, rechecks the complete source inventory, then renames the
directory. There is no archive/extraction duplicate. `VERIFIED_HASHED_COPY`
means file-content and inventory verification, not crash-proof storage claims.

Independent tests:26 synthetic retention cases PASS, including wrong hashes,
truncation/excess, nonzero subprocess, deadline, fsync failure, source mutation,
symlink/FIFO and path rejection. The118-reference/561-pin/154-unit comparator
is now available as `stage17_native_parity.py` with12 passing synthetic mutation
tests at its final repository location. Neither test suite is native evidence.

An actual existing-image container tested the same250MiB tmpfs,2CPU,4GiB,
zero-swap, readonly-root, network-none and shared-guard environment with Python
synthetic files only. Four files totalling4,194,471bytes, including a4MiB
binary and an empty log, were retained and independently hash-verified.
Missing-required-file rejection left the container running; successful
retention preceded fixture cleanup. `result.json` records native_commands=0.
The synthetic check used a110second container cap and120second guard cap;
the proposed native operation retains its600second ceiling. Guard receipt:
PASS exit0 secs1 min_mem_mb10047. The4MiB binary is reproducible from
`bytes(range(256))*16384`; it is kept locally, not committed.

Future wrappers `stage17_native_host.py` and `stage17_native_container.py` are
**NOT EXECUTED**. They bind executing code to a verification commit, preserve
the original source commit and all generated/source hashes, and wait for a
fresh admission after actual runtime-capability review. `done.json` separates
success, version mismatch and failure; command attempts have pre-invocation
records. Successful-copy cleanup additionally requires expected logs, exact
native argv, exits0, version10.0.6 and nonempty netlist when success is claimed.
On copy failure the source is held until the hard deadline, with partial files
and host error retained. No native retry is automated. This is preparation for
a separately owner-approved run002, not permission to execute it.

The native budget remains250MiB live output plus250MiB retained copy plus
12MiB host metadata, at most512MiB total. All config/cache/tmp/logs share the
same live quota. All earlier electrical/procurement/PCB limitations remain.
