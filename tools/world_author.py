#!/usr/bin/env python3
"""Review and apply Dot-authored JSON with validated candidates and recoverable swaps.

This local development tool is not an authority boundary for an agent that can
edit the repository directly. It never edits saves, downloads assets, executes
scene code, grants permissions, or approves a request on the owner's behalf.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import uuid

try:
    from .validate_content import ContentValidator, read_json
except ImportError:
    from validate_content import ContentValidator, read_json

ROOT = Path(__file__).resolve().parents[1]
MAX_TREE_BYTES = 16 * 1024 * 1024
MAX_TRANSACTIONS = 10
DEFAULT_POLICY = {
    "autonomy": "within_bounds", "allowed_tools": ["world_author"],
    "allowed_operations": ["add_object", "move_object", "modify_object", "add_zone", "modify_zone", "add_station", "modify_station", "add_asset", "modify_asset", "replace_character", "edit_routine_presentation", "decorate", "edit_brief"],
    "destructive_actions": "require_owner_review", "max_objects": 1000,
    "max_zones": 100, "max_stations": 1000, "max_assets": 5000,
    "max_primitive_parts": 100000, "max_content_bytes": MAX_TREE_BYTES,
    "world_bounds": {"min_x": -10000, "max_x": 10000, "min_z": -10000, "max_z": 10000},
    "forbidden_asset_tags": [], "forbidden_behaviors": [],
}


class AuthoringError(ValueError):
    pass


def is_link(path: Path) -> bool:
    if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
        return True
    try:
        # Python 3.11 lacks Path.is_junction; reject Windows reparse points
        # through their native file attributes there as well.
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except FileNotFoundError:
        return False


def encoded(document: dict) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(document))


def tree_files(directory: Path) -> list[Path]:
    if is_link(directory):
        raise AuthoringError("content directories cannot be links or junctions")
    files = []
    total = 0
    for path in sorted(directory.rglob("*")):
        if is_link(path):
            raise AuthoringError("content cannot contain links or junctions")
        if path.is_file():
            total += path.stat().st_size
            files.append(path)
    if total > MAX_TREE_BYTES or len(files) > 4096:
        raise AuthoringError("content snapshot exceeds 16 MiB or 4096 files; reduce it before authoring")
    return files


def content_hash(directory: Path) -> str:
    if not directory.is_dir():
        raise AuthoringError("content directory is missing; inspect the authoring journal and recover")
    digest = hashlib.sha256()
    for path in tree_files(directory):
        name = path.relative_to(directory).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(name).to_bytes(4, "big") + name)
        digest.update(len(payload).to_bytes(8, "big") + payload)
    return digest.hexdigest()


class CandidateValidator(ContentValidator):
    """Candidate content plus already-reviewed resources from the real project."""
    def __init__(self, candidate_root: Path, source_root: Path):
        super().__init__(candidate_root)
        self.source = ContentValidator(source_root)

    def resource_path(self, reference: str) -> Path:
        if reference.casefold().startswith("res://content/"):
            return super().resource_path(reference)
        return self.source.resource_path(reference)


def bundle(validator: ContentValidator, world_id: str) -> dict:
    catalog = read_json(validator.godot / "content/catalog.json")
    entries = [entry for entry in catalog["worlds"] if entry["id"] == world_id]
    if len(entries) != 1:
        raise AuthoringError(f"world {world_id!r} is not registered exactly once")
    entry = entries[0]
    world = read_json(validator.resource_path(entry["path"]))
    paths = {"world": entry["path"], "brief": world["brief_path"], "character": world["character_path"], "routine": world["routine_path"]}
    result = {name: read_json(validator.resource_path(path)) for name, path in paths.items()}
    result["paths"] = set(paths.values()) | set(world["asset_manifest_paths"])
    result["assets"] = {}
    for path in world["asset_manifest_paths"]:
        for asset in read_json(validator.resource_path(path))["assets"]:
            result["assets"][asset["id"]] = asset
    return result


def routine_meaning(routine: dict) -> tuple:
    # Presentation, clips, station choice and project visual/stage labels can
    # change without reinterpreting integrated seconds for an existing epoch.
    return (
        routine["id"], routine["cycle_seconds"],
        [(s["id"], s["activity_tag"], s["duration_seconds"]) for s in routine["steps"]],
        [(p["id"], p["activity_tag"], p["required_seconds"]) for p in routine["projects"]],
    )


def operation_diff(before: dict | None, after: dict) -> set[str]:
    if before is None:
        return {"create_world"}
    operations = set()
    for plural, singular in [("objects", "object"), ("zones", "zone"), ("stations", "station")]:
        old = {item["id"]: item for item in before["world"][plural]}
        new = {item["id"]: item for item in after["world"][plural]}
        if new.keys() - old.keys():
            operations.add("add_" + singular)
        if old.keys() - new.keys():
            operations.add("remove_" + singular)
        for identity in old.keys() & new.keys():
            if old[identity] == new[identity]:
                continue
            changed = {key for key in old[identity].keys() | new[identity].keys() if old[identity].get(key) != new[identity].get(key)}
            operations.add("move_object" if singular == "object" and changed <= {"position", "rotation_y", "scale"} else "modify_" + singular)
    for identity in after["assets"].keys() - before["assets"].keys():
        operations.add("add_asset")
    for identity in before["assets"].keys() - after["assets"].keys():
        operations.add("remove_asset")
    for identity in before["assets"].keys() & after["assets"].keys():
        if before["assets"][identity] != after["assets"][identity]:
            operations.add("modify_asset")
    for name, operation in [("character", "replace_character"), ("routine", "edit_routine_presentation"), ("brief", "edit_brief")]:
        if before[name] != after[name]:
            operations.add(operation)
    ignored = {"objects", "zones", "stations", "asset_manifest_paths", "character_path", "routine_path", "brief_path"}
    if any(before["world"].get(key) != after["world"].get(key) for key in before["world"] if key not in ignored):
        operations.add("decorate")
    return operations


def enforce_policy(policy: dict, before: dict | None, after: dict, operations: set[str], validator: ContentValidator) -> tuple[list[str], dict]:
    problems = []
    if "world_author" not in policy["allowed_tools"]:
        problems.append("owner policy does not allow world_author")
    if before:
        denied = operations - set(policy["allowed_operations"])
        if denied:
            problems.append("operations outside owner policy: " + ", ".join(sorted(denied)))
        if any(op.startswith("remove_") for op in operations) and policy["destructive_actions"] != "allow":
            problems.append("destructive removal requires a separately reviewed owner amendment; there is no JSON approval override")
    world = after["world"]
    metrics = {"objects": len(world["objects"]), "zones": len(world["zones"]), "stations": len(world["stations"]), "assets": len(after["assets"]), "primitive_parts": sum(len(asset["parts"]) for asset in after["assets"].values()), "content_bytes": sum(validator.resource_path(path).stat().st_size for path in after["paths"])}
    for name, count in metrics.items():
        if count > policy["max_" + name]:
            problems.append(f"owner budget exceeded: {name}={count}, maximum={policy['max_' + name]}")
    limits = policy["world_bounds"]
    if limits["min_x"] >= limits["max_x"] or limits["min_z"] >= limits["max_z"]:
        problems.append("owner world bounds must have increasing minima/maxima")
    points = [("spawn", world["spawn"])]
    for zone in world["zones"]:
        for sx, sz in [(-1, -1), (1, 1)]:
            points.append(("zone " + zone["id"], [zone["center"][0] + sx * zone["size"][0] / 2, 0, zone["center"][2] + sz * zone["size"][1] / 2]))
    for obj in world["objects"]:
        asset = after["assets"][obj["asset_id"]]
        # Declared footprints use exactly the same nested transform order as
        # NavigationCheck, including nonuniform scale and non-colliding props.
        for sign_x, sign_z in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            x = sign_x * asset["footprint"][0] * asset["scale"][0] / 2
            z = sign_z * asset["footprint"][1] * asset["scale"][2] / 2
            for degrees, scale_x, scale_z in [(asset["rotation_y"], obj["scale"][0], obj["scale"][2]), (obj["rotation_y"], 1, 1)]:
                angle = math.radians(-degrees)
                x, z = (x * math.cos(angle) - z * math.sin(angle)) * scale_x, (x * math.sin(angle) + z * math.cos(angle)) * scale_z
            points.append(("object footprint " + obj["id"], [obj["position"][0] + x, 0, obj["position"][2] + z]))
    points += [("station " + station["id"], station[key]) for station in world["stations"] for key in ["approach", "interaction"]]
    for label, point in points:
        if not (limits["min_x"] <= point[0] <= limits["max_x"] and limits["min_z"] <= point[2] <= limits["max_z"]):
            problems.append(label + " is outside owner world bounds")
    forbidden_tags = set(policy["forbidden_asset_tags"])
    forbidden_behaviors = set(policy["forbidden_behaviors"])
    for asset in after["assets"].values():
        if forbidden_tags.intersection(asset["tags"] + [asset["category"]]):
            problems.append("owner policy forbids asset tags/category for " + asset["id"])
        if asset["behavior"] and asset["behavior"] in forbidden_behaviors:
            problems.append("owner policy forbids asset behavior " + asset["behavior"])
    for station in world["stations"]:
        if station["behavior"] and station["behavior"] in forbidden_behaviors:
            problems.append("owner policy forbids station behavior " + station["behavior"])
    return problems, metrics


def load_request(path: Path) -> dict:
    if path.stat().st_size > MAX_TREE_BYTES:
        raise AuthoringError("request exceeds 16 MiB")
    return read_json(path)


def prepare_request(root: Path, proposal: dict) -> dict:
    check_root(root)
    proposal = dict(proposal)
    proposal["base_content_hash"] = content_hash(root / "godot/content")
    errors = ContentValidator(root).validate_document("change-request", proposal)
    if errors:
        raise AuthoringError("\n".join(errors))
    return proposal


def prepare_candidate(root: Path, request: dict, stage: Path) -> dict:
    check_root(root)
    source = ContentValidator(root)
    errors = source.validate_document("change-request", request)
    if errors:
        raise AuthoringError("\n".join(errors))
    if request["base_content_hash"] != content_hash(root / "godot/content"):
        raise AuthoringError("stale_request: authored content changed; review and prepare a new request")
    errors = source.validate()
    if errors:
        raise AuthoringError("source content is invalid; repair before applying:\n" + "\n".join(errors))
    def document_key(path: str) -> str:
        return os.path.normcase(str((root / path).resolve()))
    paths = [item["path"] for item in request["files"]]
    path_keys = [document_key(path) for path in paths]
    if len(path_keys) != len(set(path_keys)):
        raise AuthoringError("request repeats a document path")
    catalog = read_json(root / "godot/content/catalog.json")
    existing = {entry["id"]: entry for entry in catalog["worlds"]}
    creating = request["intent"] == "create"
    if creating and request["world_id"] in existing:
        raise AuthoringError("create requires a new world identity; use expand for an existing home")
    if not creating and request["world_id"] not in existing:
        raise AuthoringError("expand requires an existing world identity")
    before = None if creating else bundle(source, request["world_id"])
    world_path = "godot/content/worlds/" + request["world_id"] + ".json" if creating else "godot/" + existing[request["world_id"]]["path"][6:]
    if document_key(world_path) not in path_keys:
        raise AuthoringError("request must include the complete target world document")
    supplied_world = next(item["document"] for item in request["files"] if document_key(item["path"]) == document_key(world_path))
    errors = source.validate_document("world", supplied_world)
    if errors:
        raise AuthoringError("\n".join(errors))
    if supplied_world["id"] != request["world_id"]:
        raise AuthoringError("request and world identities differ")
    target_paths = {world_path, "godot/" + supplied_world["brief_path"][6:], "godot/" + supplied_world["character_path"][6:], "godot/" + supplied_world["routine_path"][6:]}
    target_paths.update("godot/" + path[6:] for path in supplied_world["asset_manifest_paths"])
    if set(path_keys) - {document_key(path) for path in target_paths}:
        raise AuthoringError("request contains documents outside the target world's referenced bundle")
    # Another world's shared documents may be reused verbatim, never rewritten.
    protected = set()
    for world_id in existing:
        if world_id != request["world_id"]:
            protected.update(document_key("godot/" + path[6:]) for path in bundle(source, world_id)["paths"])
    for item in request["files"]:
        path = root / item["path"]
        if path.exists() and (creating or document_key(item["path"]) in protected):
            if read_json(path) != item["document"]:
                raise AuthoringError("cannot overwrite existing/shared document: " + item["path"])
    shutil.copytree(root / "schemas", stage / "schemas")
    shutil.copytree(root / "godot/content", stage / "godot/content")
    for item in request["files"]:
        write_json(stage / item["path"], item["document"])
    if creating:
        catalog["worlds"].append({"id": request["world_id"], "title": supplied_world["title"], "path": "res://" + world_path[len("godot/"):]})
    else:
        existing[request["world_id"]]["title"] = supplied_world["title"]
    write_json(stage / "godot/content/catalog.json", catalog)
    candidate = CandidateValidator(stage, root)
    errors = candidate.validate()
    if errors:
        raise AuthoringError("candidate validation failed:\n" + "\n".join(errors))
    after = bundle(candidate, request["world_id"])
    if before:
        if before["brief"]["owner_locked"] != after["brief"]["owner_locked"]:
            raise AuthoringError("owner_locked is immutable here, including authoring_policy; use a separately reviewed owner amendment")
        if before["brief"]["expansion_history"] != after["brief"]["expansion_history"]:
            raise AuthoringError("history is append-only and written by the tool; supply the existing history unchanged")
        if before["world"]["version"] != after["world"]["version"] or before["character"]["id"] != after["character"]["id"] or before["brief"]["dot_name"] != after["brief"]["dot_name"]:
            raise AuthoringError("compatible expansion preserves world version, character identity and Dot name; create a new world identity for a new timeline")
        if routine_meaning(before["routine"]) != routine_meaning(after["routine"]):
            raise AuthoringError("routine timing/project meaning changed: preserve existing epoch with presentation-only edits, or create a separate world/routine identity and fresh timeline; active saves are never migrated here")
    elif any(after["routine"]["id"] == bundle(source, world_id)["routine"]["id"] for world_id in existing):
        raise AuthoringError("new worlds need a distinct routine identity for their own timeline")
    if any(entry["id"] == request["id"] for entry in after["brief"]["expansion_history"]):
        raise AuthoringError("request id already appears in world history")
    operations = operation_diff(before, after)
    policy = after["brief"]["owner_locked"].get("authoring_policy", DEFAULT_POLICY)
    errors = candidate.validate_document("owner-policy", policy)
    if errors:
        raise AuthoringError("\n".join(errors))
    after["brief"]["expansion_history"].append({
        "id": request["id"], "owner_locked_preserved": True,
        "description": f"{datetime.now(timezone.utc).date().isoformat()}: {request['description']} Operations: {', '.join(sorted(operations))}. Source SHA256: {request['base_content_hash']}. Existing locks preserved; native/browser saves untouched. Candidate schema/reference/navigation validation passed; runtime/browser acceptance is separate. Recovery: artifacts/authoring transaction receipt.",
    })
    write_json(candidate.resource_path(after["world"]["brief_path"]), after["brief"])
    errors, metrics = enforce_policy(policy, before, after, operations, candidate)
    errors.extend(candidate.validate())
    if errors:
        raise AuthoringError("\n".join(errors))
    # Budget and link checks apply to the entire swapped tree as well.
    candidate_hash = content_hash(stage / "godot/content")
    return {
        "schema_version": 1, "request_id": request["id"], "world_id": request["world_id"], "intent": request["intent"],
        "base_content_hash": request["base_content_hash"], "candidate_content_hash": candidate_hash,
        "request_hash": hashlib.sha256(encoded(request)).hexdigest(), "operations": sorted(operations),
        "metrics": metrics, "policy_source": "owner_locked.authoring_policy" if "authoring_policy" in after["brief"]["owner_locked"] else "documented_default",
        "status": "ready" if policy["autonomy"] == "within_bounds" else "owner_review_required",
        "save_effect": "untouched; compatible existing identities and integrated routine timing preserved",
        "verification": "authoring checks only; build and runtime/browser acceptance still required",
    }


def plan(root: Path, request: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="domes-author-plan-") as temporary:
        return prepare_candidate(root, request, Path(temporary))


def workspace(root: Path) -> Path:
    check_root(root)
    path = root / "artifacts/authoring"
    if not path.resolve().is_relative_to(root.resolve()) or is_link(path) or is_link(path.parent):
        raise AuthoringError("authoring workspace must remain inside the repository")
    path.mkdir(parents=True, exist_ok=True)
    return path


def check_root(root: Path) -> None:
    for relative in ["godot", "godot/content", "schemas"]:
        path = root / relative
        if is_link(path) or not path.resolve().is_relative_to(root.resolve()):
            raise AuthoringError("authoring source paths must remain inside the repository without links or junctions")


def check_output(root: Path, path: Path) -> None:
    resolved = path.resolve()
    if path.exists() or is_link(path):
        raise AuthoringError("output already exists; use a new reviewable artifact filename")
    if resolved.is_relative_to(root):
        if not resolved.is_relative_to(root / "artifacts") or resolved.is_relative_to(root / "artifacts/authoring"):
            raise AuthoringError("repository outputs must use artifacts/ outside reserved artifacts/authoring; never overwrite source or transaction files")


def write_output(root: Path, path: Path, result: dict) -> None:
    check_output(root, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents a same-name file appearing after the check
    # from being overwritten by a report.
    with path.open("xb") as output:
        output.write(encoded(result))


@contextmanager
def writer_lock(root: Path):
    lock = workspace(root) / "write.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise AuthoringError("authoring writer lock exists; close other authoring processes before manually removing the empty artifacts/authoring/write.lock directory")
    try:
        yield
    finally:
        lock.rmdir()


def save_journal(transaction: Path, report: dict) -> None:
    temporary = transaction / "journal.tmp"
    with temporary.open("wb") as output:
        output.write(encoded(report))
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, transaction / "journal.json")


def apply_request(root: Path, request: dict, *, fault_hook=None) -> dict:
    with writer_lock(root):
        home = workspace(root)
        if len([p for p in home.iterdir() if p.is_dir() and p.name != "write.lock"]) >= MAX_TRANSACTIONS:
            raise AuthoringError("10 retained transactions reached; archive reviewed old receipts/backups outside artifacts/authoring before applying another request")
        # The candidate is rebuilt under the exclusive authoring-tool lock.
        # External editors are not locked: close editors/builds during apply.
        with tempfile.TemporaryDirectory(prefix="domes-author-stage-") as temporary:
            stage = Path(temporary)
            report = prepare_candidate(root, request, stage)
            if report["status"] != "ready":
                raise AuthoringError("owner policy is proposal_only; candidate is reviewable but this tool cannot approve or apply it")
            transaction_id = request["id"] + "-" + uuid.uuid4().hex[:12]
            transaction = home / transaction_id
            transaction.mkdir()
            candidate_path = transaction / "candidate"
            shutil.copytree(stage / "godot/content", candidate_path)
        report.update({"transaction_id": transaction_id, "status": "prepared"})
        save_journal(transaction, report)
        try:
            if content_hash(root / "godot/content") != report["base_content_hash"]:
                raise AuthoringError("stale_request: source changed during validation; no content replaced")
            if content_hash(candidate_path) != report["candidate_content_hash"]:
                raise AuthoringError("candidate bytes changed after validation")
            os.replace(root / "godot/content", transaction / "before")
            if fault_hook:
                fault_hook("after_backup")
            os.replace(candidate_path, root / "godot/content")
            if fault_hook:
                fault_hook("after_install")
            if content_hash(root / "godot/content") != report["candidate_content_hash"]:
                raise AuthoringError("installed content failed verification")
            report["status"] = "committed"
            save_journal(transaction, report)
        except Exception:
            # Best effort recovery uses the same byte guards as explicit recovery.
            # If another writer intervened, keep all versions and fail closed.
            if (transaction / "before").exists():
                recover_transaction(root, transaction_id, already_locked=True)
            raise
        return report


def recover_transaction(root: Path, transaction_id: str, *, already_locked=False) -> dict:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}-[a-f0-9]{12}", transaction_id):
        raise AuthoringError("invalid transaction id")
    if not already_locked:
        with writer_lock(root):
            return recover_transaction(root, transaction_id, already_locked=True)
    transaction = workspace(root) / transaction_id
    if is_link(transaction):
        raise AuthoringError("transaction cannot be a link or junction")
    report = read_json(transaction / "journal.json")
    live = root / "godot/content"
    before = transaction / "before"
    current = content_hash(live) if live.exists() else None
    if current == report["base_content_hash"]:
        report["status"] = "recovered"
        save_journal(transaction, report)
        return report
    if current is not None and current != report["candidate_content_hash"]:
        raise AuthoringError("recovery_conflict: content has newer edits; preserve them and resolve manually")
    if not before.exists() or content_hash(before) != report["base_content_hash"]:
        raise AuthoringError("recovery backup is missing or fails its content hash")
    displaced = transaction / "rolled_back_candidate"
    if displaced.exists():
        if live.exists() or content_hash(displaced) != report["candidate_content_hash"]:
            raise AuthoringError("recovery candidate destination conflicts; inspect transaction")
        # A previous recovery moved live aside and then stopped before restoring
        # before. Both hashes are now known, so finish that interrupted restore.
    if live.exists():
        os.replace(live, displaced)
    os.replace(before, live)
    if content_hash(live) != report["base_content_hash"]:
        raise AuthoringError("restored content hash failed; preserve the journal for manual recovery")
    report["status"] = "recovered"
    save_journal(transaction, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["create", "prepare"]:
        command = commands.add_parser(name, help="snapshot a complete Dot-authored proposal into a change request")
        command.add_argument("proposal", type=Path)
        command.add_argument("--output", type=Path, required=True)
    for name in ["plan", "apply"]:
        command = commands.add_parser(name)
        command.add_argument("request", type=Path)
        command.add_argument("--output", type=Path)
    command = commands.add_parser("recover", help="guarded rollback of a committed or interrupted transaction")
    command.add_argument("transaction_id")
    commands.add_parser("hash", help="current source-content hash")
    commands.add_parser("default-policy", help="print the exact fallback limits; does not grant authority")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if getattr(args, "output", None):
            check_output(root, args.output)
        if args.command == "hash":
            result = {"base_content_hash": content_hash(root / "godot/content")}
        elif args.command == "default-policy":
            result = DEFAULT_POLICY
        elif args.command in {"create", "prepare"}:
            proposal = load_request(args.proposal)
            if args.command == "create" and proposal.get("intent") != "create":
                raise AuthoringError("create expects intent=create; use prepare for an expansion")
            result = prepare_request(root, proposal)
            write_output(root, args.output, result)
            result = {"status": "request_prepared", "request": str(args.output), "base_content_hash": result["base_content_hash"]}
        elif args.command == "recover":
            result = recover_transaction(root, args.transaction_id)
        else:
            request = load_request(args.request)
            result = plan(root, request) if args.command == "plan" else apply_request(root, request)
            if args.output:
                write_output(root, args.output, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as issue:
        print(f"FAIL: {issue}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
