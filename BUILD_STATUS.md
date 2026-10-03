# Domes for Dots — build status

## Autonomous World Creator experiment · 2026-10-02

Based on merged main `c4fb1e2743ede9750582750b3e531fc2e0549aa5`, including Character Factory PR #1. The earlier pre-merge notes below are historical. This feature is [draft PR #2](https://github.com/bslizzle8552/domes-for-dots/pull/2), not a new release.

Implemented: semantic intent/spec/package compiler, three independent synthetic layouts and compatible characters, straight-ramp physics and navigation, protected narrow revisions and recovery, and a reusable owner-private Site adapter with D1 state and approved primitive JSON loading. [Cloud worker run](https://github.com/bslizzle8552/domes-for-dots/actions/runs/37080816856) succeeded. Final local shared Web runtime passed 47 browser checks; native suites passed 611 assertions. Hosted and consolidated evidence is recorded in the [completion report](AUTONOMOUS_WORLD_CREATOR_COMPLETION_2026-10-02.md).

The new [private World Creator Lab](https://domes-world-creator-lab.bslizzle.chatgpt.site) is separate from Rocky and Aster. The owner installs nothing. Current boundaries: operator-mediated compilation/publication, bounded primitive layouts, straight ramps only, stationary simulated station animations without IK/contact guarantees, desktop Chromium acceptance, and no native ChatGPT work/call feed. General self-service provisioning and arbitrary live executable assets are unavailable.

## Post-V2 cloud character increment · 2026-10-02

**Historical pre-merge cleanup:** generic package v2 + mandatory strict producer validation; accurate proof/operator/target wording; Sites preferred for a private-world experiment while hosting stays portable. [Cleanup files and acceptance](docs/CHARACTER_FACTORY_CLEANUP.md). PR #1 was subsequently merged; the experiment above supersedes this earlier pending status.

The current development branch implements approved-reference/specification transport, a deterministic skinned GLB factory, validated isolated world installation and a real GitHub-hosted Godot export. [The dispatched cloud job passed](https://github.com/bslizzle8552/domes-for-dots/actions/runs/37071571343). See the [completion report](docs/AUTOMATIC_CHARACTER_COMPLETION.md), [cloud build receipt](docs/validation/factory-cloud-build.json), [Rocky investigation](docs/ROCKY_REFERENCE_PIPELINE.md), [capability inventory](docs/CAPABILITY_INVENTORY.md) and [dependency audit](docs/VIRTUAL_ONLY_AUDIT.md).

**Hosted proof: PASS. [Visit Aster's generated world](https://bslizzle8552.github.io/domes-for-dots/).** GitHub Pages serves the verified cloud artifact from publication commit `a40d43059ad08ef1448d4979331500ea7a1ae8a4`. All 16 anonymous downloads matched the cloud file hashes; all nine hosted desktop Chromium checks passed, including actual bone motion, navigation, station clips and same-browser reload. [Hosting evidence](docs/validation/factory-hosted-acceptance.json) and [capture](docs/images/factory-aster-hosted.png). The public specimen uses synthetic preferences and an original reference, with the existing Cedar Atelier template.

Owner documentation now distinguishes the verified installation-free visit, operator-managed generation/build/hosting, and target conversation-to-private-world experience. General self-service creation and automatic private Site provisioning are not deployed. The prototype generates a bounded original segmented robot from approved structured choices; it does not reconstruct image geometry. Production authentication/private storage, cross-device saves, arbitrary retargeting and mobile acceptance remain pending. Existing source worlds and Rocky's working world were preserved.

The v0.2.0 release below is historical and has not been replaced by this development increment. Its original acceptance and publication records remain intact.

## Published V2 release

Current release: **V2 / 0.2.0 publicly released and independently download-verified**. Updated: 2026-10-02.

The published V2 runtime is unchanged. **PASS at release:** 70 Python tests, 92 core assertions, 200 runtime assertions, 43 character assertions, three character audits and 37 browser checks. The clean build, source-archive rebuild and release preparation are recorded in [docs/V2_BUILD.md](docs/V2_BUILD.md). No public world hosting was deployed as part of that release.

## v0.2.0 publication receipt

- Published: **2026-10-02T14:42:06Z**, following explicit owner authorization for this release.
- Public release: [Domes for Dots v0.2.0](https://github.com/bslizzle8552/domes-for-dots/releases/tag/v0.2.0).
- Published source and unchanged annotated tag commit: `9e00fea63e45e1a3ed5a91290d63ce0a04300ff4`.
- Clean runtime build commit: `a2786137c82d75fb04ff120dc8d46b8e3d088a53`; the release commit changes documentation/evidence only.
- GitHub validation: **PASS** for [main run 37021479228](https://github.com/bslizzle8552/domes-for-dots/actions/runs/37021479228) and [tag run 37021479256](https://github.com/bslizzle8552/domes-for-dots/actions/runs/37021479256) on the released commit.
- Exactly four prepared assets published: source ZIP, Web ZIP, `SHA256SUMS` and `release_manifest.json`.
- Public verification: **PASS**. The release page is anonymously reachable with the correct tag/title and rendered description. All four assets were downloaded without authentication and matched the prepared local copies by SHA-256.
- [Machine-readable publication evidence and all four hashes](docs/validation/v0.2.0-publication.json).
- This post-publication receipt is recorded on `main`; the published `v0.2.0` tag and packaged source remain fixed. No publication steps remain pending.

## Historical v0.1.0 milestone

M6: v0.1.0 published and verified. No remaining v0.1.0 implementation or publication blockers.

- Repository: https://github.com/bslizzle8552/domes-for-dots
- Release: https://github.com/bslizzle8552/domes-for-dots/releases/tag/v0.1.0
- Release source/tag commit: 738fa7e24aca5997c874e58507670efac7ad28b4.
- Runtime build commit: 2039920faad095ff1de5aa856f77d4212b9ef8bf. Later commits change documentation/evidence only.
- Public assets were downloaded anonymously and compared byte for byte by SHA-256 to the locally verified packages: PASS.
- GitHub CI for the release commit: PASS, https://github.com/bslizzle8552/domes-for-dots/actions/runs/37009910087 .
- The immutable release source records acceptance before publication. Main additionally contains this post-publication receipt.

## Completed

- Read the user's build-and-ship request. Workspace contains the two supplied research files (the Downloads paths are no longer present).
- Established this durable handoff file before implementation.
- Preserved supplied research under prototype/, initialized Git and committed the starting architecture.
- Installed ignored portable Godot 4.5.1.stable.official.f62fdbde1; editor and matching template SHA-512 checks match the official release checksums.
- Built a real Compatibility-rendered GDScript 3D runtime: manifest loader, composed assets, replaceable character visual, generic stations, planar NavigationMesh/NavigationServer3D paths, CharacterBody3D motion, UI and mock-only browser bridge.
- Authored Moss's Cedar Atelier and Nova's Tidal Observatory, with different layouts, props, activities, projects and character definitions.
- Added independent wind-chime manifest/station extension and nine strict versioned schemas.
- Added onboarding, expansion, asset and character prompts; architecture and authoring docs.
- User clarified Dots have Godot and Blender on their VMs. Local Windows inspection did not find either in standard locations; local portable installation is for this build's validation.

## Verification

- Workspace inspection: PASS (new project, research inputs only).
- Godot headless startup and matching Web export: PASS.
- EARLY Web smoke in isolated Chrome, actual 3D rendered/WebGL2/single-threaded: PASS, no browser errors. artifacts/early-web.png (local verification evidence).
- Full runtime renders both example worlds in Chrome and switches between them: PASS. Initial UI clipping fixed with bounded scrolling; lighting adjusted after visual inspection.
- GDScript deterministic core suite: PASS (71 assertions).
- Python content/release-tool suite: PASS (46 tests, including source-archive operation without Git metadata).
- Content validator: PASS both worlds and extension.
- Native runtime integration: PASS (108 assertions, all 49 Cedar and 36 Tidal station pairs, physical visits to every station plus returns, 13,956 collider-clearance samples, safe unreachable target, replacement geometry/AnimationPlayer/fallbacks/navigation).
- Startup synchronization bug found and fixed: wait for the newly created navigation region to own the spawn point, with a 5-second timeout; do not infer readiness from two frames alone.
- Browser acceptance: PASS (26 checks) again on the final export, including both worlds, mock priority/expiry/pose, data-only extension, bridge crossing, save/reload/shared epoch/project IDs, stale revision conflict, injected storage failure preserving original bytes, backup recovery, downloads and pointer input.
- Clean build: PASS from runtime source commit 2039920faad095ff1de5aa856f77d4212b9ef8bf, recorded with source_dirty=false in docs/validation/build-manifest.json. Later commits update documentation/evidence only.
- Archive acceptance: PASS source/Web ZIP CRCs and SHA-256 inventories. Extracted source rebuilt with 46 Python, 71 core and 108 runtime passes and a new Web export without Git metadata.
- Repository hygiene: PASS tracked-only package scan, review of authored files, no private Dot world or secrets found. Toolchains, caches, local saves, downloaded test exports and credentials are excluded.
- Public repository created: https://github.com/bslizzle8552/domes-for-dots . The original request authorizes publication after validation.

## Decisions

- Godot 4 + GDScript, 3D, browser-first compatibility renderer.
- Engine, authored content, character contracts, runtime state, and connections remain separate.
- No access to any private Dot world. Native call integration is unavailable unless independently verified; mocks must be labeled.

## Release artifacts

- `dist/release/domes-for-dots-v0.1.0-source.zip`: 611,468 bytes; 106 tracked source files. SHA-256 `0337f3364426a98f84de8e94f8a50bb473bb1b1e5248d0cc003b62fcc33daf1d`.
- `dist/release/domes-for-dots-v0.1.0-web.zip`: 9,512,459 bytes; runtime, notices, launch README and build/release manifests. SHA-256 `edf7e9986845c1ac7b83c66d8f2aaf56e8770353a63cdf3687d3dcec2c52f0a3`.
- `dist/release/SHA256SUMS` and `release_manifest.json` are also published.
- Both source and Web archives passed CRC/inventory checks. Downloaded public files matched the prepared files, including manifest and checksum assets. Tag v0.1.0 resolves to the release source commit above.
- Local preview: http://127.0.0.1:8060 while tools/serve.py is running. No public world hosting or real activity connection was provisioned.

## Reproduce verification

```powershell
.\.venv\Scripts\python.exe tools/build.py
.\.venv\Scripts\python.exe tools/serve.py --port 8060
node tools/browser_acceptance.cjs
.\.venv\Scripts\python.exe tools/check_release.py
.\.venv\Scripts\python.exe tools/package_release.py
```

Use Godot 4.5.1 plus matching templates; set GODOT_BIN if it is not discoverable. The browser script requires Playwright and Chrome. See docs/GETTING_STARTED.md and docs/WEB_EXPORT.md. Tests, schema validation, engine-error log checks and Web export are included in build.py.

## v0.1 limits

- Real work/native-call adapters unavailable; mock events never establish integration.
- One saving browser tab recommended: stale revisions are detected, but localStorage is not an atomic cross-tab transaction or hosted state.
- Flat connected floors, static footprints, simple standing/hand poses; arbitrary rigs, stairs, mobile and other browsers are unverified.
- New content is authored JSON/scene data and rebuilt; in-app import/editing and automatic photo-to-rig generation are not shipped.

## Post-v0.1 backlog

- Real activity adapters, richer characters/animations, multi-level navigation, hosted persistence, migrations beyond schema v1.
