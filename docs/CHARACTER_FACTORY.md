# Automatic character factory

The implemented factory takes an approved reference image and structured Dot/human
choices, produces a validated specification, generates a skinned animated GLB,
packages the existing Domes character manifest, and installs it into an isolated
copy of a world. The cloud worker imports that copy into Godot, audits the actual
rig and clips, tests animation behavior, and exports browser files.

This is backend infrastructure. Owners contribute references and preferences,
approve the proposed character, and visit a hosted URL. None of the commands below
are owner onboarding steps. Python, GitHub, Godot and export tooling belong to the
operator/CI environment.

## What the implemented backend produces

[`factory_glb.py`](../tools/factory_glb.py) is a deterministic pure-Python glTF 2.0
writer. It creates original segmented robot geometry, material colors, a real
18-joint skeleton, inverse bind matrices, rigid vertex weights, and twelve
skeletal clips. It requires no Blender or external 3D service.

The backend consumes approved **structured choices**, not image pixels. The
reference image is input evidence with its approved description, source, rights
declaration and SHA-256 digest. A capable upstream assistant can use image
understanding to help prepare those choices. This worker does not perform image
understanding, image-to-3D reconstruction, texture extraction or likeness matching.

The supported choices are deliberately bounded:

| Choice | Implemented range |
| --- | --- |
| Body | Original segmented robot |
| Height | 1.2–1.6 m parameter; world clearance may reject larger variants |
| Head scale | 0.85–1.1 relative to the fixed rig |
| Colors | Primary, secondary, accent, visor |
| Clothing | None or a geometric vest |
| Accessories | Chest badge, antenna, backpack |
| Human controls | Explicit accessory vetoes and color overrides |

Other personality cues and identifying features remain recorded creative intent;
the specification explicitly records them under `unimplemented_intent`. Freeform
human notes are informational and do not silently change the geometry. The
integrating assistant must convert enforceable preferences into supported fields
and resolve unsupported hard constraints before obtaining approval.

The supplied Aster example is a **synthetic fixture** with an original small PNG
and authored answers. It is not evidence of a conversation with a real Dot or
human. It does not reproduce Rocky. The [Rocky reference audit](ROCKY_REFERENCE_PIPELINE.md)
documents his separate working Blender/Godot pipeline.

## Interview, specification and package

Use the reusable [character interview prompt](../prompts/character-interview.md)
with the [Aster interview template](../examples/character_factory/aster.interview.json).
The Dot describes its self-image, colors, proportions, clothing, accessories,
personality, identifying features and expected activities. The human supplies
preferences/vetoes and approves the exact submitted choices and reference use.
The factory rejects missing approval; an integration must never invent consent.

The data boundaries are explicit:

| Contract | Purpose |
| --- | --- |
| [`character-interview.schema.json`](../schemas/character-interview.schema.json) | Approved reference declarations and Dot/human choices |
| [`character-spec.schema.json`](../schemas/character-spec.schema.json) | Normalized choices, image digests, creative intent and implementation limits |
| [`character-package.schema.json`](../schemas/character-package.schema.json) | Data-only backend package, provenance, capabilities and file hashes |
| [`character.schema.json`](../schemas/character.schema.json) | Existing producer-independent runtime character contract |
| [`character-job.schema.json`](../schemas/character-job.schema.json) | Cloud worker progress, validation and build receipt |

Each generated package contains:

```text
character.glb   # self-contained geometry, materials, skin and clips
character.json # ordinary Domes runtime manifest, schema_version 1
spec.json      # approved structured specification and reference evidence
package.json   # identity, provenance, capability list and immutable file hashes
validation.json
```

Raw uploaded image pixels are not copied into the package or world. Reference
descriptions, source/license declarations, creative intent and human notes are
included, so keep private information out of a package intended for public hosting.
The generator refuses to overwrite an existing output directory. Its files are
deterministic for equal inputs. Hashes detect unexpected changes; they are not a
publisher signature or an authorization system.

The standard runtime manifest does not depend on this generation backend. A future
Blender worker or other generator can deliver the same runtime contract. The
current procedural package validator deliberately accepts only this backend's
bounded, data-only package format; additional generators need their own verified
adapters before installation.

## Rig, clips and world installation

The GLB is in meters with +Y up, -Z forward and a ground-level visual origin.
The motor owns horizontal movement. Skin joints are `Root`, `Hips`, `Spine`,
`Chest`, `Neck`, `Head`, and left/right upper arm, forearm, hand, thigh, shin and
foot. Each geometric segment is rigidly weighted to its joint; this is real skinning
for a segmented body, not smooth organic deformation or arbitrary-rig retargeting.

Godot 4.5.1 imports the generated skeleton at `Character/Skeleton3D` and the
animation player at `AnimationPlayer`. GLB clip names use `<semantic>_loop`;
the importer strips that suffix and sets linear looping. The runtime manifest maps
semantic names to the resulting names:

