# Conditional inverse reference-range diagnostic

This calculation inverts the existing passive negative-monitor corner equations.
For each of 256 independent resistor corners it derives the reference sensitivity
and worst comparator/input-current error spread. Positive normal-band margins
require REF to lie strictly between the maximum OV lower boundary and minimum
UV upper boundary. Exact fractions and limiting corner witnesses are retained;
displayed endpoints are rounded strictly inward. Nonpositive sensitivity or an
empty intersection is rejected.

Under the original assumptions the strict interval is approximately
(3.182265562468151, 3.335063872556685) V. This is conditional normal-band
compatibility, not reference validity or fault rejection. The trip enclosures
use the closure of that interval and can extend beyond the normal rail band.
The prescribed nominal REF=3.2 V / VN=−10.9 V case remains inside the interval
while both ideal comparators release. It is a static diagnostic, not a claimed
reachable trajectory.

No reference requirement, circuit value, source-current limit, fitted component
or panel position changes. The original 3.29–3.31 V reference assumption and its
unproved applicability remain intact. Source conditions, current/ground integrity,
power transitions, real comparator behavior and physical qualification remain open.

Six focused tests exercise exact zero-margin witnesses, strict inward rounding,
acceptance on each side of the boundary through the independent forward model,
changed error envelopes, rejected slope/empty cases, and the retained unsafe case.
The prepared calculation passed an independent read-only review. Regeneration
binds all source bytes and rejects changes during the calculation. Full combined
regeneration and documentation/CI checks are required before merge.

The guarded baseline and post-change aggregate, documentation checks, build and
strict site checks pass (exit0,635 seconds; one existing template-link exception
is allowlisted). All24 focused inverse/forward/reference tests pass. Review caught
a prose-only upper-endpoint rounding error; the checkpoint now prints the actual
inward report bounds. The parent standard-summary correction was fast-forwarded
after that run; all six diagnostic input hashes remain current and its report
check passes. Exact combined-source CI remains required before merge.
