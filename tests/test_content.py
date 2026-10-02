"""Authoring contract tests. Runtime behavior is tested in Godot separately."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_content", ROOT / "tools/validate_content.py")
CONTENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTENT)


class ContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = CONTENT.ContentValidator(ROOT)

    def bundle(self, name="cedar_atelier"):
        world = CONTENT.read_json(ROOT / f"godot/content/worlds/{name}.json")
        character = CONTENT.read_json(self.validator.resource_path(world["character_path"]))
        routine = CONTENT.read_json(self.validator.resource_path(world["routine_path"]))
        brief = CONTENT.read_json(self.validator.resource_path(world["brief_path"]))
        assets = {}
        for path in world["asset_manifest_paths"]:
            for asset in CONTENT.read_json(self.validator.resource_path(path))["assets"]:
                assets[asset["id"]] = asset
        return world, assets, character, routine, brief

    def assert_bundle_error(self, bundle, message):
        self.assertTrue(any(message in error for error in self.validator.validate_world_bundle(*bundle)), message)

    def test_all_shipped_content_validates(self):
        self.assertEqual([], self.validator.validate())

    def test_two_different_layouts_and_routines_share_contract(self):
        cedar, *_, cedar_routine, _ = self.bundle()
        orbital, *_, orbital_routine, _ = self.bundle("tidal_observatory")
        self.assertEqual(2, len(cedar["zones"]))
        self.assertEqual(3, len(orbital["zones"]))
        self.assertNotEqual(cedar["character_path"], orbital["character_path"])
        self.assertNotEqual({s["activity_tag"] for s in cedar_routine["steps"]}, {s["activity_tag"] for s in orbital_routine["steps"]})

    def test_world_schema_rejects_unknown_fields(self):
        world, *_ = self.bundle()
        world["surprise"] = True
        self.assertTrue(self.validator.validate_document("world", world))

    def test_schema_rejects_unknown_version(self):
        world, *_ = self.bundle()
        world["schema_version"] = 2
        self.assertTrue(self.validator.validate_document("world", world))

    def test_schema_rejects_malformed_vector_and_zero_scale(self):
        world, *_ = self.bundle()
        world["spawn"] = [0, 0]
        world["objects"][0]["scale"] = [1, 0, 1]
        errors = self.validator.validate_document("world", world)
        self.assertGreaterEqual(len(errors), 2)

    def test_schema_rejects_non_finite_values(self):
        world, *_ = self.bundle()
        world["camera"]["size"] = float("nan")
        self.assertTrue(any("finite" in error for error in self.validator.validate_document("world", world)))

    def test_resource_paths_reject_remote_and_escape(self):
        for path in ["https://example.com/model.glb", "res://../LICENSE", "res://content\\secret.json"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.validator.resource_path(path)

    def test_world_schema_rejects_parent_traversal(self):
        world, *_ = self.bundle()
        world["brief_path"] = "res://../brief.json"
        self.assertTrue(self.validator.validate_document("world", world))

    def test_credentials_and_camel_case_rejected_inside_metadata(self):
        world, *_ = self.bundle()
        world["metadata"]["nested"] = {"access_token": "redacted_fixture", "camelCase": True}
        errors = self.validator.validate_document("world", world)
        self.assertTrue(any("credentials" in error for error in errors))
        self.assertTrue(any("snake_case" in error for error in errors))

    def test_duplicate_json_properties_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text('{"id":"first","id":"second"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                CONTENT.read_json(path)

    def test_duplicate_object_ids_rejected(self):
        bundle = self.bundle()
        bundle[0]["objects"][1]["id"] = bundle[0]["objects"][0]["id"]
        self.assert_bundle_error(bundle, "duplicate id")

    def test_unknown_asset_rejected(self):
        bundle = self.bundle()
        bundle[0]["objects"][0]["asset_id"] = "not_installed"
        self.assert_bundle_error(bundle, "unknown asset")

    def test_unknown_station_object_rejected(self):
        bundle = self.bundle()
        bundle[0]["stations"][0]["object_id"] = "absent_object"
        self.assert_bundle_error(bundle, "unknown object")

    def test_routine_sum_rejected(self):
        bundle = self.bundle()
        bundle[3]["cycle_seconds"] += 1
        self.assert_bundle_error(bundle, "must sum")

    def test_routine_requires_reachable_activity_station(self):
        bundle = self.bundle()
        bundle[3]["steps"][0]["activity_tag"] = "unavailable_hobby"
        self.assert_bundle_error(bundle, "no station")

    def test_projects_reference_existing_visuals_and_routine_tags(self):
        bundle = self.bundle()
        bundle[3]["projects"][0]["visual_object_id"] = "not_here"
        bundle[3]["projects"][0]["activity_tag"] = "not_scheduled"
        self.assert_bundle_error(bundle, "unknown visual_object_id")
        self.assert_bundle_error(bundle, "absent from routine")

    def test_brief_identity_preserved(self):
        bundle = self.bundle()
        bundle[4]["world_id"] = "different_world"
        self.assert_bundle_error(bundle, "brief world_id")

    def test_owner_locked_is_required_and_nonempty(self):
        *_, brief = self.bundle()
        brief["owner_locked"] = {}
        self.assertTrue(self.validator.validate_document("brief", brief))
        del brief["owner_locked"]
        self.assertTrue(self.validator.validate_document("brief", brief))

    def test_owner_locked_expansion_declaration_is_required(self):
        *_, brief = self.bundle()
        brief["expansion_history"][0]["owner_locked_preserved"] = False
        self.assertTrue(self.validator.validate_document("brief", brief))

    def test_fallback_cycles_rejected(self):
        bundle = self.bundle()
        bundle[2]["fallbacks"]["music"] = "custom_pose"
        bundle[2]["fallbacks"]["custom_pose"] = "music"
        self.assert_bundle_error(bundle, "cycle or unresolved")

    def test_missing_semantic_animation_rejected(self):
        bundle = self.bundle()
        bundle[0]["stations"][0]["animation"] = "unmapped_pose"
        self.assert_bundle_error(bundle, "cannot resolve")

    def test_character_swap_needs_no_named_engine_contract(self):
        bundle = self.bundle()
        replacement = copy.deepcopy(bundle[2])
        replacement["id"] = "third_character"
        replacement["appearance"] = {"color": "#aabbcc", "accent": "#ffeedd"}
        self.assertEqual([], self.validator.validate_document("character", replacement))
        self.assertEqual([], self.validator.validate_world_bundle(bundle[0], bundle[1], replacement, bundle[3], bundle[4]))

    def test_oversized_character_rejected(self):
        bundle = self.bundle()
        bundle[2]["collision"]["radius"] = .4
        self.assert_bundle_error(bundle, "character collision")

    def test_visual_scale_does_not_change_explicit_body_dimensions(self):
        bundle = self.bundle()
        bundle[2]["scale"] = [2, 2, 2]
        self.assertEqual([], self.validator.validate_world_bundle(*bundle))

    def test_approach_inside_prop_is_rejected(self):
        bundle = self.bundle()
        bundle[0]["stations"][0]["approach"] = bundle[0]["objects"][0]["position"][:]
        self.assert_bundle_error(bundle, "approach is blocked")

    def test_interaction_inside_inflated_footprint_is_rejected(self):
        bundle = self.bundle()
        # This is beyond the bench mesh but inside character-radius clearance.
        bundle[0]["stations"][0]["interaction"] = [-3, 0, -2.8]
        self.assert_bundle_error(bundle, "interaction is blocked")

    def test_severed_bridge_makes_observation_wing_unreachable(self):
        bundle = self.bundle("tidal_observatory")
        bundle[0]["zones"] = [zone for zone in bundle[0]["zones"] if zone["id"] != "bridge"]
        self.assert_bundle_error(bundle, "station observe approach is blocked or unreachable")

    def test_rotated_obstacle_clearance(self):
        bundle = self.bundle()
        world, assets, *_ = bundle
        # A one-meter-wide bench becomes two meters deep after a quarter turn.
        world["objects"][0]["rotation_y"] = 90
        navigation = CONTENT.NavigationCheck(world, assets)
        self.assertFalse(navigation.walkable(-3, -2.4))
        self.assertTrue(navigation.walkable(-1.8, -3.5))

    def test_footprint_must_cover_actual_collider(self):
        bundle = self.bundle()
        bundle[1]["cedar_workbench"]["collision"]["offset"][0] = .4
        self.assert_bundle_error(bundle, "footprint does not contain its collision box")

    def test_nested_asset_yaw_then_nonuniform_object_scale(self):
        world, assets, *_ = self.bundle()
        assets["cedar_workbench"]["rotation_y"] = 90
        world["objects"][0]["scale"] = [2, 1, .5]
        navigation = CONTENT.NavigationCheck(world, assets)
        self.assertFalse(navigation.walkable(-1.7, -3.5))

    def test_new_station_name_does_not_require_schema_enum_or_code(self):
        bundle = self.bundle()
        station = bundle[0]["stations"][-1]
        self.assertEqual("wind_chime", station["id"])
        self.assertEqual("", station["behavior"])
        self.assertIn("res://content/assets/wind_chime.json", bundle[0]["asset_manifest_paths"])
        station["id"] = "unanticipated_musical_device"
        station["activity_tags"] = ["new_hobby"]
        for step in bundle[3]["steps"]:
            if step["activity_tag"] == "chime":
                step["activity_tag"] = "new_hobby"
        self.assertEqual([], self.validator.validate_document("world", bundle[0]))
        self.assertEqual([], self.validator.validate_world_bundle(*bundle))

    def test_activity_target_and_ttl_shape(self):
        event = CONTENT.read_json(ROOT / "examples/mock_work_start.json")
        self.assertEqual([], self.validator.validate_document("activity", event))
        for invalid in [0, 61, -1]:
            event["ttl_seconds"] = invalid
            self.assertTrue(self.validator.validate_document("activity", event))
        event["ttl_seconds"] = 0
        event["operation"] = "end"
        self.assertEqual([], self.validator.validate_document("activity", event))

    def test_asset_provenance_is_required(self):
        data = CONTENT.read_json(ROOT / "godot/content/assets/wind_chime.json")
        del data["assets"][0]["provenance"]
        self.assertTrue(self.validator.validate_document("asset", data))

    def test_all_original_assets_have_mit_provenance(self):
        for path in (ROOT / "godot/content/assets").glob("*.json"):
            for asset in CONTENT.read_json(path)["assets"]:
                with self.subTest(asset=asset["id"]):
                    self.assertEqual("MIT", asset["provenance"]["license"])
                    self.assertTrue(asset["provenance"]["creator"])
                    self.assertTrue(asset["provenance"]["source"])


if __name__ == "__main__":
    unittest.main()
