"""Real content/geometry validation for guarded narrow world revisions."""
import copy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from tools import world_author as author
from tools import world_revisions as revisions
from tools.world_revision_guards import enforce_revision_guards


ROOT = Path(__file__).resolve().parents[1]


class WorldRevisionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="domes-revision-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(ROOT / "schemas", self.root / "schemas")
        shutil.copytree(ROOT / "godot", self.root / "godot", ignore=shutil.ignore_patterns(".godot"))
        self.world_path = self.root / "godot/content/worlds/cedar_atelier.json"
        # Synthetic owner edit: a lamp is manually moved before the Dot reads
        # the base. The owner pins its meaning and placement in immutable locks.
        assets_path = self.root / "godot/content/assets/cedar_atelier.json"
        assets = author.read_json(assets_path)
        lamp = copy.deepcopy(next(asset for asset in assets["assets"] if asset["id"] == "studio_rug"))
        lamp.update(id="owner_lamp_asset", display_name="Owner's reading lamp", footprint=[0.25, 0.25])
        lamp["parts"] = [{"shape": "box", "position": [0, 0.6, 0], "size": [0.08, 1.2, 0.08], "rotation": [0, 0, 0], "color": "#ddd5aa", "emission": 0}]
        lamp["collision"]["enabled"] = False
        assets["assets"].append(lamp)
        author.write_json(assets_path, assets)
        world = self.world()
        self.owner_lamp = {"id": "owner_lamp", "asset_id": "owner_lamp_asset", "position": [-2, 0, 3.5], "rotation_y": 17, "scale": [1, 1, 1]}
        world["objects"].append(copy.deepcopy(self.owner_lamp))
        author.write_json(self.world_path, world)
        brief_path = self.root / "godot/content/briefs/cedar_atelier.json"
        brief = author.read_json(brief_path)
        brief["owner_locked"]["entity_protection"] = [{"kind": "object", "id": "owner_lamp", "fields": ["*"], "chosen_by": "human", "reason": "Owner moved and pinned the reading lamp."}]
        author.write_json(brief_path, brief)
        self.save = self.root / "runtime-state.json"
        self.save.write_bytes(b'{"routine_epoch":12345,"preferences":{"volume":0.4},"project_progress":{"journal":71},"state_revision":8}')
        self.assertEqual([], author.ContentValidator(self.root).validate())

    def world(self):
        return author.read_json(self.world_path)

    def bundle(self):
        return author.bundle(author.ContentValidator(self.root), "cedar_atelier")

    def move(self):
        return {"op": "move_object", "id": "woven_rug", "position": [0.5, 0, 0], "rotation_y": 20}

    def candidate(self, operations=None, identity="furniture_refresh", **kwargs):
        return revisions.prepare_revision(self.root, "cedar_atelier", operations or [self.move()], "Make room for a new shelf while preserving the owner's lamp.", identity, **kwargs)

    def migration(self):
        return {"strategy": revisions.MIGRATION_STRATEGY, "routine_id": self.bundle()["routine"]["id"], "reset_transient_navigation": True}

    def addition(self):
        return [
            {"op": "add_object", "entity": {"id": "new_journal_shelf", "asset_id": "cedar_bookshelf", "position": [6, 0, 3], "rotation_y": 0, "scale": [0.3, 0.3, 0.3]}},
            {"op": "add_station", "entity": {"id": "inspect_journals", "label": "Inspect collected journals", "object_id": "new_journal_shelf", "activity_tags": ["inspect"], "approach": [5.5, 0, 2], "interaction": [5.5, 0, 2], "facing": 180, "animation": "interact", "fallback_animation": "interact", "behavior": "", "metadata": {}}},
        ]

    def test_furniture_edit_preserves_owner_move_routes_and_runtime_progress(self):
        candidate = self.candidate(source_package_hash="a" * 64)
        before_hash = author.content_hash(self.root / "godot/content")
        save_bytes = self.save.read_bytes()
        plan = revisions.plan_revision(self.root, candidate)
        self.assertEqual("ready", plan["status"])
        self.assertEqual(before_hash, author.content_hash(self.root / "godot/content"))
        report = revisions.apply_revision(self.root, candidate)
        self.assertEqual("committed", report["status"])
        self.assertEqual(1, report["structure_revision"])
        self.assertEqual(self.owner_lamp, next(obj for obj in self.world()["objects"] if obj["id"] == "owner_lamp"))
        self.assertEqual(save_bytes, self.save.read_bytes())
        self.assertEqual([], author.ContentValidator(self.root).validate())
        self.assertEqual("a" * 64, self.world()["metadata"]["revision_state"]["source_package_hash"])

    def test_add_meaningful_object_and_station_increments_revision_with_rollback(self):
        first = revisions.apply_revision(self.root, self.candidate())
        candidate = self.candidate(self.addition(), "journal_addition")
        report = revisions.apply_revision(self.root, candidate)
        self.assertEqual(2, report["structure_revision"])
        self.assertIn("station:inspect_journals", report["affected_entities"])
        self.assertEqual([], author.ContentValidator(self.root).validate())
        recovered = revisions.rollback_revision(self.root, report["transaction_id"])
        self.assertEqual(1, recovered["active_structure_revision"])
        self.assertEqual(first["candidate_content_hash"], author.content_hash(self.root / "godot/content"))

    def test_structural_zone_requires_explicit_identity_preserving_migration(self):
        operations = [{"op": "add_zone", "entity": {"id": "garden_deck", "label": "A connected garden deck", "center": [11, 0, 0.5], "size": [4, 7], "color": "#abc59b"}}]
        with self.assertRaisesRegex(revisions.RevisionError, "explicit state migration"):
            self.candidate(operations)
        before = author.content_hash(self.root / "godot/content")
        candidate = self.candidate(operations, "garden_deck_addition", state_migration=self.migration())
        self.assertEqual("ready", revisions.plan_revision(self.root, candidate)["status"])
        self.assertEqual(before, author.content_hash(self.root / "godot/content"))
        report = revisions.apply_revision(self.root, candidate)
        self.assertEqual(self.migration(), report["state_migration"])
        self.assertEqual([], author.ContentValidator(self.root).validate())
        self.assertEqual("garden_deck", self.world()["zones"][-1]["id"])
        revisions.rollback_revision(self.root, report["transaction_id"])
        self.assertEqual(before, author.content_hash(self.root / "godot/content"))

    def test_rollback_preserves_progress_written_after_structure_activation(self):
        report = revisions.apply_revision(self.root, self.candidate())
        progress = b'{"routine_epoch":12345,"project_progress":{"journal":99},"state_revision":15}'
        self.save.write_bytes(progress)
        self.assertEqual("recovered", revisions.rollback_revision(self.root, report["transaction_id"])["status"])
        self.assertEqual(progress, self.save.read_bytes())

    def test_stale_base_cannot_overwrite_newer_owner_or_dot_edit(self):
        old = self.candidate(self.addition(), "old_shelf_plan")
        revisions.apply_revision(self.root, self.candidate())
        current = author.content_hash(self.root / "godot/content")
        with self.assertRaisesRegex(revisions.RevisionError, "stale_revision"):
            revisions.apply_revision(self.root, old)
        self.assertEqual(current, author.content_hash(self.root / "godot/content"))

    def test_activation_failure_recovers_known_good_bytes(self):
        before = author.content_hash(self.root / "godot/content")
        state = self.save.read_bytes()
        def fault(stage):
            if stage == "after_install":
                raise OSError("injected activation failure")
        with self.assertRaisesRegex(OSError, "activation failure"):
            revisions.apply_revision(self.root, self.candidate(), fault_hook=fault)
        self.assertEqual(before, author.content_hash(self.root / "godot/content"))
        self.assertEqual(state, self.save.read_bytes())
        journals = list((self.root / "artifacts/authoring").glob("*/journal.json"))
        self.assertEqual("recovered", author.read_json(journals[0])["status"])

    def test_stale_after_validation_does_not_replace_concurrent_owner_edit(self):
        original = author.prepare_candidate
        def changed_after_validation(root, request, stage):
            report = original(root, request, stage)
            world = self.world()
            world["title"] = "Owner changed the title while validating"
            author.write_json(self.world_path, world)
            return report
        candidate = self.candidate()
        with mock.patch.object(author, "prepare_candidate", side_effect=changed_after_validation):
            with self.assertRaisesRegex(revisions.RevisionError, "source changed during validation"):
                revisions.apply_revision(self.root, candidate)
        self.assertEqual("Owner changed the title while validating", self.world()["title"])

    def test_rollback_refuses_to_erase_newer_content(self):
        report = revisions.apply_revision(self.root, self.candidate())
        revisions.apply_revision(self.root, self.candidate(self.addition(), "newer_addition"))
        current = author.content_hash(self.root / "godot/content")
        with self.assertRaisesRegex(revisions.RevisionError, "recovery_conflict"):
            revisions.rollback_revision(self.root, report["transaction_id"])
        self.assertEqual(current, author.content_hash(self.root / "godot/content"))

    def test_protected_move_fails_in_narrow_and_legacy_whole_document_paths(self):
        operation = {"op": "move_object", "id": "owner_lamp", "position": [-1, 0, 3.5], "rotation_y": 17}
        candidate = self.candidate([operation])
        with self.assertRaisesRegex(revisions.RevisionError, "protected object owner_lamp"):
            revisions.plan_revision(self.root, candidate)
        world = self.world()
        next(obj for obj in world["objects"] if obj["id"] == "owner_lamp")["scale"] = [0.01, 0.01, 0.01]
        request = author.prepare_request(self.root, {"schema_version": 1, "id": "legacy_bypass", "world_id": "cedar_atelier", "intent": "expand", "description": "Attempt an indirect bypass", "files": [{"path": "godot/content/worlds/cedar_atelier.json", "document": world}]})
        with self.assertRaisesRegex(revisions.RevisionError, "protected object owner_lamp"):
            author.plan(self.root, request)

    def test_indirect_asset_change_cannot_hide_pinned_object(self):
        request, _ = revisions._request(self.root, self.candidate())
        assets = author.read_json(self.root / "godot/content/assets/cedar_atelier.json")
        next(asset for asset in assets["assets"] if asset["id"] == "owner_lamp_asset")["parts"][0]["color"] = "#000000"
        request["files"].append({"path": "godot/content/assets/cedar_atelier.json", "document": assets})
        with self.assertRaisesRegex(revisions.RevisionError, "asset cannot be changed indirectly"):
            author.plan(self.root, request)

    def test_zone_transform_cannot_remove_pinned_object_support(self):
        before = self.bundle()
        after = copy.deepcopy(before)
        after["world"]["zones"][0]["center"][0] -= 100
        with self.assertRaisesRegex(ValueError, "support cannot be removed"):
            enforce_revision_guards(before, after)
        after = copy.deepcopy(before)
        after["world"]["zones"][0]["size"][0] += 4
        enforce_revision_guards(before, after)

    def test_field_protection_permits_unrelated_fields_and_rejects_position(self):
        before = self.bundle()
        before["brief"]["owner_locked"]["entity_protection"][0]["fields"] = ["position"]
        after = copy.deepcopy(before)
        lamp = next(obj for obj in after["world"]["objects"] if obj["id"] == "owner_lamp")
        lamp["rotation_y"] = 25
        enforce_revision_guards(before, after)
        lamp["position"][0] += 1
        with self.assertRaisesRegex(ValueError, "fields cannot change: position"):
            enforce_revision_guards(before, after)

    def test_object_move_transforms_its_station_anchors(self):
        candidate = self.candidate([{"op": "move_object", "id": "craft_bench", "position": [-2.5, 0, -3.5], "rotation_y": 0}])
        report = revisions.apply_revision(self.root, candidate)
        station = next(station for station in self.world()["stations"] if station["id"] == "craft")
        self.assertEqual([-2.5, 0, -2], station["approach"])
        self.assertIn("station:craft", report["affected_entities"])

    def test_object_resize_preserves_local_station_anchor_relationship(self):
        candidate = self.candidate([{"op": "modify_object", "id": "craft_bench", "changes": {"scale": [0.9, 1, 0.9]}}])
        report = revisions.apply_revision(self.root, candidate)
        station = next(station for station in self.world()["stations"] if station["id"] == "craft")
        self.assertEqual([-3, 0, -2.15], station["approach"])
        self.assertIn("station:craft", report["affected_entities"])

    def test_invalid_station_route_leaves_old_world_active(self):
        operations = self.addition()
        operations[1]["entity"]["approach"] = [999, 0, 999]
        candidate = self.candidate(operations)
        before = author.content_hash(self.root / "godot/content")
        with self.assertRaisesRegex(revisions.RevisionError, "unreachable"):
            revisions.apply_revision(self.root, candidate)
        self.assertEqual(before, author.content_hash(self.root / "godot/content"))

    def test_data_lane_rejects_whole_world_code_and_fake_approval(self):
        for operation in [{"op": "replace_world", "world": self.world()}, {"op": "execute_script", "script": "x"}]:
            with self.subTest(operation=operation["op"]), self.assertRaisesRegex(revisions.RevisionError, "unsupported operation"):
                self.candidate([operation])
        candidate = self.candidate()
        candidate["approved"] = True
        with self.assertRaisesRegex(revisions.RevisionError, "exactly"):
            revisions.apply_revision(self.root, candidate)

    def test_asset_addition_cannot_insert_executable_scene(self):
        asset = copy.deepcopy(self.bundle()["assets"]["studio_rug"])
        asset.update(id="unreviewed_asset", scene_path="res://scripts/evil.tscn")
        with self.assertRaisesRegex(revisions.RevisionError, "no scene path"):
            self.candidate([{"op": "add_asset", "manifest_path": "res://content/assets/cedar_atelier.json", "entity": asset}])

    def test_transition_changes_are_structural_policy_operations(self):
        before = self.bundle()
        after = copy.deepcopy(before)
        after["world"]["transitions"] = [{"id": "a_ramp"}]
        after["world"]["levels"] = [{"id": "upper"}]
        self.assertEqual({"add_transition", "add_level"}, author.operation_diff(before, after))

    def test_duplicate_entity_and_nonfinite_coordinates_are_rejected(self):
        with self.assertRaisesRegex(revisions.RevisionError, "already exists"):
            self.candidate([{"op": "add_object", "entity": copy.deepcopy(self.owner_lamp)}])
        operation = self.move()
        operation["position"][0] = float("nan")
        with self.assertRaisesRegex(revisions.RevisionError, "finite JSON"):
            self.candidate([operation])

    def test_proposal_only_policy_does_not_acquire_authority(self):
        path = self.root / "godot/content/briefs/cedar_atelier.json"
        brief = author.read_json(path)
        policy = copy.deepcopy(author.DEFAULT_POLICY)
        policy["autonomy"] = "proposal_only"
        brief["owner_locked"]["authoring_policy"] = policy
        author.write_json(path, brief)
        candidate = self.candidate()
        self.assertEqual("owner_review_required", revisions.plan_revision(self.root, candidate)["status"])
        with self.assertRaisesRegex(revisions.RevisionError, "cannot approve or apply"):
            revisions.apply_revision(self.root, candidate)

    def test_revision_bookkeeping_does_not_require_extra_decoration_authority(self):
        path = self.root / "godot/content/briefs/cedar_atelier.json"
        brief = author.read_json(path)
        policy = copy.deepcopy(author.DEFAULT_POLICY)
        policy["allowed_operations"] = ["move_object"]
        brief["owner_locked"]["authoring_policy"] = policy
        author.write_json(path, brief)
        self.assertEqual(["move_object"], revisions.plan_revision(self.root, self.candidate())["operations"])

    def test_generated_seed_revision_is_honored_and_common_metadata_updated(self):
        world = self.world()
        world["metadata"]["structure_revision"] = 1
        author.write_json(self.world_path, world)
        candidate = self.candidate()
        self.assertEqual(1, candidate["base_revision"])
        report = revisions.apply_revision(self.root, candidate)
        self.assertEqual(2, report["structure_revision"])
        self.assertEqual(2, self.world()["metadata"]["structure_revision"])

    def test_empty_disconnected_or_overlapping_zone_is_not_a_valid_expansion(self):
        for center in [[30, 0, 0], [0, 0, 0]]:
            operations = [{"op": "add_zone", "entity": {"id": "bad_zone", "label": "Invalid new zone", "center": center, "size": [4, 4], "color": "#ffffff"}}]
            candidate = self.candidate(operations, state_migration=self.migration())
            with self.subTest(center=center), self.assertRaisesRegex(revisions.RevisionError, "unreachable|overlaps existing support"):
                revisions.plan_revision(self.root, candidate)


if __name__ == "__main__":
    unittest.main()
