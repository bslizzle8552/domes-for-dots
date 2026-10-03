"""Private Site packaging boundary; these are not hosted-runtime tests."""
import copy
import gzip
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from tools import world_author as author
from tools import world_site_prepare as siteprep


ROOT = Path(__file__).resolve().parents[1]


class WorldSitePrepareTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="domes-site-boundary-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / "base"
        shutil.copytree(ROOT / "schemas", self.root / "schemas")
        shutil.copytree(ROOT / "godot", self.root / "godot", ignore=shutil.ignore_patterns(".godot"))
        self.site = self.home / "site"
        (self.site / ".openai").mkdir(parents=True)
        (self.site / ".openai/hosting.json").write_text("{}", encoding="utf-8")
        self.web = self.home / "web"
        self.web.mkdir()
        (self.web / "index.wasm").write_bytes(b"\0asm\x01\0\0\0")
        (self.web / "index.pck").write_bytes(b"reviewed-export-fixture-not-a-functional-runtime")
        (self.web / "index.js").write_text('loadPromise = preloader.loadPromise(`${loadPath}.wasm`, size, true);', encoding="utf-8")
        (self.web / "index.html").write_text('<script src="index.js"></script>\nengine.startGame({\n}).then(() => {\n\t\t\tsetStatusMode', encoding="utf-8")

    def prepare(self, roots=None):
        return siteprep.prepare(self.site, self.web, roots or [self.root], "cedar_atelier")

    def load(self, path, root=None):
        return author.read_json((root or self.root) / path)

    def candidate(self):
        target = self.home / "candidate"
        shutil.copytree(self.root, target)
        return target

    def assert_no_generated_output(self):
        self.assertFalse((self.site / "lib/world/registry.json").exists())
        self.assertFalse((self.site / "public/world-data").exists())
        self.assertFalse((self.site / "public/world/index.pck").exists())

    def test_valid_bundle_hashes_and_engine_bytes_roundtrip(self):
        receipt = self.prepare()
        self.assertEqual("cedar_atelier", receipt["world_id"])
        registry = author.read_json(self.site / "lib/world/registry.json")
        record = registry["revisions"]["1"]
        self.assertTrue((self.site / "public" / record["bundle_url"].lstrip("/")).exists())
        self.assertEqual((self.web / "index.wasm").read_bytes(), gzip.decompress((self.site / "public/world/index.wasm.gz").read_bytes()))
        script = (self.site / "public/world/index.js").read_text(encoding="utf-8")
        self.assertIn("v[0]===31 && v[1]===139", script)
        self.assertIn("window.domesHostReady.then", (self.site / "public/world/index.html").read_text(encoding="utf-8"))

    def test_invalid_second_candidate_never_writes_even_valid_first_bundle(self):
        candidate = self.candidate()
        path = candidate / "godot/content/worlds/cedar_atelier.json"
        world = author.read_json(path)
        world["stations"][0]["approach"] = [999, 0, 999]
        world["metadata"]["validation_receipt"] = {"ok": True, "status": "passed"}
        author.write_json(path, world)
        with self.assertRaisesRegex(ValueError, "Revision failed validation"):
            self.prepare([self.root, candidate])
        self.assert_no_generated_output()

    def test_owner_locked_change_is_rejected(self):
        candidate = self.candidate()
        path = candidate / "godot/content/briefs/cedar_atelier.json"
        brief = author.read_json(path)
        brief["owner_locked"]["privacy"] = "Public without owner authorization"
        author.write_json(path, brief)
        with self.assertRaisesRegex(ValueError, "cannot change owner locks"):
            self.prepare([self.root, candidate])
        self.assert_no_generated_output()

    def test_protected_object_cannot_be_moved_by_prepared_full_document(self):
        path = self.root / "godot/content/briefs/cedar_atelier.json"
        brief = author.read_json(path)
        brief["owner_locked"]["entity_protection"] = [{"kind": "object", "id": "woven_rug", "fields": ["*"], "chosen_by": "human", "reason": "Synthetic owner-pinned object."}]
        author.write_json(path, brief)
        candidate = self.candidate()
        path = candidate / "godot/content/worlds/cedar_atelier.json"
        world = author.read_json(path)
        next(obj for obj in world["objects"] if obj["id"] == "woven_rug")["rotation_y"] = 15
        author.write_json(path, world)
        with self.assertRaisesRegex(ValueError, "protected object woven_rug"):
            self.prepare([self.root, candidate])
        self.assert_no_generated_output()

    def test_policy_scope_cannot_be_bypassed_by_valid_full_document(self):
        path = self.root / "godot/content/briefs/cedar_atelier.json"
        brief = author.read_json(path)
        policy = copy.deepcopy(author.DEFAULT_POLICY)
        policy["allowed_operations"] = []
        brief["owner_locked"]["authoring_policy"] = policy
        author.write_json(path, brief)
        candidate = self.candidate()
        path = candidate / "godot/content/worlds/cedar_atelier.json"
        world = author.read_json(path)
        next(obj for obj in world["objects"] if obj["id"] == "woven_rug")["rotation_y"] = 15
        author.write_json(path, world)
        with self.assertRaisesRegex(ValueError, "outside owner policy"):
            self.prepare([self.root, candidate])
        self.assert_no_generated_output()

    def test_script_bearing_asset_is_rejected_even_when_local_scene_exists(self):
        path = self.root / "godot/content/assets/cedar_atelier.json"
        assets = author.read_json(path)
        assets["assets"][0]["scene_path"] = "res://scenes/characters/placeholder.tscn"
        author.write_json(path, assets)
        with self.assertRaisesRegex(ValueError, "bounded primitive recipes"):
            self.prepare()
        self.assert_no_generated_output()

    def test_wasm_link_is_rejected_before_reading_or_writing(self):
        actual = siteprep.is_link
        linked = self.web / "index.wasm"
        with mock.patch.object(siteprep, "is_link", side_effect=lambda path: path == linked or actual(path)):
            with self.assertRaisesRegex(ValueError, "Links and junctions forbidden"):
                self.prepare()
        self.assert_no_generated_output()

    def test_destination_junction_cannot_redirect_generated_files(self):
        actual = siteprep.is_link
        linked = self.site / "public"
        with mock.patch.object(siteprep, "is_link", side_effect=lambda path: path == linked or actual(path)):
            with self.assertRaisesRegex(ValueError, "Links and junctions forbidden"):
                self.prepare()
        self.assert_no_generated_output()

    def test_source_content_link_is_rejected_before_output(self):
        actual = author.is_link
        linked = self.root / "godot/content/worlds/cedar_atelier.json"
        with mock.patch.object(author, "is_link", side_effect=lambda path: path == linked or actual(path)):
            with self.assertRaisesRegex(ValueError, "links or junctions"):
                self.prepare()
        self.assert_no_generated_output()

    def test_unsupported_export_loader_preserves_existing_site_bytes(self):
        (self.site / "public/world").mkdir(parents=True)
        sentinel = self.site / "public/world/index.pck"
        sentinel.write_bytes(b"known-good")
        (self.web / "index.js").write_text("unsupported loader", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unsupported Godot loader"):
            self.prepare()
        self.assertEqual(b"known-good", sentinel.read_bytes())
        self.assertFalse((self.site / "public/world-data").exists())

    def test_old_content_addressed_bundles_are_retained_for_rollback(self):
        directory = self.site / "public/world-data"
        directory.mkdir(parents=True)
        old = directory / "old-known-good.json"
        old.write_bytes(b'{"retained":"previous immutable bundle"}')
        self.prepare()
        self.assertEqual(b'{"retained":"previous immutable bundle"}', old.read_bytes())

    def test_structural_revision_requires_explicit_migration(self):
        candidate = self.candidate()
        path = candidate / "godot/content/worlds/cedar_atelier.json"
        world = author.read_json(path)
        world["zones"].append({"id": "new_deck", "label": "New deck", "center": [11, 0, 0.5], "size": [4, 7], "color": "#bbccaa"})
        author.write_json(path, world)
        with self.assertRaisesRegex(ValueError, "explicit identity-preserving state migration"):
            self.prepare([self.root, candidate])
        self.assert_no_generated_output()

    def test_content_change_after_validation_cannot_gain_a_valid_bundle_receipt(self):
        original = siteprep.ContentValidator.validate
        def change_after_validation(validator):
            errors = original(validator)
            path = self.root / "godot/content/worlds/cedar_atelier.json"
            world = author.read_json(path)
            world["unvalidated_field"] = "changed after schema validation"
            author.write_json(path, world)
            return errors
        with mock.patch.object(siteprep.ContentValidator, "validate", autospec=True, side_effect=change_after_validation):
            with self.assertRaisesRegex(ValueError, "Source content changed during Site preparation"):
                self.prepare()
        self.assert_no_generated_output()


if __name__ == "__main__":
    unittest.main()
