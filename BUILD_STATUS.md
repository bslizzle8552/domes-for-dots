# Domes for Dots — build status

Target: v0.1.0. Updated: 2026-10-02.

## Current milestone

M4: implementation accepted locally; final clean Web build, package audit and GitHub publication in progress.

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
- Browser acceptance: PASS (26 checks), including both worlds, mock priority/expiry/pose, data-only extension, bridge crossing, save/reload/shared epoch, stale revision conflict, injected storage failure preserving original bytes, backup recovery, downloads and pointer input. Final export rerun pending.
- GitHub authenticated account/capability inspection: PASS, bslizzle8552 can create repositories and releases. Target repository does not yet exist. Publication is authorized by the original build-and-ship request, after final checks.

## Decisions

- Godot 4 + GDScript, 3D, browser-first compatibility renderer.
- Engine, authored content, character contracts, runtime state, and connections remain separate.
- No access to any private Dot world. Native call integration is unavailable unless independently verified; mocks must be labeled.

## Remaining v0.1 blockers

- Final clean Web build and rerun browser acceptance on that export.
- Final doc reconciliation, secret/private-material audit, source/Web archives with checksums, archive extraction smoke test.
- Create public domes-for-dots repository, push main, tag v0.1.0, upload/publish/verify release.

## Post-v0.1 backlog

- Real activity adapters, richer characters/animations, multi-level navigation, hosted persistence, migrations beyond schema v1.
