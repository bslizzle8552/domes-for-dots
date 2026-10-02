# Rocky reference pipeline — read-only investigation

Inspected on 2 October 2026. Rocky's working world was not edited or redeployed by this investigation.

## Principal finding

Rocky is a functioning Blender-created character, but his inspected character asset is **not a skinned skeletal rig**. The source package explicitly describes a design prototype with no armature, skinning or animation clips. His Godot world animates separate named character parts procedurally. This is useful evidence for a cloud factory: a convincing character does not require a humanoid skeleton, and the runtime contract must distinguish node articulation, skeletal animation and procedural behavior.

The local Domes V2 repository did not contain Rocky's assets. The supported Codex chat tools identified the current chat titled **Rocky**, on its durable cloud host. Under the user's explicit authorization, that chat was asked to inspect its existing source read-only. Its inspection agent's actual command outputs were read through `read_thread`; the findings below are grounded in those outputs, not inferred from a thumbnail or the earlier starter-kit description.

## Source locations and evidence

These are paths in Rocky's cloud workspace, not paths a Domes owner needs on their device:

| Location beneath `/workspace/scratch/597fe7c06f2f/` | Evidence |
| --- | --- |
| `rocky-blender-v1/README.txt` | Prototype scope, design, hierarchy, orientation and rebuild commands. |
| `rocky-blender-v1/source/build_rocky.py` | Reproducible Blender geometry, material, hierarchy, studio and export construction. |
| `rocky-blender-v1/source/finalize_rocky.py` | Geometry-centered mesh origins, outward normals, final export and dimensional report. |
| `rocky-blender-v1/source/model_report.json` | Blender version, mesh counts and source dimensions. |
| `rocky-blender-v1/source/check_glb.py` and `glb_import_check.json` | Existing GLB reimport verification and evaluated geometry counts. |
| `rocky-blender-v1/Rocky_Character_v1.blend` | Editable Blender source. |
| `rocky-blender-v1/Rocky_Character_v1.glb` | Character-only binary glTF export. |
| `rocky-world-v2/scripts/world.gd` | Character loading, named part lookup, navigation and procedural pose behavior. |
| `rocky-world-v2/README.txt` and `VERIFICATION.txt` | World/bridge contract and explicitly bounded prior acceptance. |
| `rocky-workshop-site/godot-source/` | Site's checked-in Godot source. |
| `rocky-workshop-site/public/rocky-world-bridge.js` | Browser bridge into the hosted world. |
| `rocky-workshop-site/db/world.ts` | Companion state model and persistence implementation. |

