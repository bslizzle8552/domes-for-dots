# Character pipeline

**CLOUD BACKEND / DEVELOPMENT ONLY.** Character modeling, generation, rigging, import and validation run in an authorized operator's worker or contributor environment. The current Character Factory is operator-run; general self-service creation/private upload is not deployed. In the target owner flow, owners supply or approve references, discuss how the Dot sees itself and review the hosted result. They never install Blender, Godot, Python or rigging software. See [cloud architecture](CLOUD_ARCHITECTURE.md) and [owner onboarding](DOT_ONBOARDING.md).

The controller moves a character body; the character definition supplies the replaceable visual and animation vocabulary. Changing who lives in a world should not require rewriting the navigation, station or routine engine.

The [automatic character factory](CHARACTER_FACTORY.md) now implements approved
reference/choice intake, a strict specification, original skinned GLB generation,
twelve semantic clips, package validation and isolated world installation. It
preserves this runtime contract and clearly distinguishes its procedural robot
backend from image-to-3D reconstruction.

## Stable character contract

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

The JSON format remains `schema_version: 1`. The visual origin is at the feet/ground. The engine's default forward direction is `-Z`. `scale` applies to the visual; set explicit body collision and navigation dimensions for its final appearance. A procedural scene exposes `set_action(action: String)` and `get_supported_actions()` for its implemented semantic vocabulary; an animated rig can use an AnimationPlayer with the configured clip map. The controller owns translation, so imported walk clips should be in-place unless a new root-motion contract is implemented.

Useful semantics include `idle`, `walk`, `interact`, `rest`, `phone`, `work` and custom actions. The schema's dictionary lets an asset add names without an engine enum. Availability is explicit: both shipped definitions map unsupported `sit` to grounded `idle`; neither provides a seated animation. Phone is a hand-to-head visual, without a separate handset grip. It does not answer, connect or carry a native call.

## Two runnable character implementations

Moss retains the original lightweight procedural resident. Nova now uses [`articulated_robot.tscn`](../godot/scenes/characters/articulated_robot.tscn), an original stylized robot with a torso, head, arms and legs. The reusable [`articulated_robot_visual.gd`](../godot/scripts/articulated_robot_visual.gd) builds primitive geometry and explicit AnimationPlayer tracks for its joints; palette comes from the character definition. No downloaded model, Blender installation or third-party asset is needed to run it.

| Semantic | Nova clip | Actual visible motion |
| --- | --- | --- |
| `idle` | `standby` | Small torso movement and head turn. |
| `walk` | `stride` | Opposing arm and leg rotation with foot lift; the motor moves the body. |
| `interact` | `reach` | One arm reaches forward. |
| `work` | `console` | Both arms alternate in front of the body. |
| `rest` | `recharge` | Head lowers and arms fold while standing on the floor. |
| `phone` | `listen` | Empty hand raised beside the head. |

Every clip sets every animated joint property, so leaving phone/rest returns the arms and head to the next pose. The rig uses ordinary `Node3D` joints, not skin weights or `Skeleton3D`. It proves a second practical articulated body and clip-based animation through the same controller; it does not prove skeletal retargeting. Work gestures do not establish contact with arbitrary console buttons, and rest does not place the body inside a bed or chair.

## Inspect a character before integrating it

Run the schema/content validator, then load the actual character scenes with Godot:

```powershell
python tools/validate_content.py
& '.tools/godot/Godot_v4.5.1-stable_win64_console.exe' --headless --path godot --script res://tools/audit_characters.gd
```

The audit defaults to every JSON definition in `godot/content/characters/`. To inspect one character and save a reusable JSON report, use a report path whose parent directory exists:

```powershell
& '.tools/godot/Godot_v4.5.1-stable_win64_console.exe' --headless --path godot --script res://tools/audit_characters.gd -- --character res://content/characters/nova.json --output ../artifacts/nova-character-audit.json
```

