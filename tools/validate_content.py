#!/usr/bin/env python3
"""Validate authored content without running, modifying, or simulating a world.

JSON Schema checks shape/types. Semantic checks resolve local resources, validate
cross-file identities, protect brief boundaries, and check planar navigation.
Godot integration tests remain authoritative for runtime movement and animation.
"""
from __future__ import annotations

import argparse
from collections import deque
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:
    raise SystemExit("Install development dependencies: python -m pip install -r requirements-dev.txt")


REPOSITORY = Path(__file__).resolve().parents[1]
SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
PRIVATE_KEYS = {"password", "api_key", "access_token", "refresh_token", "secret", "credentials", "authorization", "private_key"}
KINDS = {"worlds": "world", "assets": "asset", "characters": "character", "routines": "routine", "briefs": "brief"}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON property {key!r}")
        result[key] = value
    return result


def read_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number {value}")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object, parse_constant=reject_constant)


def _check_tree(data: Any, path: str = "$") -> list[str]:
    errors = []
    if isinstance(data, dict):
        for key, value in data.items():
            location = f"{path}.{key}"
            if not SNAKE_CASE.fullmatch(key):
                errors.append(f"{location}: properties must use snake_case")
            if key in PRIVATE_KEYS:
                errors.append(f"{location}: credentials do not belong in exportable content")
            errors.extend(_check_tree(value, location))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            errors.extend(_check_tree(value, f"{path}[{index}]"))
    elif isinstance(data, float) and not math.isfinite(data):
        errors.append(f"{path}: numbers must be finite")
    return errors


def _duplicate_ids(items: list[dict], label: str) -> list[str]:
    seen = set()
    errors = []
    for item in items:
        if item["id"] in seen:
            errors.append(f"{label}: duplicate id {item['id']}")
        seen.add(item["id"])
    return errors


def animation_resolves(character: dict, semantic: str) -> bool:
    seen = set()
    while semantic not in seen:
        if semantic in character["animations"]:
            return True
        seen.add(semantic)
        semantic = character["fallbacks"].get(semantic, "")
        if not semantic:
            return False
    return False


