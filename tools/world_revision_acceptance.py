#!/usr/bin/env python3
"""Produce independent, validated revision snapshots of one generated world.

The source composed repository is read-only. The owner move/pin is explicitly a
synthetic acceptance fixture. No Site, release, saved owner world, or deployment
is touched. Snapshot directories can subsequently be exported or registered by
the separate trusted hosting adapter.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

try:
    from . import world_author as author
    from . import world_revisions as revisions
except ImportError:
    import world_author as author
    import world_revisions as revisions


def _copy_repository(source: Path, target: Path) -> None:
    shutil.copytree(source / "schemas", target / "schemas")
    shutil.copytree(source / "godot", target / "godot", ignore=shutil.ignore_patterns(".godot"))


def _world(root: Path, world_id: str) -> tuple[dict, Path]:
    data, path = revisions._base(root, world_id)
    return data, root / path


def _lamp_asset() -> dict:
    return {
        "id": "revision_lamp_asset", "display_name": "Original field lamp", "category": "decoration", "tags": ["lamp", "original"],
        "scene_path": "", "scale": [1, 1, 1], "rotation_y": 0,
        "collision": {"enabled": False, "size": [0.3, 1.1, 0.3], "offset": [0, 0.55, 0]},
        "footprint": [0.3, 0.3], "anchors": {},
        "parts": [
            {"shape": "box", "position": [0, 0.04, 0], "size": [0.3, 0.08, 0.3], "rotation": [0, 0, 0], "color": "#8b724d", "emission": 0},
            {"shape": "box", "position": [0, 0.5, 0], "size": [0.06, 0.9, 0.06], "rotation": [0, 0, 0], "color": "#947a50", "emission": 0},
            {"shape": "box", "position": [0, 1, 0], "size": [0.3, 0.2, 0.3], "rotation": [0, 0, 0], "color": "#eed49b", "emission": 0.15},
        ],
        "animation": "", "behavior": "", "metadata": {"acceptance_fixture": True},
        "provenance": {"creator": "Domes for Dots contributors", "source": "Original procedural synthetic revision acceptance fixture", "license": "MIT"},
    }


def _owner_fixture(root: Path, world_id: str) -> dict:
    data, path = _world(root, world_id)
    world = data["world"]
    if "revision_lamp_asset" in data["assets"] or any(obj["id"] == "revision_owner_lamp" for obj in world["objects"]):
        raise revisions.RevisionError("acceptance fixture identities already exist")
    assets_path = root / ("godot/" + world["asset_manifest_paths"][0][6:])
    assets = author.read_json(assets_path)
    assets["assets"].append(_lamp_asset())
    author.write_json(assets_path, assets)
    # The moved placement is on a known support surface beside spawn. It is
    # intentionally noncolliding; all source collision/navigation still runs.
    position = list(world["spawn"])
    position[0] += 0.7
    obj = {"id": "revision_owner_lamp", "asset_id": "revision_lamp_asset", "position": position, "rotation_y": 15, "scale": [1, 1, 1]}
    world["objects"].append(obj)
    world["metadata"]["revision_acceptance_fixture"] = {"synthetic_owner_edit": True, "reason": "Synthetic owner moved this lamp and pinned it before the Dot's independent additions."}
    author.write_json(path, world)
    brief_path = root / ("godot/" + world["brief_path"][6:])
    brief = data["brief"]
    brief["owner_locked"].setdefault("entity_protection", []).append({"kind": "object", "id": obj["id"], "fields": ["*"], "chosen_by": "human", "reason": "Synthetic acceptance owner moved and pinned a meaningful lamp."})
    author.write_json(brief_path, brief)
    errors = author.ContentValidator(root).validate()
    if errors:
        raise revisions.RevisionError("owner fixture failed validation:\n" + "\n".join(errors))
    return obj


def run_acceptance(source: Path, output: Path, world_id: str, *, source_package_hash: str | None = None) -> dict:
    source, output = source.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(source / "godot") or output == source:
        raise revisions.RevisionError("use a new independent acceptance output directory")
    author.check_root(source)
    source_hash = author.content_hash(source / "godot/content")
    seed_manifest = source / "examples/world_creator" / (world_id + ".world") / "package.json"
    if source_package_hash is None and seed_manifest.is_file():
        source_package_hash = hashlib.sha256(seed_manifest.read_bytes()).hexdigest()
    output.mkdir(parents=True)
    working = output / "working"
    _copy_repository(source, working)
    lamp = _owner_fixture(working, world_id)
    state_path = working / "runtime-state.json"
    state = {"world_id": world_id, "routine_epoch": 1770000000, "preferences": {"sound": False}, "project_progress": {"synthetic_journal": 17}, "state_revision": 1}
    author.write_json(state_path, state)
    result = {"schema_version": 1, "world_id": world_id, "source_content_hash": source_hash, "source_package_hash": source_package_hash, "synthetic_owner_fixture": lamp, "snapshots": {}, "checks": {}, "limitations": ["Filesystem authoring acceptance; hosted CAS and browser scene activation are separately tested.", "Runtime state sentinel verifies no local save overwrite; it is not evidence of cloud durability."]}

    def snapshot(name: str, receipt: dict | None = None):
        target = output / name
        _copy_repository(working, target)
        data, _ = _world(working, world_id)
        entry = {"repository": str(target), "content_hash": author.content_hash(target / "godot/content"), "structure_revision": revisions._revision(data["world"])[0], "world_id": world_id, "receipt": receipt}
        result["snapshots"][name] = entry
        author.write_json(target / "snapshot.json", entry)

    def candidate(operations, identity, migration=None):
        return revisions.prepare_revision(working, world_id, operations, "Synthetic acceptance: " + identity.replace("_", " ") + "; keep the owner's lamp and all existing routine progress.", identity, state_migration=migration, source_package_hash=source_package_hash)

    def check_state():
        if author.read_json(state_path) != state:
            raise revisions.RevisionError("runtime state was changed by structure authoring")
        data, _ = _world(working, world_id)
        if next(obj for obj in data["world"]["objects"] if obj["id"] == lamp["id"]) != lamp:
            raise revisions.RevisionError("owner lamp was changed by an unrelated revision")
        errors = author.ContentValidator(working).validate()
        if errors:
            raise revisions.RevisionError("revision lost valid geometry/routes: " + "\n".join(errors))

    snapshot("base")
    data, _ = _world(working, world_id)
    protected = {record["id"] for record in data["brief"]["owner_locked"].get("entity_protection", []) if record["kind"] == "object"}
    edit = None
    rejected = []
    # Bounded candidate search changes one ordinary item by 10 cm. This is an
    # acceptance fixture search, not unconstrained automatic repair of a world.
    for obj in [obj for obj in data["world"]["objects"] if obj["id"] not in protected][:6]:
        for dx, dz in [(0.1, 0), (-0.1, 0), (0, 0.1), (0, -0.1)]:
            position = list(obj["position"])
            position[0] += dx
            position[2] += dz
            attempt = candidate([{"op": "move_object", "id": obj["id"], "position": position, "rotation_y": obj["rotation_y"]}], "acceptance_furniture")
            try:
                revisions.plan_revision(working, attempt)
                edit = attempt
                break
            except revisions.RevisionError as issue:
                rejected.append(str(issue))
        if edit:
            break
    if edit is None:
        raise revisions.RevisionError("no safe bounded furniture-edit fixture found: " + "\n".join(rejected))
    furniture = revisions.apply_revision(working, edit)
    check_state()
    snapshot("furniture", furniture)
    result["checks"]["furniture_preserves_owner_lamp_routes_and_state"] = "PASS"

    data, _ = _world(working, world_id)
    position = list(data["world"]["spawn"])
    position[0] -= 0.8
    station = {"id": "revision_inspect_lamp", "label": "Inspect a field observation lamp", "object_id": "revision_field_lamp", "activity_tags": ["inspect"], "approach": list(data["world"]["spawn"]), "interaction": list(data["world"]["spawn"]), "facing": -90, "animation": "interact", "fallback_animation": "idle", "behavior": "", "metadata": {"action_template": "inspect", "meaning": "A field lamp marks the new observation corner."}}
    if "levels" in data["world"]:
        level = next(level for level in data["world"]["levels"] if abs(level["elevation"] - position[1]) < 0.01)
        station["level_id"] = level["id"]
    addition_ops = [{"op": "add_object", "entity": {"id": "revision_field_lamp", "asset_id": "revision_lamp_asset", "position": position, "rotation_y": 0, "scale": [1, 1, 1]}}, {"op": "add_station", "entity": station}]
    addition_request = candidate(addition_ops, "acceptance_addition")
    stale = candidate([{"op": "move_object", "id": edit["operations"][0]["id"], "position": edit["operations"][0]["position"], "rotation_y": edit["operations"][0]["rotation_y"]}], "acceptance_stale")
    addition = revisions.apply_revision(working, addition_request)
    check_state()
    snapshot("addition", addition)
    result["checks"]["new_object_and_station_functional_in_validator"] = "PASS"
    current = author.content_hash(working / "godot/content")
    try:
        revisions.apply_revision(working, stale)
        raise AssertionError("stale candidate unexpectedly committed")
    except revisions.RevisionError as issue:
        if "stale_revision" not in str(issue):
            raise
        result["checks"]["stale_candidate_rejected"] = str(issue)
    if author.content_hash(working / "godot/content") != current:
        raise AssertionError("stale candidate changed content")

    data, _ = _world(working, world_id)
    migration = {"strategy": revisions.MIGRATION_STRATEGY, "routine_id": data["routine"]["id"], "reset_transient_navigation": True}
    structural_request = None
    # Try an adjacent same-level deck on a supported rectangular floor edge.
    # The actual validator rejects overlapping floors/blocked circulation.
    for zone in data["world"]["zones"]:
        for axis, sign in [(0, -1), (2, 1), (2, -1), (0, 1)]:
            extension = copy.deepcopy(zone)
            extension.update(id="revision_observation_deck", label="A new observation deck")
            extent_index = 0 if axis == 0 else 1
            width = 4
            extension["center"][axis] += sign * (zone["size"][extent_index] + width) / 2
            extension["size"][extent_index] = width
            deck_position = list(extension["center"])
            deck_position[0] += 0.8
            deck_station = copy.deepcopy(station)
            deck_station.update(id="revision_deck_inspection", label="Inspect the new observation deck", object_id="revision_deck_lamp", approach=list(extension["center"]), interaction=list(extension["center"]), facing=90)
            if "level_id" in extension:
                deck_station["level_id"] = extension["level_id"]
            deck_ops = [{"op": "add_zone", "entity": extension}, {"op": "add_object", "entity": {"id": "revision_deck_lamp", "asset_id": "revision_lamp_asset", "position": deck_position, "rotation_y": 0, "scale": [1, 1, 1]}}, {"op": "add_station", "entity": deck_station}]
            attempt = candidate(deck_ops, "acceptance_deck", migration)
            try:
                revisions.plan_revision(working, attempt)
                structural_request = attempt
                break
            except revisions.RevisionError as issue:
                rejected.append(str(issue))
        if structural_request:
            break
    if structural_request is None:
        raise revisions.RevisionError("no connected deck fixture passed validation: " + "\n".join(rejected))
    structural = revisions.apply_revision(working, structural_request)
    check_state()
    snapshot("structural", structural)
    result["checks"]["connected_zone_explicit_migration"] = "PASS"
    state["project_progress"]["synthetic_journal"] = 23
    state["state_revision"] = 2
    author.write_json(state_path, state)
    rollback = revisions.rollback_revision(working, structural["transaction_id"])
    check_state()
    if author.content_hash(working / "godot/content") != result["snapshots"]["addition"]["content_hash"]:
        raise AssertionError("rollback did not restore prior known-good structure")
    result["checks"]["rollback_preserves_newer_progress"] = "PASS"
    result["rollback_receipt"] = rollback

    def fault(stage):
        if stage == "after_install":
            raise OSError("acceptance injected activation failure")
    failure_candidate = candidate(structural_request["operations"], "acceptance_failure", migration)
    before_failure = author.content_hash(working / "godot/content")
    try:
        revisions.apply_revision(working, failure_candidate, fault_hook=fault)
        raise AssertionError("activation fault was not triggered")
    except OSError as issue:
        if "acceptance injected" not in str(issue):
            raise
    check_state()
    if author.content_hash(working / "godot/content") != before_failure:
        raise AssertionError("activation failure lost known-good structure")
    result["checks"]["activation_failure_recovers_known_good"] = "PASS"
    if author.content_hash(source / "godot/content") != source_hash:
        raise AssertionError("source repository was modified")
    result["checks"]["source_repository_unchanged"] = "PASS"
    result["bounded_fixture_candidates_rejected"] = rejected
    result["status"] = "PASS"
    author.write_json(output / "revision-acceptance.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--world-id", required=True)
    parser.add_argument("--source-package-hash")
    args = parser.parse_args()
    try:
        report = run_acceptance(args.source, args.output, args.world_id, source_package_hash=args.source_package_hash)
        print(json.dumps({"status": report["status"], "world_id": report["world_id"], "report": str(args.output / "revision-acceptance.json"), "checks": report["checks"]}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, AssertionError) as issue:
        print("FAIL: " + str(issue), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
