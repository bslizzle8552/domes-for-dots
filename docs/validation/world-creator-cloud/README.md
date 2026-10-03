# Verified cloud-created three-world export

[Cloud world creator run 37080816856](https://github.com/bslizzle8552/domes-for-dots/actions/runs/37080816856) succeeded for source commit `2c26332ec202901359bdd12870cc7c7bcedfb37e`. The worker reported a clean source checkout and unchanged source after completion. This evidence records that run, not an implied rebuild of later documentation commits.

Both GitHub artifact ZIPs were downloaded, their SHA-256 digests checked against GitHub's artifact metadata, and their contents extracted with path/size/link checks. All **15 Web files**, totaling **38,841,021 bytes**, exactly match the worker's complete SHA-256 inventory. All **six downloaded World/Character Packages** passed fresh registered validation. See [artifact verification](artifact-verification.json) and the [selected job receipt](job-receipt.json). The latter retains the original full receipt's SHA-256 and lists omitted diagnostic fields; the original remains in the GitHub artifact.

| Cloud execution gate | Result |
| --- | --- |
| Engine | Godot 4.5.1 Standard, Compatibility, single-threaded Web |
| Character motion | 59 passed for each of Ember, Lumen and Fern; 177 total |
| Generated worlds | 61 passed; 2,414 physical support samples and 8,799 prop checks |
| Multi-level transition | 38 passed; 4,542 support/headroom samples; zero support failures |
| World package build | 0.810 s Ember, 0.752 s Lumen, 0.812 s Fern |
| Composition / staged validation | 2.034 s / 0.473 s |
| Engine import / Web export | 5.363 s / 3.706 s |
| Worker elapsed | 19.697 s, excluding earlier dependency/bootstrap/workflow steps |

The downloaded Web directory was then served unchanged on a new loopback origin and exercised in a fresh desktop Chrome 154.0.8037.97 context using the repository's browser acceptance runner. Its expected station/world manifests came from the downloaded cloud packages. **All 46 browser checks passed**, with no browser or Godot errors. This includes actual imported skeleton/clips, every station, simulated routines, supported movement, uphill/downhill travel, mid-ramp interruption/redirection, and browser reload retaining timeline/pause while restoring a safe spawn. See [browser acceptance](browser-acceptance.json).

Observed first-world startup was **5.267 s** on this local loopback test. Navigation build observations were **12/4/5 ms** for Ember/Lumen/Fern. The browser collected **682 movement-support samples** and observed no recovery teleport. Median browser animation-frame cadence was approximately **16.7 ms** across the three measured 120-frame windows. JavaScript heap and resource-transfer observations are preserved in the receipt; they do not measure total WebAssembly/GPU/process memory or predict other devices/networks.

The cloud worker did not deploy these bytes. This browser test proves playback of the exact remote-created export through local loopback; it does not prove private hosted access or cloud state persistence. Those have separate Site evidence. Native activity remains unavailable, and routine animation remains SIMULATED.

Final implementation commit `611895b87244717b21c39de2b8f25e6459c330ff` subsequently passed all four CI runs: cloud [push](https://github.com/bslizzle8552/domes-for-dots/actions/runs/37082142550) and [PR](https://github.com/bslizzle8552/domes-for-dots/actions/runs/37082146060), plus source validation [push](https://github.com/bslizzle8552/domes-for-dots/actions/runs/37082142602) and [PR](https://github.com/bslizzle8552/domes-for-dots/actions/runs/37082146086). Each Linux Python run discovered 237 tests: **235 passed and two Windows-specific filesystem case-alias tests were skipped**. Both cloud runs additionally passed three 59-check character-motion suites, 61 generated-world checks with 2,414 physical samples, and 38 multi-level checks with 4,542 support/headroom samples and zero support failures. [Final CI evidence](final-ci.json) records exact SHAs, conclusions, run/job identities, downloaded-log digests and parsed counts. These final CI results do not replace the earlier exact-artifact browser proof or imply a new browser run.
