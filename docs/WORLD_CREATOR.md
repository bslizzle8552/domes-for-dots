# Autonomous World Creator: first bounded implementation

World Creator turns a synthetic Dot's creative brief into data consumed by the existing Domes runtime. It reuses Character Factory packages, runtime content schemas, asset recipes, semantic animations, content validation and guarded world authoring. It does not generate per-world scripts. The examples are synthetic decisions recorded for testing, not claims of conversations with actual Dots.

The current operator pipeline is:

```
owner boundary + six Dot answers -> WorldIntent -> WorldSpec
    -> registered semantic_grid_v1 compiler -> World Package
    + independently validated Character Package -> Composer
    -> isolated Godot project -> engine/browser acceptance -> host adapter
```

The owner visits the exported browser world. Python/Godot/other development dependencies belong to the operator or cloud build infrastructure. These command-line tools are not an owner installation requirement. Automatic end-user private Site provisioning is a separate deployment capability; see the run's Site evidence before claiming it exists.

## Intent and specification

`schemas/world-intent.schema.json` has strict fields for Dot identity, owner constraints, creative decisions, shared choices, zones, activities, meaningful objects, expansion ideas and unsupported wishes. Important choices carry `chosen_by` (`dot`, `human`, `collaborative`, `compiler`) and a reason. No private conversation transcript is stored.

The owner boundary includes private deployment, zone/object/span limits, recipe/action vetoes, accessibility flags and protected stable IDs. The compiler enforces numeric bounds, veto tags, identity and `single_level_only`. `must_haves`, `reduced_motion`, `touch_requested`, aesthetic text and unsupported wishes are retained for review; they are not falsely certified as fulfilled features. The package explicitly records those limits.

`tools/world_intent.py` is the current interview adapter. The model supplies the creative answers; there is no hidden model call, background consciousness, paid generator or native activity feed. `intent_to_spec(intent, character_manifest)` validates input and creates a semantic spec. Its geometry authority comes from trusted source code, not generated text.

`world-spec.schema.json` is the common envelope; `semantic-grid-world-spec.schema.json` adds the registered compiler's strict vocabulary. Current WorldSpec stores topology, zones, object recipes/actions, palette, a character capability profile, provenance and the source intent hash. The compiler receives exact stable semantic IDs but chooses dimensions and placements itself.

## Bounded topology and physical fit

All spaces are open pavilions with explicit rectangular support surfaces. Enclosed rooms, arbitrary walls/doors, caves and unconstrained architecture are not supported.

| Family | Physical structure |
| --- | --- |
| `single_room` | One 8 m square support surface |
| `linear` | Two to six adjoining 8 m squares along X |
| `courtyard` | Three adjoining 8 m squares forming an L; an open corner creates spatial variety |
| `two_level` | Two 8 m squares at Y=0 and Y=3, separated by an 8 m run straight ramp |

The current grammar uses four furniture reservations per zone and leaves central circulation free. More objects require an additional supported zone or a reviewed grammar extension. It accepts grounded characters with `-Z` forward, radius at most 0.7 m and height at most 2.6 m. Radius is the greater of declared navigation/collision radius. Character idle/walk must resolve; World Creator does not inspect or assume a particular skeleton/producer.

The two-level runtime contract adds optional `levels`, `zones[].level_id`, `stations[].level_id` and `transitions` to the existing world schema. A `straight_ramp` records source/destination levels, edge entry/exit, width, rise, run, headroom, two interior safe fallback anchors, bidirectionality and `hold_supported` interruption. Current examples use width 3.5 m and slope 3/8. Fallback anchors extend the ramp centerline into the floors. This is a game-world capability, not a building-code certification.

Static validation checks elevation, footprint support, collision overlap, full-width floor/ramp continuity, slope/body fit, landing clearance, swept ramp body clearance, reachable stations and reachable zones. Godot runtime tests separately establish actual collider support, traversal, redirection, interruption and reload behavior. A static package receipt explicitly leaves engine/browser acceptance pending.

## Asset and station contract

The trusted catalog implements original `workbench`, `reading_desk`, `shelf`, `planter`, `telescope`, `sculpture` and `lamp` primitive compositions. Assets have local `front_approach` and `interaction` anchors. `anchor_to_world` applies instance scale, Godot Y rotation and translation; generated world-space stations are derived from those anchors.

Supported stationary templates are inspect, work, read, garden, observe and tinker. Their verified contract is navigate to a clear approach, face the object, and select the character's implemented semantic animation/fallback. No template promises physical hand contact, IK, tools changing objects, completed real work or sit/bed fit. Unsupported character actions explicitly fall back to idle inspection and appear in limitations. A visible object does not acquire new executable behavior.

