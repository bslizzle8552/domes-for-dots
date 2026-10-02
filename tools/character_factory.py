#!/usr/bin/env python3
"""Operator Character Factory: generic package orchestration and isolated staging.

Producer implementations are trusted registered source. Backend-specific schema,
geometry, rig and motion checks are mandatory, not inferred from an upload label.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys
import uuid
import json
from character_contract import ROOT, canonical, digest, validate_schema, write_json
from character_package import validate_package
from character_backends import get_backend
from validate_content import ContentValidator, read_json


def derive_spec(interview: dict, reference_root: Path, backend: str = "procedural_rigid_skin_v1") -> dict:
    producer = get_backend(backend)
    spec = producer.derive_spec(interview, reference_root)
    validate_schema("character-spec", spec)
    producer.validate_spec(spec)
    if spec["backend"] != backend:
        raise ValueError("derived specification backend disagrees with selected producer")
    return spec


def engine_acceptance(package_dir: Path) -> dict:
    package = read_json(Path(package_dir) / "package.json")
    return dict(get_backend(package["backend"]).ENGINE_ACCEPTANCE)


def generate_package(spec: dict, output_dir: Path) -> dict:
    validate_schema("character-spec", spec)
    producer = get_backend(spec["backend"])
    producer.validate_spec(spec)
    destination = Path(output_dir).resolve()
    if destination.exists():
        raise ValueError("package output already exists; use a new immutable output directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / (".factory-"+uuid.uuid4().hex)
    temporary.mkdir()
    try:
        produced = producer.produce(spec, temporary)
        files = {path.relative_to(temporary).as_posix(): digest(path)
                 for path in sorted(temporary.rglob("*")) if path.is_file()}
        package = {"schema_version": 2, "package_kind": "domes_character", "character_id": spec["character_id"],
                   "backend": spec["backend"], "runtime_manifest": produced["runtime_manifest"],
                   "spec_path": produced["spec_path"], "assets": produced["assets"], "files": files,
                   "validation": {"validator": producer.VALIDATOR, "report": "validation.json"},
                   "provenance": produced["provenance"], "capabilities": produced["capabilities"],
                   "limitations": produced["limitations"]}
        write_json(temporary / "package.json", package)
        report = validate_package(temporary)
        if not report["ok"]:
            raise ValueError("; ".join(report["errors"]))
        write_json(temporary / "validation.json", report)
        temporary.rename(destination)
        return {"package_dir": str(destination), "character_id": spec["character_id"],
                "geometry": produced.get("geometry"), "validation": report}
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def install_package(package_dir: Path, source_repository: Path, stage_dir: Path, world_id: str) -> dict:
    report = validate_package(package_dir)
    if not report["ok"]:
        raise ValueError("; ".join(report["errors"]))
    source, destination = Path(source_repository).resolve(), Path(stage_dir).resolve()
    if destination.exists() or destination == source or source.is_relative_to(destination):
        raise ValueError("world stage must be a new isolated directory")
    if destination.is_relative_to(source) and not any(destination != source/folder and destination.is_relative_to(source/folder) for folder in ("artifacts", "dist")):
        raise ValueError("a stage inside the source repository must be a child of artifacts/ or dist/; source folders cannot contain stages")
    source_errors = ContentValidator(source).validate()
    if source_errors:
        raise ValueError("source world content invalid: "+"; ".join(source_errors))
    catalog = read_json(source / "godot/content/catalog.json")
    chosen = next((entry for entry in catalog["worlds"] if entry["id"] == world_id), None)
    if chosen is None:
        raise ValueError("unknown template world: "+world_id)
    package = read_json(Path(package_dir) / "package.json")
    manifest = read_json(Path(package_dir) / package.get("runtime_manifest", "character.json"))
    # Never overwrite a pre-existing character with a coincidentally equal ID.
    if (source / "godot/content/characters" / (manifest["id"]+".json")).exists() or (source / "godot/assets/generated" / manifest["id"]).exists():
        raise ValueError("generated character id collides with existing source content")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / (".world-stage-"+uuid.uuid4().hex)
    temporary.mkdir()
    try:
        for folder in ("godot", "schemas", "tools", "tests", "docs", "examples", "prompts", "cloud"):
            if (source/folder).exists():
                shutil.copytree(source/folder, temporary/folder, ignore=shutil.ignore_patterns(".godot", "__pycache__"))
        for name in ("LICENSE", "requirements-dev.txt"):
            shutil.copy2(source/name, temporary/name)
        assets = temporary / "godot/assets/generated" / manifest["id"]
        assets.mkdir(parents=True)
        for name, target in package.get("assets", {"character.glb": manifest["scene_path"]}).items():
            asset_path = temporary / "godot" / target[6:]
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(package_dir)/name, asset_path)
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
