"""Exercise cloud job isolation and failure receipts without an external service."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cloud_worker as worker
import setup_cloud_godot as bootstrap
from build import run as checked_run


class CloudWorkerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="domes-cloud-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.source = self.directory / "source"
        (self.source / "godot/content/worlds").mkdir(parents=True)
        (self.source / "godot/content/worlds/cedar_atelier.json").write_text('{"character_path":"original"}', encoding="utf-8")
        (self.source / "godot/project.godot").write_text("fixture source", encoding="utf-8")
        (self.source / "docs").mkdir()
        (self.source / "cloud").mkdir()
        for name in ["GODOT_LICENSE.txt", "GODOT_COPYRIGHT.txt", "THIRD_PARTY_NOTICES.md"]:
            (self.source / "docs" / name).write_text("fixture legal notice", encoding="utf-8")
        (self.source / "LICENSE").write_text("fixture license", encoding="utf-8")
        (self.source / "cloud/vercel.json").write_text("{}", encoding="utf-8")
        self.interview = self.directory / "interview.json"
        self.interview.write_text('{"fixture":"approved interview"}', encoding="utf-8")
        self.audit = {"schema_version": 1, "ok": True, "characters": [{"character_id": "fixture_dot", "ok": True}], "engine_version": "4.5.1.stable.official.fixture"}
        self.package_validation = {"ok": True, "character_id": "fixture_dot"}
        self.missing_web_file = None
        self.engine_version = "4.5.1.stable.official.fixture\n"
        self.generated_test_output = "FACTORY CHARACTER TESTS: 59 passed, 0 failed\n"
        self.factory = types.ModuleType("character_factory")
        self.factory.derive_spec = lambda interview, references: {"schema_version": 1, "id": "fixture_dot"}
        self.factory.generate_package = self.generate
        self.factory.validate_package = lambda package: copy.deepcopy(self.package_validation)
        self.factory.install_package = self.install
        self.addCleanup(mock.patch.stopall)
        mock.patch.dict(sys.modules, {"character_factory": self.factory}).start()
        mock.patch.object(worker, "ROOT", self.source).start()
        mock.patch.object(worker, "find_godot", return_value=Path(sys.executable)).start()
        self.run_mock = mock.patch.object(worker, "run", side_effect=self.engine).start()
        self.original_source = self.snapshot(self.source)

    @staticmethod
    def snapshot(root):
        return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def generate(self, spec, destination):
        destination.mkdir()
        (destination / "manifest.json").write_text(json.dumps(spec), encoding="utf-8")
        return {"id": "fixture_dot"}

    def install(self, package, source, stage, world_id):
        self.assertEqual(self.source, source)
        self.assertNotEqual(source, stage)
        shutil.copytree(source, stage)
        (stage / "godot/content/worlds" / (world_id + ".json")).write_text('{"character_path":"generated"}', encoding="utf-8")
        return {"character_id": "fixture_dot", "character_path": "res://content/characters/fixture_dot.json", "world_id": world_id, "stage": str(stage)}

    def engine(self, command, label, root, logs, **kwargs):
        (logs / (label + ".log")).write_text("fixture: " + label, encoding="utf-8")
        if "--version" in command:
            return self.engine_version
        self.assertEqual(self.source, root)
        self.assertIn("--path", command)
        self.assertNotEqual(str(self.source / "godot"), command[command.index("--path") + 1])
        if "res://tests/test_factory_character.gd" in command:
            return self.generated_test_output
        if "--output" in command:
            Path(command[command.index("--output") + 1]).write_text(json.dumps(self.audit), encoding="utf-8")
            return "CHARACTER AUDIT: 1 characters, PASS\n" if self.audit.get("ok") else "CHARACTER AUDIT: 1 characters, FAIL\n"
        if "--export-release" in command:
            web = Path(command[-1]).parent
            for name in ["index.html", "index.js", "index.wasm", "index.pck"]:
                if name != self.missing_web_file:
                    (web / name).write_bytes(b"fixture export")
        return ""

    def execute(self, name="job", web=False):
        return worker.execute(self.interview, self.directory, self.directory / name, export_web=web)

    def receipt(self, name="job"):
        return json.loads((self.directory / name / "job.json").read_text(encoding="utf-8"))

    def assert_failed(self, name="job"):
        self.assertEqual("failed", self.receipt(name)["status"])
        self.assertEqual("not_deployed", self.receipt(name)["deployment"]["status"])
        self.assertEqual(self.original_source, self.snapshot(self.source))

    def test_success_builds_only_isolated_stage_and_does_not_claim_deployment(self):
        result = self.execute()
        self.assertEqual("succeeded", result["status"])
        self.assertEqual("complete", result["phase"])
        self.assertEqual({"status": "not_deployed", "url": None}, result["deployment"])
        self.assertEqual(self.original_source, self.snapshot(self.source))
        staged = self.directory / "job/stage/godot/content/worlds/cedar_atelier.json"
        self.assertEqual("generated", json.loads(staged.read_text())["character_path"])

    def test_negative_engine_audit_cannot_succeed(self):
        self.audit["ok"] = False
        self.audit["characters"][0]["ok"] = False
        with self.assertRaises(ValueError):
            self.execute()
        self.assert_failed()

    def test_package_validation_failure_stops_before_engine(self):
        self.package_validation["ok"] = False
        with self.assertRaisesRegex(ValueError, "package"):
            self.execute()
        self.assert_failed()
        self.run_mock.assert_not_called()

    def test_generated_motion_test_failure_is_not_success(self):
        self.generated_test_output = "FACTORY CHARACTER TESTS: 58 passed, 1 failed\n"
        with self.assertRaises(ValueError):
            self.execute()
        self.assert_failed()

    def test_generated_motion_test_missing_summary_is_not_success(self):
        self.generated_test_output = "Engine exited before running the test.\n"
        with self.assertRaises(ValueError):
            self.execute()
        self.assert_failed()

    def test_empty_engine_audit_cannot_succeed(self):
        self.audit["characters"] = []
        with self.assertRaises(ValueError):
            self.execute()
        self.assert_failed()

    def test_engine_audit_must_include_generated_character(self):
        self.audit["characters"][0]["character_id"] = "unrelated_existing_resident"
        with self.assertRaises(ValueError):
            self.execute()
        self.assert_failed()

    def test_engine_version_is_pinned(self):
        self.engine_version = "4.6.3.stable.official.fixture\n"
        with self.assertRaises(ValueError):
            self.execute()
        self.assert_failed()

    def test_malformed_interview_has_failed_job_receipt(self):
        self.interview.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.execute()
        self.assert_failed()

    def test_engine_parse_error_with_zero_exit_fails_closed(self):
        def error_run(command, label, root, logs, **kwargs):
            if "--editor" in command:
                return checked_run([sys.executable, "-c", "print('SCRIPT ERROR: controlled fixture')"], label, logs.parent, logs)
            return self.engine(command, label, root, logs, **kwargs)
        self.run_mock.side_effect = error_run
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            self.execute()
        self.assert_failed()
        self.assertTrue(any("SCRIPT ERROR:" in p.read_text() for p in (self.directory / "job/logs").glob("*.log")))

    def test_existing_job_directory_is_not_reused_or_changed(self):
        self.execute()
        before = self.snapshot(self.directory / "job")
        with self.assertRaises(FileExistsError):
            self.execute()
        self.assertEqual(before, self.snapshot(self.directory / "job"))

    def test_retry_uses_new_outputs_and_preserves_failed_receipt(self):
        self.run_mock.side_effect = ValueError("controlled engine failure")
        with self.assertRaises(ValueError):
            self.execute("failed")
        before = self.snapshot(self.directory / "failed")
        self.run_mock.side_effect = self.engine
        self.assertEqual("succeeded", self.execute("retry")["status"])
        self.assertEqual(before, self.snapshot(self.directory / "failed"))
        self.assertEqual(self.original_source, self.snapshot(self.source))

    def test_incomplete_web_export_is_not_success(self):
        self.missing_web_file = "index.pck"
        with self.assertRaisesRegex(ValueError, "index.pck"):
            self.execute(web=True)
        self.assert_failed()

    def test_web_export_receipt_covers_output_hashes_and_not_reference_image(self):
        (self.directory / "private-reference.png").write_bytes(b"private fixture")
        result = self.execute(web=True)
        web = self.directory / "job/web"
        self.assertEqual("succeeded", result["status"])
        for name in ["index.html", "index.js", "index.wasm", "index.pck", "LICENSE", "docs/GODOT_LICENSE.txt"]:
            self.assertEqual(hashlib.sha256((web / name).read_bytes()).hexdigest(), result["web_sha256"][name])
        self.assertFalse((web / "private-reference.png").exists())
        self.assertFalse((web / "character-package").exists())
        self.assertFalse((web / "spec.json").exists())
        self.assertEqual(self.original_source, self.snapshot(self.source))


class CloudBootstrapTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="domes-bootstrap-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.editor_name = f"Godot_v{bootstrap.VERSION}_linux.x86_64"
        self.archives = {
            self.editor_name + ".zip": self.archive({self.editor_name: b"fixture executable", "../../escaped": b"never extract"}),
            f"Godot_v{bootstrap.VERSION}_export_templates.tpz": self.archive({"templates/web_nothreads_release.zip": b"release", "templates/web_nothreads_debug.zip": b"debug", "templates/version.txt": b"4.5.1.stable", "../../escaped": b"never extract"}),
        }

    @staticmethod
    def archive(files):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            for name, body in files.items():
                archive.writestr(name, body)
        return output.getvalue()

    def invoke(self, mismatch=False):
        sums = "\n".join(("0" * 128 if mismatch else hashlib.sha512(body).hexdigest()) + "  " + name for name, body in self.archives.items())
        def download(url, destination):
            self.assertTrue(url.startswith(bootstrap.BASE))
            Path(destination).write_bytes(self.archives[url.rsplit("/", 1)[-1]])
        with contextlib.chdir(self.root), mock.patch.object(bootstrap.platform, "system", return_value="Linux"), mock.patch.object(bootstrap.platform, "machine", return_value="x86_64"), mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root / "data")}), mock.patch.object(bootstrap.urllib.request, "urlopen", return_value=io.BytesIO(sums.encode())), mock.patch.object(bootstrap.urllib.request, "urlretrieve", side_effect=download), contextlib.redirect_stdout(io.StringIO()):
            bootstrap.main()

    def test_only_expected_pinned_archive_members_are_installed(self):
        self.invoke()
        self.assertEqual(b"fixture executable", (self.root / ".tools/cloud-godot" / self.editor_name).read_bytes())
        self.assertEqual(b"release", (self.root / "data/godot/export_templates/4.5.1.stable/web_nothreads_release.zip").read_bytes())
        self.assertFalse(any(p.name == "escaped" for p in self.root.rglob("*")))

    def test_checksum_mismatch_stops_before_installing_executable(self):
        with self.assertRaisesRegex(ValueError, "SHA512 mismatch"):
            self.invoke(mismatch=True)
        self.assertFalse((self.root / ".tools/cloud-godot" / self.editor_name).exists())

    def test_bootstrap_refuses_a_visitor_windows_environment(self):
        with mock.patch.object(bootstrap.platform, "system", return_value="Windows"), mock.patch.object(bootstrap.urllib.request, "urlopen") as network:
            with self.assertRaises(SystemExit):
                bootstrap.main()
            network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
