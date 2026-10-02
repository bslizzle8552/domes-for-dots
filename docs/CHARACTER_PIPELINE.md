# Character pipeline

The controller moves a character body; the character definition supplies the replaceable visual and animation vocabulary. Changing who lives in a world should not require rewriting the navigation, station or routine engine.

## Version 1 contract

See [`character.schema.json`](../schemas/character.schema.json) and the examples in [`godot/content/characters/`](../godot/content/characters/).

| Field | Purpose |
| --- | --- |
| `id`, `display_name`, `schema_version` | Stable identity, presentation and format. |
| `scene_path`, `scale`, `forward_axis` | Visual scene and its orientation relative to the controller. |
| `collision.radius`, `collision.height` | Explicit character body dimensions in world units. |
| `navigation.radius`, `navigation.speed` | Explicit route clearance in world units and speed in world units per second. |
| `rig.skeleton_path`, `rig.animation_player_path`, `rig.notes` | Paths and compatibility expectations inside the visual scene. |
| `animations` | Semantic action names mapped to actual animation clips. |
| `fallbacks` | Unsupported semantic action mapped to a supported simpler action. |
| `appearance`, `metadata` | Placeholder styling and descriptive, non-secret information. |

The current visual origin is at the feet/ground. The engine's default forward direction is `-Z`. `scale` applies to the visual; set explicit body collision and navigation dimensions for its final appearance. A placeholder scene exposes `set_action(action: String)`; an imported rig can use an AnimationPlayer with the configured clip map. The controller owns translation, so imported walk clips should be in-place unless a new root-motion contract is implemented.

Useful semantics include `idle`, `walk`, `interact`, `sit`, `phone`, `work` and custom actions. The schema's dictionary lets an asset add names without an engine enum. Availability is explicit: the shipped `sit` semantic intentionally falls back to grounded `idle`; it is not a seated animation. The placeholder raises a hand for `phone`, but does not pick up a separate handset mesh. A fallback pose does not establish a tested prop grip.

## Replace a character

1. Add a redistributable scene or imported GLB beneath the project. Review embedded scripts as code and record asset provenance.
2. Put the visual's origin at ground level, apply its scale, establish its forward axis and check skeleton/AnimationPlayer paths.
3. Create a new character JSON with its stable ID, scene path, dimensions, action map and fallbacks.
4. Change the world's `character_path`. Do not add a character-name branch in the engine.
5. Validate content, load the world, visit every station and test both a routine interaction and mock work/call.
6. Check feet, facing, collision clearance, clipping, missing clips and browser export. Repeat with the old character to show the same engine supports both.

A larger character can make old anchors and narrow passages invalid. Adjust world clearance or choose another character; do not shrink collision invisibly and call the pose compatible. Persisted character identity changes also need deliberate handling.

## Blender or generated characters

Blender is an optional authoring tool, never required just to run a shipped world. Export a rigged GLB with compatible materials and animations, import it into Godot, and wrap it in a small scene if node paths or orientation need adjustment. Godot's [3D import documentation](https://docs.godotengine.org/en/4.5/tutorials/assets_pipeline/importing_3d_scenes/index.html) describes the import and inherited-scene workflow.

A reference image is input to asset work, not a finished rig. Modeling, topology, rigging, weight painting, animation retargeting and pose adaptation may need manual work. Version 0.1 does not automate photo-to-3D generation or promise arbitrary rigs will swap without adaptation.

The shipped examples share a simple original placeholder. The 108-check native runtime suite also swaps in a separate test scene with different box geometry, clip names and an AnimationPlayer. It verifies actual animated transforms, initial idle, missing-clip/station fallback, fallback chains and navigation through the same motor without an engine change. That establishes the replacement-scene contract; it does not establish production skeleton retargeting or arbitrary GLB compatibility. See [Verification](VERIFICATION.md) and [Core notes](CORE_NOTES.md).
