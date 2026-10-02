#!/usr/bin/env python3
"""Validate, import, test and export with an existing Godot 4.5.1 installation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from check_release import FORBIDDEN_DIRECTORIES, FORBIDDEN_SUFFIXES, ROOT, git, tracked_files

VERSION = "0.2.0"
GODOT_TEST_SUITES = ("core", "runtime", "character")
GODOT_VERSION = "4.5.1"
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ENGINE_ERROR = re.compile(r"(?m)^\s*(?:SCRIPT\s+)?ERROR:")
WEB_README = """DOMES FOR DOTS v0.2.0 - Standalone Web build

Godot is not required to run this prebuilt browser version.

1. Extract every file into one folder, preserving the names and docs folder.
2. Open a terminal in that extracted folder. With Python 3 installed, run:

   python -m http.server 8060 --bind 127.0.0.1

3. Open http://127.0.0.1:8060 in a desktop browser with WebGL 2 support.

Keep index.html, index.js, index.wasm, index.pck and their generated siblings
together. Opening index.html via file:// is unsupported. Stop the local server
with Ctrl+C. This loopback preview server is not a public deployment service.

Select Moss's Cedar Atelier, Nova's Tidal Observatory or Lumen's Lantern Archive.
Their routines and finite projects are SIMULATED; mock work/call controls are MOCK.
Actual Dot work and native-call connections are unavailable. This world does
not carry or initiate calls, run another assistant, or continuously call a model.

State is saved only in this browser profile and origin. Different hostnames,
ports, browsers and devices have separate state. Browser storage can be cleared
or blocked; use state export for a backup and keep one saving tab open. Hosting
these files does not provide cross-device database persistence or private access.

Original project material is MIT-licensed (LICENSE). The Godot runtime and
third-party component notices are in docs/GODOT_LICENSE.txt and
docs/GODOT_COPYRIGHT.txt. See docs/THIRD_PARTY_NOTICES.md for provenance.
Keep these license files when redistributing this build.

