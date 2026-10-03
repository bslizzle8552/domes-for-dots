"""Worker failure receipts and gates; engine behavior is tested by Godot suites."""
import contextlib
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
import world_creator_worker as worker
from character_contract import write_json
from validate_content import read_json


class WorldCreatorWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.ids = ["ember_synthetic", "lumen_synthetic", "fern_synthetic"]
        self.version = "4.5.1.stable.official.fixture"
        self.motion = "FACTORY CHARACTER TESTS: 59 passed, 0 failed"
        self.generated = "GENERATED WORLD TESTS: 60 passed, 0 failed"
        self.missing_web = None
        self.audit_ids = self.ids[:]
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(worker, "find_godot", return_value=Path(sys.executable)).start()
        mock.patch.object(worker, "source_hashes", return_value={"fixture": "same"}).start()
        self.engine = mock.patch.object(worker, "run", side_effect=self.fake_engine).start()

    def fake_engine(self, command, label, root, logs, **kwargs):
        (logs/(label+".log")).write_text("MOCK ORCHESTRATION TEST "+label, encoding="utf-8")
        if "--version" in command:
            return self.version
        if "--output" in command:
            write_json(Path(command[command.index("--output")+1]), {"ok": True, "characters": [{"character_id": cid, "ok": True} for cid in self.audit_ids]})
        if "res://tests/test_factory_character.gd" in command:
            return self.motion
        if "res://tests/test_generated_worlds.gd" in command:
            return self.generated
        if "res://tests/test_multilevel.gd" in command:
            return "MULTILEVEL TESTS: 26 passed, 0 failed"
        if "--export-release" in command:
            for name in ["index.html", "index.js", "index.wasm", "index.pck"]:
                if name != self.missing_web:
                    (Path(command[-1]).parent/name).write_bytes(b"mock export fixture")
        return ""

    def execute(self, name="job", web=False):
        with contextlib.redirect_stdout(io.StringIO()):
            return worker.execute(self.directory/name, export_web=web)

    def failed_receipt(self):
        receipt = read_json(self.directory/"job/job.json")
        self.assertEqual("failed", receipt["status"])
        self.assertEqual("not_deployed", receipt["deployment"]["status"])

    def test_success_preserves_three_independent_packages_and_hashes(self):
        receipt = self.execute(web=True)
        self.assertEqual("succeeded", receipt["status"])
        self.assertEqual(3, len(receipt["package_validation"]))
        self.assertEqual(3, len(receipt["motion_acceptance"]))
        self.assertEqual("not_deployed", receipt["deployment"]["status"])
        self.assertIn("not_run_by_worker", receipt["browser_acceptance"])
        self.assertIn("index.wasm", receipt["web_sha256"])
        self.assertTrue(receipt["source_unchanged"])
        self.assertGreater(receipt["durations_seconds"]["total"], 0)

    def test_missing_character_audit_fails(self):
        self.audit_ids.pop()
        with self.assertRaisesRegex(ValueError, "audit"):
            self.execute()
        self.failed_receipt()

    def test_motion_failure_blocks_export(self):
        self.motion = "FACTORY CHARACTER TESTS: 58 passed, 1 failed"
        with self.assertRaisesRegex(ValueError, "zero-failure"):
            self.execute(web=True)
        self.failed_receipt()
        self.assertFalse((self.directory/"job/web").exists())

    def test_runtime_failure_blocks_export(self):
        self.generated = "GENERATED WORLD TESTS: 58 passed, 1 failed"
        with self.assertRaisesRegex(ValueError, "zero-failure"):
            self.execute(web=True)
        self.failed_receipt()

    def test_wrong_engine_rejected(self):
        self.version = "4.6.stable"
        with self.assertRaisesRegex(ValueError, "pinned Godot"):
            self.execute()
        self.failed_receipt()

    def test_missing_web_asset_fails(self):
        self.missing_web = "index.wasm"
        with self.assertRaisesRegex(ValueError, "missing Web export"):
            self.execute(web=True)
        self.failed_receipt()

    def test_existing_job_cannot_be_overwritten(self):
        (self.directory/"job").mkdir()
        with self.assertRaises(FileExistsError):
            self.execute()
        self.engine.assert_not_called()


if __name__ == "__main__":
    unittest.main()