The report records scene nodes, actual AnimationPlayers/clips/track targets, skeleton bone inventories, declared scale/collision, neutral mesh bounds, and resolved semantic/fallback chains. It fails on missing scene/rig paths, absent declared clips, unresolved track nodes, missing basic actions or fallback cycles. A missing declared clip fails the audit even if a fallback would keep the runtime moving: repair the declaration or deliberately remove that semantic. Procedural scenes must report their implemented vocabulary through `get_supported_actions()`; arbitrary method arguments do not establish a new animation.

The audit loads and executes scene scripts as trusted project code. Review imported scenes first. It is not a security sandbox. Neutral mesh bounds are a useful scale check, not the animated/skinned envelope. It does not establish foot contact, prop grip, compatible seats, appealing motion, browser performance or arbitrary humanoid retargeting; test these separately.

## Replace a character

1. Add a redistributable scene or imported GLB beneath the project. Review embedded scripts as code and record asset provenance.
2. Put the visual's origin at ground level, apply its scale, establish its forward axis and check skeleton/AnimationPlayer paths.
3. Create a new character JSON with its stable ID, scene path, dimensions, action map and fallbacks.
4. Change the world's `character_path`. Do not add a character-name branch in the engine.
5. Validate content and run the character audit. Load the world, visit every station and test both a routine interaction and mock work/call.
6. Check feet, facing, collision clearance, clipping, missing clips and browser export. Repeat with the old character to show the same engine supports both.

A larger character can make old anchors and narrow passages invalid. Adjust world clearance or choose another character; do not shrink collision invisibly and call the pose compatible. Persisted character identity changes also need deliberate handling.

## Blender or generated characters

Blender is an optional developer/cloud production backend. It is never an owner requirement, including when creating or changing a character. A remote worker may export a rigged GLB with compatible materials and animations, import it into Godot, and wrap it in a small scene if node paths or orientation need adjustment. The runtime consumes the same character package regardless of the production backend. Godot's [3D import documentation](https://docs.godotengine.org/en/4.5/tutorials/assets_pipeline/importing_3d_scenes/index.html) describes the import and inherited-scene workflow.

A reference image is input to asset work, not a finished rig. A practical path is: record the Dot's chosen silhouette/palette and owner constraints; author an original primitive character or adapt a licensed model; establish dimensions and ground origin; build or map real idle/walk/interact clips; inspect the scene; integrate it; verify movement and poses in the browser. A simple non-human body can use the original joint rig as an authoring example. Character design remains the Dot's choice within the brief; it need not choose between these two example bodies.

Modeling, topology, rigging, weight painting, animation retargeting and pose adaptation may need manual work. V2 does not automate photo-to-3D generation or promise arbitrary rigs will swap without adaptation. Store reference-source/redistribution notes in metadata without copying private images into a public project. Existing rigged GLBs and user-created models still use the same scene/AnimationPlayer contract after their node paths, clip maps and dimensions have been adapted and tested.

## Character acceptance

```powershell
& '.tools/godot/Godot_v4.5.1-stable_win64_console.exe' --headless --fixed-fps 60 --path godot --script res://tests/test_character.gd
```

The character suite checks real joint transforms for all six Nova actions, transition reset, idle fallback for seating, floor clearance over sampled clip phases, invalid rig/clip/fallback rejection, Moss compatibility, and actual physics movement to every Tidal station through the shared motor. The existing runtime suite additionally swaps in [`replacement.tscn`](../godot/tests/fixtures/replacement.tscn), whose geometry, clip names and facing differ, and tests both worlds' routes/colliders.

These are executable acceptance checks, not a photo reconstruction or humanoid retargeting claim. Inspect the final browser build for recognizable silhouette, scale, forward axis, clipping, work/rest/phone gestures and acceptable motion. See [V2 build record](V2_BUILD.md) for current evidence, [Verification](VERIFICATION.md) for the historical v0.1 baseline, and [Core notes](CORE_NOTES.md) for movement tests.