The existing hosted reference is [Rocky's Living World](https://rockys-workshop.bslizzle.chatgpt.site). Finding its URL is not an independent browser acceptance test. Its audience was not changed. Rocky's private assets were not copied into this repository or redistributed.

## Reference → geometry → export

The package describes an interpretation of the supplied Rocky pixel-art reference: a large faceted sandstone hood/head, cream face inset, charcoal rectangular eyes, rose square cheeks, asymmetric crest, tapered small torso and detached pebble hands/feet. Side and rear surfaces are explicitly artistic interpretations; the single reference did not establish their complete construction. Actual reference files were found: `rocky-reference/rocky.png` is 166 × 172 pixels and `rocky-reference/rocky-spritesheet-v4.webp` is 1,536 × 1,872. Their original image-generation provenance requires separate evidence and must not be invented.

`build_rocky.py` builds actual mesh geometry with Blender Python. It seeds its small geometric variations with `random.seed(18)`, uses explicit vertex/face construction and primitive cubes, creates materials, and adds bevel/weighted-normal modifiers. It creates a character collection separate from lighting/cameras. **The generator never loads an image:** the modeling coordinates were authored from visual interpretation. This is reproducible scripted modeling, not automatic image-to-3D reconstruction. The source README says the cloud Blender desktop was used for inspection; that historical interactive inspection was not independently observed here. Earlier interactive edits and the original image upload lineage cannot be established from these files alone.

The saved source report records:

- Blender 4.3.2; Cycles studio rendering.
- 14 mesh objects, 361 base vertices and 515 base polygons.
- Source dimensions: width 3.3100864887, depth 1.8801081181, height 3.4018938579 scene units.
- Blender front `-Y`, up `+Z`.
- Reimport check: 14 meshes, 3,942 evaluated vertices and 1,832 polygons after export/import processing. These are a different measurement stage from the base counts.

A fresh **read-only Blender inspection** of the actual `.blend` confirmed metric units, scale length 1.0, no armatures, no actions and no animated objects. A fresh direct parse of the actual GLB confirmed 16 nodes, 14 meshes, 11 materials, **zero skins, zero animations, zero images and zero textures**, with 3,942 exported vertices and 1,832 triangles. Its SHA-256 is `b440d24df5115a137efd19bb3d5937864e79c39435035d1a185a335669a05a28`. The exporter identifies itself as Khronos glTF Blender I/O v4.3.47, producing glTF 2.0. These new inspection results are recorded in [the evidence JSON](validation/rocky-reference-evidence.json); they are distinct from the saved earlier reimport report.

The actual finalization script applies geometry-centered origins, recalculates outward normals, saves the `.blend`, selects only the character collection and calls:

```python
bpy.ops.export_scene.gltf(
    filepath=R+'/Rocky_Character_v1.glb',
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
```

The exporter converts to glTF Y-up. No specific animation-export, Draco, texture-compression or retargeting settings were supplied in this call. Do not turn exporter defaults into deliberate production decisions.

## Articulation, materials and runtime behavior

The source hierarchy has `Rocky_CTRL` as the character root and `Head_CTRL` for the head, crest and face. The 14 named meshes are the faceted head shell, cream face inset, `Eye.L`, `Cheek.L`, `Eye.R`, `Cheek.R`, tapered torso, `Foot.L`, `Foot.R`, `Hand.L`, `Hand.R`, and three crest pieces. These object nodes are not bones. No bone parent map, weights or humanoid retargeter can be reconstructed from a skeleton that is absent.

Materials use simple Principled BSDF/PBR colors, with no external image textures required. The character report lists six sandstone variants plus warm porcelain face, rose-quartz cheeks, charcoal eyes, earthen recess and ochre-brown body. Studio lighting and presentation background are separate from the exported character.

`build_rocky()` in `rocky-world-v2/scripts/world.gd` loads `Rocky_Character_v1.glb`, sets visual scale to `Vector3.ONE * 0.55`, finds `Head_CTRL` and the four named hands/feet, and asserts that imported components exist. It handles both dotted source names and underscore names sanitized by Godot. Runtime props include a modeled mallet, phone receiver, book, watering can and headset. The world controls character translation independently of its part motion. There is no imported root-motion clip to consume.

The exported front faces `+Z`: the face/eye node positions are on positive glTF Z after conversion from Blender `-Y`, and `move_rocky()` turns the resident using `atan2(vector.x, vector.z)`. The imported model has no corrective local yaw in `build_rocky()`. A Domes manifest wrapping this asset would therefore declare `forward_axis: "+Z"`; Domes' shared motor would apply its existing half-turn adapter. Do not label every GLB as `-Z` merely because that is the engine's default convention.

The source world contract distinguishes routine activities `work`, `make`, `read`, `rest`, `garden`, `music` and `stargaze` from real-only `call`. A browser bridge supplies state; routine requests cannot assert a real call. A call poses a handset as a visual response; voice transport remains outside the world. The inspected README describes bridge reads every two seconds, explicit offline simulation when disconnected, and cloud-state rejection warnings. This describes the inspected implementation and does not promise end-to-end native-call latency.

Rocky's completed source inspection identifies `animate_character(delta)` at `world.gd:1175–1239`. It restores the cached base transforms each frame, then applies the current pose. Walking is selected by a nonempty path, not a named clip. Motions are:

| Runtime state | Actual pose mechanism |
| --- | --- |
| Walking | Alternating foot lift/fore-aft movement, opposing hand swing, visual bob and roll. |
| `work` | Typing hand oscillation. |
| `make` | Mallet pose. |
| `call` | Handset pose. |
| `read` | Book pose. |
| `garden` | Watering-can pose. |
| `music` | Key-playing hands. |
| `stargaze` | Telescope pose followed by sketching. |
| `rest` | Sway and head tilt. |

These positions are authored for Rocky's proportions. Props are Godot geometry; there are no bone sockets or inverse-kinematics constraints. Work/make/garden/music face `PI` radians, stargaze faces `PI/2`, and the other stationary states generally face positive Z. A new character still needs contact/prop adaptation.

In the companion's `lib/world/model.ts:125–130`, real `call` maps to office/call, `building` to workshop/make, `coding` and `research` to office/work, and `idle` to home/rest. An unexpired connected lease is required. This is explicit event reporting; it does not demonstrate automatic observation of arbitrary assistant activity.

The inspected world uses Godot 4.6.3, Compatibility rendering and a single-thread Web export. Domes V2's existing toolchain is Godot 4.5.1; copying a newer project's source blindly is not a compatibility guarantee. Rocky's static export preparation gzip-packs the WASM and uses a browser decompression loader; the normal export remains separately available.

## What can be reused safely

| Mechanism | Automation implication |
| --- | --- |
| Reference interpretation and creative decisions | Capture the Dot's appearance choices and the human's vetoes in a reviewed specification. Record uncertain rear/side interpretation. |
| Scripted mesh/material creation | Run a generator in an isolated cloud worker; the owner never installs Blender. Blender is one replaceable backend. |
| Named part hierarchy | Expose semantic joints/capabilities in a package, with a generator-specific adapter. Do not add Rocky filenames to the shared runtime. |
| Procedural poses | Bake verified motions to portable clips or provide a trusted runtime adapter. Do not describe them as existing imported clips or retargeting. |
| Navigation-owned translation | Keep walk motion in place and declare root-motion policy explicitly. |
| World-specific hand/prop placement | Validate props/stations separately; a phone label does not establish handset grip. |
| Scripted export and existing reimport checks | Automate artifact hashes, geometry bounds, hierarchy/clip inventory and a real engine import. |
| Cloud Site and bridge | Deliver a URL and authenticated state; owner devices remain browsers. |

Domes already separates `character_motor.gd`, manifest semantics and the visual scene. Its loaded-scene audit checks real AnimationPlayers, clips, skeleton inventories, fallback resolution and neutral bounds. Extend that contract with generated packages; do not replace it with Rocky-specific branches. The existing Nova joint rig already follows the same broad non-skeletal articulation pattern, though its motions are actual AnimationPlayer clips rather than Rocky's direct procedural updates.

## Limits of this reference evidence

This investigation does not establish arbitrary image-to-mesh reconstruction, automatic skinning, skeletal retargeting, photorealistic materials, arbitrary seated poses, or mobile-browser acceptance. Rocky's own historical verification explicitly limits device/browser coverage and distinguishes pose fixtures from real calls. The working reference demonstrates a reproducible, scripted stylized asset and procedural behavior hosted in a persistent world; a new factory must independently test its generated artifacts and published build.

Fresh hash comparisons in Rocky's inspection verified that the Blender export, world asset and Site's Godot source asset are byte-identical; the two `world.gd` copies are identical; and the Site's packaged world matches the normal and static world exports. The existing source ZIPs also match the current inspected source. Those comparisons establish consistency of the cloud workspace and its built assets, not a new browser run against the live Site. The original character/world files were preserved, and the inspection only wrote separate evidence files under `rocky-pipeline-evidence/`.
