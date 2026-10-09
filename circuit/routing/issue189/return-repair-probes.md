# Supply/return repair probes

These probes do not change a canonical board. Native gates rejected both fixed
signal proposals after plane fanout failed to restore original supply membership.
The main branch retains JL139/JR162. Do not repeat that unchanged fanout method.

- JR run37875619974, artifact11592851696, ZIP SHA256
  `0a74c371c14b3b4b2b67547db013d9edc61d4a02eabbaa2c00a4fdec63d9aac5`.
  Extract under `.circuit-cache/issue189-downloaded/jr-coupled/`.
- JL run37877201397, artifact11593520062, ZIP SHA256
  `0bd16fa13d1bc30adb33d4a9eeb5398593dd238d66e99e7344da6245da401415`.
  Extract under `.circuit-cache/issue189-downloaded/jl-coupled/`.

From the repository root, using the pinned numerical environment:

```sh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jr-rail-link-probe.py
bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jl-rail-link-probe.py
```

Both use the existing rail-link dimensions:0.4mm width,0.25mm clearance,0.05mm grid,
6mm window, original expansion limit, and original layer/fill restrictions. JR:
zero paths/six failures in31.04s. JL:two paths/four failures,20 objects in50.05s.
The JL paths include its newly detached supply group and a pre-existing supply
obligation. Native validation of these added rail paths is NOT RUN yet.

`jr-fill-attribution.py` uses the earlier native-cut JR dump from local pilot
37873299470, documented in the artifact ledger. Its approximate fill screen marks
multiple new target In3 segments and the victim's new via as individual split
risks. Removing any one object from that screen is insufficient; this is not
native causal proof or an eligible proposal. It cannot justify dropping necessary
signal copper or changing electrical constraints. Exact diagnostic JSON is saved.

The follow-up JL native pilot selects the existing `rail-links` stage to connect
components rather than fan out into a disconnected plane fragment. It must restore
all original supply membership, optionally stitch AGND, pass the independent
reload, and improve the original canonical result without warning regressions.
