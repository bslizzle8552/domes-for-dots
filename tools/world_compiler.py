"""Bounded deterministic semantic world compiler using existing Domes contracts.

Open pavilions have explicit support edges (not inaccessible painted rooms).
Interactions are stationary animation templates, never promised hand contact/IK.
"""
from __future__ import annotations
import copy
import hashlib
import math
from character_contract import ROOT, canonical, validate_schema
from validate_content import ContentValidator, NavigationCheck, animation_resolves
from world_intent import ACTIONS, COMPILER, VERSION, character_profile, safe_data

VALIDATOR = "semantic_grid_validator_v1"
RECIPE_ACTIONS = {"workbench": {"inspect", "work", "tinker"}, "reading_desk": {"inspect", "read", "work"},
                  "shelf": {"inspect", "read"}, "planter": {"inspect", "garden"},
                  "telescope": {"inspect", "observe"}, "sculpture": {"inspect"}, "lamp": {"inspect"}}
LIMITATIONS = ["Open pavilion grammar; no arbitrary buildings or enclosed door solver.",
              "Activity poses are simulated; no IK, physical hand contact, seat fit or actual work is claimed.",
              "Owner must_haves and unsupported wishes are retained prose, not automatically proven requirements.",
              "Private is a deployment requirement, not access control implemented by world JSON.",
              "Engine, browser, accessibility and hosting acceptance are separate from static compilation."]


def anchor_to_world(placed, anchor):
    """Godot Y rotation, local anchor scaled then rotated around object origin."""
    x, y, z = [anchor["position"][i]*placed["scale"][i] for i in range(3)]
    angle = math.radians(placed["rotation_y"])
    result = [x*math.cos(angle)+z*math.sin(angle), y, -x*math.sin(angle)+z*math.cos(angle)]
    return {"position": [round(placed["position"][i]+result[i], 6) for i in range(3)],
            "facing": anchor["facing"]+placed["rotation_y"]}


def _part(shape, position, size, color, rotation=None, emission=0):
    return {"shape": shape, "position": position, "size": size, "rotation": rotation or [0, 0, 0],
            "color": color, "emission": emission}


def recipe_asset(recipe, palette, radius):
    """Reviewed original primitive recipes; no executable scene paths are emitted."""
    wood, accent = palette["material"], palette["accent"]
    dims = {"workbench": [2, 1.1, 1], "reading_desk": [1.8, 1.1, 1], "shelf": [1.8, 2, .65],
            "planter": [1.8, 1.3, 1], "telescope": [1.2, 1.9, 1.2], "sculpture": [1.1, 1.6, 1.1], "lamp": [.6, 1.9, .6]}
    sx, sy, sz = dims[recipe]
    parts = []
    if recipe in ("workbench", "reading_desk"):
        parts.append(_part("box", [0, .85, 0], [sx, .18, sz], wood))
        for x in [-sx/2+.12, sx/2-.12]:
            for z in [-sz/2+.12, sz/2-.12]:
                parts.append(_part("box", [x, .4, z], [.15, .8, .15], accent))
        parts.append(_part("box", [0, .985, 0], [.6, .09, .45], palette["secondary"]))
    elif recipe == "shelf":
        for y in [.12, .75, 1.4, 1.95]:
            parts.append(_part("box", [0, y, 0], [sx, .1, sz], wood))
        for x in [-.85, .85]:
            parts.append(_part("box", [x, 1, 0], [.1, 2, sz], accent))
        for x in [-.5, 0, .5]:
            parts.append(_part("box", [x, 1.0, 0], [.25, .4, .45], palette["secondary"]))
    elif recipe == "planter":
        parts.append(_part("box", [0, .3, 0], [sx, .6, sz], wood))
        for x in [-.55, 0, .55]:
            parts.append(_part("cylinder", [x, .75, 0], [.08, .4, .08], accent))
            parts.append(_part("sphere", [x, 1, 0], [.5, .6, .6], palette["secondary"]))
    elif recipe == "telescope":
        parts.extend([_part("cylinder", [0, .5, 0], [.16, 1, .16], wood),
                      _part("cylinder", [0, .08, 0], [1.1, .16, 1.1], wood),
                      _part("cylinder", [0, 1.35, 0], [.48, 1, .48], accent, [65, 0, 0])])
    elif recipe == "lamp":
        parts.extend([_part("cylinder", [0, .08, 0], [.6, .16, .6], wood),
                      _part("cylinder", [0, .85, 0], [.09, 1.7, .09], wood),
                      _part("sphere", [0, 1.65, 0], [.5, .45, .5], accent, emission=.4)])
    else:
        parts.extend([_part("box", [0, .25, 0], [sx, .5, sz], wood),
                      _part("sphere", [0, 1, 0], [.8, 1.1, .8], accent),
                      _part("box", [0, 1.4, 0], [.75, .1, .75], palette["secondary"], [0, 35, 0])])
    approach = round(sz/2+radius+.45, 3)
    return {"id": "wc_"+recipe, "display_name": recipe.replace("_", " ").title(), "category": recipe,
            "tags": [recipe], "scene_path": "", "scale": [1, 1, 1], "rotation_y": 0,
            "collision": {"enabled": True, "size": [sx, sy, sz], "offset": [0, sy/2, 0]}, "footprint": [sx, sz],
            "anchors": {"front_approach": {"position": [0, 0, approach], "facing": 0},
                        "interaction": {"position": [0, 0, approach], "facing": 0}},
            "parts": parts, "animation": "", "behavior": "", "metadata": {"contact": "not_implemented", "anchor_space": "local"},
            "provenance": {"creator": "Domes for Dots semantic compiler", "source": "Original reviewed primitive recipe", "license": "MIT"}}


