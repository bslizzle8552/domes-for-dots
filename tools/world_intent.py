"""Six-question creative input adapter. Data chooses meaning; trusted code sizes space."""
from __future__ import annotations
import copy
import hashlib
from character_contract import canonical, validate_schema
from validate_content import animation_resolves

COMPILER = "semantic_grid_v1"
VERSION = "1.0.0"
QUESTIONS = [
    "What place would you choose, and how should it feel?",
    "What three things would you actually do there?",
    "Which spaces do those activities need, and how should they connect?",
    "What meaningful object makes the place recognizably yours?",
    "How private, social and outdoors should the place feel?",
    "What may change later, and what must stay protected?",
]
RECIPES = ("workbench", "reading_desk", "shelf", "planter", "telescope", "sculpture", "lamp")
ACTIONS = {"inspect": "idle", "work": "work", "read": "read", "garden": "garden", "observe": "observe", "tinker": "interact"}


def safe_data(value, location="$"):
    """No data-carried code, resource locations, credentials, or URL authority."""
    canonical(value)
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"script", "code", "url", "scene_path", "credentials", "api_key", "secret", "password", "access_token"}:
                raise ValueError(f"{location}.{key}: executable/resource/secret fields are outside the data lane")
            safe_data(item, location+"."+key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            safe_data(item, f"{location}[{index}]")
    elif isinstance(value, str) and ("://" in value or "\\" in value or "../" in value or "<script" in value.lower()):
        raise ValueError(f"{location}: URLs, paths and executable markup are outside the data lane")


def character_profile(character):
    validate_schema("character", character)
    if character["forward_axis"] != "-Z":
        raise ValueError("semantic_grid_v1 currently requires the common -Z forward orientation")
    radius = max(character["collision"]["radius"], character["navigation"]["radius"])
    height = character["collision"]["height"]
    if radius > .7 or height > 2.6 or height < 2*character["collision"]["radius"]:
        raise ValueError("character envelope exceeds bounded compiler fit: radius <=0.7m, height <=2.6m and valid capsule required")
    if not animation_resolves(character, "idle") or not animation_resolves(character, "walk"):
        raise ValueError("character must implement idle and walk through its semantic contract")
    return {"character_id": character["id"], "display_name": character["display_name"], "radius": radius,
            "height": height, "forward_axis": "-Z", "movement": "ground_walk",
            "actions": sorted(action for action in ACTIONS if animation_resolves(character, ACTIONS[action])),
            "contact": "not_declared", "reach": "unknown"}


def intent_to_spec(intent, character):
    validate_schema("world-intent", intent)
    safe_data(intent)
    profile = character_profile(character)
    if intent["dot"]["id"] != profile["character_id"] or intent["dot"]["name"] != profile["display_name"]:
        raise ValueError("intent Dot identity must match the independently validated character package")
    choices, constraints = intent["choices"], intent["owner_constraints"]
    zones = copy.deepcopy(choices["zones"])
    if len({z["id"] for z in zones}) != len(zones):
        raise ValueError("duplicate semantic zone ID")
    count = {"single_room": (1, 1), "linear": (2, 6), "courtyard": (3, 3), "two_level": (2, 2)}[choices["topology"]["value"]]
    if not count[0] <= len(zones) <= count[1]:
        raise ValueError(f"topology {choices['topology']['value']} requires {count[0]}..{count[1]} zones")
    if len(zones) > constraints["max_zones"]:
        raise ValueError("owner max_zones veto blocks selected topology")
    if choices["topology"]["value"] == "two_level" and "single_level_only" in constraints["accessibility"]:
        raise ValueError("owner accessibility veto single_level_only blocks two_level")
    objects = []
    for activity in choices["activities"]:
        objects.append({"id": activity["id"], "zone_id": activity["zone_id"], "recipe": activity["recipe"],
                        "label": activity["label"], "action": activity["action"], "reason": activity["reason"],
                        "chosen_by": activity["chosen_by"], "protected": activity["id"] in constraints["protected_objects"]})
    for item in choices["meaningful_objects"]:
        objects.append(dict(item, action="inspect", protected=item["protected"] or item["id"] in constraints["protected_objects"]))
    if len({o["id"] for o in objects}) != len(objects):
        raise ValueError("duplicate object/activity ID")
    if len(objects) > constraints["max_objects"]:
        raise ValueError("owner max_objects budget exceeded")
    for item in objects:
        if item["zone_id"] not in {z["id"] for z in zones}:
            raise ValueError(f"object {item['id']} references unknown zone {item['zone_id']}")
        if item["recipe"] in constraints["veto_tags"] or item["action"] in constraints["veto_tags"]:
            raise ValueError(f"owner veto blocks {item['id']} recipe/action")
    if set(constraints["protected_objects"]) - {o["id"] for o in objects}:
        raise ValueError("protected_objects must reference concrete stable object IDs")
    # Natural-language wishes are retained, not falsely claimed as solver constraints.
    spec = {"schema_version": 1, "compiler": COMPILER, "compiler_version": VERSION, "world_id": intent["world_id"],
            "intent_sha256": hashlib.sha256(canonical(intent)).hexdigest(), "character_profile": profile,
            "topology": choices["topology"]["value"], "zones": zones, "objects": objects,
            "palette": copy.deepcopy(choices["palette"]), "owner_constraints": copy.deepcopy(constraints),
            "title": choices["setting"]["value"], "description": choices["mood"]["value"],
            "provenance": {"setting": choices["setting"], "mood": choices["mood"], "topology": choices["topology"],
                           "shared_decisions": intent["shared_decisions"], "expansion_ideas": intent["expansion_ideas"],
                           "unsupported_wishes": intent["unsupported_wishes"]}}
    validate_schema("world-spec", spec)
    validate_schema("semantic-grid-world-spec", spec)
    return spec
