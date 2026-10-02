"""Exercise generated files and isolation; no network or creative tool required."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import character_factory as factory
from factory_glb import accessor_values, read_glb

FIXTURE = ROOT / "examples/character_factory"


def source_hashes():
    return {str(path.relative_to(ROOT)): factory.digest(path) for path in (ROOT / "godot").rglob("*")
            if path.is_file() and ".godot" not in path.parts}


def rewrite_glb(path, doc, binary):
    serialized = json.dumps(doc, separators=(",", ":")).encode()
    serialized += b" "*(-len(serialized) % 4)
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, 28+len(serialized)+len(binary))
                     + struct.pack("<II", len(serialized), 0x4E4F534A)+serialized
                     + struct.pack("<II", len(binary), 0x004E4942)+binary)
    package = factory.read_json(path.parent / "package.json")
    package["files"]["character.glb"] = factory.digest(path)
    factory.write_json(path.parent / "package.json", package)


class CharacterFactoryTests(unittest.TestCase):
    def setUp(self):
        self.interview = factory.read_json(FIXTURE / "aster.interview.json")
        self.temp = tempfile.TemporaryDirectory(prefix="domes-factory-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def spec(self):
        return factory.derive_spec(self.interview, FIXTURE)

    def package(self):
        folder = self.folder / "package"
        factory.generate_package(self.spec(), folder)
        return folder

    def test_reference_evidence_is_bound_to_approved_image_bytes(self):
        spec = self.spec()
        self.assertEqual(factory.digest(FIXTURE / "aster-reference.png"), spec["references"][0]["sha256"])
        self.assertNotIn("path", spec["references"][0])
        self.assertIn("does not infer geometry", spec["decisions"]["implementation_scope"])

    def test_dot_choices_survive_and_human_veto_and_override_take_precedence(self):
        self.interview["human"]["color_overrides"]["accent"] = "#123456"
        spec = self.spec()
        self.assertEqual(["chest_badge"], spec["appearance"]["accessories"])
        self.assertEqual("#123456", spec["appearance"]["colors"]["accent"])
        self.assertEqual(self.interview["dot"]["self_image"], spec["creative_intent"]["self_image"])

    def test_missing_approval_stops_before_generation(self):
        for key in ("human", "reference"):
            interview = copy.deepcopy(self.interview)
            (interview["human"] if key == "human" else interview["references"][0])["approved"] = False
            with self.subTest(key=key), self.assertRaises(ValueError):
                factory.derive_spec(interview, FIXTURE)

    def test_reference_traversal_and_external_urls_are_rejected(self):
        for value in ("../character_factory/aster-reference.png", "https://example.com/model.png", str(FIXTURE / "aster-reference.png")):
            self.interview["references"][0]["path"] = value
            with self.subTest(path=value), self.assertRaises(ValueError):
                self.spec()

    def test_duplicate_reference_identity_is_rejected(self):
        entry = copy.deepcopy(self.interview["references"][0])
        entry["description"] += " alternate"
        self.interview["references"].append(entry)
        with self.assertRaisesRegex(ValueError, "duplicate reference"):
            self.spec()

    def test_non_image_upload_is_rejected(self):
        (self.folder / "text.png").write_text("not image bytes", encoding="utf-8")
        self.interview["references"][0]["path"] = "text.png"
        with self.assertRaisesRegex(ValueError, "signature"):
            factory.derive_spec(self.interview, self.folder)

    def test_unsupported_geometry_and_non_finite_proportions_are_rejected(self):
        for field, value in (("body", "photoreal_human"), ("height_m", float("nan")), ("height_m", 3)):
            interview = copy.deepcopy(self.interview)
            interview["dot"]["appearance"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                factory.derive_spec(interview, FIXTURE)

    def test_complete_package_has_real_skin_geometry_and_twelve_animated_clips(self):
        folder = self.package()
        report = factory.validate_package(folder)
        self.assertTrue(report["ok"], report)
        self.assertEqual(18, report["joint_count"])
        self.assertEqual(12, report["clip_count"])
        self.assertGreater(report["vertex_count"], 400)
        doc, binary = read_glb(folder / "character.glb")
        self.assertEqual("2.0", doc["asset"]["version"])
        self.assertTrue(any(node.get("skin") == 0 for node in doc["nodes"]))
        self.assertEqual(18, len(accessor_values(doc, binary, doc["skins"][0]["inverseBindMatrices"])))
        self.assertEqual(12, len(doc["animations"]))
        self.assertFalse(list(folder.glob("*.png")), "private reference pixels must not be published")

    def test_same_approved_inputs_generate_identical_immutable_assets(self):
        first = self.package()
        second = self.folder / "second"
        factory.generate_package(self.spec(), second)
        for name in ("character.glb", "character.json", "spec.json", "package.json"):
            self.assertEqual(factory.digest(first/name), factory.digest(second/name), name)
        with self.assertRaisesRegex(ValueError, "already exists"):
            factory.generate_package(self.spec(), first)

    def test_palette_and_accessories_change_actual_mesh_materials(self):
        first = self.package()
        first_doc, _ = read_glb(first / "character.glb")
        self.interview["human"]["veto_accessories"] = []
        self.interview["human"]["color_overrides"]["primary"] = "#ff0000"
        second = self.folder / "variant"
        factory.generate_package(self.spec(), second)
        second_doc, _ = read_glb(second / "character.glb")
        self.assertEqual([1, 0, 0, 1], second_doc["materials"][0]["pbrMetallicRoughness"]["baseColorFactor"])
        self.assertGreater(len(second_doc["meshes"][0]["primitives"]), len(first_doc["meshes"][0]["primitives"]))

    def test_tampered_package_hash_is_rejected(self):
        folder = self.package()
        with (folder / "character.glb").open("ab") as output:
            output.write(b"tampered")
        report = factory.validate_package(folder)
        self.assertFalse(report["ok"])
        self.assertIn("digest mismatch", report["errors"][0])

    def test_manifest_cannot_redirect_install_to_arbitrary_scene(self):
        folder = self.package()
        manifest = factory.read_json(folder / "character.json")
        manifest["scene_path"] = "res://scenes/characters/placeholder.tscn"
        factory.write_json(folder / "character.json", manifest)
        report = factory.validate_package(folder)
        self.assertFalse(report["ok"])
        self.assertIn("backend contract", report["errors"][0])

    def test_rehashed_glb_with_missing_skin_is_rejected(self):
        folder = self.package()
        doc, binary = read_glb(folder / "character.glb")
        doc["skins"] = []
        rewrite_glb(folder / "character.glb", doc, binary)
        report = factory.validate_package(folder)
        self.assertFalse(report["ok"])
        self.assertIn("real 18-joint skin", report["errors"][0])

    def test_rehashed_glb_with_missing_semantic_is_rejected(self):
        folder = self.package()
        doc, binary = read_glb(folder / "character.glb")
        doc["animations"].pop()
        rewrite_glb(folder / "character.glb", doc, binary)
        report = factory.validate_package(folder)
        self.assertFalse(report["ok"])
        self.assertIn("semantic clips", report["errors"][0])

    def test_rehashed_glb_accessor_cannot_escape_binary_buffer(self):
        folder = self.package()
        doc, binary = read_glb(folder / "character.glb")
        doc["bufferViews"][0]["byteOffset"] = len(binary)+100
        rewrite_glb(folder / "character.glb", doc, binary)
        report = factory.validate_package(folder)
        self.assertFalse(report["ok"])
        self.assertIn("exceeds", report["errors"][0])

    def test_install_uses_isolated_copy_and_preserves_original_worlds(self):
        folder = self.package()
        before = source_hashes()
        stage = self.folder / "stage"
        receipt = factory.install_package(folder, ROOT, stage, "tidal_observatory")
        self.assertEqual(before, source_hashes())
        self.assertEqual([], factory.ContentValidator(stage).validate())
        self.assertTrue((stage / "godot/assets/generated/aster/character.glb").is_file())
        world = factory.read_json(stage / "godot/content/worlds/tidal_observatory.json")
        self.assertEqual(receipt["character_path"], world["character_path"])
        self.assertEqual("pending", receipt["godot_import"])
        self.assertEqual("pending", receipt["browser_acceptance"])
        self.assertTrue((stage / "tools/build.py").is_file())
        source_brief = factory.read_json(ROOT / "godot/content/briefs/tidal_observatory.json")
        stage_brief = factory.read_json(stage / "godot/content/briefs/tidal_observatory.json")
        self.assertEqual(source_brief["owner_locked"], stage_brief["owner_locked"])

    def test_install_refuses_existing_directory_and_live_source(self):
        folder = self.package()
        for destination in (ROOT, self.folder, ROOT / "godot" / "test_stage"):
            with self.subTest(path=destination), self.assertRaises(ValueError):
                factory.install_package(folder, ROOT, destination, "tidal_observatory")

    def test_character_name_collision_does_not_replace_source_character(self):
        self.interview["character_id"] = "nova"
        folder = self.package()
        with self.assertRaisesRegex(ValueError, "collides"):
            factory.install_package(folder, ROOT, self.folder / "stage", "tidal_observatory")

    def test_incompatible_clearance_rejects_install_and_cleans_incomplete_stage(self):
        self.interview["dot"]["appearance"]["height_m"] = 1.6
        folder = self.package()
        before = source_hashes()
        with self.assertRaisesRegex(ValueError, "character"):
            factory.install_package(folder, ROOT, self.folder / "stage", "tidal_observatory")
        self.assertFalse((self.folder / "stage").exists())
        self.assertFalse(list(self.folder.glob(".world-stage-*")))
        self.assertEqual(before, source_hashes())


if __name__ == "__main__":
    unittest.main()
