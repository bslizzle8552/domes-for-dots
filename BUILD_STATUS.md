# Domes for Dots — build status

Target: v0.1.0. Updated: 2026-10-02.

## Current milestone

M0: inspect source material and installed tools; establish a real Godot 4 3D runtime and test Web export early.

## Completed

- Read the user's build-and-ship request. Workspace contains the two supplied research files (the Downloads paths are no longer present).
- Established this durable handoff file before implementation.

## Verification

- Workspace inspection: PASS (new project, research inputs only).
- Godot, export templates, Blender, browser, GitHub authentication: pending inspection.
- Runtime, schemas, simulation, activity leases, persistence, Web export: NOT YET TESTED.

## Decisions

- Godot 4 + GDScript, 3D, browser-first compatibility renderer.
- Engine, authored content, character contracts, runtime state, and connections remain separate.
- No access to any private Dot world. Native call integration is unavailable unless independently verified; mocks must be labeled.

## Remaining v0.1 blockers

- Implement and verify all core contracts and same-engine example worlds.
- Early Web smoke test, deterministic and runtime tests, visual validation.
- Documentation, onboarding, extension proof, release hygiene, packaging.
- Inspect GitHub capability only after local release readiness.

## Post-v0.1 backlog

- Real activity adapters, richer characters/animations, multi-level navigation, hosted persistence, migrations beyond schema v1.
