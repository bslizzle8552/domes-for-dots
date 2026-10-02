#!/usr/bin/env python3
"""Narrow, hash-bound revisions over the existing recoverable world author.

Only supported data operations are accepted. The isolated candidate is rebuilt
from the current base for plan AND apply. A stored validation receipt has no
authority. This is an operator filesystem adapter, not cloud authentication or
distributed compare-and-swap.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys

try:
    from . import world_author as author
    from .world_revision_guards import KINDS, protection_records
except ImportError:
    import world_author as author
    from world_revision_guards import KINDS, protection_records


RevisionError = author.AuthoringError
ID = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")
MIGRATION_STRATEGY = "preserve_existing_ids_and_routine"
STRUCTURAL = {"add_zone", "add_transition", "add_level"}
ADD = {"add_object": "objects", "add_station": "stations", "add_zone": "zones", "add_transition": "transitions", "add_level": "levels"}
CANDIDATE_KEYS = {"schema_version", "id", "world_id", "base_revision", "base_revision_id", "base_content_hash", "reason", "operations", "state_migration", "source_package_hash"}


def _exact(document: dict, keys: set[str], label: str) -> None:
    if not isinstance(document, dict) or set(document) != keys:
        raise RevisionError(label + " must contain exactly: " + ", ".join(sorted(keys)))


def _identity(value, label: str) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise RevisionError("invalid " + label)
    return value


def _base(root: Path, world_id: str) -> tuple[dict, str]:
    _identity(world_id, "world identity")
    author.check_root(root)
    source = author.ContentValidator(root)
    data = author.bundle(source, world_id)
    catalog = author.read_json(root / "godot/content/catalog.json")
    path = next(entry["path"] for entry in catalog["worlds"] if entry["id"] == world_id)
    return data, "godot/" + path[6:]


def _revision(world: dict) -> tuple[int, str]:
    state = world["metadata"].get("revision_state")
    if state is None:
        number = world["metadata"].get("structure_revision", 0)
        if type(number) is not int or number < 0:
            raise RevisionError("invalid initial structure revision")
        return number, "initial"
    if not isinstance(state, dict) or type(state.get("structure_revision")) is not int or state["structure_revision"] < 1:
        raise RevisionError("invalid current revision_state")
    if world["metadata"].get("structure_revision", state["structure_revision"]) != state["structure_revision"]:
        raise RevisionError("inconsistent active structure revision metadata")
    return state["structure_revision"], _identity(state.get("revision_id"), "current revision id")


def prepare_revision(root: Path, world_id: str, operations: list[dict], reason: str, request_id: str, *, state_migration: dict | None = None, source_package_hash: str | None = None) -> dict:
    """Snapshot the authoritative base and return a reviewable data-only request.

    Structural operations require an explicit migration. The package hash points
    to the immutable compiler seed; revisions do not rewrite that seed package.
    """
    before, _ = _base(root, world_id)
    number, revision_id = _revision(before["world"])
    prior = before["world"]["metadata"].get("revision_state", {})
    candidate = {
        "schema_version": 1, "id": request_id, "world_id": world_id,
        "base_revision": number, "base_revision_id": revision_id,
        "base_content_hash": author.content_hash(root / "godot/content"),
        "reason": reason, "operations": copy.deepcopy(operations),
        "state_migration": copy.deepcopy(state_migration),
        "source_package_hash": source_package_hash if source_package_hash is not None else prior.get("source_package_hash"),
    }
    _request(root, candidate)
    return candidate


def _validate_envelope(candidate: dict) -> None:
    _exact(candidate, CANDIDATE_KEYS, "revision candidate")
    if candidate["schema_version"] != 1 or type(candidate["base_revision"]) is not int or candidate["base_revision"] < 0:
        raise RevisionError("unsupported revision schema or base revision")
    for key in ["id", "world_id", "base_revision_id"]:
        _identity(candidate[key], key)
    if not isinstance(candidate["reason"], str) or not 1 <= len(candidate["reason"]) <= 1600:
        raise RevisionError("revision reason must contain 1..1600 characters")
    if not isinstance(candidate["base_content_hash"], str) or not HASH.fullmatch(candidate["base_content_hash"]):
        raise RevisionError("base content hash must be SHA-256")
    if candidate["source_package_hash"] is not None and (not isinstance(candidate["source_package_hash"], str) or not HASH.fullmatch(candidate["source_package_hash"])):
        raise RevisionError("source package hash must be SHA-256 or null")
    if not isinstance(candidate["operations"], list) or not 1 <= len(candidate["operations"]) <= 100:
        raise RevisionError("revision needs 1..100 narrow operations")
    # Reject non-JSON and nonfinite data before deriving geometry or writing.
    try:
        if len(author.encoded(candidate)) > 1024 * 1024:
            raise RevisionError("revision exceeds 1 MiB")
    except (ValueError, TypeError) as issue:
        raise RevisionError("revision requires finite JSON data") from issue


def _object(world: dict, identity: str) -> dict:
    _identity(identity, "object identity")
    found = [obj for obj in world["objects"] if obj["id"] == identity]
    if len(found) != 1:
        raise RevisionError("object must exist exactly once: " + identity)
    return found[0]


def _move(world: dict, operation: dict) -> list[str]:
    _exact(operation, {"op", "id", "position", "rotation_y"}, "move_object")
    obj = _object(world, operation["id"])
    position = operation["position"]
    yaw = operation["rotation_y"]
    if not isinstance(position, list) or len(position) != 3 or any(type(v) not in {int, float} or not math.isfinite(v) or abs(v) > 10000 for v in position) or type(yaw) not in {int, float} or not math.isfinite(yaw):
        raise RevisionError("move requires finite bounded position and rotation_y")
    old_position = obj["position"]
    delta = yaw - obj["rotation_y"]
    # Godot Y rotation maps +Z toward +X; preserve local station anchors.
    angle = math.radians(-delta)
    affected = ["object:" + obj["id"]]
    for station in world["stations"]:
        if station["object_id"] != obj["id"]:
            continue
        for key in ["approach", "interaction"]:
            x, y, z = [station[key][i] - old_position[i] for i in range(3)]
            station[key] = [round(position[0] + x * math.cos(angle) - z * math.sin(angle), 8), round(position[1] + y, 8), round(position[2] + x * math.sin(angle) + z * math.cos(angle), 8)]
        station["facing"] += delta
        affected.append("station:" + station["id"])
    obj.update(position=copy.deepcopy(position), rotation_y=yaw)
    return affected


def _rescale_station_anchors(world: dict, obj: dict, scale: list) -> list[str]:
    if not isinstance(scale, list) or len(scale) != 3 or any(type(value) not in {int, float} or not math.isfinite(value) or not 0.001 <= value <= 1000 for value in scale):
        raise RevisionError("scale requires three finite components in 0.001..1000")
    ratio = [scale[index] / obj["scale"][index] for index in range(3)]
    yaw = math.radians(obj["rotation_y"])
    affected = []
    for station in world["stations"]:
        if station["object_id"] != obj["id"]:
            continue
        for key in ["approach", "interaction"]:
            x, y, z = [station[key][index] - obj["position"][index] for index in range(3)]
            local_x = (x * math.cos(yaw) - z * math.sin(yaw)) * ratio[0]
            local_z = (x * math.sin(yaw) + z * math.cos(yaw)) * ratio[2]
            station[key] = [round(obj["position"][0] + local_x * math.cos(yaw) + local_z * math.sin(yaw), 8), round(obj["position"][1] + y * ratio[1], 8), round(obj["position"][2] - local_x * math.sin(yaw) + local_z * math.cos(yaw), 8)]
        affected.append("station:" + station["id"])
    return affected


def _request(root: Path, candidate: dict) -> tuple[dict, dict]:
    _validate_envelope(candidate)
    if author.content_hash(root / "godot/content") != candidate["base_content_hash"]:
        raise RevisionError("stale_revision: content changed; replan against the current world")
    before, world_path = _base(root, candidate["world_id"])
    if _revision(before["world"]) != (candidate["base_revision"], candidate["base_revision_id"]):
        raise RevisionError("stale_revision: active revision identity changed")
    world = copy.deepcopy(before["world"])
    documents = {world_path: world}
    affected = set()
    structural = False
    for operation in candidate["operations"]:
        if not isinstance(operation, dict) or not isinstance(operation.get("op"), str):
            raise RevisionError("operation must name a supported data operation")
        name = operation["op"]
        structural |= name in STRUCTURAL
        if name in ADD:
            _exact(operation, {"op", "entity"}, name)
            entity = operation["entity"]
            if not isinstance(entity, dict):
                raise RevisionError(name + " requires an entity document")
            identity = _identity(entity.get("id"), name + " identity")
            values = world.setdefault(ADD[name], [])
            if any(item["id"] == identity for item in values):
                raise RevisionError("stable entity identity already exists: " + identity)
            values.append(copy.deepcopy(entity))
            affected.add(name.removeprefix("add_") + ":" + identity)
        elif name == "move_object":
            affected.update(_move(world, operation))
        elif name == "modify_object":
            _exact(operation, {"op", "id", "changes"}, name)
            changes = operation["changes"]
            if not isinstance(changes, dict) or not changes or set(changes) - {"asset_id", "scale"}:
                raise RevisionError("modify_object supports asset_id/scale only; use move_object for transforms")
            obj = _object(world, operation["id"])
            if "scale" in changes:
                affected.update(_rescale_station_anchors(world, obj, changes["scale"]))
            obj.update(copy.deepcopy(changes))
            affected.add("object:" + operation["id"])
        elif name == "add_asset":
            _exact(operation, {"op", "manifest_path", "entity"}, name)
            path = operation["manifest_path"]
            if path not in world["asset_manifest_paths"] or not re.fullmatch(r"res://content/assets/[a-z][a-z0-9_]{0,63}\.json", path):
                raise RevisionError("add_asset requires an existing world-owned manifest")
            asset = operation["entity"]
            identity = _identity(asset.get("id") if isinstance(asset, dict) else None, "asset identity")
            if identity in before["assets"]:
                raise RevisionError("asset identity already exists")
            # New data-lane assets are procedural. Reviewed imported binaries
            # enter through the package/asset pipeline, never executable scenes.
            if asset.get("scene_path") or not asset.get("parts"):
                raise RevisionError("add_asset requires nonempty procedural parts and no scene path")
            relative = "godot/" + path[6:]
            if relative not in documents:
                documents[relative] = author.read_json(root / relative)
            documents[relative]["assets"].append(copy.deepcopy(asset))
            affected.add("asset:" + identity)
        elif name == "decorate":
            _exact(operation, {"op", "environment"}, name)
            _exact(operation["environment"], set(world["environment"]), "environment")
            world["environment"] = copy.deepcopy(operation["environment"])
            affected.add("world:environment")
        else:
            raise RevisionError("unsupported operation in data lane: " + name)
    migration = candidate["state_migration"]
    if structural and migration is None:
        raise RevisionError("structural addition requires an explicit state migration")
    if migration is not None:
        _exact(migration, {"strategy", "routine_id", "reset_transient_navigation"}, "state migration")
        if migration["strategy"] != MIGRATION_STRATEGY or migration["routine_id"] != before["routine"]["id"] or migration["reset_transient_navigation"] is not True:
            raise RevisionError("only identity-preserving migration with the current routine and transient navigation reset is supported")
    prior = before["world"]["metadata"].get("revision_state", {})
    if prior.get("source_package_hash") is not None and prior["source_package_hash"] != candidate["source_package_hash"]:
        raise RevisionError("source package provenance is immutable across narrow edits")
    protections = protection_records(before)
    world["metadata"]["structure_revision"] = candidate["base_revision"] + 1
    world["metadata"]["revision_state"] = {
        "structure_revision": candidate["base_revision"] + 1,
        "revision_id": candidate["id"], "parent_revision_id": candidate["base_revision_id"],
        "base_content_hash": candidate["base_content_hash"],
        "source_package_hash": candidate["source_package_hash"],
        "reason": candidate["reason"], "chosen_by": "dot",
        "operations": copy.deepcopy(candidate["operations"]),
        "affected_entities": sorted(affected),
        "protected_entities": [item["kind"] + ":" + item["id"] for item in protections],
        "state_migration": copy.deepcopy(migration),
        "rollback_reference": {"revision_id": candidate["base_revision_id"], "content_hash": candidate["base_content_hash"]},
        "compiled_seed_modified": True,
    }
    request = {
        "schema_version": 1, "id": candidate["id"], "world_id": candidate["world_id"], "intent": "expand",
        "description": candidate["reason"], "base_content_hash": candidate["base_content_hash"],
        "files": [{"path": path, "document": document} for path, document in documents.items()],
    }
    context = {
        "base_revision": candidate["base_revision"], "structure_revision": candidate["base_revision"] + 1,
        "revision_id": candidate["id"], "affected_entities": sorted(affected),
        "protected_entities": world["metadata"]["revision_state"]["protected_entities"],
        "expected_capabilities": sorted({operation["op"] for operation in candidate["operations"]}),
        "state_migration": migration,
        "state_effect": "runtime state files untouched; routine epoch, preferences and meaningful progress preserved",
        "activation_scope": "local authored content; export/publication/runtime reload remain separate",
        "candidate_hash": hashlib.sha256(author.encoded(candidate)).hexdigest(),
    }
    return request, context


def plan_revision(root: Path, candidate: dict) -> dict:
    request, context = _request(root, candidate)
    return {**author.plan(root, request), **context}


def apply_revision(root: Path, candidate: dict, *, fault_hook=None) -> dict:
    request, context = _request(root, candidate)
    # world_author rebuilds and revalidates under its writer lock and checks the
    # exact content hash again before replacing anything.
    return {**author.apply_request(root, request, fault_hook=fault_hook), **context}


def rollback_revision(root: Path, transaction_id: str) -> dict:
    """Guarded exact recovery; refuses newer content rather than erasing it.

    The complete previous content tree/assets and original structure identity
    are restored. Runtime state lives outside that tree and is never restored
    from an old snapshot. The retained transaction journal remains the audit.
    """
    report = author.recover_transaction(root, transaction_id)
    before, _ = _base(root, report["world_id"])
    number, identity = _revision(before["world"])
    return {**report, "active_structure_revision": number, "active_revision_id": identity,
            "state_effect": "runtime state untouched; unrelated durable progress is not rolled back",
            "activation_scope": "local content recovery; hosted deployment requires its own rollback"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=author.ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("proposal", type=Path, help="JSON with world_id, operations, reason, request_id and optional state_migration/source_package_hash")
    prepare.add_argument("--output", type=Path, required=True)
    for name in ["plan", "apply"]:
        command = commands.add_parser(name)
        command.add_argument("candidate", type=Path)
        command.add_argument("--output", type=Path)
    rollback = commands.add_parser("rollback")
    rollback.add_argument("transaction_id")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if getattr(args, "output", None):
            author.check_output(root, args.output)
        if args.command == "prepare":
            proposal = author.load_request(args.proposal)
            result = prepare_revision(root, **proposal)
        elif args.command == "rollback":
            result = rollback_revision(root, args.transaction_id)
        else:
            candidate = author.load_request(args.candidate)
            result = plan_revision(root, candidate) if args.command == "plan" else apply_revision(root, candidate)
        if getattr(args, "output", None):
            author.write_output(root, args.output, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as issue:
        print("FAIL: " + str(issue), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
