# Asset and station pipeline

An asset describes reusable content. A world object places one instance. A station describes how the character can approach and interact with that instance. Those three records can add an ordinary object and activity without an engine edit.

## Asset manifest

Each manifest contains `schema_version`, an `id` and `assets`. Asset IDs must be unique across the manifests used by a world. See [`asset.schema.json`](../schemas/asset.schema.json).

An asset records its display name, category/tags, scene path or primitive parts, scale/yaw, collision box, footprint, anchors, animation/behavior strings, metadata and provenance. Use empty animation/behavior strings when no extra action applies. A primitive part uses box, cylinder or sphere geometry with position, size, rotation, color and an emission value (`0` for none). These are geometry primitives, not a list of permitted furniture types.

Leave `scene_path` empty to build the listed parts. For a custom model, add an imported GLB/GLTF or compatible Godot scene under the project and reference its `res://` path. Run Godot import before export. Keep all dependencies with the asset; do not point content at a creator's local filesystem or an authenticated URL.

Transforms affect visuals and obstacle footprints. Set a conservative footprint that covers the occupied floor area, then keep station approach and interaction positions outside it with character clearance. A decorative non-colliding object should not obstruct movement visually.

## Add an ordinary station

1. Add the asset to a manifest with provenance.
2. Add that manifest to the world's `asset_manifest_paths`.
3. Add a world object with a unique ID, `asset_id`, position, yaw and scale.
4. Add a station with a unique ID, `object_id`, activity tags, world-space approach/interaction positions, facing, animation and fallback.
5. Add a routine step using the same activity tag, with durations still summing to `cycle_seconds`.
6. Validate, run the world and visit the station from the other zones. Export and inspect the browser result.

`approach` and `interaction` are already in world coordinates; they are not automatically transformed asset anchors. Keep them correct if an object moves. `facing` uses degrees. A station's activity tags identify uses, not a fixed station class. An empty `behavior` means ordinary arrival and semantic animation. Asset-level `anchors`, `animation` and `behavior` retain authoring information; the current builder does not automatically execute them. Rendered character actions come from station semantics, and arrival hooks use the station's `behavior`.

## Shipped extension proof

The separate [`wind_chime.json`](../godot/content/assets/wind_chime.json) manifest defines `hanging_chime`. Cedar Atelier references it, places `terrace_chime`, adds station `wind_chime` with tag `chime`, and schedules that tag in its routine. Its `music` semantic falls back to `interact`; it does not imply synthesized sound or a hand-authored performance.

This is the intended extension mechanism: a manifest plus world and routine content, using generic station handling. There is no wind-chime object enum or special central engine case. The validator and runtime acceptance should continue to cover the added route.

V2 also exercises [a telescope request](../examples/authoring/lantern_archive/telescope.proposal.json) through the authoring CLI. It adds a primitive asset, placement and reachable `observe` station to Lumen's terrace, leaving the saved schedule meaning unchanged. The new station can be visited manually or through a labeled tagged MOCK activity. The [pilot instructions](../examples/authoring/lantern_archive/README.md) explain reproduction and the boundary around changing an existing timeline.

To inspect the proof, open Cedar Atelier, select **Play the four-note chime**, and choose **Visit**. The character should leave the studio, enter the terrace, stop at the clear anchor and perform the generic interaction fallback. **Resume routine** returns control to the schedule. The separate manifest, world placement/station and `chime_pause` routine step are the only content records required; a new sound-producing behavior would be additional work. See [Verification](VERIFICATION.md) for the actual automated/browser result.

## What still needs code

New geometry/layouts within the current contract are data. New visual action clips need compatible assets. Novel interaction mechanics such as opening a physics door, lifting an object, playing an instrument with actual audio or switching scenes need reviewed behavior code and tests. The main runtime exposes `register_behavior(id, callback)` and calls a registered station hook on arrival with the motor, station and object node. Metadata and an arbitrary `behavior` string do not create that implementation. Only capabilities explicitly registered by application code are available.

Imported scenes may contain scripts and are trusted project code. The runtime is not a sandbox for untrusted downloaded scenes. Review scene dependencies, license and cost of materials/meshes before shipping them in the browser.

V2 includes one reviewed `activity_light` station behavior: it adds a small local light at arrival and removes it when the resident leaves, the activity is interrupted or the world changes. It indicates visual occupancy; it does not create a real external activity. Registered arrival callbacks may return a cleanup callable. Asset-level behavior strings still do not execute automatically.

## Provenance

Record `creator`, `source` and `license` for each asset, plus modifications and attribution obligations in metadata where needed. Original primitive compositions in this project use MIT. Third-party assets keep their own terms; a world manifest does not relicense them. Avoid checking in personal reference images or downloaded assets until redistribution is established.
