"""Compose independently validated world/character packages into an isolated runtime."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import uuid
from character_contract import ROOT, digest, write_json
from character_package import validate_package as validate_character
from world_package import validate_package as validate_world
from validate_content import ContentValidator, read_json


def compose_many(pairs, output_repo, source_repository=ROOT):
    """pairs is [(world_package_dir, character_package_dir), ...]. No template mutation."""
    source, destination = Path(source_repository).resolve(), Path(output_repo).resolve()
    if destination.exists() or destination == source or source.is_relative_to(destination):
        raise ValueError("composition destination must be a new isolated directory")
    if destination.is_relative_to(source) and not any(destination.is_relative_to(source/d) and destination != source/d for d in ["artifacts", "dist"]):
        raise ValueError("in-repository composition must be under artifacts/ or dist/")
    loaded, world_ids, character_ids = [], set(), set()
    for world_dir, character_dir in pairs:
        world_dir, character_dir = Path(world_dir), Path(character_dir)
        for validator, directory in [(validate_world, world_dir), (validate_character, character_dir)]:
            report = validator(directory)
            if not report["ok"]:
                raise ValueError("composition package rejected: "+"; ".join(report["errors"]))
        wp, cp = read_json(world_dir/"package.json"), read_json(character_dir/"package.json")
        world, character = read_json(world_dir/wp["runtime_manifest"]), read_json(character_dir/cp.get("runtime_manifest", "character.json"))
        if character != read_json(world_dir/wp["character_manifest"]):
            raise ValueError("world was compiled for a different character manifest; recompile for selected character")
        if wp["provenance"].get("character_package_sha256") != digest(character_dir/"package.json"):
            raise ValueError("character package identity/hash differs from composed world requirements")
        if world["id"] in world_ids or character["id"] in character_ids:
            raise ValueError("composition world/character IDs collide")
        world_ids.add(world["id"])
        character_ids.add(character["id"])
        loaded.append((world_dir, character_dir, wp, cp, world, character))
    if not loaded:
        raise ValueError("composition needs at least one world")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent/(".world-compose-"+uuid.uuid4().hex)
    temporary.mkdir()
    try:
        for folder in ("godot", "schemas", "tools", "tests", "docs", "examples", "cloud"):
            if (source/folder).exists():
                shutil.copytree(source/folder, temporary/folder, ignore=shutil.ignore_patterns(".godot", "__pycache__"))
        for filename in ("LICENSE", "requirements-dev.txt"):
            shutil.copy2(source/filename, temporary/filename)
        catalog = read_json(temporary/"godot/content/catalog.json")
        entries = []
        for world_dir, character_dir, wp, cp, world, character in loaded:
            for kind, data in [("worlds", world), ("characters", character), ("assets", read_json(world_dir/wp["documents"]["assets"])),
                               ("routines", read_json(world_dir/wp["documents"]["routine"])), ("briefs", read_json(world_dir/wp["documents"]["brief"]))]:
                name = character["id"] if kind == "characters" else world["id"]
                target = temporary/"godot/content"/kind/(name+".json")
                if target.exists():
                    raise ValueError("composition collides with existing content: "+target.name)
                write_json(target, data)
            for name, target in cp.get("assets", {"character.glb": character["scene_path"]}).items():
                path = temporary/"godot"/target[6:]
                if path.exists():
                    raise ValueError("character asset installation collision")
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(character_dir/name, path)
            entries.append({"id": world["id"], "title": world["title"], "path": f"res://content/worlds/{world['id']}.json"})
        catalog["worlds"] = entries
        write_json(temporary/"godot/content/catalog.json", catalog)
        errors = ContentValidator(temporary).validate()
        if errors:
            raise ValueError("composed content validation failed: "+"; ".join(errors))
        receipt = {"schema_version": 1, "ok": True, "world_ids": sorted(world_ids), "character_ids": sorted(character_ids),
                   "packages": [{"world_sha256": digest(w/"package.json"), "character_sha256": digest(c/"package.json")} for w,c,*_ in loaded],
                   "validation": "schemas, references, actions, body envelope and navigation passed", "engine_acceptance": "pending", "browser_acceptance": "pending"}
        write_json(temporary/"world-composition.json", receipt)
        temporary.rename(destination)
        return receipt
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def compose(world_package_dir, character_package_dir, output_repo, source_repository=ROOT):
    return compose_many([(world_package_dir, character_package_dir)], output_repo, source_repository)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-package", required=True, type=Path)
    parser.add_argument("--character-package", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(compose(args.world_package, args.character_package, args.output), indent=2))
