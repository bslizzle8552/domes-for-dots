"""Generic World Package envelope plus mandatory trusted compiler revalidation.

Receipts never authorize data: exact registered compilation is recomputed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import uuid
from character_contract import canonical, digest, validate_schema, write_json
from character_package import local_file, validate_package as validate_character_package
from validate_content import read_json
from world_intent import intent_to_spec

MAX_PACKAGE_BYTES = 4*1024*1024


def get_compiler(name):
    # Never load a module or Python path named by generated data.
    if name == "semantic_grid_v1":
        import world_compiler
        return world_compiler
    raise ValueError("unregistered world compiler: "+name)


def validate_package(package_dir):
    report = {"schema_version": 1, "ok": False, "errors": [], "checks": [],
              "scope": "Static package/registered compiler acceptance only; browser and host evidence are separate."}
    try:
        folder = Path(package_dir).absolute()
        package = read_json(local_file(folder, "package.json"))
        validate_schema("world-package", package)
        compiler = get_compiler(package["compiler"])
        names = list(package["files"])
        if len({n.casefold() for n in names}) != len(names) or any(n.casefold() in {"package.json", "validation.json"} for n in names):
            raise ValueError("duplicate/aliased/reserved world package file names")
        if package["validation"] != {"validator": compiler.VALIDATOR, "report": "validation.json"}:
            raise ValueError("validator metadata differs from trusted compiler registration")
        total = 0
        for name, expected in package["files"].items():
            path = local_file(folder, name)
            total += path.stat().st_size
            if total > MAX_PACKAGE_BYTES:
                raise ValueError("world package exceeds 4 MiB data budget")
            if digest(path) != expected:
                raise ValueError("world package digest mismatch: "+name)
        permitted = set(names) | {"package.json", "validation.json"}
        for path in folder.rglob("*"):
            if path.is_symlink():
                raise ValueError("world package links are forbidden")
            if path.is_file():
                name = path.relative_to(folder).as_posix()
                local_file(folder, name)
                if name not in permitted:
                    raise ValueError("undeclared world package file: "+name)
        required = [package[k] for k in ["runtime_manifest", "spec_path", "intent_path", "character_manifest"]]
        required += list(package["documents"].values())
        if len(required) != len(set(required)) or set(required) != set(names):
            raise ValueError("every file must have exactly one declared document role")
        compiler.validate_package_contents(folder, package, report)
        report.update(ok=True, world_id=package["world_id"], compiler=package["compiler"], validator=compiler.VALIDATOR)
        report["checks"][:0] = ["bounded_local_files", "complete_hashes"]
    except (ValueError, OSError, KeyError, TypeError, IndexError, OverflowError) as error:
        report["errors"].append(str(error))
    return report


def build_package(intent, character_package_dir, output_dir):
    character_report = validate_character_package(Path(character_package_dir))
    if not character_report["ok"]:
        raise ValueError("character package rejected: "+"; ".join(character_report["errors"]))
    character_package = read_json(Path(character_package_dir)/"package.json")
    character = read_json(Path(character_package_dir)/character_package.get("runtime_manifest", "character.json"))
    spec = intent_to_spec(intent, character)
    compiler = get_compiler(spec["compiler"])
    result = compiler.compile_world(spec, character)
    destination = Path(output_dir).absolute()
    if destination.exists():
        raise ValueError("immutable package output already exists; choose a new directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent/(".world-package-"+uuid.uuid4().hex)
    temporary.mkdir()
    try:
        documents = {"intent.json": intent, "spec.json": spec, "character.json": character, "world.json": result["world"],
                     "assets.json": result["assets"], "routine.json": result["routine"], "brief.json": result["brief"], "compile.json": result["receipt"]}
        for name, data in documents.items():
            write_json(temporary/name, data)
        package = {"schema_version": 1, "package_kind": "domes_world", "world_id": spec["world_id"],
                   "compiler": spec["compiler"], "compiler_version": spec["compiler_version"], "runtime_manifest": "world.json",
                   "spec_path": "spec.json", "intent_path": "intent.json", "character_manifest": "character.json",
                   "files": {name: digest(temporary/name) for name in sorted(documents)},
                   "documents": {"assets": "assets.json", "routine": "routine.json", "brief": "brief.json", "receipt": "compile.json"},
                   "requirements": spec["character_profile"], "provenance": {"character_package_sha256": digest(Path(character_package_dir)/"package.json"),
                   "intent_sha256": hashlib.sha256(canonical(intent)).hexdigest(), "source": "Structured Dot and owner intent; original procedural assets"},
                   "limitations": result["receipt"]["limitations"], "validation": {"validator": compiler.VALIDATOR, "report": "validation.json"}}
        write_json(temporary/"package.json", package)
        report = validate_package(temporary)
        if not report["ok"]:
            raise ValueError("; ".join(report["errors"]))
        write_json(temporary/"validation.json", report)
        temporary.rename(destination)
        return {"package_dir": str(destination), "world_id": spec["world_id"], "validation": report}
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("build")
    create.add_argument("--intent", type=Path, required=True)
    create.add_argument("--character-package", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("validate")
    check.add_argument("package", type=Path)
    args = parser.parse_args()
    try:
        result = validate_package(args.package) if args.command == "validate" else build_package(read_json(args.intent), args.character_package, args.output)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok", True) else 1
    except (ValueError, OSError) as error:
        print(json.dumps({"ok": False, "errors": [str(error)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
