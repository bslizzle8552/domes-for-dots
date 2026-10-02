"""Exercise release failure boundaries using isolated temporary fixtures."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build
import check_release
import package_release


class ReleaseToolsTests(unittest.TestCase):
    def test_extracted_source_build_hashes_do_not_require_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "godot/.godot/imported").mkdir(parents=True)
            (root / "godot/project.godot").write_text("fixture")
            (root / "godot/.godot/imported/cache.bin").write_bytes(b"generated")
            (root / "godot/import.log").write_text("generated")
            with patch.object(build, "git", side_effect=AssertionError("must not call Git")), patch.object(build, "tracked_files", side_effect=AssertionError("must not call Git")):
                hashes = build.runtime_hashes(root)
                metadata = build.source_metadata(root)
            self.assertEqual({"godot/project.godot":build.sha256(root / "godot/project.godot")}, hashes)
            self.assertEqual({"source_commit":"source-archive","source_dirty":None}, metadata)

    def test_exit_zero_with_engine_error_is_still_a_build_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            logs = root / "logs"
            logs.mkdir()
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, "engine error log=True"):
                build.run([sys.executable, "-c", "print('SCRIPT ERROR: synthetic fixture')"], "fixture", root, logs)
            self.assertIn("SCRIPT ERROR:", (logs / "fixture.log").read_text())

    def test_nonzero_engine_exit_is_build_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            logs = root / "logs"
            logs.mkdir()
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, "exit 7"):
                build.run([sys.executable, "-c", "raise SystemExit(7)"], "fixture", root, logs)

    def test_cleanup_cannot_escape_dist(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            precious = root / "source"
            precious.mkdir()
            (precious / "keep").write_text("keep")
            with self.assertRaises(ValueError):
                build.safe_remove_tree(precious, root)
            self.assertTrue((precious / "keep").is_file())

    def test_recognizable_secret_is_redacted_in_diagnostic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            token = "ghp" + "_" + "x" * 36
            (root / "fixture.txt").write_text(token)
            issues = check_release.inspect_file(root, "fixture.txt")
            self.assertTrue(any("GitHub token" in issue.message for issue in issues))
            self.assertNotIn(token, " ".join(str(issue) for issue in issues))

    def test_home_directory_path_rejected_outside_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "fixture.txt").write_text("C:" + "/Users/" + "fixture_owner/private.json")
            self.assertTrue(any("private absolute" in issue.message for issue in check_release.inspect_file(root, "fixture.txt")))

    def test_provenance_exception_does_not_exempt_secrets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "prototype").mkdir()
            (root / "prototype/README.md").write_text("ghp" + "_" + "y" * 36)
            self.assertTrue(any("token" in issue.message for issue in check_release.inspect_file(root, "prototype/README.md")))

    def test_accidental_cache_or_credential_filename_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".env").write_text("EXAMPLE=fixture")
            self.assertTrue(check_release.inspect_file(root, ".env"))
            (root / "dist").mkdir()
            (root / "dist/cache.txt").write_text("fixture")
            self.assertTrue(check_release.inspect_file(root, "dist/cache.txt"))

    @unittest.skipUnless(shutil.which("git"), "Git is only required for release packaging")
    def test_archive_uses_git_tracked_files_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (root / "source.txt").write_text("public fixture")
            (root / "untracked.txt").write_text("not a release source")
            check_release.git(root, "add", "source.txt")
            files = check_release.tracked_files(root)
            self.assertEqual(["source.txt"], files)
            package_release.write_zip(root / "candidate.zip", root, files, "project/")
            with zipfile.ZipFile(root / "candidate.zip") as archive:
                self.assertEqual(["project/source.txt"], archive.namelist())
                self.assertIsNone(archive.testzip())

    def test_final_packaging_rejects_dirty_source(self):
        with patch.object(sys, "argv", ["package_release.py"]), patch.object(package_release, "git", return_value=b" M README.md\n"), contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(1, package_release.main())
        self.assertIn("dirty/staged", output.getvalue())

    def test_allow_dirty_does_not_bypass_hygiene(self):
        issues = [check_release.Issue("fixture", "synthetic hygiene failure")]
        with patch.object(sys, "argv", ["package_release.py", "--allow-dirty"]), patch.object(package_release, "git", return_value=b" M README.md\n"), patch.object(package_release, "scan", return_value=([], issues)), contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(1, package_release.main())
        self.assertIn("hygiene failed", output.getvalue())

    def test_tampered_web_file_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            web = root / "dist/web"
            (web / "docs").mkdir(parents=True)
            files = ["index.html", "index.js", "index.wasm", "index.pck", "LICENSE", "README.txt", "docs/GODOT_LICENSE.txt", "docs/GODOT_COPYRIGHT.txt", "docs/THIRD_PARTY_NOTICES.md"]
            for relative in files:
                (web / relative).write_text("fixture")
            manifest = dict(version=build.VERSION,godot_version="4.5.1.stable.official.fixture",validation="passed",python_tests="passed",character_audit="passed",godot_tests={name: "passed" for name in build.GODOT_TEST_SUITES},runtime_source_sha256={},files={name:build.sha256(web/name) for name in files})
            (web / "build_manifest.json").write_text(json.dumps(manifest))
            (web / "index.js").write_text("changed")
            with patch.object(package_release, "runtime_hashes", return_value={}), self.assertRaisesRegex(ValueError, "integrity mismatch"):
                package_release.verify_web(root)


if __name__ == "__main__":
    unittest.main()
