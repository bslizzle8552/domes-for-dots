"""Publisher boundary tests; real isolated Git commits, no external publication."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import publish_pages as publisher


class PublishPagesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="domes-pages-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.web = self.root / "cloud/web"
        self.web.mkdir(parents=True)
        (self.web / "index.html").write_bytes(b"<!doctype html>\r\nSynthetic demo\n")
        (self.web / "index.wasm").write_bytes(bytes(range(256)))
        (self.web / "assets").mkdir()
        (self.web / "assets/icon.svg").write_bytes(b"<svg/>\n")
        self.job_path = self.root / "cloud/job.json"
        self.job = {"status": "succeeded", "run_id": "37071425952", "source_commit": "b" * 40, "web_sha256": {path.relative_to(self.web).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in self.web.rglob("*") if path.is_file()}}
        self.write_job()
        self.checkout = self.root / "artifacts/pages-proof"
        self.receipt_path = self.checkout.with_name("pages-proof.publication.json")
        self.site = {"source": {"branch": publisher.BRANCH, "path": "/"}, "build_type": "legacy", "html_url": "https://example.github.io/domes/", "status": "building"}
        patcher = mock.patch.object(publisher, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_job(self):
        self.job_path.write_text(json.dumps(self.job), encoding="utf-8")

    def publish(self, **kwargs):
        return publisher.publish(self.web, self.job_path, "example/domes", self.checkout, public_demo=True, **kwargs)

    def external_mocks(self, *, branch_exists=False, push_fails=False, corrupt_blob=False):
        real_git = publisher._git

        def controlled_git(args, cwd, allowed=(0,)):
            if args[0] == "ls-remote":
                return (0, b"existing") if branch_exists else (2, b"")
            if args[0] == "push":
                self.assertEqual(["push", "--set-upstream", "origin", "HEAD:refs/heads/" + publisher.BRANCH], args)
                self.assertEqual(self.checkout, cwd)
                if push_fails:
                    raise ValueError("mock push failed")
                return 0, b""
            if corrupt_blob and args[0] == "cat-file":
                return 0, b"changed by filter"
            return real_git(args, cwd, allowed)

        return mock.patch.object(publisher, "_git", side_effect=controlled_git)

    def test_verified_cloud_web_commits_exact_bytes_and_submits_separate_receipt(self):
        with mock.patch.object(publisher, "_token", return_value="never-printed"), mock.patch.object(publisher, "_pages", side_effect=[None, self.site]) as pages, self.external_mocks() as git:
            result = self.publish()
        self.assertEqual("submitted", result["status"])
        self.assertTrue(result["branch_pushed"])
        self.assertFalse(result["browser_verified"])
        self.assertEqual(self.site["html_url"], result["html_url"])
        self.assertEqual(self.job["run_id"], result["job_run_id"])
        self.assertEqual(hashlib.sha256(self.job_path.read_bytes()).hexdigest(), result["job_receipt_sha256"])
        self.assertEqual(result, json.loads(self.receipt_path.read_text()))
        self.assertNotIn("never-printed", self.receipt_path.read_text())
        self.assertEqual(mock.call("example/domes", "never-printed", create=True), pages.call_args)
        self.assertEqual(1, sum(call.args[0][0] == "push" for call in git.call_args_list))
        self.assertEqual(self.job["web_sha256"], publisher.verify_web(self.web, self.job_path)[1])
        self.assertFalse((self.checkout / self.receipt_path.name).exists())

    def test_existing_matching_pages_source_is_not_modified(self):
        with mock.patch.object(publisher, "_token", return_value="secret"), mock.patch.object(publisher, "_pages", return_value=self.site) as pages, self.external_mocks():
            self.publish()
        pages.assert_called_once_with("example/domes", "secret")

    def test_public_acknowledgment_required_before_network_or_disk_mutation(self):
        with mock.patch.object(publisher, "_token") as token, self.assertRaisesRegex(ValueError, "public-demo"):
            publisher.publish(self.web, self.job_path, "example/domes", self.checkout)
        token.assert_not_called()
        self.assertFalse(self.checkout.exists())

    def test_failed_job_missing_modified_and_extra_files_are_rejected(self):
        cases = ["job_failed", "missing", "modified", "extra"]
        for case in cases:
            with self.subTest(case=case):
                original = (self.web / "index.wasm").read_bytes()
                if case == "job_failed":
                    self.job["status"] = "failed"
                    self.write_job()
                elif case == "missing":
                    (self.web / "index.wasm").unlink()
                elif case == "modified":
                    (self.web / "index.wasm").write_bytes(b"tampered")
                else:
                    (self.web / "unexpected.txt").write_text("extra")
                with mock.patch.object(publisher, "_token") as token, self.assertRaises(ValueError):
                    self.publish()
                token.assert_not_called()
                self.job["status"] = "succeeded"
                self.write_job()
                (self.web / "index.wasm").write_bytes(original)
                (self.web / "unexpected.txt").unlink(missing_ok=True)

    def test_invalid_inventory_and_git_metadata_fail_closed(self):
        self.job["web_sha256"]["../escape"] = "0" * 64
        self.write_job()
        with self.assertRaises(ValueError):
            publisher.verify_web(self.web, self.job_path)
        del self.job["web_sha256"]["../escape"]
        self.write_job()
        (self.web / ".git").mkdir()
        with self.assertRaisesRegex(ValueError, "Git metadata"):
            publisher.verify_web(self.web, self.job_path)

    def test_linked_web_output_is_rejected(self):
        target = self.root / "secret.txt"
        target.write_text("not-public")
        link = self.web / "linked.txt"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("platform does not grant symlink creation")
        with self.assertRaisesRegex(ValueError, "links"):
            publisher.verify_web(self.web, self.job_path)

    def test_existing_branch_refused_before_checkout_creation(self):
        with mock.patch.object(publisher, "_token", return_value="secret"), mock.patch.object(publisher, "_pages", return_value=None), self.external_mocks(branch_exists=True), self.assertRaisesRegex(ValueError, "already exists"):
            self.publish()
        self.assertFalse(self.checkout.exists())

    def test_different_pages_source_refused_without_git(self):
        other = {**self.site, "source": {"branch": "main", "path": "/docs"}}
        with mock.patch.object(publisher, "_token", return_value="secret"), mock.patch.object(publisher, "_pages", return_value=other), mock.patch.object(publisher, "_git") as git, self.assertRaisesRegex(ValueError, "different Pages source"):
            self.publish()
        git.assert_not_called()

    def test_checkout_must_be_fresh_and_under_ignored_artifacts(self):
        for checkout in [self.root, self.web, self.root / "outside", self.root / "artifacts"]:
            with self.subTest(checkout=checkout), mock.patch.object(publisher, "_token") as token, self.assertRaises(ValueError):
                publisher.publish(self.web, self.job_path, "example/domes", checkout, public_demo=True)
            token.assert_not_called()
        self.checkout.mkdir(parents=True)
        with self.assertRaises(ValueError):
            self.publish()

    def test_committed_blob_mismatch_prevents_push(self):
        with mock.patch.object(publisher, "_token", return_value="secret"), mock.patch.object(publisher, "_pages", return_value=None) as pages, self.external_mocks(corrupt_blob=True) as git, self.assertRaisesRegex(ValueError, "changed a verified"):
            self.publish()
        self.assertFalse(any(call.args[0][0] == "push" for call in git.call_args_list))
        self.assertEqual(1, pages.call_count)
        receipt = json.loads(self.receipt_path.read_text())
        self.assertEqual("failed", receipt["status"])
        self.assertFalse(receipt["branch_pushed"])

    def test_push_failure_never_creates_pages(self):
        with mock.patch.object(publisher, "_token", return_value="secret"), mock.patch.object(publisher, "_pages", return_value=None) as pages, self.external_mocks(push_fails=True), self.assertRaises(ValueError):
            self.publish()
        self.assertEqual(1, pages.call_count)
        self.assertEqual("failed", json.loads(self.receipt_path.read_text())["status"])

    def test_pages_failure_preserves_successful_push_in_receipt(self):
        with mock.patch.object(publisher, "_token", return_value="secret"), mock.patch.object(publisher, "_pages", side_effect=[None, ValueError("no Pages permission")]), self.external_mocks(), self.assertRaises(ValueError):
            self.publish()
        receipt = json.loads(self.receipt_path.read_text())
        self.assertEqual("failed", receipt["status"])
        self.assertTrue(receipt["branch_pushed"])
        self.assertEqual(40, len(receipt["commit"]))
        self.assertFalse(receipt["browser_verified"])

    def test_git_environment_cannot_redirect_isolated_writes(self):
        with mock.patch.dict(os.environ, {"GIT_DIR": "protected/.git", "GIT_WORK_TREE": "protected", "GIT_INDEX_FILE": "protected/index", "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.worktree", "GIT_CONFIG_VALUE_0": "protected"}):
            environment = publisher._git_environment()
        self.assertFalse(any(key in environment for key in ["GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"]))
        self.assertEqual("0", environment["GIT_TERMINAL_PROMPT"])

    def test_api_rejects_redirect_and_does_not_follow_token(self):
        handler = publisher._NoRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, "", {}, "https://untrusted.example"))
        opener = mock.MagicMock()
        opener.open.side_effect = urllib.error.HTTPError("https://api.github.com/repos/example/domes/pages", 302, "redirect", {}, None)
        with mock.patch.object(publisher.urllib.request, "build_opener", return_value=opener), self.assertRaisesRegex(ValueError, "HTTP 302"):
            publisher._pages("example/domes", "secret")
        self.assertEqual(1, opener.open.call_count)

    def test_pages_api_fixed_host_and_exact_creation_source(self):
        opener = mock.MagicMock()
        response = opener.open.return_value.__enter__.return_value
        response.status = 201
        response.read.return_value = json.dumps(self.site).encode()
        with mock.patch.object(publisher.urllib.request, "build_opener", return_value=opener):
            self.assertEqual(self.site, publisher._pages("example/domes", "secret", create=True))
        request = opener.open.call_args.args[0]
        self.assertEqual("https://api.github.com/repos/example/domes/pages", request.full_url)
        self.assertEqual("POST", request.method)
        self.assertEqual({"build_type": "legacy", "source": {"branch": publisher.BRANCH, "path": "/"}}, json.loads(request.data))

    def test_token_uses_environment_or_captured_git_helper(self):
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "operator-env-token"}), mock.patch.object(publisher.subprocess, "run") as run:
            self.assertEqual("operator-env-token", publisher._token())
        run.assert_not_called()
        result = subprocess.CompletedProcess([], 0, b"protocol=https\nhost=github.com\nusername=operator\npassword=helper-secret\n", b"")
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": ""}), mock.patch.object(publisher.subprocess, "run", return_value=result) as run:
            self.assertEqual("helper-secret", publisher._token())
        self.assertEqual(["git", "credential", "fill"], run.call_args.args[0])
        self.assertEqual(subprocess.PIPE, run.call_args.kwargs["stdout"])


if __name__ == "__main__":
    unittest.main()