Build verification and runtime file hashes: build_manifest.json.
Release identity when distributed in the release ZIP: release_manifest.json.
"""


def sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def find_godot(explicit: str | None, root: Path) -> Path:
    choice = explicit or os.environ.get("GODOT_BIN")
    if choice:
        path = Path(choice).expanduser()
        if not path.is_file():
            located = shutil.which(choice)
            if located:
                path = Path(located)
        if not path.is_file():
            raise ValueError("Godot executable was not found at --godot/GODOT_BIN")
        return path.resolve()
    candidates = []
    for path in (root / ".tools").glob("**/*"):
        if path.is_file() and "4.5.1" in path.name and (path.suffix.lower() == ".exe" or os.access(path, os.X_OK)) and "godot" in path.name.lower() and "mono" not in path.name.lower():
            candidates.append(path)
    candidates.sort(key=lambda path: ("console" not in path.name.lower(), len(str(path))))
    if candidates:
        return candidates[0].resolve()
    for command in ["godot", "godot4"]:
        if executable := shutil.which(command):
            return Path(executable).resolve()
    raise ValueError("Godot was not found. Install 4.5.1 Standard and matching Web templates, then set GODOT_BIN or --godot. No toolchain is installed by this script.")


def run(command: list[str], label: str, root: Path, log_dir: Path, timeout: int = 240) -> str:
    print(f"RUN: {label}", flush=True)
    try:
        completed = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
    except subprocess.TimeoutExpired as error:
        output = error.stdout or b""
        if isinstance(output, bytes):
            output = output.decode("utf-8", "replace")
        (log_dir / f"{label}.log").write_text(output, encoding="utf-8")
        raise ValueError(f"{label} timed out after {timeout}s; inspect {log_dir.relative_to(root)}/{label}.log") from error
    output = ANSI.sub("", completed.stdout)
    (log_dir / f"{label}.log").write_text(output, encoding="utf-8")
    if completed.returncode or ENGINE_ERROR.search(output):
        print(output[-12000:])
        raise ValueError(f"{label} failed (exit {completed.returncode}, engine error log={bool(ENGINE_ERROR.search(output))}); inspect {log_dir.relative_to(root)}/{label}.log")
    print(f"PASS: {label}", flush=True)
    for line in output.splitlines():
        if re.search(r"(?:TESTS:|tests? passed|^Ran \d+ tests|^PASS:)", line, re.I):
            print(f"  {line}", flush=True)
    return output


def safe_remove_tree(path: Path, root: Path) -> None:
    resolved = path.resolve()
    dist = (root / "dist").resolve()
    if resolved == dist or not resolved.is_relative_to(dist):
        raise ValueError("Refusing removal outside a child of the project dist directory")
    if path.exists():
        shutil.rmtree(path)


def runtime_hashes(root: Path) -> dict[str, str]:
    if (root / ".git").exists():
        files = tracked_files(root, True)
    else:
        # A downloaded source ZIP deliberately has no Git metadata. Resource
        # hashes and builds still work; only final packaging requires Git.
        files = [path.relative_to(root).as_posix() for path in (root / "godot").rglob("*")
                 if path.is_file() and not any(part in FORBIDDEN_DIRECTORIES for part in path.relative_to(root).parts)
                 and path.suffix.lower() not in FORBIDDEN_SUFFIXES]
    result = {}
    for relative in sorted(files):
        path = root / relative
        if relative.startswith("godot/") and path.is_file():
            if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"Runtime source must be a regular file inside the project: {relative}")
            result[relative] = sha256(path)
    return result


def source_metadata(root: Path) -> dict:
    if not (root / ".git").exists():
        return dict(source_commit="source-archive", source_dirty=None)
    return dict(source_commit=git(root,"rev-parse","HEAD").decode().strip(),
                source_dirty=bool(git(root,"status","--porcelain","--untracked-files=normal").strip()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", help="existing Godot executable; otherwise GODOT_BIN, .tools, then PATH")
    parser.add_argument("--allow-missing-runtime-test", action="store_true", help="candidate build only; final packages require runtime tests")
    args = parser.parse_args()
    root = ROOT.resolve()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    log_dir = root / "artifacts/build" / run_id
    log_dir.mkdir(parents=True, exist_ok=False)
    staging = root / "dist" / (".web-build-" + uuid.uuid4().hex)
    staging.mkdir(parents=True, exist_ok=False)
    try:
        godot = find_godot(args.godot, root)
        version = run([str(godot), "--version"], "godot_version", root, log_dir).strip()
        if not re.fullmatch(r"4\.5\.1\.stable(?:\.official)?(?:\.[A-Za-z0-9]+)?", version):
            raise ValueError(f"Godot version must be 4.5.1 Standard stable; found {version!r}")
        project = (root / "godot/project.godot").read_text(encoding="utf-8")
        if f'config/version="{VERSION}"' not in project:
            raise ValueError(f"Project config/version must be {VERSION}")
        run([sys.executable, "tools/validate_content.py"], "content", root, log_dir)
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], "python_tests", root, log_dir)
        before_hashes = runtime_hashes(root)
        base = [str(godot), "--headless", "--path", str(root / "godot")]
        run([*base, "--editor", "--import"], "godot_import", root, log_dir)
        audit = run([*base, "--script", "res://tools/audit_characters.gd", "--", "--output", str(log_dir / "character-audit.json")], "character_audit", root, log_dir)
        if not re.search(r"CHARACTER AUDIT:\s*\d+ characters, PASS", audit):
            raise ValueError("Character audit exited without a recognized success summary")
        tests = {}
        for name in GODOT_TEST_SUITES:
            path = root / f"godot/tests/test_{name}.gd"
            if not path.is_file():
                if name == "runtime" and args.allow_missing_runtime_test:
                    tests[name] = "missing_candidate_only"
                    print("CANDIDATE: runtime test missing; final packaging will refuse this build", flush=True)
                    continue
                raise ValueError(f"Missing required runtime test: {path.relative_to(root)}")
            command = [*base, "--script", f"res://tests/test_{name}.gd"]
            if name in {"runtime", "character"}:
                command.extend(["--fixed-fps", "60"])
            output = run(command, f"godot_{name}_tests", root, log_dir)
            if not re.search(rf"{name.upper()} TESTS:\s*\d+ passed,\s*0 failed", output):
                raise ValueError(f"{name} tests exited without a recognized success summary")
            tests[name] = "passed"
        run([*base, "--export-release", "Web", str(staging / "index.html")], "web_export", root, log_dir)
        for filename in ["index.html", "index.js", "index.wasm", "index.pck"]:
            path = staging / filename
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError(f"Export missing/empty required file: {filename}")
        shutil.copyfile(root / "LICENSE", staging / "LICENSE")
        notices = staging / "docs"
        notices.mkdir()
        for filename in ["GODOT_LICENSE.txt", "GODOT_COPYRIGHT.txt", "THIRD_PARTY_NOTICES.md"]:
            shutil.copyfile(root / "docs" / filename, notices / filename)
        (staging / "README.txt").write_text(WEB_README, encoding="utf-8")
        after_hashes = runtime_hashes(root)
        # Import may create tracked-resource UID sidecars on the first import.
        if any(after_hashes.get(path) != value for path, value in before_hashes.items()):
            raise ValueError("Runtime source changed during build; rerun after edits finish")
        manifest = dict(schema_version=1,version=VERSION,godot_version=version,renderer="gl_compatibility",threads=False,
            built_at_utc=datetime.now(timezone.utc).isoformat(),**source_metadata(root),
            validation="passed",python_tests="passed",character_audit="passed",godot_tests=tests,
            runtime_source_sha256=after_hashes,files={path.relative_to(staging).as_posix():sha256(path) for path in sorted(staging.rglob("*")) if path.is_file()})
        (staging / "build_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
        destination = root / "dist/web"
        previous = root / "dist" / (".web-previous-" + uuid.uuid4().hex)
        if destination.exists():
            if not destination.resolve().is_relative_to((root / "dist").resolve()):
                raise ValueError("Export destination escapes project dist directory")
            destination.rename(previous)
        try:
            staging.rename(destination)
        except OSError:
            if previous.exists():
                previous.rename(destination)
            raise
        safe_remove_tree(previous, root)
        print(f"PASS: Web {VERSION} exported to dist/web/index.html; logs: {log_dir.relative_to(root)}")
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    finally:
        safe_remove_tree(staging, root)


if __name__ == "__main__":
    raise SystemExit(main())
