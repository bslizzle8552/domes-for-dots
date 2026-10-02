# v0.1.0 verification

Updated 2026-10-02. The local implementation has passing native core/runtime and browser checkpoint evidence. Final rebuilt Web/package verification and public release publishing remain pending. Historical tests mentioned in `prototype/` are not evidence for the Godot runtime. PASS always refers to the stated scope; pending checks do not become passes because source code exists.

## Evidence recorded so far

| Check | Result | Scope |
| --- | --- | --- |
| Godot toolchain identity | PASS | Portable Godot reports `4.5.1.stable.official.f62fdbde1`; downloaded archive checksum matches the official release checksum. Matching Web templates were used for export. |
| Early Web export | PASS | A real early Godot 3D scene rendered in Chrome using Compatibility/WebGL 2 and a single-threaded export, without browser/engine errors in that smoke test. This was deliberately before full runtime integration. |
| Content schemas and relationships | PASS | Both authored worlds and their referenced content pass the Python validator. |
| Python tests | PASS | 45 authoring/contract checks passed at this checkpoint. Any subsequent tooling/portability test additions require a fresh recorded result. |
| GDScript core tests | PASS | Final native rerun: 71 passed, 0 failed. Covers simulation, bounded leases, revision protection and native state recovery. Browser storage and scene movement have separate checks below. |
| Full-world browser rendering | PASS | Cedar Atelier and Tidal Observatory rendered with distinct layouts/content in the same runtime: studio/terrace versus research deck/bridge/observation wing. Seven versus six stations are exposed. |
| Headless runtime integration | PASS | Final native rerun: 108 passed, 0 failed. All 49 Cedar and 36 Tidal station pairs resolve. The character physically visits all 13 stations and returns, with 13,956 collider-clearance samples. Unreachable targets stop safely. Alternate character geometry/AnimationPlayer clips, initial idle, fallbacks/chains and same-motor movement pass. Navigation initialization now waits for the new region to own the spawn point, bounded to five seconds. |
| Browser state and event acceptance | PASS checkpoint; final rerun PENDING | [26 checks](validation/browser-acceptance.json) passed in Chrome 154.0.8037.97 on Windows: wind-chime arrival, orbital bridge traversal, MOCK pose/priority/expiry/replay rejection, shared epoch, preference reload, unsaved time preview, stale-save conflict, injected quota failure preserving bytes, corrupt-primary recovery, repair, exports, pointer control and no runtime errors. The final navigation synchronization change still requires a fresh Web export and rerun. |
| Documentation | PASS | Local Markdown targets resolve; onboarding and activity JSON examples validate against their published schemas. Source review separates executed behavior from future contracts. |
| Release archives, hygiene and publishing | PENDING | Clean source/Web archives, checksum verification, final secret/private-material review, tagging and public publishing remain release work. |

Selected sanitized browser evidence is included in [`docs/validation/`](validation/) and [`docs/images/`](images/): [Cedar Atelier](images/cedar-atelier.png), [Tidal Observatory](images/tidal-observatory.png), and the [MOCK phone pose](images/mock-phone.png). Other screenshots, downloaded state and raw outputs remain ignored development artifacts. Final release evidence should identify the tested commit and resulting archive checksums. [BUILD_STATUS.md](../BUILD_STATUS.md) tracks the current build milestone.

## Release requirements

| # | Requirement | Acceptance state and evidence |
| --- | --- | --- |
| 1 | Coherent, clean repository | PENDING final hygiene/package review; documented source layout exists. |
| 2 | Godot project opens/runs | PASS export/import, live browser execution and final native integration suite. |
| 3 | Real simple 3D world | PASS browser rendering of both actual Godot worlds. |
| 4 | Character exists | PASS original procedural resident rendered in the full scenes. |
| 5 | Character navigates to multiple stations | PASS all 85 native station-pair paths, physical visits to all 13 stations plus returns, and checkpoint browser wind-chime/call/bridge travel. Final browser rerun remains listed above. |
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
| 20 | Appropriate tests pass | PASS current content/native suites and 26-check browser checkpoint; final rebuilt Web rerun and package checks PENDING. |
| 21 | Stranger-ready README | PASS entry points, actual features, limitations, setup and onboarding documented; final command/archive check pending. |
| 22 | Accurate build status | PASS current M3 handoff; final reconciliation with rerun outcomes and release artifacts remains required. |
| 23 | No secrets/private Dot material | PENDING final repository/archive scan. No private world was used; only owner-supplied research and original content were authored here. |
| 24 | Ready to release | PENDING until the remaining checks and packaging complete. |

## Explicitly unverified or unavailable

Real ChatGPT work/native-call reporting is unavailable. No mock establishes a live integration. Imported production rigs, photo-to-3D generation, multilevel traversal, hosted transactional state, cross-device synchronization, mobile and other untested browsers are outside this acceptance.

Browser localStorage has no guaranteed cross-tab compare-and-swap; ordinary stale revision conflicts are checked, but simultaneous writers can race. Use one saving tab in v0.1. State/world-pack exports are JSON authoring/backup aids, not a tested in-app restore workflow. See [Core notes](CORE_NOTES.md), [World format](WORLD_FORMAT.md), and [Web export](WEB_EXPORT.md).

## Reproduce the browser evidence

Build and serve the Web export, then run `node tools/browser_acceptance.cjs` with Playwright and Chrome available. [Web export](WEB_EXPORT.md#acceptance-and-troubleshooting) documents setup, the `PLAYWRIGHT_MODULE`/`DOMES_URL` overrides and output files. The script operates an isolated profile. Most checks use the runtime's diagnostic bridge to inspect real Godot state; a separate pointer check verifies a visible canvas control. It is not a full manual UI tour or a real Dot integration test.