| Semantic | Implemented gesture |
| --- | --- |
| `idle` | Small chest/head movement |
| `walk` | Opposing limbs and knee motion; in-place |
| `interact` | Reaching arm |
| `sit` | Lowered hips, bent thighs/knees; no seat alignment |
| `work` | Alternating hands in front of the body |
| `read` | Raised hands and lowered head; no book grip |
| `build` | Alternating forearm gestures |
| `inspect` | Looking around with a raised arm |
| `garden` | Forward lean and reaching gesture |
| `sleep` | Seated doze; no bed placement |
| `talk` | Head and conversational hand movement |
| `phone` | Empty hand raised; no handset or real call |

Fallbacks map `rest` to `sleep`, `observe` to `inspect`, and `music` to `talk`.
All clips author every joint rotation and hip height so action changes can reset
the previous pose. None establishes prop contact, physical task completion, live
Dot activity, seat compatibility or inverse kinematics.

`install_package` validates the source and candidate content, copies the project
to a fresh stage, adds the generated character and changes the selected copied
world's character reference. It updates the copied display name and catalog order
so the preview opens first. Owner-locked brief content remains intact. Existing
source worlds and character files are not modified. A colliding character ID,
existing stage or incompatible navigation clearance fails installation.

## Backend API and operator examples

[`character_factory.py`](../tools/character_factory.py) exposes:

```python
derive_spec(interview: dict, reference_root: Path) -> dict
generate_package(spec: dict, output_dir: Path) -> dict
validate_package(package_dir: Path) -> dict
install_package(package_dir: Path, source_repository: Path,
                stage_dir: Path, world_id: str) -> dict
```

`validate_package` returns `ok`, `errors`, checked boundaries and measured counts;
callers must check `ok`. Installation returns its stage path, character path and
content-validation result while marking Godot import/browser acceptance pending.

In a configured contributor checkout or cloud worker, one command produces a
package and an isolated preview project:

```powershell
python tools/character_factory.py run --interview examples/character_factory/aster.interview.json --reference-root examples/character_factory --output artifacts/aster-package --stage artifacts/aster-world --world tidal_observatory
```

The separate `spec`, `generate`, `validate` and `install` subcommands expose each
boundary. Use fresh output paths for subsequent jobs. Generation and installation
do not imply that the world has been imported, exported or deployed.

[`cloud_worker.py`](../tools/cloud_worker.py) runs generation through Web export:

```powershell
python tools/cloud_worker.py --interview examples/character_factory/aster.interview.json --reference-root examples/character_factory --job-dir artifacts/aster-cloud-job --world-id cedar_atelier --godot .tools/godot/Godot_v4.5.1-stable_win64_console.exe
```

The [cloud workflow](../.github/workflows/character-factory.yml) runs the same
pipeline on an ephemeral Linux worker and preserves job evidence and browser
artifacts. [`character_request.py`](../tools/character_request.py) packs approved
interviews and their declared image bytes into a bounded 48 KiB transport envelope,
unpacks it into a fresh upload directory, and supports authenticated operator
dispatch. Workflow input is data, never interpolated shell code. This small-input
prototype still needs private object storage for typical larger references.

The worker receipt separates build success from deployment: it retains
`deployment.status = not_deployed` until an external publisher establishes a URL.
See [cloud architecture](CLOUD_ARCHITECTURE.md) for orchestration, hosting and
persistence boundaries. A public multi-user request UI, production authentication,
private upload storage, per-owner hosting and cross-device world persistence are
separate work; this factory does not claim they already exist.

## Verification and limits

On 2026-10-02 the factory-specific Python suite passed **19 tests** and the imported
generated-character Godot suite passed **59 checks** locally.

```powershell
python -m unittest discover -s tests -p test_character_factory.py -v
& '.tools/godot/Godot_v4.5.1-stable_win64_console.exe' --headless --path artifacts/aster-world/godot --editor --import
& '.tools/godot/Godot_v4.5.1-stable_win64_console.exe' --headless --path artifacts/aster-world/godot --script res://tests/test_factory_character.gd -- --character res://content/characters/aster.json
```

The Python tests inspect real generated files: schemas/digests, reference approval
and traversal rejection, deterministic output, changed geometry/materials,
corrupted skins/accessors/clips, unsafe manifest redirection, human veto precedence,
source preservation, identity collisions and failed-stage cleanup.

The Godot suite loads the actual GLB, runs the runtime audit, confirms 18 imported
bones, tests all twelve clips for looping and changing joint transforms, checks
horizontal motion ownership, and verifies arm/hip reset after phone, sit, sleep and
garden. The default Aster GLB has 480 vertices across 20 mesh primitives.

These results do not prove visual likeness, organic deformation, arbitrary-rig
retargeting, foot contact over every interpolated frame, station fitting, phone
grip or browser/device acceptance. Hosted/browser proof and its exact deployed
revision belong in the final validation report, independently of these local
package and engine tests.