Camera framing derives from floor extents; colors come from the recorded palette; lighting uses bounded existing environment fields. The compiler emits the existing world/assets/routine/brief documents. Routines are marked SIMULATED and do not create architecture or real project progress merely because time passes.

## Repair, packages and composition

`compile_world(spec, character, max_repairs=2)` returns world, assets, routine, brief and a receipt. Optional spec `position_hint` is a solver suggestion. A suggestion outside its assigned feasible slot produces a violation and a targeted placement repair; unrelated objects/choices remain fixed. The budget is bounded to 0–4, each repair is recorded, and exhaustion fails with the named object and constraint. Other unsupported inputs fail honestly rather than inventing a repair.

`world-package.schema.json` is a compiler-independent envelope: identities, compiler/version, explicit document roles, file hashes, character requirements, provenance, limitations and validator metadata. `tools/world_package.py` enforces bounded local regular files, complete digests, declared roles and registered compiler dispatch. It never imports a module named by package data. The current registered compiler alone restricts its payload to strict JSON and recomputes exact output from the validated intent/spec/character profile. Altering geometry and recomputing hashes cannot bypass that check; a stored success receipt grants no authority. Future producers require trusted registration and strict asset validation.

`build_package(intent, character_package_dir, output_dir)` validates the real Character Package first and creates a new immutable directory. Character provenance is bound by its package-manifest SHA-256. `validate_package(directory)` rechecks everything, including deterministic recompilation.

`tools/world_composer.py` exposes `compose(world_package, character_package, output_repo)` and `compose_many(pairs, output_repo)`. It checks both producer validators, character identity/capability equality, package hashes and colliding IDs; copies the approved character asset mappings; writes generated documents into an isolated project using the existing runtime; and runs the full content validator. The source runtime project and published releases remain unchanged. The composition receipt leaves export/browser/hosting results pending until they actually run.

Current implementation limits are explicit: 4 MiB world package data, JSON-only registered world compiler payload, at most six zones and 48 semantic object records (four placed objects per zone), fixed pavilion/ramp dimensions, no executable generated scenes, no URLs, no paid generation. These are implementation bounds, not measured product performance targets.

## Revisions and provenance

Generated meaningful/protected objects become immutable `brief.owner_locked.entity_protection` records with stable object IDs, protected fields, author and reason. Revision authoring operates on installed runtime documents through `world_revisions.py` and `world_author.py`. The immutable World Package remains the original compiled seed. Later changes record base/source hashes, operations and revision provenance; an edited runtime world is not mislabeled as exact seed compiler output.

Intent, structure, runtime state, compiled output and revision history are separate. Unrelated owner edits survive narrow operations. Revision conflict/recovery/rollback tests belong to `test_world_revisions.py`; a structural rollback must not erase unrelated durable progress.

## Reproduction and evidence

From the repository's development Python environment:

```powershell
python examples/world_creator/generate_examples.py --output artifacts/world_creator/rebuilt --stage artifacts/world_creator/rebuilt-stage
python -m unittest discover -s tests -p test_world_creator.py -v
python tools/world_package.py validate examples/world_creator/lumen_observatory.world
```

Use new output directories for new immutable packages. The generator reuses the independently authored public Character Factory reference card through the existing registered producer, with distinct synthetic identities, palettes, proportions and creative briefs. It does not copy Rocky's assets or identity. Examples are Ember's linear foundry, Lumen's elevated observatory and Fern's garden courtyard. They differ in topology, activities, geometry placement and character packages, not only colors.

Package receipts prove static acceptance only. Consult current completion/validation reports for exact Godot, browser, host, state, revision and performance evidence. A successful export alone is not a successful private deployment.

## Operator cloud execution

`.github/workflows/world-creator.yml` runs the same three independent synthetic inputs on an ephemeral GitHub Actions worker. `tools/world_creator_worker.py` regenerates each Character Package from its approved spec, compiles each World Package, composes all three, imports them with pinned Godot 4.5.1, audits actual characters, runs each producer's registered motion contract, runs generated-world/multilevel physical acceptance, and exports one shared Web runtime. It reuses `setup_cloud_godot.py` and the checked engine runner from the existing Character Factory build infrastructure.

The immutable job directory contains phase durations, source/engine/package/export SHA-256 hashes, independent validation results and engine logs. Failure preserves diagnostics and never claims publication. Web artifacts include licenses. The workflow does not publish, grant private access, or claim browser playback; those gates need separate evidence for the exported bytes. This operator-dispatched proof does not implement generalized self-service creation or authentication.