def _layout(spec):
    size = 8.0
    zones, topology = [], spec["topology"]
    for i, item in enumerate(spec["zones"]):
        center = [i*size, 0, 0]
        if topology == "courtyard":
            center = [[0, 0, 0], [size, 0, 0], [0, 0, size]][i]
        elif topology == "two_level":
            center = [i*(size+8), i*3, 0]
        zones.append({"id": item["id"], "label": item["label"], "center": center, "size": [size, size],
                      "color": spec["palette"]["floor" if i%2 == 0 else "secondary"], "level_id": "upper" if center[1] else "lower"})
    extents = [max(z["center"][axis]+size/2 for z in zones)-min(z["center"][axis]-size/2 for z in zones) for axis in (0, 2)]
    if max(extents) > spec["owner_constraints"]["max_span"]:
        raise ValueError(f"topology spans {max(extents):g}m, exceeding owner max_span {spec['owner_constraints']['max_span']:g}m")
    transitions = []
    levels = [{"id": "lower", "elevation": 0}]
    if topology == "two_level":
        levels.append({"id": "upper", "elevation": 3})
        transitions.append({"id": "observatory_ramp", "kind": "straight_ramp", "source_level": "lower", "destination_level": "upper",
                            "entry": [4, 0, 0], "exit": [12, 3, 0], "width": 3.5, "rise": 3, "run": 8,
                            "headroom": round(spec["character_profile"]["height"]+.5, 3), "bidirectional": True,
                            "interruption": "hold_supported", "safe_fallbacks": [[2.5, 0, 0], [13.5, 3, 0]]})
    return zones, levels, transitions, extents


def validate_candidate(bundle, character):
    validator = ContentValidator(ROOT)
    errors = []
    for key, kind in [("world", "world"), ("assets", "asset"), ("routine", "routine"), ("brief", "brief")]:
        errors.extend(validator.validate_document(kind, bundle[key]))
    if not errors:
        errors.extend(validator.validate_world_bundle(bundle["world"], {a["id"]: a for a in bundle["assets"]["assets"]},
                                                     character, bundle["routine"], bundle["brief"]))
    return [{"code": "functional_constraint", "message": message,
             "repair": "Check named station/object clearance or adjust only the affected zone/object."} for message in errors]


