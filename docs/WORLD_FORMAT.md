# World format

The source of truth is the versioned JSON schemas in [`schemas/`](../schemas/), together with cross-reference and geometry validation in `tools/validate_content.py`. Do not use the historical HTML prototype's camelCase configuration as a v0.1 world file.

## Separate documents

| Document | What it owns |
| --- | --- |
| Catalog | Discoverable world IDs, titles and local world paths. |
| World | Layout, objects, stations, environment, camera and references to other documents. |
| Character | Visual scene, physical/navigation dimensions, rig and animation contract. |
| Asset manifest | Reusable geometry/scenes, collision, anchors and provenance. |
| Routine | Activity schedule and finite imagined projects. |
| Brief | Owner locks, Dot choices, shared decisions and expansion history. |
| Runtime state | World/character/routine identity, epoch, project IDs, preferences and save revision. |
| Connections | Real integration status and authorization, outside exportable world content. No real adapter ships in v0.1. |

All shipped JSON documents use `schema_version: 1`. Paths inside content use `res://content/...` or another allowed project resource path. Credentials, permissions and private activity payloads do not belong in any world, character or asset document.

## World definition

A world identifies itself with `id`, `version`, `title` and `description`. `brief_path`, `character_path`, `routine_path` and `asset_manifest_paths` reference its collaborators. It has no embedded mutable save counter.

`environment` defines background, ambient and directional light color/energy. `camera` defines a position, target and orthographic size. `spawn` starts the character on the floor. `navigation` defines grid cell size and character clearance. Units are Godot world units, conventionally meters; positions are `[x, y, z]`, and yaw values are degrees.

`zones` are axis-aligned flat floor rectangles with ID, label, center, two-dimensional size and color. Current examples connect them at ground height. `objects` instantiate an `asset_id` with their own ID, position, rotation and scale. A custom room shape may be composed from zones; changing to arbitrary mesh navigation requires further implementation.

`stations` connect an object with activity tags and free approach/interaction positions, facing and semantic animations. Their IDs, object references and tag relationships must resolve. A routine choosing a missing or unreachable station is an authoring error, not permission to walk through the prop.

## Routines and finite projects

A routine declares `cycle_seconds` and ordered steps. Every step has a stable ID, label, activity tag, animation field and positive duration. Step durations must sum to the cycle. The current display chooses a station by activity tag and plays that station's semantic action; the routine's animation field is retained authoring information rather than an override of the station. These compressed cycles demonstrate elapsed-time behavior; v0.1 does not implement civil-time/daylight-saving schedules.

Projects have stable IDs, titles, matching activity tags, required activity seconds, stage labels and a required associated `visual_object_id`. Progress counts time assigned to the matching activity, including completed cycles, and clamps to completion. The display shows the stage label and scales the associated visual's height as a simple progress effect. Nothing in that calculation authorizes real work or generates a novel object.

## Runtime state and upgrades

State identifies `world_id`, `world_version`, `character_id`, `routine_id`, `project_ids`, `schema_version` and `revision`. It stores `routine_epoch` and preferences. Pure simulation derives current step and project progress from the saved epoch and authored routine.

Save callers provide an expected revision. Stale revisions produce a conflict; corrupt or failed writes must preserve known-good content and report an error. Native files and browser local storage are local adapters, not distributed transactional storage. Browser read/check/write is not a guaranteed cross-tab transaction, so use one saving tab and export important state. Deterministic progress still avoids multiplied progress when several viewers read the same epoch.

Keep a state export and versioned source before changing a routine's meaning. Retaining an ID while changing project durations can reinterpret old progress. For v0.1, compatible visual additions can preserve the epoch; changed routines/projects need a deliberate state migration or explicitly chosen fresh timeline. No general migration wizard or cross-device restore UI is promised.

The creative brief remains a separate referenced source file. Preserve it in a source/world backup; a runtime-state export alone is not a backup of meshes, routines or owner decisions. **World pack** exports a JSON authoring bundle with keys `schema_version`, `world`, `character`, `routine`, `assets` (resolved by ID) and `brief`. It does not embed referenced scene/model/texture files and is not a replacement world-schema document or an in-app import format. Keep the full project for an editable asset-complete backup.

## Validation workflow

Run `python tools/validate_content.py` in the development environment after content edits. Resolve schema errors, duplicate IDs, missing paths, invalid references and unreachable anchors before a visual preview. Then test the actual Godot runtime and browser export. Valid JSON cannot prove an imported mesh's appearance, animation quality or performance.

Add a new version before a breaking format change. A future migration must take an explicit old version, write to a new candidate, validate it and preserve the original on failure. Version numbers are not permission to silently reset progress.
