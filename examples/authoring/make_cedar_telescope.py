#!/usr/bin/env python3
"""Prepare one additive example against the current Cedar source, without applying."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import world_author as author


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=Path("artifacts/cedar-telescope.request.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    world = author.read_json(root / "godot/content/worlds/cedar_atelier.json")
    if any(obj["id"] == "terrace_telescope" for obj in world["objects"]):
        raise SystemExit("This example is already present; choose another creative increment.")
    world["asset_manifest_paths"].append("res://content/assets/cedar_telescope.json")
    world["objects"].append({"id": "terrace_telescope", "asset_id": "small_telescope", "position": [8.25, 0, 0.5], "rotation_y": -45, "scale": [1, 1, 1]})
    world["stations"].append({"id": "telescope", "label": "Observe from the terrace", "object_id": "terrace_telescope", "activity_tags": ["observe"], "approach": [7, 0, 0.5], "interaction": [7, 0, 0.5], "facing": -90, "animation": "observe", "fallback_animation": "interact", "behavior": "", "metadata": {"note": "Generic observe fallback; no sky sensor or optical simulation."}})
    def part(shape, position, size, color, rotation=None):
        return {"shape": shape, "position": position, "size": size, "rotation": rotation or [0, 0, 0], "color": color, "emission": 0}
    manifest = {"schema_version": 1, "id": "cedar_telescope", "assets": [{
        "id": "small_telescope", "display_name": "Moss's terrace telescope", "category": "instrument", "tags": ["observe"], "scene_path": "", "scale": [1, 1, 1], "rotation_y": 0,
        "collision": {"enabled": True, "size": [0.75, 1.5, 0.75], "offset": [0, 0.75, 0]}, "footprint": [1.2, 1.2], "anchors": {},
        "parts": [part("cylinder", [0, 0.06, 0], [0.75, 0.12, 0.75], "#8c7554"), part("cylinder", [0, 0.65, 0], [0.09, 1.18, 0.09], "#735f4a"), part("cylinder", [0, 1.35, 0], [0.25, 0.95, 0.25], "#d8b677", [0, 0, 60])],
        "animation": "", "behavior": "", "metadata": {}, "provenance": {"creator": "Domes for Dots contributors", "source": "Original primitive authoring example", "license": "MIT"},
    }]}
    proposal = {"schema_version": 1, "id": "cedar_telescope_addition", "world_id": "cedar_atelier", "intent": "expand", "description": "Moss chooses a small terrace telescope and an observation station. Existing routines and epoch remain unchanged; Visit or a MOCK observe event can use it.", "files": [{"path": "godot/content/worlds/cedar_atelier.json", "document": world}, {"path": "godot/content/assets/cedar_telescope.json", "document": manifest}]}
    request = author.prepare_request(root, proposal)
    report = author.plan(root, request)
    author.write_output(root, args.output, request)
    print(f"{report['status']}: {args.output}; additive schema/navigation checks passed; apply and runtime preview remain separate")


if __name__ == "__main__":
    main()
