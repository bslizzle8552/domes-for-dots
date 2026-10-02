"""Strict procedural_rigid_skin_v1 producer and acceptance contract.

All segmented-body, skeleton, rigid-weight and fixed-clip assumptions live here.
This is trusted source selected from a registry, never uploaded executable code.
"""
import copy
import hashlib
import math
from pathlib import Path
from character_contract import ROOT, canonical, digest, validate_schema, write_json
from factory_glb import SEMANTICS, accessor_values, create_character, read_glb
from validate_content import ContentValidator
ID = "procedural_rigid_skin_v1"
MAX_REFERENCE_BYTES = 10 * 1024 * 1024
VALIDATOR = ID
ENGINE_ACCEPTANCE = {"script": "res://tests/test_factory_character.gd",
                    "success_pattern": r"FACTORY CHARACTER TESTS:\s*\d+ passed,\s*0 failed"}


def derive_spec(interview: dict, reference_root: Path) -> dict:
    validate_schema("character-interview", interview)
    reference_root = Path(reference_root).resolve()
    evidence = []
    ids = set()
    for item in interview["references"]:
        if item["id"] in ids:
            raise ValueError("duplicate reference id")
        ids.add(item["id"])
        relative = Path(item["path"])
        path = reference_root / relative
        if relative.is_absolute() or ".." in relative.parts or path.is_symlink() or not path.resolve().is_relative_to(reference_root):
            raise ValueError("reference path must stay inside its upload directory")
        if not path.is_file() or not 0 < path.stat().st_size <= MAX_REFERENCE_BYTES:
            raise ValueError("reference must be a nonempty local upload no larger than 10 MiB")
        raw = path.read_bytes()
        if raw.startswith(b"\x89PNG\r\n\x1a\n") and len(raw) >= 33 and raw[12:16] == b"IHDR":
            media = "image/png"
        elif raw.startswith(b"\xff\xd8\xff") and raw.endswith(b"\xff\xd9"):
            media = "image/jpeg"
        else:
            raise ValueError("reference must have a PNG or JPEG signature")
        evidence.append({key: item[key] for key in ("id", "description", "source", "license")}
                        | {"sha256": hashlib.sha256(raw).hexdigest(), "media_type": media, "bytes": len(raw)})
    appearance = copy.deepcopy(interview["dot"]["appearance"])
    appearance["colors"].update(interview["human"]["color_overrides"])
    appearance["accessories"] = [value for value in appearance["accessories"] if value not in interview["human"]["veto_accessories"]]
    spec = {"schema_version": 1, "character_id": interview["character_id"], "display_name": interview["display_name"],
            "backend": "procedural_rigid_skin_v1", "appearance": appearance, "references": evidence,
            "creative_intent": {key: interview["dot"][key] for key in ("self_image", "personality_cues", "identifying_features", "activities")},
            "decisions": {"human_approved": True, "veto_accessories": interview["human"]["veto_accessories"],
                          "human_notes": interview["human"]["notes"],
                          "implementation_scope": "Original segmented robot from explicit palette, proportions, clothing and accessory choices. Images are approved reference evidence; this backend does not infer geometry from pixels. Gestures have no automatic prop contact or arbitrary-rig retargeting.",
                          "unimplemented_intent": interview["dot"]["identifying_features"] + interview["dot"]["personality_cues"]},
            "input_sha256": hashlib.sha256(canonical(interview)).hexdigest()}
    validate_spec(spec)
    return spec

def manifest_for(spec):
    factor = spec["appearance"]["height_m"] / 1.6
    colors = spec["appearance"]["colors"]
    height = (1.39 + .045 + .155*spec["appearance"]["head_scale"])*factor
    if "antenna" in spec["appearance"]["accessories"]:
        height = max(height, 1.7275*factor)
    return {"schema_version": 1, "id": spec["character_id"], "display_name": spec["display_name"],
            "scene_path": f"res://assets/generated/{spec['character_id']}/character.glb",
            "scale": [1, 1, 1], "forward_axis": "-Z", "collision": {"radius": round(.31*factor, 5), "height": round(height, 5)},
            "navigation": {"radius": round(.315*factor, 5), "speed": 2.4},
            "rig": {"skeleton_path": "Character/Skeleton3D", "animation_player_path": "AnimationPlayer",
                    "notes": "18-joint glTF skin, rigid weights for segmented geometry. Twelve original in-place skeletal clips. No arbitrary retargeting or station IK; sit and sleep use a seated pose, phone an empty-hand gesture."},
            "animations": {name: name for name in SEMANTICS},
            "fallbacks": {"rest": "sleep", "observe": "inspect", "music": "talk"},
            "appearance": {"color": colors["primary"], "accent": colors["accent"]},
            "metadata": {"creator": "Domes character factory", "license": "MIT", "backend": spec["backend"],
                         "spec_sha256": hashlib.sha256(canonical(spec)).hexdigest(),
                         "source": "Original procedural geometry and authored skeletal clips; not image reconstruction"}}

def validate_spec(spec):
    validate_schema("procedural-rigid-skin-spec", spec)


