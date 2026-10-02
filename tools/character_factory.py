#!/usr/bin/env python3
"""Server/CI character factory. These commands are contributor tools, not user setup.

Approved image evidence + Dot interview -> strict spec -> original skinned GLB
-> existing Domes character contract -> validation -> isolated world stage.
The deterministic backend interprets structured choices, not image pixels.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import sys
import uuid

from jsonschema import Draft202012Validator
from factory_glb import SEMANTICS, accessor_values, create_character, read_glb
from validate_content import ContentValidator, read_json

ROOT = Path(__file__).resolve().parents[1]
MAX_REFERENCE_BYTES = 10 * 1024 * 1024


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def validate_schema(kind, data):
    schema = read_json(ROOT / "schemas" / (kind+".schema.json"))
    issues = list(Draft202012Validator(schema).iter_errors(data))
    # jsonschema's numeric checks alone are not a NaN guard.
    canonical(data)
    if issues:
        raise ValueError("; ".join(f"{'.'.join(map(str, item.path))}: {item.message}" for item in issues))


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
    validate_schema("character-spec", spec)
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


def generate_package(spec: dict, output_dir: Path) -> dict:
    validate_schema("character-spec", spec)
    destination = Path(output_dir).resolve()
    if destination.exists():
        raise ValueError("package output already exists; use a new immutable output directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / (".factory-"+uuid.uuid4().hex)
    temporary.mkdir()
    try:
        geometry = create_character(spec, temporary / "character.glb")
        manifest = manifest_for(spec)
        errors = ContentValidator(ROOT).validate_document("character", manifest)
        if errors:
            raise ValueError("; ".join(errors))
        write_json(temporary / "character.json", manifest)
        write_json(temporary / "spec.json", spec)
        package = {"schema_version": 1, "package_kind": "domes_character", "character_id": spec["character_id"],
                   "backend": spec["backend"], "files": {name: digest(temporary/name) for name in ("character.glb", "character.json", "spec.json")},
                   "provenance": {"geometry": "Original procedural segmented robot generated from approved structured choices",
                                  "animation": "Original fixed-rig skeletal clips authored in factory_glb.py; no third-party animation or retargeting",
                                  "reference_handling": "Only upload digests, approved descriptions and source/license declarations; no uploaded image pixels are copied into the package",
                                  "license": "MIT for generated geometry and clips; input reference rights remain with their owners"},
                   "capabilities": list(SEMANTICS),
                   "limitations": ["Procedural stylized prototype, not image-to-3D reconstruction", "Rigid skin weights; not organic deformation",
                                   "Sleep is a seated doze, not bed placement", "Phone uses an empty hand; no handset or live call", "No prop grip, seat alignment, inverse kinematics, arbitrary-rig retargeting or visual likeness guarantee"]}
        write_json(temporary / "package.json", package)
        report = validate_package(temporary)
        if not report["ok"]:
            raise ValueError("; ".join(report["errors"]))
        write_json(temporary / "validation.json", report)
        temporary.rename(destination)
        return {"package_dir": str(destination), "character_id": spec["character_id"], "geometry": geometry, "validation": report}
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def validate_package(package_dir: Path) -> dict:
    folder = Path(package_dir).resolve()
    report = {"schema_version": 1, "ok": False, "errors": [], "checks": [],
              "scope": "Package schemas, immutable file digests, bounded self-contained GLB, real skin and animated joints. Godot import, appearance, motion quality, station fit and browser playback require separate acceptance."}
    try:
        for name in ("character.glb", "character.json", "spec.json", "package.json"):
            path = folder/name
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(folder):
                raise ValueError("package must contain regular local files: "+name)
            if path.stat().st_size > 20*1024*1024:
                raise ValueError("package file exceeds 20 MiB")
        package, manifest, spec = [read_json(folder/name) for name in ("package.json", "character.json", "spec.json")]
        validate_schema("character-package", package)
        validate_schema("character-spec", spec)
        errors = ContentValidator(ROOT).validate_document("character", manifest)
        if errors:
            raise ValueError("; ".join(errors))
        if not package["character_id"] == manifest["id"] == spec["character_id"]:
            raise ValueError("package/spec/character identities disagree")
        # This backend's package is a narrow data-only format, not permission to
        # install arbitrary res:// scenes or scripts supplied by an upload.
        if manifest != manifest_for(spec):
            raise ValueError("manifest does not match the approved specification and backend contract")
        if package["capabilities"] != list(SEMANTICS):
            raise ValueError("package capabilities disagree with backend contract")
        for name, expected in package["files"].items():
            if digest(folder/name) != expected:
                raise ValueError("file digest mismatch: "+name)
        report["checks"].append("schemas_and_digests")
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
        report["ok"] = True
    except (ValueError, OSError, KeyError, IndexError, TypeError, struct.error, OverflowError) as error:
        report["errors"].append(str(error))
    return report


def install_package(package_dir: Path, source_repository: Path, stage_dir: Path, world_id: str) -> dict:
    report = validate_package(package_dir)
    if not report["ok"]:
        raise ValueError("; ".join(report["errors"]))
    source, destination = Path(source_repository).resolve(), Path(stage_dir).resolve()
    if destination.exists() or destination == source or source.is_relative_to(destination):
        raise ValueError("world stage must be a new isolated directory")
    if destination.is_relative_to(source / "godot"):
        raise ValueError("world stage cannot be nested inside the live Godot project")
    source_errors = ContentValidator(source).validate()
    if source_errors:
        raise ValueError("source world content invalid: "+"; ".join(source_errors))
    catalog = read_json(source / "godot/content/catalog.json")
    chosen = next((entry for entry in catalog["worlds"] if entry["id"] == world_id), None)
    if chosen is None:
        raise ValueError("unknown template world: "+world_id)
    manifest = read_json(Path(package_dir) / "character.json")
    # Never overwrite a pre-existing character with a coincidentally equal ID.
    if (source / "godot/content/characters" / (manifest["id"]+".json")).exists() or (source / "godot/assets/generated" / manifest["id"]).exists():
        raise ValueError("generated character id collides with existing source content")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / (".world-stage-"+uuid.uuid4().hex)
    temporary.mkdir()
    try:
        for folder in ("godot", "schemas", "tools", "tests", "docs"):
            if (source/folder).exists():
                shutil.copytree(source/folder, temporary/folder, ignore=shutil.ignore_patterns(".godot", "__pycache__"))
        for name in ("LICENSE", "requirements-dev.txt"):
            shutil.copy2(source/name, temporary/name)
        assets = temporary / "godot/assets/generated" / manifest["id"]
        assets.mkdir(parents=True)
        shutil.copy2(Path(package_dir)/"character.glb", assets/"character.glb")
        character_path = f"res://content/characters/{manifest['id']}.json"
        write_json(temporary / "godot/content/characters" / (manifest["id"]+".json"), manifest)
        world_path = temporary / "godot" / chosen["path"][6:]
        world = read_json(world_path)
        world["character_path"] = character_path
        world["title"] = manifest["display_name"]+"'s Character Factory Preview"
        write_json(world_path, world)
        brief_path = temporary / "godot" / world["brief_path"][6:]
        brief = read_json(brief_path)
        brief["dot_name"] = manifest["display_name"]
        write_json(brief_path, brief)
        chosen["title"] = world["title"]
        catalog["worlds"] = [chosen] + [item for item in catalog["worlds"] if item["id"] != world_id]
        write_json(temporary / "godot/content/catalog.json", catalog)
        errors = ContentValidator(temporary).validate()
        if errors:
            raise ValueError("staged world content invalid: "+"; ".join(errors))
        receipt = {"schema_version": 1, "stage_root": str(destination), "world_id": world_id,
                   "character_id": manifest["id"], "character_path": character_path,
                   "source_unchanged": True, "content_validation": "passed", "godot_import": "pending", "browser_acceptance": "pending",
                   "package_manifest_sha256": digest(Path(package_dir)/"package.json")}
        write_json(temporary/"factory-install.json", receipt)
        temporary.rename(destination)
        return receipt
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("spec", "run"):
        part = sub.add_parser(command)
        part.add_argument("--interview", type=Path, required=True)
        part.add_argument("--reference-root", type=Path)
        part.add_argument("--output", type=Path, required=True)
        if command == "run":
            part.add_argument("--stage", type=Path)
            part.add_argument("--world", default="tidal_observatory")
            part.add_argument("--root", type=Path, default=ROOT)
    part = sub.add_parser("generate")
    part.add_argument("--spec", type=Path, required=True)
    part.add_argument("--output", type=Path, required=True)
    part = sub.add_parser("validate")
    part.add_argument("package", type=Path)
    part = sub.add_parser("install")
    part.add_argument("package", type=Path)
    part.add_argument("--root", type=Path, default=ROOT)
    part.add_argument("--stage", type=Path, required=True)
    part.add_argument("--world", required=True)
    args = parser.parse_args()
    try:
        if args.command in ("spec", "run"):
            spec = derive_spec(read_json(args.interview), args.reference_root or args.interview.parent)
            if args.command == "spec":
                if args.output.exists():
                    raise ValueError("spec output already exists")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                write_json(args.output, spec)
                result = {"spec": str(args.output)}
            else:
                result = generate_package(spec, args.output)
                if args.stage:
                    result["installation"] = install_package(args.output, args.root, args.stage, args.world)
        elif args.command == "generate":
            result = generate_package(read_json(args.spec), args.output)
        elif args.command == "validate":
            result = validate_package(args.package)
        else:
            result = install_package(args.package, args.root, args.stage, args.world)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok", True) else 1
    except (ValueError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
