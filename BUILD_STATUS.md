# Domes for Dots — build status

Target: v0.1.0. Updated: 2026-10-02.

## Current milestone

M5: all local v0.1.0 acceptance and packaging checks pass. Public repository created; tag and release upload are the remaining publication steps.

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

## Remaining publication steps

- No implementation blockers remain at the stated v0.1 level.
- Commit final evidence/docs, regenerate final archives, push main and v0.1.0, publish/verify release downloads.

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