def produce(spec, folder):
    validate_spec(spec)
    geometry = create_character(spec, folder / "character.glb")
    manifest = manifest_for(spec)
    errors = ContentValidator(ROOT).validate_document("character", manifest)
    if errors:
        raise ValueError("; ".join(errors))
    write_json(folder / "character.json", manifest)
    write_json(folder / "spec.json", spec)
    return {"runtime_manifest": "character.json", "spec_path": "spec.json",
            "assets": {"character.glb": manifest["scene_path"]},
            "geometry": geometry,
            "provenance": {"geometry": "Original procedural segmented robot generated from approved structured choices",
                           "animation": "Original fixed-rig skeletal clips authored in factory_glb.py; no third-party animation or retargeting",
                           "reference_handling": "Only upload digests, approved descriptions and source/license declarations; no uploaded image pixels are copied into the package",
                           "license": "MIT for generated geometry and clips; input reference rights remain with their owners"},
            "capabilities": list(SEMANTICS),
            "limitations": ["Procedural stylized prototype, not image-to-3D reconstruction", "Rigid skin weights; not organic deformation",
                            "Sleep is a seated doze, not bed placement", "Phone uses an empty hand; no handset or live call", "No prop grip, seat alignment, inverse kinematics, arbitrary-rig retargeting or visual likeness guarantee"]}


def validate_assets(folder, package, manifest, spec, report):
    validate_spec(spec)
    if manifest != manifest_for(spec):
        raise ValueError("manifest does not match the approved specification and backend contract")
    if package["capabilities"] != list(SEMANTICS):
        raise ValueError("package capabilities disagree with backend contract")
    if set(package["files"]) != {"character.glb", "character.json", "spec.json"}:
        raise ValueError("procedural backend contract requires exactly its three data files")
    if package.get("runtime_manifest", "character.json") != "character.json" or package.get("spec_path", "spec.json") != "spec.json":
        raise ValueError("procedural backend contract requires its declared manifest/spec paths")
    if package.get("assets", {"character.glb": manifest["scene_path"]}) != {"character.glb": manifest["scene_path"]}:
        raise ValueError("procedural backend contract requires its generated GLB mapping")
    doc, binary = read_glb(folder / "character.glb")
    if doc.get("asset", {}).get("version") != "2.0" or len(doc.get("buffers", [])) != 1 or "uri" in doc["buffers"][0] or doc.get("images") or doc.get("extensionsUsed"):
        raise ValueError("GLB must use a self-contained supported glTF 2.0 buffer with no external images/extensions")
    if doc["buffers"][0]["byteLength"] > len(binary):
        raise ValueError("GLB buffer exceeds binary chunk")
    if len(doc.get("nodes", [])) > 256 or len(doc.get("accessors", [])) > 2048:
        raise ValueError("GLB complexity limit exceeded")
    decoded = []
    for index in range(len(doc["accessors"])):
        values = accessor_values(doc, binary, index)
        if any(not math.isfinite(v) for row in values for v in row):
            raise ValueError("non-finite GLB accessor")
        decoded.append(values)
    skins = doc.get("skins", [])
    if len(skins) != 1 or len(skins[0].get("joints", [])) != 18:
        raise ValueError("expected one real 18-joint skin")
    joints = skins[0]["joints"]
    if len(set(joints)) != len(joints) or any(not 0 <= n < len(doc["nodes"]) for n in joints):
        raise ValueError("invalid skin joint indices")
    if len(decoded[skins[0]["inverseBindMatrices"]]) != len(joints):
        raise ValueError("inverse bind matrix count does not match skin")
    if not any(node.get("skin") == 0 and "mesh" in node for node in doc["nodes"]):
        raise ValueError("skin has no mesh instance")
    vertex_count = 0
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            attrs = primitive["attributes"]
            positions, weights, indices = (decoded[attrs[name]] for name in ("POSITION", "WEIGHTS_0", "JOINTS_0"))
            if not positions or len(positions) != len(weights) or len(weights) != len(indices):
                raise ValueError("skin attribute counts disagree")
            vertex_count += len(positions)
            if vertex_count > 100000:
                raise ValueError("GLB vertex limit exceeded")
            if any(abs(sum(row)-1) > 1e-5 or any(v < 0 or v > 1 for v in row) for row in weights):
                raise ValueError("skin weights must be normalized")
            if any(v >= len(joints) for row in indices for v in row):
                raise ValueError("vertex references absent skin joint")
            if any(row[0] >= len(positions) for row in decoded[primitive["indices"]]):
                raise ValueError("mesh index out of bounds")
            if any(list(row) != [1.0, 0.0, 0.0, 0.0] for row in weights):
                raise ValueError("procedural rigid weights must assign each vertex to exactly one joint")
    report["checks"].append("real_skin_and_weighted_geometry")
    animations = doc.get("animations", [])
    if {a["name"] for a in animations} != {name+"_loop" for name in SEMANTICS} or len(animations) != len(SEMANTICS):
        raise ValueError("required semantic clips are absent or duplicated")
    for animation in animations:
        changed = False
        covered = set()
        for channel in animation["channels"]:
            target = channel["target"]
            if target["node"] not in joints or target["path"] not in ("rotation", "translation"):
                raise ValueError("animation does not target a supported skeleton transform")
            sampler = animation["samplers"][channel["sampler"]]
            time_rows, output = decoded[sampler["input"]], decoded[sampler["output"]]
            times = [row[0] for row in time_rows]
            if len(times) < 2 or len(times) != len(output) or any(b <= a for a, b in zip(times, times[1:])):
                raise ValueError("animation sample counts or times invalid")
            if target["path"] == "rotation":
                if any(abs(sum(v*v for v in row)-1) > 1e-4 for row in output):
                    raise ValueError("animation quaternion is not normalized")
                covered.add(target["node"])
            elif any(abs(row[0]) > 1e-6 or abs(row[2]) > 1e-6 for row in output):
                raise ValueError("locomotion must remain in place; motor owns horizontal translation")
            changed |= any(row != output[0] for row in output[1:])
        if covered != set(joints) or not changed:
            raise ValueError("clip must reset every joint and have actual animated motion")
    report.update(joint_count=len(joints), vertex_count=vertex_count, clip_count=len(animations))
    report["checks"].append("semantic_clips_and_in_place_motion")
