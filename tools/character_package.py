"""Producer-independent envelope checks followed by mandatory backend validation.

Valid JSON and correct hashes do not authorize arbitrary models or scripts.
Only trusted registered producer validators can approve a package for staging.
"""
from pathlib import Path, PurePosixPath
import stat
import struct

from character_backends import get_backend
from character_contract import ROOT, digest, validate_schema
from validate_content import ContentValidator, read_json

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_PACKAGE_BYTES = 100 * 1024 * 1024


def local_file(folder, name):
    logical = PurePosixPath(name)
    if logical.is_absolute() or any(part in (".", "..") for part in logical.parts) or "\\" in name:
        raise ValueError("unsafe package file path")
    path = folder / name
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            raise ValueError("package files cannot contain links or reparse points")
        if part == folder:
            break
    if not path.is_file() or not path.resolve().is_relative_to(folder):
        raise ValueError("package must contain regular local files: " + name)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("package file exceeds 20 MiB")
    return path


def validate_package(package_dir: Path) -> dict:
    folder = Path(package_dir).absolute()
    report = {"schema_version": 1, "ok": False, "errors": [], "checks": [],
              "scope": "Generic envelope, identities, bounded files/digests and runtime manifest, followed by registered backend-specific specification/asset checks. Engine import, visual fit and browser playback require separate acceptance."}
    try:
        # Check the root before resolving it so a linked root is not normalized away.
        if folder.is_symlink() or getattr(folder.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            raise ValueError("package root cannot be a link or reparse point")
        package = read_json(local_file(folder, "package.json"))
        validate_schema("character-package", package)
        producer = get_backend(package["backend"])
        runtime_path = package.get("runtime_manifest", "character.json")
        spec_path = package.get("spec_path", "spec.json")
        if runtime_path == spec_path or any(name not in package["files"] for name in (runtime_path, spec_path)):
            raise ValueError("manifest and specification must be distinct hashed package files")
        names = list(package["files"])
        if len({name.casefold() for name in names}) != len(names) or any(name.casefold() in ("package.json", "validation.json") for name in names):
            raise ValueError("package file aliases or reserved metadata names")
        total = 0
        for name, expected in package["files"].items():
            path = local_file(folder, name)
            total += path.stat().st_size
            if total > MAX_PACKAGE_BYTES:
                raise ValueError("package exceeds 100 MiB")
            if digest(path) != expected:
                raise ValueError("file digest mismatch: " + name)
        validation = package.get("validation", {"validator": producer.VALIDATOR, "report": "validation.json"})
        if validation != {"validator": producer.VALIDATOR, "report": "validation.json"}:
            raise ValueError("validation metadata disagrees with registered backend contract")
        # validation.json is a non-authoritative receipt; always recompute approval.
        permitted = set(names) | {"package.json", "validation.json"}
        for path in folder.rglob("*"):
            if path.is_symlink():
                raise ValueError("package cannot contain links")
            if path.is_file():
                local_file(folder, path.relative_to(folder).as_posix())
                if path.relative_to(folder).as_posix() not in permitted:
                    raise ValueError("undeclared package file")
        manifest = read_json(folder / runtime_path)
        spec = read_json(folder / spec_path)
        validate_schema("character-spec", spec)
        errors = ContentValidator(ROOT).validate_document("character", manifest)
        if errors:
            raise ValueError("; ".join(errors))
        if not package["character_id"] == manifest["id"] == spec["character_id"] or package["backend"] != spec["backend"]:
            raise ValueError("package/spec/character identities or backends disagree")
        assets = package.get("assets", {"character.glb": manifest["scene_path"]})
        if set(assets) != set(names) - {runtime_path, spec_path}:
            raise ValueError("every asset must have a hashed file and installation mapping")
        if manifest["scene_path"] not in assets.values() or len(set(assets.values())) != len(assets):
            raise ValueError("runtime scene must resolve to a unique packaged asset")
        prefix = f"res://assets/generated/{package['character_id']}/"
        targets = []
        for target in assets.values():
            logical = PurePosixPath(target[6:])
            if not target.startswith(prefix) or "\\" in target or ".." in logical.parts or target.endswith("/"):
                raise ValueError("asset installation path must stay in the character namespace")
            targets.append(target.casefold())
        if len(set(targets)) != len(targets):
            raise ValueError("asset installation aliases")
        report.update(backend=package["backend"], validator=producer.VALIDATOR)
        report["checks"].append("schemas_and_digests")
        # No unknown backend can pass simply by presenting a generic envelope.
        producer.validate_assets(folder, package, manifest, spec, report)
        report["ok"] = True
    except (ValueError, OSError, KeyError, IndexError, TypeError, struct.error, OverflowError) as error:
        report["errors"].append(str(error))
    return report
