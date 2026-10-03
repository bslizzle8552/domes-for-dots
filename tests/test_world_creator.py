"""Functional and adversarial acceptance for the semantic World Creator boundary."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from character_contract import canonical, digest, validate_schema, write_json
from validate_content import ContentValidator, read_json
from world_intent import intent_to_spec
from world_compiler import anchor_to_world, compile_world, validate_candidate
from world_package import validate_package, build_package
from world_composer import compose, compose_many

EXAMPLES = ROOT/"examples/world_creator"


class WorldCreatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intent = read_json(EXAMPLES/"ember_foundry.intent.json")
        cls.character = read_json(EXAMPLES/"ember_foundry.character/character.json")
        cls.spec = intent_to_spec(cls.intent, cls.character)

    def bundle(self):
        return compile_world(self.spec, self.character)

    def test_three_independent_intents_and_characters(self):
        worlds, topology, activity_sets, footprints, characters = [], set(), set(), set(), set()
        for filename in sorted(EXAMPLES.glob("*.intent.json")):
            intent = read_json(filename)
            name = intent["world_id"]
            character = read_json(EXAMPLES/(name+".character")/"character.json")
            bundle = compile_world(intent_to_spec(intent, character), character)
            self.assertEqual([], validate_candidate(bundle, character))
            worlds.append(bundle)
            topology.add(bundle["world"]["metadata"]["topology"])
            activity_sets.add(tuple(sorted(s["animation"] for s in bundle["world"]["stations"])))
            footprints.add(tuple(tuple(z["center"]) for z in bundle["world"]["zones"]))
            characters.add(character["id"])
        self.assertEqual(3, len(worlds))
        self.assertEqual(3, len(topology))
        self.assertEqual(3, len(footprints))
        self.assertEqual(3, len(characters))
        self.assertEqual(3, len(activity_sets))

    def test_deterministic_bytes(self):
        self.assertEqual(canonical(self.bundle()), canonical(self.bundle()))

    def test_local_anchor_rotation_scale_translation(self):
        placed = {"position": [5, 3, -2], "scale": [2, 1, 3], "rotation_y": 90}
        result = anchor_to_world(placed, {"position": [1, 0, 2], "facing": 15})
        self.assertEqual([11, 3, -4], result["position"])
        self.assertEqual(105, result["facing"])

    def test_station_positions_come_from_local_anchors(self):
        bundle = self.bundle()
        objects = {o["id"]: o for o in bundle["world"]["objects"]}
        assets = {a["id"]: a for a in bundle["assets"]["assets"]}
        for station in bundle["world"]["stations"]:
            placed = objects[station["object_id"]]
            anchor = anchor_to_world(placed, assets[placed["asset_id"]]["anchors"]["front_approach"])
            self.assertEqual(anchor["position"], station["approach"])
            self.assertEqual(anchor["facing"], station["facing"])
            self.assertEqual("not_implemented", station["metadata"]["contact"])

    def test_bounded_targeted_repair(self):
        spec = copy.deepcopy(self.spec)
        spec["objects"][0]["position_hint"] = [80, 0, 80]
        result = compile_world(spec, self.character)
        self.assertEqual(1, len(result["receipt"]["repairs"]))
        self.assertEqual("activity_0", result["receipt"]["repairs"][0]["object_id"])
        self.assertEqual(self.bundle()["world"]["objects"], result["world"]["objects"])
        with self.assertRaisesRegex(ValueError, "repair budget exhausted"):
            compile_world(spec, self.character, max_repairs=0)

    def test_unaffected_objects_preserved_by_repair(self):
        original = self.bundle()
        spec = copy.deepcopy(self.spec)
        spec["objects"][1]["position_hint"] = [3, 0, 0]
        result = compile_world(spec, self.character)
        self.assertEqual(original["world"], result["world"])

    def test_owner_veto(self):
        intent = copy.deepcopy(self.intent)
        intent["owner_constraints"]["veto_tags"] = ["workbench"]
        with self.assertRaisesRegex(ValueError, "veto"):
            intent_to_spec(intent, self.character)

    def test_owner_span_budget(self):
        spec = copy.deepcopy(self.spec)
        spec["owner_constraints"]["max_span"] = 10
        with self.assertRaisesRegex(ValueError, "max_span"):
            compile_world(spec, self.character)

    def test_duplicate_ids(self):
        intent = copy.deepcopy(self.intent)
        intent["choices"]["activities"][1]["id"] = "activity_0"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            intent_to_spec(intent, self.character)

    def test_unknown_zone(self):
        intent = copy.deepcopy(self.intent)
        intent["choices"]["activities"][0]["zone_id"] = "absent"
        with self.assertRaisesRegex(ValueError, "unknown zone"):
            intent_to_spec(intent, self.character)

    def test_character_envelope_fit(self):
        character = copy.deepcopy(self.character)
        character["collision"]["height"] = 4
        with self.assertRaisesRegex(ValueError, "envelope"):
            intent_to_spec(self.intent, character)

    def test_changed_character_requires_new_spec(self):
        character = copy.deepcopy(self.character)
        character["navigation"]["radius"] += .01
        with self.assertRaisesRegex(ValueError, "profile changed"):
            compile_world(self.spec, character)

    def test_unknown_action_falls_back_honestly(self):
        character = copy.deepcopy(self.character)
        character["animations"].pop("work", None)
        character["fallbacks"].pop("work", None)
        bundle = compile_world(intent_to_spec(self.intent, character), character)
        station = next(s for s in bundle["world"]["stations"] if s["activity_tags"] == ["work"])
        self.assertEqual("idle", station["animation"])
        self.assertTrue(any("falls back" in item for item in bundle["receipt"]["limitations"]))

    def test_no_fake_sit_or_new_physics(self):
        intent = copy.deepcopy(self.intent)
        intent["choices"]["activities"][0]["action"] = "sit"
        with self.assertRaises(ValueError):
            intent_to_spec(intent, self.character)

    def test_incompatible_object_action_is_explicit_inspection(self):
        intent = copy.deepcopy(self.intent)
        intent["choices"]["activities"][0]["recipe"] = "lamp"
        bundle = compile_world(intent_to_spec(intent, self.character), self.character)
        station = bundle["world"]["stations"][0]
        self.assertEqual("inspect", station["metadata"]["template"])
        self.assertEqual("idle", station["animation"])
        self.assertTrue(any("lamp has no tinker" in line for line in bundle["receipt"]["limitations"]))

    def test_no_code_urls_paths_or_nonfinite_input(self):
        for change in [lambda x:x["choices"].update(script="evil.gd"),
                       lambda x:x["choices"]["setting"].update(value="https://evil.example/x"),
                       lambda x:x["choices"]["setting"].update(value="../escape"),
                       lambda x:x["owner_constraints"].update(max_span=float("nan"))]:
            intent = copy.deepcopy(self.intent)
            change(intent)
            with self.assertRaises(ValueError):
                intent_to_spec(intent, self.character)

    def test_protected_intent_maps_to_existing_owner_lock(self):
        brief = self.bundle()["brief"]
        records = brief["owner_locked"]["entity_protection"]
        self.assertEqual(["keepsake"], [r["id"] for r in records])
        self.assertEqual(["*"], records[0]["fields"])

    def test_blocked_station_rejected(self):
        bundle = self.bundle()
        bundle["world"]["stations"][0]["approach"] = bundle["world"]["objects"][0]["position"]
        self.assertTrue(any("blocked" in item["message"] for item in validate_candidate(bundle, self.character)))

    def multilevel(self):
        intent = read_json(EXAMPLES/"lumen_observatory.intent.json")
        character = read_json(EXAMPLES/"lumen_observatory.character/character.json")
        return compile_world(intent_to_spec(intent, character), character), character

    def test_multilevel_reachability_and_fit(self):
        bundle, character = self.multilevel()
        self.assertEqual([], validate_candidate(bundle, character))
        self.assertEqual(2, len(bundle["world"]["levels"]))
        self.assertTrue(any(s["approach"][1] == 3 for s in bundle["world"]["stations"]))

    def test_disconnected_upper_level_rejected(self):
        bundle, character = self.multilevel()
        bundle["world"]["transitions"] = []
        self.assertTrue(any("unreachable" in e["message"] for e in validate_candidate(bundle, character)))

    def test_ramp_headroom_and_width_rejected(self):
        for field, value in [("headroom", .4), ("width", 1.0), ("run", 4.0)]:
            bundle, character = self.multilevel()
            bundle["world"]["transitions"][0][field] = value
            self.assertTrue(validate_candidate(bundle, character), field)

    def test_ramp_blocked_landing_rejected(self):
        bundle, character = self.multilevel()
        bundle["world"]["objects"][0]["position"] = [3, 0, 0]
        self.assertTrue(any("landing" in e["message"] or "blocked" in e["message"] for e in validate_candidate(bundle, character)))

    def test_disconnected_empty_zone_rejected(self):
        bundle = self.bundle()
        zone = copy.deepcopy(bundle["world"]["zones"][0])
        zone.update(id="disconnected", center=[0, 0, 30])
        bundle["world"]["zones"].append(zone)
        self.assertTrue(any("no reachable circulation" in e["message"] for e in validate_candidate(bundle, self.character)))

    def test_furniture_collision_overlap_rejected(self):
        bundle = self.bundle()
        bundle["world"]["objects"][1]["position"] = bundle["world"]["objects"][0]["position"]
        self.assertTrue(any("overlap" in e["message"] for e in validate_candidate(bundle, self.character)))

    def test_floating_furniture_rejected(self):
        bundle = self.bundle()
        bundle["world"]["objects"][0]["position"][1] = 5
        self.assertTrue(any("outside support" in e["message"] for e in validate_candidate(bundle, self.character)))

    def test_ramp_gap_rejected(self):
        bundle, character = self.multilevel()
        bundle["world"]["zones"][1]["center"][0] += .5
        self.assertTrue(any("endpoint has a gap" in e["message"] for e in validate_candidate(bundle, character)))

    def test_owner_single_level_accessibility_veto(self):
        intent = read_json(EXAMPLES/"lumen_observatory.intent.json")
        character = read_json(EXAMPLES/"lumen_observatory.character/character.json")
        intent["owner_constraints"]["accessibility"] = ["single_level_only"]
        with self.assertRaisesRegex(ValueError, "single_level_only"):
            intent_to_spec(intent, character)

    def test_spec_unknown_compiler_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec["compiler"] = "custom_unknown"
        with self.assertRaisesRegex(ValueError, "unregistered"):
            compile_world(spec, self.character)


class WorldPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)/"world"
        shutil.copytree(EXAMPLES/"ember_foundry.world", self.folder)

    def tearDown(self):
        self.temp.cleanup()

    def mutate(self, file, change, rehash=True):
        data = read_json(self.folder/file)
        change(data)
        write_json(self.folder/file, data)
        if rehash and file != "package.json":
            package = read_json(self.folder/"package.json")
            package["files"][file] = digest(self.folder/file)
            write_json(self.folder/"package.json", package)

    def test_valid_package(self):
        report = validate_package(self.folder)
        self.assertTrue(report["ok"], report)

    def test_fake_receipt_cannot_bypass_rehashed_invalid_geometry(self):
        self.mutate("world.json", lambda x:x["spawn"].__setitem__(0, 80))
        write_json(self.folder/"validation.json", {"ok": True})
        report = validate_package(self.folder)
        self.assertFalse(report["ok"])
        self.assertTrue(any("output mismatch" in e for e in report["errors"]))

    def test_unknown_compiler_fails_closed(self):
        self.mutate("package.json", lambda x:x.update(compiler="unknown"))
        self.assertFalse(validate_package(self.folder)["ok"])

    def test_package_provenance_cannot_carry_secret_or_fake_source_hash(self):
        self.mutate("package.json", lambda x:x["provenance"].update(api_key="fixture-secret"))
        self.assertFalse(validate_package(self.folder)["ok"])
        self.mutate("package.json", lambda x:x["provenance"].pop("api_key"))
        self.mutate("package.json", lambda x:x["provenance"].update(intent_sha256="0"*64))
        self.assertFalse(validate_package(self.folder)["ok"])

    def test_digest_mismatch(self):
        self.mutate("world.json", lambda x:x.update(title="changed"), rehash=False)
        self.assertFalse(validate_package(self.folder)["ok"])

    def test_undeclared_script_rejected(self):
        (self.folder/"evil.gd").write_text("extends Node")
        self.assertFalse(validate_package(self.folder)["ok"])

    def test_declared_executable_rejected(self):
        (self.folder/"evil.gd").write_text("extends Node")
        self.mutate("package.json", lambda x:x["files"].update({"evil.gd": digest(self.folder/"evil.gd")}))
        self.assertFalse(validate_package(self.folder)["ok"])

    def test_path_traversal_rejected(self):
        self.mutate("package.json", lambda x:x["files"].update({"../escape.json": "0"*64}))
        self.assertFalse(validate_package(self.folder)["ok"])

    def test_wrong_character_composition(self):
        with self.assertRaisesRegex(ValueError, "different character"):
            compose(self.folder, EXAMPLES/"lumen_observatory.character", Path(self.temp.name)/"stage")

    def test_composition_is_asset_complete(self):
        stage = Path(self.temp.name)/"stage"
        result = compose(self.folder, EXAMPLES/"ember_foundry.character", stage)
        self.assertTrue(result["ok"])
        self.assertEqual([], ContentValidator(stage).validate())
        world = read_json(stage/"godot/content/worlds/ember_foundry.json")
        character = read_json(stage/"godot"/world["character_path"][6:])
        self.assertTrue((stage/"godot"/character["scene_path"][6:]).is_file())

    def test_collision_ids_rejected(self):
        pair = (self.folder, EXAMPLES/"ember_foundry.character")
        with self.assertRaisesRegex(ValueError, "collide"):
            compose_many([pair, pair], Path(self.temp.name)/"stage")


if __name__ == "__main__":
    unittest.main()
