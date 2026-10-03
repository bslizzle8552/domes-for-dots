#!/usr/bin/env python3
"""Operator/cloud proof: three independent intents -> packages -> shared runtime -> Web.

Uses the existing pinned engine bootstrap and checked command runner. This is an
operator workflow for synthetic fixtures, not a public provisioning/auth service.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from build import find_godot, run, runtime_hashes, source_metadata
from character_contract import ROOT, digest, write_json
from character_factory import engine_acceptance, generate_package
from character_package import validate_package as validate_character
from world_package import build_package, validate_package as validate_world
from world_composer import compose_many
from validate_content import ContentValidator, read_json

FIXTURES = ("ember_foundry", "lumen_observatory", "verdant_courtyard")


def atomic_json(path, data):
    temporary = path.with_suffix(".partial")
    write_json(temporary, data)
    temporary.replace(path)


def source_hashes(root):
    result = runtime_hashes(root)
    for folder, pattern in [("tools", "*.py"), ("schemas", "*.json"), ("examples/world_creator", "*.intent.json"),
                            ("examples/world_creator", "*.character-spec.json")]:
        for path in sorted((root/folder).glob(pattern)):
            result[path.relative_to(root).as_posix()] = digest(path)
    return result


def require_test_success(output, label, expression):
    if not re.search(expression, output):
        raise ValueError(label+" did not report explicit zero-failure acceptance")


def execute(job_dir, godot_bin=None, export_web=True):
    job_dir = Path(job_dir).resolve()
    # No resume-in-place: a new attempt creates a new receipt and candidate.
    job_dir.mkdir(parents=True, exist_ok=False)
    logs = job_dir/"logs"
    logs.mkdir()
    clock = time.monotonic()
    receipt = {"schema_version": 1, "status": "running", "phase": "initializing",
               "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "provider": "github_actions" if os.environ.get("GITHUB_ACTIONS") == "true" else "developer_worker",
               "run_id": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
               "source": source_metadata(ROOT), "world_ids": list(FIXTURES), "events": [], "durations_seconds": {},
               "deployment": {"status": "not_deployed", "privacy": "requires_private_host", "url": None},
               "browser_acceptance": "not_run_by_worker; requires separate browser evidence for these bytes"}

    def phase(name):
        receipt["phase"] = name
        receipt["events"].append({"phase": name, "at_utc": datetime.now(timezone.utc).isoformat()})
        atomic_json(job_dir/"job.json", receipt)

    def timed(name, operation):
        phase(name)
        start = time.monotonic()
        try:
            return operation()
        finally:
            receipt["durations_seconds"][name] = round(time.monotonic()-start, 6)
            atomic_json(job_dir/"job.json", receipt)

    try:
        before = source_hashes(ROOT)
        receipt["source_sha256"] = before
        pairs, package_reports = [], []
        package_root = job_dir/"packages"
        package_root.mkdir()
        for world_id in FIXTURES:
            character_dir, world_dir = package_root/(world_id+".character"), package_root/(world_id+".world")
            intent = read_json(ROOT/"examples/world_creator"/(world_id+".intent.json"))
            character_spec = read_json(ROOT/"examples/world_creator"/(world_id+".character-spec.json"))
            timed(world_id+"_character", lambda: generate_package(character_spec, character_dir))
            timed(world_id+"_compile", lambda: build_package(intent, character_dir, world_dir))
            reports = {"world_id": world_id, "character": validate_character(character_dir), "world": validate_world(world_dir)}
            if not reports["character"]["ok"] or not reports["world"]["ok"]:
                raise ValueError("world or character package failed mandatory registered validation: "+world_id)
            reports.update(world_package_sha256=digest(world_dir/"package.json"), character_package_sha256=digest(character_dir/"package.json"))
            package_reports.append(reports)
            pairs.append((world_dir, character_dir))
        receipt["package_validation"] = package_reports
        stage = job_dir/"stage"
        receipt["composition"] = timed("composition", lambda: compose_many(pairs, stage, ROOT))
        errors = timed("staged_content_validation", lambda: ContentValidator(stage).validate())
        if errors:
            raise ValueError("staged content failed: "+"; ".join(errors))
        godot = find_godot(godot_bin, ROOT)
        version = timed("engine_version", lambda: run([str(godot), "--version"], "engine_version", ROOT, logs)).strip()
        if not re.fullmatch(r"4\.5\.1\.stable(?:\.official)?(?:\.[A-Za-z0-9]+)?", version):
            raise ValueError("World Creator worker requires pinned Godot 4.5.1 Standard stable")
        receipt["engine"] = {"version": version, "binary_sha256": digest(godot), "export_profile": "Compatibility Web, single-threaded"}
        base = [str(godot), "--headless", "--path", str(stage/"godot")]
        timed("engine_import", lambda: run([*base, "--editor", "--import"], "import", ROOT, logs))
        audit_path = job_dir/"engine-audit.json"
        timed("engine_audit", lambda: run([*base, "--script", "res://tools/audit_characters.gd", "--", "--output", str(audit_path)], "audit", ROOT, logs))
        audit = read_json(audit_path)
        required_ids = set(receipt["composition"]["character_ids"])
        observed_ids = {c.get("character_id") for c in audit.get("characters", []) if c.get("ok") is True}
        if audit.get("ok") is not True or not required_ids <= observed_ids or not all(c.get("ok") is True for c in audit.get("characters", [])):
            raise ValueError("engine audit must include all three generated characters and pass every audited character")
        receipt["engine_audit"] = audit
        receipt["motion_acceptance"] = []
        for _, character_dir in pairs:
            package = read_json(character_dir/"package.json")
            acceptance = engine_acceptance(character_dir)
            cid = package["character_id"]
            output = timed(cid+"_motion", lambda: run([*base, "--fixed-fps", "60", "--script", acceptance["script"], "--", "--character", f"res://content/characters/{cid}.json"], cid+"_motion", ROOT, logs))
            require_test_success(output, cid+" motion", acceptance["success_pattern"])
            receipt["motion_acceptance"].append({"character_id": cid, "status": "passed", "contract": acceptance})
        for test, expression in [("generated_worlds", r"GENERATED WORLD TESTS:\s*\d+ passed,\s*0 failed"),
                                 ("multilevel", r"MULTILEVEL TESTS:\s*\d+ passed,\s*0 failed")]:
            output = timed(test, lambda: run([*base, "--fixed-fps", "60", "--script", "res://tests/test_"+test+".gd"], test, ROOT, logs, timeout=480))
            require_test_success(output, test, expression)
            receipt[test] = {"status": "passed", "summary": next(line for line in output.splitlines() if re.search(expression, line))}
            if test == "generated_worlds":
                evidence_line = next((line.split("GENERATED_WORLD_EVIDENCE ", 1)[1] for line in output.splitlines() if "GENERATED_WORLD_EVIDENCE " in line), None)
                if evidence_line:
                    receipt["generated_world_evidence"] = json.loads(evidence_line)
        if export_web:
            web = job_dir/"web"
            web.mkdir()
            timed("web_export", lambda: run([*base, "--export-release", "Web", str(web/"index.html")], "web_export", ROOT, logs))
            for name in ["index.html", "index.js", "index.wasm", "index.pck"]:
                if not (web/name).is_file() or not (web/name).stat().st_size:
                    raise ValueError("missing Web export: "+name)
            (web/"docs").mkdir()
            shutil.copy2(ROOT/"LICENSE", web/"LICENSE")
            for name in ["GODOT_LICENSE.txt", "GODOT_COPYRIGHT.txt", "THIRD_PARTY_NOTICES.md"]:
                shutil.copy2(ROOT/"docs"/name, web/"docs"/name)
            (web/"README.txt").write_text("DOMES FOR DOTS - World Creator synthetic proof\n\nVisitors open the operator's private HTTPS link; no developer tools are needed.\nContains Ember's foundry, Lumen's observatory and Fern's courtyard.\nRoutines are SIMULATED. Hosting alone does not grant private access or durable cloud state.\nThis artifact has not been deployed by the worker. Keep all runtime files and licenses together.\nBrowser playback needs separate acceptance for these exact exported bytes.\n", encoding="utf-8", newline="\n")
            (web/".nojekyll").touch()
            receipt["web_sha256"] = {p.relative_to(web).as_posix(): digest(p) for p in sorted(web.rglob("*")) if p.is_file()}
            receipt["web_bytes"] = sum(p.stat().st_size for p in web.rglob("*") if p.is_file())
        receipt["source_unchanged"] = source_hashes(ROOT) == before
        if not receipt["source_unchanged"]:
            raise ValueError("source files changed during isolated build; receipt cannot certify source snapshot")
        receipt["durations_seconds"]["total"] = round(time.monotonic()-clock, 6)
        receipt["status"] = "succeeded"
        phase("complete")
        return receipt
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = f"{type(error).__name__}: {error}"
        receipt["durations_seconds"]["total"] = round(time.monotonic()-clock, 6)
        atomic_json(job_dir/"job.json", receipt)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--godot")
    parser.add_argument("--no-web", action="store_true")
    args = parser.parse_args()
    try:
        receipt = execute(args.job_dir, args.godot, not args.no_web)
        print(json.dumps({"status": receipt["status"], "job": str(args.job_dir/"job.json")}))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print("World Creator worker failed: "+str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
