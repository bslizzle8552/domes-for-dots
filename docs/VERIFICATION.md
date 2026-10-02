# v0.1.0 verification

Updated 2026-10-02. All local v0.1.0 acceptance checks pass, including a clean final Web build, browser rerun, archive integrity and rebuilding from the extracted source ZIP without Git metadata. Historical tests mentioned in `prototype/` are not evidence for the Godot runtime. PASS refers to the stated scope. Online release status is recorded in [BUILD_STATUS.md](../BUILD_STATUS.md) and on the [release page](https://github.com/bslizzle8552/domes-for-dots/releases/tag/v0.1.0).

## Evidence recorded so far

| Check | Result | Scope |
| --- | --- | --- |
| Godot toolchain identity | PASS | Portable Godot reports `4.5.1.stable.official.f62fdbde1`; downloaded archive checksum matches the official release checksum. Matching Web templates were used for export. |
| Early Web export | PASS | A real early Godot 3D scene rendered in Chrome using Compatibility/WebGL 2 and a single-threaded export, without browser/engine errors in that smoke test. This was deliberately before full runtime integration. |
| Content schemas and relationships | PASS | Both authored worlds and their referenced content pass the Python validator. |
| Python tests | PASS | 46 content, schema, transformed-footprint, release-hygiene, archive-integrity and source-archive portability tests pass. |
| GDScript core tests | PASS | Final native rerun: 71 passed, 0 failed. Covers simulation, bounded leases, revision protection and native state recovery. Browser storage and scene movement have separate checks below. |
| Full-world browser rendering | PASS | Cedar Atelier and Tidal Observatory rendered with distinct layouts/content in the same runtime: studio/terrace versus research deck/bridge/observation wing. Seven versus six stations are exposed. |
| Headless runtime integration | PASS | Final native rerun: 108 passed, 0 failed. All 49 Cedar and 36 Tidal station pairs resolve. The character physically visits all 13 stations and returns, with 13,956 collider-clearance samples. Unreachable targets stop safely. Alternate character geometry/AnimationPlayer clips, initial idle, fallbacks/chains and same-motor movement pass. Navigation initialization now waits for the new region to own the spawn point, bounded to five seconds. |
| Browser state and event acceptance | PASS | [26 checks](validation/browser-acceptance.json) passed again on the final export in Chrome 154.0.8037.97 on Windows: wind-chime arrival, orbital bridge traversal, MOCK pose/priority/expiry/replay rejection, shared epoch/project IDs, preference reload, unsaved time preview, stale-save conflict, injected quota failure preserving bytes, corrupt-primary recovery, repair, exports, pointer control and no runtime errors. |
| Documentation | PASS | Local Markdown targets resolve; onboarding and activity JSON examples validate against their published schemas. Source review separates executed behavior from future contracts. |
| Release archives and hygiene | PASS | 105 tracked files inspected, source/Web ZIP CRC checks pass, SHA-256 inventories produced, and exported assets match the build inventory. No secrets or private world content found by scan and review. Extracted source ZIP rebuilt successfully, including all 46/71/108 checks, with no .git directory. |

Selected sanitized browser evidence is included in [`docs/validation/`](validation/) and [`docs/images/`](images/): [Cedar Atelier](images/cedar-atelier.png), [Tidal Observatory](images/tidal-observatory.png), and the [MOCK phone pose](images/mock-phone.png). Other screenshots, downloaded state and raw outputs remain ignored development artifacts. The [build manifest](validation/build-manifest.json) records runtime source commit `2039920faad095ff1de5aa856f77d4212b9ef8bf` and resource/payload hashes. Later release commits update documentation/evidence only. Final archive hashes are in the release's `SHA256SUMS`; they are intentionally outside the source archive to avoid a self-referential checksum.

## Release requirements

| # | Requirement | Acceptance state and evidence |
| --- | --- | --- |
| 1 | Coherent, clean repository | PASS clean committed source, documented layout and tracked-files-only archive review. |
| 2 | Godot project opens/runs | PASS export/import, live browser execution and final native integration suite. |
| 3 | Real simple 3D world | PASS browser rendering of both actual Godot worlds. |
| 4 | Character exists | PASS original procedural resident rendered in the full scenes. |
| 5 | Character navigates to multiple stations | PASS all 85 native station-pair paths, physical visits to all 13 stations plus returns, and final browser wind-chime/call/bridge travel. |
| 6 | Generic station architecture | PASS source/content contract; stations use IDs, tags, anchors, facing and semantic actions. No object-type list. |
| 7 | Deterministic routine | PASS pure GDScript simulation tests, including long absences, finite projects and repeated evaluation. |
| 8 | Separate configuration/state architecture | PASS schemas and separate state adapter; no mutable world counter. |
| 9 | Data-driven content | PASS catalog/world/character/routine/asset references and validator. |
| 10 | Two different homes on one engine | PASS both render through the same scene/scripts; route behavior remains under requirement 5. |
| 11 | Character contract | PASS schema plus an actual distinct geometry/AnimationPlayer replacement scene using the same motor/navigation, including initial idle and fallback behavior. Arbitrary imported rigs remain untested. |
| 12 | World schema | PASS schema and both-world validation. |
| 13 | Asset schema | PASS primitive/scene contract, transforms, collision, footprint and provenance. |
| 14 | Activity schema/contract | PASS schema and bounded native lease tests. No real adapter is claimed. |
| 15 | Dot onboarding/master prompt | PASS paste-ready create/expand/asset/character prompts and schema-valid brief example. |
| 16 | Content/station extension without engine surgery | PASS wind-chime manifest/object/station/routine and validator; actual browser arrival at the extension anchor is recorded. |
| 17 | Persistence at v0.1 level | PASS native core revision/recovery and browser save/reload/conflict/failure/backup-repair checks. Simultaneous cross-tab writes retain the documented v0.1 limitation. |
| 18 | Web export demonstrated or exact blocker | PASS early export and both full-world renders. Complete browser interaction acceptance remains separate. |
| 19 | Original prototype preserved | PASS owner-supplied HTML/research preserved separately and labeled historical. |
| 20 | Appropriate tests pass | PASS 46 Python, 71 core, 108 runtime and 26 browser checks; extracted-source rebuild and archive integrity also pass. |
| 21 | Stranger-ready README | PASS entry points, screenshots, actual features, limitations, setup and onboarding; source ZIP rebuild tested. |
| 22 | Accurate build status | PASS durable handoff records actual results, limits and publication progress. |
| 23 | No secrets/private Dot material | PASS final repository/archive hygiene scan and source review. No private world was accessed; only the supplied research and original content are included. |
| 24 | Ready to release | PASS all v0.1.0 local requirements met. Public publication is tracked separately. |

## Explicitly unverified or unavailable

Real ChatGPT work/native-call reporting is unavailable. No mock establishes a live integration. Imported production rigs, photo-to-3D generation, multilevel traversal, hosted transactional state, cross-device synchronization, mobile and other untested browsers are outside this acceptance.

Browser localStorage has no guaranteed cross-tab compare-and-swap; ordinary stale revision conflicts are checked, but simultaneous writers can race. Use one saving tab in v0.1. State/world-pack exports are JSON authoring/backup aids, not a tested in-app restore workflow. See [Core notes](CORE_NOTES.md), [World format](WORLD_FORMAT.md), and [Web export](WEB_EXPORT.md).

## Reproduce the browser evidence

Build and serve the Web export, then run `node tools/browser_acceptance.cjs` with Playwright and Chrome available. [Web export](WEB_EXPORT.md#acceptance-and-troubleshooting) documents setup, the `PLAYWRIGHT_MODULE`/`DOMES_URL` overrides and output files. The script operates an isolated profile. Most checks use the runtime's diagnostic bridge to inspect real Godot state; a separate pointer check verifies a visible canvas control. It is not a full manual UI tour or a real Dot integration test.
