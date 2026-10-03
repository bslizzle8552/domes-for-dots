"""Shared owner-field guards for every local world-authoring entry point.

This module deliberately imports neither authoring nor compiler code. Protection
records live inside the already immutable owner_locked boundary, not in a
candidate's self-declared approval or provenance.
"""
from __future__ import annotations

import math


KINDS = {"object": "objects", "zone": "zones", "station": "stations", "transition": "transitions"}


def protection_records(bundle: dict) -> list[dict]:
    records = bundle["brief"]["owner_locked"].get("entity_protection", [])
    if not isinstance(records, list) or len(records) > 2000:
        raise ValueError("entity_protection must be a bounded list")
    seen = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != {"kind", "id", "fields", "chosen_by", "reason"}:
            raise ValueError("invalid entity_protection record; require kind, id, fields, chosen_by, reason")
        if not isinstance(record["kind"], str) or record["kind"] not in KINDS or not isinstance(record["id"], str):
            raise ValueError("invalid protected entity kind or identity")
        key = record["kind"], record["id"]
        if key in seen:
            raise ValueError("duplicate protected entity")
        seen.add(key)
        fields = record["fields"]
        if not isinstance(fields, list) or not fields or any(not isinstance(field, str) for field in fields) or len(set(fields)) != len(fields):
            raise ValueError("protected fields must be unique nonempty field names or ['*']")
        entity = next((item for item in bundle["world"].get(KINDS[record["kind"]], []) if item["id"] == record["id"]), None)
        if entity is None or (fields != ["*"] and any(field not in entity for field in fields)):
            raise ValueError("protected entity or field is missing: " + record["id"])
        if not isinstance(record["chosen_by"], str) or record["chosen_by"] not in {"human", "dot", "collaborative", "compiler"} or not isinstance(record["reason"], str) or not 1 <= len(record["reason"]) <= 2000:
            raise ValueError("protected entity requires bounded reason and decision provenance")
    return records


def _support_elevations(world: dict, obj: dict) -> set[float]:
    x, y, z = obj["position"]
    levels = {level["id"]: level["elevation"] for level in world.get("levels", [])}
    result = set()
    for zone in world["zones"]:
        if abs(x - zone["center"][0]) <= zone["size"][0] / 2 and abs(z - zone["center"][2]) <= zone["size"][1] / 2:
            elevation = levels.get(zone.get("level_id"), zone["center"][1])
            if elevation <= y + 0.01:
                result.add(elevation)
    return result


def enforce_revision_guards(before: dict | None, after: dict) -> None:
    """Reject direct and indirect edits to protected fields/entities.

    A pinned object also pins its reviewed asset and station meaning. Its support
    must remain at the same elevation; a harmless floor extension is permitted.
    Partial field locks permit other fields to change but still preserve identity.
    """
    protection_records(after)
    if before is None:
        return
    _validate_added_zones(before, after)
    for record in protection_records(before):
        plural = KINDS[record["kind"]]
        old = next(item for item in before["world"].get(plural, []) if item["id"] == record["id"])
        new = next((item for item in after["world"].get(plural, []) if item["id"] == record["id"]), None)
        label = "protected " + record["kind"] + " " + record["id"]
        if new is None:
            raise ValueError(label + " cannot be removed or renamed")
        fields = record["fields"]
        if fields == ["*"]:
            if old != new:
                raise ValueError(label + " cannot be moved, resized, hidden, or repurposed")
        elif any(old.get(field) != new.get(field) for field in fields):
            raise ValueError(label + " fields cannot change: " + ", ".join(fields))
        if record["kind"] == "object" and fields == ["*"]:
            if before["assets"][old["asset_id"]] != after["assets"].get(new["asset_id"]):
                raise ValueError(label + " asset cannot be changed indirectly")
            old_stations = [station for station in before["world"]["stations"] if station["object_id"] == old["id"]]
            new_stations = [station for station in after["world"]["stations"] if station["object_id"] == new["id"]]
            if old_stations != new_stations:
                raise ValueError(label + " station meaning cannot be changed indirectly")
            old_support = _support_elevations(before["world"], old)
            new_support = _support_elevations(after["world"], new)
            if old_support and not any(math.isclose(max(old_support), elevation, abs_tol=0.001) for elevation in new_support):
                raise ValueError(label + " support cannot be removed or moved indirectly")


def _validate_added_zones(before: dict, after: dict) -> None:
    """An empty addition still needs reachable reserved circulation at its center.

    Existing station-only validation would otherwise accept an isolated unused
    room. Internal navigation probes are never emitted as fake user stations.
    """
    previous = {zone["id"] for zone in before["world"]["zones"]}
    added = [zone for zone in after["world"]["zones"] if zone["id"] not in previous]
    if not added:
        return
    world = after["world"]
    for zone in added:
        for other in world["zones"]:
            if other["id"] == zone["id"] or not math.isclose(zone["center"][1], other["center"][1], abs_tol=0.001):
                continue
            overlap_x = (zone["size"][0] + other["size"][0]) / 2 - abs(zone["center"][0] - other["center"][0])
            overlap_z = (zone["size"][1] + other["size"][1]) / 2 - abs(zone["center"][2] - other["center"][2])
            if overlap_x > 0.001 and overlap_z > 0.001:
                raise ValueError("added zone " + zone["id"] + " overlaps existing support " + other["id"])
    if world.get("levels"):
        import copy
        try:
            from .world_navigation import validate_layered_navigation
        except ImportError:
            from world_navigation import validate_layered_navigation
        probe = copy.deepcopy(world)
        probe["stations"] = [{"id": "zone_probe_" + zone["id"], "level_id": zone["level_id"], "approach": zone["center"], "interaction": zone["center"]} for zone in added]
        errors = validate_layered_navigation(probe, after["assets"], after["character"])
        if errors:
            raise ValueError("added zone requires reachable center circulation: " + "; ".join(errors))
    else:
        try:
            from .validate_content import NavigationCheck
        except ImportError:
            from validate_content import NavigationCheck
        nav = NavigationCheck(world, after["assets"])
        reachable = nav.reachable(world["spawn"])
        for zone in added:
            if not nav.connects(zone["center"], reachable):
                raise ValueError("added zone " + zone["id"] + " center is blocked or unreachable; reserve a connected circulation path")