def compile_world(spec, character, *, max_repairs=2):
    validate_schema("world-spec", spec)
    if spec["compiler"] != COMPILER:
        raise ValueError("unregistered world compiler: "+spec["compiler"])
    validate_schema("semantic-grid-world-spec", spec)
    safe_data(spec)
    if not 0 <= max_repairs <= 4:
        raise ValueError("repair budget must be 0..4")
    if spec["character_profile"] != character_profile(character):
        raise ValueError("character profile changed; derive a new specification for this character")
    # Direct WorldSpec callers receive the same reference/budget checks as intent.
    ids = [item["id"] for item in spec["objects"]]
    zone_ids = [z["id"] for z in spec["zones"]]
    if len(ids) != len(set(ids)) or len(zone_ids) != len(set(zone_ids)):
        raise ValueError("duplicate spec IDs")
    expected = {"single_room": (1, 1), "linear": (2, 6), "courtyard": (3, 3), "two_level": (2, 2)}[spec["topology"]]
    if not expected[0] <= len(zone_ids) <= expected[1]:
        raise ValueError("zone count disagrees with topology grammar")
    if len(ids) > spec["owner_constraints"]["max_objects"] or len(zone_ids) > spec["owner_constraints"]["max_zones"]:
        raise ValueError("owner object/zone budget exceeded")
    if spec["topology"] == "two_level" and "single_level_only" in spec["owner_constraints"]["accessibility"]:
        raise ValueError("owner single_level_only veto")
    for item in spec["objects"]:
        if item["zone_id"] not in zone_ids:
            raise ValueError(f"object {item['id']} references unknown zone")
        if item["recipe"] in spec["owner_constraints"]["veto_tags"] or item["action"] in spec["owner_constraints"]["veto_tags"]:
            raise ValueError(f"owner veto blocks {item['id']}")
    zones, levels, transitions, extents = _layout(spec)
    by_zone = {z["id"]: z for z in zones}
    assets = {recipe: recipe_asset(recipe, spec["palette"], spec["character_profile"]["radius"]) for recipe in sorted({o["recipe"] for o in spec["objects"]})}
    objects, stations, repairs, limitations = [], [], [], list(LIMITATIONS)
    slots, usage = [(-2.1, -2.5, 0), (2.1, -2.5, 0), (-2.1, 2.5, 180), (2.1, 2.5, 180)], {}
    for item in spec["objects"]:
        zone = by_zone[item["zone_id"]]
        index = usage.get(zone["id"], 0)
        usage[zone["id"]] = index+1
        if index >= len(slots):
            raise ValueError(f"zone {zone['id']} needs {index+1} object slots; grammar supports four. Add a supported zone or reduce objects.")
        dx, dz, yaw = slots[index]
        position = [zone["center"][0]+dx, zone["center"][1], zone["center"][2]+dz]
        if "position_hint" in item and item["position_hint"] != position:
            # The four reservations are the bounded solver's feasible domain.
            if len(repairs) >= max_repairs:
                raise ValueError(f"repair budget exhausted: {item['id']} position_hint is outside its circulation-safe slot")
            repairs.append({"iteration": len(repairs)+1, "object_id": item["id"], "code": "placement_outside_reserved_slot",
                            "before": item["position_hint"], "after": position, "reason": "Moved only this object into its collision-free slot; reserved central circulation retained."})
        placed = {"id": item["id"], "asset_id": "wc_"+item["recipe"], "position": position, "rotation_y": yaw, "scale": [1, 1, 1]}
        objects.append(placed)
        asset = assets[item["recipe"]]
        anchor = anchor_to_world(placed, asset["anchors"]["front_approach"])
        compatible = item["action"] in RECIPE_ACTIONS[item["recipe"]]
        desired = ACTIONS[item["action"]] if compatible else "idle"
        animation = desired if animation_resolves(character, desired) else "idle"
        if not compatible:
            limitations.append(f"{item['id']}: {item['recipe']} has no {item['action']} template; falls back to inspect/idle.")
        if animation != desired:
            limitations.append(f"{item['id']}: requested {item['action']} falls back to inspect/idle; character lacks {desired}.")
        stations.append({"id": item["id"]+"_station", "label": item["label"], "object_id": item["id"],
                         "level_id": zone["level_id"], "activity_tags": [item["action"]], "approach": anchor["position"],
                         "interaction": anchor["position"], "facing": anchor["facing"], "animation": animation,
                         "fallback_animation": "idle", "behavior": "", "metadata": {"template": item["action"] if compatible else "inspect",
                         "interaction_scope": "navigate_face_and_animate", "contact": "not_implemented", "local_anchor": "front_approach"}})
    wid = spec["world_id"]
    center = [sum(z["center"][i] for z in zones)/len(zones) for i in range(3)]
    world = {"schema_version": 1, "id": wid, "version": "0.1.0", "title": spec["title"], "description": spec["description"],
             "brief_path": f"res://content/briefs/{wid}.json", "character_path": f"res://content/characters/{character['id']}.json",
             "routine_path": f"res://content/routines/{wid}.json", "asset_manifest_paths": [f"res://content/assets/{wid}.json"],
             "environment": {"background": spec["palette"]["background"], "ambient": "#e7e2d7", "light_color": "#fff0d2", "light_energy": 1.1},
             "camera": {"position": [center[0]+18, 25, center[2]+28], "target": center, "size": max(extents)*1.15+3},
             "navigation": {"cell_size": .5, "character_radius": spec["character_profile"]["radius"]},
             "spawn": [0, 0, 0], "zones": zones, "levels": levels, "transitions": transitions, "objects": objects, "stations": stations,
             "metadata": {"compiler": COMPILER, "compiler_version": VERSION, "topology": spec["topology"],
                          "structure_revision": 1, "intent_sha256": spec["intent_sha256"], "simulation_notice": "SIMULATED ROUTINE; animation is not real work.",
                          "object_provenance": [{"id": o["id"], "chosen_by": o["chosen_by"], "reason": o["reason"]} for o in spec["objects"]]}}
    steps = [{"id": s["id"]+"_step", "label": s["label"], "activity_tag": s["activity_tags"][0], "animation": s["animation"],
              "duration_seconds": 20, "station_id": s["id"]} for s in stations]
    routine = {"schema_version": 1, "id": wid+"_routine", "cycle_seconds": 20*len(steps), "steps": steps, "projects": [],
               "metadata": {"simulation_only": True, "progress_policy": "No architecture is created by this routine."}}
    protections = [{"kind": "object", "id": o["id"], "fields": ["*"], "chosen_by": o["chosen_by"], "reason": o["reason"]} for o in spec["objects"] if o["protected"]]
    brief = {"schema_version": 1, "world_id": wid, "dot_name": character["display_name"], "concept": spec["title"],
             "owner_locked": {"constraints": spec["owner_constraints"], "entity_protection": protections, "privacy": "private deployment required"},
             "dot_choice": {"setting": spec["provenance"]["setting"], "mood": spec["provenance"]["mood"], "topology": spec["provenance"]["topology"]},
             "shared_decision": {"decisions": spec["provenance"]["shared_decisions"]},
             "capabilities": {"interactions": "navigate_face_and_animate", "contact": "not_implemented", "real_activity": "unavailable", "limitations": limitations},
             "initial_scope": [z["purpose"] for z in spec["zones"]], "expansion_history": []}
    bundle = {"world": world, "assets": {"schema_version": 1, "id": wid+"_assets", "assets": list(assets.values())}, "routine": routine, "brief": brief}
    violations = validate_candidate(bundle, character)
    if violations:
        raise ValueError("candidate failed functional validation: "+"; ".join(v["message"] for v in violations))
    bundle["receipt"] = {"schema_version": 1, "ok": True, "compiler": COMPILER, "compiler_version": VERSION,
                         "spec_sha256": hashlib.sha256(canonical(spec)).hexdigest(), "repairs": repairs,
                         "checks": ["schema", "references", "body_envelope", "station_actions", "local_anchors", "navigation", "owner_constraints"],
                         "limitations": limitations, "engine_acceptance": "pending", "browser_acceptance": "pending"}
    return bundle


