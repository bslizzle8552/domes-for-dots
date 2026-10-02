"""Isolated authoring transactions: constraints, stale edits and real rollback."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from tools import world_author as author


ROOT = Path(__file__).resolve().parents[1]


class AuthoringTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="domes-author-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "schemas", self.root / "schemas")
        shutil.copytree(ROOT / "godot", self.root / "godot", ignore=shutil.ignore_patterns(".godot"))

    def load(self, relative):
        return author.read_json(self.root / relative)

    def request(self):
        world = self.load("godot/content/worlds/cedar_atelier.json")
        world["objects"].append({"id": "new_rug", "asset_id": "studio_rug", "position": [2, 0, 1], "rotation_y": 0, "scale": [0.2, 1, 0.2]})
        return author.prepare_request(self.root, {
            "schema_version": 1, "id": "a_small_addition", "world_id": "cedar_atelier", "intent": "expand",
            "description": "A small reversible addition chosen by the Dot.",
            "files": [{"path": "godot/content/worlds/cedar_atelier.json", "document": world}],
        })

    def policy(self, **overrides):
        brief = self.load("godot/content/briefs/cedar_atelier.json")
        policy = copy.deepcopy(author.DEFAULT_POLICY)
        policy.update(overrides)
        brief["owner_locked"]["authoring_policy"] = policy
        author.write_json(self.root / "godot/content/briefs/cedar_atelier.json", brief)
        return policy

    def test_plan_does_not_change_source_and_apply_records_history_without_saves(self):
        request = self.request()
        before = author.content_hash(self.root / "godot/content")
        # A local save sentinel anywhere outside authored content stays intact.
        save = self.root / "sentinel.save.json"
        save.write_text('{"routine_epoch":12345,"revision":9}', encoding="utf-8")
        self.assertEqual("ready", author.plan(self.root, request)["status"])
        self.assertEqual(before, author.content_hash(self.root / "godot/content"))
        receipt = author.apply_request(self.root, request)
        self.assertEqual("committed", receipt["status"])
        self.assertEqual(receipt["candidate_content_hash"], author.content_hash(self.root / "godot/content"))
        self.assertEqual("a_small_addition", self.load("godot/content/briefs/cedar_atelier.json")["expansion_history"][-1]["id"])
        self.assertEqual('{"routine_epoch":12345,"revision":9}', save.read_text(encoding="utf-8"))
        self.assertEqual("recovered", author.recover_transaction(self.root, receipt["transaction_id"])["status"])
        self.assertEqual(before, author.content_hash(self.root / "godot/content"))

    def test_stale_request_rejected(self):
        request = self.request()
        path = self.root / "godot/content/worlds/cedar_atelier.json"
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(author.AuthoringError, "stale_request"):
            author.apply_request(self.root, request)

    def test_owner_locks_cannot_be_changed_or_faked_with_approval(self):
        request = self.request()
        brief = self.load("godot/content/briefs/cedar_atelier.json")
        brief["owner_locked"]["privacy"] = "changed without owner amendment"
        request["files"].append({"path": "godot/content/briefs/cedar_atelier.json", "document": brief})
        with self.assertRaisesRegex(author.AuthoringError, "owner_locked is immutable"):
            author.plan(self.root, request)
        request["approved"] = True
        with self.assertRaisesRegex(author.AuthoringError, "Additional properties"):
            author.plan(self.root, request)

    def test_existing_history_cannot_be_rewritten(self):
        request = self.request()
        brief = self.load("godot/content/briefs/cedar_atelier.json")
        brief["expansion_history"] = []
        request["files"].append({"path": "godot/content/briefs/cedar_atelier.json", "document": brief})
        with self.assertRaisesRegex(author.AuthoringError, "history is append-only"):
            author.plan(self.root, request)

    def test_navigation_failure_preserves_exact_source(self):
        request = self.request()
        request["files"][0]["document"]["stations"][0]["approach"] = [999, 0, 999]
        before = author.content_hash(self.root / "godot/content")
        with self.assertRaisesRegex(author.AuthoringError, "unreachable"):
            author.apply_request(self.root, request)
        self.assertEqual(before, author.content_hash(self.root / "godot/content"))

    def test_unapproved_destructive_removal_is_rejected(self):
        request = self.request()
        world = request["files"][0]["document"]
        world["objects"] = [item for item in world["objects"] if item["id"] != "woven_rug"]
        with self.assertRaisesRegex(author.AuthoringError, "destructive removal"):
            author.plan(self.root, request)

    def test_preagreed_removal_can_apply_without_per_object_approval(self):
        self.policy(allowed_operations=author.DEFAULT_POLICY["allowed_operations"] + ["remove_object"], destructive_actions="allow")
        request = self.request()
        world = request["files"][0]["document"]
        world["objects"] = [item for item in world["objects"] if item["id"] != "woven_rug"]
        self.assertEqual("committed", author.apply_request(self.root, request)["status"])

    def test_budget_and_tool_limits(self):
        self.policy(max_objects=1, allowed_tools=[])
        with self.assertRaisesRegex(author.AuthoringError, "does not allow world_author"):
            author.plan(self.root, self.request())

    def test_bounds_include_transformed_object_footprint(self):
        self.policy(world_bounds={"min_x": -20, "max_x": 20, "min_z": -20, "max_z": 20})
        request = self.request()
        obj = request["files"][0]["document"]["objects"][-1]
        obj["position"] = [19.9, 0, 0]
        obj["scale"] = [1, 1, 1]
        with self.assertRaisesRegex(author.AuthoringError, "object footprint new_rug"):
            author.plan(self.root, request)

    def test_proposal_only_policy_yields_plan_and_refuses_apply(self):
        self.policy(autonomy="proposal_only")
        request = self.request()
        self.assertEqual("owner_review_required", author.plan(self.root, request)["status"])
        with self.assertRaisesRegex(author.AuthoringError, "cannot approve or apply"):
            author.apply_request(self.root, request)

    def test_same_routine_timing_allows_station_and_label_edits(self):
        request = self.request()
        routine = self.load("godot/content/routines/cedar_atelier.json")
        routine["steps"][0]["label"] = "A Dot-chosen description"
        world = request["files"][0]["document"]
        routine["steps"][0]["station_id"] = next(s["id"] for s in world["stations"] if routine["steps"][0]["activity_tag"] in s["activity_tags"])
        request["files"].append({"path": "godot/content/routines/cedar_atelier.json", "document": routine})
        self.assertIn("edit_routine_presentation", author.plan(self.root, request)["operations"])
        routine["cycle_seconds"] += 1
        routine["steps"][0]["duration_seconds"] += 1
        with self.assertRaisesRegex(author.AuthoringError, "routine timing/project meaning changed"):
            author.plan(self.root, request)

    def test_project_order_is_part_of_save_identity(self):
        request = self.request()
        routine = self.load("godot/content/routines/cedar_atelier.json")
        routine["projects"].reverse()
        self.assertGreaterEqual(len(routine["projects"]), 2)
        request["files"].append({"path": "godot/content/routines/cedar_atelier.json", "document": routine})
        with self.assertRaisesRegex(author.AuthoringError, "routine timing/project meaning changed"):
            author.plan(self.root, request)

    def test_rollback_after_each_swap_boundary(self):
        for boundary in ["after_backup", "after_install"]:
            with self.subTest(boundary=boundary):
                request = self.request()
                before = author.content_hash(self.root / "godot/content")
                def fail(point):
                    if point == boundary:
                        raise RuntimeError("injected filesystem failure")
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    author.apply_request(self.root, request, fault_hook=fail)
                self.assertEqual(before, author.content_hash(self.root / "godot/content"))

    def test_recovery_refuses_to_discard_newer_edits(self):
        receipt = author.apply_request(self.root, self.request())
        path = self.root / "godot/content/worlds/cedar_atelier.json"
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(author.AuthoringError, "recovery_conflict"):
            author.recover_transaction(self.root, receipt["transaction_id"])

    def test_recovery_rejects_damaged_backup(self):
        receipt = author.apply_request(self.root, self.request())
        path = self.root / "artifacts/authoring" / receipt["transaction_id"] / "before/worlds/cedar_atelier.json"
        path.write_bytes(b"broken")
        with self.assertRaisesRegex(author.AuthoringError, "backup is missing or fails"):
            author.recover_transaction(self.root, receipt["transaction_id"])

    def test_recovery_can_resume_after_its_second_rename_fails(self):
        request = self.request()
        receipt = author.apply_request(self.root, request)
        real_replace = author.os.replace
        def fail_restore(source, target):
            if Path(source).name == "before":
                raise OSError("injected restore failure")
            return real_replace(source, target)
        with mock.patch.object(author.os, "replace", side_effect=fail_restore):
            with self.assertRaisesRegex(OSError, "restore failure"):
                author.recover_transaction(self.root, receipt["transaction_id"])
        self.assertFalse((self.root / "godot/content").exists())
        self.assertEqual("recovered", author.recover_transaction(self.root, receipt["transaction_id"])["status"])
        self.assertEqual(request["base_content_hash"], author.content_hash(self.root / "godot/content"))

    def test_report_outputs_cannot_overwrite_or_create_source(self):
        for relative in ["godot/content/worlds/cedar_atelier.json", "godot/content/worlds/not_registered.json", "schemas/new.json", "artifacts/authoring/surprise.json"]:
            with self.subTest(relative=relative), self.assertRaises(author.AuthoringError):
                author.check_output(self.root, self.root / relative)
        report = self.root / "artifacts/my_plan.json"
        author.write_output(self.root, report, {"status": "reviewable"})
        with self.assertRaisesRegex(author.AuthoringError, "already exists"):
            author.write_output(self.root, report, {"status": "overwritten"})

    def test_shared_assets_cannot_be_rewritten_through_another_world(self):
        request = self.request()
        request["files"][0]["document"]["asset_manifest_paths"].append("res://content/assets/tidal_observatory.json")
        asset = self.load("godot/content/assets/tidal_observatory.json")
        asset["assets"][0]["display_name"] = "unexpected rewrite"
        request["files"].append({"path": "godot/content/assets/tidal_observatory.json", "document": asset})
        with self.assertRaisesRegex(author.AuthoringError, "existing/shared document"):
            author.plan(self.root, request)

    @unittest.skipUnless(author.os.name == "nt", "case aliases are a Windows filesystem behavior")
    def test_windows_case_alias_does_not_bypass_shared_document_protection(self):
        world = self.load("godot/content/worlds/tidal_observatory.json")
        world["asset_manifest_paths"].append("res://content/assets/WIND_CHIME.json")
        author.write_json(self.root / "godot/content/worlds/tidal_observatory.json", world)
        self.assertEqual([], author.ContentValidator(self.root).validate())
        request = self.request()
        asset = self.load("godot/content/assets/wind_chime.json")
        asset["assets"][0]["display_name"] = "unexpected shared rewrite"
        request["files"].append({"path": "godot/content/assets/wind_chime.json", "document": asset})
        with self.assertRaisesRegex(author.AuthoringError, "existing/shared document"):
            author.plan(self.root, request)

    @unittest.skipUnless(author.os.name == "nt", "case aliases are a Windows filesystem behavior")
    def test_windows_content_folder_case_alias_still_validates_candidate_bytes(self):
        request = self.request()
        request["files"][0]["document"]["routine_path"] = "res://Content/routines/cedar_atelier.json"
        routine = self.load("godot/content/routines/cedar_atelier.json")
        routine["cycle_seconds"] += 1
        routine["steps"][0]["duration_seconds"] += 1
        request["files"].append({"path": "godot/content/routines/cedar_atelier.json", "document": routine})
        with self.assertRaisesRegex(author.AuthoringError, "routine timing/project meaning changed"):
            author.plan(self.root, request)

    def test_request_paths_and_duplicate_documents_fail_closed(self):
        request = self.request()
        request["files"].append(copy.deepcopy(request["files"][0]))
        with self.assertRaisesRegex(author.AuthoringError, "repeats a document"):
            author.plan(self.root, request)
        request["files"][0]["path"] = "godot/content/worlds/../../../outside.json"
        with self.assertRaises(author.AuthoringError):
            author.plan(self.root, request)

    def test_full_dot_authored_new_world_can_be_created(self):
        world = self.load("godot/content/worlds/cedar_atelier.json")
        world.update(id="a_new_home", title="An independently authored home", brief_path="res://content/briefs/a_new_home.json", routine_path="res://content/routines/a_new_home.json")
        routine = self.load("godot/content/routines/cedar_atelier.json")
        routine["id"] = "a_new_life"
        brief = self.load("godot/content/briefs/cedar_atelier.json")
        brief.update(world_id="a_new_home", expansion_history=[])
        proposal = {"schema_version": 1, "id": "a_new_beginning", "world_id": "a_new_home", "intent": "create", "description": "A full authored fixture, without a built-in world template.", "files": [{"path": "godot/content/worlds/a_new_home.json", "document": world}, {"path": "godot/content/briefs/a_new_home.json", "document": brief}, {"path": "godot/content/routines/a_new_home.json", "document": routine}]}
        request = author.prepare_request(self.root, proposal)
        self.assertEqual("committed", author.apply_request(self.root, request)["status"])
        self.assertEqual([], author.ContentValidator(self.root).validate())
        self.assertIn("a_new_home", [entry["id"] for entry in self.load("godot/content/catalog.json")["worlds"]])
        with self.assertRaisesRegex(author.AuthoringError, "new world identity"):
            author.plan(self.root, author.prepare_request(self.root, proposal))


if __name__ == "__main__":
    unittest.main()
