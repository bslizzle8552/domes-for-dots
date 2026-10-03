# Private World Creator Site proof

The new [World Creator Lab](https://domes-world-creator-lab.bslizzle.chatgpt.site) is owner-private. It uses synthetic Lumen content and does not reuse Rocky's Site, assets or state.

* [Deployment receipt](deployment.json): three native source/build/private-publish versions; owner-private audience counts; saved-version rollback and restoration. No credentials or owner identifiers.
* [Final browser/API acceptance](acceptance.json): **26 passed**, zero browser/Godot errors. Single registered world, real imported character, D1 save acknowledgement, pending-save preference retention, fresh isolated-browser restoration, ramp traversal, corrupted-candidate rejection, actual new station, stale-write rejection and structural rollback.
* [Earlier version 2](acceptance-v2.json): **24 passed**, including the first unchanged-PCK live structural update/rollback.
* [Delivery](delivery.json): 19 assets matched stored or approved decoded hashes. HTML adds one hosting script (938 characters), with no removed or replaced original characters. Engine gzip, PCK, JavaScript and JSON match. Anonymous PCK access is gated.
* [Saved-version rollback](version-rollback.json) and [restoration](version-restored.json): v2's original PCK was restored, then v3's final PCK; D1 state revision and epoch remained unchanged. Final active world structure is revision 1; all four registered revisions remain available.

Final PCK: `302c2b9fd9c7403f4fa662bd1da6c7752ab479d1caa1e52db6341d7ae2b00afd`. Engine WASM: `6498359ba889796a0d95a2f71113ac184badc0f2d84cf28f4103c7e399d2d547`. Engine gzip is 9,237,412 bytes; uncompressed WASM is 38,034,280 bytes. Final fresh-browser startup was 9,255 ms in this network/instrumented context.

Browser authentication used existing private scoped service access. Chromium's worklet requests required authenticated same-origin fetch followed by identical-byte Blob module execution in the test harness. This is not acceptance of normal owner sign-in UI or audio features. A fresh isolated context proves remote D1 restoration; it is not a physical second-device/offline test. R2 was not used. The backend is a single private-world adapter, not a multi-tenant creation service.

Reproduce the main runtime/API acceptance with `tools/world_site_acceptance.cjs`, the selected private origin and an authorized credential supplied only through hidden stdin. The [operator guide](../../SITES_WORLD_CREATOR.md) explains packaging, registry boundaries and the exact failure/recovery limits.
