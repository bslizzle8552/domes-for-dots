"""Actual factory validation around bounded cloud transport and dispatch mocks."""
import base64
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
import unittest
from unittest import mock
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import character_request as transport

ROOT = Path(__file__).resolve().parents[1]


class CharacterRequestTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="domes-request-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source"
        shutil.copytree(ROOT / "examples/character_factory", self.source)
        self.interview = self.source / "aster.interview.json"
        self.request = transport.pack(self.interview, self.source)
        self.output = self.root / "unpacked"

    def assert_rejected(self, request):
        with self.assertRaises((ValueError, OSError)):
            transport.unpack(request, self.output)
        self.assertFalse(self.output.exists())
        self.assertFalse(any(path.name.startswith(".request-") for path in self.root.iterdir()))

    def test_roundtrip_validates_both_sides_and_copies_only_declared_references(self):
        (self.source / "unrelated.py").write_text("raise RuntimeError('must not execute')", encoding="utf-8")
        with mock.patch.object(transport, "derive_spec", wraps=transport.derive_spec) as derive:
            request = transport.pack(self.interview, self.source)
            path = transport.unpack(request, self.output)
            self.assertEqual(2, derive.call_count)
        self.assertEqual(json.loads(self.interview.read_text()), json.loads(path.read_text()))
        self.assertEqual((self.source / "aster-reference.png").read_bytes(), (self.output / "aster-reference.png").read_bytes())
        self.assertEqual({"interview.json", "aster-reference.png"}, {path.name for path in self.output.iterdir()})
        self.assertLessEqual(len(transport.encode(request)), 48 * 1024)

    def test_unapproved_human_and_reference_are_rejected(self):
        for target in ("human", "reference"):
            request = copy.deepcopy(self.request)
            approval = request["interview"]["human"] if target == "human" else request["interview"]["references"][0]
            approval["approved"] = False
            with self.subTest(target=target):
                self.assert_rejected(request)

    def test_tampered_reference_digest_is_rejected_before_writing(self):
        request = copy.deepcopy(self.request)
        request["references"][0]["sha256"] = "0" * 64
        self.assert_rejected(request)

    def test_archive_payload_with_matching_digest_still_fails_factory_validation(self):
        request = copy.deepcopy(self.request)
        raw = b"PK\x03\x04not-an-image"
        request["references"][0].update(sha256=hashlib.sha256(raw).hexdigest(), bytes_base64=base64.b64encode(raw).decode())
        self.assert_rejected(request)

    def test_undeclared_missing_duplicate_and_extra_envelopes_are_rejected(self):
        variants = []
        request = copy.deepcopy(self.request)
        request["references"][0]["path"] = "unrelated.png"
        variants.append(request)
        request = copy.deepcopy(self.request)
        request["references"] = []
        variants.append(request)
        request = copy.deepcopy(self.request)
        request["references"].append(copy.deepcopy(request["references"][0]))
        variants.append(request)
        request = copy.deepcopy(self.request)
        request["executable"] = "do-not-run.py"
        variants.append(request)
        for request in variants:
            with self.subTest(keys=list(request)):
                self.assert_rejected(request)

    def test_portable_traversal_and_device_paths_are_rejected(self):
        for name in ["../escape.png", "/tmp/escape.png", "C:/escape.png", "a\\escape.png", "a//b.png", "a/../b.png", "CON.png", "a/NUL.jpg", "a/trailing./b.png", "https://example.com/a.png", "upload.py"]:
            request = copy.deepcopy(self.request)
            request["references"][0]["path"] = name
            request["interview"]["references"][0]["path"] = name
            with self.subTest(path=name):
                self.assert_rejected(request)

    def test_case_colliding_reference_paths_are_rejected(self):
        request = copy.deepcopy(self.request)
        other = copy.deepcopy(request["interview"]["references"][0])
        other.update(id="another", path=other["path"].upper())
        request["interview"]["references"].append(other)
        image = copy.deepcopy(request["references"][0])
        image["path"] = image["path"].upper()
        request["references"].append(image)
        self.assert_rejected(request)

    def test_oversized_and_invalid_base64_are_rejected(self):
        for encoded in ["!bad-base64!", "A" * (transport.MAX_REQUEST_BYTES + 1)]:
            request = copy.deepcopy(self.request)
            request["references"][0]["bytes_base64"] = encoded
            self.assert_rejected(request)

    def test_pack_rejects_oversized_reference_without_transporting_it(self):
        (self.source / "aster-reference.png").write_bytes(b"x" * (transport.MAX_REFERENCE_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "oversized"):
            transport.pack(self.interview, self.source)

    def test_existing_output_is_preserved(self):
        transport.unpack(self.request, self.output)
        sentinel = self.output / "keep.txt"
        sentinel.write_text("preserve", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            transport.unpack(self.request, self.output)
        self.assertEqual("preserve", sentinel.read_text())

    def test_symlinked_parent_reference_is_rejected(self):
        actual = self.source / "actual"
        actual.mkdir()
        shutil.copy2(self.source / "aster-reference.png", actual / "image.png")
        link = self.source / "alias"
        try:
            link.symlink_to(actual, target_is_directory=True)
        except OSError:
            self.skipTest("filesystem does not grant symlink creation")
        interview = json.loads(self.interview.read_text())
        interview["references"][0]["path"] = "alias/image.png"
        self.interview.write_text(json.dumps(interview), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "symlinks"):
            transport.pack(self.interview, self.source)

    def test_env_cli_uses_explicit_default_through_same_transport(self):
        argv = ["character_request.py", "--output-dir", str(self.output), "--default-interview", str(self.interview)]
        with mock.patch.object(sys, "argv", argv), mock.patch.dict(os.environ, {"DOMES_CHARACTER_REQUEST": ""}), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, transport.main())
        self.assertEqual("unpacked", json.loads(output.getvalue())["status"])
        self.assertTrue((self.output / "interview.json").exists())

    def test_env_cli_rejects_without_echoing_sensitive_input(self):
        secret_fixture = "sensitive-private-reference"
        argv = ["character_request.py", "--output-dir", str(self.output)]
        with mock.patch.object(sys, "argv", argv), mock.patch.dict(os.environ, {"DOMES_CHARACTER_REQUEST": "{invalid " + secret_fixture}), contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(1, transport.main())
        self.assertNotIn(secret_fixture, output.getvalue())
        self.assertFalse(self.output.exists())

    def dispatch(self, request=None, **overrides):
        return transport.dispatch(request or self.request, **({"repository": "example/domes", "ref": "main"} | overrides))

    def test_dispatch_sends_fixed_origin_post_and_returns_only_acceptance(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.read.return_value = json.dumps({"workflow_run_id": 42, "html_url": "https://github.com/example/domes/actions/runs/42"}).encode()
        opener = mock.Mock()
        opener.open.return_value = response
        token = "test-operator-secret"
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": token}), mock.patch.object(transport.urllib.request, "build_opener", return_value=opener):
            receipt = self.dispatch()
        call = opener.open.call_args.args[0]
        self.assertEqual("POST", call.method)
        self.assertEqual("https://api.github.com/repos/example/domes/actions/workflows/character-factory.yml/dispatches", call.full_url)
        payload = json.loads(call.data)
        self.assertEqual("main", payload["ref"])
        self.assertEqual(self.request, json.loads(payload["inputs"]["request_json"]))
        self.assertEqual("accepted", receipt["status"])
        self.assertEqual(42, receipt["workflow_run_id"])
        self.assertNotIn(token, json.dumps(receipt))

    def test_dispatch_rejects_unconfigured_auth_or_untrusted_config_before_network(self):
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": ""}), mock.patch.object(transport.urllib.request, "build_opener") as network:
            with self.assertRaisesRegex(ValueError, "GITHUB_TOKEN"):
                self.dispatch()
            network.assert_not_called()
        for overrides in [{"repository": "https://evil.example/repo"}, {"workflow": "../evil.yml"}, {"ref": "main\nrun"}]:
            with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "fixture"}), mock.patch.object(transport.urllib.request, "build_opener") as network:
                with self.assertRaises(ValueError):
                    self.dispatch(**overrides)
                network.assert_not_called()

    def test_dispatch_failure_does_not_echo_upstream_body_or_token(self):
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError("https://api.github.com/", 403, "private upstream content", {}, None)
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "secret-token"}), mock.patch.object(transport.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(ValueError, "HTTP 403") as failure:
                self.dispatch()
        self.assertNotIn("private", str(failure.exception))
        self.assertNotIn("secret-token", str(failure.exception))

    def test_authenticated_redirects_are_not_followed(self):
        self.assertIsNone(transport._NoRedirect().redirect_request(None, None, 302, "", {}, "https://elsewhere.invalid"))


if __name__ == "__main__":
    unittest.main()