class NavigationCheck:
    """Conservative 2D clearance check for the v1 axis-aligned floor contract.

    This authoring validator does not reproduce the simulation or move an actor.
    A four-neighbor grid establishes connectivity. Disc samples catch floor-edge
    clearance; transformed obstacle bounds include the character radius.
    """
    def __init__(self, world: dict, assets: dict[str, dict]):
        self.cell = world["navigation"]["cell_size"]
        self.radius = world["navigation"]["character_radius"]
        self.zones = []
        self.obstacles = []
        for zone in world["zones"]:
            x, _, z = zone["center"]
            sx, sz = zone["size"]
            self.zones.append((x - sx / 2, x + sx / 2, z - sz / 2, z + sz / 2))
        for placed in world["objects"]:
            asset = assets.get(placed["asset_id"])
            if not asset or not asset["collision"]["enabled"]:
                continue
            x, _, z = placed["position"]
            corners = []
            for sign_x, sign_z in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                px = sign_x * asset["footprint"][0] * asset["scale"][0] / 2
                pz = sign_z * asset["footprint"][1] * asset["scale"][2] / 2
                for angle_degrees, scale_x, scale_z in [(asset["rotation_y"], placed["scale"][0], placed["scale"][2]), (placed["rotation_y"], 1, 1)]:
                    angle = math.radians(-angle_degrees)
                    px, pz = (px * math.cos(angle) - pz * math.sin(angle)) * scale_x, (px * math.sin(angle) + pz * math.cos(angle)) * scale_z
                corners.append((px, pz))
            # Same conservative world-axis bounds as the runtime, including its
            # small margin. Nested nonuniform scale and yaw must not be merged.
            sx = max(abs(point[0]) for point in corners)
            sz = max(abs(point[1]) for point in corners)
            self.obstacles.append((x, z, sx, sz))

    def on_floor(self, x: float, z: float) -> bool:
        return any(x0 - 1e-7 <= x <= x1 + 1e-7 and z0 - 1e-7 <= z <= z1 + 1e-7 for x0, x1, z0, z1 in self.zones)

    def walkable(self, x: float, z: float) -> bool:
        if not self.on_floor(x, z):
            return False
        for n in range(16):
            angle = 2 * math.pi * n / 16
            if not self.on_floor(x + math.cos(angle) * self.radius, z + math.sin(angle) * self.radius):
                return False
        for ox, oz, sx, sz in self.obstacles:
            if abs(x - ox) < sx + self.radius + .04 - 1e-7 and abs(z - oz) < sz + self.radius + .04 - 1e-7:
                return False
        return True

    def reachable(self, spawn: list[float]) -> set[tuple[int, int]]:
        minimum_x = math.floor(min(z[0] for z in self.zones) / self.cell)
        maximum_x = math.ceil(max(z[1] for z in self.zones) / self.cell)
        minimum_z = math.floor(min(z[2] for z in self.zones) / self.cell)
        maximum_z = math.ceil(max(z[3] for z in self.zones) / self.cell)
        if (maximum_x - minimum_x + 1) * (maximum_z - minimum_z + 1) > 250_000:
            raise ValueError("navigation grid exceeds 250000 cells; reduce extent or increase cell_size")
        valid = {(x, z) for x in range(minimum_x, maximum_x + 1) for z in range(minimum_z, maximum_z + 1) if self.walkable(x * self.cell, z * self.cell)}
        start = (round(spawn[0] / self.cell), round(spawn[2] / self.cell))
        if start not in valid or not self.walkable(spawn[0], spawn[2]):
            return set()
        reached = {start}
        queue = deque([start])
        while queue:
            x, z = queue.popleft()
            for neighbor in [(x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)]:
                if neighbor in valid and neighbor not in reached:
                    # Sample edges as well as nodes so thin barriers do not vanish.
                    if all(self.walkable((x + (neighbor[0] - x) * t) * self.cell, (z + (neighbor[1] - z) * t) * self.cell) for t in [.25, .5, .75]):
                        reached.add(neighbor)
                        queue.append(neighbor)
        return reached

    def connects(self, point: list[float], reached: set[tuple[int, int]]) -> bool:
        if not self.walkable(point[0], point[2]):
            return False
        node = (round(point[0] / self.cell), round(point[2] / self.cell))
        if node not in reached:
            return False
        x, z = node[0] * self.cell, node[1] * self.cell
        return all(self.walkable(point[0] + (x - point[0]) * t, point[2] + (z - point[2]) * t) for t in [.25, .5, .75])