def validate_package_contents(folder, package, report):
    """Strict registered producer validation, separate from the generic envelope."""
    from validate_content import read_json
    from world_intent import intent_to_spec
    safe_data(package["provenance"], "$.provenance")
    for name in package["files"]:
        if not name.endswith(".json"):
            raise ValueError("registered primitive compiler accepts JSON documents only")
    spec = read_json(folder/package["spec_path"])
    intent = read_json(folder/package["intent_path"])
    if package["provenance"].get("intent_sha256") != hashlib.sha256(canonical(intent)).hexdigest():
        raise ValueError("intent provenance hash disagrees with validated intent")
    character = read_json(folder/package["character_manifest"])
    if spec != intent_to_spec(intent, character):
        raise ValueError("world specification does not match its hashed creative intent and character profile")
    if package["world_id"] != spec["world_id"] or package["compiler_version"] != spec["compiler_version"] or package["compiler"] != spec["compiler"]:
        raise ValueError("world package/spec identities disagree")
    if package["requirements"] != spec["character_profile"]:
        raise ValueError("world requirements do not match validated character profile")
    expected = compile_world(spec, character)
    if package["documents"] != {"assets": "assets.json", "routine": "routine.json", "brief": "brief.json", "receipt": "compile.json"}:
        raise ValueError("registered compiler document roles differ")
    for name, document in expected.items():
        path = package["runtime_manifest"] if name == "world" else package["documents"][name]
        if canonical(read_json(folder/path)) != canonical(document):
            raise ValueError("registered compiler output mismatch: "+name+"; stored receipt cannot authorize changed geometry")
    if package["limitations"] != expected["receipt"]["limitations"]:
        raise ValueError("world package limitations disagree with compiler")
    report["checks"].extend(["identity", "strict_spec", "exact_recompilation", "functional_validation"])
