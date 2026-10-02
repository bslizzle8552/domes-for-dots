"""Replay the complete shipped fictional design through the public authoring API."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import world_author as author


class CreationPilotTests(unittest.TestCase):
    def test_create_expand_recover_a_complete_authored_world(self):
        folder = ROOT / "examples/authoring/lantern_archive"
        create = author.read_json(folder / "create.proposal.json")
        expand = author.read_json(folder / "telescope.proposal.json")
        # Construct a pre-pilot project in a temporary directory; the user's
        # checkout and any native/browser saves are never modified by this test.
        authored_paths = {ROOT / entry["path"] for request in [create, expand] for entry in request["files"]}
        with tempfile.TemporaryDirectory(prefix="domes-creation-pilot-") as temporary:
            sandbox = Path(temporary)
            def omit(directory, names):
                return [name for name in names if name == ".godot" or Path(directory) / name in authored_paths]
            shutil.copytree(ROOT / "godot", sandbox / "godot", ignore=omit)
            shutil.copytree(ROOT / "schemas", sandbox / "schemas")
            catalog_path = sandbox / "godot/content/catalog.json"
            catalog = author.read_json(catalog_path)
            catalog["worlds"] = [entry for entry in catalog["worlds"] if entry["id"] != create["world_id"]]
            author.write_json(catalog_path, catalog)
            request = author.prepare_request(sandbox, create)
            self.assertEqual("ready", author.plan(sandbox, request)["status"])
            created = author.apply_request(sandbox, request)
            self.assertEqual("committed", created["status"])
            initial_hash = author.content_hash(sandbox / "godot/content")
            initial_routine = (sandbox / "godot/content/routines/lantern_archive.json").read_bytes()
            brief_path = sandbox / "godot/content/briefs/lantern_archive.json"
            initial_locks = author.read_json(brief_path)["owner_locked"]
            request = author.prepare_request(sandbox, expand)
            report = author.plan(sandbox, request)
            self.assertTrue({"add_asset", "add_object", "add_station"}.issubset(report["operations"]))
            expanded = author.apply_request(sandbox, request)
            self.assertEqual("committed", expanded["status"])
            world = author.read_json(sandbox / "godot/content/worlds/lantern_archive.json")
            self.assertTrue(any(station["id"] == "observe" for station in world["stations"]))
            self.assertEqual(initial_routine, (sandbox / "godot/content/routines/lantern_archive.json").read_bytes())
            brief = author.read_json(brief_path)
            self.assertEqual(initial_locks, brief["owner_locked"])
            self.assertEqual([create["id"], expand["id"]], [entry["id"] for entry in brief["expansion_history"]])
            self.assertEqual([], author.ContentValidator(sandbox).validate())
            author.recover_transaction(sandbox, expanded["transaction_id"])
            self.assertEqual(initial_hash, author.content_hash(sandbox / "godot/content"))


if __name__ == "__main__":
    unittest.main()
