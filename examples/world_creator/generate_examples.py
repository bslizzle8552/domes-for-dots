"""Regenerate the three independent synthetic acceptance packages in a new folder."""
import argparse
import copy
import hashlib
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools"))
from character_contract import canonical, write_json
from character_factory import generate_package
from validate_content import read_json
from world_package import build_package
from world_composer import compose_many

SETTINGS = [
    ("ember_foundry", "Ember", "linear", ["Forge", "Assembly", "Archive"], ["workbench", "workbench", "shelf"], ["tinker", "work", "inspect"], ["#4a4c50", "#80715c", "#ffa154", "#171e25", "#606973"], 1.3),
    ("lumen_observatory", "Lumen", "two_level", ["Quiet archive", "Instrument deck"], ["reading_desk", "telescope"], ["read", "observe"], ["#606d98", "#a9b7bf", "#e5c675", "#151d34", "#3d465f"], 1.5),
    ("verdant_courtyard", "Fern", "courtyard", ["Garden court", "Painting pavilion", "Seed library"], ["planter", "workbench", "shelf"], ["garden", "tinker", "read"], ["#9eac7b", "#c2b89a", "#e8a772", "#293b35", "#85644e"], 1.4),
]


def inputs():
    source = read_json(ROOT/"examples/character_factory/generated-aster/spec.json")
    for wid, name, topology, labels, recipes, actions, colors, height in SETTINGS:
        cid = name.lower()+"_synthetic"
        zones = [{"id": "zone_"+str(i), "label": label, "purpose": label+" supports "+actions[i]} for i, label in enumerate(labels)]
        def choice(value, reason):
            return {"value": value, "chosen_by": "dot", "reason": reason}
        intent = {"schema_version": 1, "world_id": wid, "dot": {"id": cid, "name": name},
                  "owner_constraints": {"privacy": "private", "max_zones": 6, "max_objects": 24, "max_span": 60,
                                        "must_haves": ["No paid generation; preserve the meaningful object."], "veto_tags": [],
                                        "accessibility": ["desktop_keyboard"], "protected_objects": ["keepsake"]},
                  "choices": {"setting": choice(name+"'s "+wid.replace("_", " ").title(), "Independent synthetic Dot choice for this specimen."),
                              "mood": choice({"linear": "Industrial flow from making through assembly to useful records.",
                                              "two_level": "Quiet low archive and elevated open-sky instrument deck.",
                                              "courtyard": "An open garden, outdoor making and seed library surrounding a shared bend."}[topology], "Activities determine the physical plan."),
                              "topology": choice(topology, "Separate chosen activities through a distinct usable spatial relationship."),
                              "palette": dict(zip(["floor", "secondary", "accent", "background", "material"], colors)), "zones": zones,
                              "activities": [{"id": "activity_"+str(i), "label": label+" - "+actions[i], "zone_id": zones[i]["id"],
                                              "recipe": recipes[i], "action": actions[i], "chosen_by": "dot", "reason": "I want a dedicated place to "+actions[i]+"."} for i, label in enumerate(labels)],
                              "meaningful_objects": [{"id": "keepsake", "label": name+" original signal sculpture", "zone_id": "zone_0", "recipe": "sculpture",
                                                      "protected": True, "chosen_by": "dot", "reason": "A stable personal marker that survives later expansions."}]},
                  "shared_decisions": [{"value": "Use supported animation poses and keep the first world private.", "chosen_by": "collaborative",
                                        "reason": "Honest capabilities and owner privacy belong in this synthetic brief."}],
                  "expansion_ideas": ["A connected display room using the same bounded grammar."],
                  "unsupported_wishes": ["Physical hand contact and a general organic character rig are not implemented."]}
        spec = copy.deepcopy(source)
        spec.update(character_id=cid, display_name=name)
        spec["appearance"]["height_m"] = height
        spec["appearance"]["colors"].update(primary=colors[0], secondary=colors[4], accent=colors[2])
        spec["creative_intent"]["self_image"] = "Independent synthetic "+name+" character for "+wid
        spec["decisions"]["human_notes"] = "Independent synthetic fixture; approved original reusable reference card, no private identity."
        spec["input_sha256"] = hashlib.sha256(canonical({"identity": cid, "appearance": spec["appearance"]})).hexdigest()
        yield wid, intent, spec


def generate(output, stage=None):
    output.mkdir(parents=True, exist_ok=True)
    pairs = []
    for wid, intent, spec in inputs():
        write_json(output/(wid+".intent.json"), intent)
        write_json(output/(wid+".character-spec.json"), spec)
        cp, wp = output/(wid+".character"), output/(wid+".world")
        if not cp.exists():
            generate_package(spec, cp)
        if not wp.exists():
            build_package(intent, cp, wp)
        pairs.append((wp, cp))
        print(wid+" package ready", flush=True)
    if stage:
        compose_many(pairs, stage)
        print("STAGE READY "+str(stage), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage", type=Path)
    args = parser.parse_args()
    generate(args.output, args.stage)
