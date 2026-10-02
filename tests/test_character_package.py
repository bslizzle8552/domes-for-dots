"""Exercise the generic/strict boundary using real packages and hostile edits."""
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import character_factory as factory
import character_backends
import procedural_character
from factory_glb import read_glb, accessor_values

FIXTURE = ROOT / "examples/character_factory"


class CharacterPackageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="domes-contract-")
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name) / "package"
        self.spec = factory.derive_spec(factory.read_json(FIXTURE / "aster.interview.json"), FIXTURE)
        factory.generate_package(self.spec, self.folder)
        self.package = factory.read_json(self.folder / "package.json")

    def save(self):
        factory.write_json(self.folder / "package.json", self.package)

    def rewrite_spec(self, spec):
        factory.write_json(self.folder / "spec.json", spec)
        self.package["files"]["spec.json"] = factory.digest(self.folder / "spec.json")
        self.save()

    def test_v2_envelope_declares_runtime_assets_and_validator(self):
        self.assertEqual(2, self.package["schema_version"])
        self.assertEqual("character.json", self.package["runtime_manifest"])
        self.assertEqual("spec.json", self.package["spec_path"])
        self.assertEqual({"character.glb": "res://assets/generated/aster/character.glb"}, self.package["assets"])
        self.assertEqual(procedural_character.ID, self.package["validation"]["validator"])
        self.assertTrue(factory.validate_package(self.folder)["ok"])

    def test_generic_spec_accepts_alternate_body_but_producer_rejects_it(self):
        self.spec["appearance"] = {"body": "organic_mascot", "deformation": "smooth"}
        factory.validate_schema("character-spec", self.spec)
        with self.assertRaises(ValueError):
            factory.generate_package(self.spec, self.folder.parent / "rejected")
        self.assertFalse((self.folder.parent / "rejected").exists())

    def test_generic_envelopes_do_not_require_robot_backend_or_fixed_file_names(self):
        self.spec["backend"] = "future_organic_v1"
        self.spec["appearance"] = {"body": "organic_mascot"}
        self.spec["creative_intent"]["activities"] = ["swim"]
        self.spec["decisions"] = {"human_approved": True, "representation": "approved"}
        factory.validate_schema("character-spec", self.spec)
        self.package.update(backend="future_organic_v1", runtime_manifest="avatar/manifest.json",
                            spec_path="input/choices.json", files={"avatar/manifest.json": "0"*64, "input/choices.json": "1"*64, "mesh/body.glb": "2"*64},
                            assets={"mesh/body.glb": "res://assets/generated/aster/body.glb"},
                            capabilities=["idle", "swim"], validation={"validator": "future_organic_v1", "report": "validation.json"})
        factory.validate_schema("character-package", self.package)
        with self.assertRaisesRegex(ValueError, "unsupported character backend"):
            factory.generate_package(self.spec, self.folder.parent / "unknown")

    def test_unknown_backend_cannot_pass_with_a_forged_success_report(self):
        self.package["backend"] = "future_organic_v1"
        self.save()
        factory.write_json(self.folder / "validation.json", {"ok": True, "checks": ["claimed"]})
        report = factory.validate_package(self.folder)
        self.assertFalse(report["ok"])
        self.assertIn("unsupported character backend", report["errors"][0])

    def test_backend_identifier_mismatch_is_rejected_after_rehash(self):
        self.spec["backend"] = "future_organic_v1"
        self.rewrite_spec(self.spec)
        report = factory.validate_package(self.folder)
        self.assertFalse(report["ok"])
        self.assertIn("backends disagree", report["errors"][0])

    def test_registered_validator_is_mandatory_and_cannot_be_bypassed(self):
        with mock.patch.object(procedural_character, "validate_assets", side_effect=ValueError("strict producer rejected asset")) as validator:
            report = factory.validate_package(self.folder)
        validator.assert_called_once()
        self.assertFalse(report["ok"])
        self.assertIn("strict producer rejected", report["errors"][0])

    def test_legacy_v1_fixture_still_runs_full_strict_validation(self):
        self.package["schema_version"] = 1
        for key in ("runtime_manifest", "spec_path", "assets", "validation"):
            del self.package[key]
        self.save()
        report = factory.validate_package(self.folder)
        self.assertTrue(report["ok"], report)
        self.assertEqual(18, report["joint_count"])
        self.assertEqual(12, report["clip_count"])

    def test_missing_hashed_manifest_and_undeclared_file_are_rejected(self):
        self.package["runtime_manifest"] = "absent.json"
        self.save()
        self.assertFalse(factory.validate_package(self.folder)["ok"])
        self.package["runtime_manifest"] = "character.json"
        self.save()
        (self.folder / "unreviewed.gd").write_text("extends Node")
        self.assertIn("undeclared package file", factory.validate_package(self.folder)["errors"][0])

    def test_traversal_and_cross_character_install_mapping_are_rejected(self):
        self.package["files"]["../outside.glb"] = "0" * 64
        self.save()
        self.assertFalse(factory.validate_package(self.folder)["ok"])
        del self.package["files"]["../outside.glb"]
        self.package["assets"]["character.glb"] = "res://assets/generated/someone_else/character.glb"
        self.save()
        self.assertFalse(factory.validate_package(self.folder)["ok"])

    def test_validator_receipt_and_capability_claims_cannot_weaken_validation(self):
        self.package["validation"]["validator"] = "permissive_validator"
        self.save()
        self.assertIn("validation metadata", factory.validate_package(self.folder)["errors"][0])
        self.package["validation"]["validator"] = procedural_character.ID
        self.package["capabilities"] = ["idle", "walk"]
        self.save()
        self.assertIn("capabilities disagree", factory.validate_package(self.folder)["errors"][0])

    def test_rehashed_smooth_weights_are_rejected_by_rigid_backend(self):
        path = self.folder / "character.glb"
        doc, binary = read_glb(path)
        accessor = doc["accessors"][doc["meshes"][0]["primitives"][0]["attributes"]["WEIGHTS_0"]]
        view = doc["bufferViews"][accessor["bufferView"]]
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        binary = bytearray(binary)
        struct.pack_into("<ffff", binary, offset, .5, .5, 0, 0)
        # Header and JSON chunk remain unchanged, replace just the binary payload.
        raw = bytearray(path.read_bytes())
        raw[-len(binary):] = binary
        path.write_bytes(raw)
        self.package["files"]["character.glb"] = factory.digest(path)
        self.save()
        self.assertIn("rigid weights", factory.validate_package(self.folder)["errors"][0])

    def test_generated_runtime_matches_the_published_aster_fixture(self):
        # The deployed job used canonical wire key ordering. Reuse its exact
        # spec, rather than treating differently ordered JSON as the same bytes.
        published = FIXTURE / "generated-aster"
        regenerated = self.folder.parent / "published-spec"
        factory.generate_package(factory.read_json(published / "spec.json"), regenerated)
        for name in ("character.json", "spec.json"):
            self.assertEqual(factory.read_json(published / name), factory.read_json(regenerated / name), name)
        old, old_binary = read_glb(published / "character.glb")
        new, new_binary = read_glb(regenerated / "character.glb")
        def equivalent(first, second):
            if isinstance(first, float) or isinstance(second, float):
                self.assertAlmostEqual(first, second, places=12)
            elif isinstance(first, dict):
                self.assertEqual(set(first), set(second))
                for key in first:
                    equivalent(first[key], second[key])
            elif isinstance(first, list):
                self.assertEqual(len(first), len(second))
                for a, b in zip(first, second):
                    equivalent(a, b)
            else:
                self.assertEqual(first, second)
        equivalent(old, new)
        # Native math libraries may differ in insignificant quaternion low bits
        # across Windows/Linux. Verify actual decoded geometry/clip samples.
        for index in range(len(old["accessors"])):
            first = accessor_values(old, old_binary, index)
            second = accessor_values(new, new_binary, index)
            self.assertEqual(len(first), len(second))
            for left, right in zip(first, second):
                for a, b in zip(left, right):
                    self.assertAlmostEqual(a, b, places=6)


if __name__ == "__main__":
    unittest.main()