class ContentValidator:
    def __init__(self, root: Path = REPOSITORY):
        self.root = root.resolve()
        self.godot = self.root / "godot"
        self.schemas = {path.name.removesuffix(".schema.json"): read_json(path) for path in (self.root / "schemas").glob("*.schema.json")}
        for schema in self.schemas.values():
            Draft202012Validator.check_schema(schema)
        self.documents: dict[Path, dict] = {}

    def validate_document(self, kind: str, data: Any, source: str = "document") -> list[str]:
        if kind not in self.schemas:
            return [f"{source}: unknown schema {kind}"]
        issues = _check_tree(data)
        validator = Draft202012Validator(self.schemas[kind])
        for issue in sorted(validator.iter_errors(data), key=lambda value: str(list(value.path))):
            location = ".".join(str(x) for x in issue.path) or "$"
            issues.append(f"{location}: {issue.message}")
        return [f"{source}: {issue}" for issue in issues]

    def resource_path(self, reference: str) -> Path:
        if not reference.startswith("res://") or "\\" in reference:
            raise ValueError(f"not a project-local resource: {reference}")
        path = (self.godot / reference[6:]).resolve()
        if not path.is_relative_to(self.godot.resolve()):
            raise ValueError(f"resource escapes Godot project: {reference}")
        if not path.is_file():
            raise ValueError(f"missing resource: {reference}")
        return path

    def _load(self, reference: str, kind: str) -> dict:
        path = self.resource_path(reference)
        data = read_json(path)
        errors = self.validate_document(kind, data, reference)
        if errors:
            raise ValueError("; ".join(errors))
        self.documents[path] = data
        return data

    def validate_world_bundle(self, world: dict, assets: dict[str, dict], character: dict, routine: dict, brief: dict) -> list[str]:
        errors = []
        for label in ["zones", "objects", "stations"]:
            errors.extend(_duplicate_ids(world[label], label))
        errors.extend(_duplicate_ids(routine["steps"], "routine steps"))
        errors.extend(_duplicate_ids(routine["projects"], "projects"))
        errors.extend(_duplicate_ids(brief["expansion_history"], "expansion_history"))
        if brief["world_id"] != world["id"]:
            errors.append("brief world_id does not match world id")
        if brief["dot_name"] != character["display_name"]:
            errors.append("brief dot_name does not match character display_name")
        if "authoring_policy" in brief["owner_locked"]:
            policy = brief["owner_locked"]["authoring_policy"]
            errors.extend(self.validate_document("owner-policy", policy, "owner_locked.authoring_policy"))
            if isinstance(policy, dict) and isinstance(policy.get("world_bounds"), dict):
                limits = policy["world_bounds"]
                if all(isinstance(limits.get(key), (int, float)) for key in ["min_x", "max_x", "min_z", "max_z"]):
                    if limits["min_x"] >= limits["max_x"] or limits["min_z"] >= limits["max_z"]:
                        errors.append("authoring_policy world_bounds require increasing minima/maxima")
        if not math.isclose(sum(step["duration_seconds"] for step in routine["steps"]), routine["cycle_seconds"], rel_tol=0, abs_tol=1e-7):
            errors.append("routine step durations must sum to cycle_seconds")
        if character["navigation"]["radius"] > world["navigation"]["character_radius"] + 1e-7:
            errors.append("world navigation clearance is smaller than character navigation radius")
        physical_radius = character["collision"]["radius"]
        if physical_radius > world["navigation"]["character_radius"] + 1e-7:
            errors.append("world navigation clearance is smaller than character collision radius")
        if character["collision"]["height"] < 2 * character["collision"]["radius"]:
            errors.append("character capsule height must be at least twice its radius")
        for asset in assets.values():
            if asset["collision"]["enabled"]:
                collision = asset["collision"]
                for footprint_index, axis in [(0, 0), (1, 2)]:
                    extent = abs(collision["offset"][axis]) + collision["size"][axis] / 2
                    if extent > asset["footprint"][footprint_index] / 2 + 1e-7:
                        errors.append(f"asset {asset['id']} footprint does not contain its collision box")
                        break
        for semantic in character["fallbacks"]:
            if not animation_resolves(character, semantic):
                errors.append(f"character fallback {semantic} has a cycle or unresolved target")
        objects = {item["id"]: item for item in world["objects"]}
        for placed in world["objects"]:
            if placed["asset_id"] not in assets:
                errors.append(f"object {placed['id']} references unknown asset {placed['asset_id']}")
        station_tags = set()
        for station in world["stations"]:
            if station["object_id"] not in objects:
                errors.append(f"station {station['id']} references unknown object {station['object_id']}")
            station_tags.update(station["activity_tags"])
            for semantic in [station["animation"], station["fallback_animation"]]:
                if not animation_resolves(character, semantic):
                    errors.append(f"station {station['id']} animation {semantic} cannot resolve through character contract")
        step_tags = set()
        stations_by_id = {station["id"]: station for station in world["stations"]}
        for step in routine["steps"]:
            step_tags.add(step["activity_tag"])
            if step["activity_tag"] not in station_tags:
                errors.append(f"routine step {step['id']} has no station for activity {step['activity_tag']}")
            if not animation_resolves(character, step["animation"]):
                errors.append(f"routine step {step['id']} has unsupported animation {step['animation']}")
            if "station_id" in step:
                station = stations_by_id.get(step["station_id"])
                if station is None:
                    errors.append(f"routine step {step['id']} references unknown station_id {step['station_id']}")
                elif step["activity_tag"] not in station["activity_tags"]:
                    errors.append(f"routine step {step['id']} station_id does not support its activity_tag")
        for project in routine["projects"]:
            if project["activity_tag"] not in step_tags:
                errors.append(f"project {project['id']} activity is absent from routine")
            if project["visual_object_id"] not in objects:
                errors.append(f"project {project['id']} references unknown visual_object_id")
        if errors:
            return errors
        if world.get("levels"):
            from world_navigation import validate_layered_navigation
            return validate_layered_navigation(world, assets, character)
        for zone in world["zones"]:
            if abs(zone["center"][1]) > 1e-7:
                errors.append(f"zone {zone['id']} must lie on y=0 in v1")
        navigation = NavigationCheck(world, assets)
        try:
            reached = navigation.reachable(world["spawn"])
        except ValueError as issue:
            return errors + [str(issue)]
        if not reached:
            errors.append("spawn is blocked, outside floor, or has no navigable grid cell")
        if abs(world["spawn"][1]) > 1e-7:
            errors.append("spawn must lie on y=0 in v1")
        for station in world["stations"]:
            for anchor_name in ["approach", "interaction"]:
                point = station[anchor_name]
                if abs(point[1]) > 1e-7:
                    errors.append(f"station {station['id']} {anchor_name} must lie on y=0 in v1")
                if not navigation.connects(point, reached):
                    errors.append(f"station {station['id']} {anchor_name} is blocked or unreachable with character clearance")
        return errors

    def validate(self) -> list[str]:
        errors = []
        catalog = None
        # Validate even unreferenced authoring files, so a broken extension does
        # not hide simply because it has not been added to the catalog yet.
        for path in sorted((self.godot / "content").rglob("*.json")):
            kind = KINDS.get(path.parent.name, path.stem if path.stem in {"catalog", "connections"} else "")
            label = str(path.relative_to(self.root))
            try:
                data = read_json(path)
                issues = self.validate_document(kind, data, label)
                errors.extend(issues)
                if not issues:
                    self.documents[path.resolve()] = data
                    if kind == "catalog":
                        catalog = data
            except (OSError, ValueError) as issue:
                errors.append(f"{label}: {issue}")
        if catalog is None:
            return errors + ["A valid godot/content/catalog.json is required"]
        errors.extend(_duplicate_ids(catalog["worlds"], "catalog worlds"))
        for entry in catalog["worlds"]:
            try:
                world = self._load(entry["path"], "world")
                if entry["id"] != world["id"] or entry["title"] != world["title"]:
                    errors.append(f"catalog entry {entry['id']} does not match world id/title")
                character = self._load(world["character_path"], "character")
                routine = self._load(world["routine_path"], "routine")
                brief = self._load(world["brief_path"], "brief")
                self.resource_path(character["scene_path"])
                if Path(character["scene_path"]).suffix.lower() not in {".tscn", ".scn", ".glb", ".gltf"}:
                    errors.append(f"character {character['id']}: scene_path must reference a Godot scene or GLTF/GLB model")
                assets = {}
                manifests = []
                for reference in world["asset_manifest_paths"]:
                    manifest = self._load(reference, "asset")
                    manifests.append(manifest)
                    for asset in manifest["assets"]:
                        if asset["id"] in assets:
                            errors.append(f"world {world['id']}: duplicate asset id {asset['id']}")
                        assets[asset["id"]] = asset
                        if asset["scene_path"]:
                            self.resource_path(asset["scene_path"])
                            if Path(asset["scene_path"]).suffix.lower() not in {".tscn", ".scn", ".glb", ".gltf"}:
                                errors.append(f"asset {asset['id']}: scene_path must reference a Godot scene or GLTF/GLB model")
                        elif not asset["parts"]:
                            errors.append(f"asset {asset['id']}: needs scene_path or nonempty parts")
                errors.extend(_duplicate_ids(manifests, "asset manifests"))
                errors.extend(f"world {world['id']}: {error}" for error in self.validate_world_bundle(world, assets, character, routine, brief))
            except (OSError, ValueError) as issue:
                errors.append(f"catalog {entry['id']}: {issue}")
        for path in sorted((self.root / "examples").glob("*.json")):
            kind = "activity" if path.name.startswith("mock_") else "state" if "state" in path.name else ""
            if kind:
                try:
                    errors.extend(self.validate_document(kind, read_json(path), str(path.relative_to(self.root))))
                except (OSError, ValueError) as issue:
                    errors.append(f"{path.name}: {issue}")
        return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPOSITORY, help="repository root (defaults to this script's parent)")
    args = parser.parse_args()
    try:
        validator = ContentValidator(args.root)
        errors = validator.validate()
    except (OSError, ValueError) as issue:
        print(f"FAIL: {issue}", file=sys.stderr)
        return 1
    if errors:
        print(f"FAIL: {len(errors)} content issue(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    catalog = read_json(args.root / "godot/content/catalog.json")
    print(f"PASS: {len(catalog['worlds'])} worlds; schema, resource, identity, routine, character and navigation checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
